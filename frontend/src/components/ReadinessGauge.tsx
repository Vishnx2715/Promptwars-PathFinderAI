import React from 'react';
import { Target, TrendingUp } from 'lucide-react';

interface ReadinessGaugeProps {
  score: number; // 0-100
  roleName?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const ReadinessGauge: React.FC<ReadinessGaugeProps> = ({
  score,
  roleName = 'Target Career Role',
  size = 'md',
}) => {
  const normalizedScore = Math.min(100, Math.max(0, Math.round(score)));
  
  // Dimensions
  const radius = size === 'sm' ? 42 : size === 'lg' ? 76 : 60;
  const strokeWidth = size === 'sm' ? 8 : size === 'lg' ? 14 : 12;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (normalizedScore / 100) * circumference;

  let strokeColor = '#f43f5e'; // rose-500
  let statusText = 'Early Preparation';
  let badgeClass = 'text-rose-400 bg-rose-950/60 border-rose-800/60';

  if (normalizedScore >= 85) {
    strokeColor = '#10b981'; // emerald-500
    statusText = 'Role Ready';
    badgeClass = 'text-emerald-400 bg-emerald-950/60 border-emerald-800/60';
  } else if (normalizedScore >= 60) {
    strokeColor = '#6366f1'; // indigo-500
    statusText = 'Developing Fit';
    badgeClass = 'text-indigo-400 bg-indigo-950/60 border-indigo-800/60';
  } else if (normalizedScore >= 30) {
    strokeColor = '#f59e0b'; // amber-500
    statusText = 'Foundation In Progress';
    badgeClass = 'text-amber-400 bg-amber-950/60 border-amber-800/60';
  }

  const svgSize = (radius + strokeWidth) * 2;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 flex flex-col items-center justify-center text-center shadow-lg">
      <div className="flex items-center gap-1.5 text-xs text-slate-400 font-medium mb-3 uppercase tracking-wider">
        <Target className="w-4 h-4 text-indigo-400" />
        <span>Career Readiness Score</span>
      </div>

      <div className="relative flex items-center justify-center my-2">
        <svg
          width={svgSize}
          height={svgSize}
          className="transform -rotate-90 transition-all duration-700 ease-out"
        >
          {/* Background circle */}
          <circle
            cx={radius + strokeWidth}
            cy={radius + strokeWidth}
            r={radius}
            stroke="#1e293b" // slate-800
            strokeWidth={strokeWidth}
            fill="transparent"
          />
          {/* Animated progress circle */}
          <circle
            cx={radius + strokeWidth}
            cy={radius + strokeWidth}
            r={radius}
            stroke={strokeColor}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            fill="transparent"
            className="transition-all duration-1000 ease-out"
          />
        </svg>

        {/* Centered Score */}
        <div className="absolute flex flex-col items-center justify-center">
          <span className="text-3xl lg:text-4xl font-extrabold text-white tracking-tight">
            {normalizedScore}%
          </span>
          <span className="text-[11px] text-slate-400 font-medium -mt-0.5">Readiness</span>
        </div>
      </div>

      <div className="mt-4 flex flex-col items-center gap-1">
        <span className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${badgeClass}`}>
          {statusText}
        </span>
        <span className="text-xs text-slate-400 mt-1 max-w-[200px] truncate" title={roleName}>
          for <strong className="text-slate-200">{roleName}</strong>
        </span>
      </div>
    </div>
  );
};

