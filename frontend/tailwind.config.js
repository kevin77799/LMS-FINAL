/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        theme: {
          bg: "var(--theme-bg)",
          surface: "var(--theme-surface)",
          accent: "var(--theme-accent)",
          "accent-hover": "var(--theme-accent-hover)",
          text: "var(--theme-text)",
          "text-secondary": "var(--theme-text-secondary)",
          border: "var(--theme-border)",
        },
      },
    },
  },
  plugins: [],
}
