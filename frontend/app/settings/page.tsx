import type { Metadata } from 'next';
import { SettingsScreen } from '@/components/screens/settings';

export const metadata: Metadata = {
  title: 'Settings — RevFlow AI',
  description: 'Environment settings (read-only)',
};

export default function Page() {
  return <SettingsScreen />;
}
