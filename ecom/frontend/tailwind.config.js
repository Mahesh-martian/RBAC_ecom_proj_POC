/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f8f7ff',
          100: '#f0eeff',
          200: '#e5dcff',
          300: '#d4c5ff',
          400: '#bfa5ff',
          500: '#a78dff',
          600: '#8f6aff',
          700: '#7c52ff',
          800: '#6b3dff',
          900: '#5d2dff',
        },
        secondary: {
          50: '#fff7ed',
          100: '#fed3b3',
          200: '#fdab7b',
          300: '#fc8343',
          400: '#fb5a1b',
          500: '#fa3200',
          600: '#e02900',
          700: '#c62000',
          800: '#ac1700',
          900: '#930e00',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
