from typing import Optional, List
from pydantic import BaseModel, Field


class RoleSkillRequirementResponse(BaseModel):
    id: int
    career_role_id: int
    skill_id: int
    skill_name: str
    category: str
    required_level: int
    weight: int
    is_prerequisite_for: Optional[str] = None
    prerequisite_skill_id: Optional[int] = None
    prerequisite_skill_name: Optional[str] = None

    class Config:
        from_attributes = True


class CareerRoleResponse(BaseModel):
    id: int
    name: str
    description: str
    is_active: bool
    requirements: List[RoleSkillRequirementResponse] = []

    class Config:
        from_attributes = True


class CareerGoalSelect(BaseModel):
    career_role_id: int
