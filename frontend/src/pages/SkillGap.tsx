import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { getSkillGapAnalysis } from '../api/career';
import { useAuth } from '../context/AuthContext';
import { ReadinessGauge } from '../components/ReadinessGauge';
import { SkillBar } from '../components/SkillBar';
import { NextActionCard } from '../components/NextActionCard';
import { ExplanationCard } from '../components/ExplanationCard';
import { 
  BarChart3, 
  ShieldAlert, 
  CheckCircle2, 
  AlertTriangle, 
  ArrowRight, 
  Sparkles,
  HelpCircle,
  Award
} from 'lucide-react';

export const SkillGap: React.FC = () => {
  const navigate = useNavigate();
  const { profile } = useAuth();

  const { data: gapData, isLoading, error, refetch } = useQuery({
    queryKey: ['gapAnalysis'],
    queryFn: getSkillGapAnalysis,
  });

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-slate-400">
        <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mb-3" />
        <p className="text-sm">Synthesizing evidence-based skill gaps...</p>
      </div>
    );
  }

  if (error || !gapData) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 text-center max-w-xl mx-auto space-y-4">
        <ShieldAlert className="w-12 h-12 text-amber-400 mx-auto" />
        <h3 className="text-lg font-bold text-white">Target Career Goal Required</h3>
        <p className="text-xs text-slate-400">
          Please select a target career role to compute your weighted readiness score and priority skill gaps.
        </p>
        <button
          onClick={() => navigate('/career-goal')}
          className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition-all inline-flex items-center gap-2"
        >
          <span>Select Career Role</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    );
  }

  const criticalGaps = gapData.gaps.filter((g) => g.priority === 'critical');
  const highGaps = gapData.gaps.filter((g) => g.priority === 'high');
  const mediumGaps = gapData.gaps.filter((g) => g.priority === 'medium');

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-12">
      {/* Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-bold text-indigo-400 uppercase tracking-wider">Step 3 of 4</span>
          <span className="text-xs text-slate-500">•</span>
          <span className="text-xs text-slate-400">AI Gap Evaluation</span>
        </div>
        <h1 className="text-2xl font-bold text-white tracking-tight">Evidence-Based Skill-Gap Analysis</h1>
        <p className="text-xs sm:text-sm text-slate-400 mt-1 max-w-3xl">
          {gapData.summary}
        </p>
      </div>

      {/* Top Section: Readiness Gauge & Next Best Action */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-stretch">
        <div className="lg:col-span-1">
          <ReadinessGauge
            score={gapData.readiness_score}
            roleName={profile?.target_role_name || 'Career Role'}
            size="lg"
          />
        </div>

        <div className="lg:col-span-2 flex flex-col justify-between gap-4">
          <NextActionCard
            actionText={gapData.next_best_action}
            targetPath={gapData.next_best_action.toLowerCase().includes('diagnostic') || gapData.next_best_action.toLowerCase().includes('assessment') ? '/assessment' : '/roadmap'}
            buttonLabel={gapData.next_best_action.toLowerCase().includes('assessment') ? 'Start Assessment' : 'View Learning Roadmap'}
          />

          {/* Strengths Card */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg flex-1">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
              <span className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                Verified Strengths ({gapData.strengths.length})
              </span>
              <span className="text-[11px] text-slate-500">&gt;= 85% verified mastery</span>
            </div>

            {gapData.strengths.length === 0 ? (
              <p className="text-xs text-slate-500 py-3 italic">
                No skills verified above 85% yet. Take diagnostic assessments to verify self-reported skills.
              </p>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                {gapData.strengths.map((s, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-xs"
                  >
                    <div className="flex items-center justify-between font-bold text-slate-100">
                      <span>{s.skill}</span>
                      <span className="text-emerald-400 font-extrabold">{s.mastery.toFixed(0)}%</span>
                    </div>
                    <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">{s.reason}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Gaps Breakdown & Explanations */}
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-indigo-400" />
            <span>Target Competencies & Skill Gaps ({gapData.gaps.length})</span>
          </h2>

          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/roadmap')}
              className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-all shadow-md flex items-center gap-1.5"
            >
              <span>Explore Personalized Roadmap</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Critical & High Priority Gaps */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {gapData.gaps.map((gap, idx) => {
            const isBlocking = gap.blocking_skills && gap.blocking_skills.length > 0;

            return (
              <div key={idx} className="space-y-2">
                <SkillBar
                  skillName={gap.skill}
                  currentMastery={gap.current_mastery}
                  requiredLevel={gap.required_level}
                  isBlocking={isBlocking}
                />
                <ExplanationCard
                  type={gap.priority === 'critical' ? 'revision' : isBlocking ? 'lock' : 'info'}
                  reason={gap.reason}
                />
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

