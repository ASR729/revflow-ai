import { Metadata } from 'next';
import { ExceptionsPage } from '@/components/exceptions';

export const metadata: Metadata = {
  title: 'Exceptions - RevFlow',
  description: 'Exceptions - RevFlow AI Revenue Recovery',
};

export default function Page() {
  return <ExceptionsPage />;
}