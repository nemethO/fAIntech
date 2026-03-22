/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/templates/**/*.html',
    './app/static/js/**/*.js',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Dark theme palette (from design mockups)
        dark: {
          bg: '#0f1117',
          card: '#1a1d2e',
          border: '#2a2d3e',
          hover: '#252840',
        },
        primary: {
          DEFAULT: '#7c3aed',  // Purple accent
          light: '#a78bfa',
          dark: '#5b21b6',
        },
        accent: {
          green: '#22c55e',
          red: '#ef4444',
          yellow: '#eab308',
          blue: '#3b82f6',
          orange: '#f97316',
          pink: '#ec4899',
          cyan: '#06b6d4',
        },
      },
    },
  },
  plugins: [],
}
