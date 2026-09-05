import type { Metadata } from 'next';
import { AuditScreen } from '@/components/screens/audit';

export const metadata: Metadata = {
  title: 'Audit Trail — RevFlow AI',
  description: 'Decision audit trail',
};

export default function Page() {
  return <AuditScreen />;
}
