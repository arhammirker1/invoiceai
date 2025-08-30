# tailwind.config.js - Tailwind CSS Configuration
# ============================================================================

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        cream: '#fdf6ec',
        matcha: {
          50: '#f6f9f6',
          100: '#e8f2e7',
          200: '#d2e4d1',
          300: '#a4c3a2',
          400: '#8faf8d',
          500: '#7a9b78',
          600: '#647d62',
          700: '#526350',
          800: '#435041',
          900: '#384236'
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'float': 'float 3s ease-in-out infinite',
        'bounce-slow': 'bounce 2s infinite',
        'pulse-slow': 'pulse 3s infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' }
        }
      },
      backgroundImage: {
        'gradient-cream-matcha': 'linear-gradient(135deg, #fdf6ec 0%, #a4c3a2 100%)',
        'gradient-matcha': 'linear-gradient(135deg, #a4c3a2 0%, #8faf8d 100%)',
      },
      boxShadow: {
        'premium': '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
        'glow': '0 0 20px rgba(164, 195, 162, 0.3)',
      }
    },
  },
  plugins: [],
}

