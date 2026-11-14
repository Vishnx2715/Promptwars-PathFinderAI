import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { getMentorProfile, getMentees } from '../../api/mentor';
import { Users, Copy, AlertTriangle, CheckCircle2, Clock } from 'lucide-react';

export const MentorDashboard: React.FC = () => {
  const [copied, setCopied] = useState(false);
  const { data: profile } = useQuery({ queryKey: ['mentorProfile'], queryFn: getMentorProfile });
  const { data: mentees } = useQuery({ queryKey: ['mentees'], queryFn: getMentees });

  const copyCode = () => {
    if (profile?.mentor_code) {
      navigator.clipboard.writeText(profile.mentor_code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const riskColors: Record<string, string> = {
    high: 'text-rose-400 bg-rose-950/40 border-rose-800/50',
    medium: 'text-amber-400 bg-amber-950/40 border-amber-800/50',
    low: 'text-emerald-400 bg-emerald-950/40 border-emerald-800/50',
  };

  return (
    <div className="space-y-6 pb-12">
      <div>
        <h1 className="text-2xl font-bold text-white">Mentor Dashboard</h1>
        <p className="text-sm text-slate-400">Welcome back, {profile?.full_name}</p>
      </div>

      {/* Mentor profile card */}
      {profile && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="text-sm font-semibold text-slate-200 mb-1">Your Mentor Code</h3>
              <p className="text-xs text-slate-500 mb-3">Share this with students so they can connect</p>
              <div className="flex items-center gap-2">
                <code className="px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-indigo-400 font-mono text-sm">
                  {profile.mentor_code}
                </code>
                <button onClick={copyCode} className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300">
                  {copied ? <CheckCircle2 className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
                </button>
              </div>
              <p className="text-xs text-slate-500 mt-2">{profile.expertise}</p>
            </div>
            <div className="text-right">
              <div className="text-3xl font-bold text-indigo-400">{profile.connected_students}</div>
              <p className="text-xs text-slate-500">Connected Students</p>
            </div>
          </div>
        </div>
      )}

      {/* Mentee list */}
      <div>
        <h3 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
          <Users className="w-4 h-4 text-slate-400" /> Connected Students
        </h3>
        {!mentees || mentees.length === 0 ? (
          <div className="text-center py-8">
            <Users className="w-12 h-12 mx-auto mb-3 opacity-30 text-slate-500" />
            <p className="text-slate-500 text-sm">No students connected yet. Share your mentor code!</p>
          </div>
        ) : (
          <div className="space-y-3">
            {mentees.map((m) => (
              <Link key={m.profile_id} to={`/mentor/mentees/${m.profile_id}`}
                className="block p-4 rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 transition-all">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-semibold text-slate-100">{m.student_name}</p>
                    <p className="text-xs text-slate-500">{m.career_goal || 'No goal set'}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="text-right">
                      <div className="text-sm font-bold text-slate-200">{m.readiness_score.toFixed(0)}%</div>
                      <div className="text-xs text-slate-500">Readiness</div>
                    </div>
                    <span className={`text-xs px-2 py-0.5 rounded border ${riskColors[m.risk_level]}`}>
                      {m.risk_level}
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-4 mt-2 text-xs text-slate-500">
                  <span>Progress: {m.roadmap_progress_pct.toFixed(0)}%</span>
                  {m.pending_doubts > 0 && (
                    <span className="flex items-center gap-1 text-amber-400">
                      <Clock className="w-3 h-3" /> {m.pending_doubts} pending doubts
                    </span>
                  )}
                  {m.pending_project_reviews > 0 && (
                    <span className="flex items-center gap-1 text-indigo-400">
                      <AlertTriangle className="w-3 h-3" /> {m.pending_project_reviews} project reviews
                    </span>
                  )}
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
