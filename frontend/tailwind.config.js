/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        surface: {
          DEFAULT: 'hsl(var(--surface))',
          muted: 'hsl(var(--surface-muted))',
        },
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
          hover: 'hsl(var(--primary-hover))',
        },
        border: 'hsl(var(--border))',
        ring: 'hsl(var(--ring))',
        // Colores semánticos ITIL v4
        itil: {
          info: {
            DEFAULT: 'hsl(var(--itil-info))',
            light: '#eff6ff',
            border: '#bfdbfe',
          },
          warning: {
            DEFAULT: 'hsl(var(--itil-warning))',
            light: '#fffbeb',
            border: '#fde68a',
          },
          exception: {
            DEFAULT: 'hsl(var(--itil-exception))',
            light: '#fef2f2',
            border: '#fecaca',
          },
          success: {
            DEFAULT: 'hsl(var(--itil-success))',
            light: '#f0fdf4',
            border: '#bbf7d0',
          },
          request: {
            DEFAULT: 'hsl(var(--itil-request))',
            light: '#f5f3ff',
            border: '#ddd6fe',
          },
        },
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
    },
  },
  plugins: [],
}
