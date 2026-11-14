"""AnalyticsService: Student, mentor, and admin analytics."""
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import select, func, and_, case
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.profile import StudentProfile
from app.models.skill import Skill, LearnerSkill
from app.models.career import CareerRole
from app.models.assessment import AssessmentAttempt
from app.models.roadmap import LearningPath, RoadmapModule
from app.models.mentor import Mentor, MentorConnection, MentorDoubt
from app.models.practice import CodeSubmission, PracticeSession, CodingProblem
from app.models.project import ProjectSubmission
from app.models.analytics import LearningActivity


class AnalyticsService:
    @staticmethod
    async def get_student_analytics(db: AsyncSession, profile_id: int) -> Dict[str, Any]:
        # Readiness trend from archived + active learning paths
        lp_res = await db.execute(
            select(LearningPath)
            .where(LearningPath.student_profile_id == profile_id)
            .order_by(LearningPath.created_at)
        )
        paths = lp_res.scalars().all()
        readiness_trend = [
            {"date": p.created_at.isoformat(), "score": p.readiness_score, "version": p.version}
            for p in paths
        ]

        # Skill mastery
        ls_res = await db.execute(
            select(LearnerSkill).options(selectinload(LearnerSkill.skill)).where(
                LearnerSkill.student_profile_id == profile_id
            )
        )
        skills = ls_res.scalars().all()
        skill_mastery = [
            {"skill": ls.skill.name if ls.skill else "", "mastery": ls.mastery_percentage}
            for ls in skills
        ]

        # Assessment score trend
        assess_res = await db.execute(
            select(AssessmentAttempt)
            .where(AssessmentAttempt.student_profile_id == profile_id, AssessmentAttempt.submitted_at != None)
            .order_by(AssessmentAttempt.submitted_at)
        )
        attempts = assess_res.scalars().all()
        assessment_trend = [
            {"date": a.submitted_at.isoformat() if a.submitted_at else "", "mastery": a.mastery_percentage}
            for a in attempts
        ]

        # Coding stats
        cs_res = await db.execute(
            select(
                func.count(CodeSubmission.id).label("total"),
                func.sum(case((CodeSubmission.status == "passed", 1), else_=0)).label("solved"),
                func.avg(CodeSubmission.score).label("avg"),
            ).where(CodeSubmission.student_profile_id == profile_id)
        )
        cs = cs_res.one()
        total_subs = cs.total or 0
        solved = cs.solved or 0
        accuracy = round(float(cs.avg or 0), 1)

        # Practice streak (consecutive days with activity)
        act_res = await db.execute(
            select(LearningActivity)
            .where(LearningActivity.student_profile_id == profile_id)
            .order_by(LearningActivity.created_at.desc())
        )
        activities = act_res.scalars().all()
        streak = 0
        if activities:
            dates = set()
            for a in activities:
                d = a.created_at.date() if a.created_at else None
                if d:
                    dates.add(d)
            today = datetime.now(timezone.utc).date()
            for i in range(365):
                if (today - timedelta(days=i)) in dates:
                    streak += 1
                else:
                    break

        # Project portfolio score
        proj_res = await db.execute(
            select(func.avg(ProjectSubmission.evaluation_score)).where(
                ProjectSubmission.student_profile_id == profile_id,
                ProjectSubmission.status == "evaluated",
            )
        )
        portfolio_score = float(proj_res.scalar() or 0)

        # Weekly completion
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        weekly_act_res = await db.execute(
            select(LearningActivity).where(
                LearningActivity.student_profile_id == profile_id,
                LearningActivity.created_at >= week_ago,
            )
        )
        weekly_activities = weekly_act_res.scalars().all()
        weekly = {"total_activities": len(weekly_activities)}
        by_type = {}
        for a in weekly_activities:
            by_type[a.activity_type] = by_type.get(a.activity_type, 0) + 1
        weekly["by_type"] = by_type

        return {
            "readiness_trend": readiness_trend,
            "skill_mastery": skill_mastery,
            "assessment_score_trend": assessment_trend,
            "coding_accuracy": accuracy,
            "problems_solved": solved,
            "practice_streak": streak,
            "project_portfolio_score": round(portfolio_score, 1) if portfolio_score else None,
            "weekly_completion": weekly,
        }

    @staticmethod
    async def get_mentor_analytics(db: AsyncSession, mentor_id: int) -> Dict[str, Any]:
        # Mentee count
        mentee_res = await db.execute(
            select(func.count(MentorConnection.id)).where(
                MentorConnection.mentor_id == mentor_id,
                MentorConnection.status == "connected",
            )
        )
        mentee_count = mentee_res.scalar() or 0

        # Get all connected student profile ids
        conn_res = await db.execute(
            select(MentorConnection.student_profile_id).where(
                MentorConnection.mentor_id == mentor_id,
                MentorConnection.status == "connected",
            )
        )
        profile_ids = [r[0] for r in conn_res.all()]

        avg_readiness = 0.0
        at_risk = 0
        weak_skills = {}

        if profile_ids:
            # Average readiness
            lp_res = await db.execute(
                select(func.avg(LearningPath.readiness_score)).where(
                    LearningPath.student_profile_id.in_(profile_ids),
                    LearningPath.status == "active",
                )
            )
            avg_readiness = float(lp_res.scalar() or 0)

            # At-risk
            at_risk_res = await db.execute(
                select(func.count(func.distinct(LearningPath.student_profile_id))).where(
                    LearningPath.student_profile_id.in_(profile_ids),
                    LearningPath.status == "active",
                    LearningPath.readiness_score < 40,
                )
            )
            at_risk = at_risk_res.scalar() or 0

            # Common weak skills
            ls_res = await db.execute(
                select(LearnerSkill)
                .options(selectinload(LearnerSkill.skill))
                .where(
                    LearnerSkill.student_profile_id.in_(profile_ids),
                    LearnerSkill.mastery_percentage < 50,
                )
            )
            for ls in ls_res.scalars().all():
                name = ls.skill.name if ls.skill else "Unknown"
                weak_skills[name] = weak_skills.get(name, 0) + 1

        common_weak = [
            {"skill": k, "count": v} for k, v in sorted(weak_skills.items(), key=lambda x: -x[1])[:10]
        ]

        # Doubts answered
        doubt_res = await db.execute(
            select(func.count(MentorDoubt.id)).where(
                MentorDoubt.mentor_id == mentor_id,
                MentorDoubt.status.in_(["answered", "resolved"]),
            )
        )
        doubts_answered = doubt_res.scalar() or 0

        # Average response time
        answered_res = await db.execute(
            select(MentorDoubt).where(
                MentorDoubt.mentor_id == mentor_id,
                MentorDoubt.answered_at != None,
            )
        )
        answered = answered_res.scalars().all()
        avg_response = None
        if answered:
            total_hours = 0
            for d in answered:
                if d.answered_at and d.created_at:
                    diff = (d.answered_at - d.created_at).total_seconds() / 3600
                    total_hours += diff
            avg_response = round(total_hours / len(answered), 1)

        # Project reviews completed
        # (projects that have been evaluated for connected students)
        proj_res = await db.execute(
            select(func.count(ProjectSubmission.id)).where(
                ProjectSubmission.student_profile_id.in_(profile_ids),
                ProjectSubmission.status == "evaluated",
            )
        )
        project_reviews = proj_res.scalar() or 0

        return {
            "mentee_count": mentee_count,
            "avg_mentee_readiness": round(avg_readiness, 1),
            "at_risk_mentees": at_risk,
            "common_weak_skills": common_weak,
            "doubts_answered": doubts_answered,
            "avg_response_time_hours": avg_response,
            "project_reviews_completed": project_reviews,
        }

    @staticmethod
    async def get_admin_analytics(db: AsyncSession) -> Dict[str, Any]:
        # Platform skill gaps
        ls_res = await db.execute(
            select(
                Skill.name,
                func.avg(LearnerSkill.mastery_percentage).label("avg_mastery"),
                func.count(LearnerSkill.id).label("count"),
            )
            .join(LearnerSkill, LearnerSkill.skill_id == Skill.id)
            .group_by(Skill.id, Skill.name)
        )
        skill_gaps = [
            {"skill": r[0], "avg_mastery": round(float(r[1] or 0), 1), "students": r[2]}
            for r in ls_res.all()
            if float(r[1] or 0) < 70
        ]
        skill_gaps.sort(key=lambda x: x["avg_mastery"])

        # Career role distribution
        cr_res = await db.execute(
            select(
                CareerRole.name,
                func.count(StudentProfile.id).label("count"),
            )
            .join(StudentProfile, StudentProfile.target_role_id == CareerRole.id)
            .group_by(CareerRole.id, CareerRole.name)
        )
        role_dist = [{"role": r[0], "count": r[1]} for r in cr_res.all()]

        # Assessment performance by subject
        from app.models.assessment import Assessment, AssessmentAttempt
        ap_res = await db.execute(
            select(
                Skill.name,
                func.avg(AssessmentAttempt.mastery_percentage).label("avg_mastery"),
                func.count(AssessmentAttempt.id).label("attempts"),
            )
            .join(Assessment, AssessmentAttempt.assessment_id == Assessment.id)
            .join(Skill, Assessment.skill_id == Skill.id)
            .where(AssessmentAttempt.submitted_at != None)
            .group_by(Skill.id, Skill.name)
        )
        assess_perf = [
            {"skill": r[0], "avg_mastery": round(float(r[1] or 0), 1), "attempts": r[2]}
            for r in ap_res.all()
        ]

        # Coding problem analysis
        cp_res = await db.execute(
            select(
                CodingProblem.id,
                CodingProblem.title,
                CodingProblem.difficulty,
                func.count(CodeSubmission.id).label("submissions"),
                func.sum(func.case((CodeSubmission.status == "passed", 1), else_=0)).label("passed"),
            )
            .join(CodeSubmission, CodeSubmission.coding_problem_id == CodingProblem.id)
            .group_by(CodingProblem.id, CodingProblem.title, CodingProblem.difficulty)
        )
        coding_analysis = [
            {
                "title": r[1],
                "difficulty": r[2],
                "submissions": r[3],
                "pass_rate": round((r[4] / max(r[3], 1)) * 100, 1) if r[3] else 0,
            }
            for r in cp_res.all()
        ]

        # Project evaluation trends
        proj_res = await db.execute(
            select(
                func.date(ProjectSubmission.submitted_at).label("date"),
                func.count(ProjectSubmission.id).label("count"),
                func.avg(ProjectSubmission.evaluation_score).label("avg_score"),
            )
            .where(ProjectSubmission.status == "evaluated")
            .group_by(func.date(ProjectSubmission.submitted_at))
            .order_by(func.date(ProjectSubmission.submitted_at).desc())
            .limit(30)
        )
        project_trends = [
            {"date": str(r[0]), "count": r[1], "avg_score": round(float(r[2] or 0), 1)}
            for r in proj_res.all()
        ]

        # Mentor performance
        mentors_res = await db.execute(select(Mentor))
        mentors = mentors_res.scalars().all()
        mentor_perf = []
        for m in mentors:
            count_res = await db.execute(
                select(func.count(MentorConnection.id)).where(
                    MentorConnection.mentor_id == m.id,
                    MentorConnection.status == "connected",
                )
            )
            mc = count_res.scalar() or 0
            doubt_res = await db.execute(
                select(func.count(MentorDoubt.id)).where(
                    MentorDoubt.mentor_id == m.id,
                    MentorDoubt.status.in_(["answered", "resolved"]),
                )
            )
            doubts = doubt_res.scalar() or 0
            mentor_perf.append({
                "name": m.full_name,
                "student_count": mc,
                "doubts_answered": doubts,
                "is_active": m.is_active,
            })

        # At-risk learners
        at_risk_res = await db.execute(
            select(LearningPath)
            .options(selectinload(LearningPath.student_profile))
            .where(LearningPath.status == "active", LearningPath.readiness_score < 40)
        )
        at_risk_paths = at_risk_res.scalars().all()
        at_risk_list = [
            {
                "student_name": p.student_profile.full_name if p.student_profile else "",
                "readiness": round(p.readiness_score, 1),
                "career_role": p.career_role.name if p.career_role else "",
            }
            for p in at_risk_paths
        ]

        return {
            "platform_skill_gaps": skill_gaps[:10],
            "career_role_distribution": role_dist,
            "assessment_performance": assess_perf,
            "coding_problem_analysis": coding_analysis,
            "project_evaluation_trends": project_trends,
            "mentor_performance": mentor_perf,
            "at_risk_learners": at_risk_list,
        }
