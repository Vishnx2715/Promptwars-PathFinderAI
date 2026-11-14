from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.schemas.skill import LearnerSkillResponse, LearnerSkillCreate


class ProjectItem(BaseModel):
    title: str
    description: str
    tech_stack: List[str] = []
    github_url: Optional[str] = None


class CertificationItem(BaseModel):
    name: str
    issuer: str
    issue_date: Optional[str] = None
    credential_url: Optional[str] = None


class StudentProfileCreate(BaseModel):
    full_name: str
    education_level: Optional[str] = None
    experience_level: Optional[str] = None
    weekly_study_hours: int = Field(default=8, ge=1, le=100)
    learning_preference: Optional[str] = None
    skills: Optional[List[LearnerSkillCreate]] = []
    projects: Optional[List[ProjectItem]] = []
    certifications: Optional[List[CertificationItem]] = []


class StudentProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    education_level: Optional[str] = None
    experience_level: Optional[str] = None
    weekly_study_hours: Optional[int] = Field(default=None, ge=1, le=100)
    learning_preference: Optional[str] = None
    projects: Optional[List[ProjectItem]] = None
    certifications: Optional[List[CertificationItem]] = None


class StudentProfileResponse(BaseModel):
    id: int
    user_id: int
    full_name: str
    education_level: Optional[str] = None
    experience_level: Optional[str] = None
    weekly_study_hours: int
    learning_preference: Optional[str] = None
    target_role_id: Optional[int] = None
    target_role_name: Optional[str] = None
    career_goal_changed_at: Optional[datetime] = None
    projects: Optional[List[Dict[str, Any]]] = []
    certifications: Optional[List[Dict[str, Any]]] = []
    learner_skills: List[LearnerSkillResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
