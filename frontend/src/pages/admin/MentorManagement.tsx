import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { listMentors, createMentor, toggleMentorActive, listUsers } from '../../api/admin';
import { Users, Plus, CheckCircle2, XCircle } from 'lucide-react';

export const MentorManagement: React.FC = () => {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ user_id: '', full_name: '', expertise: '' });

  const { data: mentors } = useQuery({ queryKey: ['adminMentors'], queryFn: listMentors });
  const { data: users } = useQuery({ queryKey: ['adminUsers', 'student'], queryFn: () => listUsers('student') });

  const createMutation = useMutation({
    mutationFn: () => createMentor({
      user_id: Number(form.user_id),
      full_name: form.full_name,
      expertise: form.expertise,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['adminMentors'] });
      queryClient.invalidateQueries({ queryKey: ['adminUsers'] });
      setShowForm(false);
      setForm({ user_id: '', full_name: '', expertise: '' });
    },
  });

  const toggleMutation = useMutation({
    mutationFn: (id: number) => toggleMentorActive(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['adminMentors'] }),
  });

  return (
    <div className="space-y-6 pb-12">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-purple-950/80 text-purple-400 flex items-center justify-center">
            <Users className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Mentor Management</h1>
            <p className="text-sm text-slate-400">Create and manage mentors</p>
          </div>
        </div>
        <button onClick={() => setShowForm(!showForm)} className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium">
          <Plus className="w-4 h-4" /> Create Mentor
        </button>
      </div>

      {showForm && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-3">
          <div>
            <label className="text-xs text-slate-400 mb-1 block">Select User</label>
            <select value={form.user_id} onChange={(e) => setForm({ ...form, user_id: e.target.value })}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 outline-none focus:border-indigo-500">
              <option value="">Choose a student to promote...</option>
              {users?.map((u) => <option key={u.id} value={u.id}>{u.username} ({u.email})</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs text-slate-400 mb-1 block">Full Name</label>
            <input value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 outline-none focus:border-indigo-500" />
          </div>
          <div>
            <label className="text-xs text-slate-400 mb-1 block">Expertise</label>
            <input value={form.expertise} onChange={(e) => setForm({ ...form, expertise: e.target.value })}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 outline-none focus:border-indigo-500" />
          </div>
          <button onClick={() => createMutation.mutate()} disabled={createMutation.isPending || !form.user_id || !form.full_name}
            className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium disabled:opacity-50">
            {createMutation.isPending ? 'Creating...' : 'Create Mentor'}
          </button>
          {createMutation.isSuccess && <p className="text-sm text-emerald-400">Mentor created with unique code!</p>}
        </div>
      )}

      <div className="space-y-2">
        {mentors?.map((m: any) => (
          <div key={m.id} className="flex items-center justify-between p-4 rounded-xl bg-slate-900 border border-slate-800">
            <div>
              <p className="text-sm font-semibold text-slate-100">{m.full_name}</p>
              <div className="flex items-center gap-2 mt-1 text-xs text-slate-500">
                <span className="font-mono text-indigo-400">{m.mentor_code}</span>
                <span>•</span>
                <span>{m.student_count} students</span>
                <span>•</span>
                <span>{m.expertise}</span>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className={`text-xs font-medium ${m.is_active ? 'text-emerald-400' : 'text-rose-400'}`}>
                {m.is_active ? 'Active' : 'Inactive'}
              </span>
              <button onClick={() => toggleMutation.mutate(m.id)}
                className={`p-2 rounded-lg ${m.is_active ? 'text-rose-400 hover:bg-rose-950/40' : 'text-emerald-400 hover:bg-emerald-950/40'}`}>
                {m.is_active ? <XCircle className="w-4 h-4" /> : <CheckCircle2 className="w-4 h-4" />}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
