/**
 * RevFlow Design Tokens
 * 
 * Centralized design tokens for the RevFlow frontend.
 * All visual styling MUST use these tokens.
 * No component may contain raw color literals or hardcoded spacing values.
 */

// Color tokens
export const colors = {
  // Brand colors - Razorpay-inspired
  primary: {
    50: '#f0f5ff',
    100: '#e0ebff',
    200: '#c7d9ff',
    300: '#a3bbff',
    400: '#7a93ff',
    500: '#536bff',
    600: '#3b4dff',
    700: '#2a3be8',
    800: '#222ec7',
    900: '#1f28a3',
    950: '#171a63',
  },

  // Surface colors
  surface: {
    DEFAULT: '#ffffff',
    muted: '#f8fafc',
    elevated: '#ffffff',
  },

  // Background colors
  background: {
    DEFAULT: '#f8fafc',
    secondary: '#f1f5f9',
  },

  // Text colors
  text: {
    primary: '#0f172a',
    secondary: '#475569',
    muted: '#94a3b8',
    inverse: '#ffffff',
  },

  // Border colors
  border: {
    DEFAULT: '#e2e8f0',
    strong: '#cbd5e1',
  },

  // Semantic colors
  success: {
    50: '#f0fdf4',
    100: '#dcfce7',
    500: '#22c55e',
    600: '#16a34a',
    700: '#15803d',
  },
  warning: {
    50: '#fffbeb',
    100: '#fef3c7',
    500: '#f59e0b',
    600: '#d97706',
    700: '#b45309',
  },
  danger: {
    50: '#fef2f2',
    100: '#fee2e2',
    500: '#ef4444',
    600: '#dc2626',
    700: '#b91c1c',
  },
  info: {
    50: '#eff6ff',
    100: '#dbeafe',
    500: '#3b82f6',
    600: '#2563eb',
    700: '#1d4ed8',
  },
} as const;

// Spacing tokens
export const spacing = {
  0: '0',
  1: '0.25rem',
  2: '0.5rem',
  3: '0.75rem',
  4: '1rem',
  5: '1.25rem',
  6: '1.5rem',
  8: '2rem',
  10: '2.5rem',
  12: '3rem',
  16: '4rem',
  20: '5rem',
  24: '6rem',
} as const;

// Typography tokens
export const typography = {
  fontSize: {
    xs: '0.75rem',
    sm: '0.875rem',
    base: '1rem',
    lg: '1.125rem',
    xl: '1.25rem',
    '2xl': '1.5rem',
    '3xl': '1.875rem',
    '4xl': '2.25rem',
  },
  fontWeight: {
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
  lineHeight: {
    tight: 1.25,
    normal: 1.5,
    relaxed: 1.75,
  },
  fontFamily: {
    sans: ['Inter', 'system-ui', 'sans-serif'],
    mono: ['JetBrains Mono', 'monospace'],
  },
} as const;

// Border radius tokens
export const borderRadius = {
  none: '0',
  sm: '0.25rem',
  DEFAULT: '0.375rem',
  md: '0.5rem',
  lg: '0.75rem',
  xl: '1rem',
  '2xl': '1.5rem',
  full: '9999px',
} as const;

// Shadow tokens
export const shadows = {
  sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
  DEFAULT: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
  md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
  lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
  xl: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
} as const;

// Transition tokens
export const transitions = {
  duration: {
    '75': '75ms',
    '100': '100ms',
    '150': '150ms',
    '200': '200ms',
    '300': '300ms',
    '500': '500ms',
    '700': '700ms',
    '1000': '1000ms',
  },
  timing: {
    DEFAULT: 'cubic-bezier(0.4, 0, 0.2, 1)',
    in: 'cubic-bezier(0.4, 0, 1, 1)',
    out: 'cubic-bezier(0, 0, 0.2, 1)',
    'in-out': 'cubic-bezier(0.4, 0, 0.2, 1)',
  },
} as const;

// Z-index tokens
export const zIndex = {
  hide: -1,
  auto: 'auto',
  base: '0',
  dropdown: '1000',
  sticky: '1100',
  modal: '1300',
  popover: '1400',
  tooltip: '1500',
  toast: '1700',
} as const;

// Breakpoint tokens
export const breakpoints = {
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px',
} as const;

// Export all tokens as a single object for easy importing
export const designTokens = {
  colors,
} as const;

// Type exports for TypeScript
export type Colors = typeof designTokens.colors;
export type Spacing = typeof spacing;
export type Typography = typeof typography;
export type BorderRadius = typeof borderRadius;
export type Shadows = typeof shadows;
export type Transitions = typeof transitions;
export type ZIndex = typeof zIndex;
export type Breakpoints = typeof breakpoints;