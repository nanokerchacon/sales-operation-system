/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        slate: {
          950: "#060b16",
        },
        brand: {
          ink: "#0f172a",
          panel: "#111827",
          line: "#d9e1ec",
          mist: "#f4f7fb",
          steel: "#526277",
          accent: "#1f3a5f",
        },
        priority: {
          low: "#5f6f86",
          medium: "#b7791f",
          high: "#b42318",
        },
      },
      boxShadow: {
        panel: "0 10px 30px rgba(15, 23, 42, 0.06)",
        soft: "0 1px 2px rgba(15, 23, 42, 0.04), 0 12px 24px rgba(15, 23, 42, 0.06)",
      },
      fontFamily: {
        sans: ['"Segoe UI Variable"', '"Bahnschrift"', '"Segoe UI"', "sans-serif"],
      },
      gridTemplateColumns: {
        dashboard: "minmax(0, 1.9fr) minmax(320px, 0.95fr)",
      },
    },
  },
  plugins: [],
};
