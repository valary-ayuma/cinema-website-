/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        house: {
          950: "#0c0f16",   // theater darkness
          900: "#12151f",
          800: "#1b2030",
        },
        marquee: {
          400: "#f0c05a",   // bulb gold
          500: "#e8b54d",
        },
        velvet: {
          500: "#b23a48",   // seat red
          600: "#8f2d39",
        },
        screen: {
          glow: "#fdf6e3",
        },
      },
      fontFamily: {
        display: ["'Bebas Neue'", "Oswald", "sans-serif"],
        body: ["Inter", "sans-serif"],
      },
    },
  },
  plugins: [],
}
