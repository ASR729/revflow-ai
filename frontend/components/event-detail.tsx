'use client';

import { useState, useEffect } from 'react';

function LoadingState() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Event Detail</h1>
          <p className="text-text-secondary mt-1">Loading event details...</p>
        </div>
      </div>
      <div className="card p-8 text-center">
        <div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        <p className="text-text-secondary">Loading event details...</p>
      </div>
    </div>
  );
}

function ErrorState() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-text-primary">Event Detail</h1>
        <p className="text-text-secondary mt-1">Event details</p>
      </div>
      <div className="card p-6 text-center text-danger-600">
        Failed to load event details
      </div>
    </div>
  );
}

function NotFoundState() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-text-primary">Event Detail</h1>
        <p className="text-text-secondary mt-1">Event details</p>
      </div>
      <div className="card p-6 text-center text-danger-600">
        Event not found
      </div>
    </div>
  );
}

interface EventDetailPageProps {
  eventId: string;
}

export function EventDetailPage({ eventId }: EventDetailPageProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setTimeout(() => {
      setLoading(false);
    }, 1000);
  }, [eventId]);

  if (loading) {
    return <LoadingState />;
  }

  if (error) {
    return <ErrorState />;
  }

  return <NotFoundState />;
}