/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Guardian Re Official Brand Colors (from Brand Manual)
        guardian: {
          green: '#218949',           // Primary - Guardian Green
          'green-dark': '#1a6d3a',    // Darker green for hover/active
          'green-light': '#2ea85c',   // Lighter green accent
          'green-50': '#f0fdf4',      // Very light green bg
          'green-100': '#dcfce7',     // Light green bg
          black: '#000000',           // Guardian Black
          gold: '#CBA875',            // Guardian Gold - premium accents
          'gold-light': '#DCC59A',    // Lighter gold
          'gold-dark': '#A88B5E',     // Darker gold
          red: '#E11B22',             // Minerva Red - partner accent
          'red-light': '#F4555B',     // Lighter red
          cream: '#FFF9F0',           // Warm cream background
          ivory: '#FDFBF7',           // Off-white
        },
        // Semantic aliases
        primary: {
          50: '#f0fdf4',
          100: '#dcfce7',
          200: '#bbf7d0',
          300: '#86efac',
          400: '#4ade80',
          500: '#218949',   // Guardian Green
          600: '#1a6d3a',
          700: '#15803d',
          800: '#166534',
          900: '#14532d',
          950: '#052e16',
        },
        accent: {
          50: '#fefce8',
          100: '#fef9c3',
          200: '#fef08a',
          300: '#fde047',
          400: '#CBA875',   // Guardian Gold
          500: '#DCC59A',
          600: '#A88B5E',
          700: '#8B7355',
          800: '#78634A',
          900: '#5C4B38',
          950: '#3D3225',
        },
      },
      fontFamily: {
        // Guardian Re Brand Typography
        sans: ['Raleway', 'system-ui', '-apple-system', 'sans-serif'],  // Brandon Grotesque alternative
        serif: ['Georgia', 'Cambria', 'Times New Roman', 'serif'],      // Primary brand font
        display: ['Georgia', 'Cambria', 'Times New Roman', 'serif'],    // Headings
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      typography: (theme) => ({
        DEFAULT: {
          css: {
            maxWidth: '75ch',
            color: theme('colors.gray.700'),
            a: {
              color: theme('colors.primary.600'),
              '&:hover': {
                color: theme('colors.primary.700'),
              },
            },
            'h1, h2, h3, h4': {
              color: theme('colors.gray.900'),
              fontWeight: '700',
            },
            blockquote: {
              borderLeftColor: theme('colors.primary.500'),
              color: theme('colors.gray.600'),
            },
            code: {
              backgroundColor: theme('colors.gray.100'),
              padding: '0.25rem 0.375rem',
              borderRadius: '0.25rem',
              fontWeight: '500',
            },
            'code::before': {
              content: '""',
            },
            'code::after': {
              content: '""',
            },
          },
        },
        dark: {
          css: {
            color: theme('colors.gray.300'),
            a: {
              color: theme('colors.primary.400'),
              '&:hover': {
                color: theme('colors.primary.300'),
              },
            },
            'h1, h2, h3, h4': {
              color: theme('colors.gray.100'),
            },
            blockquote: {
              borderLeftColor: theme('colors.primary.500'),
              color: theme('colors.gray.400'),
            },
            code: {
              backgroundColor: theme('colors.gray.800'),
              color: theme('colors.gray.200'),
            },
          },
        },
      }),
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out',
        'slide-up': 'slideUp 0.5s ease-out',
        'slide-down': 'slideDown 0.3s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideDown: {
          '0%': { opacity: '0', transform: 'translateY(-10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
};
