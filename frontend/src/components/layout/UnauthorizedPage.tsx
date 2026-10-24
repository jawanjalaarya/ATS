import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export function UnauthorizedPage() {
  const navigate = useNavigate();

  return (
    <div className="flex items-center justify-center min-h-screen bg-background p-4">
      <Card className="w-full max-w-[500px]">
        <CardHeader>
          <CardTitle className="text-destructive text-2xl">Access Denied</CardTitle>
          <CardDescription>
            You do not have the required permissions to view this page.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-6">
          <p className="text-muted-foreground">
            This area is restricted to administrators or users with specific roles. If you believe you should have access, please contact your system administrator.
          </p>
          <Button onClick={() => navigate('/')} className="self-start">
            Return to Dashboard
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
