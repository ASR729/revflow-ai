const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  images: { domains: ['localhost'] },
  async rewrites() { return [
    { source: '/api/:path*', destination: 'http://localhost:8000/api/:path*' },
    { source: '/health', destination: 'http://localhost:8000/health' },
    { source: '/metrics', destination: 'http://localhost:8000/metrics' },
    { source: '/runs', destination: 'http://localhost:8000/runs' },
    { source: '/run-batch', destination: 'http://localhost:8000/run-batch' },
    { source: '/classifier-metrics', destination: 'http://localhost:8000/classifier-metrics' },
    { source: '/events/:path*', destination: 'http://localhost:8000/events/:path*' },
    { source: '/config', destination: 'http://localhost:8000/config' },
    { source: '/webhook', destination: 'http://localhost:8000/webhook' },
  ]; },
  webpack: (config, { isServer, dev }) => {
    if (isServer && !dev) {
      config.optimization.splitChunks = {
        ...config.optimization.splitChunks,
        cacheGroups: {
          ...config.optimization.splitChunks.cacheGroups,
          document: {
            test: /[\\/]pages[\\/]_document/,
            name: 'document',
            chunks: 'all',
            enforce: true,
            priority: 100,
            minSize: 0,
            minChunks: 1,
            reuseExistingChunk: true,
          },
        },
      };
    }
    return config;
  },
};
module.exports = nextConfig;