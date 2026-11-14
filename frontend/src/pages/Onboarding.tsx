import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { saveOnboarding, addOrUpdateSkill } from '../api/profile';
import { 
  User, 
  Sparkles, 
  Plus, 
  Trash2, 
  ArrowRight, 
  CheckCircle2, 
  Briefcase, 
  Clock, 
  BookOpen, 
  GraduationCap,
  Layers
} from 'lucide-react';

const COMMON_SKILLS = [
  'Python', 'SQL', 'HTML', 'CSS', 'JavaScript', 
  'React', 'Node.js', 'Express', 'Git', 'Pandas'
];

export const Onboarding: React.FC = () => {
  const { profile, refreshProfile } = useAuth();
  const navigate = useNavigate();

  const [fullName, setFullName] = useState(profile?.full_name || '');
  const [educationLevel, setEducationLevel] = useState(profile?.education_level || "Bachelor's Degree");
  const [experienceLevel, setExperienceLevel] = useState(profile?.experience_level || 'Beginner');
  const [weeklyStudyHours, setWeeklyStudyHours] = useState(profile?.weekly_study_hours || 10);
  const [learningPreference, setLearningPreference] = useState(profile?.learning_preference || 'Hands-on projects');

  // Skills state
  const [skills, setSkills] = useState<{ skill_name: string; level: number }[]>([
    { skill_name: 'Python', level: 3 },
    { skill_name: 'SQL', level: 2 },
    { skill_name: 'HTML', level: 2 },
  ]);

  // Projects state
  const [projects, setProjects] = useState<{ title: string; description: string; tech_stack: string[]; github_url?: string }[]>([
    {
      title: 'Personal Portfolio Website',
      description: 'Static website built with semantic HTML and CSS Grid layout.',
      tech_stack: ['HTML', 'CSS'],
      github_url: 'https://github.com/learner/portfolio'
    }
  ]);

  // Certifications state
  const [certifications, setCertifications] = useState<{ name: string; issuer: string; issue_date?: string }[]>([
    {
      name: 'Python for Everybody Specialization',
      issuer: 'Coursera',
      issue_date: '2024-05'
    }
  ]);

  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    if (profile) {
      if (profile.full_name) setFullName(profile.full_name);
      if (profile.education_level) setEducationLevel(profile.education_level);
      if (profile.experience_level) setExperienceLevel(profile.experience_level);
      if (profile.weekly_study_hours) setWeeklyStudyHours(profile.weekly_study_hours);
      if (profile.learning_preference) setLearningPreference(profile.learning_preference);

      if (profile.learner_skills && profile.learner_skills.length > 0) {
        setSkills(profile.learner_skills.map((s) => ({ skill_name: s.skill_name, level: s.self_reported_level })));
      }
    }
  }, [profile]);

  const handleAddSkill = () => {
    setSkills([...skills, { skill_name: 'JavaScript', level: 1 }]);
  };

  const handleRemoveSkill = (index: number) => {
    setSkills(skills.filter((_, i) => i !== index));
  };

  const handleSkillChange = (index: number, field: 'skill_name' | 'level', value: any) => {
    const updated = [...skills];
    updated[index] = { ...updated[index], [field]: value };
    setSkills(updated);
  };

  const handleLoadDemoValues = () => {
    setFullName('Alex Mercer');
    setEducationLevel("Bachelor's Degree in Computer Science");
    setExperienceLevel('Junior Learner');
    setWeeklyStudyHours(12);
    setLearningPreference('Project-based interactive learning');
    setSkills([
      { skill_name: 'Python', level: 3 },
      { skill_name: 'SQL', level: 2 },
      { skill_name: 'HTML', level: 2 },
    ]);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setMessage(null);

    try {
      await saveOnboarding({
        full_name: fullName,
        education_level: educationLevel,
        experience_level: experienceLevel,
        weekly_study_hours: weeklyStudyHours,
        learning_preference: learningPreference,
        skills,
        projects,
        certifications,
      });

      await refreshProfile();
      setMessage('Profile saved successfully! Redirecting to Career Goal selection...');
      setTimeout(() => {
        navigate('/career-goal');
      }, 1000);
    } catch (err: any) {
      console.error(err);
      setMessage(err.response?.data?.detail || 'Failed to save profile. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-bold text-indigo-400 uppercase tracking-wider">Step 1 of 4</span>
            <span className="text-xs text-slate-500">•</span>
            <span className="text-xs text-slate-400">Baseline Assessment</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Learner Profile & Onboarding</h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Configure your educational background, weekly study budget, and existing self-reported competencies.
          </p>
        </div>

        <button
          type="button"
          onClick={handleLoadDemoValues}
          className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-indigo-950/80 border border-indigo-800/80 hover:bg-indigo-900/60 text-indigo-300 text-xs font-semibold transition-all whitespace-nowrap self-start sm:self-auto"
        >
          <Sparkles className="w-4 h-4 text-indigo-400" />
          <span>Load Acceptance Demo Profile</span>
        </button>
      </div>

      {message && (
        <div className="p-4 rounded-xl bg-indigo-950/40 border border-indigo-800/60 text-indigo-200 text-xs font-medium flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{message}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Basic Information */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-lg space-y-6">
          <div className="flex items-center gap-2 pb-3 border-b border-slate-800 text-sm font-bold text-slate-200">
            <User className="w-4 h-4 text-indigo-400" />
            <span>Personal & Study Parameters</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Full Name
              </label>
              <input
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-100 text-sm focus:outline-none focus:border-indigo-500"
                placeholder="e.g. Alex Mercer"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Weekly Study Time (Hours)
              </label>
              <div className="flex items-center gap-3">
                <input
                  type="number"
                  min="1"
                  max="60"
                  required
                  value={weeklyStudyHours}
                  onChange={(e) => setWeeklyStudyHours(Number(e.target.value))}
                  className="w-32 px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-100 text-sm focus:outline-none focus:border-indigo-500 font-semibold"
                />
                <span className="text-xs text-slate-400">Hours/week used to scale module phase pacing</span>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Education Level
              </label>
              <select
                value={educationLevel}
                onChange={(e) => setEducationLevel(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-100 text-sm focus:outline-none focus:border-indigo-500"
              >
                <option value="High School">High School</option>
                <option value="Self-Taught / Bootcamp">Self-Taught / Bootcamp</option>
                <option value="Associate Degree">Associate Degree</option>
                <option value="Bachelor's Degree">Bachelor's Degree</option>
                <option value="Master's Degree">Master's Degree</option>
                <option value="PhD">PhD</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Experience Level
              </label>
              <select
                value={experienceLevel}
                onChange={(e) => setExperienceLevel(e.target.value)}
                className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-100 text-sm focus:outline-none focus:border-indigo-500"
              >
                <option value="Complete Beginner">Complete Beginner</option>
                <option value="Junior Learner">Junior Learner (some coding experience)</option>
                <option value="Career Transitioner">Career Transitioner</option>
                <option value="Mid-Level">Mid-Level Developer</option>
              </select>
            </div>
          </div>
        </div>

        {/* Existing Skills Selection */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-lg space-y-6">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div className="flex items-center gap-2 text-sm font-bold text-slate-200">
              <Layers className="w-4 h-4 text-indigo-400" />
              <span>Prior Skills & Self-Reported Levels (0 to 5)</span>
            </div>

            <button
              type="button"
              onClick={handleAddSkill}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600/20 border border-indigo-500/30 hover:bg-indigo-600/30 text-indigo-400 text-xs font-semibold transition-all"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add Skill</span>
            </button>
          </div>

          <div className="space-y-3">
            {skills.map((s, idx) => (
              <div
                key={idx}
                className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-950/80 border border-slate-800/80 p-3.5 rounded-xl"
              >
                <div className="flex-1 flex items-center gap-3">
                  <select
                    value={s.skill_name}
                    onChange={(e) => handleSkillChange(idx, 'skill_name', e.target.value)}
                    className="bg-slate-900 border border-slate-700/80 rounded-lg px-3 py-2 text-xs font-semibold text-slate-100 focus:outline-none focus:border-indigo-500"
                  >
                    {COMMON_SKILLS.map((c) => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))}
                  </select>

                  <div className="flex items-center gap-2 flex-1 max-w-xs">
                    <span className="text-xs text-slate-400 whitespace-nowrap">Level:</span>
                    <input
                      type="range"
                      min="0"
                      max="5"
                      step="1"
                      value={s.level}
                      onChange={(e) => handleSkillChange(idx, 'level', Number(e.target.value))}
                      className="w-full accent-indigo-500 cursor-pointer"
                    />
                    <span className="text-xs font-bold text-indigo-300 w-10 text-right">
                      {s.level} / 5
                    </span>
                  </div>
                </div>

                <div className="flex items-center justify-end">
                  <button
                    type="button"
                    onClick={() => handleRemoveSkill(idx)}
                    className="p-1.5 text-slate-500 hover:text-rose-400 transition-colors"
                    title="Remove skill"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Action Button */}
        <div className="flex justify-end pt-4">
          <button
            type="submit"
            disabled={saving}
            className="flex items-center gap-2 px-8 py-3.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-sm transition-all shadow-xl shadow-indigo-600/30 disabled:opacity-50"
          >
            {saving ? 'Saving Profile...' : 'Save & Select Career Goal'}
            {!saving && <ArrowRight className="w-4 h-4" />}
          </button>
        </div>
      </form>
    </div>
  );
};

