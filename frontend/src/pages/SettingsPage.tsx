import { useEffect, useState } from 'react';
import { Settings, Shield } from 'lucide-react';
import { toast } from 'sonner';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import apiClient from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';

interface SystemSetting {
  key: string;
  value: string;
}

export function SettingsPage() {
  const { user } = useAuth();
  const [anonymousScreening, setAnonymousScreening] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const response = await apiClient.get<{ items: SystemSetting[] }>('/settings/');
        const items = response.data.items;
        const anonSetting = items.find((s) => s.key === 'anonymous_screening');
        setAnonymousScreening(anonSetting?.value === 'true');
      } catch {
        // Settings may not exist yet — default to off
        setAnonymousScreening(false);
      } finally {
        setIsLoading(false);
      }
    };

    void fetchSettings();
  }, []);

  const handleToggle = async (checked: boolean) => {
    setIsSaving(true);
    try {
      await apiClient.put('/settings/anonymous_screening', { value: checked ? 'true' : 'false' });
      setAnonymousScreening(checked);
      toast.success(`Anonymous screening ${checked ? 'enabled' : 'disabled'}.`);
    } catch {
      toast.error('Failed to update setting.');
    } finally {
      setIsSaving(false);
    }
  };

  if (user?.role !== 'admin') {
    return (
      <div className="page-frame">
        <p className="text-destructive">Access denied. Admin role required.</p>
      </div>
    );
  }

  return (
    <div className="page-frame">
      <section className="management-toolbar" aria-labelledby="settings-heading">
        <div>
          <p className="page-label">Administration</p>
          <h1 id="settings-heading" className="page-heading">Settings</h1>
          <p className="page-heading-copy">Manage global system configuration.</p>
        </div>
        <Settings aria-hidden="true" size={24} className="text-primary" />
      </section>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield size={18} aria-hidden="true" />
            Privacy & Screening
          </CardTitle>
          <CardDescription>
            Configure privacy controls for the recruitment process.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="anonymous-screening">Anonymous Screening Mode</Label>
              <p className="text-sm text-muted-foreground">
                When enabled, candidate names, emails, phone numbers, and personal URLs are hidden
                from recruiters in all views and exports. Original resume downloads are blocked.
              </p>
            </div>
            <Switch
              id="anonymous-screening"
              checked={anonymousScreening}
              onCheckedChange={(checked) => void handleToggle(checked)}
              disabled={isLoading || isSaving}
              aria-describedby="anonymous-screening-desc"
            />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
