import { useState } from 'react';
import { LogOut, LoaderCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';

export function LogoutButton() {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const handleLogout = async () => {
    setIsLoggingOut(true);
    try {
      await logout();
    } finally {
      navigate('/login', { replace: true });
      setIsLoggingOut(false);
    }
  };

  return (
    <Button variant="secondary" onClick={handleLogout} disabled={isLoggingOut} className="gap-2" aria-label={isLoggingOut ? 'Logging out' : 'Log out'}>
      {isLoggingOut ? <LoaderCircle className="animate-spin" aria-hidden="true" /> : <LogOut aria-hidden="true" />}
      <span className="desktop-only">{isLoggingOut ? 'Logging out' : 'Log out'}</span>
    </Button>
  );
}
