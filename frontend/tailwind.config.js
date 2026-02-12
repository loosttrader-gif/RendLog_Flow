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
          bg: '#0a0e27',
          card: '#151b34',
          border: '#1f2937',
          text: '#e5e7eb',
          textGray: '#9ca3af',
        },
        primary: {
          DEFAULT: '#3b82f6',
          dark: '#2563eb',
          light: '#60a5fa',
        },
        success: '#10b981',
        danger: '#ef4444',
      },
    },
  },
  plugins: [],
}
