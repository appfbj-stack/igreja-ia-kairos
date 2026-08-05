/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Para acesso na rede local (celular)
  async rewrites() {
    return [
      {
        source: '/api-backend/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
