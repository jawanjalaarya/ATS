import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { LoaderCircle, ArrowLeft } from 'lucide-react';
import * as z from 'zod';
import { jobsApi, type Job, type JobCreate, type JobUpdate } from '@/lib/api';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { TagInput } from '@/components/jobs/TagInput';

interface JobFormPageProps {
  isEdit?: boolean;
}

const jobFormSchema = z.object({
  title: z.string().min(1, 'Title is required').max(100, 'Title must be 100 characters or less'),
  department: z.string().min(1, 'Department is required'),
  description: z.string().min(1, 'Description is required'),
  location: z.string().min(1, 'Location is required'),
  work_mode: z.enum(['remote', 'hybrid', 'on-site']),
  employment_type: z.enum(['full-time', 'part-time', 'contract', 'internship']),
  min_experience: z.number().min(0, 'Minimum experience must be 0 or greater'),
  max_experience: z.number().min(0, 'Maximum experience must be 0 or greater'),
  education_requirement: z.enum(['high_school', 'associate', 'bachelor', 'master', 'phd', 'none']),
  salary_min: z.number().min(0, 'Minimum salary must be 0 or greater').optional(),
  salary_max: z.number().min(0, 'Maximum salary must be 0 or greater').optional(),
  status: z.enum(['draft', 'active', 'paused', 'closed']),
  weight_skills: z.number().min(0, 'Weight must be between 0 and 100').max(100, 'Weight must be between 0 and 100'),
  weight_experience: z.number().min(0, 'Weight must be between 0 and 100').max(100, 'Weight must be between 0 and 100'),
  weight_education: z.number().min(0, 'Weight must be between 0 and 100').max(100, 'Weight must be between 0 and 100'),
  weight_projects: z.number().min(0, 'Weight must be between 0 and 100').max(100, 'Weight must be between 0 and 100'),
  weight_certs: z.number().min(0, 'Weight must be between 0 and 100').max(100, 'Weight must be between 0 and 100'),
  required_skills: z.array(z.string()),
  preferred_skills: z.array(z.string()),
  required_certs: z.array(z.string()),
  preferred_certs: z.array(z.string()),
}).refine((data) => {
  return data.min_experience <= data.max_experience;
}, {
  message: 'Minimum experience must be less than or equal to maximum experience',
  path: ['max_experience'],
}).refine((data) => {
  if (data.salary_min && data.salary_max) {
    return data.salary_min <= data.salary_max;
  }
  return true;
}, {
  message: 'Minimum salary must be less than or equal to maximum salary',
  path: ['salary_max'],
}).refine((data) => {
  if (data.status === 'active') {
    const total = data.weight_skills + data.weight_experience + data.weight_education + data.weight_projects + data.weight_certs;
    return total === 100;
  }
  return true;
}, {
  message: 'Active jobs must have weights totaling exactly 100%',
  path: ['weight_skills'], // Show error on first weight field
});

type JobFormValues = z.infer<typeof jobFormSchema>;

export function JobFormPage({ isEdit = false }: JobFormPageProps) {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [_job, setJob] = useState<Job | null>(null);
  const [isLoading, setIsLoading] = useState(isEdit);
  const [error, setError] = useState<string | null>(null);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    reset,
    formState: { errors, isSubmitting, isDirty },
  } = useForm<JobFormValues>({
    resolver: zodResolver(jobFormSchema),
    defaultValues: {
      title: '',
      department: '',
      description: '',
      location: '',
      work_mode: 'remote',
      employment_type: 'full-time',
      min_experience: 0,
      max_experience: 0,
      education_requirement: 'none',
      salary_min: undefined,
      salary_max: undefined,
      status: 'draft',
      weight_skills: 20,
      weight_experience: 20,
      weight_education: 20,
      weight_projects: 20,
      weight_certs: 20,
      required_skills: [],
      preferred_skills: [],
      required_certs: [],
      preferred_certs: [],
    },
  });

  const watchedWeights = watch(['weight_skills', 'weight_experience', 'weight_education', 'weight_projects', 'weight_certs']);
  const watchedStatus = watch('status');
  const totalWeights = watchedWeights.reduce((sum, weight) => sum + (weight || 0), 0);

  // Load job data if editing
  useEffect(() => {
    if (isEdit && id) {
      const fetchJob = async () => {
        setIsLoading(true);
        setError(null);
        try {
          const jobData = await jobsApi.getJob(parseInt(id, 10));
          setJob(jobData);
          
          // Reset form with job data
          reset({
            title: jobData.title,
            department: jobData.department,
            description: jobData.description,
            location: jobData.location,
            work_mode: jobData.work_mode,
            employment_type: jobData.employment_type,
            min_experience: jobData.min_experience,
            max_experience: jobData.max_experience,
            education_requirement: jobData.education_requirement,
            salary_min: jobData.salary_min || undefined,
            salary_max: jobData.salary_max || undefined,
            status: jobData.status,
            weight_skills: jobData.weight_skills,
            weight_experience: jobData.weight_experience,
            weight_education: jobData.weight_education,
            weight_projects: jobData.weight_projects,
            weight_certs: jobData.weight_certs,
            required_skills: jobData.required_skills,
            preferred_skills: jobData.preferred_skills,
            required_certs: jobData.required_certs,
            preferred_certs: jobData.preferred_certs,
          });
        } catch {
          setError('Unable to load job. The job may not exist or you may not have permission to view it.');
        } finally {
          setIsLoading(false);
        }
      };
      
      void fetchJob();
    }
  }, [isEdit, id, reset]);

  // Track unsaved changes
  useEffect(() => {
    setHasUnsavedChanges(isDirty);
  }, [isDirty]);

  // Warn before leaving with unsaved changes
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (hasUnsavedChanges) {
        e.preventDefault();
        e.returnValue = '';
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [hasUnsavedChanges]);

  const onSubmit = async (data: JobFormValues) => {
    setError(null);
    try {
      if (isEdit && id) {
        const updateData: JobUpdate = {
          title: data.title,
          department: data.department,
          description: data.description,
          location: data.location,
          work_mode: data.work_mode,
          employment_type: data.employment_type,
          min_experience: Math.round(data.min_experience),
          max_experience: Math.round(data.max_experience),
          education_requirement: data.education_requirement,
          status: data.status,
          weight_skills: Math.round(data.weight_skills),
          weight_experience: Math.round(data.weight_experience),
          weight_education: Math.round(data.weight_education),
          weight_projects: Math.round(data.weight_projects),
          weight_certs: Math.round(data.weight_certs),
          required_skills: data.required_skills,
          preferred_skills: data.preferred_skills,
          required_certs: data.required_certs,
          preferred_certs: data.preferred_certs,
        };
        // Only include salary fields if they have values
        if (data.salary_min) updateData.salary_min = Math.round(data.salary_min);
        if (data.salary_max) updateData.salary_max = Math.round(data.salary_max);
        
        await jobsApi.updateJob(parseInt(id, 10), updateData);
      } else {
        const createData: JobCreate = {
          title: data.title,
          department: data.department,
          description: data.description,
          location: data.location,
          work_mode: data.work_mode,
          employment_type: data.employment_type,
          min_experience: Math.round(data.min_experience),
          max_experience: Math.round(data.max_experience),
          education_requirement: data.education_requirement,
          status: data.status,
          weight_skills: Math.round(data.weight_skills),
          weight_experience: Math.round(data.weight_experience),
          weight_education: Math.round(data.weight_education),
          weight_projects: Math.round(data.weight_projects),
          weight_certs: Math.round(data.weight_certs),
          required_skills: data.required_skills,
          preferred_skills: data.preferred_skills,
          required_certs: data.required_certs,
          preferred_certs: data.preferred_certs,
        };
        // Only include salary fields if they have values
        if (data.salary_min) createData.salary_min = Math.round(data.salary_min);
        if (data.salary_max) createData.salary_max = Math.round(data.salary_max);
        
        await jobsApi.createJob(createData);
      }
      
      setHasUnsavedChanges(false);
      navigate('/jobs');
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail 
        || err.response?.data?.message 
        || err.message 
        || 'Unable to save job. Please check your entries and try again.';
      
      // Log the full error for debugging
      console.error('Job save error:', err.response?.data || err.message || err);
      
      setError(errorMessage);
    }
  };

  const handleCancel = () => {
    if (hasUnsavedChanges) {
      if (confirm('You have unsaved changes. Are you sure you want to leave?')) {
        navigate('/jobs');
      }
    } else {
      navigate('/jobs');
    }
  };

  const getWeightValidationClass = () => {
    if (watchedStatus === 'active' && totalWeights !== 100) {
      return 'text-destructive';
    }
    return totalWeights === 100 ? 'text-success' : 'text-muted-foreground';
  };

  const getWeightValidationMessage = () => {
    if (watchedStatus === 'active' && totalWeights !== 100) {
      return 'Active jobs must have weights totaling exactly 100%';
    }
    return null;
  };

  if (isLoading) {
    return (
      <div className="page-frame">
        <div className="flex items-center justify-center min-h-96">
          <LoaderCircle className="animate-spin" size={32} />
        </div>
      </div>
    );
  }

  return (
    <div className="page-frame">
      <section className="management-toolbar">
        <div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate('/jobs')}
            className="mb-2 -ml-2"
          >
            <ArrowLeft size={16} />
            Back to Jobs
          </Button>
          <p className="page-label">Recruitment</p>
          <h1 className="page-heading">{isEdit ? 'Edit Job' : 'Create Job'}</h1>
          <p className="page-heading-copy">
            {isEdit ? 'Update job details and requirements.' : 'Create a new job opening to attract candidates.'}
          </p>
        </div>
      </section>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Card>
        <CardContent className="p-6">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
            {/* Basic Information Section */}
            <div className="space-y-4">
              <h2 className="text-lg font-semibold">Basic Information</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="form-field">
                  <Label htmlFor="title">Job Title *</Label>
                  <Input
                    id="title"
                    {...register('title')}
                    aria-invalid={Boolean(errors.title)}
                    maxLength={100}
                  />
                  {errors.title && <p className="form-error">{errors.title.message}</p>}
                </div>

                <div className="form-field">
                  <Label htmlFor="department">Department *</Label>
                  <Input
                    id="department"
                    {...register('department')}
                    aria-invalid={Boolean(errors.department)}
                  />
                  {errors.department && <p className="form-error">{errors.department.message}</p>}
                </div>
              </div>

              <div className="form-field">
                <Label htmlFor="description">Job Description *</Label>
                <Textarea
                  id="description"
                  {...register('description')}
                  aria-invalid={Boolean(errors.description)}
                  rows={5}
                  placeholder="Describe the role, responsibilities, and requirements..."
                />
                {errors.description && <p className="form-error">{errors.description.message}</p>}
              </div>

              <div className="form-field">
                <Label htmlFor="location">Location *</Label>
                <Input
                  id="location"
                  {...register('location')}
                  aria-invalid={Boolean(errors.location)}
                  placeholder="e.g., San Francisco, CA or Remote"
                />
                {errors.location && <p className="form-error">{errors.location.message}</p>}
              </div>
            </div>

            {/* Position Details Section */}
            <div className="space-y-4">
              <h2 className="text-lg font-semibold">Position Details</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="form-field">
                  <Label htmlFor="work_mode">Work Mode</Label>
                  <Select
                    onValueChange={(value) => setValue('work_mode', value as any, { shouldValidate: true })}
                    defaultValue={watch('work_mode')}
                  >
                    <SelectTrigger id="work_mode">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="remote">Remote</SelectItem>
                      <SelectItem value="hybrid">Hybrid</SelectItem>
                      <SelectItem value="on-site">On-site</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="form-field">
                  <Label htmlFor="employment_type">Employment Type</Label>
                  <Select
                    onValueChange={(value) => setValue('employment_type', value as any, { shouldValidate: true })}
                    defaultValue={watch('employment_type')}
                  >
                    <SelectTrigger id="employment_type">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="full-time">Full-time</SelectItem>
                      <SelectItem value="part-time">Part-time</SelectItem>
                      <SelectItem value="contract">Contract</SelectItem>
                      <SelectItem value="internship">Internship</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="form-field">
                  <Label htmlFor="min_experience">Minimum Experience (years)</Label>
                  <Input
                    id="min_experience"
                    type="number"
                    min="0"
                    max="50"
                    {...register('min_experience', { valueAsNumber: true })}
                    aria-invalid={Boolean(errors.min_experience)}
                  />
                  {errors.min_experience && <p className="form-error">{errors.min_experience.message}</p>}
                </div>

                <div className="form-field">
                  <Label htmlFor="max_experience">Maximum Experience (years)</Label>
                  <Input
                    id="max_experience"
                    type="number"
                    min="0"
                    max="50"
                    {...register('max_experience', { valueAsNumber: true })}
                    aria-invalid={Boolean(errors.max_experience)}
                  />
                  {errors.max_experience && <p className="form-error">{errors.max_experience.message}</p>}
                </div>
              </div>

              <div className="form-field">
                <Label htmlFor="education_requirement">Education Requirement</Label>
                <Select
                  onValueChange={(value) => setValue('education_requirement', value as any, { shouldValidate: true })}
                  defaultValue={watch('education_requirement')}
                >
                  <SelectTrigger id="education_requirement">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">No requirement</SelectItem>
                    <SelectItem value="high_school">High School</SelectItem>
                    <SelectItem value="associate">Associate Degree</SelectItem>
                    <SelectItem value="bachelor">Bachelor's Degree</SelectItem>
                    <SelectItem value="master">Master's Degree</SelectItem>
                    <SelectItem value="phd">PhD</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="form-field">
                  <Label htmlFor="salary_min">Minimum Salary (optional)</Label>
                  <Input
                    id="salary_min"
                    type="number"
                    min="0"
                    {...register('salary_min', { valueAsNumber: true })}
                    aria-invalid={Boolean(errors.salary_min)}
                    placeholder="e.g., 75000"
                  />
                  {errors.salary_min && <p className="form-error">{errors.salary_min.message}</p>}
                </div>

                <div className="form-field">
                  <Label htmlFor="salary_max">Maximum Salary (optional)</Label>
                  <Input
                    id="salary_max"
                    type="number"
                    min="0"
                    {...register('salary_max', { valueAsNumber: true })}
                    aria-invalid={Boolean(errors.salary_max)}
                    placeholder="e.g., 125000"
                  />
                  {errors.salary_max && <p className="form-error">{errors.salary_max.message}</p>}
                </div>
              </div>
            </div>

            {/* Screening Weights Section */}
            <div className="space-y-4">
              <div>
                <h2 className="text-lg font-semibold">Screening Weights</h2>
                <p className="text-sm text-muted-foreground mt-1">
                  Configure how different criteria are weighted when screening candidates.
                </p>
                <div className={`text-sm font-medium mt-2 ${getWeightValidationClass()}`}>
                  Total: {totalWeights}% {totalWeights === 100 ? '✓' : ''}
                </div>
                {getWeightValidationMessage() && (
                  <p className="text-sm text-destructive mt-1">{getWeightValidationMessage()}</p>
                )}
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div className="form-field">
                  <Label htmlFor="weight_skills">Skills (%)</Label>
                  <Input
                    id="weight_skills"
                    type="number"
                    min="0"
                    max="100"
                    {...register('weight_skills', { valueAsNumber: true })}
                    aria-invalid={Boolean(errors.weight_skills)}
                  />
                  {errors.weight_skills && <p className="form-error">{errors.weight_skills.message}</p>}
                </div>

                <div className="form-field">
                  <Label htmlFor="weight_experience">Experience (%)</Label>
                  <Input
                    id="weight_experience"
                    type="number"
                    min="0"
                    max="100"
                    {...register('weight_experience', { valueAsNumber: true })}
                    aria-invalid={Boolean(errors.weight_experience)}
                  />
                  {errors.weight_experience && <p className="form-error">{errors.weight_experience.message}</p>}
                </div>

                <div className="form-field">
                  <Label htmlFor="weight_education">Education (%)</Label>
                  <Input
                    id="weight_education"
                    type="number"
                    min="0"
                    max="100"
                    {...register('weight_education', { valueAsNumber: true })}
                    aria-invalid={Boolean(errors.weight_education)}
                  />
                  {errors.weight_education && <p className="form-error">{errors.weight_education.message}</p>}
                </div>

                <div className="form-field">
                  <Label htmlFor="weight_projects">Projects (%)</Label>
                  <Input
                    id="weight_projects"
                    type="number"
                    min="0"
                    max="100"
                    {...register('weight_projects', { valueAsNumber: true })}
                    aria-invalid={Boolean(errors.weight_projects)}
                  />
                  {errors.weight_projects && <p className="form-error">{errors.weight_projects.message}</p>}
                </div>

                <div className="form-field">
                  <Label htmlFor="weight_certs">Certifications (%)</Label>
                  <Input
                    id="weight_certs"
                    type="number"
                    min="0"
                    max="100"
                    {...register('weight_certs', { valueAsNumber: true })}
                    aria-invalid={Boolean(errors.weight_certs)}
                  />
                  {errors.weight_certs && <p className="form-error">{errors.weight_certs.message}</p>}
                </div>
              </div>
            </div>

            {/* Skills & Certifications Section */}
            <div className="space-y-4">
              <h2 className="text-lg font-semibold">Skills & Certifications</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <TagInput
                  label="Required Skills"
                  values={watch('required_skills')}
                  onChange={(values) => setValue('required_skills', values, { shouldValidate: true })}
                  placeholder="Type skill and press Enter"
                />

                <TagInput
                  label="Preferred Skills"
                  values={watch('preferred_skills')}
                  onChange={(values) => setValue('preferred_skills', values, { shouldValidate: true })}
                  placeholder="Type skill and press Enter"
                />

                <TagInput
                  label="Required Certifications"
                  values={watch('required_certs')}
                  onChange={(values) => setValue('required_certs', values, { shouldValidate: true })}
                  placeholder="Type certification and press Enter"
                />

                <TagInput
                  label="Preferred Certifications"
                  values={watch('preferred_certs')}
                  onChange={(values) => setValue('preferred_certs', values, { shouldValidate: true })}
                  placeholder="Type certification and press Enter"
                />
              </div>
            </div>

            {/* Status & Actions Section */}
            <div className="space-y-4">
              <h2 className="text-lg font-semibold">Status & Actions</h2>
              
              <div className="form-field">
                <Label htmlFor="status">Job Status</Label>
                <Select
                  onValueChange={(value) => setValue('status', value as any, { shouldValidate: true })}
                  defaultValue={watch('status')}
                >
                  <SelectTrigger id="status">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="draft">Draft</SelectItem>
                    <SelectItem value="active">Active</SelectItem>
                    <SelectItem value="paused">Paused</SelectItem>
                    <SelectItem value="closed">Closed</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="flex gap-3 pt-4">
                <Button type="button" variant="outline" onClick={handleCancel} disabled={isSubmitting}>
                  Cancel
                </Button>
                <Button type="submit" disabled={isSubmitting}>
                  {isSubmitting && <LoaderCircle className="animate-spin" aria-hidden="true" />}
                  {isSubmitting ? 'Saving...' : (isEdit ? 'Save Changes' : 'Create Job')}
                </Button>
              </div>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}