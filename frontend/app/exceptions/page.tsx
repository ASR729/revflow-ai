import type { Metadata } from 'next';
import { ExceptionsScreen } from '@/components/screens/exceptions';

export const metadata: Metadata = {
  title: 'Exceptions — RevFlow AI',
  description: 'Withheld and escalated events',
};

export default function Page() {
  return <ExceptionsScreen />;
}
