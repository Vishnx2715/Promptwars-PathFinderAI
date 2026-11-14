import React from 'react';
import { CheckCircle2, XCircle, Eye, EyeOff } from 'lucide-react';
import { TestResultItem } from '../types';

interface TestResultTableProps {
  results: TestResultItem[];
}

export const TestResultTable: React.FC<TestResultTableProps> = ({ results }) => {
  if (!results || results.length === 0) {
    return (
      <div className="text-center text-slate-500 py-8 text-sm">
        No test results yet. Run or submit your solution to see results.
      </div>
    );
  }

  const passed = results.filter((r) => r.passed).length;
  const total = results.length;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-semibold text-slate-200">
          Test Results: {passed}/{total} passed
        </span>
        <div className="w-32 h-2 bg-slate-800 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${
              passed === total ? 'bg-emerald-500' : passed > 0 ? 'bg-amber-500' : 'bg-rose-500'
            }`}
            style={{ width: `${(passed / total) * 100}%` }}
          />
        </div>
      </div>
      <div className="space-y-2">
        {results.map((r, i) => (
          <div
            key={i}
            className={`flex items-start gap-3 p-3 rounded-lg border ${
              r.passed
                ? 'bg-emerald-950/40 border-emerald-800/50'
                : 'bg-rose-950/40 border-rose-800/50'
            }`}
          >
            {r.passed ? (
              <CheckCircle2 className="w-5 h-5 text-emerald-500 shrink-0 mt-0.5" />
            ) : (
              <XCircle className="w-5 h-5 text-rose-500 shrink-0 mt-0.5" />
            )}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-slate-200">{r.name}</span>
                {r.is_hidden ? (
                  <span className="flex items-center gap-1 text-xs text-slate-500">
                    <EyeOff className="w-3 h-3" /> Hidden
                  </span>
                ) : (
                  <span className="flex items-center gap-1 text-xs text-slate-500">
                    <Eye className="w-3 h-3" /> Visible
                  </span>
                )}
              </div>
              {!r.passed && (
                <div className="mt-1 text-xs space-y-0.5">
                  <div className="text-slate-400">Expected: <code className="text-emerald-400">{r.expected}</code></div>
                  <div className="text-slate-400">Actual: <code className="text-rose-400">{r.actual || 'No output'}</code></div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
