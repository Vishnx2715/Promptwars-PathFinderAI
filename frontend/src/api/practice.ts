import api from './axios';
import {
  CodingProblemListItem,
  CodingProblemDetail,
  CodeSubmissionResponse,
  SubmissionHistoryItem,
} from '../types';

export const listProblems = async (params?: {
  language?: string;
  skill_id?: number;
  subtopic?: string;
  difficulty?: string;
  status?: string;
}): Promise<CodingProblemListItem[]> => {
  const { data } = await api.get<CodingProblemListItem[]>('/practice/problems', { params });
  return data;
};

export const getProblem = async (problemId: number): Promise<CodingProblemDetail> => {
  const { data } = await api.get<CodingProblemDetail>(`/practice/problems/${problemId}`);
  return data;
};

export const runSampleTests = async (
  problemId: number,
  code: string,
  language: string
): Promise<{ results: any[] }> => {
  const { data } = await api.post(`/practice/problems/${problemId}/run`, { code, language, problem_id: problemId });
  return data;
};

export const submitSolution = async (
  problemId: number,
  code: string,
  language: string,
  frontendResults?: any[]
): Promise<CodeSubmissionResponse> => {
  const { data } = await api.post<CodeSubmissionResponse>(`/practice/problems/${problemId}/submit`, {
    code,
    language,
    problem_id: problemId,
    frontend_results: frontendResults,
  });
  return data;
};

export const getSubmissionHistory = async (problemId: number): Promise<SubmissionHistoryItem[]> => {
  const { data } = await api.get<SubmissionHistoryItem[]>(`/practice/problems/${problemId}/history`);
  return data;
};

export const getNextRecommended = async (problemId: number) => {
  const { data } = await api.get(`/practice/problems/${problemId}/next`);
  return data;
};
