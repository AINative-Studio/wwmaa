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
  // Log environment variables during build for debugging
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    NEXT_PUBLIC_API_MODE: process.env.NEXT_PUBLIC_API_MODE,
    NEXT_PUBLIC_SITE_URL: process.env.NEXT_PUBLIC_SITE_URL,
  },
};

// Validate required environment variables at build time
const requiredEnvVars = ['NEXT_PUBLIC_API_URL', 'NEXT_PUBLIC_API_MODE'];
const missingEnvVars = requiredEnvVars.filter(varName => !process.env[varName]);

if (missingEnvVars.length > 0) {
  console.warn('\n⚠️  WARNING: Missing required environment variables:');
  missingEnvVars.forEach(varName => {
    console.warn(`   - ${varName}`);
  });
  console.warn('\n   The application will default to localhost:8000');
  console.warn('   Set these variables in Railway to connect to production backend.\n');
}

// Log the API URL being used during build
console.log('\n🔧 Build-time environment:');
console.log(`   NEXT_PUBLIC_API_URL: ${process.env.NEXT_PUBLIC_API_URL || 'NOT SET (will use localhost:8000)'}`);
console.log(`   NEXT_PUBLIC_API_MODE: ${process.env.NEXT_PUBLIC_API_MODE || 'NOT SET (will use mock)'}`);
console.log(`   NEXT_PUBLIC_SITE_URL: ${process.env.NEXT_PUBLIC_SITE_URL || 'NOT SET'}\n`);

module.exports = nextConfig;
