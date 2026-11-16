/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ivory: "#F6F2E8",
        ink: "#171815",
        acid: "#C7F432",
        moss: "#54643A",
      },
      fontFamily: {
        display: ["Cormorant Garamond", "Georgia", "serif"],
        body: ["Manrope", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

