import api from './axios';
import { Roadmap, RoadmapResource } from '../types';

export const getActiveRoadmap = async (): Promise<Roadmap | null> => {
  const { data } = await api.get<Roadmap | null>('/roadmap/active');
  return data;
};

export const generateRoadmap = async (): Promise<Roadmap> => {
  const { data } = await api.post<Roadmap>('/roadmap/generate');
  return data;
};

export const replanRoadmap = async (): Promise<Roadmap> => {
  const { data } = await api.post<Roadmap>('/roadmap/replan');
  return data;
};

export const updateModuleStatus = async (moduleId: number, status: string): Promise<Roadmap> => {
  const { data } = await api.patch<Roadmap>(`/roadmap/modules/${moduleId}/status`, { status });
  return data;
};

export const toggleResourceCompletion = async (
  resourceId: number,
  isCompleted: boolean
): Promise<RoadmapResource> => {
  const { data } = await api.patch<RoadmapResource>(`/roadmap/resources/${resourceId}/complete`, {
    is_completed: isCompleted,
  });
  return data;
};

