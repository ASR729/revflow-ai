import type { Metadata } from 'next';
import { ConfigScreen } from '@/components/screens/config';

export const metadata: Metadata = {
  title: 'Configuration — RevFlow AI',
  description: 'Policy configuration (read-only)',
};

export default function Page() {
  return <ConfigScreen />;
}
