export interface User {
  id: number;
  email: string;
  username: string;
  role: 'student' | 'mentor' | 'admin';
  is_active: boolean;
  created_at: string;
}

export interface LearnerSkill {
  id: number;
  skill_id: number;
  skill_name: string;
  category: string;
  self_reported_level: number;
  verified_level: number;
  evidence_type: 'self_report' | 'assessment' | 'project' | 'mentor';
  mastery_percentage: number;
  last_assessed_at?: string | null;
}

export interface ProjectItem {
  title: string;
  description: string;
  tech_stack: string[];
  github_url?: string;
}

export interface CertificationItem {
  name: string;
  issuer: string;
  issue_date?: string;
  credential_url?: string;
}

export interface StudentProfile {
  id: number;
  user_id: number;
  full_name: string;
  education_level?: string | null;
  experience_level?: string | null;
  weekly_study_hours: number;
  learning_preference?: string | null;
  target_role_id?: number | null;
  target_role_name?: string | null;
  career_goal_changed_at?: string | null;
  projects?: ProjectItem[];
  certifications?: CertificationItem[];
  learner_skills: LearnerSkill[];
  created_at: string;
  updated_at: string;
}

export interface RoleSkillRequirement {
  id: number;
  career_role_id: number;
  skill_id: number;
  skill_name: string;
  category: string;
  required_level: number;
  weight: number;
  is_prerequisite_for?: string | null;
  prerequisite_skill_id?: number | null;
  prerequisite_skill_name?: string | null;
}

export interface CareerRole {
  id: number;
  name: string;
  description: string;
  is_active: boolean;
  requirements: RoleSkillRequirement[];
}

export interface StrengthItem {
  skill: string;
  mastery: number;
  reason: string;
}

export interface GapItem {
  skill: string;
  current_mastery: number;
  required_level: number;
  priority: 'critical' | 'high' | 'medium' | 'low';
  blocking_skills: string[];
  reason: string;
}

export interface GapAnalysisResponse {
  readiness_score: number;
  strengths: StrengthItem[];
  gaps: GapItem[];
  next_best_action: string;
  summary: string;
}

export interface RoadmapResource {
  id: number;
  roadmap_module_id: number;
  title: string;
  url: string;
  resource_type: 'course' | 'documentation' | 'video' | 'exercise' | 'project';
  difficulty: string;
  estimated_minutes: number;
  reason: string;
  is_completed: boolean;
}

export interface RoadmapModule {
  id: number;
  learning_path_id: number;
  title: string;
  description: string;
  skill_id: number;
  skill_name: string;
  phase: number;
  order_index: number;
  estimated_hours: number;
  status: 'locked' | 'available' | 'in_progress' | 'completed' | 'needs_revision';
  prerequisite_module_id?: number | null;
  prerequisite_module_title?: string | null;
  min_mastery_to_unlock: number;
  reason?: string | null;
  resources: RoadmapResource[];
}

export interface Roadmap {
  id: number;
  student_profile_id: number;
  career_role_id: number;
  career_role_name: string;
  version: number;
  status: 'active' | 'archived';
  readiness_score: number;
  replan_reason?: string | null;
  modules: RoadmapModule[];
  created_at: string;
}

export interface QuestionPublic {
  id: number;
  assessment_id: number;
  skill_id: number;
  subtopic: string;
  question_text: string;
  options: Record<string, string>;
  difficulty: string;
  marks: number;
}

export interface AssessmentStartResponse {
  attempt_id: number;
  assessment_id: number;
  title: string;
  skill_id: number;
  skill_name: string;
  total_questions: number;
  questions: QuestionPublic[];
}

export interface QuestionBreakdownItem {
  question_id: number;
  subtopic: string;
  question_text: string;
  selected_option: string;
  correct_option: string;
  is_correct: boolean;
  explanation: string;
}

export interface WeakTopicItem {
  subtopic: string;
  incorrect_count: number;
  recommendation: string;
}

export interface RoadmapChange {
  module_title: string;
  action: string;
  reason: string;
}

export interface AssessmentResult {
  attempt_id: number;
  assessment_title: string;
  skill_name: string;
  score: number;
  max_score: number;
  mastery_percentage: number;
  started_at: string;
  submitted_at?: string;
  breakdown: QuestionBreakdownItem[];
  weak_topics: WeakTopicItem[];
  recommended_resources: any[];
  roadmap_changes: RoadmapChange[];
  next_best_action: string;
  mentor_message?: string;
}

// ---- Section 2 Types ----

export interface CodingProblemListItem {
  id: number;
  title: string;
  language: string;
  skill_id: number;
  skill_name: string;
  subtopic: string;
  difficulty: string;
  is_solved: boolean;
  is_attempted: boolean;
  acceptance_rate: number;
  total_submissions: number;
}

export interface CodingProblemDetail {
  id: number;
  title: string;
  description: string;
  language: string;
  skill_id: number;
  skill_name: string;
  subtopic: string;
  difficulty: string;
  starter_code: string;
  function_name: string;
  examples: { input: string; output: string; explanation?: string }[];
  constraints?: string | null;
  visible_test_cases: { name: string; input: string; expected_output: string; is_hidden: boolean }[];
}

export interface TestResultItem {
  name: string;
  passed: boolean;
  expected: string;
  actual: string;
  is_hidden: boolean;
}

export interface CodeSubmissionResponse {
  id: number;
  coding_problem_id: number;
  language: string;
  status: string;
  score: number;
  tests_passed: number;
  tests_total: number;
  runtime_ms?: number | null;
  ai_review?: any;
  submitted_at: string;
  test_results: TestResultItem[];
  mastery_change?: number | null;
  mentor_alert: boolean;
}

export interface SubmissionHistoryItem {
  id: number;
  status: string;
  score: number;
  tests_passed: number;
  tests_total: number;
  submitted_at: string;
}

export interface ProjectListItem {
  id: number;
  title: string;
  project_type: string;
  status: string;
  evaluation_score?: number | null;
  submitted_at: string;
  evaluated_at?: string | null;
}

export interface ProjectDetail {
  id: number;
  title: string;
  project_type: string;
  description: string;
  github_url?: string | null;
  live_url?: string | null;
  status: string;
  evaluation_score?: number | null;
  evaluation_report?: any;
  submitted_at: string;
  evaluated_at?: string | null;
}

export interface MentorConnectResponse {
  connected: boolean;
  mentor_name: string;
  mentor_expertise: string;
  status: string;
}

export interface MentorConnection {
  id: number;
  mentor_name: string;
  mentor_expertise: string;
  status: string;
  connected_at: string;
}

export interface MentorProfileResponse {
  id: number;
  full_name: string;
  expertise: string;
  mentor_code: string;
  is_active: boolean;
  connected_students: number;
}

export interface MenteeSummary {
  profile_id: number;
  student_name: string;
  career_goal?: string | null;
  readiness_score: number;
  roadmap_progress_pct: number;
  last_active?: string | null;
  risk_level: string;
  pending_doubts: number;
  pending_project_reviews: number;
}

export interface MenteeDetail {
  profile_id: number;
  student_name: string;
  career_goal?: string | null;
  readiness_score: number;
  roadmap_modules: { id: number; title: string; status: string; skill_name: string; phase: number; reason?: string }[];
  learner_skills: { skill_name: string; mastery: number; verified_level: number; evidence_type: string }[];
  assessment_history: { id: number; title: string; skill: string; mastery: number; submitted_at?: string }[];
  coding_stats: { total_submissions: number; solved: number; accuracy: number };
  project_submissions: { id: number; title: string; status: string; score?: number; submitted_at: string }[];
  weak_areas: string[];
  ai_insight?: {
    student_name: string;
    readiness_score: number;
    risk_level: string;
    primary_blocker: string;
    weak_areas: string[];
    strengths: string[];
    recommended_mentor_action: string;
    ai_summary: string;
  } | null;
}

export interface MentorFeedback {
  id: number;
  mentor_id: number;
  feedback_type: string;
  comment: string;
  recommended_action?: string | null;
  created_at: string;
}

export interface DoubtItem {
  id: number;
  subject: string;
  question: string;
  ai_draft_answer?: string | null;
  mentor_response?: string | null;
  status: string;
  created_at: string;
  answered_at?: string | null;
  student_name?: string;
  student_profile_id?: number;
}

export interface AdminOverview {
  total_students: number;
  total_mentors: number;
  active_learning_paths: number;
  total_assessments_completed: number;
  total_coding_submissions: number;
  total_projects_submitted: number;
  average_readiness_score: number;
  at_risk_student_count: number;
}

export interface AdminUser {
  id: number;
  email: string;
  username: string;
  role: string;
  is_active: boolean;
  created_at: string;
  profile_name?: string | null;
  mentor_code?: string | null;
}

export interface MentorChatResponse {
  answer: string;
  next_action: string;
  suggests_mentor: boolean;
  related_module?: string | null;
}

export interface StudentAnalytics {
  readiness_trend: { date: string; score: number; version: number }[];
  skill_mastery: { skill: string; mastery: number }[];
  assessment_score_trend: { date: string; mastery: number }[];
  coding_accuracy: number;
  problems_solved: number;
  practice_streak: number;
  project_portfolio_score?: number | null;
  weekly_completion: { total_activities: number; by_type: Record<string, number> };
}

export interface MentorAnalytics {
  mentee_count: number;
  avg_mentee_readiness: number;
  at_risk_mentees: number;
  common_weak_skills: { skill: string; count: number }[];
  doubts_answered: number;
  avg_response_time_hours?: number | null;
  project_reviews_completed: number;
}

export interface AdminAnalytics {
  platform_skill_gaps: { skill: string; avg_mastery: number; students: number }[];
  career_role_distribution: { role: string; count: number }[];
  assessment_performance: { skill: string; avg_mastery: number; attempts: number }[];
  coding_problem_analysis: { title: string; difficulty: string; submissions: number; pass_rate: number }[];
  project_evaluation_trends: { date: string; count: number; avg_score: number }[];
  mentor_performance: { name: string; student_count: number; doubts_answered: number; is_active: boolean }[];
  at_risk_learners: { student_name: string; readiness: number; career_role: string }[];
}

