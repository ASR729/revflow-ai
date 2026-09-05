import { Metadata } from 'next';
import { Dashboard } from '@/components/dashboard';

export const metadata: Metadata = {
  title: 'RevFlow - AI Revenue Recovery',
  description: 'AI-Powered Revenue Recovery Orchestration',
};

export default function Page() {
  return <Dashboard />;
}