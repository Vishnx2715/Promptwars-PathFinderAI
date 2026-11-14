"""Weekly study planner service."""
from datetime import datetime, timezone, date, timedelta
from typing import List, Dict, Any, Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.study_plan import WeeklyStudyPlan, StudyTask
from app.models.profile import StudentProfile
from app.models.skill import LearnerSkill
from app.models.roadmap import LearningPath, RoadmapModule
from app.models.college import CollegeAssignment, StudentCourseEnrollment
from app.agents.study_planner_agent import StudyPlannerAgent
from app.services.notification_service import NotificationService


class StudyPlannerService:
    @staticmethod
    async def get_or_create_plan(db: AsyncSession, profile_id: int) -> Dict[str, Any]:
        """Return current week's plan or generate a new one."""
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

        res = await db.execute(
            select(WeeklyStudyPlan)
            .options(selectinload(WeeklyStudyPlan.tasks))
            .where(
                WeeklyStudyPlan.student_profile_id == profile_id,
                WeeklyStudyPlan.week_start_date == week_start,
            )
        )
        plan = res.scalar_one_or_none()
        if plan:
            return StudyPlannerService._format(plan)
        return await StudyPlannerService.generate_plan(db, profile_id)

    @staticmethod
    async def generate_plan(db: AsyncSession, profile_id: int) -> Dict[str, Any]:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())

        # Load profile context
        prof_res = await db.execute(
            select(StudentProfile)
            .options(
                selectinload(StudentProfile.learner_skills).selectinload(LearnerSkill.skill),
                selectinload(StudentProfile.target_role),
            )
            .where(StudentProfile.id == profile_id)
        )
        profile = prof_res.scalar_one_or_none()
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found.")

        weekly_hours = profile.weekly_study_hours or 8
        career_role = profile.target_role.name if profile.target_role else "General"

        # Weak areas
        weak = [ls.skill.name for ls in profile.learner_skills
                if ls.mastery_percentage < 60 and ls.skill][:5]

        # Active roadmap
        lp_res = await db.execute(
            select(LearningPath)
            .options(selectinload(LearningPath.modules).selectinload(RoadmapModule.skill))
            .where(LearningPath.student_profile_id == profile_id, LearningPath.status == "active")
        )
        lp = lp_res.scalar_one_or_none()
        roadmap_modules = []
        if lp:
            for m in sorted(lp.modules, key=lambda x: (x.phase, x.order_index)):
                if m.status in ("available", "in_progress", "needs_revision"):
                    roadmap_modules.append({
                        "title": m.title, "status": m.status,
                        "skill_name": m.skill.name if m.skill else "", "id": m.id
                    })

        # Upcoming college assignments
        upcoming_assignments: List[Dict[str, Any]] = []
        enroll_res = await db.execute(
            select(StudentCourseEnrollment)
            .where(StudentCourseEnrollment.student_profile_id == profile_id,
                   StudentCourseEnrollment.status == "active")
        )
        enrollments = enroll_res.scalars().all()
        for e in enrollments:
            assign_res = await db.execute(
                select(CollegeAssignment)
                .where(CollegeAssignment.college_course_id == e.college_course_id)
            )
            for a in assign_res.scalars().all():
                if a.due_date and (a.due_date.date() if hasattr(a.due_date, 'date') else a.due_date) >= today:
                    upcoming_assignments.append({"title": a.title, "due": str(a.due_date)[:10], "id": a.id})

        # Generate plan
        plan_data = await StudyPlannerAgent.run(
            str(week_start), weekly_hours, weak, roadmap_modules,
            career_role, upcoming_assignments[:5]
        )

        # Save plan
        plan = WeeklyStudyPlan(
            student_profile_id=profile_id,
            career_role_id=profile.target_role_id,
            week_start_date=week_start,
            weekly_hours=weekly_hours,
            planned_hours=plan_data.get("planned_hours", 0.0),
            plan=plan_data,
            status="active",
            created_at=datetime.now(timezone.utc),
        )
        db.add(plan)
        await db.flush()

        for t in plan_data.get("tasks", []):
            task = StudyTask(
                weekly_study_plan_id=plan.id,
                title=t.get("title", ""),
                description=t.get("description", ""),
                estimated_minutes=t.get("estimated_minutes", 30),
                task_type=t.get("task_type", "resource"),
                day=t.get("day"),
                status="pending",
            )
            db.add(task)

        await db.commit()
        await db.refresh(plan)

        # Notify
        try:
            await NotificationService.create(
                db, user_id=profile.user_id,
                title="Weekly Study Plan Ready",
                message=f"Your week of {week_start} plan has {len(plan_data.get('tasks', []))} tasks.",
                notification_type="system",
                reference_path="/weekly-plan",
            )
        except Exception:
            pass

        return StudyPlannerService._format(plan)

    @staticmethod
    async def complete_task(db: AsyncSession, profile_id: int, task_id: int) -> Dict[str, Any]:
        res = await db.execute(
            select(StudyTask)
            .join(WeeklyStudyPlan)
            .where(StudyTask.id == task_id, WeeklyStudyPlan.student_profile_id == profile_id)
        )
        task = res.scalar_one_or_none()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found.")
        task.status = "completed"
        task.completed_at = datetime.now(timezone.utc)

        # Update plan hours
        plan_res = await db.execute(select(WeeklyStudyPlan).where(WeeklyStudyPlan.id == task.weekly_study_plan_id))
        plan = plan_res.scalar_one_or_none()
        if plan:
            plan.completed_hours += task.estimated_minutes / 60.0

        await db.commit()
        return {"task_id": task_id, "status": "completed"}

    @staticmethod
    def _format(plan: WeeklyStudyPlan) -> Dict[str, Any]:
        tasks = []
        for t in sorted(plan.tasks, key=lambda x: (x.day or "Monday", x.id)):
            tasks.append({
                "id": t.id, "title": t.title, "description": t.description,
                "estimated_minutes": t.estimated_minutes, "task_type": t.task_type,
                "day": t.day, "status": t.status,
                "completed_at": t.completed_at.isoformat() if t.completed_at else None,
            })
        return {
            "id": plan.id, "week_start_date": str(plan.week_start_date),
            "weekly_hours": plan.weekly_hours, "planned_hours": plan.planned_hours,
            "completed_hours": plan.completed_hours, "tasks": tasks,
            "plan_meta": plan.plan or {}, "status": plan.status,
        }
