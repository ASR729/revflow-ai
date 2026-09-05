import type { Metadata } from 'next';
import { OverviewScreen } from '@/components/screens/overview';

export const metadata: Metadata = {
  title: 'Overview — RevFlow AI',
  description: 'RevFlow AI overview',
};

export default function Page() {
  return <OverviewScreen />;
}
