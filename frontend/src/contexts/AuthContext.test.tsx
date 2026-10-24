import React from 'react';
import { render, screen, act, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { AuthProvider, useAuth } from './AuthContext';
import { authApi } from '@/lib/api';

// Mock authApi
vi.mock('@/lib/api', () => ({
  authApi: {
    getCurrentUser: vi.fn(),
    login: vi.fn(),
    logout: vi.fn()
  }
}));

// Test component to access context
const TestComponent = () => {
  const { user, isAuthenticated, isLoading, login, logout } = useAuth();
  
  if (isLoading) return <div>Loading...</div>;
  
  return (
    <div>
      <div data-testid="auth-status">{isAuthenticated ? 'Auth: Yes' : 'Auth: No'}</div>
      {user && <div data-testid="user-email">{user.email}</div>}
      <button onClick={() => login({ email: 'test@example.com', password: 'password123' }).catch(() => {})}>Login</button>
      <button onClick={logout}>Logout</button>
    </div>
  );
};

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('test_auth_context_provides_initial_state', async () => {
    // me() fails so user is not authenticated
    (authApi.getCurrentUser as any).mockRejectedValue(new Error('Unauthorized'));
    
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );
    
    // Initially isLoading might be true
    expect(screen.getByText('Loading...')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Auth: No');
    });
  });

  it('test_login_success_updates_state', async () => {
    (authApi.getCurrentUser as any).mockRejectedValueOnce(new Error('Unauthorized'));
    const mockUser = { id: 1, email: 'test@example.com', role: 'admin' };
    (authApi.getCurrentUser as any).mockResolvedValue(mockUser);
    (authApi.login as any).mockResolvedValue(mockUser);
    
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );
    
    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Auth: No');
    });
    
    act(() => {
      screen.getByText('Login').click();
    });
    
    await waitFor(() => {
      expect(authApi.login).toHaveBeenCalledWith({ email: 'test@example.com', password: 'password123' });
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Auth: Yes');
      expect(screen.getByTestId('user-email')).toHaveTextContent('test@example.com');
    });
  });

  it('test_login_failure_handles_error', async () => {
    (authApi.getCurrentUser as any).mockRejectedValue(new Error('Unauthorized'));
    (authApi.login as any).mockRejectedValue(new Error('Invalid credentials'));
    
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );
    
    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Auth: No');
    });
    
    act(() => {
      screen.getByText('Login').click();
    });
    
    // It should throw or just not update the state. Since the Error is uncaught in TestComponent,
    // let's just assert that auth status remains 'Auth: No'
    await waitFor(() => {
      expect(authApi.login).toHaveBeenCalled();
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Auth: No');
    });
  });

  it('test_logout_clears_state', async () => {
    const mockUser = { id: 1, email: 'test@example.com', role: 'admin' };
    // Start authenticated
    (authApi.getCurrentUser as any).mockResolvedValue(mockUser);
    (authApi.logout as any).mockResolvedValue({});
    
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );
    
    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Auth: Yes');
    });
    
    act(() => {
      screen.getByText('Logout').click();
    });
    
    await waitFor(() => {
      expect(authApi.logout).toHaveBeenCalled();
      expect(screen.getByTestId('auth-status')).toHaveTextContent('Auth: No');
    });
  });

  it('test_loading_states', async () => {
    // Delay me() to check loading state
    (authApi.getCurrentUser as any).mockImplementation(() => new Promise(resolve => setTimeout(() => resolve({ id: 1 }), 100)));
    
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );
    
    expect(screen.getByText('Loading...')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
    });
  });
});

describe('useAuth', () => {
  it('test_auth_context_throws_outside_provider', () => {
    // To suppress console.error from React about the thrown error
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    
    expect(() => render(<TestComponent />)).toThrow('useAuth must be used within an AuthProvider');
    
    consoleSpy.mockRestore();
  });
});
