/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                'event-interview': '#3B82F6',
                'event-offer': '#10B981',
                'event-applied': '#8B5CF6',
                'event-rejection': '#EF4444',
                'event-assessment': '#F59E0B',
            },
            animation: {
                'in': 'fadeIn 0.2s ease-in',
                'slide-in-from-bottom': 'slideInFromBottom 0.2s ease-out',
            },
            keyframes: {
                fadeIn: {
                    '0%': { opacity: '0' },
                    '100%': { opacity: '1' },
                },
                slideInFromBottom: {
                    '0%': { transform: 'translateY(100%)', opacity: '0' },
                    '100%': { transform: 'translateY(0)', opacity: '1' },
                },
            },
        },
    },
    plugins: [],
}

