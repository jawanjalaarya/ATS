import { useState, useEffect } from 'react';
import {
  CheckCircle,
  AlertTriangle,
  Target,
  Briefcase,
  GraduationCap,
  FolderGit2,
  Award,
  Brain,
  Loader2,
} from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { candidatesApi, type Candidate, type ScreeningResult } from '@/lib/api';

interface CandidateDetailProps {
  candidate: Candidate;
  jobId?: number;
  open: boolean;
  onClose: () => void;
}

const DIMENSION_CONFIG = [
  { key: 'skills_score' as const, label: 'Skills', icon: Target },
  { key: 'experience_score' as const, label: 'Experience', icon: Briefcase },
  { key: 'education_score' as const, label: 'Education', icon: GraduationCap },
  { key: 'projects_score' as const, label: 'Projects', icon: FolderGit2 },
  { key: 'certification_score' as const, label: 'Certifications', icon: Award },
  { key: 'semantic_score' as const, label: 'Semantic Match', icon: Brain },
] as const;

function ScoreBar({
  label,
  score,
  icon: Icon,
}: {
  label: string;
  score: number | null;
  icon: React.ElementType;
}) {
  if (score === null) return null;
  const pct = Math.round(score);
  const colorClass =
    pct >= 75
      ? 'text-emerald-600 dark:text-emerald-400'
      : pct >= 50
      ? 'text-amber-500 dark:text-amber-400'
      : 'text-rose-500 dark:text-rose-400';

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center justify-between text-sm">
        <span className="flex items-center gap-1.5 font-medium text-muted-foreground">
          <Icon className="h-3.5 w-3.5" aria-hidden="true" />
          {label}
        </span>
        <span className={`font-semibold tabular-nums ${colorClass}`}>{pct}%</span>
      </div>
      <Progress value={pct} className="h-2" />
    </div>
  );
}

function RequirementItem({ label, matched }: { label: string; matched: boolean }) {
  return (
    <div className="flex items-center gap-2 text-sm py-0.5">
      {matched ? (
        <>
          <CheckCircle
            className="h-4 w-4 text-emerald-500 shrink-0"
            aria-hidden="true"
          />
          <span className="text-emerald-700 dark:text-emerald-400">
            <span className="sr-only">Matched: </span>
            {label}
          </span>
        </>
      ) : (
        <>
          <AlertTriangle
            className="h-4 w-4 text-amber-500 shrink-0"
            aria-hidden="true"
          />
          <span className="text-amber-700 dark:text-amber-400">
            <span className="sr-only">Missing: </span>
            {label}
          </span>
        </>
      )}
    </div>
  );
}

export function CandidateDetail({
  candidate,
  jobId,
  open,
  onClose,
}: CandidateDetailProps) {
  const [screening, setScreening] = useState<ScreeningResult | null>(null);
  const [loadingScreening, setLoadingScreening] = useState(false);

  useEffect(() => {
    if (!open || !jobId) {
      setScreening(null);
      return;
    }
    setLoadingScreening(true);
    candidatesApi
      .getScreeningResult(candidate.id, jobId)
      .then(setScreening)
      .catch(() => setScreening(null))
      .finally(() => setLoadingScreening(false));
  }, [open, candidate.id, jobId]);

  const explanation = screening?.explanation;
  const skillsBreakdown = explanation?.skills;
  const expBreakdown = explanation?.experience;
  const eduBreakdown = explanation?.education;
  const certBreakdown = explanation?.certifications;

  const allRequired = [
    ...(skillsBreakdown?.required_matched?.map((s) => ({ label: s, matched: true })) ?? []),
    ...(skillsBreakdown?.required_missing?.map((s) => ({ label: s, matched: false })) ?? []),
  ];

  const allPreferred = [
    ...(skillsBreakdown?.preferred_matched?.map((s) => ({ label: s, matched: true })) ?? []),
    ...(skillsBreakdown?.preferred_missing?.map((s) => ({ label: s, matched: false })) ?? []),
  ];

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-xl">
            {candidate.name ?? 'Unknown Candidate'}
          </DialogTitle>
          <DialogDescription asChild>
            <div className="flex flex-wrap gap-x-3 gap-y-1 mt-1 text-sm text-muted-foreground">
              {candidate.email && <span>{candidate.email}</span>}
              {candidate.phone && <span>· {candidate.phone}</span>}
              {candidate.location && <span>· {candidate.location}</span>}
            </div>
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-5 mt-2">
          {/* Screening Score Section */}
          {jobId && (
            <section
              aria-label="Match scores"
              className="border rounded-lg p-4 bg-muted/30"
            >
              <h3 className="font-semibold text-sm mb-3 flex items-center gap-2">
                <Target className="h-4 w-4" aria-hidden="true" />
                Match Score
                {screening && (
                  <Badge variant="secondary" className="ml-auto text-sm font-bold px-2">
                    {Math.round(screening.overall_score ?? 0)}% overall
                  </Badge>
                )}
              </h3>

              {loadingScreening && (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                  Loading scores…
                </div>
              )}

              {!loadingScreening && screening && (
                <div className="space-y-3">
                  {DIMENSION_CONFIG.map(({ key, label, icon }) => (
                    <ScoreBar
                      key={key}
                      label={label}
                      score={screening[key]}
                      icon={icon}
                    />
                  ))}
                </div>
              )}

              {!loadingScreening && !screening && (
                <p className="text-sm text-muted-foreground">
                  No screening result available. Upload the resume with a job selected to
                  auto-screen, or trigger screening manually.
                </p>
              )}
            </section>
          )}

          {/* Required Skills Breakdown */}
          {allRequired.length > 0 && (
            <section aria-label="Required skills breakdown">
              <h3 className="font-semibold text-sm mb-2">Required Skills</h3>
              <div className="space-y-0.5">
                {allRequired.map((item) => (
                  <RequirementItem
                    key={item.label}
                    label={item.label}
                    matched={item.matched}
                  />
                ))}
              </div>
            </section>
          )}

          {/* Preferred Skills Breakdown */}
          {allPreferred.length > 0 && (
            <section aria-label="Preferred skills breakdown">
              <h3 className="font-semibold text-sm mb-2 text-muted-foreground">
                Preferred Enhancements
              </h3>
              <div className="space-y-0.5">
                {allPreferred.map((item) => (
                  <RequirementItem
                    key={item.label}
                    label={item.label}
                    matched={item.matched}
                  />
                ))}
              </div>
            </section>
          )}

          {/* Certifications Breakdown */}
          {certBreakdown && !certBreakdown.omitted && (
            <section aria-label="Certifications breakdown">
              <h3 className="font-semibold text-sm mb-2">Certifications</h3>
              <div className="space-y-0.5">
                {(certBreakdown.required_matched ?? []).map((c) => (
                  <RequirementItem key={c} label={c} matched={true} />
                ))}
                {(certBreakdown.required_missing ?? []).map((c) => (
                  <RequirementItem key={c} label={c} matched={false} />
                ))}
              </div>
            </section>
          )}

          {/* Experience Details */}
          {expBreakdown && (
            <section aria-label="Experience summary">
              <h3 className="font-semibold text-sm mb-2">Experience</h3>
              <p className="text-sm text-muted-foreground">
                Candidate: <strong>{expBreakdown.candidate_years ?? '?'} yrs</strong>
                {' · '}
                Required: <strong>{expBreakdown.required_min ?? 0}+ yrs</strong>
                {' · '}
                {expBreakdown.meets_minimum ? (
                  <span className="text-emerald-600 dark:text-emerald-400 font-medium">
                    ✓ Meets requirement
                  </span>
                ) : (
                  <span className="text-amber-600 dark:text-amber-400 font-medium">
                    ⚠ Below requirement
                  </span>
                )}
              </p>
            </section>
          )}

          {/* Education Details */}
          {eduBreakdown && (
            <section aria-label="Education summary">
              <h3 className="font-semibold text-sm mb-2">Education</h3>
              <p className="text-sm text-muted-foreground">
                Candidate: <strong>{eduBreakdown.candidate_level ?? '?'}</strong>
                {' · '}
                Required: <strong>{eduBreakdown.required_level ?? '?'}</strong>
                {' · '}
                {eduBreakdown.meets_requirement ? (
                  <span className="text-emerald-600 dark:text-emerald-400 font-medium">
                    ✓ Meets requirement
                  </span>
                ) : (
                  <span className="text-amber-600 dark:text-amber-400 font-medium">
                    ⚠ Below requirement
                  </span>
                )}
              </p>
            </section>
          )}

          {/* Candidate Skills (always shown) */}
          <section aria-label="Candidate skills">
            <h3 className="font-semibold text-sm mb-2">Skills</h3>
            <div className="flex flex-wrap gap-1.5">
              {(candidate.skills ?? []).length > 0 ? (
                candidate.skills.map((skill) => (
                  <Badge key={skill} variant="outline" className="text-xs">
                    {skill}
                  </Badge>
                ))
              ) : (
                <span className="text-sm text-muted-foreground">No skills parsed</span>
              )}
            </div>
          </section>

          {/* Links */}
          {(candidate.linkedin_url || candidate.github_url || candidate.portfolio_url) && (
            <section aria-label="Candidate links">
              <h3 className="font-semibold text-sm mb-2">Links</h3>
              <div className="flex flex-wrap gap-2">
                {candidate.linkedin_url && (
                  <a
                    href={candidate.linkedin_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
                  >
                    LinkedIn ↗
                  </a>
                )}
                {candidate.github_url && (
                  <a
                    href={candidate.github_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
                  >
                    GitHub ↗
                  </a>
                )}
                {candidate.portfolio_url && (
                  <a
                    href={candidate.portfolio_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
                  >
                    Portfolio ↗
                  </a>
                )}
              </div>
            </section>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
