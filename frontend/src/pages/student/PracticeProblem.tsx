import React, { useState, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getProblem, runSampleTests, submitSolution, getSubmissionHistory } from '../../api/practice';
import { CodeEditor } from '../../components/CodeEditor';
import { TestResultTable } from '../../components/TestResultTable';
import { ArrowLeft, Play, Send, Lightbulb, History, ChevronRight } from 'lucide-react';

export const PracticeProblem: React.FC = () => {
  const { problemId } = useParams<{ problemId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [code, setCode] = useState('');
  const [testResults, setTestResults] = useState<any[]>([]);
  const [submitResult, setSubmitResult] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'tests' | 'review' | 'history'>('tests');
  const [isRunning, setIsRunning] = useState(false);
  const workerRef = useRef<Worker | null>(null);

  const { data: problem, isLoading } = useQuery({
    queryKey: ['practiceProblem', problemId],
    queryFn: () => getProblem(Number(problemId)),
    enabled: !!problemId,
  });

  const { data: history } = useQuery({
    queryKey: ['submissionHistory', problemId],
    queryFn: () => getSubmissionHistory(Number(problemId)),
    enabled: !!problemId,
  });

  // Initialize code from starter
  React.useEffect(() => {
    if (problem && !code) {
      setCode(problem.starter_code);
    }
  }, [problem]);

  // Execute JavaScript in a Web Worker sandbox
  const executeJS = (code: string, testCases: any[], functionName: string): Promise<any[]> => {
    return new Promise((resolve) => {
      const workerCode = `
        self.onmessage = function(e) {
          const { code, testCases, functionName } = e.data;
          const results = [];
          let userFunc;
          try {
            // eslint-disable-next-line no-eval
            eval(code);
            userFunc = eval(functionName);
            if (typeof userFunc !== 'function') {
              for (const tc of testCases) {
                results.push({ name: tc.name, passed: false, expected: String(tc.expected_output), actual: 'Function not found', is_hidden: tc.is_hidden });
              }
              self.postMessage(results);
              return;
            }
          } catch (err) {
            for (const tc of testCases) {
              results.push({ name: tc.name, passed: false, expected: String(tc.expected_output), actual: 'Error: ' + err.message, is_hidden: tc.is_hidden });
            }
            self.postMessage(results);
            return;
          }
          for (const tc of testCases) {
            try {
              const args = tc.function_args || tc.functionArgs || [];
              let result;
              if (Array.isArray(args) && args.length > 0 && Array.isArray(args[0])) {
                result = userFunc(...args[0]);
              } else {
                result = userFunc(...args);
              }
              const actual = String(result);
              const expected = String(tc.expected_output).trim();
              results.push({
                name: tc.name,
                passed: actual.trim() === expected,
                expected: expected,
                actual: actual,
                is_hidden: tc.is_hidden || false
              });
            } catch (err) {
              results.push({ name: tc.name, passed: false, expected: String(tc.expected_output), actual: 'Runtime error: ' + err.message, is_hidden: tc.is_hidden });
            }
          }
          self.postMessage(results);
        };
      `;

      const blob = new Blob([workerCode], { type: 'application/javascript' });
      const workerUrl = URL.createObjectURL(blob);
      const worker = new Worker(workerUrl);
      workerRef.current = worker;

      const timeout = setTimeout(() => {
        worker.terminate();
        resolve(testCases.map((tc) => ({
          name: tc.name,
          passed: false,
          expected: String(tc.expected_output),
          actual: 'Timeout (>5s)',
          is_hidden: tc.is_hidden,
        })));
      }, 5000);

      worker.onmessage = (e) => {
        clearTimeout(timeout);
        worker.terminate();
        resolve(e.data);
      };

      worker.postMessage({ code, testCases, functionName });
      URL.revokeObjectURL(workerUrl);
    });
  };

  const runTestsMutation = useMutation({
    mutationFn: async () => {
      if (!problem) return;
      setIsRunning(true);
      // For JavaScript, execute in browser sandbox
      if (problem.language === 'javascript') {
        const visibleCases = problem.visible_test_cases;
        const results = await executeJS(code, visibleCases, problem.function_name);
        setTestResults(results);
        return { results };
      } else {
        // For Python, call backend
        const data = await runSampleTests(Number(problemId), code, problem.language);
        setTestResults(data.results);
        return data;
      }
    },
    onSuccess: () => {
      setIsRunning(false);
      setActiveTab('tests');
    },
    onError: () => setIsRunning(false),
  });

  const submitMutation = useMutation({
    mutationFn: async () => {
      if (!problem) return;
      let frontendResults: any[] | undefined;

      if (problem.language === 'javascript') {
        // Execute ALL test cases (visible + hidden) in browser
        // We need to get all test cases from backend by calling run first
        // Actually, submit endpoint handles it. Let's run visible tests first,
        // then the backend will evaluate all.
        // For JS, we pass frontend results for the visible ones, backend handles the rest
        const allResults = await executeJS(code, problem.visible_test_cases, problem.function_name);
        frontendResults = allResults;
      }

      return await submitSolution(Number(problemId), code, problem.language, frontendResults);
    },
    onSuccess: (data) => {
      setSubmitResult(data);
      if (data) {
        setTestResults(data.test_results);
      }
      setActiveTab('tests');
      queryClient.invalidateQueries({ queryKey: ['practiceProblems'] });
      queryClient.invalidateQueries({ queryKey: ['submissionHistory', problemId] });
    },
  });

  if (isLoading) {
    return <div className="text-center text-slate-500 py-12">Loading problem...</div>;
  }

  if (!problem) {
    return <div className="text-center text-slate-500 py-12">Problem not found.</div>;
  }

  const difficultyColors: Record<string, string> = {
    easy: 'text-emerald-400 bg-emerald-950/50 border-emerald-800/50',
    medium: 'text-amber-400 bg-amber-950/50 border-amber-800/50',
    hard: 'text-rose-400 bg-rose-950/50 border-rose-800/50',
  };

  return (
    <div className="space-y-4 pb-12">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-slate-500">
        <Link to="/practice" className="hover:text-indigo-400 flex items-center gap-1">
          <ArrowLeft className="w-4 h-4" /> Practice Lab
        </Link>
        <ChevronRight className="w-4 h-4" />
        <span className="text-slate-300">{problem.title}</span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Left: Problem description */}
        <div className="space-y-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
            <div className="flex items-start justify-between">
              <h1 className="text-xl font-bold text-white">{problem.title}</h1>
              <span className={`px-2.5 py-1 rounded-md border text-xs font-medium ${difficultyColors[problem.difficulty]}`}>
                {problem.difficulty}
              </span>
            </div>
            <div className="flex flex-wrap items-center gap-2 text-xs text-slate-400">
              <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700">{problem.language}</span>
              <span>{problem.skill_name}</span>
              <span>/</span>
              <span>{problem.subtopic}</span>
            </div>
            <p className="text-sm text-slate-300 leading-relaxed">{problem.description}</p>

            {problem.examples && problem.examples.length > 0 && (
              <div className="space-y-2">
                <h3 className="text-sm font-semibold text-slate-200">Examples</h3>
                {problem.examples.map((ex, i) => (
                  <div key={i} className="p-3 rounded-lg bg-slate-950/60 border border-slate-800 text-xs">
                    <div className="text-slate-400">Input: <span className="text-slate-200">{ex.input}</span></div>
                    <div className="text-slate-400">Output: <span className="text-emerald-400">{ex.output}</span></div>
                    {ex.explanation && <div className="text-slate-500 mt-1">{ex.explanation}</div>}
                  </div>
                ))}
              </div>
            )}

            {problem.constraints && (
              <div>
                <h3 className="text-sm font-semibold text-slate-200 mb-1">Constraints</h3>
                <p className="text-xs text-slate-400">{problem.constraints}</p>
              </div>
            )}

            {problem.visible_test_cases && problem.visible_test_cases.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-slate-200 mb-2">Sample Test Cases</h3>
                <div className="space-y-1.5">
                  {problem.visible_test_cases.map((tc, i) => (
                    <div key={i} className="p-2 rounded-lg bg-slate-950/60 border border-slate-800 text-xs">
                      <div className="text-slate-400">{tc.name}: Input <span className="text-slate-200">{tc.input}</span> → Expected <span className="text-emerald-400">{tc.expected_output}</span></div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Test Results / AI Review / History tabs */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <div className="flex gap-4 border-b border-slate-800 pb-2 mb-3">
              <button onClick={() => setActiveTab('tests')} className={`text-sm font-medium pb-1 ${activeTab === 'tests' ? 'text-indigo-400 border-b-2 border-indigo-500' : 'text-slate-400'}`}>
                Test Results
              </button>
              <button onClick={() => setActiveTab('review')} className={`text-sm font-medium pb-1 ${activeTab === 'review' ? 'text-indigo-400 border-b-2 border-indigo-500' : 'text-slate-400'}`}>
                AI Review
              </button>
              <button onClick={() => setActiveTab('history')} className={`text-sm font-medium pb-1 ${activeTab === 'history' ? 'text-indigo-400 border-b-2 border-indigo-500' : 'text-slate-400'}`}>
                History
              </button>
            </div>

            {activeTab === 'tests' && (
              <TestResultTable results={testResults} />
            )}

            {activeTab === 'review' && (
              <div className="space-y-3">
                {submitResult?.ai_review ? (
                  <>
                    {submitResult.ai_review.verdict && (
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-semibold text-slate-200">Verdict:</span>
                        <span className={`text-sm font-medium ${submitResult.ai_review.verdict === 'correct' ? 'text-emerald-400' : submitResult.ai_review.verdict === 'partially_correct' ? 'text-amber-400' : 'text-rose-400'}`}>
                          {submitResult.ai_review.verdict}
                        </span>
                      </div>
                    )}
                    {submitResult.ai_review.strengths?.length > 0 && (
                      <div>
                        <p className="text-sm font-semibold text-emerald-400 mb-1">Strengths</p>
                        <ul className="text-xs text-slate-300 list-disc list-inside space-y-1">
                          {submitResult.ai_review.strengths.map((s: string, i: number) => <li key={i}>{s}</li>)}
                        </ul>
                      </div>
                    )}
                    {submitResult.ai_review.issues?.length > 0 && (
                      <div>
                        <p className="text-sm font-semibold text-amber-400 mb-1">Issues</p>
                        <div className="space-y-2">
                          {submitResult.ai_review.issues.map((issue: any, i: number) => (
                            <div key={i} className="p-2 rounded-lg bg-slate-950/60 border border-slate-800 text-xs">
                              <div className="font-medium text-slate-200">{issue.title} <span className="text-slate-500">({issue.type})</span></div>
                              <div className="text-slate-400 mt-1">{issue.explanation}</div>
                              {issue.suggested_fix && <div className="text-indigo-400 mt-1">Fix: {issue.suggested_fix}</div>}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    {submitResult.ai_review.complexity && (
                      <div className="text-xs text-slate-400">
                        Time: {submitResult.ai_review.complexity.time} | Space: {submitResult.ai_review.complexity.space}
                      </div>
                    )}
                    {submitResult.ai_review.next_problem_recommendation && (
                      <div className="p-3 rounded-lg bg-indigo-950/40 border border-indigo-800/50 text-xs">
                        <Lightbulb className="w-4 h-4 text-indigo-400 inline mr-1" />
                        <span className="text-slate-200">{submitResult.ai_review.next_problem_recommendation.title}</span>
                        <p className="text-slate-400 mt-1">{submitResult.ai_review.next_problem_recommendation.reason}</p>
                      </div>
                    )}
                    {submitResult.mentor_alert && (
                      <div className="p-3 rounded-lg bg-rose-950/40 border border-rose-800/50 text-xs text-rose-300">
                        Your mentor has been notified about repeated difficulties with this topic.
                      </div>
                    )}
                    {submitResult.mastery_change !== null && submitResult.mastery_change !== undefined && (
                      <div className="text-xs text-slate-400">
                        Mastery {submitResult.mastery_change >= 0 ? '+' : ''}{submitResult.mastery_change.toFixed(1)} points
                      </div>
                    )}
                  </>
                ) : (
                  <p className="text-sm text-slate-500 text-center py-4">Submit your solution to get an AI code review.</p>
                )}
              </div>
            )}

            {activeTab === 'history' && (
              <div className="space-y-2">
                {history && history.length > 0 ? (
                  history.map((h, i) => (
                    <div key={i} className="flex items-center justify-between p-2 rounded-lg bg-slate-950/60 border border-slate-800 text-xs">
                      <span className={`font-medium ${h.status === 'passed' ? 'text-emerald-400' : h.status === 'failed' ? 'text-amber-400' : 'text-rose-400'}`}>
                        {h.status}
                      </span>
                      <span className="text-slate-400">{h.tests_passed}/{h.tests_total} tests</span>
                      <span className="text-slate-500">{new Date(h.submitted_at).toLocaleString()}</span>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-slate-500 text-center py-4">No submissions yet.</p>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Right: Code editor */}
        <div className="space-y-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-slate-200">Code Editor</span>
                <span className="text-xs text-slate-500">{problem.language}</span>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => runTestsMutation.mutate()}
                  disabled={isRunning || submitMutation.isPending}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium border border-slate-700 transition-colors disabled:opacity-50"
                >
                  <Play className="w-4 h-4" /> {isRunning ? 'Running...' : 'Run Tests'}
                </button>
                <button
                  onClick={() => submitMutation.mutate()}
                  disabled={submitMutation.isPending || isRunning}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium transition-colors disabled:opacity-50"
                >
                  <Send className="w-4 h-4" /> {submitMutation.isPending ? 'Submitting...' : 'Submit'}
                </button>
              </div>
            </div>
            <CodeEditor
              value={code}
              onChange={setCode}
              language={problem.language as 'javascript' | 'python'}
              height="400px"
            />
          </div>

          {submitResult && (
            <div className={`p-4 rounded-xl border ${submitResult.status === 'passed' ? 'bg-emerald-950/40 border-emerald-800/50' : 'bg-amber-950/40 border-amber-800/50'}`}>
              <div className="flex items-center justify-between">
                <span className={`text-sm font-semibold ${submitResult.status === 'passed' ? 'text-emerald-400' : 'text-amber-400'}`}>
                  {submitResult.status === 'passed' ? 'All tests passed!' : `${submitResult.tests_passed}/${submitResult.tests_total} tests passed`}
                </span>
                <span className="text-xs text-slate-400">Score: {submitResult.score}%</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
