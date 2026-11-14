"""Portfolio, leaderboard, skill-decay, and recommendation services."""
from datetime import datetime, timezone, date, timedelta
from typing import List, Dict, Any, Optional

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.portfolio import PortfolioProfile, SkillDecayAlert, Campus, LeaderboardEntry
from app.models.notification import AIRecommendation
from app.models.profile import StudentProfile
from app.models.skill import Skill, LearnerSkill
from app.models.practice import CodeSubmission
from app.models.project import ProjectSubmission
from app.models.assessment import AssessmentAttempt
from app.models.analytics import LearningActivity
from app.services.notification_service import NotificationService


class PortfolioService:
    @staticmethod
    async def get_or_create_portfolio(db: AsyncSession, profile_id: int) -> Dict[str, Any]:
        res = await db.execute(
            select(PortfolioProfile).where(PortfolioProfile.student_profile_id == profile_id)
        )
        pp = res.scalar_one_or_none()
        if not pp:
            pp = PortfolioProfile(
                student_profile_id=profile_id, updated_at=datetime.now(timezone.utc)
            )
            db.add(pp)
            await db.commit()
            await db.refresh(pp)
        return PortfolioService._fmt(pp)

    @staticmethod
    async def update_portfolio(
        db: AsyncSession, profile_id: int, updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        res = await db.execute(
            select(PortfolioProfile).where(PortfolioProfile.student_profile_id == profile_id)
        )
        pp = res.scalar_one_or_none()
        if not pp:
            pp = PortfolioProfile(student_profile_id=profile_id)
            db.add(pp)

        for field in ("github_url", "leetcode_url", "hackerrank_url",
                      "problems_solved", "show_in_leaderboard"):
            if field in updates:
                setattr(pp, field, updates[field])
        pp.updated_at = datetime.now(timezone.utc)

        # Update streak
        today = date.today()
        if pp.last_activity_date == today - timedelta(days=1):
            pp.current_streak += 1
        elif pp.last_activity_date != today:
            pp.current_streak = 1
        pp.last_activity_date = today
        if pp.current_streak > pp.longest_streak:
            pp.longest_streak = pp.current_streak

        # Recalculate portfolio score
        pp.portfolio_score = await PortfolioService._calc_score(db, profile_id, pp)
        await db.commit()
        return PortfolioService._fmt(pp)

    @staticmethod
    async def _calc_score(db: AsyncSession, profile_id: int, pp: PortfolioProfile) -> float:
        # Projects evaluated: up to 30
        proj_res = await db.execute(
            select(func.count(ProjectSubmission.id)).where(
                ProjectSubmission.student_profile_id == profile_id,
                ProjectSubmission.status == "evaluated",
            )
        )
        proj_count = proj_res.scalar() or 0
        project_pts = min(30.0, proj_count * 10.0)

        # Problems solved: up to 25
        problems_pts = min(25.0, (pp.problems_solved or 0) * 0.5)

        # Assessment mastery avg: up to 20
        assess_res = await db.execute(
            select(func.avg(AssessmentAttempt.mastery_percentage)).where(
                AssessmentAttempt.student_profile_id == profile_id,
                AssessmentAttempt.submitted_at != None,
            )
        )
        avg_mastery = float(assess_res.scalar() or 0)
        assessment_pts = (avg_mastery / 100.0) * 20.0

        # Streak consistency: up to 10
        streak_pts = min(10.0, (pp.current_streak or 0) * 1.0)

        return round(project_pts + problems_pts + assessment_pts + streak_pts, 1)

    @staticmethod
    def _fmt(pp: PortfolioProfile) -> Dict[str, Any]:
        return {
            "id": pp.id, "github_url": pp.github_url, "leetcode_url": pp.leetcode_url,
            "hackerrank_url": pp.hackerrank_url, "problems_solved": pp.problems_solved,
            "current_streak": pp.current_streak, "longest_streak": pp.longest_streak,
            "portfolio_score": pp.portfolio_score, "show_in_leaderboard": pp.show_in_leaderboard,
            "last_activity_date": str(pp.last_activity_date) if pp.last_activity_date else None,
        }

    @staticmethod
    async def get_leaderboard(
        db: AsyncSession, campus_id: Optional[int], period_type: str = "weekly"
    ) -> List[Dict[str, Any]]:
        q = select(LeaderboardEntry).where(LeaderboardEntry.period_type == period_type)
        if campus_id:
            q = q.where(LeaderboardEntry.campus_id == campus_id)
        q = q.order_by(LeaderboardEntry.total_points.desc()).limit(50)
        res = await db.execute(q)
        entries = res.scalars().all()

        result = []
        for i, e in enumerate(entries, start=1):
            # Load student name
            prof_res = await db.execute(
                select(StudentProfile).where(StudentProfile.id == e.student_profile_id)
            )
            profile = prof_res.scalar_one_or_none()
            # Check leaderboard opt-in
            pp_res = await db.execute(
                select(PortfolioProfile).where(PortfolioProfile.student_profile_id == e.student_profile_id)
            )
            pp = pp_res.scalar_one_or_none()
            if pp and not pp.show_in_leaderboard:
                continue
            result.append({
                "rank": i, "student_name": profile.full_name if profile else "Anonymous",
                "total_points": e.total_points, "practice_points": e.practice_points,
                "assessment_points": e.assessment_points, "project_points": e.project_points,
                "consistency_points": e.consistency_points,
                "current_streak": pp.current_streak if pp else 0,
            })
        return result

    @staticmethod
    async def recalculate_leaderboard(db: AsyncSession) -> None:
        """Background task: recalculate leaderboard for all profiles."""
        prof_res = await db.execute(select(StudentProfile))
        for profile in prof_res.scalars().all():
            # Practice points
            cs_res = await db.execute(
                select(func.count(CodeSubmission.id)).where(
                    CodeSubmission.student_profile_id == profile.id,
                    CodeSubmission.status == "passed",
                )
            )
            practice_pts = float(cs_res.scalar() or 0) * 2.0

            # Assessment points
            a_res = await db.execute(
                select(func.avg(AssessmentAttempt.mastery_percentage)).where(
                    AssessmentAttempt.student_profile_id == profile.id,
                    AssessmentAttempt.submitted_at != None,
                )
            )
            assessment_pts = float(a_res.scalar() or 0) * 0.5

            # Project points
            p_res = await db.execute(
                select(func.count(ProjectSubmission.id)).where(
                    ProjectSubmission.student_profile_id == profile.id,
                    ProjectSubmission.status == "evaluated",
                )
            )
            project_pts = float(p_res.scalar() or 0) * 10.0

            # Consistency
            pp_res = await db.execute(
                select(PortfolioProfile).where(PortfolioProfile.student_profile_id == profile.id)
            )
            pp = pp_res.scalar_one_or_none()
            consistency_pts = float(pp.current_streak if pp else 0) * 1.0

            total = practice_pts + assessment_pts + project_pts + consistency_pts

            # Upsert
            le_res = await db.execute(
                select(LeaderboardEntry).where(
                    LeaderboardEntry.student_profile_id == profile.id,
                    LeaderboardEntry.period_type == "all_time",
                )
            )
            le = le_res.scalar_one_or_none()
            if le:
                le.practice_points = practice_pts
                le.assessment_points = assessment_pts
                le.project_points = project_pts
                le.consistency_points = consistency_pts
                le.total_points = total
                le.updated_at = datetime.now(timezone.utc)
            else:
                db.add(LeaderboardEntry(
                    student_profile_id=profile.id, period_type="all_time",
                    practice_points=practice_pts, assessment_points=assessment_pts,
                    project_points=project_pts, consistency_points=consistency_pts,
                    total_points=total, rank=0, updated_at=datetime.now(timezone.utc),
                ))
        await db.commit()


class SkillDecayService:
    @staticmethod
    async def detect_and_create_alerts(db: AsyncSession, profile_id: int) -> List[Dict[str, Any]]:
        ls_res = await db.execute(
            select(LearnerSkill)
            .options(selectinload(LearnerSkill.skill))
            .where(LearnerSkill.student_profile_id == profile_id)
        )
        skills = ls_res.scalars().all()
        now = datetime.now(timezone.utc)
        created = []

        for ls in skills:
            if not ls.last_assessed_at:
                continue
            last = ls.last_assessed_at
            if last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)
            days = (now - last).days

            if days < 14:
                continue
            level = "info" if days < 30 else ("warning" if days < 45 else "critical")
            action = (
                f"Complete a quick {ls.skill.name if ls.skill else 'skill'} "
                f"revision exercise to prevent mastery loss."
            )

            # Check for existing active alert
            ex_res = await db.execute(
                select(SkillDecayAlert).where(
                    SkillDecayAlert.student_profile_id == profile_id,
                    SkillDecayAlert.skill_id == ls.skill_id,
                    SkillDecayAlert.is_dismissed == False,  # noqa: E712
                )
            )
            existing = ex_res.scalar_one_or_none()
            if existing:
                existing.days_since_practice = days
                existing.alert_level = level
                existing.recommended_action = action
            else:
                alert = SkillDecayAlert(
                    student_profile_id=profile_id, skill_id=ls.skill_id,
                    last_practiced_at=last, days_since_practice=days,
                    previous_mastery=ls.mastery_percentage, current_mastery=ls.mastery_percentage,
                    alert_level=level, recommended_action=action,
                    created_at=now,
                )
                db.add(alert)
                created.append(ls.skill.name if ls.skill else "")

        await db.commit()
        return created

    @staticmethod
    async def get_alerts(db: AsyncSession, profile_id: int) -> List[Dict[str, Any]]:
        res = await db.execute(
            select(SkillDecayAlert)
            .options(selectinload(SkillDecayAlert.skill))
            .where(
                SkillDecayAlert.student_profile_id == profile_id,
                SkillDecayAlert.is_dismissed == False,  # noqa: E712
            )
            .order_by(SkillDecayAlert.alert_level.desc())
        )
        return [
            {"id": a.id, "skill": a.skill.name if a.skill else "", "days_since": a.days_since_practice,
             "alert_level": a.alert_level, "recommended_action": a.recommended_action,
             "created_at": a.created_at.isoformat()}
            for a in res.scalars().all()
        ]


class RecommendationService:
    @staticmethod
    async def get_active(db: AsyncSession, profile_id: int) -> List[Dict[str, Any]]:
        res = await db.execute(
            select(AIRecommendation)
            .where(AIRecommendation.student_profile_id == profile_id,
                   AIRecommendation.status == "active")
            .order_by(AIRecommendation.priority, AIRecommendation.created_at.desc())
        )
        return [
            {"id": r.id, "type": r.recommendation_type, "title": r.title,
             "description": r.description, "reason": r.reason,
             "evidence": r.evidence or [], "priority": r.priority,
             "action_path": r.action_path, "estimated_minutes": r.estimated_minutes,
             "created_at": r.created_at.isoformat()}
            for r in res.scalars().all()
        ]

    @staticmethod
    async def update_status(
        db: AsyncSession, profile_id: int, rec_id: int, new_status: str
    ) -> Dict[str, Any]:
        res = await db.execute(
            select(AIRecommendation).where(
                AIRecommendation.id == rec_id,
                AIRecommendation.student_profile_id == profile_id,
            )
        )
        rec = res.scalar_one_or_none()
        if not rec:
            raise HTTPException(status_code=404, detail="Recommendation not found.")
        rec.status = new_status
        await db.commit()
        return {"id": rec_id, "status": new_status}

    @staticmethod
    async def seed_recommendations(db: AsyncSession, profile_id: int) -> None:
        """Generate and upsert deterministic recommendations from learner state."""
        ls_res = await db.execute(
            select(LearnerSkill)
            .options(selectinload(LearnerSkill.skill))
            .where(LearnerSkill.student_profile_id == profile_id)
        )
        skills = ls_res.scalars().all()

        # Clear old active ones
        from sqlalchemy import update as sa_update
        await db.execute(
            sa_update(AIRecommendation)
            .where(AIRecommendation.student_profile_id == profile_id,
                   AIRecommendation.status == "active")
            .values(status="dismissed")
        )

        recs = []
        for ls in sorted(skills, key=lambda x: x.mastery_percentage)[:3]:
            if ls.mastery_percentage < 60 and ls.skill:
                recs.append(AIRecommendation(
                    student_profile_id=profile_id,
                    recommendation_type="revision",
                    title=f"Revise {ls.skill.name}",
                    description=f"Your {ls.skill.name} mastery is at {ls.mastery_percentage:.0f}%. "
                                f"Complete a targeted practice session.",
                    reason=f"Below 60% mastery — revision needed before advancing.",
                    evidence=[{"type": "assessment", "summary": f"{ls.mastery_percentage:.0f}% mastery"}],
                    priority="high" if ls.mastery_percentage < 40 else "medium",
                    action_path=f"/practice",
                    estimated_minutes=45,
                    created_at=datetime.now(timezone.utc),
                ))
        for r in recs:
            db.add(r)
        await db.commit()
