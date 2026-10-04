const ports = require('./ports.json')

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  distDir: 'out',
  images: { unoptimized: true },
  trailingSlash: true,
  // The backend's address, from ports.json (the one place the ports are set).
  env: {
    NEXT_PUBLIC_API_BASE_URL:
      process.env.NEXT_PUBLIC_API_BASE_URL || `http://127.0.0.1:${ports.backend}`,
  },
}

module.exports = nextConfig
