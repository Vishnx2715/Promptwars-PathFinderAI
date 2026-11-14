from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import StudentProfile
from app.models.skill import Skill, LearnerSkill
from app.models.career import RoleSkillRequirement
from app.models.assessment import (
    Assessment,
    Question,
    AssessmentAttempt,
    AssessmentResponse,
)
from app.schemas.assessment import (
    AssessmentStartResponse,
    QuestionPublicResponse,
    AssessmentSubmitRequest,
    AssessmentResultResponse,
    QuestionBreakdownItem,
    WeakTopicItem,
)
from app.services.replanning_service import ReplanningService


class AssessmentService:
    @staticmethod
    async def get_assessment_by_skill(db: AsyncSession, skill_id: int) -> Assessment:
        res = await db.execute(
            select(Assessment)
            .options(selectinload(Assessment.skill))
            .where(Assessment.skill_id == skill_id)
        )
        assessment = res.scalar_one_or_none()
        if not assessment:
            raise HTTPException(status_code=404, detail="No assessment found for this skill")
        return assessment

    @staticmethod
    async def start_assessment(
        db: AsyncSession, profile_id: int, assessment_id: int
    ) -> AssessmentStartResponse:
        res = await db.execute(
            select(Assessment)
            .options(
                selectinload(Assessment.skill),
                selectinload(Assessment.questions),
            )
            .where(Assessment.id == assessment_id)
        )
        assessment = res.scalar_one_or_none()
        if not assessment:
            raise HTTPException(status_code=404, detail="Assessment not found")

        # Create new AssessmentAttempt
        attempt = AssessmentAttempt(
            student_profile_id=profile_id,
            assessment_id=assessment.id,
            score=0.0,
            max_score=float(sum(q.marks for q in assessment.questions)),
            mastery_percentage=0.0,
            started_at=datetime.now(timezone.utc),
        )
        db.add(attempt)
        await db.commit()
        await db.refresh(attempt)

        # Map questions without correct answers for test integrity
        questions_resp = [
            QuestionPublicResponse(
                id=q.id,
                assessment_id=q.assessment_id,
                skill_id=q.skill_id,
                subtopic=q.subtopic,
                question_text=q.question_text,
                options=q.options,
                difficulty=q.difficulty,
                marks=q.marks,
            )
            for q in assessment.questions
        ]

        return AssessmentStartResponse(
            attempt_id=attempt.id,
            assessment_id=assessment.id,
            title=assessment.title,
            skill_id=assessment.skill_id,
            skill_name=assessment.skill.name if assessment.skill else "",
            total_questions=len(questions_resp),
            questions=questions_resp,
        )

    @staticmethod
    async def submit_assessment(
        db: AsyncSession,
        profile_id: int,
        attempt_id: int,
        submission: AssessmentSubmitRequest
    ) -> AssessmentResultResponse:
        res = await db.execute(
            select(AssessmentAttempt)
            .options(
                selectinload(AssessmentAttempt.assessment).selectinload(Assessment.skill),
                selectinload(AssessmentAttempt.assessment).selectinload(Assessment.questions),
            )
            .where(
                AssessmentAttempt.id == attempt_id,
                AssessmentAttempt.student_profile_id == profile_id,
            )
        )
        attempt = res.scalar_one_or_none()
        if not attempt:
            raise HTTPException(status_code=404, detail="Assessment attempt not found")

        if attempt.submitted_at:
            raise HTTPException(status_code=400, detail="This assessment attempt has already been submitted.")

        assessment = attempt.assessment
        questions_dict = {q.id: q for q in assessment.questions}

        total_score = 0.0
        max_score = sum(q.marks for q in assessment.questions)
        breakdown: List[QuestionBreakdownItem] = []
        subtopic_misses: Dict[str, int] = {}

        # Process answers
        for ans in submission.answers:
            q = questions_dict.get(ans.question_id)
            if not q:
                continue

            is_correct = (ans.selected_option.strip().upper() == q.correct_option.strip().upper())
            if is_correct:
                total_score += q.marks
            else:
                subtopic_misses[q.subtopic] = subtopic_misses.get(q.subtopic, 0) + 1

            # Save response
            resp_record = AssessmentResponse(
                attempt_id=attempt.id,
                question_id=q.id,
                selected_option=ans.selected_option,
                is_correct=is_correct,
                time_taken_seconds=ans.time_taken_seconds,
            )
            db.add(resp_record)

            breakdown.append(
                QuestionBreakdownItem(
                    question_id=q.id,
                    subtopic=q.subtopic,
                    question_text=q.question_text,
                    selected_option=ans.selected_option,
                    correct_option=q.correct_option,
                    is_correct=is_correct,
                    explanation=q.explanation,
                )
            )

        mastery_pct = round((total_score / max_score) * 100.0, 1) if max_score > 0 else 0.0

        # Update attempt
        attempt.score = total_score
        attempt.max_score = max_score
        attempt.mastery_percentage = mastery_pct
        attempt.submitted_at = datetime.now(timezone.utc)

        # Update LearnerSkill
        verified_lvl = round((mastery_pct / 100.0) * 5.0, 2)
        ls_res = await db.execute(
            select(LearnerSkill).where(
                LearnerSkill.student_profile_id == profile_id,
                LearnerSkill.skill_id == assessment.skill_id,
            )
        )
        learner_skill = ls_res.scalar_one_or_none()
        if learner_skill:
            learner_skill.verified_level = verified_lvl
            learner_skill.mastery_percentage = mastery_pct
            learner_skill.evidence_type = "assessment"
            learner_skill.last_assessed_at = datetime.now(timezone.utc)
        else:
            learner_skill = LearnerSkill(
                student_profile_id=profile_id,
                skill_id=assessment.skill_id,
                self_reported_level=int(verified_lvl),
                verified_level=verified_lvl,
                evidence_type="assessment",
                mastery_percentage=mastery_pct,
                last_assessed_at=datetime.now(timezone.utc),
            )
            db.add(learner_skill)

        await db.flush()

        # Apply adaptive replanning rules to active roadmap
        roadmap_changes = await ReplanningService.apply_assessment_adaptive_rules(
            db, profile_id, assessment.skill_id, mastery_pct
        )

        # Weak topics
        weak_topics = [
            WeakTopicItem(
                subtopic=subtopic,
                incorrect_count=count,
                recommendation=f"Review targeted documentation and code examples on {subtopic}."
            )
            for subtopic, count in subtopic_misses.items()
        ]

        # Determine next best action and mentor message
        skill_name = assessment.skill.name if assessment.skill else "Skill"
        if mastery_pct < 50.0:
            next_action = f"Complete the revision resources in '{skill_name}' module and review {', '.join(subtopic_misses.keys()) or 'core fundamentals'}."
            mentor_msg = f"You scored {mastery_pct:.0f}% in {skill_name}. We've created a targeted revision sprint so you can master the core topics before progressing."
        elif mastery_pct < 75.0:
            next_action = f"Practice code exercises on {skill_name} to reach 75%+ and unblock dependent modules."
            mentor_msg = f"Good effort! You reached {mastery_pct:.0f}% in {skill_name}. Work through a few more practical exercises to reach full readiness."
        else:
            next_action = f"Excellent! Your {skill_name} mastery is verified at {mastery_pct:.0f}%. Proceed to your next unlocked roadmap module."
            mentor_msg = f"Outstanding work! With {mastery_pct:.0f}% mastery, you have successfully satisfied prerequisites for advanced modules."

        # Coach agent invocation with fallback
        try:
            from app.agents.progress_coach_agent import ProgressCoachAgent
            coach_feedback = await ProgressCoachAgent.run(
                skill_name=skill_name,
                mastery=mastery_pct,
                weak_topics=weak_topics,
                roadmap_changes=roadmap_changes,
                fallback_action=next_action,
                fallback_msg=mentor_msg
            )
            next_action = coach_feedback.get("next_best_action", next_action)
            mentor_msg = coach_feedback.get("mentor_message", mentor_msg)
        except Exception:
            pass

        # Save result analysis in attempt
        analysis_data = {
            "score": total_score,
            "max_score": max_score,
            "mastery_percentage": mastery_pct,
            "breakdown": [b.model_dump() for b in breakdown],
            "weak_topics": [w.model_dump() for w in weak_topics],
            "roadmap_changes": roadmap_changes,
            "next_best_action": next_action,
            "mentor_message": mentor_msg,
        }
        attempt.result_analysis = analysis_data
        await db.commit()

        return AssessmentResultResponse(
            attempt_id=attempt.id,
            assessment_title=assessment.title,
            skill_name=skill_name,
            score=total_score,
            max_score=max_score,
            mastery_percentage=mastery_pct,
            started_at=attempt.started_at,
            submitted_at=attempt.submitted_at,
            breakdown=breakdown,
            weak_topics=weak_topics,
            recommended_resources=[],
            roadmap_changes=roadmap_changes,
            next_best_action=next_action,
            mentor_message=mentor_msg,
        )

    @staticmethod
    async def get_attempt_result(
        db: AsyncSession, profile_id: int, attempt_id: int
    ) -> AssessmentResultResponse:
        res = await db.execute(
            select(AssessmentAttempt)
            .options(
                selectinload(AssessmentAttempt.assessment).selectinload(Assessment.skill),
            )
            .where(
                AssessmentAttempt.id == attempt_id,
                AssessmentAttempt.student_profile_id == profile_id,
            )
        )
        attempt = res.scalar_one_or_none()
        if not attempt or not attempt.submitted_at or not attempt.result_analysis:
            raise HTTPException(status_code=404, detail="Completed assessment result not found")

        analysis = attempt.result_analysis
        breakdown_objs = [QuestionBreakdownItem(**b) for b in analysis.get("breakdown", [])]
        weak_topics_objs = [WeakTopicItem(**w) for w in analysis.get("weak_topics", [])]

        return AssessmentResultResponse(
            attempt_id=attempt.id,
            assessment_title=attempt.assessment.title,
            skill_name=attempt.assessment.skill.name if attempt.assessment.skill else "",
            score=attempt.score,
            max_score=attempt.max_score,
            mastery_percentage=attempt.mastery_percentage,
            started_at=attempt.started_at,
            submitted_at=attempt.submitted_at,
            breakdown=breakdown_objs,
            weak_topics=weak_topics_objs,
            recommended_resources=analysis.get("recommended_resources", []),
            roadmap_changes=analysis.get("roadmap_changes", []),
            next_best_action=analysis.get("next_best_action", "Proceed to your roadmap."),
            mentor_message=analysis.get("mentor_message"),
        )

