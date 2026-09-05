import { Metadata } from 'next';
import { SettingsPage } from '@/components/settings';

export const metadata: Metadata = {
  title: 'Settings - RevFlow',
  description: 'Settings - RevFlow AI Revenue Recovery',
};

export default function Page() {
  return <SettingsPage />;
}