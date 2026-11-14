import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { listProjects, getProjectDetail, submitProject } from '../../api/project';
import { FolderGit2, Upload, CheckCircle2, Clock, AlertCircle } from 'lucide-react';
const statusColors: Record<string, { color: string; bg: string; icon: any }> = {
  pending: { color: 'text-slate-400', bg: 'bg-slate-800/50 border-slate-700', icon: Clock },
  evaluating: { color: 'text-amber-400', bg: 'bg-amber-950/40 border-amber-800/50', icon: Clock },
  evaluated: { color: 'text-emerald-400', bg: 'bg-emerald-950/40 border-emerald-800/50', icon: CheckCircle2 },
  failed: { color: 'text-rose-400', bg: 'bg-rose-950/40 border-rose-800/50', icon: AlertCircle },
};

export const ProjectSubmission: React.FC = () => {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [selectedProject, setSelectedProject] = useState<number | null>(null);
  const [form, setForm] = useState({
    title: '', project_type: 'frontend', description: '',
    github_url: '', live_url: '',
  });
  const [file, setFile] = useState<File | null>(null);

  const { data: projects, isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: listProjects,
  });

  const { data: projectDetail } = useQuery({
    queryKey: ['projectDetail', selectedProject],
    queryFn: () => getProjectDetail(selectedProject!),
    enabled: !!selectedProject,
  });

  const submitMutation = useMutation({
    mutationFn: async () => {
      const formData = new FormData();
      formData.append('title', form.title);
      formData.append('project_type', form.project_type);
      formData.append('description', form.description);
      if (form.github_url) formData.append('github_url', form.github_url);
      if (form.live_url) formData.append('live_url', form.live_url);
      if (file) formData.append('file', file);
      return submitProject(formData);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      setShowForm(false);
      setForm({ title: '', project_type: 'frontend', description: '', github_url: '', live_url: '' });
      setFile(null);
    },
  });

  const projectTypes = ['frontend', 'backend', 'full_stack', 'data_analysis', 'machine_learning'];

  return (
    <div className="space-y-6 pb-12">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-cyan-950/80 text-cyan-400 flex items-center justify-center">
            <FolderGit2 className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Projects</h1>
            <p className="text-sm text-slate-400">Submit projects for AI evaluation and build your portfolio</p>
          </div>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium transition-colors"
        >
          {showForm ? 'Cancel' : 'Submit Project'}
        </button>
      </div>

      {/* Submit form */}
      {showForm && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
          <h3 className="text-base font-semibold text-slate-200">New Project Submission</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Project Title *</label>
              <input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 outline-none focus:border-indigo-500" />
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Project Type *</label>
              <select value={form.project_type} onChange={(e) => setForm({ ...form, project_type: e.target.value })}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 outline-none focus:border-indigo-500">
                {projectTypes.map((t) => <option key={t} value={t}>{t.replace('_', ' ')}</option>)}
              </select>
            </div>
          </div>
          <div>
            <label className="text-xs text-slate-400 mb-1 block">Description *</label>
            <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })}
              rows={3} className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 outline-none focus:border-indigo-500" />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-slate-400 mb-1 block">GitHub URL</label>
              <input value={form.github_url} onChange={(e) => setForm({ ...form, github_url: e.target.value })}
                placeholder="https://github.com/..."
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 outline-none focus:border-indigo-500" />
            </div>
            <div>
              <label className="text-xs text-slate-400 mb-1 block">Live URL</label>
              <input value={form.live_url} onChange={(e) => setForm({ ...form, live_url: e.target.value })}
                placeholder="https://..."
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 outline-none focus:border-indigo-500" />
            </div>
          </div>
          <div>
            <label className="text-xs text-slate-400 mb-1 block">Upload File (optional, max 5MB)</label>
            <input type="file" onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="w-full text-sm text-slate-400 file:mr-3 file:py-2 file:px-3 file:rounded-lg file:border-0 file:bg-slate-800 file:text-slate-200" />
          </div>
          {submitMutation.isError && (
            <p className="text-sm text-rose-400">{(submitMutation.error as any)?.response?.data?.detail || 'Submission failed'}</p>
          )}
          <button
            onClick={() => submitMutation.mutate()}
            disabled={submitMutation.isPending || !form.title || !form.description}
            className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium disabled:opacity-50"
          >
            {submitMutation.isPending ? 'Submitting...' : 'Submit for Evaluation'}
          </button>
          <p className="text-xs text-slate-500">Evaluation runs in the background. Check back shortly for results.</p>
        </div>
      )}

      {/* Project list */}
      {isLoading ? (
        <p className="text-center text-slate-500 py-8">Loading projects...</p>
      ) : !projects || projects.length === 0 ? (
        <div className="text-center py-12">
          <FolderGit2 className="w-12 h-12 mx-auto mb-3 opacity-30 text-slate-500" />
          <p className="text-slate-500">No projects submitted yet. Click "Submit Project" to start!</p>
        </div>
      ) : (
        <div className="space-y-3">
          {projects.map((p) => {
            const statusInfo = statusColors[p.status] || statusColors.pending;
            const StatusIcon = statusInfo.icon;
            return (
              <div key={p.id} className="p-4 rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 transition-all">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="text-base font-semibold text-slate-100">{p.title}</h3>
                    <div className="flex items-center gap-2 mt-1 text-xs text-slate-500">
                      <span>{p.project_type.replace('_', ' ')}</span>
                      <span>•</span>
                      <span className="flex items-center gap-1">
                        <StatusIcon className={`w-3.5 h-3.5 ${statusInfo.color}`} />
                        {p.status}
                      </span>
                      {p.evaluation_score !== null && p.evaluation_score !== undefined && (
                        <>
                          <span>•</span>
                          <span className="text-emerald-400 font-medium">{p.evaluation_score}/100</span>
                        </>
                      )}
                    </div>
                  </div>
                  {p.status === 'evaluated' && (
                    <button onClick={() => setSelectedProject(p.id)}
                      className="text-xs text-indigo-400 hover:text-indigo-300 font-medium">
                      View Report →
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Evaluation report modal */}
      {projectDetail && projectDetail.evaluation_report && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4" onClick={() => setSelectedProject(null)}>
          <div className="bg-slate-900 border border-slate-700 rounded-2xl max-w-3xl w-full max-h-[80vh] overflow-y-auto p-6 space-y-4" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-bold text-white">{projectDetail.evaluation_report.project_title || projectDetail.title}</h2>
              <button onClick={() => setSelectedProject(null)} className="text-slate-400 hover:text-white">✕</button>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-3xl font-bold text-indigo-400">{projectDetail.evaluation_report.overall_score?.toFixed(0) || 'N/A'}/100</div>
              <div className="text-sm">
                <div className="text-slate-200 font-medium">{projectDetail.evaluation_report.verdict}</div>
                <div className="text-slate-500">Portfolio: {projectDetail.evaluation_report.portfolio_readiness}</div>
              </div>
            </div>
            {projectDetail.evaluation_report.strengths?.length > 0 && (
              <div><h3 className="text-sm font-semibold text-emerald-400 mb-1">Strengths</h3>
                <ul className="text-sm text-slate-300 list-disc list-inside">{projectDetail.evaluation_report.strengths.map((s: string, i: number) => <li key={i}>{s}</li>)}</ul>
              </div>
            )}
            {projectDetail.evaluation_report.weaknesses?.length > 0 && (
              <div><h3 className="text-sm font-semibold text-amber-400 mb-1">Weaknesses</h3>
                {projectDetail.evaluation_report.weaknesses.map((w: any, i: number) => (
                  <div key={i} className="p-2 rounded-lg bg-slate-950/60 border border-slate-800 text-sm mb-1">
                    <span className="font-medium text-slate-200">{w.area}</span>: <span className="text-slate-400">{w.issue}</span>
                    <p className="text-xs text-indigo-400 mt-1">Improvement: {w.improvement}</p>
                  </div>
                ))}
              </div>
            )}
            {projectDetail.evaluation_report.limitations?.length > 0 && (
              <div><h3 className="text-sm font-semibold text-slate-400 mb-1">Limitations</h3>
                <ul className="text-sm text-slate-500 list-disc list-inside">{projectDetail.evaluation_report.limitations.map((l: string, i: number) => <li key={i}>{l}</li>)}</ul>
              </div>
            )}
            {projectDetail.evaluation_report.next_improvements?.length > 0 && (
              <div><h3 className="text-sm font-semibold text-indigo-400 mb-1">Next Improvements</h3>
                <ul className="text-sm text-slate-300 list-disc list-inside">{projectDetail.evaluation_report.next_improvements.map((n: string, i: number) => <li key={i}>{n}</li>)}</ul>
              </div>
            )}
            {projectDetail.evaluation_report.verified_skills?.length > 0 && (
              <div><h3 className="text-sm font-semibold text-emerald-400 mb-1">Verified Skills</h3>
                <div className="flex flex-wrap gap-2">{projectDetail.evaluation_report.verified_skills.map((v: any, i: number) => (
                  <span key={i} className="px-2 py-1 rounded-md bg-slate-800 border border-slate-700 text-xs text-slate-300">{v.skill} ({v.confidence})</span>
                ))}</div>
              </div>
            )}
            {projectDetail.evaluation_report.rubric_scores?.length > 0 && (
              <div><h3 className="text-sm font-semibold text-slate-200 mb-2">Rubric Scores</h3>
                {projectDetail.evaluation_report.rubric_scores.map((r: any, i: number) => (
                  <div key={i} className="flex items-center gap-3 mb-1">
                    <span className="text-sm text-slate-300 w-40">{r.criterion}</span>
                    <div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden">
                      <div className="h-full bg-indigo-500 rounded-full" style={{ width: `${(r.score / r.max_score) * 100}%` }} />
                    </div>
                    <span className="text-xs text-slate-400">{r.score}/{r.max_score}</span>
                  </div>
                ))}
              </div>
            )}
            <div className="text-xs text-slate-500">
              Mentor review required: {projectDetail.evaluation_report.mentor_review_required ? 'Yes' : 'No'}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
