'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import type { ConfigResponse } from '@/lib/api';

export function ConfigPage() {
  const [config, setConfig] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchConfig = async () => {
    setLoading(true);
    try {
      const data = await api.getConfig();
      setConfig(data);
      setError(null);
    } catch (error) {
      console.error('Failed to fetch config:', error);
      setError('Failed to load configuration');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConfig();
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Configuration</h1>
          <p className="text-text-secondary mt-1">System configuration and policy ceilings</p>
        </div>
        <div className="card p-8 text-center">
          <div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-text-secondary">Loading configuration...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Configuration</h1>
          <p className="text-text-secondary mt-1">System configuration and policy ceilings</p>
        </div>
        <div className="card p-6 text-center text-danger-600">
          Failed to load configuration
        </div>
      </div>
    );
  }

  const configSections = [
    {
      title: 'Retry Policy',
      items: [
        { key: 'MAX_RETRIES', label: 'Max Retries', value: config.MAX_RETRIES },
        { key: 'COOLDOWN_HOURS', label: 'Cooldown Hours', value: `${config.COOLDOWN_HOURS}h` },
        { key: 'RETRY_BACKOFF_HOURS', label: 'Retry Backoff Hours', value: config.RETRY_BACKOFF_HOURS.join(', ') + 'h' },
      ],
    },
    {
      title: 'Checkout Session',
      items: [
        { key: 'CHECKOUT_SESSION_WINDOW_MINUTES', label: 'Session Window', value: `${config.CHECKOUT_SESSION_WINDOW_MINUTES} min` },
      ],
    },
    {
      title: 'Contact Frequency Cap',
      items: [
        { key: 'MAX_CONTACTS_PER_CUSTOMER_PER_DAY', label: 'Max Contacts/Customer/Day', value: config.MAX_CONTACTS_PER_CUSTOMER_PER_DAY },
      ],
    },
    {
      title: 'Hard Stops',
      items: [
        { key: 'STOP_IF_CAUSE_IN', label: 'Stop If Cause In', value: config.STOP_IF_CAUSE_IN.join(', ') },
      ],
    },
    {
      title: 'B2B Ladder Thresholds',
      items: [
        { key: 'LADDER_GENTLE_AFTER_DAYS', label: 'Gentle After (days)', value: config.LADDER_GENTLE_AFTER_DAYS },
        { key: 'LADDER_FIRM_AFTER_DAYS', label: 'Firm After (days)', value: config.LADDER_FIRM_AFTER_DAYS },
        { key: 'LADDER_FLAG_AFTER_DAYS', label: 'Flag After (days)', value: config.LADDER_FLAG_AFTER_DAYS },
      ],
    },
    {
      title: 'PTP Grace Period',
      items: [
        { key: 'PTP_GRACE_DAYS', label: 'PTP Grace Days', value: config.PTP_GRACE_DAYS },
      ],
    },
    {
      title: 'LLM Budget',
      items: [
        { key: 'LLM_CALL_BUDGET_PER_RUN', label: 'LLM Call Budget/Run', value: config.LLM_CALL_BUDGET_PER_RUN },
        { key: 'LLM_MAX_ATTEMPTS', label: 'LLM Max Attempts', value: config.LLM_MAX_ATTEMPTS },
        { key: 'LLM_TIMEOUT_SECONDS', label: 'LLM Timeout (seconds)', value: config.LLM_TIMEOUT_SECONDS },
      ],
    },
    {
      title: 'Batch Configuration',
      items: [
        { key: 'BATCH_SIZE', label: 'Batch Size', value: config.BATCH_SIZE },
        { key: 'RANDOM_SEED', label: 'Random Seed', value: config.RANDOM_SEED },
      ],
    },
    {
      title: 'Performance Budget',
      items: [
        { key: 'DECISION_LATENCY_BUDGET_MS', label: 'Decision Latency Budget (ms)', value: config.DECISION_LATENCY_BUDGET_MS },
      ],
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-text-primary">Configuration</h1>
        <p className="text-text-secondary mt-1">System configuration and policy ceilings</p>
      </div>

      <div className="space-y-6">
        {configSections.map((section) => (
          <section key={section.title} className="card p-6">
            <h2 className="text-lg font-semibold text-text-primary mb-4">{section.title}</h2>
            <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {section.items.map((item) => (
                <div key={item.key} className="space-y-1">
                  <dt className="text-sm font-medium text-text-secondary">{item.label}</dt>
                  <dd className="font-mono text-lg font-medium text-text-primary">{item.value}</dd>
                </div>
              ))}
            </dl>
          </section>
        ))}
      </div>
    </div>
  );
}