import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { listQuestions } from '../../api/admin';
import { FileQuestion } from 'lucide-react';

export const QuestionBank: React.FC = () => {
  const { data: questions } = useQuery({ queryKey: ['adminQuestions'], queryFn: () => listQuestions() });

  return (
    <div className="space-y-6 pb-12">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-amber-950/80 text-amber-400 flex items-center justify-center">
          <FileQuestion className="w-5 h-5" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">Question Bank</h1>
          <p className="text-sm text-slate-400">View and manage assessment questions</p>
        </div>
      </div>

      <div className="space-y-2">
        {questions?.map((q: any) => (
          <div key={q.id} className="flex items-start justify-between p-4 rounded-xl bg-slate-900 border border-slate-800">
            <div className="flex-1">
              <p className="text-sm text-slate-200">{q.question_text}</p>
              <div className="flex items-center gap-2 mt-1 text-xs text-slate-500">
                <span>{q.skill_name}</span>
                <span>•</span>
                <span>{q.subtopic}</span>
                <span>•</span>
                <span className="capitalize">{q.difficulty}</span>
                <span>•</span>
                <span>{q.marks} marks</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
