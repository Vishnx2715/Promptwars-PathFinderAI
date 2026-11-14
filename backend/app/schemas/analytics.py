from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class StudentAnalyticsResponse(BaseModel):
    readiness_trend: List[Dict[str, Any]] = []
    skill_mastery: List[Dict[str, Any]] = []
    assessment_score_trend: List[Dict[str, Any]] = []
    coding_accuracy: float = 0.0
    problems_solved: int = 0
    practice_streak: int = 0
    project_portfolio_score: Optional[float] = None
    weekly_completion: Dict[str, Any] = {}


class MentorAnalyticsResponse(BaseModel):
    mentee_count: int = 0
    avg_mentee_readiness: float = 0.0
    at_risk_mentees: int = 0
    common_weak_skills: List[Dict[str, Any]] = []
    doubts_answered: int = 0
    avg_response_time_hours: Optional[float] = None
    project_reviews_completed: int = 0


class AdminAnalyticsResponse(BaseModel):
    platform_skill_gaps: List[Dict[str, Any]] = []
    career_role_distribution: List[Dict[str, Any]] = []
    assessment_performance: List[Dict[str, Any]] = []
    coding_problem_analysis: List[Dict[str, Any]] = []
    project_evaluation_trends: List[Dict[str, Any]] = []
    mentor_performance: List[Dict[str, Any]] = []
    at_risk_learners: List[Dict[str, Any]] = []
