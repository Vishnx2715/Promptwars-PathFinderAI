import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { submitDoubt, getMyDoubts, resolveDoubt } from '../../api/doubt';
import { MessageSquare, Send, CheckCircle2, Bot, User } from 'lucide-react';

export const Doubts: React.FC = () => {
  const queryClient = useQueryClient();
  const [form, setForm] = useState({ subject: '', question: '' });

  const { data: doubts } = useQuery({ queryKey: ['myDoubts'], queryFn: getMyDoubts });

  const submitMutation = useMutation({
    mutationFn: () => submitDoubt(form),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['myDoubts'] });
      setForm({ subject: '', question: '' });
    },
  });

  const resolveMutation = useMutation({
    mutationFn: (id: number) => resolveDoubt(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['myDoubts'] }),
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
          <h1 className="text-2xl font-bold text-white">Doubts</h1>
          <p className="text-sm text-slate-400">Ask questions and get AI-drafted answers reviewed by your mentor</p>
        </div>
      </div>

      {/* Submit doubt form */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-3">
        <h3 className="text-sm font-semibold text-slate-200">Ask a Question</h3>
        <input
          value={form.subject}
          onChange={(e) => setForm({ ...form, subject: e.target.value })}
          placeholder="Subject (e.g., How do closures work?)"
          className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 outline-none focus:border-indigo-500"
        />
        <textarea
          value={form.question}
          onChange={(e) => setForm({ ...form, question: e.target.value })}
          placeholder="Describe your doubt in detail..."
          rows={3}
          className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 outline-none focus:border-indigo-500"
        />
        {submitMutation.isError && (
          <p className="text-sm text-rose-400">Failed to submit. Make sure you're connected to a mentor.</p>
        )}
        <button
          onClick={() => submitMutation.mutate()}
          disabled={submitMutation.isPending || !form.subject || !form.question}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium disabled:opacity-50"
        >
          <Send className="w-4 h-4" /> {submitMutation.isPending ? 'Submitting...' : 'Submit Doubt'}
        </button>
      </div>

      {/* Doubt list */}
      {doubts && doubts.length > 0 && (
        <div className="space-y-3">
          {doubts.map((d) => (
            <div key={d.id} className="p-4 rounded-xl bg-slate-900 border border-slate-800">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-semibold text-slate-100">{d.subject}</h4>
                <span className={`text-xs px-2 py-0.5 rounded border ${statusColors[d.status]}`}>{d.status}</span>
              </div>
              <p className="text-sm text-slate-300 mb-3">{d.question}</p>
              {d.ai_draft_answer && (
                <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 mb-2">
                  <div className="flex items-center gap-1.5 mb-1">
                    <Bot className="w-3.5 h-3.5 text-indigo-400" />
                    <span className="text-xs font-medium text-indigo-400">AI Draft Answer</span>
                  </div>
                  <p className="text-xs text-slate-300">{d.ai_draft_answer}</p>
                </div>
              )}
              {d.mentor_response && (
                <div className="p-3 rounded-lg bg-indigo-950/40 border border-indigo-800/50 mb-2">
                  <div className="flex items-center gap-1.5 mb-1">
                    <User className="w-3.5 h-3.5 text-emerald-400" />
                    <span className="text-xs font-medium text-emerald-400">Mentor Response</span>
                  </div>
                  <p className="text-xs text-slate-300">{d.mentor_response}</p>
                </div>
              )}
              {d.status === 'answered' && (
                <button
                  onClick={() => resolveMutation.mutate(d.id)}
                  className="flex items-center gap-1 text-xs text-emerald-400 hover:text-emerald-300 font-medium"
                >
                  <CheckCircle2 className="w-3.5 h-3.5" /> Mark as Resolved
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
