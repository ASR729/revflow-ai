import { Metadata } from 'next';
import { ConfigPage } from '@/components/config';

export const metadata: Metadata = {
  title: 'Configuration - RevFlow',
  description: 'Configuration - RevFlow AI Revenue Recovery',
};

export default function Page() {
  return <ConfigPage />;
}