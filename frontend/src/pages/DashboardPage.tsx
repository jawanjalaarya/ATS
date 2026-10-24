import { useEffect, useState } from 'react';
import { Briefcase, CalendarDays, FileText, Users } from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  CartesianGrid,
} from 'recharts';
import apiClient from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';

interface DashboardStats {
  summary: {
    total_jobs: number;
    active_jobs: number;
    total_candidates: number;
    total_applications: number;
    total_interviews: number;
    scheduled_interviews: number;
  };
  applications_by_status: Record<string, number>;
  jobs_by_department: { name: string; count: number }[];
}

const STATUS_COLORS: Record<string, string> = {
  applied: 'oklch(0.55 0.15 195)',
  screening: 'oklch(0.60 0.14 265)',
  shortlisted: 'oklch(0.62 0.12 145)',
  interview: 'oklch(0.58 0.13 50)',
  selected: 'oklch(0.48 0.14 160)',
  rejected: 'oklch(0.55 0.05 260)',
};

function CustomTooltip({ active, payload, label }: { active?: boolean; payload?: Array<{ value: number; name: string; color?: string }>; label?: string }) {
  if (!active || !payload?.length) return null;

  return (
    <div className="rounded-lg border border-border bg-card px-3 py-2 shadow-lg">
      {label && <p className="text-xs font-medium text-muted-foreground mb-1">{label}</p>}
      {payload.map((entry, i) => (
        <p key={i} className="text-sm font-semibold text-foreground">
          {entry.name}: {entry.value}
        </p>
      ))}
    </div>
  );
}

function PieTooltip({ active, payload }: { active?: boolean; payload?: Array<{ name: string; value: number; payload: { fill: string } }> }) {
  if (!active || !payload?.length) return null;
  const entry = payload[0];

  return (
    <div className="rounded-lg border border-border bg-card px-3 py-2 shadow-lg">
      <div className="flex items-center gap-2">
        <span
          className="inline-block w-2.5 h-2.5 rounded-full"
          style={{ background: entry.payload.fill }}
        />
        <span className="text-sm font-semibold text-foreground">
          {entry.name}: {entry.value}
        </span>
      </div>
    </div>
  );
}

export function DashboardPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await apiClient.get<DashboardStats>('/jobs/dashboard/stats');
        setStats(response.data);
      } catch {
        // Silently fail - dashboard shows empty state
      } finally {
        setIsLoading(false);
      }
    };

    void fetchStats();
  }, []);

  const accountName = user?.email?.split('@')[0] ?? 'there';

  if (isLoading) {
    return (
      <div className="page-frame">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="stat-card">
              <div className="stat-card-icon loading-bar !w-11 !h-11 !rounded-xl" />
              <div className="stat-card-body">
                <div className="loading-bar w-20 h-3 mb-2" />
                <div className="loading-bar w-14 h-7 mb-2" />
                <div className="loading-bar w-24 h-3" />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  const summary = stats?.summary ?? {
    total_jobs: 0,
    active_jobs: 0,
    total_candidates: 0,
    total_applications: 0,
    total_interviews: 0,
    scheduled_interviews: 0,
  };

  const statusData = Object.entries(stats?.applications_by_status ?? {}).map(([status, count]) => ({
    name: status.charAt(0).toUpperCase() + status.slice(1),
    value: count,
    fill: STATUS_COLORS[status] ?? 'oklch(0.55 0.05 260)',
  }));

  const deptData = stats?.jobs_by_department ?? [];

  const statCards = [
    {
      label: 'Active Jobs',
      value: summary.active_jobs,
      meta: `${summary.total_jobs} total jobs`,
      icon: Briefcase,
      accent: 'stat-card-icon--blue' as const,
    },
    {
      label: 'Candidates',
      value: summary.total_candidates,
      meta: `${summary.total_applications} applications`,
      icon: Users,
      accent: 'stat-card-icon--teal' as const,
    },
    {
      label: 'Applications',
      value: summary.total_applications,
      meta: 'Across all jobs',
      icon: FileText,
      accent: 'stat-card-icon--amber' as const,
    },
    {
      label: 'Interviews',
      value: summary.scheduled_interviews,
      meta: `${summary.total_interviews} total conducted`,
      icon: CalendarDays,
      accent: 'stat-card-icon--violet' as const,
    },
  ];

  return (
    <div className="page-frame">
      <section className="management-toolbar" aria-labelledby="dashboard-title">
        <div>
          <p className="page-label">Analytics</p>
          <h1 id="dashboard-title" className="page-heading">Dashboard</h1>
          <p className="page-heading-copy">Welcome back, {accountName}. Here's your recruitment overview.</p>
        </div>
      </section>

      {/* Stat Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mt-6">
        {statCards.map((card, i) => {
          const Icon = card.icon;
          return (
            <div
              key={card.label}
              className={`stat-card animate-fade-in-up stagger-${i + 1}`}
            >
              <div className={`stat-card-icon ${card.accent}`}>
                <Icon aria-hidden="true" />
              </div>
              <div className="stat-card-body">
                <p className="stat-card-label">{card.label}</p>
                <p className="stat-card-value">{card.value}</p>
                <p className="stat-card-meta">{card.meta}</p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Charts */}
      <div className="grid gap-4 md:grid-cols-2 mt-6">
        {/* Applications by Status - Pie Chart */}
        <div className="chart-card animate-fade-in-up stagger-3">
          <div className="chart-card-header">
            <h2 className="chart-card-title">Pipeline Status</h2>
            <p className="chart-card-description">Application distribution across workflow stages</p>
          </div>
          {statusData.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                  data={statusData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  innerRadius={56}
                  outerRadius={95}
                  strokeWidth={2}
                  stroke="var(--card)"
                >
                  {statusData.map((entry, idx) => (
                    <Cell key={idx} fill={entry.fill} />
                  ))}
                </Pie>
                <Tooltip content={<PieTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty-state">
              <div className="empty-state-icon">
                <FileText aria-hidden="true" />
              </div>
              <p className="empty-state-title">No application data yet</p>
              <p className="empty-state-description">
                Application pipeline data will appear here once candidates begin applying.
              </p>
            </div>
          )}
        </div>

        {/* Jobs by Department - Bar Chart */}
        <div className="chart-card animate-fade-in-up stagger-4">
          <div className="chart-card-header">
            <h2 className="chart-card-title">Jobs by Department</h2>
            <p className="chart-card-description">Distribution of open positions</p>
          </div>
          {deptData.length > 0 ? (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={deptData} barCategoryGap="28%">
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="oklch(0.92 0.006 260)"
                  vertical={false}
                />
                <XAxis
                  dataKey="name"
                  fontSize={12}
                  tickLine={false}
                  axisLine={false}
                  tick={{ fill: 'oklch(0.46 0.02 265)' }}
                />
                <YAxis
                  allowDecimals={false}
                  fontSize={12}
                  tickLine={false}
                  axisLine={false}
                  tick={{ fill: 'oklch(0.46 0.02 265)' }}
                  width={32}
                />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: 'oklch(0.96 0.008 195 / 0.3)' }} />
                <Bar
                  dataKey="count"
                  name="Jobs"
                  fill="oklch(0.55 0.15 195)"
                  radius={[6, 6, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty-state">
              <div className="empty-state-icon">
                <Briefcase aria-hidden="true" />
              </div>
              <p className="empty-state-title">No jobs created yet</p>
              <p className="empty-state-description">
                Department distribution will appear here once you create your first job opening.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
