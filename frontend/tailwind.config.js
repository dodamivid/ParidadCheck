/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#EEF1F9',
          100: '#D5DCF0',
          500: '#2C4BA3',
          600: '#1B2B5E',
          700: '#111D42',
          900: '#080D1F',
        },
        accent: {
          400: '#E040A0',
          500: '#C2185B',
          600: '#880E4F',
        },
        success: {
          100: '#DCFCE7',
          500: '#16A34A',
          700: '#15803D',
        },
        warning: {
          100: '#FEF9C3',
          500: '#CA8A04',
          700: '#A16207',
        },
        danger: {
          100: '#FEE2E2',
          500: '#DC2626',
          700: '#B91C1C',
        },
        neutral: {
          50: '#F8FAFC',
          100: '#F1F5F9',
          200: '#E2E8F0',
          400: '#94A3B8',
          600: '#475569',
          800: '#1E293B',
          900: '#0F172A',
        },
      },
    },
  },
  plugins: [],
}
