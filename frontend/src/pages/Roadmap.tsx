import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { 
  getActiveRoadmap, 
  generateRoadmap, 
  replanRoadmap, 
  updateModuleStatus, 
  toggleResourceCompletion 
} from '../api/roadmap';
import { RoadmapTimeline } from '../components/RoadmapTimeline';
import { NextActionCard } from '../components/NextActionCard';
import { 
  Map, 
  RotateCw, 
  Sparkles, 
  AlertCircle, 
  Layers, 
  CheckCircle2, 
  ArrowRight,
  Award
} from 'lucide-react';

export const Roadmap: React.FC = () => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  const [notification, setNotification] = useState<string | null>(null);

  // Fetch active roadmap
  const { data: roadmap, isLoading, error } = useQuery({
    queryKey: ['activeRoadmap'],
    queryFn: getActiveRoadmap,
  });

  // Replan mutation
  const replanMutation = useMutation({
    mutationFn: replanRoadmap,
    onSuccess: (updated) => {
      queryClient.setQueryData(['activeRoadmap'], updated);
      queryClient.invalidateQueries({ queryKey: ['gapAnalysis'] });
      setNotification('Roadmap adaptively replanned based on updated competencies.');
      setTimeout(() => setNotification(null), 4000);
    },
  });

  // Generate mutation
  const generateMutation = useMutation({
    mutationFn: generateRoadmap,
    onSuccess: (updated) => {
      queryClient.setQueryData(['activeRoadmap'], updated);
      queryClient.invalidateQueries({ queryKey: ['gapAnalysis'] });
      setNotification('New personalized roadmap generated!');
      setTimeout(() => setNotification(null), 4000);
    },
  });

  // Toggle resource
  const handleToggleResource = async (resourceId: number, isCompleted: boolean) => {
    try {
      await toggleResourceCompletion(resourceId, isCompleted);
      queryClient.invalidateQueries({ queryKey: ['activeRoadmap'] });
    } catch (err: any) {
      console.error(err);
    }
  };

  // Update status
  const handleUpdateStatus = async (moduleId: number, status: string) => {
    try {
      await updateModuleStatus(moduleId, status);
      queryClient.invalidateQueries({ queryKey: ['activeRoadmap'] });
      queryClient.invalidateQueries({ queryKey: ['gapAnalysis'] });
      setNotification(`Module status updated to '${status}'. Dependent prerequisites re-evaluated.`);
      setTimeout(() => setNotification(null), 4000);
    } catch (err: any) {
      setNotification(err.response?.data?.detail || 'Failed to update module status.');
      setTimeout(() => setNotification(null), 4000);
    }
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-slate-400">
        <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mb-3" />
        <p className="text-sm">Synthesizing personalized learning path...</p>
      </div>
    );
  }

  if (error || !roadmap) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 text-center max-w-xl mx-auto space-y-4">
        <AlertCircle className="w-12 h-12 text-amber-400 mx-auto" />
        <h3 className="text-lg font-bold text-white">No Active Learning Roadmap</h3>
        <p className="text-xs text-slate-400">
          You haven't generated a personalized roadmap yet. Select your target career role or generate a fresh roadmap.
        </p>
        <div className="flex items-center justify-center gap-3 pt-2">
          <button
            onClick={() => generateMutation.mutate()}
            disabled={generateMutation.isPending}
            className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition-all shadow-lg flex items-center gap-2"
          >
            <Sparkles className="w-4 h-4" />
            <span>{generateMutation.isPending ? 'Generating...' : 'Generate Roadmap'}</span>
          </button>
          <button
            onClick={() => navigate('/career-goal')}
            className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition-all border border-slate-700"
          >
            Career Goal
          </button>
        </div>
      </div>
    );
  }

  // Summary statistics
  const totalModules = roadmap.modules.length;
  const completedModules = roadmap.modules.filter((m) => m.status === 'completed').length;
  const needsRevisionModules = roadmap.modules.filter((m) => m.status === 'needs_revision').length;
  const overallProgress = totalModules > 0 ? Math.round((completedModules / totalModules) * 100) : 0;

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-12">
      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-bold text-indigo-400 uppercase tracking-wider">
              Roadmap v{roadmap.version}
            </span>
            <span className="text-xs text-slate-500">•</span>
            <span className="text-xs text-slate-400">{roadmap.career_role_name}</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Personalized Learning Roadmap</h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1 max-w-2xl">
            Prerequisite-ordered curriculum with deterministic module unlocking and adaptive remediation sprints.
          </p>
        </div>

        <div className="flex items-center gap-3 self-start md:self-auto">
          <button
            type="button"
            onClick={() => replanMutation.mutate()}
            disabled={replanMutation.isPending}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs font-semibold transition-all shadow-md"
            title="Re-evaluate prerequisites and sync roadmap"
          >
            <RotateCw className={`w-3.5 h-3.5 ${replanMutation.isPending ? 'animate-spin' : ''}`} />
            <span>Adaptive Replan</span>
          </button>

          <button
            type="button"
            onClick={() => navigate('/assessment')}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition-all shadow-lg shadow-indigo-600/25"
          >
            <Award className="w-4 h-4" />
            <span>Take Diagnostic</span>
          </button>
        </div>
      </div>

      {notification && (
        <div className="p-4 rounded-xl bg-indigo-950/40 border border-indigo-800/60 text-indigo-200 text-xs font-semibold flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{notification}</span>
        </div>
      )}

      {/* Progress Metric Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-md">
          <span className="text-xs text-slate-400 font-medium">Roadmap Completion</span>
          <div className="flex items-baseline justify-between mt-1">
            <span className="text-2xl font-extrabold text-white">{overallProgress}%</span>
            <span className="text-xs text-slate-400">{completedModules} of {totalModules} Modules</span>
          </div>
          <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden mt-2">
            <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${overallProgress}%` }} />
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-md">
          <span className="text-xs text-slate-400 font-medium">Readiness Score</span>
          <div className="flex items-baseline justify-between mt-1">
            <span className="text-2xl font-extrabold text-indigo-400">{Math.round(roadmap.readiness_score)}%</span>
            <span className="text-xs text-slate-400">Verified Weighted Fit</span>
          </div>
          <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden mt-2">
            <div className="h-full bg-indigo-500 rounded-full" style={{ width: `${roadmap.readiness_score}%` }} />
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-md">
          <span className="text-xs text-slate-400 font-medium">Status & Alerts</span>
          <div className="flex items-baseline justify-between mt-1">
            <span className={`text-base font-bold ${needsRevisionModules > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
              {needsRevisionModules > 0 ? `${needsRevisionModules} Needs Revision` : 'All Systems Clear'}
            </span>
            <span className="text-xs text-slate-500">Adaptive Loop</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1 truncate">
            {roadmap.replan_reason || 'Active learning path.'}
          </p>
        </div>
      </div>

      {/* Roadmap Timeline */}
      <div className="bg-slate-900/50 border border-slate-800/80 rounded-2xl p-6 lg:p-8 shadow-xl">
        <RoadmapTimeline
          modules={roadmap.modules}
          onToggleResource={handleToggleResource}
          onUpdateStatus={handleUpdateStatus}
        />
      </div>
    </div>
  );
};

