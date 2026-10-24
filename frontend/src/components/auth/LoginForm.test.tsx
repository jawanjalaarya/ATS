import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { LoginForm } from './LoginForm';

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

import { useAuth } from '@/contexts/AuthContext';

describe('LoginForm', () => {
  const mockLogin = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (useAuth as ReturnType<typeof vi.fn>).mockReturnValue({
      login: mockLogin,
      isAuthenticated: false,
      isLoading: false,
    });
  });

  it('renders the workspace sign-in form', () => {
    render(<LoginForm />);
    expect(screen.getByRole('heading', { name: /Sign in to your workspace/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/Email address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^Password$/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^Log In$/i })).toBeInTheDocument();
  });

  it('shows validation errors for an empty submission', async () => {
    render(<LoginForm />);
    fireEvent.click(screen.getByRole('button', { name: /^Log In$/i }));

    await waitFor(() => {
      expect(screen.getByText(/Invalid email address/i)).toBeInTheDocument();
      expect(screen.getByText(/Password is required/i)).toBeInTheDocument();
    });
    expect(mockLogin).not.toHaveBeenCalled();
  });

  it('rejects an invalid email address', async () => {
    render(<LoginForm />);
    fireEvent.change(screen.getByLabelText(/Email address/i), { target: { value: 'not-an-email' } });
    fireEvent.change(screen.getByLabelText(/^Password$/i), { target: { value: 'password123' } });
    fireEvent.click(screen.getByRole('button', { name: /^Log In$/i }));

    await waitFor(() => expect(screen.getByText(/Invalid email address/i)).toBeInTheDocument());
    expect(mockLogin).not.toHaveBeenCalled();
  });

  it('submits valid credentials', async () => {
    render(<LoginForm />);
    fireEvent.change(screen.getByLabelText(/Email address/i), { target: { value: 'test@example.com' } });
    fireEvent.change(screen.getByLabelText(/^Password$/i), { target: { value: 'password123' } });
    fireEvent.click(screen.getByRole('button', { name: /^Log In$/i }));

    await waitFor(() => expect(mockLogin).toHaveBeenCalledWith({ email: 'test@example.com', password: 'password123' }));
  });

  it('shows the approved authentication error message', async () => {
    mockLogin.mockRejectedValue(new Error('Auth failed'));
    render(<LoginForm />);
    fireEvent.change(screen.getByLabelText(/Email address/i), { target: { value: 'test@example.com' } });
    fireEvent.change(screen.getByLabelText(/^Password$/i), { target: { value: 'password123' } });
    fireEvent.click(screen.getByRole('button', { name: /^Log In$/i }));

    await waitFor(() => {
      expect(screen.getByText('Failed to authenticate. Check your email and password and try again.')).toBeInTheDocument();
    });
  });

  it('disables the primary action while authentication is pending', async () => {
    mockLogin.mockImplementation(() => new Promise((resolve) => setTimeout(resolve, 100)));
    render(<LoginForm />);
    fireEvent.change(screen.getByLabelText(/Email address/i), { target: { value: 'test@example.com' } });
    fireEvent.change(screen.getByLabelText(/^Password$/i), { target: { value: 'password123' } });
    fireEvent.click(screen.getByRole('button', { name: /^Log In$/i }));

    expect(screen.getByRole('button', { name: /Logging in/i })).toBeDisabled();
    await waitFor(() => expect(screen.getByRole('button', { name: /^Log In$/i })).not.toBeDisabled());
  });

  it('toggles password visibility with an accessible control', () => {
    render(<LoginForm />);
    const passwordInput = screen.getByLabelText(/^Password$/i);

    expect(passwordInput).toHaveAttribute('type', 'password');
    fireEvent.click(screen.getByRole('button', { name: /Show password/i }));
    expect(passwordInput).toHaveAttribute('type', 'text');
    fireEvent.click(screen.getByRole('button', { name: /Hide password/i }));
    expect(passwordInput).toHaveAttribute('type', 'password');
  });
});
