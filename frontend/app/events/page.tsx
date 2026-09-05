import { Metadata } from 'next';
import { EventsPage } from '@/components/events';

export const metadata: Metadata = {
  title: 'Events - RevFlow',
  description: 'Events - RevFlow AI Revenue Recovery',
};

export default function Page() {
  return <EventsPage />;
}