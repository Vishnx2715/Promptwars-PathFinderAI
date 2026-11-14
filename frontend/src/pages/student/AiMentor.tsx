import React, { useState, useRef, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import { sendMentorChat } from '../../api/analytics';
import { Sparkles, Send, Bot, ArrowRight, User, AlertTriangle } from 'lucide-react';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  nextAction?: { title: string; description: string; estimated_minutes?: number };
  escalate?: boolean;
}

const SUGGESTED = [
  'What should I learn next?',
  'Why is a module locked?',
  'How can I improve my weakest skill?',
  'What project should I build now?',
  'Am I on track for my career goal?',
];

export const AiMentor: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);

  // Build history slice for backend (last 10 turns)
  const buildHistory = () =>
    messages.slice(-10).map((m) => ({ role: m.role, content: m.content }));

  const chatMutation = useMutation({
    mutationFn: (msg: string) => sendMentorChat(msg, buildHistory()),
    onSuccess: (data) => {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: data.answer,
          nextAction: data.next_best_action?.title ? data.next_best_action : undefined,
          escalate: data.escalate_to_mentor,
        },
      ]);
    },
    onError: () => {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'I ran into an issue. Please try again in a moment.' },
      ]);
    },
  });

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, chatMutation.isPending]);

  const handleSend = (text?: string) => {
    const msg = (text ?? input).trim();
    if (!msg || chatMutation.isPending) return;
    setMessages((prev) => [...prev, { role: 'user', content: msg }]);
    setInput('');
    chatMutation.mutate(msg);
  };

  return (
    <div className="h-[calc(100vh-7rem)] flex flex-col gap-3">
      {/* Header */}
      <div className="flex items-center gap-3 shrink-0 px-1">
        <div className="w-9 h-9 rounded-xl bg-indigo-950 border border-indigo-800 text-indigo-400 flex items-center justify-center">
          <Sparkles className="w-4 h-4" />
        </div>
        <div>
          <h1 className="text-lg font-bold text-white leading-tight">AI Career Mentor</h1>
          <p className="text-xs text-slate-500">Grounded in your roadmap, skills & progress</p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto rounded-xl bg-slate-900 border border-slate-800 p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center gap-4 text-center py-6">
            <div className="w-14 h-14 rounded-2xl bg-indigo-950 border border-indigo-800 flex items-center justify-center">
              <Bot className="w-7 h-7 text-indigo-400" />
            </div>
            <div>
              <p className="text-slate-200 font-semibold">Ask me anything about your career journey</p>
              <p className="text-xs text-slate-500 mt-1">I know your skills, roadmap, assessments and projects.</p>
            </div>
            <div className="flex flex-wrap justify-center gap-2 max-w-lg">
              {SUGGESTED.map((q) => (
                <button
                  key={q}
                  onClick={() => handleSend(q)}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-xs text-slate-300 hover:border-indigo-500 hover:text-indigo-300 transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg, i) => (
              <div key={i} className={`flex gap-2.5 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                {msg.role === 'assistant' && (
                  <div className="w-7 h-7 rounded-lg bg-indigo-950 border border-indigo-800 flex items-center justify-center shrink-0 mt-0.5">
                    <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                  </div>
                )}
                <div className={`max-w-[78%] space-y-2 ${msg.role === 'user' ? 'items-end' : 'items-start'} flex flex-col`}>
                  <div className={`rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                    msg.role === 'user'
                      ? 'bg-indigo-600 text-white rounded-tr-sm'
                      : 'bg-slate-800 text-slate-200 rounded-tl-sm'
                  }`}>
                    {msg.content}
                  </div>
                  {msg.nextAction && (
                    <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-slate-800/60 border border-indigo-800/50 text-xs text-indigo-300">
                      <ArrowRight className="w-3 h-3 shrink-0" />
                      <span>
                        <strong>{msg.nextAction.title}</strong>
                        {msg.nextAction.estimated_minutes
                          ? ` · ${msg.nextAction.estimated_minutes} min`
                          : ''}
                      </span>
                    </div>
                  )}
                  {msg.escalate && (
                    <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-amber-950/40 border border-amber-700/40 text-xs text-amber-300">
                      <AlertTriangle className="w-3 h-3 shrink-0" />
                      <span>Your mentor can help further — connect via Mentor Chat.</span>
                    </div>
                  )}
                </div>
                {msg.role === 'user' && (
                  <div className="w-7 h-7 rounded-lg bg-slate-700 flex items-center justify-center shrink-0 mt-0.5">
                    <User className="w-3.5 h-3.5 text-slate-300" />
                  </div>
                )}
              </div>
            ))}
            {chatMutation.isPending && (
              <div className="flex gap-2.5 justify-start">
                <div className="w-7 h-7 rounded-lg bg-indigo-950 border border-indigo-800 flex items-center justify-center shrink-0">
                  <Sparkles className="w-3.5 h-3.5 text-indigo-400 animate-pulse" />
                </div>
                <div className="bg-slate-800 rounded-2xl rounded-tl-sm px-4 py-2.5 text-sm text-slate-500">
                  <span className="animate-pulse">Thinking…</span>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </>
        )}
      </div>

      {/* Input */}
      <div className="flex gap-2 shrink-0">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
          placeholder="Ask your AI mentor…"
          className="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-4 py-3 text-sm text-slate-200 placeholder-slate-500 outline-none focus:border-indigo-500 transition-colors"
        />
        <button
          onClick={() => handleSend()}
          disabled={chatMutation.isPending || !input.trim()}
          className="px-4 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white transition-colors"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
