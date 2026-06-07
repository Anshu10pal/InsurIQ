import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        gold: {
          DEFAULT: "#C9A84C",
          light:   "#E2C97E",
          dark:    "#9A7A2E",
        },
        obsidian: {
          DEFAULT: "#0A0A0A",
          800:     "#141414",
          700:     "#1E1E1E",
          600:     "#2A2A2A",
          500:     "#3A3A3A",
        },
        risk: {
          low:    "#22C55E",
          medium: "#F59E0B",
          high:   "#EF4444",
        },
      },
      fontFamily: {
        display:  ["'Cormorant Garamond'", "serif"],
        heading:  ["'Playfair Display'", "serif"],
        sans:     ["'Montserrat'", "sans-serif"],
        body:     ["'Inter'", "sans-serif"],
      },
      backgroundImage: {
        "gold-gradient": "linear-gradient(135deg, #C9A84C 0%, #E2C97E 50%, #9A7A2E 100%)",
      },
    },
  },
  plugins: [],
} satisfies Config;
