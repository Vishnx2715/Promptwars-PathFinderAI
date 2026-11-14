import React from 'react';
import { Info, Lock, AlertCircle, CheckCircle2 } from 'lucide-react';

interface ExplanationCardProps {
  type?: 'lock' | 'revision' | 'info' | 'success';
  title?: string;
  reason: string;
  prerequisiteModuleTitle?: string | null;
  prerequisiteSkill?: string;
}

export const ExplanationCard: React.FC<ExplanationCardProps> = ({
  type = 'info',
  title,
  reason,
  prerequisiteModuleTitle,
  prerequisiteSkill,
}) => {
  let containerStyle = 'bg-slate-900 border-slate-800 text-slate-300';
  let icon = <Info className="w-4 h-4 text-indigo-400 mt-0.5 shrink-0" />;

  if (type === 'lock') {
    containerStyle = 'bg-slate-900/90 border-amber-900/40 text-amber-200/90';
    icon = <Lock className="w-4 h-4 text-amber-400 mt-0.5 shrink-0" />;
  } else if (type === 'revision') {
    containerStyle = 'bg-rose-950/20 border-rose-900/50 text-rose-200';
    icon = <AlertCircle className="w-4 h-4 text-rose-400 mt-0.5 shrink-0" />;
  } else if (type === 'success') {
    containerStyle = 'bg-emerald-950/20 border-emerald-900/50 text-emerald-200';
    icon = <CheckCircle2 className="w-4 h-4 text-emerald-400 mt-0.5 shrink-0" />;
  }

  return (
    <div className={`p-3.5 rounded-xl border flex items-start gap-3 text-xs leading-relaxed ${containerStyle}`}>
      {icon}
      <div className="flex-1">
        {title && <p className="font-semibold text-slate-100 mb-0.5">{title}</p>}
        <p>{reason}</p>
        {(prerequisiteModuleTitle || prerequisiteSkill) && (
          <p className="mt-1 text-[11px] opacity-80">
            {prerequisiteSkill && <span>Prerequisite Skill: <strong>{prerequisiteSkill}</strong> (min. 70% mastery). </span>}
            {prerequisiteModuleTitle && <span>Prerequisite Module: <strong>{prerequisiteModuleTitle}</strong>.</span>}
          </p>
        )}
      </div>
    </div>
  );
};

