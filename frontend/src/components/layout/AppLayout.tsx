import { Link, Outlet, useLocation } from 'react-router-dom';
import { LayoutDashboard, ShieldCheck, UsersRound, Briefcase, Users } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { LogoutButton } from '@/components/auth/LogoutButton';

const navigation = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/jobs', label: 'Jobs', icon: Briefcase },
  { to: '/candidates', label: 'Candidates', icon: Users },
  { to: '/users', label: 'User management', icon: UsersRound, adminOnly: true },
];

export function AppLayout() {
  const { user } = useAuth();
  const location = useLocation();
  const currentItem = navigation.find((item) => item.to === location.pathname);
  const visibleNavigation = navigation.filter((item) => !item.adminOnly || user?.role === 'admin');
  const accountName = user?.email?.split('@')[0] ?? 'Account';

  return (
    <div className="app-shell">
      <aside className="app-sidebar" aria-label="Primary navigation">
        <div className="sidebar-brand">
          <div className="brand-mark" aria-hidden="true">ATS</div>
          <div>
            <span className="brand-name">ATS System</span>
            <span className="brand-context">Recruitment operations</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          <p className="sidebar-section-label">Workspace</p>
          {visibleNavigation.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.to;
            return (
              <Link
                key={item.to}
                to={item.to}
                className={`side-nav-link${isActive ? ' is-active' : ''}`}
                aria-current={isActive ? 'page' : undefined}
              >
                <Icon aria-hidden="true" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="sidebar-footer">
          <ShieldCheck aria-hidden="true" size={16} />
          <div>
            <strong>Private workspace</strong>
            <span>Role-based access is active.</span>
          </div>
        </div>
      </aside>

      <div className="app-content">
        <header className="workspace-header">
          <div>
            <p className="workspace-crumb">Recruitment operations</p>
            <p className="workspace-title">{currentItem?.label ?? 'Workspace'}</p>
          </div>
          <div className="workspace-user">
            <div className="user-identity desktop-only">
              <p className="user-email">{user?.email ?? 'Signed-in user'}</p>
              <p className="user-role">{user?.role ?? 'member'}</p>
            </div>
            <div className="user-avatar" aria-label={`Signed in as ${accountName}`}>
              {accountName.slice(0, 1).toUpperCase()}
            </div>
            <LogoutButton />
          </div>
        </header>

        <nav className="mobile-nav" aria-label="Mobile navigation">
          {visibleNavigation.map((item) => {
            const isActive = location.pathname === item.to;
            return (
              <Link
                key={item.to}
                to={item.to}
                className={isActive ? 'is-active' : ''}
                aria-current={isActive ? 'page' : undefined}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        <main className="page-frame">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
