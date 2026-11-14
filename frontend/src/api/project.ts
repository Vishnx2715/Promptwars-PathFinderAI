import api from './axios';
import { ProjectListItem, ProjectDetail } from '../types';

export const submitProject = async (
  formData: FormData
): Promise<{ message: string; id: number; status: string }> => {
  const { data } = await api.post('/projects/submit', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
};

export const listProjects = async (): Promise<ProjectListItem[]> => {
  const { data } = await api.get<ProjectListItem[]>('/projects/');
  return data;
};

export const getProjectDetail = async (projectId: number): Promise<ProjectDetail> => {
  const { data } = await api.get<ProjectDetail>(`/projects/${projectId}`);
  return data;
};

export const getStudentProjects = async (profileId: number): Promise<ProjectListItem[]> => {
  const { data } = await api.get<ProjectListItem[]>(`/projects/student/${profileId}`);
  return data;
};
