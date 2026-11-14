import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { listCodingProblems } from '../../api/admin';
import { Database } from 'lucide-react';

export const CodingProblemManagement: React.FC = () => {
  const { data: problems } = useQuery({ queryKey: ['adminCodingProblems'], queryFn: listCodingProblems });

  return (
    <div className="space-y-6 pb-12">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-cyan-950/80 text-cyan-400 flex items-center justify-center">
          <Database className="w-5 h-5" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">Coding Problems</h1>
          <p className="text-sm text-slate-400">View and manage practice problems</p>
        </div>
      </div>

      <div className="space-y-2">
        {problems?.map((p: any) => (
          <div key={p.id} className="flex items-center justify-between p-4 rounded-xl bg-slate-900 border border-slate-800">
            <div>
              <p className="text-sm font-semibold text-slate-100">{p.title}</p>
              <div className="flex items-center gap-2 mt-1 text-xs text-slate-500">
                <span>{p.language}</span>
                <span>•</span>
                <span>{p.skill_name}</span>
                <span>•</span>
                <span>{p.subtopic}</span>
                <span>•</span>
                <span className="capitalize">{p.difficulty}</span>
              </div>
            </div>
            <span className={`text-xs font-medium ${p.is_active ? 'text-emerald-400' : 'text-rose-400'}`}>
              {p.is_active ? 'Active' : 'Inactive'}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};
