import api from './axios';
import { StudentProfile } from '../types';

export interface OnboardingPayload {
  full_name: string;
  education_level?: string;
  experience_level?: string;
  weekly_study_hours: number;
  learning_preference?: string;
  skills?: { skill_name?: string; skill_id?: number; level: number }[];
  projects?: { title: string; description: string; tech_stack: string[]; github_url?: string }[];
  certifications?: { name: string; issuer: string; issue_date?: string; credential_url?: string }[];
}

export const getProfile = async (): Promise<StudentProfile> => {
  const { data } = await api.get<StudentProfile>('/profile/me');
  return data;
};

export const updateProfile = async (payload: Partial<OnboardingPayload>): Promise<StudentProfile> => {
  const { data } = await api.put<StudentProfile>('/profile/me', payload);
  return data;
};

export const saveOnboarding = async (payload: OnboardingPayload): Promise<StudentProfile> => {
  const { data } = await api.post<StudentProfile>('/profile', payload);
  return data;
};

export const addOrUpdateSkill = async (payload: { skill_name?: string; skill_id?: number; level: number }): Promise<StudentProfile> => {
  const { data } = await api.post<StudentProfile>('/profile/skills', payload);
  return data;
};

export const deleteSkill = async (skillId: number): Promise<StudentProfile> => {
  const { data } = await api.delete<StudentProfile>(`/profile/skills/${skillId}`);
  return data;
};

