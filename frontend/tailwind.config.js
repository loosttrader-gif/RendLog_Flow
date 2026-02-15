/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,jsx}',
    './components/**/*.{js,jsx}',
    './app/**/*.{js,jsx}',
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          bg: '#0a0a0a',
          card: '#111111',
          cardHover: '#1a1a1a',
          border: '#1f1f1f',
          borderLight: '#2a2a2a',
          text: '#f5f5f5',
          textGray: '#8a8a8a',
        },
        accent: {
          DEFAULT: '#F59E0B',
          dark: '#D97706',
          light: '#FBBF24',
          muted: 'rgba(245, 158, 11, 0.15)',
        },
        success: '#10b981',
        danger: '#ef4444',
        warning: '#f59e0b',
      },
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [],
}
