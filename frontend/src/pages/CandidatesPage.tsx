import { useCallback, useEffect, useState } from 'react';
import { ChevronLeft, ChevronRight, Download, LoaderCircle, MoreHorizontal, Search, Users } from 'lucide-react';
import { toast } from 'sonner';
import { candidatesApi, type Candidate, type CandidateListResponse } from '@/lib/api';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
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
import { Input } from '@/components/ui/input';
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
import { ResumeUpload, type CandidateResponse } from '@/components/candidates/ResumeUpload';
import { CandidateEditForm } from '@/components/candidates/CandidateEditForm';
import { CandidateDetail } from '@/components/candidates/CandidateDetail';

const PAGE_SIZE = 20;

export function CandidatesPage() {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [sortBy, setSortBy] = useState<string>('created_at');
  const [sortOrder, setSortOrder] = useState<string>('desc');
  const [page, setPage] = useState(0);
  const [editingCandidate, setEditingCandidate] = useState<Candidate | null>(null);
  const [candidateToDelete, setCandidateToDelete] = useState<Candidate | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [detailCandidate, setDetailCandidate] = useState<Candidate | null>(null);

  const fetchCandidates = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response: CandidateListResponse = await candidatesApi.getCandidates(
        page * PAGE_SIZE,
        PAGE_SIZE,
        statusFilter || undefined,
        searchQuery || undefined,
        sortBy,
        sortOrder
      );
      setCandidates(response.items);
      setTotal(response.total);
    } catch {
      setError('Unable to load candidates. Check your connection and try again.');
    } finally {
      setIsLoading(false);
    }
  }, [statusFilter, searchQuery, sortBy, sortOrder, page]);

  useEffect(() => {
    void fetchCandidates();
  }, [fetchCandidates]);

  // Reset to page 0 when filters change
  const handleStatusFilterChange = (value: string) => {
    setStatusFilter(value === 'all' ? '' : value);
    setPage(0);
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
    setPage(0);
  };

  const handleSortChange = (value: string) => {
    const [field, order] = value.split(':');
    setSortBy(field);
    setSortOrder(order);
    setPage(0);
  };

  const totalPages = Math.ceil(total / PAGE_SIZE);

  const handleUploadComplete = (_candidates: CandidateResponse[]) => {
    void fetchCandidates();
  };

  const handleEditSave = (updated: Candidate) => {
    setCandidates((prev) =>
      prev.map((c) => (c.id === updated.id ? updated : c))
    );
    setEditingCandidate(null);
    toast.success('Candidate profile updated successfully.');
  };

  const handleDelete = async () => {
    if (!candidateToDelete) return;
    setIsDeleting(true);
    try {
      await candidatesApi.deleteCandidate(candidateToDelete.id);
      setCandidateToDelete(null);
      toast.success('Candidate deleted successfully.');
      await fetchCandidates();
    } catch {
      toast.error('Unable to delete candidate. Please try again.');
    } finally {
      setIsDeleting(false);
    }
  };

  const handleDownload = (candidate: Candidate) => {
    const url = candidatesApi.downloadResume(candidate.id);
    const link = document.createElement('a');
    link.href = url;
    link.download = candidate.original_filename || 'resume';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const formatCreatedDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));

    if (diffInDays === 0) return 'Today';
    if (diffInDays === 1) return '1 day ago';
    if (diffInDays < 30) return `${diffInDays} days ago`;
    return date.toLocaleDateString();
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'complete':
        return <Badge variant="success">Complete</Badge>;
      case 'pending_review':
        return <Badge variant="warning">Pending Review</Badge>;
      default:
        return <Badge variant="destructive">Failed</Badge>;
    }
  };

  const truncateSkills = (skills: string[], max: number = 3) => {
    if (skills.length <= max) return skills.join(', ');
    return `${skills.slice(0, max).join(', ')} +${skills.length - max} more`;
  };

  return (
    <div className="page-frame">
      <section className="management-toolbar" aria-labelledby="candidates-heading">
        <div>
          <p className="page-label">Recruitment</p>
          <h1 id="candidates-heading" className="page-heading">Candidates</h1>
          <p className="page-heading-copy">View and manage candidate profiles from uploaded resumes.</p>
        </div>
        <div className="management-toolbar-actions">
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" aria-hidden="true" />
            <Input
              type="search"
              placeholder="Search name, email, skills…"
              value={searchQuery}
              onChange={handleSearchChange}
              className="pl-8 w-56"
              aria-label="Search candidates"
            />
          </div>
          <Select onValueChange={handleStatusFilterChange} value={statusFilter || 'all'}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="All statuses" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All statuses</SelectItem>
              <SelectItem value="complete">Complete</SelectItem>
              <SelectItem value="pending_review">Pending Review</SelectItem>
            </SelectContent>
          </Select>
          <Select onValueChange={handleSortChange} value={`${sortBy}:${sortOrder}`}>
            <SelectTrigger className="w-44">
              <SelectValue placeholder="Sort by" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="created_at:desc">Newest first</SelectItem>
              <SelectItem value="created_at:asc">Oldest first</SelectItem>
              <SelectItem value="name:asc">Name A–Z</SelectItem>
              <SelectItem value="name:desc">Name Z–A</SelectItem>
            </SelectContent>
          </Select>
          <ResumeUpload onUploadComplete={handleUploadComplete} />
        </div>
      </section>

      {error && (
        <Alert variant="destructive">
          <AlertDescription className="flex items-center justify-between gap-3">
            <span>{error}</span>
            <Button variant="outline" size="sm" onClick={() => void fetchCandidates()}>Retry</Button>
          </AlertDescription>
        </Alert>
      )}

      <section aria-labelledby="candidates-table-heading">
        <div className="access-table-head">
          <div>
            <h2 id="candidates-table-heading">Candidate Profiles</h2>
            <p>Review parsed candidate profiles and complete pending reviews.</p>
          </div>
          <Users aria-hidden="true" size={20} color="var(--primary)" />
        </div>
        <Card className="table-shell">
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Skills</TableHead>
                    <TableHead>Applied Date</TableHead>
                    <TableHead><span className="sr-only">Actions</span></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {isLoading ? Array.from({ length: 5 }).map((_, index) => (
                    <TableRow key={`skeleton-${index}`} aria-busy="true">
                      <TableCell><div className="loading-bar w-32" /></TableCell>
                      <TableCell><div className="loading-bar w-40" /></TableCell>
                      <TableCell><div className="loading-bar w-24" /></TableCell>
                      <TableCell><div className="loading-bar w-36" /></TableCell>
                      <TableCell><div className="loading-bar w-20" /></TableCell>
                      <TableCell><div className="loading-bar ml-auto w-8" /></TableCell>
                    </TableRow>
                  )) : candidates.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} className="h-44 text-center">
                        <Users className="mx-auto mb-3 text-muted-foreground" aria-hidden="true" size={24} />
                        <p className="font-semibold text-foreground">No candidates yet</p>
                        <p className="mt-1 text-sm text-muted-foreground">
                          Upload resumes to create candidate profiles. Drag files here or use the Upload button.
                        </p>
                        <div className="mt-3">
                          <ResumeUpload onUploadComplete={handleUploadComplete} />
                        </div>
                      </TableCell>
                    </TableRow>
                  ) : candidates.map((candidate) => (
                    <TableRow key={candidate.id} className="h-[52px]">
                      <TableCell className="font-medium">
                        {candidate.name || '—'}
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {candidate.email || '—'}
                      </TableCell>
                      <TableCell>
                        {getStatusBadge(candidate.status)}
                      </TableCell>
                      <TableCell className="text-muted-foreground max-w-[200px] truncate" title={candidate.skills.join(', ')}>
                        {candidate.skills.length > 0 ? truncateSkills(candidate.skills) : '—'}
                      </TableCell>
                      <TableCell className="table-meta">
                        {formatCreatedDate(candidate.created_at)}
                      </TableCell>
                      <TableCell className="user-actions-cell">
                        <div className="flex items-center gap-1">
                          {candidate.status === 'pending_review' && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => setEditingCandidate(candidate)}
                            >
                              Review
                            </Button>
                          )}
                          {candidate.resume_path && (
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => handleDownload(candidate)}
                              aria-label={`Download resume for ${candidate.name || 'candidate'}`}
                            >
                              <Download aria-hidden="true" />
                            </Button>
                          )}
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="icon" aria-label={`Manage ${candidate.name || 'candidate'}`}>
                                <MoreHorizontal aria-hidden="true" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem onClick={() => setDetailCandidate(candidate)}>
                                View Details
                              </DropdownMenuItem>
                              {candidate.status === 'pending_review' && (
                                <DropdownMenuItem onClick={() => setEditingCandidate(candidate)}>
                                  Review Profile
                                </DropdownMenuItem>
                              )}
                              {candidate.resume_path && (
                                <DropdownMenuItem onClick={() => handleDownload(candidate)}>
                                  Download Resume
                                </DropdownMenuItem>
                              )}
                              <DropdownMenuItem
                                className="text-destructive focus:bg-destructive/10"
                                onClick={() => setCandidateToDelete(candidate)}
                              >
                                Delete
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-2" role="navigation" aria-label="Pagination">
          <p className="text-sm text-muted-foreground">
            Showing {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, total)} of {total}
          </p>
          <div className="flex items-center gap-1">
            <Button
              variant="outline"
              size="icon"
              disabled={page === 0}
              onClick={() => setPage(page - 1)}
              aria-label="Previous page"
            >
              <ChevronLeft size={16} aria-hidden="true" />
            </Button>
            <span className="px-3 text-sm">
              Page {page + 1} of {totalPages}
            </span>
            <Button
              variant="outline"
              size="icon"
              disabled={page >= totalPages - 1}
              onClick={() => setPage(page + 1)}
              aria-label="Next page"
            >
              <ChevronRight size={16} aria-hidden="true" />
            </Button>
          </div>
        </div>
      )}

      {/* Candidate Edit Dialog */}
      <Dialog open={Boolean(editingCandidate)} onOpenChange={(open) => !open && setEditingCandidate(null)}>
        <DialogContent className="sm:max-w-[640px] max-h-[85vh] overflow-y-auto">
          {editingCandidate && (
            <CandidateEditForm
              candidate={editingCandidate}
              onSave={handleEditSave}
              onCancel={() => setEditingCandidate(null)}
            />
          )}
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={Boolean(candidateToDelete)} onOpenChange={(open) => !open && setCandidateToDelete(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Candidate</DialogTitle>
            <DialogDescription>
              This will permanently remove the candidate profile and their resume file. This cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCandidateToDelete(null)} disabled={isDeleting}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={() => void handleDelete()} disabled={isDeleting}>
              {isDeleting && <LoaderCircle className="animate-spin" aria-hidden="true" />}
              {isDeleting ? 'Deleting…' : 'Delete Candidate'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {/* Candidate Detail Dialog */}
      {detailCandidate && (
        <CandidateDetail
          candidate={detailCandidate}
          open={Boolean(detailCandidate)}
          onClose={() => setDetailCandidate(null)}
        />
      )}
    </div>
  );
}
