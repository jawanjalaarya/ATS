import * as React from 'react';
import { LoaderCircle } from 'lucide-react';
import { toast } from 'sonner';
import { candidatesApi, type Candidate, type CandidateUpdate } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { TagInput } from '@/components/jobs/TagInput';

interface CandidateEditFormProps {
  candidate: Candidate;
  onSave: (updated: Candidate) => void;
  onCancel: () => void;
}

export function CandidateEditForm({ candidate, onSave, onCancel }: CandidateEditFormProps) {
  const [isSaving, setIsSaving] = React.useState(false);
  const [name, setName] = React.useState(candidate.name || '');
  const [email, setEmail] = React.useState(candidate.email || '');
  const [phone, setPhone] = React.useState(candidate.phone || '');
  const [location, setLocation] = React.useState(candidate.location || '');
  const [linkedinUrl, setLinkedinUrl] = React.useState(candidate.linkedin_url || '');
  const [githubUrl, setGithubUrl] = React.useState(candidate.github_url || '');
  const [portfolioUrl, setPortfolioUrl] = React.useState(candidate.portfolio_url || '');
  const [skills, setSkills] = React.useState<string[]>(candidate.skills || []);
  const [education, setEducation] = React.useState(
    candidate.education?.map((e) => JSON.stringify(e)).join('\n') || ''
  );
  const [experience, setExperience] = React.useState(
    candidate.experience?.map((e) => JSON.stringify(e)).join('\n') || ''
  );
  const [projects, setProjects] = React.useState(
    candidate.projects?.map((p) => JSON.stringify(p)).join('\n') || ''
  );
  const [certifications, setCertifications] = React.useState(
    candidate.certifications?.join('\n') || ''
  );

  // Track which fields were originally null/empty for warning border
  const wasEmpty = React.useMemo(() => ({
    name: !candidate.name,
    email: !candidate.email,
    phone: !candidate.phone,
    location: !candidate.location,
    linkedin_url: !candidate.linkedin_url,
    github_url: !candidate.github_url,
    portfolio_url: !candidate.portfolio_url,
    skills: !candidate.skills || candidate.skills.length === 0,
    education: !candidate.education || candidate.education.length === 0,
    experience: !candidate.experience || candidate.experience.length === 0,
    projects: !candidate.projects || candidate.projects.length === 0,
    certifications: !candidate.certifications || candidate.certifications.length === 0,
  }), [candidate]);

  const warningBorder = 'border-l-[3px] border-l-[oklch(0.53_0.12_78)] pl-3';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);

    try {
      const updateData: CandidateUpdate = {
        name: name || undefined,
        email: email || undefined,
        phone: phone || undefined,
        location: location || undefined,
        linkedin_url: linkedinUrl || undefined,
        github_url: githubUrl || undefined,
        portfolio_url: portfolioUrl || undefined,
        skills,
        certifications: certifications ? certifications.split('\n').filter(Boolean) : undefined,
      };

      // Parse structured fields back from JSON lines
      if (education.trim()) {
        try {
          updateData.education = education.split('\n').filter(Boolean).map((line) => JSON.parse(line));
        } catch {
          updateData.education = education.split('\n').filter(Boolean).map((line) => ({ text: line }));
        }
      }
      if (experience.trim()) {
        try {
          updateData.experience = experience.split('\n').filter(Boolean).map((line) => JSON.parse(line));
        } catch {
          updateData.experience = experience.split('\n').filter(Boolean).map((line) => ({ text: line }));
        }
      }
      if (projects.trim()) {
        try {
          updateData.projects = projects.split('\n').filter(Boolean).map((line) => JSON.parse(line));
        } catch {
          updateData.projects = projects.split('\n').filter(Boolean).map((line) => ({ text: line }));
        }
      }

      // Mark as complete once reviewed
      updateData.status = 'complete';

      const updated = await candidatesApi.updateCandidate(candidate.id, updateData);
      onSave(updated);
    } catch {
      toast.error('Unable to save candidate profile. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <form onSubmit={(e) => void handleSubmit(e)} className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold">Review Candidate Profile</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Some fields could not be parsed automatically. Please verify and complete.
        </p>
      </div>

      {/* Contact fields - two-column grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className={wasEmpty.name ? warningBorder : ''}>
          <Label htmlFor="candidate-name">Name</Label>
          <Input
            id="candidate-name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Full name"
          />
        </div>
        <div className={wasEmpty.email ? warningBorder : ''}>
          <Label htmlFor="candidate-email">Email</Label>
          <Input
            id="candidate-email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="email@example.com"
          />
        </div>
        <div className={wasEmpty.phone ? warningBorder : ''}>
          <Label htmlFor="candidate-phone">Phone</Label>
          <Input
            id="candidate-phone"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            placeholder="+1 (555) 000-0000"
          />
        </div>
        <div className={wasEmpty.location ? warningBorder : ''}>
          <Label htmlFor="candidate-location">Location</Label>
          <Input
            id="candidate-location"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="City, State"
          />
        </div>
      </div>

      {/* Links */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className={wasEmpty.linkedin_url ? warningBorder : ''}>
          <Label htmlFor="candidate-linkedin">LinkedIn</Label>
          <Input
            id="candidate-linkedin"
            value={linkedinUrl}
            onChange={(e) => setLinkedinUrl(e.target.value)}
            placeholder="https://linkedin.com/in/..."
          />
        </div>
        <div className={wasEmpty.github_url ? warningBorder : ''}>
          <Label htmlFor="candidate-github">GitHub</Label>
          <Input
            id="candidate-github"
            value={githubUrl}
            onChange={(e) => setGithubUrl(e.target.value)}
            placeholder="https://github.com/..."
          />
        </div>
        <div className={`md:col-span-2 ${wasEmpty.portfolio_url ? warningBorder : ''}`}>
          <Label htmlFor="candidate-portfolio">Portfolio</Label>
          <Input
            id="candidate-portfolio"
            value={portfolioUrl}
            onChange={(e) => setPortfolioUrl(e.target.value)}
            placeholder="https://portfolio.example.com"
          />
        </div>
      </div>

      {/* Skills */}
      <div className={wasEmpty.skills ? warningBorder : ''}>
        <TagInput
          label="Skills"
          values={skills}
          onChange={setSkills}
          placeholder="Type a skill and press Enter..."
        />
      </div>

      {/* Summary fields */}
      <div className="grid grid-cols-1 gap-4">
        <div className={wasEmpty.education ? warningBorder : ''}>
          <Label htmlFor="candidate-education">Education</Label>
          <Textarea
            id="candidate-education"
            value={education}
            onChange={(e) => setEducation(e.target.value)}
            placeholder="One entry per line"
            rows={3}
          />
        </div>
        <div className={wasEmpty.experience ? warningBorder : ''}>
          <Label htmlFor="candidate-experience">Experience</Label>
          <Textarea
            id="candidate-experience"
            value={experience}
            onChange={(e) => setExperience(e.target.value)}
            placeholder="One entry per line"
            rows={3}
          />
        </div>
        <div className={wasEmpty.projects ? warningBorder : ''}>
          <Label htmlFor="candidate-projects">Projects</Label>
          <Textarea
            id="candidate-projects"
            value={projects}
            onChange={(e) => setProjects(e.target.value)}
            placeholder="One entry per line"
            rows={3}
          />
        </div>
        <div className={wasEmpty.certifications ? warningBorder : ''}>
          <Label htmlFor="candidate-certifications">Certifications</Label>
          <Textarea
            id="candidate-certifications"
            value={certifications}
            onChange={(e) => setCertifications(e.target.value)}
            placeholder="One certification per line"
            rows={2}
          />
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-end gap-3 pt-4 border-t">
        <Button type="button" variant="outline" onClick={onCancel} disabled={isSaving}>
          Cancel
        </Button>
        <Button type="submit" disabled={isSaving}>
          {isSaving && <LoaderCircle className="animate-spin" aria-hidden="true" />}
          {isSaving ? 'Saving…' : 'Save Profile'}
        </Button>
      </div>
    </form>
  );
}
