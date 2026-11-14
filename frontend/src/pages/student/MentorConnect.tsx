import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { connectToMentor, getMyConnections, disconnectMentor, getMyFeedback } from '../../api/mentor';
import { Users, Link2, UserCheck, MessageSquare, Trash2 } from 'lucide-react';

export const MentorConnect: React.FC = () => {
  const queryClient = useQueryClient();
  const [mentorCode, setMentorCode] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const { data: connections } = useQuery({ queryKey: ['mentorConnections'], queryFn: getMyConnections });
  const { data: feedback } = useQuery({ queryKey: ['mentorFeedback'], queryFn: getMyFeedback });

  const connectMutation = useMutation({
    mutationFn: () => connectToMentor(mentorCode),
    onSuccess: (data) => {
      setSuccess(`Connected to ${data.mentor_name}!`);
      setError('');
      setMentorCode('');
      queryClient.invalidateQueries({ queryKey: ['mentorConnections'] });
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to connect');
      setSuccess('');
    },
  });

  const disconnectMutation = useMutation({
    mutationFn: (id: number) => disconnectMentor(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['mentorConnections'] }),
  });

  return (
    <div className="space-y-6 pb-12">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-purple-950/80 text-purple-400 flex items-center justify-center">
          <Users className="w-5 h-5" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">My Mentor</h1>
          <p className="text-sm text-slate-400">Connect with a mentor, view feedback, and manage your connection</p>
        </div>
      </div>

      {/* Connect card */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
        <h3 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
          <Link2 className="w-4 h-4 text-indigo-400" /> Connect to a Mentor
        </h3>
        <p className="text-xs text-slate-400 mb-4">Enter the unique code your mentor shared with you.</p>
        <div className="flex gap-2">
          <input
            value={mentorCode}
            onChange={(e) => setMentorCode(e.target.value)}
            placeholder="PF-MENTOR-XXXXXXXX"
            className="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 outline-none focus:border-indigo-500 font-mono uppercase"
          />
          <button
            onClick={() => connectMutation.mutate()}
            disabled={connectMutation.isPending || !mentorCode}
            className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium disabled:opacity-50"
          >
            {connectMutation.isPending ? 'Connecting...' : 'Connect'}
          </button>
        </div>
        {error && <p className="text-sm text-rose-400 mt-2">{error}</p>}
        {success && <p className="text-sm text-emerald-400 mt-2">{success}</p>}
      </div>

      {/* Current connections */}
      {connections && connections.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-slate-200 mb-3">Your Mentors</h3>
          <div className="space-y-2">
            {connections.filter((c) => c.status === 'connected').map((c) => (
              <div key={c.id} className="flex items-center justify-between p-4 rounded-xl bg-slate-900 border border-slate-800">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-indigo-950 border border-indigo-700 flex items-center justify-center">
                    <UserCheck className="w-5 h-5 text-indigo-400" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-slate-100">{c.mentor_name}</p>
                    <p className="text-xs text-slate-500">{c.mentor_expertise}</p>
                  </div>
                </div>
                <button
                  onClick={() => disconnectMutation.mutate(c.id)}
                  className="p-2 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Mentor feedback */}
      {feedback && feedback.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
            <MessageSquare className="w-4 h-4 text-slate-400" /> Mentor Feedback
          </h3>
          <div className="space-y-2">
            {feedback.map((f) => (
              <div key={f.id} className="p-4 rounded-xl bg-slate-900 border border-slate-800">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">{f.feedback_type}</span>
                  <span className="text-xs text-slate-500">{new Date(f.created_at).toLocaleDateString()}</span>
                </div>
                <p className="text-sm text-slate-300">{f.comment}</p>
                {f.recommended_action && (
                  <p className="text-xs text-indigo-400 mt-1">→ {f.recommended_action}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
