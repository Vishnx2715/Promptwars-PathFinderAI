import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getMenteeDetail, addMentorFeedback, assignAssessment } from '../../api/mentor';
import { ArrowLeft, Send, AlertTriangle } from 'lucide-react';

export const MenteeDetail: React.FC = () => {
  const { profileId } = useParams<{ profileId: string }>();
  const queryClient = useQueryClient();
  const [feedback, setFeedback] = useState({ comment: '', feedback_type: 'general' });
  const [assignSkillId, setAssignSkillId] = useState<number | ''>('');

  const { data: mentee, isLoading } = useQuery({
    queryKey: ['menteeDetail', profileId],
    queryFn: () => getMenteeDetail(Number(profileId)),
    enabled: !!profileId,
  });

  const feedbackMutation = useMutation({
    mutationFn: () => addMentorFeedback({
      student_profile_id: Number(profileId),
      feedback_type: feedback.feedback_type,
      comment: feedback.comment,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['menteeDetail', profileId] });
      setFeedback({ comment: '', feedback_type: 'general' });
    },
  });

  const assignMutation = useMutation({
    mutationFn: () => assignAssessment({ student_profile_id: Number(profileId), skill_id: Number(assignSkillId) }),
    onSuccess: () => setAssignSkillId(''),
  });

  if (isLoading) return <div className="text-center text-slate-500 py-12">Loading...</div>;
  if (!mentee) return <div className="text-center text-slate-500 py-12">Mentee not found</div>;

  const riskColors: Record<string, string> = {
    high: 'text-rose-400 bg-rose-950/40 border-rose-800/50',
    medium: 'text-amber-400 bg-amber-950/40 border-amber-800/50',
    low: 'text-emerald-400 bg-emerald-950/40 border-emerald-800/50',
  };

  return (
    <div className="space-y-6 pb-12">
      <Link to="/mentor/dashboard" className="text-sm text-slate-500 hover:text-indigo-400 flex items-center gap-1">
        <ArrowLeft className="w-4 h-4" /> Back to Dashboard
      </Link>

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">{mentee.student_name}</h1>
          <p className="text-sm text-slate-400">{mentee.career_goal || 'No goal set'}</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right">
            <div className="text-2xl font-bold text-indigo-400">{mentee.readiness_score.toFixed(0)}%</div>
            <p className="text-xs text-slate-500">Readiness</p>
          </div>
          <span className={`text-xs px-2 py-1 rounded border ${riskColors[mentee.ai_insight?.risk_level || 'low']}`}>
            {mentee.ai_insight?.risk_level || 'low'}
          </span>
        </div>
      </div>

      {/* AI Insight */}
      {mentee.ai_insight && (
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <h3 className="text-sm font-semibold text-indigo-400 mb-2">AI Insight</h3>
          <p className="text-sm text-slate-300 mb-2">{mentee.ai_insight.ai_summary}</p>
          <div className="text-xs text-slate-400">
            <p><strong className="text-slate-300">Primary blocker:</strong> {mentee.ai_insight.primary_blocker}</p>
            <p><strong className="text-slate-300">Recommended action:</strong> {mentee.ai_insight.recommended_mentor_action}</p>
          </div>
          {mentee.ai_insight.weak_areas?.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {mentee.ai_insight.weak_areas.map((w, i) => (
                <span key={i} className="text-xs px-2 py-0.5 rounded bg-rose-950/40 border border-rose-800/50 text-rose-400">{w}</span>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Skill mastery */}
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <h3 className="text-sm font-semibold text-slate-200 mb-3">Skill Mastery</h3>
          <div className="space-y-2">
            {mentee.learner_skills.map((s, i) => (
              <div key={i}>
                <div className="flex items-center justify-between text-xs mb-1">
                  <span className="text-slate-300">{s.skill_name}</span>
                  <span className="text-slate-500">{s.mastery.toFixed(0)}%</span>
                </div>
                <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                  <div className={`h-full rounded-full ${s.mastery >= 75 ? 'bg-emerald-500' : s.mastery >= 50 ? 'bg-amber-500' : 'bg-rose-500'}`} style={{ width: `${s.mastery}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Roadmap */}
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <h3 className="text-sm font-semibold text-slate-200 mb-3">Roadmap Progress</h3>
          <div className="space-y-2">
            {mentee.roadmap_modules.map((m, i) => (
              <div key={i} className="flex items-center gap-2 text-xs">
                <span className={`w-2 h-2 rounded-full ${
                  m.status === 'completed' ? 'bg-emerald-500' :
                  m.status === 'available' ? 'bg-indigo-500' :
                  m.status === 'locked' ? 'bg-slate-600' :
                  m.status === 'needs_revision' ? 'bg-amber-500' : 'bg-slate-600'
                }`} />
                <span className="text-slate-300 flex-1">{m.title}</span>
                <span className="text-slate-500">{m.status}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Assessment history */}
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <h3 className="text-sm font-semibold text-slate-200 mb-3">Assessment History</h3>
          {mentee.assessment_history.length > 0 ? (
            <div className="space-y-1">
              {mentee.assessment_history.map((a, i) => (
                <div key={i} className="flex items-center justify-between text-xs">
                  <span className="text-slate-300">{a.title}</span>
                  <span className={`font-medium ${a.mastery >= 75 ? 'text-emerald-400' : a.mastery >= 50 ? 'text-amber-400' : 'text-rose-400'}`}>{a.mastery.toFixed(0)}%</span>
                </div>
              ))}
            </div>
          ) : <p className="text-xs text-slate-500">No assessments yet</p>}
        </div>

        {/* Coding stats + Projects */}
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <h3 className="text-sm font-semibold text-slate-200 mb-3">Practice & Projects</h3>
          <div className="text-xs text-slate-400 space-y-1 mb-3">
            <p>Coding submissions: {mentee.coding_stats.total_submissions}</p>
            <p>Solved: {mentee.coding_stats.solved}</p>
            <p>Accuracy: {mentee.coding_stats.accuracy}%</p>
          </div>
          {mentee.project_submissions.length > 0 && (
            <div className="space-y-1">
              {mentee.project_submissions.map((p, i) => (
                <div key={i} className="flex items-center justify-between text-xs">
                  <span className="text-slate-300">{p.title}</span>
                  <span className="text-slate-500">{p.status}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Feedback form */}
      <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
        <h3 className="text-sm font-semibold text-slate-200 mb-3">Add Feedback</h3>
        <div className="flex flex-col gap-3">
          <select value={feedback.feedback_type} onChange={(e) => setFeedback({ ...feedback, feedback_type: e.target.value })}
            className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 outline-none focus:border-indigo-500">
            <option value="general">General</option>
            <option value="roadmap">Roadmap</option>
            <option value="project">Project</option>
            <option value="assessment">Assessment</option>
          </select>
          <textarea value={feedback.comment} onChange={(e) => setFeedback({ ...feedback, comment: e.target.value })}
            placeholder="Write feedback..."
            rows={3}
            className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 outline-none focus:border-indigo-500" />
          <button onClick={() => feedbackMutation.mutate()} disabled={feedbackMutation.isPending || !feedback.comment}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium disabled:opacity-50 w-fit">
            <Send className="w-4 h-4" /> Send Feedback
          </button>
        </div>
      </div>

      {/* Assign assessment */}
      {mentee.weak_areas.length > 0 && (
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
          <h3 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400" /> Assign Revision Assessment
          </h3>
          <div className="flex gap-2">
            <select value={assignSkillId} onChange={(e) => setAssignSkillId(Number(e.target.value))}
              className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 outline-none focus:border-indigo-500">
              <option value="">Select skill...</option>
              {mentee.learner_skills.map((s, i) => (
                <option key={i} value={0}>{s.skill_name} (mastery: {s.mastery.toFixed(0)}%)</option>
              ))}
            </select>
            <button onClick={() => assignSkillId && assignMutation.mutate()} disabled={assignMutation.isPending || !assignSkillId}
              className="px-4 py-2 rounded-lg bg-amber-600 hover:bg-amber-500 text-white text-sm font-medium disabled:opacity-50">
              Assign
            </button>
          </div>
          {assignMutation.isSuccess && <p className="text-sm text-emerald-400 mt-2">Assessment assigned!</p>}
        </div>
      )}
    </div>
  );
};
