/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#020617', // slate-950
        card: '#0f172a', // slate-900
        accent: {
          DEFAULT: '#6366f1', // indigo-500
          hover: '#4f46e5',
        }
      }
    },
  },
  plugins: [],
}
