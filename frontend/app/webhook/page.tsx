import type { Metadata } from 'next';
import { WebhookScreen } from '@/components/screens/webhook';

export const metadata: Metadata = {
  title: 'Webhook — RevFlow AI',
  description: 'Single-event ingestion',
};

export default function Page() {
  return <WebhookScreen />;
}
