import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate, useParams } from 'react-router-dom';
import { 
  startAssessment, 
  submitAssessment, 
  getAssessmentResult,
  getAssessmentForSkill
} from '../api/assessment';
import { 
  AssessmentStartResponse, 
  AssessmentResult 
} from '../types';
import { 
  Award, 
  CheckCircle2, 
  XCircle, 
  ArrowRight, 
  ArrowLeft, 
  RotateCcw, 
  Map, 
  Sparkles, 
  AlertTriangle,
  HelpCircle,
  Clock,
  ShieldCheck,
  Brain
} from 'lucide-react';
import { ExplanationCard } from '../components/ExplanationCard';
import { NextActionCard } from '../components/NextActionCard';

export const Assessment: React.FC = () => {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { assessmentId: urlAssessmentId } = useParams<{ assessmentId?: string }>();

  // State
  const [selectedAssessmentId, setSelectedAssessmentId] = useState<number>(
    urlAssessmentId ? Number(urlAssessmentId) : 1
  );
  const [activeTest, setActiveTest] = useState<AssessmentStartResponse | null>(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState<number>(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [result, setResult] = useState<AssessmentResult | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Auto-start assessment if ID is provided in URL
  useEffect(() => {
    if (urlAssessmentId && !activeTest && !result) {
      startMutation.mutate(Number(urlAssessmentId));
    }
  }, [urlAssessmentId]);

  // Start Assessment Mutation
  const startMutation = useMutation({
    mutationFn: (assessmentId: number) => startAssessment(assessmentId),
    onSuccess: (data) => {
      setActiveTest(data);
      setCurrentQuestionIndex(0);
      setAnswers({});
      setResult(null);
    },
  });

  // Submit Assessment Mutation
  const submitMutation = useMutation({
    mutationFn: async () => {
      if (!activeTest) return;
      const formattedAnswers = Object.entries(answers).map(([qId, opt]) => ({
        question_id: Number(qId),
        selected_option: opt,
      }));
      return await submitAssessment(activeTest.attempt_id, formattedAnswers);
    },
    onSuccess: (resData) => {
      if (resData) {
        setResult(resData);
        setActiveTest(null);
        // Refresh all roadmap and gap analysis queries to show adaptive changes
        queryClient.invalidateQueries({ queryKey: ['activeRoadmap'] });
        queryClient.invalidateQueries({ queryKey: ['gapAnalysis'] });
      }
    },
  });

  const handleSelectOption = (questionId: number, optionKey: string) => {
    setAnswers((prev) => ({
      ...prev,
      [questionId]: optionKey,
    }));
  };

  // Test helpers to instantly demonstrate Acceptance Criteria #8 (<50%) and #9 (>=85%)
  const handleAutoFillLowScore = () => {
    if (!activeTest) return;
    const lowAnswers: Record<number, string> = {};
    // Deliberately choose wrong answers
    activeTest.questions.forEach((q, i) => {
      // Pick D for all to get <50% score
      lowAnswers[q.id] = i === 0 ? 'B' : 'D'; 
    });
    setAnswers(lowAnswers);
  };

  const handleAutoFillHighScore = () => {
    if (!activeTest) return;
    // Known correct options from seed data:
    // JS: Q1=B, Q2=B, Q3=C, Q4=B, Q5=A, Q6=C, Q7=B, Q8=B
    const correctMap: Record<number, string> = {
      1: 'B', 2: 'B', 3: 'C', 4: 'B', 5: 'A', 6: 'C', 7: 'B', 8: 'B',
      9: 'C', 10: 'A', 11: 'B', 12: 'B', 13: 'C', 14: 'B', 15: 'A', 16: 'B'
    };
    const highAnswers: Record<number, string> = {};
    activeTest.questions.forEach((q) => {
      highAnswers[q.id] = correctMap[q.id] || 'B';
    });
    setAnswers(highAnswers);
  };

  // 1. ASSESSMENT SELECTOR VIEW
  if (!activeTest && !result) {
    return (
      <div className="max-w-4xl mx-auto space-y-8 pb-12">
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-bold text-indigo-400 uppercase tracking-wider">Step 4 of 4</span>
            <span className="text-xs text-slate-500">•</span>
            <span className="text-xs text-slate-400">Diagnostic Verification</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Diagnostic Skill Assessments</h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1 max-w-2xl">
            Take an evidence-based diagnostic test to verify your skills. Your performance dynamically adapts your roadmap: scoring &lt;50% initiates a Revision Sprint; scoring &gt;=85% completes the module and unlocks dependent skills.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* JavaScript Diagnostic */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-lg flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="w-10 h-10 rounded-xl bg-amber-500/20 text-amber-400 flex items-center justify-center font-bold">
                  JS
                </div>
                <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                  8 Questions • Diagnostic
                </span>
              </div>
              <h3 className="text-lg font-bold text-white mb-1">JavaScript Core Diagnostic</h3>
              <p className="text-xs text-slate-400 leading-relaxed mb-4">
                Tests variables, closures, event loop microtasks, async/await, equality coercion, array methods, prototype chain, and lexical scope.
              </p>
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 text-[11px] text-slate-400 mb-4">
                <strong>Prerequisite Key:</strong> Passing with &gt;= 70% unblocks <strong>React</strong> and <strong>Node.js</strong> on Full Stack roadmap.
              </div>
            </div>

            <button
              onClick={() => startMutation.mutate(1)}
              disabled={startMutation.isPending}
              className="w-full py-2.5 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs transition-all shadow-lg shadow-indigo-600/25 flex items-center justify-center gap-2"
            >
              {startMutation.isPending ? 'Preparing Test...' : 'Start JavaScript Diagnostic'}
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Python Diagnostic */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-lg flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4">
                <div className="w-10 h-10 rounded-xl bg-cyan-500/20 text-cyan-400 flex items-center justify-center font-bold">
                  PY
                </div>
                <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                  8 Questions • Diagnostic
                </span>
              </div>
              <h3 className="text-lg font-bold text-white mb-1">Python Core Diagnostic</h3>
              <p className="text-xs text-slate-400 leading-relaxed mb-4">
                Tests mutability, list comprehensions, default parameter evaluation, generators, context managers, decorators, GIL, and exception flow.
              </p>
              <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 text-[11px] text-slate-400 mb-4">
                <strong>Prerequisite Key:</strong> Passing unblocks <strong>Pandas</strong> and Data Analyst / Machine Learning tracks.
              </div>
            </div>

            <button
              onClick={() => startMutation.mutate(2)}
              disabled={startMutation.isPending}
              className="w-full py-2.5 px-4 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-bold text-xs transition-all flex items-center justify-center gap-2"
            >
              {startMutation.isPending ? 'Preparing Test...' : 'Start Python Diagnostic'}
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    );
  }

  // 2. ACTIVE QUESTION RUNNER VIEW
  if (activeTest && !result) {
    const totalQuestions = activeTest.questions.length;
    const currentQ = activeTest.questions[currentQuestionIndex];
    const selectedOpt = answers[currentQ.id];
    const answeredCount = Object.keys(answers).length;
    const progressPercent = Math.round(((currentQuestionIndex + 1) / totalQuestions) * 100);

    return (
      <div className="max-w-3xl mx-auto space-y-6 pb-12">
        {/* Test Bar Header */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl flex items-center justify-between">
          <div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-400 block">
              {activeTest.title}
            </span>
            <h2 className="text-base font-bold text-white">
              Question {currentQuestionIndex + 1} of {totalQuestions}
            </h2>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 font-medium">
              Answered: <strong className="text-indigo-300">{answeredCount}/{totalQuestions}</strong>
            </span>
          </div>
        </div>

        {/* Question Progress bar */}
        <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-indigo-500 to-cyan-400 rounded-full transition-all duration-300"
            style={{ width: `${progressPercent}%` }}
          />
        </div>

        {/* Demo Fast Fill Bar for Quick Acceptance Verification */}
        <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between gap-2 text-xs">
          <span className="text-slate-400 font-medium flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            Hackathon Demo Controls:
          </span>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleAutoFillLowScore}
              className="px-2.5 py-1 rounded-md bg-rose-950/80 border border-rose-800/80 text-rose-300 text-[11px] font-semibold hover:bg-rose-900/60 transition-colors"
              title="Simulate low score to test Revision Sprint & Locked modules"
            >
              Fill &lt;50% (Test Revision Sprint)
            </button>
            <button
              type="button"
              onClick={handleAutoFillHighScore}
              className="px-2.5 py-1 rounded-md bg-emerald-950/80 border border-emerald-800/80 text-emerald-300 text-[11px] font-semibold hover:bg-emerald-900/60 transition-colors"
              title="Simulate high score to test React & Node.js Unlocking"
            >
              Fill &gt;=85% (Test Unlocking)
            </button>
          </div>
        </div>

        {/* Current Question Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-xl space-y-6">
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-semibold text-slate-400 bg-slate-800 px-2.5 py-0.5 rounded-full">
              {currentQ.subtopic}
            </span>
            <span className="text-[11px] font-semibold text-indigo-300 bg-indigo-950/60 border border-indigo-800/60 px-2.5 py-0.5 rounded-full capitalize">
              {currentQ.difficulty}
            </span>
            <span className="text-[11px] text-slate-500 ml-auto">
              {currentQ.marks} mark{currentQ.marks > 1 ? 's' : ''}
            </span>
          </div>

          <h3 className="text-base sm:text-lg font-medium text-slate-100 whitespace-pre-wrap leading-relaxed">
            {currentQ.question_text}
          </h3>

          {/* Options */}
          <div className="space-y-3 pt-2">
            {Object.entries(currentQ.options).map(([optKey, optText]) => {
              const isSelected = selectedOpt === optKey;
              return (
                <button
                  key={optKey}
                  type="button"
                  onClick={() => handleSelectOption(currentQ.id, optKey)}
                  className={`w-full text-left p-4 rounded-xl border transition-all flex items-start gap-3 ${
                    isSelected
                      ? 'bg-indigo-950/40 border-indigo-500 text-white shadow-md shadow-indigo-950/40 ring-1 ring-indigo-500'
                      : 'bg-slate-950/60 border-slate-800 text-slate-300 hover:border-slate-700 hover:bg-slate-950'
                  }`}
                >
                  <span
                    className={`w-6 h-6 rounded-lg font-bold text-xs flex items-center justify-center shrink-0 mt-0.5 ${
                      isSelected
                        ? 'bg-indigo-600 text-white'
                        : 'bg-slate-800 text-slate-400'
                    }`}
                  >
                    {optKey}
                  </span>
                  <span className="text-xs sm:text-sm font-normal leading-relaxed">{optText}</span>
                </button>
              );
            })}
          </div>

          {/* Bottom Question Navigation Controls */}
          <div className="flex items-center justify-between pt-6 border-t border-slate-800/80">
            <button
              type="button"
              disabled={currentQuestionIndex === 0}
              onClick={() => setCurrentQuestionIndex((prev) => prev - 1)}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Previous</span>
            </button>

            {currentQuestionIndex < totalQuestions - 1 ? (
              <button
                type="button"
                onClick={() => setCurrentQuestionIndex((prev) => prev + 1)}
                className="flex items-center gap-1.5 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-all shadow-md"
              >
                <span>Next Question</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            ) : (
              <button
                type="button"
                disabled={submitMutation.isPending}
                onClick={() => submitMutation.mutate()}
                className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold transition-all shadow-lg shadow-emerald-900/30"
              >
                <span>{submitMutation.isPending ? 'Grading & Replanning...' : 'Submit Assessment'}</span>
                <CheckCircle2 className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  // 3. RESULT VIEW
  if (result) {
    const isPassing = result.mastery_percentage >= 70;
    const isHigh = result.mastery_percentage >= 85;
    const isCritical = result.mastery_percentage < 50;

    return (
      <div className="max-w-4xl mx-auto space-y-8 pb-12">
        {/* Result Header Card */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-xl text-center space-y-4">
          <div
            className={`w-16 h-16 rounded-full mx-auto flex items-center justify-center shadow-lg ${
              isHigh
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                : isCritical
                ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                : 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30'
            }`}
          >
            <Award className="w-8 h-8" />
          </div>

          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Assessment Completed: {result.assessment_title}
            </span>
            <h2 className="text-3xl font-extrabold text-white tracking-tight mt-1">
              {result.mastery_percentage.toFixed(0)}% Verified Mastery
            </h2>
            <p className="text-xs sm:text-sm text-slate-400 mt-1 max-w-lg mx-auto">
              Score: <strong className="text-slate-200">{result.score}</strong> / {result.max_score} marks.
            </p>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
            <button
              onClick={() => navigate('/roadmap')}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition-all shadow-lg"
            >
              <Map className="w-4 h-4" />
              <span>Inspect Roadmap Changes</span>
            </button>
            <button
              onClick={() => {
                setResult(null);
                setActiveTest(null);
              }}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition-all border border-slate-700"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Take Another Test</span>
            </button>
          </div>
        </div>

        {/* AI Mentor & Next Action Card */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-lg flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-indigo-400 mb-2">
                <Brain className="w-4 h-4" />
                <span>AI Progress Coach Message</span>
              </div>
              <p className="text-xs sm:text-sm text-slate-200 leading-relaxed italic">
                "{result.mentor_message || 'Great effort on completing your diagnostic.'}"
              </p>
            </div>
          </div>

          <NextActionCard
            actionText={result.next_best_action}
            targetPath="/roadmap"
            buttonLabel="Go to Roadmap"
          />
        </div>

        {/* Adaptive Roadmap Adaptations Applied */}
        {result.roadmap_changes && result.roadmap_changes.length > 0 && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-lg space-y-3">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-indigo-400" />
              <span>Automated Adaptive Replanning Log ({result.roadmap_changes.length})</span>
            </h3>
            <div className="space-y-2">
              {result.roadmap_changes.map((ch, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 text-xs flex items-center justify-between"
                >
                  <div>
                    <span className="font-semibold text-slate-200 block">{ch.module_title}</span>
                    <span className="text-[11px] text-slate-400">{ch.reason}</span>
                  </div>
                  <span
                    className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-md ${
                      ch.action === 'unlock' || ch.action === 'complete'
                        ? 'bg-emerald-950/80 text-emerald-400 border border-emerald-800'
                        : 'bg-rose-950/80 text-rose-400 border border-rose-800'
                    }`}
                  >
                    {ch.action}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Weak Subtopics */}
        {result.weak_topics && result.weak_topics.length > 0 && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-lg space-y-3">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              <span>Subtopics Requiring Strengthening</span>
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {result.weak_topics.map((w, idx) => (
                <div key={idx} className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800 text-xs">
                  <div className="flex items-center justify-between font-bold text-slate-200">
                    <span>{w.subtopic}</span>
                    <span className="text-amber-400">{w.incorrect_count} missed</span>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-1">{w.recommendation}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Detailed Question-by-Question Breakdown */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-lg space-y-4">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">
            Detailed Diagnostic Review ({result.breakdown.length} Questions)
          </h3>

          <div className="space-y-3">
            {result.breakdown.map((item, idx) => (
              <div
                key={idx}
                className={`p-4 rounded-xl border text-xs space-y-2 ${
                  item.is_correct
                    ? 'bg-emerald-950/10 border-emerald-900/40 text-slate-300'
                    : 'bg-rose-950/10 border-rose-900/40 text-slate-300'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-200">
                    Q{idx + 1}: {item.subtopic}
                  </span>
                  <span
                    className={`flex items-center gap-1 font-bold ${
                      item.is_correct ? 'text-emerald-400' : 'text-rose-400'
                    }`}
                  >
                    {item.is_correct ? (
                      <>
                        <CheckCircle2 className="w-3.5 h-3.5" /> Correct
                      </>
                    ) : (
                      <>
                        <XCircle className="w-3.5 h-3.5" /> Incorrect
                      </>
                    )}
                  </span>
                </div>

                <p className="text-slate-300 whitespace-pre-wrap">{item.question_text}</p>

                <div className="flex flex-wrap gap-4 text-[11px] pt-1">
                  <span>
                    Your Answer: <strong className="text-slate-100">{item.selected_option}</strong>
                  </span>
                  <span>
                    Correct Answer: <strong className="text-emerald-400">{item.correct_option}</strong>
                  </span>
                </div>

                <div className="p-2.5 rounded-lg bg-slate-950/80 border border-slate-800 text-[11px] text-slate-400 leading-relaxed">
                  <strong className="text-slate-300">Explanation:</strong> {item.explanation}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return null;
};

