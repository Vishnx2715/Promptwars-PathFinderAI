import api from './axios';
import { DoubtItem } from '../types';

export const submitDoubt = async (payload: {
  subject: string;
  question: string;
  skill_id?: number;
  roadmap_module_id?: number;
}): Promise<DoubtItem> => {
  const { data } = await api.post<DoubtItem>('/doubts/submit', payload);
  return data;
};

export const getMyDoubts = async (): Promise<DoubtItem[]> => {
  const { data } = await api.get<DoubtItem[]>('/doubts/');
  return data;
};

export const resolveDoubt = async (doubtId: number) => {
  const { data } = await api.put(`/doubts/${doubtId}/resolve`);
  return data;
};

export const getMentorDoubts = async (): Promise<DoubtItem[]> => {
  const { data } = await api.get<DoubtItem[]>('/doubts/mentor');
  return data;
};

export const answerDoubt = async (doubtId: number, payload: {
  mentor_response: string;
  status: string;
}) => {
  const { data } = await api.put(`/doubts/${doubtId}/answer`, payload);
  return data;
};
