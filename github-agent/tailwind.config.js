const { fontFamily } = require('tailwindcss/defaultTheme')

/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ['class'],
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
        sidebar: 'hsl(var(--sidebar))',
        brand: {
          DEFAULT: 'hsl(var(--brand))',
          foreground: 'hsl(var(--brand-foreground))',
        },
        success: 'hsl(var(--success))',
        warning: 'hsl(var(--warning))',
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
        'chat-input': 'var(--chat-input-radius)',
      },
      fontFamily: {
        // Claude-style type: a serif for headings and replies, a clean sans for the interface.
        serif: ['"Source Serif 4 Variable"', 'Georgia', ...fontFamily.serif],
        rounded: ['"Source Serif 4 Variable"', 'Georgia', ...fontFamily.serif],
        sans: ['"Inter Variable"', '-apple-system', 'BlinkMacSystemFont', 'system-ui', ...fontFamily.sans],
        mono: ['"JetBrains Mono Variable"', 'ui-monospace', 'SFMono-Regular', 'Menlo', ...fontFamily.mono],
      },
      fontSize: {
        'app-caption': ['var(--app-text-caption)', { lineHeight: '1.33', fontWeight: '400' }],
        'app-body': ['var(--app-text-body)', { lineHeight: '1.5', fontWeight: '400' }],
        'app-heading': ['var(--app-text-heading)', { lineHeight: '1.2', fontWeight: '500' }],
        'app-display': ['var(--app-text-display)', { lineHeight: '1.11', fontWeight: '500' }],
        'display-xl': ['2.25rem', { lineHeight: '1.11', fontWeight: '500' }],
        'heading-lg': ['1.5rem', { lineHeight: '1.2', fontWeight: '500' }],
        'heading-md': ['1.125rem', { lineHeight: '1.33', fontWeight: '500' }],
        'body-md': ['1rem', { lineHeight: '1.5', fontWeight: '400' }],
        'body-sm': ['0.875rem', { lineHeight: '1.43', fontWeight: '400' }],
        caption: ['0.75rem', { lineHeight: '1.33', fontWeight: '400' }],
      },
      transitionDuration: {
        fast: '150ms',
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
    require('tailwind-scrollbar')({ nocompatible: true }),
  ],
}
