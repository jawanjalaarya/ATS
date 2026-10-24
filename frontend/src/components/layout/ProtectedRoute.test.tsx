import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { ProtectedRoute } from './ProtectedRoute';
import * as AuthContextModule from '@/contexts/AuthContext';

// Mock the useAuth hook
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

const mockUseAuth = AuthContextModule.useAuth as ReturnType<typeof vi.fn>;

describe('ProtectedRoute', () => {
  const TestChild = () => <div data-testid="test-child">Protected Content</div>;
  const LoginPage = () => <div data-testid="login-page">Login Page</div>;
  const UnauthorizedPage = () => <div data-testid="unauthorized-page">Unauthorized Page</div>;

  const renderWithRouter = (ui: React.ReactElement, initialRoute = '/protected') => {
    return render(
      <MemoryRouter initialEntries={[initialRoute]}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/unauthorized" element={<UnauthorizedPage />} />
          <Route path="/protected" element={ui} />
        </Routes>
      </MemoryRouter>
    );
  };

  it('test_shows_loading_spinner_when_isLoading_is_true', () => {
    mockUseAuth.mockReturnValue({
      isLoading: true,
      isAuthenticated: false,
      user: null,
    });

    renderWithRouter(
      <ProtectedRoute>
        <TestChild />
      </ProtectedRoute>
    );

    expect(screen.getByText(/Loading.../i)).toBeInTheDocument();
    expect(screen.queryByTestId('test-child')).not.toBeInTheDocument();
  });

  it('test_redirects_to_login_when_not_authenticated', () => {
    mockUseAuth.mockReturnValue({
      isLoading: false,
      isAuthenticated: false,
      user: null,
    });

    renderWithRouter(
      <ProtectedRoute>
        <TestChild />
      </ProtectedRoute>
    );

    expect(screen.getByTestId('login-page')).toBeInTheDocument();
    expect(screen.queryByTestId('test-child')).not.toBeInTheDocument();
  });

  it('test_renders_children_when_authenticated', () => {
    mockUseAuth.mockReturnValue({
      isLoading: false,
      isAuthenticated: true,
      user: { id: 1, role: 'recruiter' },
    });

    renderWithRouter(
      <ProtectedRoute>
        <TestChild />
      </ProtectedRoute>
    );

    expect(screen.getByTestId('test-child')).toBeInTheDocument();
  });

  it('test_redirects_to_unauthorized_when_role_not_allowed', () => {
    mockUseAuth.mockReturnValue({
      isLoading: false,
      isAuthenticated: true,
      user: { id: 1, role: 'recruiter' },
    });

    renderWithRouter(
      <ProtectedRoute allowedRoles={['admin']}>
        <TestChild />
      </ProtectedRoute>
    );

    expect(screen.getByTestId('unauthorized-page')).toBeInTheDocument();
    expect(screen.queryByTestId('test-child')).not.toBeInTheDocument();
  });

  it('test_admin_can_access_any_route', () => {
    mockUseAuth.mockReturnValue({
      isLoading: false,
      isAuthenticated: true,
      user: { id: 1, role: 'admin' },
    });

    renderWithRouter(
      <ProtectedRoute allowedRoles={['recruiter']}>
        <TestChild />
      </ProtectedRoute>
    );

    // Admin should bypass the role check based on the implementation
    expect(screen.getByTestId('test-child')).toBeInTheDocument();
    expect(screen.queryByTestId('unauthorized-page')).not.toBeInTheDocument();
  });
});
