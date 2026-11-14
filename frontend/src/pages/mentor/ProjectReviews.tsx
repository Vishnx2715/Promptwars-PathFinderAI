import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { getMentees } from '../../api/mentor';
import { getStudentProjects } from '../../api/project';
import { FolderGit2 } from 'lucide-react';

export const ProjectReviews: React.FC = () => {
  const { data: mentees } = useQuery({ queryKey: ['mentees'], queryFn: getMentees });
  const [selectedMentee, setSelectedMentee] = React.useState<number | null>(null);

  const { data: projects } = useQuery({
    queryKey: ['studentProjects', selectedMentee],
    queryFn: () => getStudentProjects(selectedMentee!),
    enabled: !!selectedMentee,
  });

  const statusColors: Record<string, string> = {
    pending: 'text-slate-400',
    evaluating: 'text-amber-400',
    evaluated: 'text-emerald-400',
    failed: 'text-rose-400',
  };

  return (
    <div className="space-y-6 pb-12">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-cyan-950/80 text-cyan-400 flex items-center justify-center">
          <FolderGit2 className="w-5 h-5" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">Project Reviews</h1>
          <p className="text-sm text-slate-400">Review student project evaluations and add feedback</p>
        </div>
      </div>

      {/* Mentee selector */}
      <div className="flex flex-wrap gap-2">
        {mentees?.map((m) => (
          <button key={m.profile_id} onClick={() => setSelectedMentee(m.profile_id)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium border transition-colors ${
              selectedMentee === m.profile_id ? 'bg-indigo-600 text-white border-indigo-500' : 'bg-slate-900 text-slate-300 border-slate-700 hover:border-slate-600'
            }`}>
            {m.student_name}
          </button>
        ))}
      </div>

      {/* Projects */}
      {selectedMentee && (
        <div className="space-y-3">
          {!projects || projects.length === 0 ? (
            <p className="text-sm text-slate-500 text-center py-8">No projects from this student.</p>
          ) : (
            projects.map((p) => (
              <div key={p.id} className="p-4 rounded-xl bg-slate-900 border border-slate-800">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="text-sm font-semibold text-slate-100">{p.title}</h3>
                    <p className="text-xs text-slate-500 capitalize">{p.project_type.replace('_', ' ')}</p>
                  </div>
                  <div className="text-right">
                    <span className={`text-xs font-medium ${statusColors[p.status] || 'text-slate-400'}`}>{p.status}</span>
                    {p.evaluation_score !== null && p.evaluation_score !== undefined && (
                      <p className="text-lg font-bold text-indigo-400">{p.evaluation_score.toFixed(0)}/100</p>
                    )}
                  </div>
                </div>
                <p className="text-xs text-slate-600 mt-1">{new Date(p.submitted_at).toLocaleString()}</p>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};
