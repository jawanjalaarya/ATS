import { useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import apiClient from '@/lib/api';

interface InterviewModalProps {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
  applicationId: number;
  candidateId: number;
  jobId: number;
}

interface GeneratedQuestions {
  questions: string[];
}

export function InterviewModal({
  open,
  onClose,
  onCreated,
  applicationId,
  candidateId,
  jobId,
}: InterviewModalProps) {
  const [interviewerName, setInterviewerName] = useState('');
  const [interviewerEmail, setInterviewerEmail] = useState('');
  const [scheduledAt, setScheduledAt] = useState('');
  const [duration, setDuration] = useState('60');
  const [location, setLocation] = useState('');
  const [questions, setQuestions] = useState<string[]>([]);
  const [questionsText, setQuestionsText] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);

  const handleGenerateQuestions = async (interviewId: number) => {
    setIsGenerating(true);
    try {
      const response = await apiClient.post<{ questions: string[] }>(
        `/interviews/${interviewId}/generate-questions`
      );
      const generated = response.data.questions || [];
      setQuestions(generated);
      setQuestionsText(generated.join('\n\n'));
      toast.success(`Generated ${generated.length} interview questions.`);
    } catch {
      toast.error('Failed to generate questions.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSubmit = async () => {
    if (!interviewerName || !scheduledAt) {
      toast.error('Interviewer name and scheduled time are required.');
      return;
    }

    setIsSubmitting(true);
    try {
      // Parse edited questions from textarea (D-07)
      const finalQuestions = questionsText
        .split('\n')
        .map((q) => q.trim())
        .filter((q) => q.length > 0);

      const response = await apiClient.post('/interviews/', {
        application_id: applicationId,
        candidate_id: candidateId,
        job_id: jobId,
        interviewer_name: interviewerName,
        interviewer_email: interviewerEmail || undefined,
        scheduled_at: new Date(scheduledAt).toISOString(),
        duration_minutes: parseInt(duration, 10),
        location: location || undefined,
        questions: finalQuestions,
      });

      // If no questions were provided upfront, generate them now
      if (finalQuestions.length === 0 && response.data) {
        await handleGenerateQuestions((response.data as { id: number }).id);
      }

      toast.success('Interview scheduled successfully.');
      onCreated();
      onClose();
    } catch {
      toast.error('Failed to schedule interview.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <DialogContent className="sm:max-w-[560px] max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Schedule Interview</DialogTitle>
          <DialogDescription>
            Schedule an interview and generate tailored questions based on the candidate's skills.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="interviewer-name">Interviewer Name *</Label>
              <Input
                id="interviewer-name"
                value={interviewerName}
                onChange={(e) => setInterviewerName(e.target.value)}
                placeholder="Jane Smith"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="interviewer-email">Interviewer Email</Label>
              <Input
                id="interviewer-email"
                type="email"
                value={interviewerEmail}
                onChange={(e) => setInterviewerEmail(e.target.value)}
                placeholder="jane@company.com"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="scheduled-at">Date & Time *</Label>
              <Input
                id="scheduled-at"
                type="datetime-local"
                value={scheduledAt}
                onChange={(e) => setScheduledAt(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="duration">Duration (minutes)</Label>
              <Input
                id="duration"
                type="number"
                min="15"
                max="480"
                value={duration}
                onChange={(e) => setDuration(e.target.value)}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="location">Location / Meeting Link</Label>
            <Input
              id="location"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="Conference Room B or https://meet.example.com/..."
            />
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="questions">Interview Questions (D-07: editable)</Label>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => void handleGenerateQuestions(0)}
                disabled={isGenerating}
              >
                {isGenerating ? 'Generating…' : 'Auto-Generate'}
              </Button>
            </div>
            <Textarea
              id="questions"
              value={questionsText}
              onChange={(e) => setQuestionsText(e.target.value)}
              placeholder="Questions will appear here after generation. You can edit them freely before saving."
              rows={8}
              className="font-mono text-sm"
            />
            <p className="text-xs text-muted-foreground">
              One question per line. Generated questions are based on candidate skills and job requirements.
            </p>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button onClick={() => void handleSubmit()} disabled={isSubmitting}>
            {isSubmitting ? 'Scheduling…' : 'Schedule Interview'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
