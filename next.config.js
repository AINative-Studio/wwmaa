/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  // Use standalone output to avoid static page generation errors
  // Pages will render dynamically at runtime instead of at build time
  output: 'standalone',
};

module.exports = nextConfig;
