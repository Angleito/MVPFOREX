/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Enable cross-origin requests to Flask API
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: '/api/:path*', // Let Vercel handle /api/ with Python
      },
    ];
  },
};

module.exports = nextConfig;
