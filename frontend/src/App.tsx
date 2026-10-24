import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider } from '@/contexts/AuthContext';
import { UserManagement } from '@/components/admin/UserManagement';
import { AppLayout } from '@/components/layout/AppLayout';
import { ProtectedRoute } from '@/components/layout/ProtectedRoute';
import { UnauthorizedPage } from '@/components/layout/UnauthorizedPage';
import { AuditLogPage } from '@/pages/AuditLogPage';
import { CandidateComparePage } from '@/pages/CandidateComparePage';
import { CandidatesPage } from '@/pages/CandidatesPage';
import { DashboardPage } from '@/pages/DashboardPage';
import { JobDetailsPage } from '@/pages/JobDetailsPage';
import { JobFormPage } from '@/pages/JobFormPage';
import { JobsPage } from '@/pages/JobsPage';
import { LoginPage } from '@/pages/LoginPage';
import { SettingsPage } from '@/pages/SettingsPage';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/unauthorized" element={<UnauthorizedPage />} />
          <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/jobs" element={<JobsPage />} />
            <Route path="/jobs/new" element={<JobFormPage />} />
            <Route path="/jobs/:id" element={<JobDetailsPage />} />
            <Route path="/jobs/:id/edit" element={<JobFormPage isEdit={true} />} />
            <Route path="/candidates" element={<CandidatesPage />} />
            <Route path="/candidates/compare" element={<CandidateComparePage />} />
            <Route path="/settings" element={<ProtectedRoute allowedRoles={['admin']}><SettingsPage /></ProtectedRoute>} />
            <Route path="/audit" element={<ProtectedRoute allowedRoles={['admin']}><AuditLogPage /></ProtectedRoute>} />
            <Route path="/users" element={<ProtectedRoute allowedRoles={['admin']}><UserManagement /></ProtectedRoute>} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
