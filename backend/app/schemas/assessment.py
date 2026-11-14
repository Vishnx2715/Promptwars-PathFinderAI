from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class QuestionPublicResponse(BaseModel):
    id: int
    assessment_id: int
    skill_id: int
    subtopic: str
    question_text: str
    options: Dict[str, str]
    difficulty: str
    marks: int

    class Config:
        from_attributes = True


class AssessmentStartResponse(BaseModel):
    attempt_id: int
    assessment_id: int
    title: str
    skill_id: int
    skill_name: str
    total_questions: int
    questions: List[QuestionPublicResponse]


class AnswerSubmitItem(BaseModel):
    question_id: int
    selected_option: str
    time_taken_seconds: Optional[int] = None


class AssessmentSubmitRequest(BaseModel):
    answers: List[AnswerSubmitItem]


class QuestionBreakdownItem(BaseModel):
    question_id: int
    subtopic: str
    question_text: str
    selected_option: str
    correct_option: str
    is_correct: bool
    explanation: str


class WeakTopicItem(BaseModel):
    subtopic: str
    incorrect_count: int
    recommendation: str


class AssessmentResultResponse(BaseModel):
    attempt_id: int
    assessment_title: str
    skill_name: str
    score: float
    max_score: float
    mastery_percentage: float
    started_at: datetime
    submitted_at: Optional[datetime] = None
    breakdown: List[QuestionBreakdownItem] = []
    weak_topics: List[WeakTopicItem] = []
    recommended_resources: List[Dict[str, Any]] = []
    roadmap_changes: List[Dict[str, Any]] = []
    next_best_action: str
    mentor_message: Optional[str] = None

    class Config:
        from_attributes = True
