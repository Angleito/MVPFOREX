/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Enable cross-origin requests to Flask API
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:5000/api/:path*', // Proxy to Flask backend in dev
      },
    ];
  },
};

module.exports = nextConfig;
