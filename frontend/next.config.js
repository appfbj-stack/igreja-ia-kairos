/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Output standalone para Docker (imagem final menor)
  output: 'standalone',
  // Para acesso na rede local (celular em dev)
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
