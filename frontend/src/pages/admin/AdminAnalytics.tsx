import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { getAdminAnalytics } from '../../api/analytics';
import { TrendingUp, AlertTriangle } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const PIE_COLORS = ['#6366f1', '#22c55e', '#f59e0b', '#ef4444', '#06b6d4', '#a855f7', '#ec4899'];

export const AdminAnalytics: React.FC = () => {
  const { data, isLoading } = useQuery({ queryKey: ['adminAnalytics'], queryFn: getAdminAnalytics });

  if (isLoading) return <div className="text-center text-slate-500 py-12">Loading analytics...</div>;
  if (!data) return null;

  return (
    <div className="space-y-6 pb-12">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-teal-950/80 text-teal-400 flex items-center justify-center">
          <TrendingUp className="w-5 h-5" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">Platform Analytics</h1>
          <p className="text-sm text-slate-400">Platform-wide insights and trends</p>
        </div>
      </div>

      {/* Career role distribution */}
      {data.career_role_distribution.length > 0 && (
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <h3 className="text-sm font-semibold text-slate-200 mb-3">Career Role Distribution</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie data={data.career_role_distribution} dataKey="count" nameKey="role" cx="50%" cy="50%" outerRadius={80} label>
                {data.career_role_distribution.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
              </Pie>
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Platform skill gaps */}
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <h3 className="text-sm font-semibold text-slate-200 mb-3">Common Skill Gaps</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={data.platform_skill_gaps} layout="vertical">
              <XAxis type="number" domain={[0, 100]} tick={{ fill: '#64748b', fontSize: 11 }} />
              <YAxis type="category" dataKey="skill" tick={{ fill: '#94a3b8', fontSize: 11 }} width={80} />
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }} />
              <Bar dataKey="avg_mastery" fill="#6366f1" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Assessment performance */}
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <h3 className="text-sm font-semibold text-slate-200 mb-3">Assessment Performance</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={data.assessment_performance}>
              <XAxis dataKey="skill" tick={{ fill: '#94a3b8', fontSize: 10 }} angle={-20} textAnchor="end" height={50} />
              <YAxis tick={{ fill: '#64748b', fontSize: 11 }} />
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }} />
              <Bar dataKey="avg_mastery" fill="#22c55e" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* At-risk learners */}
      {data.at_risk_learners.length > 0 && (
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <h3 className="text-sm font-semibold text-rose-400 mb-3 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" /> At-Risk Learners
          </h3>
          <div className="space-y-2">
            {data.at_risk_learners.map((l, i) => (
              <div key={i} className="flex items-center justify-between p-2 rounded-lg bg-slate-950/60 border border-slate-800 text-sm">
                <span className="text-slate-200">{l.student_name}</span>
                <div className="flex items-center gap-3 text-xs text-slate-500">
                  <span>{l.career_role}</span>
                  <span className="text-rose-400 font-medium">{l.readiness.toFixed(0)}% readiness</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Mentor performance */}
      {data.mentor_performance.length > 0 && (
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <h3 className="text-sm font-semibold text-slate-200 mb-3">Mentor Performance</h3>
          <div className="space-y-2">
            {data.mentor_performance.map((m, i) => (
              <div key={i} className="flex items-center justify-between p-2 rounded-lg bg-slate-950/60 border border-slate-800 text-sm">
                <span className="text-slate-200">{m.name}</span>
                <div className="flex items-center gap-3 text-xs text-slate-500">
                  <span>{m.student_count} students</span>
                  <span>{m.doubts_answered} doubts</span>
                  <span className={m.is_active ? 'text-emerald-400' : 'text-rose-400'}>{m.is_active ? 'Active' : 'Inactive'}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
