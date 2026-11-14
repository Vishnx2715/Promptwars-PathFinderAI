import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getActiveRoadmap } from '../api/roadmap';
import { getSkillGapAnalysis } from '../api/career';
import { ReadinessGauge } from '../components/ReadinessGauge';
import { NextActionCard } from '../components/NextActionCard';
import { 
  Sparkles, 
  Target, 
  Map, 
  BarChart3, 
  Award, 
  Clock, 
  ArrowRight, 
  CheckCircle2, 
  Layers,
  Calendar,
  Compass
} from 'lucide-react';

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { user, profile } = useAuth();

  // Queries
  const { data: roadmap } = useQuery({
    queryKey: ['activeRoadmap'],
    queryFn: getActiveRoadmap,
  });

  const { data: gapData } = useQuery({
    queryKey: ['gapAnalysis'],
    queryFn: getSkillGapAnalysis,
  });

  const readinessScore = gapData?.readiness_score ?? (roadmap?.readiness_score ? Math.round(roadmap.readiness_score) : 0);
  const targetRole = profile?.target_role_name || 'No Goal Selected';

  const totalModules = roadmap?.modules.length || 0;
  const completedModules = roadmap?.modules.filter((m) => m.status === 'completed').length || 0;
  const inProgressModules = roadmap?.modules.filter((m) => m.status === 'in_progress').length || 0;
  const roadmapPct = totalModules > 0 ? Math.round((completedModules / totalModules) * 100) : 0;

  // Determine current active phase
  const currentPhase = React.useMemo(() => {
    if (!roadmap || roadmap.modules.length === 0) return 1;
    const activeMod = roadmap.modules.find(
      (m) => m.status === 'in_progress' || m.status === 'available' || m.status === 'needs_revision'
    );
    return activeMod ? activeMod.phase : 1;
  }, [roadmap]);

  const nextAction = gapData?.next_best_action || (
    profile?.target_role_id
      ? 'Explore your learning roadmap and start your first foundational module.'
      : 'Select a target career role to calculate your skill gap.'
  );

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-12">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-indigo-400 bg-indigo-950/80 border border-indigo-800/80 px-2.5 py-0.5 rounded-full flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5" /> Learner Command Center
              </span>
              <span className="text-xs text-slate-500">•</span>
              <span className="text-xs text-slate-400">Weekly Target: {profile?.weekly_study_hours || 8}h/week</span>
            </div>

            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Welcome back, {profile?.full_name || user?.username}!
            </h1>
            <p className="text-xs sm:text-sm text-slate-400 max-w-xl">
              Target Career Role:{' '}
              <strong className="text-slate-100">{targetRole}</strong>.
              Your adaptive career readiness loop is active.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {!profile?.target_role_id ? (
              <button
                onClick={() => navigate('/career-goal')}
                className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition-all shadow-lg shadow-indigo-600/30 flex items-center gap-2"
              >
                <Target className="w-4 h-4" />
                <span>Select Career Goal</span>
              </button>
            ) : (
              <button
                onClick={() => navigate('/assessment')}
                className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition-all shadow-md shadow-indigo-600/20 flex items-center gap-2"
              >
                <Award className="w-4 h-4" />
                <span>Diagnostic Assessment</span>
              </button>
            )}

            <button
              onClick={() => navigate('/roadmap')}
              className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition-all border border-slate-700 flex items-center gap-2"
            >
              <Map className="w-4 h-4" />
              <span>Learning Roadmap</span>
            </button>
          </div>
        </div>
      </div>

      {/* Next Best Action Card */}
      <NextActionCard
        actionText={nextAction}
        targetPath={
          nextAction.toLowerCase().includes('assessment') || nextAction.toLowerCase().includes('diagnostic')
            ? '/assessment'
            : !profile?.target_role_id
            ? '/career-goal'
            : '/roadmap'
        }
        buttonLabel={
          nextAction.toLowerCase().includes('assessment')
            ? 'Start Diagnostic'
            : !profile?.target_role_id
            ? 'Select Role'
            : 'Continue Learning'
        }
      />

      {/* Primary Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-stretch">
        {/* Readiness Gauge */}
        <ReadinessGauge
          score={readinessScore}
          roleName={targetRole}
          size="md"
        />

        {/* Roadmap Progress Overview */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-lg flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                <Map className="w-4 h-4 text-indigo-400" />
                Roadmap Trajectory
              </span>
              <span className="text-xs font-semibold px-2 py-0.5 rounded-md bg-indigo-950/80 text-indigo-300 border border-indigo-800/80">
                Phase {currentPhase} of 4
              </span>
            </div>

            <div className="mt-4 flex items-baseline justify-between">
              <span className="text-3xl font-extrabold text-white">{roadmapPct}%</span>
              <span className="text-xs text-slate-400">
                {completedModules} of {totalModules} Modules
              </span>
            </div>

            {/* Progress bar */}
            <div className="w-full h-2.5 bg-slate-800 rounded-full overflow-hidden mt-2">
              <div
                className="h-full bg-gradient-to-r from-indigo-500 to-emerald-500 rounded-full transition-all duration-500"
                style={{ width: `${roadmapPct}%` }}
              />
            </div>

            <div className="mt-4 space-y-2 text-xs text-slate-400">
              <div className="flex justify-between">
                <span>In Progress:</span>
                <span className="font-semibold text-slate-200">{inProgressModules}</span>
              </div>
              <div className="flex justify-between">
                <span>Completed:</span>
                <span className="font-semibold text-emerald-400">{completedModules}</span>
              </div>
              <div className="flex justify-between">
                <span>Weekly Hours Allocated:</span>
                <span className="font-semibold text-slate-200">{profile?.weekly_study_hours || 8}h</span>
              </div>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-800/80 mt-4">
            <Link
              to="/roadmap"
              className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold flex items-center gap-1"
            >
              <span>View full curriculum timeline</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>

        {/* Quick Launch & Skill Summary */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-lg flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                <BarChart3 className="w-4 h-4 text-indigo-400" />
                Gaps & Verification
              </span>
              <span className="text-xs text-slate-500">
                {profile?.learner_skills?.length || 0} Skills Logged
              </span>
            </div>

            <div className="space-y-3 mt-3">
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-xs flex items-center justify-between">
                <span className="text-slate-400">Critical Priority Gaps:</span>
                <strong className="text-rose-400 font-bold">
                  {gapData?.gaps.filter((g) => g.priority === 'critical').length || 0}
                </strong>
              </div>

              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-xs flex items-center justify-between">
                <span className="text-slate-400">Verified Strengths (&gt;=85%):</span>
                <strong className="text-emerald-400 font-bold">
                  {gapData?.strengths.length || 0}
                </strong>
              </div>

              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-xs flex items-center justify-between">
                <span className="text-slate-400">Prerequisite Dependencies:</span>
                <strong className="text-indigo-400 font-bold">Guaranteed Strict</strong>
              </div>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-800/80 mt-4">
            <Link
              to="/skill-gap"
              className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold flex items-center gap-1"
            >
              <span>Review full skill gap report</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </div>

      {/* Quick Access Pathways */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
        <Link
          to="/career-goal"
          className="group p-4 rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 transition-all shadow-md flex items-center gap-3"
        >
          <div className="w-10 h-10 rounded-lg bg-indigo-950/80 text-indigo-400 flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform">
            <Target className="w-5 h-5" />
          </div>
          <div>
            <span className="text-xs font-bold text-slate-100 block group-hover:text-indigo-400 transition-colors">
              1. Career Goal
            </span>
            <span className="text-[11px] text-slate-500">Select or switch roles</span>
          </div>
        </Link>

        <Link
          to="/skill-gap"
          className="group p-4 rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 transition-all shadow-md flex items-center gap-3"
        >
          <div className="w-10 h-10 rounded-lg bg-cyan-950/80 text-cyan-400 flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform">
            <BarChart3 className="w-5 h-5" />
          </div>
          <div>
            <span className="text-xs font-bold text-slate-100 block group-hover:text-cyan-400 transition-colors">
              2. Skill Gap
            </span>
            <span className="text-[11px] text-slate-500">Readiness & priority gaps</span>
          </div>
        </Link>

        <Link
          to="/assessment"
          className="group p-4 rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 transition-all shadow-md flex items-center gap-3"
        >
          <div className="w-10 h-10 rounded-lg bg-amber-950/80 text-amber-400 flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform">
            <Award className="w-5 h-5" />
          </div>
          <div>
            <span className="text-xs font-bold text-slate-100 block group-hover:text-amber-400 transition-colors">
              3. Diagnostic Assessment
            </span>
            <span className="text-[11px] text-slate-500">Trigger adaptive replanning</span>
          </div>
        </Link>
      </div>
    </div>
  );
};

