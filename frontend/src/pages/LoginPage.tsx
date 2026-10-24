import { BadgeCheck, LockKeyhole, ShieldCheck } from 'lucide-react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { LoginForm } from '@/components/auth/LoginForm';

export function LoginPage() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="app-loader" aria-label="Checking your session">
        <div className="app-loader-mark" aria-hidden="true" />
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="login-page">
      <aside className="login-context">
        <div>
          <div className="sidebar-brand">
            <div className="brand-mark" aria-hidden="true">ATS</div>
            <div>
              <span className="brand-name">Etechstreamers Technologies</span>
              <span className="brand-context">Recruitment Operations</span>
            </div>
          </div>
          <h1 className="login-context-title">Hiring work, handled with confidence.</h1>
          <p className="login-context-copy">
            A focused workspace for the people responsible for thoughtful, defensible recruitment decisions.
          </p>
          <ul className="login-principles">
            <li><ShieldCheck aria-hidden="true" /> Role-based access</li>
            <li><LockKeyhole aria-hidden="true" /> Protected candidate information</li>
            <li><BadgeCheck aria-hidden="true" /> Accountable recruitment operations</li>
          </ul>
        </div>
        <p className="login-context-footer">Internal recruitment platform · Authorized users only</p>
      </aside>

      <main className="login-main">
        <div className="login-form-wrap">
          <p className="login-security-note"><LockKeyhole aria-hidden="true" /> Secure sign-in</p>
          <LoginForm />
        </div>
      </main>
    </div>
  );
}
