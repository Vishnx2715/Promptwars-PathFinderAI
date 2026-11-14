import api from './axios';
import { StudentAnalytics, MentorAnalytics, AdminAnalytics } from '../types';

export const getStudentAnalytics = async (): Promise<StudentAnalytics> => {
  const { data } = await api.get<StudentAnalytics>('/analytics/student');
  return data;
};

export const getMentorAnalytics = async (): Promise<MentorAnalytics> => {
  const { data } = await api.get<MentorAnalytics>('/analytics/mentor');
  return data;
};

export const getAdminAnalytics = async (): Promise<AdminAnalytics> => {
  const { data } = await api.get<AdminAnalytics>('/analytics/admin');
  return data;
};

export const sendMentorChat = async (message: string) => {
  const { data } = await api.post('/mentor-chat/chat', { message });
  return data;
};
