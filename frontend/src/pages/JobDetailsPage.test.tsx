import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, act, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { JobDetailsPage } from './JobDetailsPage'
import { jobsApi } from '@/lib/api'
import type { Job } from '@/lib/api'

// Mock the API
vi.mock('@/lib/api', () => ({
  jobsApi: {
    getJob: vi.fn(),
    closeJob: vi.fn(),
    archiveJob: vi.fn(),
  }
}))

// Mock the auth context to avoid AuthProvider requirement
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({
    user: { role: 'admin' },
    isAuthenticated: true,
  })
}))

// Mock react-router-dom useParams
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useParams: () => ({ id: '1' }),
    useNavigate: () => vi.fn(),
  }
})

const mockedJobsApi = jobsApi as {
  getJob: any
  closeJob: any
  archiveJob: any
}

const renderWithRouter = (component: React.ReactElement) => {
  return render(<BrowserRouter>{component}</BrowserRouter>)
}

const mockJob: Job = {
  id: 1,
  title: 'Senior Software Engineer',
  department: 'Engineering',
  description: 'We are looking for a senior software engineer to join our team.',
  location: 'San Francisco, CA',
  work_mode: 'remote',
  employment_type: 'full-time',
  min_experience: 3,
  max_experience: 8,
  education_requirement: 'bachelor',
  salary_min: 120000,
  salary_max: 180000,
  status: 'active',
  weight_skills: 30,
  weight_experience: 25,
  weight_education: 15,
  weight_projects: 20,
  weight_certs: 10,
  required_skills: ['JavaScript', 'React', 'Node.js'],
  preferred_skills: ['TypeScript', 'GraphQL'],
  required_certs: ['AWS Certified Solutions Architect'],
  preferred_certs: [],
  applicant_count: 12,
  archived_at: null,
  created_at: '2024-01-15T10:00:00Z',
  updated_at: '2024-01-15T10:00:00Z'
}

describe('JobDetailsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Loading States', () => {
    it('shows loading state while fetching job', async () => {
      mockedJobsApi.getJob.mockImplementation(() => new Promise(() => {}))
      
      await act(async () => {
        renderWithRouter(<JobDetailsPage />)
      })
      
      // Should show loading spinner
      expect(document.querySelector('.lucide-loader-circle')).toBeInTheDocument()
    })
  })

  describe('Job Display', () => {
    beforeEach(() => {
      mockedJobsApi.getJob.mockResolvedValue(mockJob)
    })

    it('displays job title and department', async () => {
      await act(async () => {
        renderWithRouter(<JobDetailsPage />)
      })
      
      await waitFor(() => {
        expect(screen.getByText('Senior Software Engineer')).toBeInTheDocument()
        expect(screen.getByText('Engineering')).toBeInTheDocument()
      })
    })

    it('displays action buttons for authorized users', async () => {
      await act(async () => {
        renderWithRouter(<JobDetailsPage />)
      })
      
      await waitFor(() => {
        expect(screen.getByRole('button', { name: 'Edit Job' })).toBeInTheDocument()
      })
    })
  })

  describe('Error States', () => {
    it('handles job not found error', async () => {
      const error = new Error('Job not found')
      ;(error as any).response = { status: 404 }
      mockedJobsApi.getJob.mockRejectedValue(error)
      
      await act(async () => {
        renderWithRouter(<JobDetailsPage />)
      })
      
      await waitFor(() => {
        // Look for any instance of "Job not found" text
        expect(screen.getAllByText('Job not found').length).toBeGreaterThan(0)
      })
    })

    it('handles general API errors with retry', async () => {
      mockedJobsApi.getJob.mockRejectedValue(new Error('API Error'))
      
      await act(async () => {
        renderWithRouter(<JobDetailsPage />)
      })
      
      await waitFor(() => {
        // Look for the actual error message shown in the component
        expect(screen.getByText('Unable to load job. Please check your connection and try again.')).toBeInTheDocument()
      })
    })
  })

  describe('Navigation', () => {
    beforeEach(() => {
      mockedJobsApi.getJob.mockResolvedValue(mockJob)
    })

    it('has back to jobs button', async () => {
      await act(async () => {
        renderWithRouter(<JobDetailsPage />)
      })
      
      await waitFor(() => {
        expect(screen.getByRole('button', { name: 'Back to Jobs' })).toBeInTheDocument()
      })
    })
  })
})