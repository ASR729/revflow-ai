import { Metadata } from 'next';
import { EventDetailPage } from '@/components/event-detail';

export const metadata: Metadata = {
  title: 'Event Detail - RevFlow',
  description: 'Event Detail - RevFlow AI Revenue Recovery',
};

export default function Page({ params }: { params: { event_id: string } }) {
  return <EventDetailPage eventId={params.event_id} />;
}