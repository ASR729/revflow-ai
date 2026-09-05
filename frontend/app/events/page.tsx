import type { Metadata } from 'next';
import { EventsScreen } from '@/components/screens/events';

export const metadata: Metadata = {
  title: 'Events — RevFlow AI',
  description: 'Processed events',
};

export default function Page() {
  return <EventsScreen />;
}
