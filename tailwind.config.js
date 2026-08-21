/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./*/templates/**/*.html",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        appbg: 'var(--appbg)', surface: 'var(--surface)', field: 'var(--field)',
        line: 'var(--line)', linestrong: 'var(--linestrong)',
        body: 'var(--body)', muted: 'var(--muted)', ink: 'var(--ink)',
        brand: { DEFAULT: 'var(--brand)', ink: 'var(--brand-ink)', soft: 'var(--brand-soft)' },
        pend: { bg: 'var(--pend-bg)', ink: 'var(--pend-ink)', dot: 'var(--pend-dot)' },
        apro: { bg: 'var(--apro-bg)', ink: 'var(--apro-ink)', dot: 'var(--apro-dot)' },
        rech: { bg: 'var(--rech-bg)', ink: 'var(--rech-ink)', dot: 'var(--rech-dot)' },
      },
      fontFamily: {
        sans: ['-apple-system', 'Segoe UI', 'system-ui', 'Roboto', 'sans-serif'],
        mono: ['SF Mono', 'ui-monospace', 'Cascadia Mono', 'Roboto Mono', 'monospace'],
      },
    },
  },
  plugins: [],
}
