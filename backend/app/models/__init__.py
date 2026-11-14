from app.models.user import User
from app.models.profile import StudentProfile
from app.models.skill import Skill, LearnerSkill
from app.models.career import CareerRole, RoleSkillRequirement
from app.models.assessment import Assessment, Question, AssessmentAttempt, AssessmentResponse
from app.models.roadmap import LearningPath, RoadmapModule, RoadmapResource
from app.models.mentor import Mentor, MentorConnection, MentorFeedback, MentorDoubt
from app.models.practice import CodingProblem, CodeSubmission, PracticeSession
from app.models.project import ProjectSubmission, ProjectRubric
from app.models.analytics import LearningActivity
# Section 3
from app.models.portfolio import PortfolioProfile, SkillDecayAlert, Campus, LeaderboardEntry
from app.models.notification import Notification, AIRecommendation
from app.models.interview import InterviewSession, InterviewQuestion, InterviewResponse
from app.models.career_intelligence import ResumeUpload, JobDescription, JobMatch, CareerRecommendation
from app.models.study_plan import WeeklyStudyPlan, StudyTask, CareerReadinessReport
from app.models.college import (
    CollegeCourse, StudentCourseEnrollment, CourseSchedule,
    CollegeAssignment, AssignmentSubmission, CollegeAnnouncement,
    AcademicRecord, AcademicRiskAlert,
)

__all__ = [
    "User", "StudentProfile", "Skill", "LearnerSkill",
    "CareerRole", "RoleSkillRequirement",
    "Assessment", "Question", "AssessmentAttempt", "AssessmentResponse",
    "LearningPath", "RoadmapModule", "RoadmapResource",
    "Mentor", "MentorConnection", "MentorFeedback", "MentorDoubt",
    "CodingProblem", "CodeSubmission", "PracticeSession",
    "ProjectSubmission", "ProjectRubric", "LearningActivity",
    # Section 3
    "PortfolioProfile", "SkillDecayAlert", "Campus", "LeaderboardEntry",
    "Notification", "AIRecommendation",
    "InterviewSession", "InterviewQuestion", "InterviewResponse",
    "ResumeUpload", "JobDescription", "JobMatch", "CareerRecommendation",
    "WeeklyStudyPlan", "StudyTask", "CareerReadinessReport",
    "CollegeCourse", "StudentCourseEnrollment", "CourseSchedule",
    "CollegeAssignment", "AssignmentSubmission", "CollegeAnnouncement",
    "AcademicRecord", "AcademicRiskAlert",
]
