import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { JobFormPage } from './JobFormPage'
import { jobsApi } from '@/lib/api'

// Mock the API
vi.mock('@/lib/api', () => ({
  jobsApi: {
    getJob: vi.fn(),
    createJob: vi.fn(),
    updateJob: vi.fn(),
  }
}))

const renderWithRouter = (component: React.ReactElement) => {
  return render(<BrowserRouter>{component}</BrowserRouter>)
}

describe('JobFormPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Basic Rendering', () => {
    it('renders form fields correctly', () => {
      act(() => {
        renderWithRouter(<JobFormPage />)
      })
      
      expect(screen.getByLabelText('Job Title *')).toBeInTheDocument()
      expect(screen.getByLabelText('Department *')).toBeInTheDocument()
      expect(screen.getByLabelText('Job Description *')).toBeInTheDocument()
      expect(screen.getByLabelText('Location *')).toBeInTheDocument()
      expect(screen.getByRole('heading', { name: 'Create Job' })).toBeInTheDocument()
    })
  })

  describe('Weight Controls', () => {
    it('shows five numeric weight inputs', () => {
      act(() => {
        renderWithRouter(<JobFormPage />)
      })
      
      // Verify all five weight controls exist
      expect(screen.getByLabelText('Skills (%)')).toBeInTheDocument()
      expect(screen.getByLabelText('Experience (%)')).toBeInTheDocument()
      expect(screen.getByLabelText('Education (%)')).toBeInTheDocument()
      expect(screen.getByLabelText('Projects (%)')).toBeInTheDocument()
      expect(screen.getByLabelText('Certifications (%)')).toBeInTheDocument()
      
      // Verify they are number inputs (not sliders)
      const skillsInput = screen.getByLabelText('Skills (%)')
      expect(skillsInput).toHaveAttribute('type', 'number')
    })

    it('shows live weight sum display', () => {
      act(() => {
        renderWithRouter(<JobFormPage />)
      })
      
      // Should show current total (default 100%)
      expect(screen.getByText(/Total: 100%/)).toBeInTheDocument()
    })
  })

  describe('Form Fields', () => {
    it('has salary fields with correct labels', () => {
      act(() => {
        renderWithRouter(<JobFormPage />)
      })
      
      expect(screen.getByLabelText('Minimum Salary (optional)')).toBeInTheDocument()
      expect(screen.getByLabelText('Maximum Salary (optional)')).toBeInTheDocument()
    })

    it('has experience range fields', () => {
      act(() => {
        renderWithRouter(<JobFormPage />)
      })
      
      expect(screen.getByLabelText('Minimum Experience (years)')).toBeInTheDocument()
      expect(screen.getByLabelText('Maximum Experience (years)')).toBeInTheDocument()
    })

    it('has all required select fields', () => {
      act(() => {
        renderWithRouter(<JobFormPage />)
      })
      
      expect(screen.getByLabelText('Work Mode')).toBeInTheDocument()
      expect(screen.getByLabelText('Employment Type')).toBeInTheDocument()
      expect(screen.getByLabelText('Education Requirement')).toBeInTheDocument()
    })
  })

  describe('Tag Inputs', () => {
    it('renders skills and certifications sections', () => {
      act(() => {
        renderWithRouter(<JobFormPage />)
      })
      
      // Check that there are skill input sections
      expect(screen.getByText('Required Skills')).toBeInTheDocument()
      expect(screen.getByText('Preferred Skills')).toBeInTheDocument()
      expect(screen.getByText('Required Certifications')).toBeInTheDocument()
      expect(screen.getByText('Preferred Certifications')).toBeInTheDocument()
    })
  })

  describe('Navigation', () => {
    it('has back to jobs button', () => {
      act(() => {
        renderWithRouter(<JobFormPage />)
      })
      
      expect(screen.getByRole('button', { name: 'Back to Jobs' })).toBeInTheDocument()
    })

    it('has submit button', () => {
      act(() => {
        renderWithRouter(<JobFormPage />)
      })
      
      expect(screen.getByRole('button', { name: 'Create Job' })).toBeInTheDocument()
    })
  })

  describe('Loading States', () => {
    it('shows loading state in edit mode', async () => {
      // Mock a pending promise to show loading state
      const mockedJobsApi = jobsApi as any
      mockedJobsApi.getJob.mockImplementation(() => new Promise(() => {}))
      
      await act(async () => {
        renderWithRouter(<JobFormPage isEdit={true} />)
      })
      
      // Should show loading spinner (lucide-loader-circle class)
      expect(document.querySelector('.lucide-loader-circle')).toBeInTheDocument()
    })
  })
})