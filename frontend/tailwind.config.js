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
        serif: ['Newsreader', 'Georgia', 'Cambria', 'serif'],
        sans: ['Manrope', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      boxShadow: {
        'subtle': '0 1px 2px 0 rgba(39, 40, 56, 0.04)',
        'card': '0 1px 3px 0 rgba(39, 40, 56, 0.05), 0 1px 2px -1px rgba(39, 40, 56, 0.03)',
        'elevated': '0 4px 14px -2px rgba(39, 40, 56, 0.08), 0 2px 6px -2px rgba(39, 40, 56, 0.04)',
      },
      borderRadius: {
        'academic': '6px',
      },
    },
  },
  plugins: [],
};

