import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { getCareerRoles, selectCareerRole } from '../api/career';
import { generateRoadmap } from '../api/roadmap';
import { useAuth } from '../context/AuthContext';
import { 
  Target, 
  CheckCircle2, 
  ArrowRight, 
  Layers, 
  Sparkles, 
  AlertCircle,
  Clock,
  BookOpen
} from 'lucide-react';

export const CareerGoal: React.FC = () => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { profile, refreshProfile } = useAuth();

  const [selectedRoleId, setSelectedRoleId] = useState<number | null>(
    profile?.target_role_id || null
  );
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Fetch Career Roles
  const { data: roles, isLoading, error } = useQuery({
    queryKey: ['careerRoles'],
    queryFn: getCareerRoles,
  });

  // Select Career Mutation
  const selectMutation = useMutation({
    mutationFn: async (roleId: number) => {
      await selectCareerRole(roleId);
      // Auto-generate initial roadmap for the role
      await generateRoadmap();
      await refreshProfile();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gapAnalysis'] });
      queryClient.invalidateQueries({ queryKey: ['activeRoadmap'] });
      setSuccessMessage('Career role selected and adaptive learning roadmap initialized!');
      setTimeout(() => {
        navigate('/skill-gap');
      }, 1200);
    },
  });

  const handleSelectRole = (roleId: number) => {
    setSelectedRoleId(roleId);
    selectMutation.mutate(roleId);
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-slate-400">
        <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mb-3" />
        <p className="text-sm">Loading available career pathways...</p>
      </div>
    );
  }

  if (error || !roles) {
    return (
      <div className="p-6 rounded-2xl bg-rose-950/30 border border-rose-900/50 text-rose-300 text-sm flex items-center gap-3">
        <AlertCircle className="w-5 h-5 shrink-0" />
        <span>Failed to load career roles. Please refresh or verify the backend server.</span>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-12">
      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-bold text-indigo-400 uppercase tracking-wider">Step 2 of 4</span>
          <span className="text-xs text-slate-500">•</span>
          <span className="text-xs text-slate-400">Target Role Selection</span>
        </div>
        <h1 className="text-2xl font-bold text-white tracking-tight">Select Your Career Target</h1>
        <p className="text-xs sm:text-sm text-slate-400 mt-1 max-w-2xl">
          Choose a role to generate your real-time skill-gap analysis and prerequisite-aware roadmap.
          Switching roles at any time preserves your transferable verified competencies.
        </p>
      </div>

      {successMessage && (
        <div className="p-4 rounded-xl bg-emerald-950/40 border border-emerald-800/60 text-emerald-200 text-xs font-semibold flex items-center gap-2 animate-fade-in">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{successMessage}</span>
        </div>
      )}

      {/* Role Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {roles.map((role) => {
          const isSelected = profile?.target_role_id === role.id;
          const isPending = selectMutation.isPending && selectedRoleId === role.id;

          return (
            <div
              key={role.id}
              className={`flex flex-col justify-between rounded-2xl p-6 transition-all border ${
                isSelected
                  ? 'bg-indigo-950/20 border-indigo-500/80 ring-1 ring-indigo-500/50 shadow-indigo-900/20 shadow-xl'
                  : 'bg-slate-900 border-slate-800 hover:border-slate-700 shadow-md'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="w-10 h-10 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center text-indigo-400">
                    <Target className="w-5 h-5" />
                  </div>
                  {isSelected && (
                    <span className="flex items-center gap-1 text-[11px] font-bold text-emerald-400 bg-emerald-950/80 border border-emerald-800/60 px-2.5 py-0.5 rounded-full">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Active Target
                    </span>
                  )}
                </div>

                <h3 className="text-lg font-bold text-white mb-2">{role.name}</h3>
                <p className="text-xs text-slate-400 leading-relaxed mb-4 min-h-[48px]">
                  {role.description}
                </p>

                {/* Required Skills Tags */}
                <div className="space-y-2 mb-6">
                  <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                    Core Competencies ({role.requirements?.length || 0}):
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {role.requirements?.slice(0, 7).map((req) => (
                      <span
                        key={req.id}
                        className="text-[11px] font-medium bg-slate-800/80 text-slate-300 border border-slate-700/60 px-2 py-0.5 rounded-md"
                      >
                        {req.skill_name} <span className="text-slate-500">Lv{req.required_level}</span>
                      </span>
                    ))}
                    {(role.requirements?.length || 0) > 7 && (
                      <span className="text-[11px] font-medium text-slate-500 px-1 py-0.5">
                        +{role.requirements.length - 7} more
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Action Button */}
              <div className="pt-4 border-t border-slate-800/80">
                <button
                  type="button"
                  disabled={isPending || isSelected}
                  onClick={() => handleSelectRole(role.id)}
                  className={`w-full py-2.5 px-4 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-2 ${
                    isSelected
                      ? 'bg-slate-800 text-slate-400 border border-slate-700 cursor-default'
                      : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-600/25'
                  }`}
                >
                  {isPending ? (
                    <span>Generating Roadmap...</span>
                  ) : isSelected ? (
                    <span>Selected Role</span>
                  ) : (
                    <>
                      <span>Select This Role</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </>
                  )}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

