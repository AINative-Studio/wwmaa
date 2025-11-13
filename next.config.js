/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  // Disable SWC to avoid corrupted binary downloads on Railway
  // Use Babel instead (slower but more reliable)
  swcMinify: false,
  compiler: {
    // This tells Next.js to use Babel instead of SWC
  },
};

module.exports = nextConfig;
