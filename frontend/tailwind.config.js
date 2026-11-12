/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'iron-grey': '#3E4E50',
        'ash-grey': '#C6D8D3',
        'deep-crimson': '#8E151F',
        'vivid-tangerine': '#FF7F11',
        'shadow-grey': '#272838',
        'warm-porcelain': '#F5F2EA',
        'soft-sand': '#E7DCCB',
      },
      fontFamily: {
        serif: ['Newsreader', 'Georgia', 'serif'],
        sans: ['Manrope', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
};

