/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  // Force WASM fallback for SWC to prevent binary download issues
  swcMinify: true,
  experimental: {
    // Use WASM version of SWC instead of native binaries
    forceSwcTransforms: true,
  },
};

module.exports = nextConfig;
