import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { listUsers, toggleUserActive } from '../../api/admin';
import { UserCog, CheckCircle2, XCircle } from 'lucide-react';

export const UserManagement: React.FC = () => {
  const queryClient = useQueryClient();
  const [roleFilter, setRoleFilter] = useState('');
  const { data: users } = useQuery({ queryKey: ['adminUsers', roleFilter], queryFn: () => listUsers(roleFilter || undefined) });
  const toggleMutation = useMutation({
    mutationFn: (id: number) => toggleUserActive(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['adminUsers'] }),
  });

  return (
    <div className="space-y-6 pb-12">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-indigo-950/80 text-indigo-400 flex items-center justify-center">
          <UserCog className="w-5 h-5" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">User Management</h1>
          <p className="text-sm text-slate-400">View and manage all platform users</p>
        </div>
      </div>

      <select value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)}
        className="bg-slate-900 border border-slate-700 text-slate-200 text-sm rounded-lg px-3 py-2 outline-none focus:border-indigo-500">
        <option value="">All Roles</option>
        <option value="student">Students</option>
        <option value="mentor">Mentors</option>
        <option value="admin">Admins</option>
      </select>

      <div className="space-y-2">
        {users?.map((u) => (
          <div key={u.id} className="flex items-center justify-between p-4 rounded-xl bg-slate-900 border border-slate-800">
            <div>
              <p className="text-sm font-semibold text-slate-100">{u.username} <span className="text-xs text-slate-500 ml-2">{u.email}</span></p>
              <div className="flex items-center gap-2 mt-1 text-xs text-slate-500">
                <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700 capitalize">{u.role}</span>
                {u.profile_name && <span>Profile: {u.profile_name}</span>}
                {u.mentor_code && <span className="text-indigo-400 font-mono">{u.mentor_code}</span>}
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className={`text-xs font-medium ${u.is_active ? 'text-emerald-400' : 'text-rose-400'}`}>
                {u.is_active ? 'Active' : 'Inactive'}
              </span>
              <button onClick={() => toggleMutation.mutate(u.id)}
                className={`p-2 rounded-lg ${u.is_active ? 'text-rose-400 hover:bg-rose-950/40' : 'text-emerald-400 hover:bg-emerald-950/40'}`}>
                {u.is_active ? <XCircle className="w-4 h-4" /> : <CheckCircle2 className="w-4 h-4" />}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
