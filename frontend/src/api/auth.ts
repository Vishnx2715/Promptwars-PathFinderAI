import api from './axios';
import { User } from '../types';

export interface RegisterPayload {
  email: string;
  username: string;
  password: string;
  confirm_password: string;
}

export interface LoginPayload {
  username_or_email: string;
  password: string;
}

export interface AuthResponse {
  message: string;
  user: User;
}

export const registerUser = async (payload: RegisterPayload): Promise<AuthResponse> => {
  const { data } = await api.post<AuthResponse>('/auth/register', payload);
  return data;
};

export const loginUser = async (payload: LoginPayload): Promise<AuthResponse> => {
  const { data } = await api.post<AuthResponse>('/auth/login', payload);
  return data;
};

export const logoutUser = async (): Promise<{ message: string }> => {
  const { data } = await api.post<{ message: string }>('/auth/logout');
  return data;
};

export const getCurrentUser = async (): Promise<User> => {
  const { data } = await api.get<User>('/auth/me');
  return data;
};

