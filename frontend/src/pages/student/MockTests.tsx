import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import api from '../../api/axios';
import { Award, ClipboardList, TrendingUp } from 'lucide-react';

export const MockTests: React.FC = () => {
  const { data: assessments, isLoading } = useQuery({
    queryKey: ['assessments'],
    queryFn: async () => {
      const res = await api.get('/assessments/');
      return res.data as any[];
    },
  });

  const { data: history } = useQuery({
    queryKey: ['assessmentHistory'],
    queryFn: async () => {
      const res = await api.get('/assessments/history');
      return res.data as any[];
    },
  });

  return (
    <div className="space-y-6 pb-12">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-amber-950/80 text-amber-400 flex items-center justify-center">
          <Award className="w-5 h-5" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">Assessments</h1>
          <p className="text-sm text-slate-400">Test your knowledge and track mastery</p>
        </div>
      </div>

      {/* Available assessments */}
      <div>
        <h2 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
          <ClipboardList className="w-4 h-4 text-slate-400" /> Available Tests
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {(assessments || []).map((a: any) => (
            <div key={a.id} className="p-4 rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 transition-all">
              <div className="flex items-start justify-between mb-2">
                <h3 className="text-base font-semibold text-slate-100">{a.title}</h3>
                <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                  {a.assessment_type}
                </span>
              </div>
              <div className="text-xs text-slate-500 mb-3">
                {a.skill_name} • {a.total_questions} questions
              </div>
              <Link
                to={`/assessment/${a.id}`}
                className="text-xs font-medium text-indigo-400 hover:text-indigo-300"
              >
                Start Assessment →
              </Link>
            </div>
          ))}
        </div>
      </div>

      {/* History */}
      <div>
        <h2 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-slate-400" /> Recent Results
        </h2>
        {history && history.length > 0 ? (
          <div className="space-y-2">
            {history.slice(0, 10).map((h: any, i: number) => (
              <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-slate-900 border border-slate-800 text-sm">
                <div className="flex items-center gap-3">
                  <span className={`w-2 h-2 rounded-full ${h.mastery_percentage >= 75 ? 'bg-emerald-500' : h.mastery_percentage >= 50 ? 'bg-amber-500' : 'bg-rose-500'}`} />
                  <Link to={`/assessment/result/${h.attempt_id}`} className="text-slate-200 hover:text-indigo-400 font-medium">
                    View Result
                  </Link>
                </div>
                <div className="flex items-center gap-4 text-xs text-slate-400">
                  <span className={`font-semibold ${h.mastery_percentage >= 75 ? 'text-emerald-400' : h.mastery_percentage >= 50 ? 'text-amber-400' : 'text-rose-400'}`}>
                    {h.mastery_percentage}%
                  </span>
                  <span>{new Date(h.submitted_at).toLocaleDateString()}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-slate-500 text-center py-6">No assessments completed yet. Start one above!</p>
        )}
      </div>
    </div>
  );
};
