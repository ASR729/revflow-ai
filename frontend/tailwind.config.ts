import type { Config } from 'tailwindcss';

const withAlpha = (variable: string) => `rgb(var(${variable}) / <alpha-value>)`;

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './lib/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        canvas: withAlpha('--canvas-rgb'),
        ink: withAlpha('--ink-rgb'),
        navy: withAlpha('--ledger-navy-rgb'),
        recovered: withAlpha('--recovered-green-rgb'),
        atrisk: withAlpha('--at-risk-amber-rgb'),
        stopped: withAlpha('--stopped-crimson-rgb'),
        simulated: withAlpha('--simulated-slate-rgb'),
        surface: withAlpha('--surface-rgb'),
        'surface-2': withAlpha('--surface-2-rgb'),
        edge: withAlpha('--border-rgb'),
        'edge-strong': withAlpha('--border-strong-rgb'),
        muted: withAlpha('--muted-rgb'),
      },
      fontFamily: {
        sans: ['var(--font-plex-sans)', 'system-ui', 'sans-serif'],
        display: ['var(--font-newsreader)', 'Georgia', 'serif'],
        mono: ['var(--font-plex-mono)', 'ui-monospace', 'monospace'],
      },
      borderRadius: {
        card: '6px',
      },
      boxShadow: {
        card: '0 1px 2px 0 rgb(18 22 28 / 0.04), 0 1px 3px 0 rgb(18 22 28 / 0.06)',
        lift: '0 6px 16px -4px rgb(18 22 28 / 0.10), 0 2px 6px -2px rgb(18 22 28 / 0.08)',
        pop: '0 16px 40px -12px rgb(18 22 28 / 0.18), 0 4px 12px -4px rgb(18 22 28 / 0.10)',
      },
      transitionTimingFunction: {
        smooth: 'cubic-bezier(0.22, 1, 0.36, 1)',
      },
    },
  },
  plugins: [],
};

export default config;
