import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getMentorDoubts, answerDoubt } from '../../api/doubt';
import { MessageSquare, Bot, Send, CheckCircle2 } from 'lucide-react';

export const DoubtQueue: React.FC = () => {
  const queryClient = useQueryClient();
  const [responses, setResponses] = useState<Record<number, string>>({});

  const { data: doubts } = useQuery({ queryKey: ['mentorDoubts'], queryFn: getMentorDoubts });

  const answerMutation = useMutation({
    mutationFn: ({ id, response, status }: { id: number; response: string; status: string }) =>
      answerDoubt(id, { mentor_response: response, status }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['mentorDoubts'] }),
  });

  const statusColors: Record<string, string> = {
    open: 'text-amber-400 bg-amber-950/40 border-amber-800/50',
    answered: 'text-indigo-400 bg-indigo-950/40 border-indigo-800/50',
    resolved: 'text-emerald-400 bg-emerald-950/40 border-emerald-800/50',
  };

  return (
    <div className="space-y-6 pb-12">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-blue-950/80 text-blue-400 flex items-center justify-center">
          <MessageSquare className="w-5 h-5" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">Doubt Queue</h1>
          <p className="text-sm text-slate-400">Review and answer student doubts</p>
        </div>
      </div>

      {(!doubts || doubts.length === 0) ? (
        <div className="text-center py-12">
          <MessageSquare className="w-12 h-12 mx-auto mb-3 opacity-30 text-slate-500" />
          <p className="text-slate-500 text-sm">No doubts from your mentees yet.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {doubts.map((d) => (
            <div key={d.id} className="p-4 rounded-xl bg-slate-900 border border-slate-800">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <span className="text-sm font-semibold text-slate-100">{d.student_name || 'Student'}</span>
                  <span className="text-xs text-slate-500 ml-2">{d.subject}</span>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded border ${statusColors[d.status]}`}>{d.status}</span>
              </div>
              <p className="text-sm text-slate-300 mb-3">{d.question}</p>

              {d.ai_draft_answer && (
                <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 mb-3">
                  <div className="flex items-center gap-1.5 mb-1">
                    <Bot className="w-3.5 h-3.5 text-indigo-400" />
                    <span className="text-xs font-medium text-indigo-400">AI Draft Answer</span>
                  </div>
                  <p className="text-xs text-slate-400">{d.ai_draft_answer}</p>
                </div>
              )}

              {d.mentor_response && (
                <div className="p-3 rounded-lg bg-emerald-950/40 border border-emerald-800/50 mb-3">
                  <span className="text-xs font-medium text-emerald-400">Your Response</span>
                  <p className="text-xs text-slate-300 mt-1">{d.mentor_response}</p>
                </div>
              )}

              {d.status === 'open' && (
                <div className="space-y-2">
                  <textarea
                    value={responses[d.id] || ''}
                    onChange={(e) => setResponses({ ...responses, [d.id]: e.target.value })}
                    placeholder="Write your response..."
                    rows={3}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 outline-none focus:border-indigo-500"
                  />
                  <div className="flex gap-2">
                    <button
                      onClick={() => answerMutation.mutate({ id: d.id, response: responses[d.id] || '', status: 'answered' })}
                      disabled={answerMutation.isPending || !responses[d.id]}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium disabled:opacity-50"
                    >
                      <Send className="w-3.5 h-3.5" /> Send Answer
                    </button>
                  </div>
                </div>
              )}

              {d.status === 'answered' && (
                <button
                  onClick={() => answerMutation.mutate({ id: d.id, response: d.mentor_response || '', status: 'resolved' })}
                  className="flex items-center gap-1.5 text-xs text-emerald-400 hover:text-emerald-300 font-medium"
                >
                  <CheckCircle2 className="w-3.5 h-3.5" /> Mark Resolved
                </button>
              )}

              <p className="text-xs text-slate-600 mt-2">{new Date(d.created_at).toLocaleString()}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
