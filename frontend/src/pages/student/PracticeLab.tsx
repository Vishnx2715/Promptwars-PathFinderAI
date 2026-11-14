import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { listProblems } from '../../api/practice';
import { Code2, CheckCircle2, Clock, Filter } from 'lucide-react';

const difficultyColors: Record<string, string> = {
  easy: 'text-emerald-400 bg-emerald-950/50 border-emerald-800/50',
  medium: 'text-amber-400 bg-amber-950/50 border-amber-800/50',
  hard: 'text-rose-400 bg-rose-950/50 border-rose-800/50',
};

export const PracticeLab: React.FC = () => {
  const [filters, setFilters] = useState({
    language: '',
    difficulty: '',
    status: '',
  });

  const { data: problems, isLoading } = useQuery({
    queryKey: ['practiceProblems', filters],
    queryFn: () => listProblems({
      language: filters.language || undefined,
      difficulty: filters.difficulty || undefined,
      status: filters.status || undefined,
    }),
  });

  return (
    <div className="space-y-6 pb-12">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-indigo-950/80 text-indigo-400 flex items-center justify-center">
          <Code2 className="w-5 h-5" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">Practice Lab</h1>
          <p className="text-sm text-slate-400">Sharpen your coding skills with real problems</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-center">
        <Filter className="w-4 h-4 text-slate-500" />
        <select
          value={filters.language}
          onChange={(e) => setFilters({ ...filters, language: e.target.value })}
          className="bg-slate-900 border border-slate-700 text-slate-200 text-sm rounded-lg px-3 py-2 outline-none focus:border-indigo-500"
        >
          <option value="">All Languages</option>
          <option value="javascript">JavaScript</option>
          <option value="python">Python</option>
        </select>
        <select
          value={filters.difficulty}
          onChange={(e) => setFilters({ ...filters, difficulty: e.target.value })}
          className="bg-slate-900 border border-slate-700 text-slate-200 text-sm rounded-lg px-3 py-2 outline-none focus:border-indigo-500"
        >
          <option value="">All Difficulties</option>
          <option value="easy">Easy</option>
          <option value="medium">Medium</option>
          <option value="hard">Hard</option>
        </select>
        <select
          value={filters.status}
          onChange={(e) => setFilters({ ...filters, status: e.target.value })}
          className="bg-slate-900 border border-slate-700 text-slate-200 text-sm rounded-lg px-3 py-2 outline-none focus:border-indigo-500"
        >
          <option value="">All Status</option>
          <option value="solved">Solved</option>
          <option value="attempted">Attempted</option>
          <option value="unsolved">Unsolved</option>
        </select>
      </div>

      {/* Problem list */}
      {isLoading ? (
        <div className="text-center text-slate-500 py-12">Loading problems...</div>
      ) : !problems || problems.length === 0 ? (
        <div className="text-center text-slate-500 py-12">
          <Code2 className="w-12 h-12 mx-auto mb-3 opacity-30" />
          <p>No problems found. Try adjusting your filters.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {problems.map((p) => (
            <Link
              key={p.id}
              to={`/practice/${p.id}`}
              className="group p-5 rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 transition-all"
            >
              <div className="flex items-start justify-between mb-3">
                <h3 className="text-base font-semibold text-slate-100 group-hover:text-indigo-400 transition-colors">
                  {p.title}
                </h3>
                {p.is_solved && (
                  <CheckCircle2 className="w-5 h-5 text-emerald-500 shrink-0" />
                )}
              </div>
              <div className="flex flex-wrap items-center gap-2 text-xs">
                <span className="px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 border border-slate-700">
                  {p.language === 'javascript' ? 'JS' : 'PY'}
                </span>
                <span className="text-slate-500">{p.skill_name}</span>
                <span className="text-slate-600">/</span>
                <span className="text-slate-500">{p.subtopic}</span>
                <span className={`px-2 py-0.5 rounded-md border ${difficultyColors[p.difficulty] || ''}`}>
                  {p.difficulty}
                </span>
              </div>
              <div className="flex items-center gap-4 mt-3 text-xs text-slate-500">
                <span className="flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5" /> {p.acceptance_rate}% acceptance
                </span>
                <span>{p.total_submissions} attempts</span>
                {p.is_attempted && !p.is_solved && (
                  <span className="text-amber-400">Attempted</span>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
};
