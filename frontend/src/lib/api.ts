import axios, { AxiosError, InternalAxiosRequestConfig, AxiosResponse } from 'axios';

// TypeScript interfaces for API schemas

export interface User {
  id: number;
  email: string;
  role: 'admin' | 'recruiter';
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface UserLogin {
  email: string;
  password: string;
}

export interface UserCreate {
  email: string;
  password: string;
  role: 'admin' | 'recruiter';
  is_active?: boolean;
}

export interface UserUpdate {
  email?: string;
  role?: 'admin' | 'recruiter';
  is_active?: boolean;
}

// Job interfaces matching backend JobResponse schema exactly
export interface Job {
  id: number;
  title: string;
  department: string;
  description: string;
  location: string;
  work_mode: 'remote' | 'hybrid' | 'on-site';
  employment_type: 'full-time' | 'part-time' | 'contract' | 'internship';
  min_experience: number;
  max_experience: number;
  education_requirement: 'high_school' | 'associate' | 'bachelor' | 'master' | 'phd' | 'none';
  salary_min?: number;
  salary_max?: number;
  status: 'draft' | 'active' | 'paused' | 'closed';
  weight_skills: number;
  weight_experience: number;
  weight_education: number;
  weight_projects: number;
  weight_certs: number;
  required_skills: string[];
  preferred_skills: string[];
  required_certs: string[];
  preferred_certs: string[];
  created_at: string;
  updated_at: string;
  archived_at?: string | null;
  applicant_count: number;
}

export interface JobCreate {
  title: string;
  department: string;
  description: string;
  location: string;
  work_mode: 'remote' | 'hybrid' | 'on-site';
  employment_type: 'full-time' | 'part-time' | 'contract' | 'internship';
  min_experience: number;
  max_experience: number;
  education_requirement?: 'high_school' | 'associate' | 'bachelor' | 'master' | 'phd' | 'none';
  salary_min?: number;
  salary_max?: number;
  status?: 'draft' | 'active' | 'paused' | 'closed';
  weight_skills?: number;
  weight_experience?: number;
  weight_education?: number;
  weight_projects?: number;
  weight_certs?: number;
  required_skills?: string[];
  preferred_skills?: string[];
  required_certs?: string[];
  preferred_certs?: string[];
}

export interface JobUpdate {
  title?: string;
  department?: string;
  description?: string;
  location?: string;
  work_mode?: 'remote' | 'hybrid' | 'on-site';
  employment_type?: 'full-time' | 'part-time' | 'contract' | 'internship';
  min_experience?: number;
  max_experience?: number;
  education_requirement?: 'high_school' | 'associate' | 'bachelor' | 'master' | 'phd' | 'none';
  salary_min?: number;
  salary_max?: number;
  status?: 'draft' | 'active' | 'paused' | 'closed';
  weight_skills?: number;
  weight_experience?: number;
  weight_education?: number;
  weight_projects?: number;
  weight_certs?: number;
  required_skills?: string[];
  preferred_skills?: string[];
  required_certs?: string[];
  preferred_certs?: string[];
}

export interface JobListResponse {
  items: Job[];
  total: number;
}

// Candidate interfaces matching backend CandidateResponse schema
export interface Candidate {
  id: number;
  name: string | null;
  email: string | null;
  phone: string | null;
  location: string | null;
  linkedin_url: string | null;
  github_url: string | null;
  portfolio_url: string | null;
  skills: string[];
  education: Record<string, unknown>[];
  experience: Record<string, unknown>[];
  projects: Record<string, unknown>[];
  certifications: string[];
  achievements: string[];
  resume_path: string | null;
  original_filename: string | null;
  status: 'complete' | 'pending_review';
  created_at: string;
  updated_at: string;
}

export interface CandidateUpdate {
  name?: string;
  email?: string;
  phone?: string;
  location?: string;
  linkedin_url?: string;
  github_url?: string;
  portfolio_url?: string;
  skills?: string[];
  education?: Record<string, unknown>[];
  experience?: Record<string, unknown>[];
  projects?: Record<string, unknown>[];
  certifications?: string[];
  achievements?: string[];
  status?: string;
}

export interface CandidateListResponse {
  items: Candidate[];
  total: number;
}

// Screening interfaces matching backend schemas
export interface DimensionBreakdown {
  required_matched?: string[];
  required_missing?: string[];
  preferred_matched?: string[];
  preferred_missing?: string[];
  candidate_years?: number;
  required_min?: number;
  required_max?: number;
  meets_minimum?: boolean;
  candidate_level?: string;
  required_level?: string;
  meets_requirement?: boolean;
  matched_keywords?: string[];
  missing_keywords?: string[];
  total_keywords?: number;
  raw_cosine?: number;
  scaled_score?: number;
  omitted?: boolean;
  reason?: string;
}

export interface ScreeningBreakdown {
  skills?: DimensionBreakdown;
  experience?: DimensionBreakdown;
  education?: DimensionBreakdown;
  projects?: DimensionBreakdown;
  certifications?: DimensionBreakdown;
  semantic?: DimensionBreakdown;
}

export interface ScreeningResult {
  id: number;
  application_id: number;
  overall_score: number | null;
  skills_score: number | null;
  experience_score: number | null;
  education_score: number | null;
  projects_score: number | null;
  certification_score: number | null;
  semantic_score: number | null;
  explanation: ScreeningBreakdown | null;
  created_at: string | null;
}

export interface UploadResult {
  filename: string;
  status: 'success' | 'error';
  candidate: Candidate | null;
  error: string | null;
}

// Create configured Axios instance
const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // We can add consistent logic here, e.g., logging or other headers
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error: AxiosError) => {
    if (error.response && error.response.status === 401) {
      // Avoid infinite loop if we are already on login or checking auth
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// Auth endpoints
export const authApi = {
  login: async (credentials: UserLogin) => {
    const response = await apiClient.post<{ message: string; role: string }>('/auth/login', credentials);
    return response.data;
  },
  
  logout: async () => {
    const response = await apiClient.post<{ message: string }>('/auth/logout');
    return response.data;
  },
  
  getCurrentUser: async () => {
    const response = await apiClient.get<User>('/auth/me');
    return response.data;
  }
};

// User management endpoints
export const usersApi = {
  getUsers: async (skip: number = 0, limit: number = 100) => {
    const response = await apiClient.get<User[]>(`/users/?skip=${skip}&limit=${limit}`);
    return response.data;
  },
  
  createUser: async (userData: UserCreate) => {
    const response = await apiClient.post<User>('/users/', userData);
    return response.data;
  },
  
  updateUser: async (userId: number, userData: UserUpdate) => {
    const response = await apiClient.patch<User>(`/users/${userId}`, userData);
    return response.data;
  },
  
  toggleUserActive: async (userId: number) => {
    const response = await apiClient.patch<User>(`/users/${userId}/disable`);
    return response.data;
  }
};

// Jobs API endpoints
export const jobsApi = {
  getJobs: async (
    skip?: number,
    limit?: number, 
    status?: string,
    include_archived?: boolean
  ): Promise<JobListResponse> => {
    const params = new URLSearchParams();
    if (skip !== undefined) params.append('skip', skip.toString());
    if (limit !== undefined) params.append('limit', limit.toString());
    if (status) params.append('status', status);
    if (include_archived) params.append('include_archived', 'true');
    
    const response = await apiClient.get<JobListResponse>(`/jobs/?${params.toString()}`);
    return response.data;
  },

  getJob: async (id: number): Promise<Job> => {
    const response = await apiClient.get<Job>(`/jobs/${id}`);
    return response.data;
  },

  createJob: async (data: JobCreate): Promise<Job> => {
    const response = await apiClient.post<Job>('/jobs/', data);
    return response.data;
  },

  updateJob: async (id: number, data: JobUpdate): Promise<Job> => {
    const response = await apiClient.patch<Job>(`/jobs/${id}`, data);
    return response.data;
  },

  closeJob: async (id: number): Promise<Job> => {
    const response = await apiClient.patch<Job>(`/jobs/${id}/close`);
    return response.data;
  },

  archiveJob: async (id: number): Promise<Job> => {
    const response = await apiClient.patch<Job>(`/jobs/${id}/archive`);
    return response.data;
  },

  restoreJob: async (id: number): Promise<Job> => {
    const response = await apiClient.patch<Job>(`/jobs/${id}/restore`);
    return response.data;
  }
};

// Candidates API endpoints
export const candidatesApi = {
  getCandidates: async (
    skip: number = 0,
    limit: number = 100,
    status?: string,
    search?: string,
    sortBy?: string,
    sortOrder?: string,
    skills?: string,
    location?: string
  ): Promise<CandidateListResponse> => {
    const params = new URLSearchParams();
    params.append('skip', skip.toString());
    params.append('limit', limit.toString());
    if (status) params.append('status', status);
    if (search) params.append('search', search);
    if (sortBy) params.append('sort_by', sortBy);
    if (sortOrder) params.append('sort_order', sortOrder);
    if (skills) params.append('skills', skills);
    if (location) params.append('location', location);
    const response = await apiClient.get<CandidateListResponse>(`/candidates/?${params.toString()}`);
    return response.data;
  },

  getCandidate: async (id: number): Promise<Candidate> => {
    const response = await apiClient.get<Candidate>(`/candidates/${id}`);
    return response.data;
  },

  updateCandidate: async (id: number, data: CandidateUpdate): Promise<Candidate> => {
    const response = await apiClient.patch<Candidate>(`/candidates/${id}`, data);
    return response.data;
  },

  deleteCandidate: async (id: number): Promise<void> => {
    await apiClient.delete(`/candidates/${id}`);
  },

  uploadResume: async (
    file: File,
    jobId?: number,
    onUploadProgress?: (progress: number) => void
  ): Promise<Candidate> => {
    const formData = new FormData();
    formData.append('file', file);
    if (jobId) formData.append('job_id', jobId.toString());
    const response = await apiClient.post<Candidate>('/candidates/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onUploadProgress) {
          onUploadProgress(Math.round((progressEvent.loaded * 100) / progressEvent.total));
        }
      },
    });
    return response.data;
  },

  downloadResume: (id: number): string => {
    return `${apiClient.defaults.baseURL}/candidates/${id}/resume`;
  },

  triggerScreening: async (candidateId: number, jobId: number): Promise<ScreeningResult> => {
    const response = await apiClient.post<ScreeningResult>(
      `/candidates/${candidateId}/screen/${jobId}`
    );
    return response.data;
  },

  getScreeningResult: async (candidateId: number, jobId: number): Promise<ScreeningResult> => {
    const response = await apiClient.get<ScreeningResult>(
      `/candidates/${candidateId}/screening/${jobId}`
    );
    return response.data;
  },
};

export default apiClient;
