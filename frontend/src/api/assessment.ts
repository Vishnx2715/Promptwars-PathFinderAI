import api from './axios';
import { AssessmentStartResponse, AssessmentResult } from '../types';

export interface AnswerItem {
  question_id: number;
  selected_option: string;
  time_taken_seconds?: number;
}

export const getAssessmentForSkill = async (skillId: number) => {
  const { data } = await api.get<{
    id: number;
    title: string;
    skill_id: number;
    skill_name: string;
    assessment_type: string;
    total_questions: number;
  }>(`/assessments/skill/${skillId}`);
  return data;
};

export const startAssessment = async (assessmentId: number): Promise<AssessmentStartResponse> => {
  const { data } = await api.post<AssessmentStartResponse>(`/assessments/${assessmentId}/start`);
  return data;
};

export const submitAssessment = async (
  attemptId: number,
  answers: AnswerItem[]
): Promise<AssessmentResult> => {
  const { data } = await api.post<AssessmentResult>(`/assessments/attempts/${attemptId}/submit`, {
    answers,
  });
  return data;
};

export const getAssessmentResult = async (attemptId: number): Promise<AssessmentResult> => {
  const { data } = await api.get<AssessmentResult>(`/assessments/attempts/${attemptId}/result`);
  return data;
};

