import api from './axios';
import { AdminOverview, AdminUser } from '../types';

export const getAdminOverview = async (): Promise<AdminOverview> => {
  const { data } = await api.get<AdminOverview>('/admin/overview');
  return data;
};

export const listUsers = async (role?: string): Promise<AdminUser[]> => {
  const { data } = await api.get<AdminUser[]>('/admin/users', { params: { role } });
  return data;
};

export const toggleUserActive = async (userId: number) => {
  const { data } = await api.put(`/admin/users/${userId}/toggle-active`);
  return data;
};

export const listMentors = async () => {
  const { data } = await api.get('/admin/mentors');
  return data;
};

export const createMentor = async (payload: { user_id: number; full_name: string; expertise: string }) => {
  const { data } = await api.post('/admin/mentors', payload);
  return data;
};

export const toggleMentorActive = async (mentorId: number) => {
  const { data } = await api.put(`/admin/mentors/${mentorId}/toggle-active`);
  return data;
};

export const listQuestions = async (params?: { skill_id?: number; subtopic?: string; difficulty?: string }) => {
  const { data } = await api.get('/admin/questions', { params });
  return data;
};

export const createQuestion = async (payload: any) => {
  const { data } = await api.post('/admin/questions', payload);
  return data;
};

export const updateQuestion = async (questionId: number, payload: any) => {
  const { data } = await api.put(`/admin/questions/${questionId}`, payload);
  return data;
};

export const deleteQuestion = async (questionId: number) => {
  const { data } = await api.delete(`/admin/questions/${questionId}`);
  return data;
};

export const listCodingProblems = async () => {
  const { data } = await api.get('/admin/coding-problems');
  return data;
};

export const createCodingProblem = async (payload: any) => {
  const { data } = await api.post('/admin/coding-problems', payload);
  return data;
};

export const updateCodingProblem = async (problemId: number, payload: any) => {
  const { data } = await api.put(`/admin/coding-problems/${problemId}`, payload);
  return data;
};

export const deleteCodingProblem = async (problemId: number) => {
  const { data } = await api.delete(`/admin/coding-problems/${problemId}`);
  return data;
};
