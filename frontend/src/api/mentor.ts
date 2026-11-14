import api from './axios';
import {
  MentorConnectResponse,
  MentorConnection,
  MentorProfileResponse,
  MenteeSummary,
  MenteeDetail,
  MentorFeedback,
} from '../types';

// Student endpoints
export const connectToMentor = async (mentorCode: string): Promise<MentorConnectResponse> => {
  const { data } = await api.post<MentorConnectResponse>('/mentors/connect', { mentor_code: mentorCode });
  return data;
};

export const getMyConnections = async (): Promise<MentorConnection[]> => {
  const { data } = await api.get<MentorConnection[]>('/mentors/connections');
  return data;
};

export const disconnectMentor = async (connectionId: number) => {
  const { data } = await api.delete(`/mentors/connections/${connectionId}`);
  return data;
};

export const getMyFeedback = async (): Promise<MentorFeedback[]> => {
  const { data } = await api.get<MentorFeedback[]>('/mentors/feedback');
  return data;
};

// Mentor endpoints
export const getMentorProfile = async (): Promise<MentorProfileResponse> => {
  const { data } = await api.get<MentorProfileResponse>('/mentors/profile');
  return data;
};

export const getMentorDashboard = async () => {
  const { data } = await api.get('/mentors/dashboard');
  return data;
};

export const getMentees = async (): Promise<MenteeSummary[]> => {
  const { data } = await api.get<MenteeSummary[]>('/mentors/mentees');
  return data;
};

export const getMenteeDetail = async (profileId: number): Promise<MenteeDetail> => {
  const { data } = await api.get<MenteeDetail>(`/mentors/mentees/${profileId}`);
  return data;
};

export const addMentorFeedback = async (payload: {
  student_profile_id: number;
  feedback_type: string;
  comment: string;
  recommended_action?: string;
  roadmap_module_id?: number;
}) => {
  const { data } = await api.post('/mentors/feedback', payload);
  return data;
};

export const assignAssessment = async (payload: {
  student_profile_id: number;
  skill_id: number;
}) => {
  const { data } = await api.post('/mentors/assign-assessment', payload);
  return data;
};

export const regenerateMentorCode = async () => {
  const { data } = await api.post('/mentors/regenerate-code');
  return data;
};

export const createMentor = async (payload: {
  user_id: number;
  full_name: string;
  expertise: string;
}) => {
  const { data } = await api.post('/mentors/create', payload);
  return data;
};
