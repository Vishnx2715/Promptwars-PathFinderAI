"""PracticeService: Coding problems, submissions, test evaluation, mastery updates.
Deterministic rules control mastery changes from coding practice."""
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import StudentProfile
from app.models.skill import Skill, LearnerSkill
from app.models.practice import CodingProblem, CodeSubmission, PracticeSession
from app.models.analytics import LearningActivity
from app.schemas.practice import (
    CodingProblemListItem,
    CodingProblemDetail,
    CodeSubmissionResponse,
    TestResultItem,
    SubmissionHistoryItem,
)
from app.services.code_execution_service import CodeExecutionService
from app.agents.code_review_agent import CodeReviewAgent


class PracticeService:
    @staticmethod
    async def list_problems(
        db: AsyncSession,
        profile_id: int,
        language: Optional[str] = None,
        skill_id: Optional[int] = None,
        subtopic: Optional[str] = None,
        difficulty: Optional[str] = None,
        status_filter: Optional[str] = None
    ) -> List[CodingProblemListItem]:
        query = (
            select(CodingProblem)
            .options(selectinload(CodingProblem.skill))
            .where(CodingProblem.is_active == True)
        )
        if language:
            query = query.where(CodingProblem.language == language)
        if skill_id:
            query = query.where(CodingProblem.skill_id == skill_id)
        if subtopic:
            query = query.where(CodingProblem.subtopic == subtopic)
        if difficulty:
            query = query.where(CodingProblem.difficulty == difficulty)

        query = query.order_by(CodingProblem.difficulty, CodingProblem.id)
        res = await db.execute(query)
        problems = res.scalars().all()

        # Get user's submission stats for each problem
        result = []
        for p in problems:
            sub_res = await db.execute(
                select(CodeSubmission).where(
                    CodeSubmission.student_profile_id == profile_id,
                    CodeSubmission.coding_problem_id == p.id,
                )
            )
            subs = sub_res.scalars().all()
            solved = any(s.status == "passed" for s in subs)
            attempted = len(subs) > 0

            if status_filter == "solved" and not solved:
                continue
            if status_filter == "unsolved" and solved:
                continue
            if status_filter == "attempted" and not attempted:
                continue

            # Acceptance rate
            all_sub_res = await db.execute(
                select(CodeSubmission).where(CodeSubmission.coding_problem_id == p.id)
            )
            all_subs = all_sub_res.scalars().all()
            total_all = len(all_subs)
            passed_all = sum(1 for s in all_subs if s.status == "passed")
            acceptance_rate = round((passed_all / total_all * 100), 1) if total_all > 0 else 0.0

            result.append(CodingProblemListItem(
                id=p.id,
                title=p.title,
                language=p.language,
                skill_id=p.skill_id,
                skill_name=p.skill.name if p.skill else "",
                subtopic=p.subtopic,
                difficulty=p.difficulty,
                is_solved=solved,
                is_attempted=attempted,
                acceptance_rate=acceptance_rate,
                total_submissions=total_all,
            ))
        return result

    @staticmethod
    async def get_problem(
        db: AsyncSession, profile_id: int, problem_id: int
    ) -> CodingProblemDetail:
        res = await db.execute(
            select(CodingProblem)
            .options(selectinload(CodingProblem.skill))
            .where(CodingProblem.id == problem_id, CodingProblem.is_active == True)
        )
        problem = res.scalar_one_or_none()
        if not problem:
            raise HTTPException(status_code=404, detail="Coding problem not found")

        # Return only visible (sample) test cases
        visible = [tc for tc in (problem.test_cases or []) if not tc.get("is_hidden", False)]

        return CodingProblemDetail(
            id=problem.id,
            title=problem.title,
            description=problem.description,
            language=problem.language,
            skill_id=problem.skill_id,
            skill_name=problem.skill.name if problem.skill else "",
            subtopic=problem.subtopic,
            difficulty=problem.difficulty,
            starter_code=problem.starter_code,
            function_name=problem.function_name,
            examples=problem.examples or [],
            constraints=problem.constraints,
            visible_test_cases=visible,
        )

    @staticmethod
    async def run_sample_tests(
        db: AsyncSession, profile_id: int, problem_id: int, code: str, language: str
    ) -> List[Dict[str, Any]]:
        """Run only visible test cases. Returns results for frontend display."""
        res = await db.execute(select(CodingProblem).where(CodingProblem.id == problem_id))
        problem = res.scalar_one_or_none()
        if not problem:
            raise HTTPException(status_code=404, detail="Problem not found")

        visible_cases = [tc for tc in (problem.test_cases or []) if not tc.get("is_hidden", False)]

        if language == "javascript":
            # Return test cases for frontend Web Worker execution
            results = CodeExecutionService.evaluate_javascript(code, visible_cases, problem.function_name)
            return results
        else:
            results = CodeExecutionService.evaluate_python(code, visible_cases, problem.function_name)
            return results

    @staticmethod
    async def submit_solution(
        db: AsyncSession,
        profile_id: int,
        problem_id: int,
        code: str,
        language: str,
        frontend_results: Optional[List[Dict[str, Any]]] = None
    ) -> CodeSubmissionResponse:
        """Submit and evaluate code against all test cases (visible + hidden)."""
        # Load problem
        res = await db.execute(
            select(CodingProblem)
            .options(selectinload(CodingProblem.skill))
            .where(CodingProblem.id == problem_id)
        )
        problem = res.scalar_one_or_none()
        if not problem:
            raise HTTPException(status_code=404, detail="Coding problem not found")

        # Check if language matches problem
        if language != problem.language:
            raise HTTPException(status_code=400, detail=f"This problem requires {problem.language}. You submitted {language}.")

        # Evaluate all test cases
        all_test_cases = problem.test_cases or []
        results, tests_passed, tests_total, status_val, runtime_ms = CodeExecutionService.evaluate_results(
            language=language,
            code=code,
            test_cases=all_test_cases,
            function_name=problem.function_name,
            frontend_results=frontend_results
        )

        # Count previous attempts for this problem
        prev_res = await db.execute(
            select(CodeSubmission).where(
                CodeSubmission.student_profile_id == profile_id,
                CodeSubmission.coding_problem_id == problem_id,
            )
        )
        prev_subs = prev_res.scalars().all()
        previous_attempts = len(prev_subs)

        # Check repeated failures on same subtopic
        subtopic_failures = sum(1 for s in prev_subs if s.status != "passed")

        # AI code review
        test_results_for_ai = [
            {
                "name": r.get("name", f"Test {i+1}"),
                "passed": r.get("passed", False),
                "expected": r.get("expected_output", ""),
                "actual": r.get("actual", ""),
            }
            for i, r in enumerate(results)
        ]

        ai_review = await CodeReviewAgent.run(
            problem_title=problem.title,
            problem_description=problem.description,
            student_code=code,
            test_results=test_results_for_ai,
            language=language,
            skill_name=problem.skill.name if problem.skill else "",
            subtopic=problem.subtopic,
            previous_attempts=previous_attempts + 1,
            tests_passed=tests_passed,
            tests_total=tests_total
        )

        # Calculate mastery change (deterministic rules)
        mastery_change = 0.0
        if tests_total > 0:
            if tests_passed == tests_total:
                # All passed: increase mastery by 5-10 points
                mastery_change = min(10.0, 5.0 + (tests_passed * 0.5))
            elif tests_passed > 0:
                # Some passed: increase by 1-3 points
                mastery_change = min(3.0, 1.0 + (tests_passed * 0.3))
            else:
                # All failed: decrease by 2-5 points
                mastery_change = -max(2.0, min(5.0, 5.0 - (previous_attempts * 0.5)))

        # Update LearnerSkill mastery
        ls_res = await db.execute(
            select(LearnerSkill).where(
                LearnerSkill.student_profile_id == profile_id,
                LearnerSkill.skill_id == problem.skill_id,
            )
        )
        learner_skill = ls_res.scalar_one_or_none()
        if not learner_skill:
            learner_skill = LearnerSkill(
                student_profile_id=profile_id,
                skill_id=problem.skill_id,
                self_reported_level=0,
                verified_level=0,
                evidence_type="assessment",
                mastery_percentage=0.0,
            )
            db.add(learner_skill)
            await db.flush()

        new_mastery = max(0.0, min(100.0, learner_skill.mastery_percentage + mastery_change))
        learner_skill.mastery_percentage = new_mastery
        learner_skill.verified_level = round((new_mastery / 100.0) * 5.0, 2)
        learner_skill.evidence_type = "assessment"
        learner_skill.last_assessed_at = datetime.now(timezone.utc)
        learner_skill.updated_at = datetime.now(timezone.utc)

        # Determine score (percentage of tests passed)
        score = round((tests_passed / max(tests_total, 1)) * 100.0, 1)

        # Create submission record
        submission = CodeSubmission(
            student_profile_id=profile_id,
            coding_problem_id=problem_id,
            language=language,
            submitted_code=code,
            status=status_val,
            score=score,
            tests_passed=tests_passed,
            tests_total=tests_total,
            runtime_ms=runtime_ms,
            execution_output=str(results[:5000]) if results else None,
            ai_review=ai_review,
            submitted_at=datetime.now(timezone.utc),
        )
        db.add(submission)

        # Update PracticeSession
        ps_res = await db.execute(
            select(PracticeSession).where(
                PracticeSession.student_profile_id == profile_id,
                PracticeSession.skill_id == problem.skill_id,
            )
        )
        practice_session = ps_res.scalar_one_or_none()
        if not practice_session:
            practice_session = PracticeSession(
                student_profile_id=profile_id,
                skill_id=problem.skill_id,
                started_at=datetime.now(timezone.utc),
            )
            db.add(practice_session)
            await db.flush()

        practice_session.problems_attempted += 1
        if status_val == "passed":
            practice_session.problems_solved += 1
        practice_session.accuracy = round(
            (practice_session.problems_solved / max(practice_session.problems_attempted, 1)) * 100, 1
        )
        practice_session.last_active_at = datetime.now(timezone.utc)

        # Create LearningActivity
        activity = LearningActivity(
            student_profile_id=profile_id,
            activity_type="coding_problem_attempted",
            reference_id=problem_id,
            meta={
                "title": problem.title,
                "status": status_val,
                "tests_passed": tests_passed,
                "tests_total": tests_total,
                "mastery_change": mastery_change,
            },
            created_at=datetime.now(timezone.utc),
        )
        db.add(activity)

        # Trigger WeaknessTrainer if repeated failures on same subtopic
        mentor_alert = False
        if subtopic_failures >= 3 and status_val != "passed":
            mentor_alert = True
            # Add a mentor_alert activity
            alert_activity = LearningActivity(
                student_profile_id=profile_id,
                activity_type="mentor_feedback",
                reference_id=problem_id,
                meta={
                    "type": "weakness_alert",
                    "subtopic": problem.subtopic,
                    "failures": subtopic_failures,
                    "message": f"Student has failed {subtopic_failures} times on {problem.subtopic}.",
                },
                created_at=datetime.now(timezone.utc),
            )
            db.add(alert_activity)

        await db.commit()
        await db.refresh(submission)

        # Format test results for response
        test_result_items = [
            TestResultItem(
                name=r.get("name", f"Test {i+1}"),
                passed=r.get("passed", False),
                expected=r.get("expected_output", ""),
                actual=r.get("actual", ""),
                is_hidden=r.get("is_hidden", False),
            )
            for i, r in enumerate(results)
        ]

        return CodeSubmissionResponse(
            id=submission.id,
            coding_problem_id=problem_id,
            language=language,
            status=status_val,
            score=score,
            tests_passed=tests_passed,
            tests_total=tests_total,
            runtime_ms=runtime_ms,
            ai_review=ai_review,
            submitted_at=submission.submitted_at,
            test_results=test_result_items,
            mastery_change=mastery_change,
            mentor_alert=mentor_alert,
        )

    @staticmethod
    async def get_submission_history(
        db: AsyncSession, profile_id: int, problem_id: int
    ) -> List[SubmissionHistoryItem]:
        res = await db.execute(
            select(CodeSubmission)
            .where(
                CodeSubmission.student_profile_id == profile_id,
                CodeSubmission.coding_problem_id == problem_id,
            )
            .order_by(CodeSubmission.submitted_at.desc())
        )
        subs = res.scalars().all()
        return [
            SubmissionHistoryItem(
                id=s.id,
                status=s.status,
                score=s.score,
                tests_passed=s.tests_passed,
                tests_total=s.tests_total,
                submitted_at=s.submitted_at,
            )
            for s in subs
        ]

    @staticmethod
    async def get_next_recommended_problem(
        db: AsyncSession, profile_id: int, problem_id: int
    ) -> Optional[Dict[str, Any]]:
        """Recommend next problem in same skill/subtopic that student hasn't solved."""
        res = await db.execute(select(CodingProblem).where(CodingProblem.id == problem_id))
        problem = res.scalar_one_or_none()
        if not problem:
            return None

        # Find unsolved problems in same skill
        all_in_skill_res = await db.execute(
            select(CodingProblem)
            .where(
                CodingProblem.skill_id == problem.skill_id,
                CodingProblem.is_active == True,
                CodingProblem.id != problem_id,
            )
            .order_by(CodingProblem.difficulty, CodingProblem.id)
        )
        candidates = all_in_skill_res.scalars().all()

        for c in candidates:
            sub_res = await db.execute(
                select(CodeSubmission).where(
                    CodeSubmission.student_profile_id == profile_id,
                    CodeSubmission.coding_problem_id == c.id,
                    CodeSubmission.status == "passed",
                )
            )
            if not sub_res.scalars().first():
                return {"id": c.id, "title": c.title, "reason": f"Continue practicing {c.subtopic}."}

        return None
