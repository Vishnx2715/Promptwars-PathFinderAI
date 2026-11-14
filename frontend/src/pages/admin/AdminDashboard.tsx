import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { getAdminOverview } from '../../api/admin';
import { Shield, Users, Award, Code2, FolderGit2, AlertTriangle, TrendingUp } from 'lucide-react';

export const AdminDashboard: React.FC = () => {
  const { data: overview, isLoading } = useQuery({ queryKey: ['adminOverview'], queryFn: getAdminOverview });

  if (isLoading) return <div className="text-center text-slate-500 py-12">Loading...</div>;

  const stats = [
    { label: 'Total Students', value: overview?.total_students || 0, icon: Users, color: 'text-indigo-400 bg-indigo-950/50' },
    { label: 'Total Mentors', value: overview?.total_mentors || 0, icon: Users, color: 'text-purple-400 bg-purple-950/50' },
    { label: 'Active Paths', value: overview?.active_learning_paths || 0, icon: TrendingUp, color: 'text-emerald-400 bg-emerald-950/50' },
    { label: 'Assessments Done', value: overview?.total_assessments_completed || 0, icon: Award, color: 'text-amber-400 bg-amber-950/50' },
    { label: 'Coding Submissions', value: overview?.total_coding_submissions || 0, icon: Code2, color: 'text-cyan-400 bg-cyan-950/50' },
    { label: 'Projects Submitted', value: overview?.total_projects_submitted || 0, icon: FolderGit2, color: 'text-blue-400 bg-blue-950/50' },
    { label: 'Avg Readiness', value: `${(overview?.average_readiness_score || 0).toFixed(1)}%`, icon: Shield, color: 'text-teal-400 bg-teal-950/50' },
    { label: 'At-Risk Students', value: overview?.at_risk_student_count || 0, icon: AlertTriangle, color: 'text-rose-400 bg-rose-950/50' },
  ];

  return (
    <div className="space-y-6 pb-12">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-slate-800 text-slate-300 flex items-center justify-center">
          <Shield className="w-5 h-5" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">Admin Dashboard</h1>
          <p className="text-sm text-slate-400">Platform overview and management</p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {stats.map((s, i) => {
          const Icon = s.icon;
          return (
            <div key={i} className="p-4 rounded-xl bg-slate-900 border border-slate-800">
              <div className={`w-9 h-9 rounded-lg flex items-center justify-center mb-2 ${s.color}`}>
                <Icon className="w-4.5 h-4.5" />
              </div>
              <div className="text-2xl font-bold text-white">{s.value}</div>
              <p className="text-xs text-slate-500">{s.label}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
};
