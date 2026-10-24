import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Briefcase, LoaderCircle, MoreHorizontal, Plus } from 'lucide-react';
import { jobsApi, type Job, type JobListResponse } from '@/lib/api';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

export function JobsPage() {
  const navigate = useNavigate();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [includeArchived, setIncludeArchived] = useState(false);
  const [jobToClose, setJobToClose] = useState<Job | null>(null);
  const [jobToArchive, setJobToArchive] = useState<Job | null>(null);
  const [isClosingJob, setIsClosingJob] = useState(false);
  const [isArchivingJob, setIsArchivingJob] = useState(false);
  const itemsPerPage = 10;

  const fetchJobs = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const skip = (page - 1) * itemsPerPage;
      const response: JobListResponse = await jobsApi.getJobs(
        skip,
        itemsPerPage,
        statusFilter || undefined,
        includeArchived
      );
      setJobs(response.items);
      setTotal(response.total);
    } catch {
      setError('Unable to load jobs. Check your connection and try again.');
    } finally {
      setIsLoading(false);
    }
  }, [page, statusFilter, includeArchived]);

  useEffect(() => {
    void fetchJobs();
  }, [fetchJobs]);

  const handleStatusFilterChange = (value: string) => {
    setStatusFilter(value === 'all' ? '' : value);
    setPage(1); // Reset to first page when filtering
  };

  const handleIncludeArchivedChange = (checked: boolean) => {
    setIncludeArchived(checked);
    setPage(1); // Reset to first page when filtering
  };

  const onCloseJob = async () => {
    if (!jobToClose) return;
    setActionError(null);
    setIsClosingJob(true);
    try {
      await jobsApi.closeJob(jobToClose.id);
      setJobToClose(null);
      await fetchJobs();
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
      setJobToArchive(null);
      await fetchJobs();
    } catch {
      setActionError('Unable to archive job. Please try again.');
    } finally {
      setIsArchivingJob(false);
    }
  };

  const formatCreatedDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
    
    if (diffInDays < 30) {
      if (diffInDays === 0) return 'Today';
      if (diffInDays === 1) return '1 day ago';
      return `${diffInDays} days ago`;
    }
    
    return date.toLocaleDateString();
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

  const getWorkModeBadge = (workMode: string) => {
    const labels = {
      'remote': 'Remote',
      'hybrid': 'Hybrid',
      'on-site': 'On-site'
    };
    return labels[workMode as keyof typeof labels] || workMode;
  };

  const firstVisibleJob = jobs.length === 0 ? 0 : (page - 1) * itemsPerPage + 1;
  const lastVisibleJob = (page - 1) * itemsPerPage + jobs.length;
  const hasNextPage = total > page * itemsPerPage;

  return (
    <div className="page-frame">
      <section className="management-toolbar" aria-labelledby="jobs-heading">
        <div>
          <p className="page-label">Recruitment</p>
          <h1 id="jobs-heading" className="page-heading">Jobs</h1>
          <p className="page-heading-copy">Create and manage job openings to attract the right candidates.</p>
        </div>
        <div className="management-toolbar-actions">
          <Select onValueChange={handleStatusFilterChange} value={statusFilter || 'all'}>
            <SelectTrigger className="w-32">
              <SelectValue placeholder="All statuses" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All statuses</SelectItem>
              <SelectItem value="draft">Draft</SelectItem>
              <SelectItem value="active">Active</SelectItem>
              <SelectItem value="paused">Paused</SelectItem>
              <SelectItem value="closed">Closed</SelectItem>
            </SelectContent>
          </Select>
          <Button
            variant={includeArchived ? "default" : "outline"}
            size="sm"
            onClick={() => handleIncludeArchivedChange(!includeArchived)}
          >
            {includeArchived ? 'Hide archived' : 'Show archived'}
          </Button>
          <Button onClick={() => navigate('/jobs/new')}>
            <Plus aria-hidden="true" /> Create Job
          </Button>
        </div>
      </section>

      {error && (
        <Alert variant="destructive">
          <AlertDescription className="flex items-center justify-between gap-3">
            <span>{error}</span>
            <Button variant="outline" size="sm" onClick={() => void fetchJobs()}>Retry</Button>
          </AlertDescription>
        </Alert>
      )}
      {actionError && (
        <Alert variant="destructive">
          <AlertDescription>{actionError}</AlertDescription>
        </Alert>
      )}

      <section aria-labelledby="jobs-table-heading">
        <div className="access-table-head">
          <div>
            <h2 id="jobs-table-heading">Job Openings</h2>
            <p>Review and manage all job postings and their current status.</p>
          </div>
          <Briefcase aria-hidden="true" size={20} color="var(--primary)" />
        </div>
        <Card className="table-shell">
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Title</TableHead>
                    <TableHead>Department</TableHead>
                    <TableHead>Work Mode</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Applicant Count</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead><span className="sr-only">Actions</span></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {isLoading ? Array.from({ length: 5 }).map((_, index) => (
                    <TableRow key={`skeleton-${index}`} aria-busy="true">
                      <TableCell><div className="loading-bar w-48" /></TableCell>
                      <TableCell><div className="loading-bar w-20" /></TableCell>
                      <TableCell><div className="loading-bar w-16" /></TableCell>
                      <TableCell><div className="loading-bar w-16" /></TableCell>
                      <TableCell><div className="loading-bar w-12" /></TableCell>
                      <TableCell><div className="loading-bar w-24" /></TableCell>
                      <TableCell><div className="loading-bar ml-auto w-8" /></TableCell>
                    </TableRow>
                  )) : jobs.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7} className="h-44 text-center">
                        <Briefcase className="mx-auto mb-3 text-muted-foreground" aria-hidden="true" size={24} />
                        <p className="font-semibold text-foreground">No jobs posted yet</p>
                        <p className="mt-1 text-sm text-muted-foreground">Create your first job opening to begin attracting candidates.</p>
                        <Button className="mt-3" onClick={() => navigate('/jobs/new')}>
                          Create Job
                        </Button>
                      </TableCell>
                    </TableRow>
                  ) : jobs.map((job) => (
                    <TableRow key={job.id}>
                      <TableCell className="max-w-[20rem]">
                        <button
                          onClick={() => navigate(`/jobs/${job.id}`)}
                          className="text-left font-medium hover:underline focus:underline truncate w-full"
                          title={job.title}
                        >
                          {job.title}
                        </button>
                      </TableCell>
                      <TableCell className="max-w-[16ch] truncate text-muted-foreground" title={job.department}>
                        {job.department || '—'}
                      </TableCell>
                      <TableCell>
                        <span className="role-chip">
                          {getWorkModeBadge(job.work_mode)}
                        </span>
                      </TableCell>
                      <TableCell>
                        <span className={`status-badge ${getStatusBadgeClass(job.status)}`}>
                          {job.status.charAt(0).toUpperCase() + job.status.slice(1)}
                        </span>
                      </TableCell>
                      <TableCell className="table-meta">
                        {job.applicant_count !== undefined ? job.applicant_count : 'Not available'}
                      </TableCell>
                      <TableCell className="table-meta">
                        {formatCreatedDate(job.created_at)}
                      </TableCell>
                      <TableCell className="user-actions-cell">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" aria-label={`Manage ${job.title}`}>
                              <MoreHorizontal aria-hidden="true" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => navigate(`/jobs/${job.id}`)}>
                              View
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => navigate(`/jobs/${job.id}/edit`)}>
                              Edit
                            </DropdownMenuItem>
                            {job.status !== 'closed' && (
                              <DropdownMenuItem onClick={() => setJobToClose(job)}>
                                Close Job
                              </DropdownMenuItem>
                            )}
                            {!job.archived_at && (
                              <DropdownMenuItem 
                                className="text-destructive focus:bg-destructive/10"
                                onClick={() => setJobToArchive(job)}
                              >
                                Archive Job
                              </DropdownMenuItem>
                            )}
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            {!isLoading && jobs.length > 0 && total > itemsPerPage && (
              <div className="table-pagination">
                <p className="table-pagination-copy">
                  Showing {firstVisibleJob}–{lastVisibleJob} of {total} jobs
                </p>
                <div className="table-pagination-actions">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage((current) => Math.max(1, current - 1))}
                    disabled={page === 1}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage((current) => current + 1)}
                    disabled={!hasNextPage}
                  >
                    Next
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </section>

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