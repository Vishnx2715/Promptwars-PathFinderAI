import React from 'react';
import { ShieldCheck, UserCheck, AlertTriangle } from 'lucide-react';

interface SkillBarProps {
  skillName: string;
  category?: string;
  currentMastery: number; // 0-100
  requiredLevel?: number; // 1-5
  verifiedLevel?: number; // 0-5
  evidenceType?: string;
  isBlocking?: boolean;
}

export const SkillBar: React.FC<SkillBarProps> = ({
  skillName,
  category,
  currentMastery,
  requiredLevel,
  verifiedLevel,
  evidenceType,
  isBlocking,
}) => {
  // Classification
  let colorClass = 'bg-rose-500';
  let badgeText = 'Critical Gap';
  let badgeColor = 'text-rose-400 bg-rose-950/60 border-rose-800/60';

  if (currentMastery >= 85) {
    colorClass = 'bg-emerald-500';
    badgeText = 'Strong';
    badgeColor = 'text-emerald-400 bg-emerald-950/60 border-emerald-800/60';
  } else if (currentMastery >= 60) {
    colorClass = 'bg-indigo-500';
    badgeText = 'Developing';
    badgeColor = 'text-indigo-400 bg-indigo-950/60 border-indigo-800/60';
  } else if (currentMastery >= 30) {
    colorClass = 'bg-amber-500';
    badgeText = 'Weak';
    badgeColor = 'text-amber-400 bg-amber-950/60 border-amber-800/60';
  }

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 transition-all hover:border-slate-700">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <span className="font-semibold text-slate-100 text-sm">{skillName}</span>
          {category && (
            <span className="text-[11px] font-medium text-slate-400 bg-slate-800 px-2 py-0.5 rounded-full">
              {category}
            </span>
          )}
          {isBlocking && (
            <span className="flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wider text-rose-300 bg-rose-950/80 border border-rose-800/80 px-2 py-0.5 rounded-md animate-pulse">
              <AlertTriangle className="w-3 h-3" /> Blocks Next Phase
            </span>
          )}
        </div>

        <div className="flex items-center space-x-2">
          {evidenceType === 'assessment' ? (
            <span className="flex items-center gap-1 text-[11px] text-cyan-400 bg-cyan-950/60 border border-cyan-800/50 px-2 py-0.5 rounded-full">
              <ShieldCheck className="w-3 h-3" /> Verified
            </span>
          ) : (
            <span className="flex items-center gap-1 text-[11px] text-slate-400 bg-slate-800/80 px-2 py-0.5 rounded-full">
              <UserCheck className="w-3 h-3" /> Self-Reported
            </span>
          )}
          <span className={`text-[11px] font-semibold border px-2 py-0.5 rounded-full ${badgeColor}`}>
            {badgeText}
          </span>
        </div>
      </div>

      {/* Progress Bar Container */}
      <div className="relative w-full h-2.5 bg-slate-800 rounded-full overflow-hidden mt-2">
        <div
          className={`h-full rounded-full transition-all duration-500 ${colorClass}`}
          style={{ width: `${Math.min(100, Math.max(0, currentMastery))}%` }}
        />
      </div>

      <div className="flex items-center justify-between mt-2 text-xs text-slate-400 font-medium">
        <span>
          Current: <strong className="text-slate-200">{currentMastery.toFixed(0)}%</strong>
          {verifiedLevel !== undefined && ` (Level ${verifiedLevel.toFixed(1)}/5)`}
        </span>
        {requiredLevel !== undefined && (
          <span>
            Target: <strong className="text-slate-300">Level {requiredLevel}/5</strong>
          </span>
        )}
      </div>
    </div>
  );
};

