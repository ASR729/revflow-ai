import { Metadata } from 'next';
import { AuditPage } from '@/components/audit';

export const metadata: Metadata = {
  title: 'Audit Trail - RevFlow',
  description: 'Audit Trail - RevFlow AI Revenue Recovery',
};

export default function Page() {
  return <AuditPage />;
}