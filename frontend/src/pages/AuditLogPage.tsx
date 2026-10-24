import { useCallback, useEffect, useState } from 'react';
import { ChevronLeft, ChevronRight, ScrollText } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
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
import apiClient from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';

interface AuditLogEntry {
  id: number;
  user_id: number;
  user_email: string;
  action: string;
  resource_type: string;
  resource_id: number | null;
  metadata_: Record<string, unknown>;
  created_at: string;
}

interface AuditLogListResponse {
  items: AuditLogEntry[];
  total: number;
}

const PAGE_SIZE = 30;

export function AuditLogPage() {
  const { user } = useAuth();
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [actionFilter, setActionFilter] = useState('');
  const [resourceFilter, setResourceFilter] = useState('');

  const fetchLogs = useCallback(async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('skip', (page * PAGE_SIZE).toString());
      params.append('limit', PAGE_SIZE.toString());
      if (actionFilter) params.append('action', actionFilter);
      if (resourceFilter) params.append('resource_type', resourceFilter);

      const response = await apiClient.get<AuditLogListResponse>(`/audit/?${params.toString()}`);
      setLogs(response.data.items);
      setTotal(response.data.total);
    } catch {
      setLogs([]);
      setTotal(0);
    } finally {
      setIsLoading(false);
    }
  }, [page, actionFilter, resourceFilter]);

  useEffect(() => {
    void fetchLogs();
  }, [fetchLogs]);

  // Admin-only guard
  if (user?.role !== 'admin') {
    return (
      <div className="page-frame">
        <p className="text-destructive">Access denied. Admin role required.</p>
      </div>
    );
  }

  const totalPages = Math.ceil(total / PAGE_SIZE);

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleString();
  };

  const getActionBadge = (action: string) => {
    if (action.includes('delete')) return <Badge variant="destructive">{action}</Badge>;
    if (action.includes('create') || action.includes('scheduled')) return <Badge variant="success">{action}</Badge>;
    return <Badge variant="secondary">{action}</Badge>;
  };

  return (
    <div className="page-frame">
      <section className="management-toolbar" aria-labelledby="audit-heading">
        <div>
          <p className="page-label">Administration</p>
          <h1 id="audit-heading" className="page-heading">Audit Log</h1>
          <p className="page-heading-copy">Immutable record of all system actions. Read-only.</p>
        </div>
        <ScrollText aria-hidden="true" size={24} className="text-primary" />
      </section>

      {/* Filters */}
      <div className="flex gap-3 mb-4">
        <Select onValueChange={(v) => { setActionFilter(v === 'all' ? '' : v); setPage(0); }} value={actionFilter || 'all'}>
          <SelectTrigger className="w-52">
            <SelectValue placeholder="All actions" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All actions</SelectItem>
            <SelectItem value="candidate.list">Candidate Listed</SelectItem>
            <SelectItem value="candidate.note_created">Note Created</SelectItem>
            <SelectItem value="candidate.deleted">Candidate Deleted</SelectItem>
            <SelectItem value="application.status_changed">Status Changed</SelectItem>
            <SelectItem value="interview.scheduled">Interview Scheduled</SelectItem>
            <SelectItem value="interview.cancelled">Interview Cancelled</SelectItem>
            <SelectItem value="setting.updated">Setting Updated</SelectItem>
          </SelectContent>
        </Select>
        <Select onValueChange={(v) => { setResourceFilter(v === 'all' ? '' : v); setPage(0); }} value={resourceFilter || 'all'}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="All resources" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All resources</SelectItem>
            <SelectItem value="candidate">Candidate</SelectItem>
            <SelectItem value="application">Application</SelectItem>
            <SelectItem value="interview">Interview</SelectItem>
            <SelectItem value="setting">Setting</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Table */}
      <Card className="table-shell">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Timestamp</TableHead>
                  <TableHead>User</TableHead>
                  <TableHead>Action</TableHead>
                  <TableHead>Resource</TableHead>
                  <TableHead>Resource ID</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  Array.from({ length: 5 }).map((_, i) => (
                    <TableRow key={`skel-${i}`} aria-busy="true">
                      <TableCell><div className="loading-bar w-28" /></TableCell>
                      <TableCell><div className="loading-bar w-32" /></TableCell>
                      <TableCell><div className="loading-bar w-24" /></TableCell>
                      <TableCell><div className="loading-bar w-20" /></TableCell>
                      <TableCell><div className="loading-bar w-12" /></TableCell>
                    </TableRow>
                  ))
                ) : logs.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} className="h-32 text-center">
                      <p className="text-muted-foreground">No audit log entries found.</p>
                    </TableCell>
                  </TableRow>
                ) : (
                  logs.map((log) => (
                    <TableRow key={log.id}>
                      <TableCell className="table-meta whitespace-nowrap">
                        {formatDate(log.created_at)}
                      </TableCell>
                      <TableCell className="text-sm">{log.user_email}</TableCell>
                      <TableCell>{getActionBadge(log.action)}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">{log.resource_type}</TableCell>
                      <TableCell className="text-sm">{log.resource_id ?? '—'}</TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-2 mt-4" role="navigation" aria-label="Audit log pagination">
          <p className="text-sm text-muted-foreground">
            Showing {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, total)} of {total}
          </p>
          <div className="flex items-center gap-1">
            <Button variant="outline" size="icon" disabled={page === 0} onClick={() => setPage(page - 1)} aria-label="Previous page">
              <ChevronLeft size={16} aria-hidden="true" />
            </Button>
            <span className="px-3 text-sm">Page {page + 1} of {totalPages}</span>
            <Button variant="outline" size="icon" disabled={page >= totalPages - 1} onClick={() => setPage(page + 1)} aria-label="Next page">
              <ChevronRight size={16} aria-hidden="true" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
