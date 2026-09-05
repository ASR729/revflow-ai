import { Metadata } from 'next';
import { WebhookPage } from '@/components/webhook';

export const metadata: Metadata = {
  title: 'Webhook - RevFlow',
  description: 'Webhook - RevFlow AI Revenue Recovery',
};

export default function Page() {
  return <WebhookPage />;
}