/** @type {import('next').NextConfig} */
const { version } = require('./package.json');
const path = require('path');

const nextConfig = {
  experimental: { instrumentationHook: true },
  reactStrictMode: false,
  output: 'standalone',
  typescript: {
    ignoreBuildErrors: true
  },
  env: {
    NEXT_PUBLIC_APP_VERSION: version,
    NEXT_PUBLIC_CREATED_DATE: new Date().toISOString(),
  },
  // Load environment variables from root .env file
  env: {
    NEXT_PUBLIC_APP_VERSION: version,
    NEXT_PUBLIC_CREATED_DATE: new Date().toISOString(),
    // Forward environment variables from .env to Next.js
    PYTHON_API_URL: process.env.PYTHON_API_URL,
    LD_SDK_KEY: process.env.LD_SDK_KEY,
    LAUNCHDARKLY_SDK_KEY: process.env.LAUNCHDARKLY_SDK_KEY,
    LAUNCHDARKLY_PROJECT_KEY: process.env.LAUNCHDARKLY_PROJECT_KEY,
    LAUNCHDARKLY_ENVIRONMENT_KEY: process.env.LAUNCHDARKLY_ENVIRONMENT_KEY,
    LAUNCHDARKLY_API_TOKEN: process.env.LAUNCHDARKLY_API_TOKEN,
    AWS_REGION: process.env.AWS_REGION,
    DB_URL: process.env.DB_URL,
  }
}

module.exports = nextConfig

