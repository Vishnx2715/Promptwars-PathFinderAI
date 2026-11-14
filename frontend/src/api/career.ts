import api from './axios';
import { CareerRole, RoleSkillRequirement, StudentProfile, GapAnalysisResponse } from '../types';

export const getCareerRoles = async (): Promise<CareerRole[]> => {
  const { data } = await api.get<CareerRole[]>('/careers');
  return data;
};

export const getCareerRequirements = async (careerRoleId: number): Promise<RoleSkillRequirement[]> => {
  const { data } = await api.get<RoleSkillRequirement[]>(`/careers/${careerRoleId}/requirements`);
  return data;
};

export const selectCareerRole = async (careerRoleId: number): Promise<StudentProfile> => {
  const { data } = await api.post<StudentProfile>('/careers/select', { career_role_id: careerRoleId });
  return data;
};

export const getSkillGapAnalysis = async (): Promise<GapAnalysisResponse> => {
  const { data } = await api.get<GapAnalysisResponse>('/skills/gap-analysis');
  return data;
};

