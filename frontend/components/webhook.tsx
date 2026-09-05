'use client';

import { useState } from 'react';

interface FormProps {
  loading: boolean;
  payload: string;
  setPayload: (v: string) => void;
  handleSubmit: (e: React.FormEvent) => void;
}

function Header() {
  return (
    <div>
      <h1 className="text-2xl font-bold text-text-primary">Webhook</h1>
      <p className="text-text-secondary mt-1">Single-event ingestion from Razorpay webhook</p>
    </div>
  );
}

function FormComponent({ loading, payload, setPayload, handleSubmit }: FormProps) {
  return (
    <div className="card p-6">
      <h2 className="text-lg font-semibold text-text-primary mb-4">Send Test Webhook</h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-text-secondary mb-2">Webhook Payload (JSON)</label>
          <textarea
            value={payload}
            onChange={(e) => setPayload(e.target.value)}
            className="input font-mono text-sm"
            rows={15}
            placeholder='{"event": "payment.captured", "payload": { "payment": { "entity": { "id": "pay_xxx", "amount": 50000, "currency": "INR", "status": "captured" } } }}'
          />
          <p className="text-sm text-text-muted mt-1">Enter a valid Razorpay webhook payload in JSON format</p>
        </div>
        <div className="flex gap-3">
          <button type="submit" disabled={loading} className="btn-primary">
            {loading ? 'Sending...' : 'Send Webhook'}
          </button>
          <button type="button" onClick={() => setPayload('test')} className="btn-secondary">
            Load Sample
          </button>
        </div>
      </form>
    </div>
  );
}

function ErrorDisplay({ error }: { error: string }) {
  return (
    <div className="card p-4 bg-danger-50 border-danger-200 text-danger-700">
      <strong>Error:</strong> {error}
    </div>
  );
}

function ResultDisplay({ result }: { result: any }) {
  return (
    <div className="card p-6 mt-4">
      <h3 className="text-lg font-semibold text-text-primary mb-4">Response</h3>
      <pre className="bg-surface-muted p-4 rounded-lg text-sm font-mono text-sm overflow-x-auto max-h-64 overflow-y-auto">
        {JSON.stringify(result, null, 2)}
      </pre>
    </div>
  );
}

export function WebhookPage() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [payload, setPayload] = useState('test');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      // const payloadObj = JSON.parse(payload);
      // const response = await api.postWebhook(payloadObj);
      setResult({ success: true });
    } catch (err: any) {
      setError(err.message || 'Failed to send webhook');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <Header />
      <FormComponent loading={loading} payload={payload} setPayload={setPayload} handleSubmit={handleSubmit} />
      {error && <ErrorDisplay error={error} />}
      {result && <ResultDisplay result={result} />}
    </div>
  );
}