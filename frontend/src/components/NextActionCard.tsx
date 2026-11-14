import React from 'react';
import { Compass, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface NextActionCardProps {
  actionText: string;
  targetPath?: string;
  buttonLabel?: string;
}

export const NextActionCard: React.FC<NextActionCardProps> = ({
  actionText,
  targetPath,
  buttonLabel = 'Take Action',
}) => {
  const navigate = useNavigate();

  return (
    <div className="relative overflow-hidden bg-gradient-to-r from-indigo-950/80 via-slate-900 to-indigo-950/60 border border-indigo-800/40 rounded-2xl p-5 shadow-xl">
      <div className="absolute top-0 right-0 -mr-8 -mt-8 w-32 h-32 bg-indigo-500/10 rounded-full blur-2xl pointer-events-none" />

      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 relative z-10">
        <div className="flex items-start gap-3.5">
          <div className="w-10 h-10 rounded-xl bg-indigo-600/30 border border-indigo-500/40 flex items-center justify-center shrink-0 text-indigo-400 mt-0.5 sm:mt-0">
            <Compass className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-indigo-400">
                Next Best Action
              </span>
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-indigo-400 animate-ping" />
            </div>
            <p className="text-slate-100 font-medium text-sm sm:text-base mt-0.5 leading-snug">
              {actionText}
            </p>
          </div>
        </div>

        {targetPath && (
          <button
            onClick={() => navigate(targetPath)}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm transition-all shadow-md shadow-indigo-600/20 whitespace-nowrap self-stretch sm:self-auto justify-center"
          >
            <span>{buttonLabel}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
};

