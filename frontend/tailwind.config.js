/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        background: 'var(--background)',
        foreground: 'var(--foreground)',
        primary: {
          DEFAULT: 'var(--primary)',
          bright: 'var(--primary-bright)',
        },
        accent: {
          lime: 'var(--accent-lime)',
          bright: 'var(--accent-bright)',
        },
        hazard: {
          red: 'var(--hazard-red)',
        },
        anomaly: {
          amber: 'var(--anomaly-amber)',
        },
        muted: {
          DEFAULT: 'var(--muted)',
          secondary: 'var(--muted-secondary)',
        },
        text: {
          secondary: 'var(--text-secondary)',
          primary: 'var(--text-primary)',
        }
      },
      fontFamily: {
        sans: ['Space Grotesk', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      keyframes: {
        driftStars: {
          from: { transform: 'translate(0,0)' },
          to: { transform: 'translate(-3%,-4%)' },
        },
        nebulaDrift1: {
          '0%, 100%': { transform: 'translate(0,0) scale(1)' },
          '50%': { transform: 'translate(3%,-2%) scale(1.08)' },
        },
        nebulaDrift2: {
          '0%, 100%': { transform: 'translate(0,0) scale(1)' },
          '50%': { transform: 'translate(-4%,3%) scale(1.05)' },
        },
        radarSweep: {
          from: { transform: 'rotate(0deg)' },
          to: { transform: 'rotate(360deg)' },
        }
      },
      animation: {
        driftStars: 'driftStars 140s linear infinite',
        nebulaDrift1: 'nebulaDrift1 40s ease-in-out infinite',
        nebulaDrift2: 'nebulaDrift2 46s ease-in-out infinite',
        radarSweep: 'radarSweep 8s linear infinite',
      }
    },
  },
  plugins: [],
}
