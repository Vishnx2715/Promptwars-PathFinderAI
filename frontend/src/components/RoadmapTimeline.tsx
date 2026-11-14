import React from 'react';
import { 
  RoadmapModule, 
  RoadmapResource 
} from '../types';
import { 
  Lock, 
  Unlock, 
  CheckCircle2, 
  Clock, 
  AlertCircle, 
  ExternalLink, 
  CheckSquare, 
  Square,
  BookOpen,
  Code2,
  Video,
  FileText
} from 'lucide-react';
import { ExplanationCard } from './ExplanationCard';

interface RoadmapTimelineProps {
  modules: RoadmapModule[];
  onToggleResource: (resourceId: number, isCompleted: boolean) => void;
  onUpdateStatus: (moduleId: number, status: string) => void;
}

export const RoadmapTimeline: React.FC<RoadmapTimelineProps> = ({
  modules,
  onToggleResource,
  onUpdateStatus,
}) => {
  // Group modules by Phase
  const phases = React.useMemo(() => {
    const map = new Map<number, RoadmapModule[]>();
    modules.forEach((mod) => {
      const list = map.get(mod.phase) || [];
      list.push(mod);
      map.set(mod.phase, list);
    });
    return Array.from(map.entries()).sort(([a], [b]) => a - b);
  }, [modules]);

  const getStatusBadge = (status: RoadmapModule['status']) => {
    switch (status) {
      case 'completed':
        return (
          <span className="flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-950/80 border border-emerald-800 text-emerald-400">
            <CheckCircle2 className="w-3.5 h-3.5" /> Completed
          </span>
        );
      case 'needs_revision':
        return (
          <span className="flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-full bg-rose-950/80 border border-rose-800 text-rose-400 animate-pulse">
            <AlertCircle className="w-3.5 h-3.5" /> Needs Revision
          </span>
        );
      case 'in_progress':
        return (
          <span className="flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-full bg-cyan-950/80 border border-cyan-800 text-cyan-400">
            <Clock className="w-3.5 h-3.5" /> In Progress
          </span>
        );
      case 'available':
        return (
          <span className="flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-full bg-indigo-950/80 border border-indigo-800 text-indigo-400">
            <Unlock className="w-3.5 h-3.5" /> Available
          </span>
        );
      case 'locked':
      default:
        return (
          <span className="flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-800 border border-slate-700 text-slate-400">
            <Lock className="w-3.5 h-3.5" /> Locked
          </span>
        );
    }
  };

  const getResourceIcon = (type: RoadmapResource['resource_type']) => {
    switch (type) {
      case 'exercise':
      case 'project':
        return <Code2 className="w-4 h-4 text-cyan-400" />;
      case 'video':
        return <Video className="w-4 h-4 text-amber-400" />;
      case 'documentation':
      case 'course':
      default:
        return <FileText className="w-4 h-4 text-indigo-400" />;
    }
  };

  return (
    <div className="space-y-10">
      {phases.map(([phaseNum, phaseModules]) => {
        const totalPhaseResources = phaseModules.reduce((acc, m) => acc + m.resources.length, 0);
        const completedPhaseResources = phaseModules.reduce(
          (acc, m) => acc + m.resources.filter((r) => r.is_completed).length,
          0
        );
        const phaseProgress = totalPhaseResources > 0 ? Math.round((completedPhaseResources / totalPhaseResources) * 100) : 0;

        return (
          <div key={phaseNum} className="relative pl-6 sm:pl-8 border-l-2 border-indigo-900/50 space-y-6">
            {/* Phase Node Marker */}
            <div className="absolute -left-[17px] top-0 w-8 h-8 rounded-full bg-slate-900 border-2 border-indigo-500 flex items-center justify-center font-bold text-xs text-indigo-400 shadow-md">
              P{phaseNum}
            </div>

            {/* Phase Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-slate-800/80">
              <div>
                <h3 className="text-lg font-bold text-slate-100">
                  Phase {phaseNum}: {phaseModules[0]?.title.split(' ')[1] || 'Core Modules'}
                </h3>
                <p className="text-xs text-slate-400">
                  {phaseModules.length} Modules • {completedPhaseResources} of {totalPhaseResources} Resources Complete ({phaseProgress}%)
                </p>
              </div>

              {/* Progress bar */}
              <div className="w-full sm:w-48 h-2 bg-slate-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-indigo-500 to-emerald-500 rounded-full transition-all duration-500"
                  style={{ width: `${phaseProgress}%` }}
                />
              </div>
            </div>

            {/* Modules in Phase */}
            <div className="grid grid-cols-1 gap-6">
              {phaseModules.map((module) => {
                const totalRes = module.resources.length;
                const completedRes = module.resources.filter((r) => r.is_completed).length;
                const allResourcesCompleted = totalRes > 0 && completedRes === totalRes;
                const isLocked = module.status === 'locked';
                const isNeedsRevision = module.status === 'needs_revision';

                return (
                  <div
                    key={module.id}
                    className={`bg-slate-900 border rounded-2xl p-5 lg:p-6 transition-all ${
                      isNeedsRevision
                        ? 'border-rose-900/60 bg-rose-950/10'
                        : isLocked
                        ? 'border-slate-800/60 opacity-80'
                        : 'border-slate-800 hover:border-slate-700 shadow-lg'
                    }`}
                  >
                    {/* Header */}
                    <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs font-semibold text-indigo-400 uppercase tracking-wider">
                            {module.skill_name}
                          </span>
                          <span className="text-xs text-slate-500">•</span>
                          <span className="text-xs text-slate-400">
                            Est. {module.estimated_hours}h
                          </span>
                        </div>
                        <h4 className="text-base font-bold text-white">{module.title}</h4>
                        <p className="text-xs text-slate-400 mt-1 max-w-2xl">{module.description}</p>
                      </div>

                      <div className="shrink-0">{getStatusBadge(module.status)}</div>
                    </div>

                    {/* Explanation if locked or needs revision */}
                    {module.reason && (isLocked || isNeedsRevision) && (
                      <div className="mt-4">
                        <ExplanationCard
                          type={isNeedsRevision ? 'revision' : 'lock'}
                          title={isNeedsRevision ? 'Adaptive Revision Sprint Activated' : 'Prerequisite Constraint'}
                          reason={module.reason}
                          prerequisiteModuleTitle={module.prerequisite_module_title}
                        />
                      </div>
                    )}

                    {/* Curated Resources Checklist */}
                    {module.resources && module.resources.length > 0 && (
                      <div className="mt-5 pt-4 border-t border-slate-800/70">
                        <div className="flex items-center justify-between mb-3">
                          <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                            <BookOpen className="w-3.5 h-3.5 text-indigo-400" />
                            Curated Resources ({completedRes}/{totalRes})
                          </span>
                          <span className="text-[11px] text-slate-400">
                            {allResourcesCompleted ? 'All items checked' : 'Complete all to finish module'}
                          </span>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                          {module.resources.map((res) => (
                            <div
                              key={res.id}
                              className={`flex items-start justify-between p-2.5 rounded-xl border text-xs transition-colors ${
                                res.is_completed
                                  ? 'bg-emerald-950/15 border-emerald-900/40 text-slate-300'
                                  : 'bg-slate-950/60 border-slate-800/80 text-slate-300 hover:border-slate-700'
                              }`}
                            >
                              <div className="flex items-start gap-2.5 flex-1 min-w-0 pr-2">
                                <button
                                  type="button"
                                  onClick={() => onToggleResource(res.id, !res.is_completed)}
                                  className="mt-0.5 text-slate-400 hover:text-indigo-400 transition-colors shrink-0"
                                  title={res.is_completed ? 'Mark incomplete' : 'Mark completed'}
                                >
                                  {res.is_completed ? (
                                    <CheckSquare className="w-4 h-4 text-emerald-400" />
                                  ) : (
                                    <Square className="w-4 h-4 text-slate-500" />
                                  )}
                                </button>
                                <div className="min-w-0">
                                  <a
                                    href={res.url}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="font-medium text-slate-200 hover:text-indigo-400 flex items-center gap-1 truncate"
                                  >
                                    <span className="truncate">{res.title}</span>
                                    <ExternalLink className="w-3 h-3 shrink-0" />
                                  </a>
                                  <p className="text-[11px] text-slate-500 truncate mt-0.5">
                                    {res.estimated_minutes}m • {res.difficulty} • {res.reason}
                                  </p>
                                </div>
                              </div>
                              <span className="shrink-0 mt-0.5">{getResourceIcon(res.resource_type)}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Actions and Status Updater */}
                    <div className="mt-5 pt-4 border-t border-slate-800/70 flex flex-wrap items-center justify-between gap-3">
                      <div className="text-xs text-slate-400">
                        Required for Unlock: <strong className="text-slate-300">&gt;={module.min_mastery_to_unlock}%</strong> prerequisite mastery
                      </div>

                      <div className="flex items-center gap-2">
                        {module.status !== 'completed' && !isLocked && (
                          <button
                            type="button"
                            disabled={!allResourcesCompleted}
                            onClick={() => onUpdateStatus(module.id, 'completed')}
                            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
                              allResourcesCompleted
                                ? 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-md shadow-emerald-900/30'
                                : 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700/50'
                            }`}
                            title={!allResourcesCompleted ? 'Complete all curated resources first' : 'Mark module complete'}
                          >
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span>Mark Completed</span>
                          </button>
                        )}

                        {module.status === 'available' && (
                          <button
                            type="button"
                            onClick={() => onUpdateStatus(module.id, 'in_progress')}
                            className="px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700"
                          >
                            Start Module
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
};

