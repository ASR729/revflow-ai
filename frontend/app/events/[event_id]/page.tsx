import type { Metadata } from 'next';
import { EventDetailScreen } from '@/components/screens/event-detail';

export const metadata: Metadata = {
  title: 'Event Detail — RevFlow AI',
  description: 'Event decision detail',
};

export default function Page({ params }: { params: { event_id: string } }) {
  return <EventDetailScreen eventId={params.event_id} />;
}
