import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Edit, LoaderCircle, Clock, Users, MapPin, Briefcase } from 'lucide-react';
import { toast } from 'sonner';
import { jobsApi, type Job } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { ResumeUpload } from '@/components/candidates/ResumeUpload';

export function JobDetailsPage() {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const [job, setJob] = useState<Job | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [jobToClose, setJobToClose] = useState<Job | null>(null);
  const [jobToArchive, setJobToArchive] = useState<Job | null>(null);
  const [isClosingJob, setIsClosingJob] = useState(false);
  const [isArchivingJob, setIsArchivingJob] = useState(false);

  useEffect(() => {
    if (id) {
      const fetchJob = async () => {
        setIsLoading(true);
        setError(null);
        try {
          const jobData = await jobsApi.getJob(parseInt(id, 10));
          setJob(jobData);
        } catch (err: any) {
          if (err.response?.status === 404) {
            setError('Job not found');
          } else if (err.response?.status === 401 || err.response?.status === 403) {
            setError('You do not have permission to view this job');
          } else {
            setError('Unable to load job. Please check your connection and try again.');
          }
        } finally {
          setIsLoading(false);
        }
      };

      void fetchJob();
    }
  }, [id]);

  const onCloseJob = async () => {
    if (!jobToClose) return;
    setActionError(null);
    setIsClosingJob(true);
    try {
      const updatedJob = await jobsApi.closeJob(jobToClose.id);
      setJob(updatedJob);
      setJobToClose(null);
    } catch {
      setActionError('Unable to close job. Please try again.');
    } finally {
      setIsClosingJob(false);
    }
  };

  const onArchiveJob = async () => {
    if (!jobToArchive) return;
    setActionError(null);
    setIsArchivingJob(true);
    try {
      await jobsApi.archiveJob(jobToArchive.id);
      // Redirect to jobs list after archiving since job will be hidden by default
      navigate('/jobs', { replace: true });
    } catch {
      setActionError('Unable to archive job. Please try again.');
    } finally {
      setIsArchivingJob(false);
    }
  };

  const retryLoad = () => {
    if (id) {
      const fetchJob = async () => {
        setIsLoading(true);
        setError(null);
        try {
          const jobData = await jobsApi.getJob(parseInt(id, 10));
          setJob(jobData);
        } catch {
          setError('Unable to load job. Please check your connection and try again.');
        } finally {
          setIsLoading(false);
        }
      };
      void fetchJob();
    }
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'active':
        return 'status-active';
      case 'paused':
        return 'status-paused';
      case 'closed':
        return 'status-closed';
      default:
        return 'status-draft';
    }
  };

  const getWorkModeDisplay = (workMode: string) => {
    const labels = {
      'remote': 'Remote',
      'hybrid': 'Hybrid',
      'on-site': 'On-site'
    };
    return labels[workMode as keyof typeof labels] || workMode;
  };

  const getEmploymentTypeDisplay = (employmentType: string) => {
    const labels = {
      'full-time': 'Full-time',
      'part-time': 'Part-time',
      'contract': 'Contract',
      'internship': 'Internship'
    };
    return labels[employmentType as keyof typeof labels] || employmentType;
  };

  const getEducationRequirementDisplay = (education: string) => {
    const labels = {
      'none': 'No requirement',
      'high_school': 'High School',
      'associate': 'Associate Degree',
      'bachelor': "Bachelor's Degree",
      'master': "Master's Degree",
      'phd': 'PhD'
    };
    return labels[education as keyof typeof labels] || education;
  };

  const formatSalaryRange = (min?: number, max?: number) => {
    if (min && max) {
      return `$${min.toLocaleString()} - $${max.toLocaleString()}`;
    } else if (min) {
      return `$${min.toLocaleString()}+`;
    } else if (max) {
      return `Up to $${max.toLocaleString()}`;
    }
    return 'Not specified';
  };

  const formatCreatedDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  // Check if user has permissions (admin or recruiter can edit jobs per D-04)
  const canEdit = user?.role === 'admin' || user?.role === 'recruiter';

  if (isLoading) {
    return (
      <div className="page-frame">
        <div className="flex items-center justify-center min-h-96">
          <LoaderCircle className="animate-spin" size={32} />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page-frame">
        <section className="management-toolbar">
          <div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate('/jobs')}
              className="mb-2 -ml-2"
            >
              <ArrowLeft size={16} />
              Back to Jobs
            </Button>
            <p className="page-label">Recruitment</p>
            <h1 className="page-heading">Job Details</h1>
          </div>
        </section>

        <Alert variant="destructive">
          <AlertDescription className="flex items-center justify-between gap-3">
            <span>{error}</span>
            {error.includes('connection') && (
              <Button variant="outline" size="sm" onClick={retryLoad}>
                Retry
              </Button>
            )}
          </AlertDescription>
        </Alert>

        {error === 'Job not found' && (
          <div className="text-center py-12">
            <Briefcase className="mx-auto mb-3 text-muted-foreground" size={48} />
            <h2 className="text-xl font-semibold mb-2">Job not found</h2>
            <p className="text-muted-foreground mb-4">
              The job you're looking for doesn't exist or may have been removed.
            </p>
            <Button onClick={() => navigate('/jobs')}>
              Back to Jobs
            </Button>
          </div>
        )}
      </div>
    );
  }

  if (!job) {
    return null;
  }

  return (
    <div className="page-frame">
      <section className="management-toolbar">
        <div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate('/jobs')}
            className="mb-2 -ml-2"
          >
            <ArrowLeft size={16} />
            Back to Jobs
          </Button>
          <p className="page-label">Recruitment</p>
          <h1 className="page-heading">{job.title}</h1>
          <p className="page-heading-copy">{job.department}</p>
        </div>
        
        {canEdit && (
          <div className="management-toolbar-actions">
            <Button
              variant="outline"
              onClick={() => navigate(`/jobs/${job.id}/edit`)}
            >
              <Edit size={16} />
              Edit Job
            </Button>
            {job.status !== 'closed' && (
              <Button
                variant="outline"
                onClick={() => setJobToClose(job)}
              >
                Close Job
              </Button>
            )}
            {!job.archived_at && (
              <Button
                variant="destructive"
                onClick={() => setJobToArchive(job)}
              >
                Archive Job
              </Button>
            )}
          </div>
        )}
      </section>

      {actionError && (
        <Alert variant="destructive">
          <AlertDescription>{actionError}</AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Job Metadata */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Briefcase size={20} />
                Job Overview
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label>Status</Label>
                  <div className="mt-1">
                    <span className={`status-badge ${getStatusBadgeClass(job.status)}`}>
                      {job.status.charAt(0).toUpperCase() + job.status.slice(1)}
                    </span>
                  </div>
                </div>
                
                <div>
                  <Label>Work Mode</Label>
                  <div className="mt-1 text-sm text-muted-foreground">
                    <MapPin size={14} className="inline mr-1" />
                    {getWorkModeDisplay(job.work_mode)} • {job.location}
                  </div>
                </div>

                <div>
                  <Label>Employment Type</Label>
                  <p className="text-sm text-muted-foreground mt-1">
                    {getEmploymentTypeDisplay(job.employment_type)}
                  </p>
                </div>

                <div>
                  <Label>Applicants</Label>
                  <p className="text-sm text-muted-foreground mt-1 flex items-center gap-1">
                    <Users size={14} />
                    {job.applicant_count !== undefined ? job.applicant_count : 'Not available'}
                  </p>
                </div>

                <div>
                  <Label>Experience Required</Label>
                  <p className="text-sm text-muted-foreground mt-1">
                    {job.min_experience === job.max_experience 
                      ? `${job.min_experience} years`
                      : `${job.min_experience}-${job.max_experience} years`
                    }
                  </p>
                </div>

                <div>
                  <Label>Education</Label>
                  <p className="text-sm text-muted-foreground mt-1">
                    {getEducationRequirementDisplay(job.education_requirement)}
                  </p>
                </div>

                <div className="md:col-span-2">
                  <Label>Salary Range</Label>
                  <p className="text-sm text-muted-foreground mt-1">
                    {formatSalaryRange(job.salary_min, job.salary_max)}
                  </p>
                </div>

                <div className="md:col-span-2">
                  <Label>Created</Label>
                  <p className="text-sm text-muted-foreground mt-1 flex items-center gap-1">
                    <Clock size={14} />
                    {formatCreatedDate(job.created_at)}
                  </p>
                </div>

                {job.archived_at && (
                  <div className="md:col-span-2">
                    <Label>Archived</Label>
                    <p className="text-sm text-destructive mt-1">
                      {formatCreatedDate(job.archived_at)}
                    </p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Job Description */}
          <Card>
            <CardHeader>
              <CardTitle>Job Description</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="whitespace-pre-wrap text-sm leading-relaxed">
                {job.description}
              </div>
            </CardContent>
          </Card>

          {/* Resume Upload Section */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-semibold">Candidates</h2>
            </div>
            <ResumeUpload
              jobId={job.id}
              onUploadComplete={(candidates) => {
                toast.success(`${candidates.length} candidate(s) uploaded and linked to this job.`);
              }}
            />
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Screening Weights */}
          <Card>
            <CardHeader>
              <CardTitle>Screening Weights</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm">Skills</span>
                <span className="text-sm font-medium">{job.weight_skills}%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">Experience</span>
                <span className="text-sm font-medium">{job.weight_experience}%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">Education</span>
                <span className="text-sm font-medium">{job.weight_education}%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">Projects</span>
                <span className="text-sm font-medium">{job.weight_projects}%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm">Certifications</span>
                <span className="text-sm font-medium">{job.weight_certs}%</span>
              </div>
              <div className="pt-2 border-t">
                <div className="flex justify-between items-center font-medium">
                  <span className="text-sm">Total</span>
                  <span className="text-sm">
                    {job.weight_skills + job.weight_experience + job.weight_education + job.weight_projects + job.weight_certs}%
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Skills & Certifications */}
          <Card>
            <CardHeader>
              <CardTitle>Skills & Certifications</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  Required Skills
                </Label>
                <div className="flex flex-wrap gap-1 mt-2">
                  {job.required_skills.length > 0 ? (
                    job.required_skills.map((skill, index) => (
                      <span key={index} className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-primary/10 text-primary">
                        {skill}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-muted-foreground">None specified</span>
                  )}
                </div>
              </div>

              <div>
                <Label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  Preferred Skills
                </Label>
                <div className="flex flex-wrap gap-1 mt-2">
                  {job.preferred_skills.length > 0 ? (
                    job.preferred_skills.map((skill, index) => (
                      <span key={index} className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-secondary text-secondary-foreground">
                        {skill}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-muted-foreground">None specified</span>
                  )}
                </div>
              </div>

              <div>
                <Label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  Required Certifications
                </Label>
                <div className="flex flex-wrap gap-1 mt-2">
                  {job.required_certs.length > 0 ? (
                    job.required_certs.map((cert, index) => (
                      <span key={index} className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-primary/10 text-primary">
                        {cert}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-muted-foreground">None specified</span>
                  )}
                </div>
              </div>

              <div>
                <Label className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  Preferred Certifications
                </Label>
                <div className="flex flex-wrap gap-1 mt-2">
                  {job.preferred_certs.length > 0 ? (
                    job.preferred_certs.map((cert, index) => (
                      <span key={index} className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-secondary text-secondary-foreground">
                        {cert}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-muted-foreground">None specified</span>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Close Job Confirmation Dialog */}
      <Dialog open={Boolean(jobToClose)} onOpenChange={(open) => !open && setJobToClose(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Close Job</DialogTitle>
            <DialogDescription>
              Close Job: Are you sure you want to close this job? Existing candidate history will be retained.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setJobToClose(null)} disabled={isClosingJob}>
              Cancel
            </Button>
            <Button onClick={() => void onCloseJob()} disabled={isClosingJob}>
              {isClosingJob && <LoaderCircle className="animate-spin" aria-hidden="true" />}
              {isClosingJob ? 'Closing job' : 'Confirm'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Archive Job Confirmation Dialog */}
      <Dialog open={Boolean(jobToArchive)} onOpenChange={(open) => !open && setJobToArchive(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Archive Job</DialogTitle>
            <DialogDescription>
              Archive Job: This job and its candidate history will be retained but hidden from active listings.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setJobToArchive(null)} disabled={isArchivingJob}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => void onArchiveJob()}
              disabled={isArchivingJob}
            >
              {isArchivingJob && <LoaderCircle className="animate-spin" aria-hidden="true" />}
              {isArchivingJob ? 'Archiving job' : 'Archive Job'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// Label component for consistent styling
function Label({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <label className={`text-sm font-medium leading-none ${className}`}>
      {children}
    </label>
  );
}