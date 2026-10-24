import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { BarChart3, Users } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import apiClient from '@/lib/api';

interface ComparisonCandidate {
  id: number;
  name: string | null;
  email: string | null;
  location: string | null;
  skills: string[];
  experience_count: number;
  education_count: number;
  certifications_count: number;
  status: string;
}

export function CandidateComparePage() {
  const [searchParams] = useSearchParams();
  const [candidates, setCandidates] = useState<ComparisonCandidate[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const ids = searchParams.getAll('ids');
    if (ids.length < 2) {
      setError('Select at least 2 candidates to compare.');
      setIsLoading(false);
      return;
    }

    const fetchComparison = async () => {
      try {
        const params = new URLSearchParams();
        ids.forEach((id) => params.append('ids', id));
        const response = await apiClient.get<{ candidates: ComparisonCandidate[] }>(
          `/candidates/compare?${params.toString()}`
        );
        setCandidates(response.data.candidates);
      } catch {
        setError('Unable to load comparison data.');
      } finally {
        setIsLoading(false);
      }
    };

    void fetchComparison();
  }, [searchParams]);

  if (isLoading) {
    return (
      <div className="page-frame">
        <p className="text-muted-foreground">Loading comparison…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page-frame">
        <p className="text-destructive">{error}</p>
      </div>
    );
  }

  const fields: { label: string; key: keyof ComparisonCandidate | 'skills_display' | 'metrics' }[] = [
    { label: 'Name', key: 'name' },
    { label: 'Email', key: 'email' },
    { label: 'Location', key: 'location' },
    { label: 'Status', key: 'status' },
    { label: 'Skills', key: 'skills_display' },
    { label: 'Metrics', key: 'metrics' },
  ];

  return (
    <div className="page-frame">
      <section className="management-toolbar" aria-labelledby="compare-heading">
        <div>
          <p className="page-label">Recruitment</p>
          <h1 id="compare-heading" className="page-heading">Compare Candidates</h1>
          <p className="page-heading-copy">
            Side-by-side comparison of {candidates.length} candidates.
          </p>
        </div>
        <BarChart3 aria-hidden="true" size={24} className="text-primary" />
      </section>

      <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${candidates.length}, 1fr)` }}>
        {candidates.map((candidate) => (
          <Card key={candidate.id}>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2">
                <Users size={16} aria-hidden="true" />
                {candidate.name || `Candidate #${candidate.id}`}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <p className="text-xs text-muted-foreground">Email</p>
                <p className="text-sm">{candidate.email || '—'}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Location</p>
                <p className="text-sm">{candidate.location || '—'}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Status</p>
                <Badge variant="secondary">{candidate.status}</Badge>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Skills ({candidate.skills.length})</p>
                <div className="flex flex-wrap gap-1 mt-1">
                  {candidate.skills.slice(0, 6).map((skill) => (
                    <Badge key={skill} variant="outline" className="text-xs">
                      {skill}
                    </Badge>
                  ))}
                  {candidate.skills.length > 6 && (
                    <Badge variant="outline" className="text-xs">
                      +{candidate.skills.length - 6} more
                    </Badge>
                  )}
                </div>
              </div>
              <div className="grid grid-cols-3 gap-2 pt-2 border-t">
                <div className="text-center">
                  <p className="text-lg font-semibold">{candidate.experience_count}</p>
                  <p className="text-xs text-muted-foreground">Experience</p>
                </div>
                <div className="text-center">
                  <p className="text-lg font-semibold">{candidate.education_count}</p>
                  <p className="text-xs text-muted-foreground">Education</p>
                </div>
                <div className="text-center">
                  <p className="text-lg font-semibold">{candidate.certifications_count}</p>
                  <p className="text-xs text-muted-foreground">Certs</p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
