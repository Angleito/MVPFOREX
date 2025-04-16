/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Enable cross-origin requests to Flask API
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:5050/api/:path*', // Use 127.0.0.1 instead of localhost
      },
    ];
  },
};

module.exports = nextConfig;
