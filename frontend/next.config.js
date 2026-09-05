const backendOrigin =
  process.env.BACKEND_INTERNAL_URL ||
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  'http://127.0.0.1:8001';

const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  async rewrites() {
    return [
      { source: '/api/:path*', destination: `${backendOrigin}/:path*` },
    ];
  },
};
module.exports = nextConfig;
