/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    appDir: true,
  },
  async rewrites() {
    return [
      {
        source: '/api/python/:path*',
        destination: '/api/:path*',
      },
    ]
  },
}

module.exports = nextConfig