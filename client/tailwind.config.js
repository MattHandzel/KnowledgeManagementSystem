/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eef6ff",
          100: "#d9eaff",
          200: "#bcd9ff",
          300: "#90c1ff",
          400: "#61a1ff",
          500: "#3c7dff",
          600: "#285fea",
          700: "#204ac2",
          800: "#1e3e99",
          900: "#1d397d"
        }
      }
    }
  },
  plugins: []
}
