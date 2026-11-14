import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { RoleRoute } from './components/RoleRoute';
import { Layout } from './components/Layout';

// Existing Section 1 Pages
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { Onboarding } from './pages/Onboarding';
import { Dashboard } from './pages/Dashboard';
import { CareerGoal } from './pages/CareerGoal';
import { SkillGap } from './pages/SkillGap';
import { Roadmap } from './pages/Roadmap';
import { Assessment } from './pages/Assessment';

// Section 2 Student Pages
import { PracticeLab } from './pages/student/PracticeLab';
import { PracticeProblem } from './pages/student/PracticeProblem';
import { MockTests } from './pages/student/MockTests';
import { ProjectSubmission } from './pages/student/ProjectSubmission';
import { MentorConnect } from './pages/student/MentorConnect';
import { Doubts } from './pages/student/Doubts';
import { AiMentor } from './pages/student/AiMentor';

// Section 2 Mentor Pages
import { MentorDashboard } from './pages/mentor/MentorDashboard';
import { MenteeDetail } from './pages/mentor/MenteeDetail';
import { DoubtQueue } from './pages/mentor/DoubtQueue';
import { ProjectReviews } from './pages/mentor/ProjectReviews';

// Section 2 Admin Pages
import { AdminDashboard } from './pages/admin/AdminDashboard';
import { UserManagement } from './pages/admin/UserManagement';
import { MentorManagement } from './pages/admin/MentorManagement';
import { QuestionBank } from './pages/admin/QuestionBank';
import { CodingProblemManagement } from './pages/admin/CodingProblemManagement';
import { AdminAnalytics } from './pages/admin/AdminAnalytics';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      staleTime: 1000 * 60 * 5,
      retry: 1,
    },
  },
});

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            {/* Public Auth Routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />

            {/* Student Routes */}
            <Route path="/dashboard" element={<ProtectedRoute><Layout><Dashboard /></Layout></ProtectedRoute>} />
            <Route path="/onboarding" element={<ProtectedRoute><Layout><Onboarding /></Layout></ProtectedRoute>} />
            <Route path="/career-goal" element={<ProtectedRoute><Layout><CareerGoal /></Layout></ProtectedRoute>} />
            <Route path="/skill-gap" element={<ProtectedRoute><Layout><SkillGap /></Layout></ProtectedRoute>} />
            <Route path="/roadmap" element={<ProtectedRoute><Layout><Roadmap /></Layout></ProtectedRoute>} />
            <Route path="/assessment" element={<ProtectedRoute><Layout><Assessment /></Layout></ProtectedRoute>} />
            <Route path="/assessment/:assessmentId" element={<ProtectedRoute><Layout><Assessment /></Layout></ProtectedRoute>} />
            <Route path="/assessments" element={<ProtectedRoute><Layout><MockTests /></Layout></ProtectedRoute>} />
            <Route path="/practice" element={<ProtectedRoute><Layout><PracticeLab /></Layout></ProtectedRoute>} />
            <Route path="/practice/:problemId" element={<ProtectedRoute><Layout><PracticeProblem /></Layout></ProtectedRoute>} />
            <Route path="/projects" element={<ProtectedRoute><Layout><ProjectSubmission /></Layout></ProtectedRoute>} />
            <Route path="/ai-mentor" element={<ProtectedRoute><Layout><AiMentor /></Layout></ProtectedRoute>} />
            <Route path="/my-mentor" element={<ProtectedRoute><Layout><MentorConnect /></Layout></ProtectedRoute>} />
            <Route path="/doubts" element={<ProtectedRoute><Layout><Doubts /></Layout></ProtectedRoute>} />

            {/* Mentor Routes */}
            <Route path="/mentor/dashboard" element={<RoleRoute roles={['mentor', 'admin']}><Layout><MentorDashboard /></Layout></RoleRoute>} />
            <Route path="/mentor/mentees/:profileId" element={<RoleRoute roles={['mentor', 'admin']}><Layout><MenteeDetail /></Layout></RoleRoute>} />
            <Route path="/mentor/doubts" element={<RoleRoute roles={['mentor', 'admin']}><Layout><DoubtQueue /></Layout></RoleRoute>} />
            <Route path="/mentor/projects" element={<RoleRoute roles={['mentor', 'admin']}><Layout><ProjectReviews /></Layout></RoleRoute>} />

            {/* Admin Routes */}
            <Route path="/admin/dashboard" element={<RoleRoute roles={['admin']}><Layout><AdminDashboard /></Layout></RoleRoute>} />
            <Route path="/admin/users" element={<RoleRoute roles={['admin']}><Layout><UserManagement /></Layout></RoleRoute>} />
            <Route path="/admin/mentors" element={<RoleRoute roles={['admin']}><Layout><MentorManagement /></Layout></RoleRoute>} />
            <Route path="/admin/questions" element={<RoleRoute roles={['admin']}><Layout><QuestionBank /></Layout></RoleRoute>} />
            <Route path="/admin/coding-problems" element={<RoleRoute roles={['admin']}><Layout><CodingProblemManagement /></Layout></RoleRoute>} />
            <Route path="/admin/analytics" element={<RoleRoute roles={['admin']}><Layout><AdminAnalytics /></Layout></RoleRoute>} />

            {/* Default fallback */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
};

export default App;
