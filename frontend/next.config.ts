import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  reactCompiler: true,
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  transpilePackages: [
    "lucide-react",
    "framer-motion",
    "@react-three/drei",
    "@studio-freight/react-lenis",
  ],
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://algoquant-env.eba-y7ktk2xn.eu-north-1.elasticbeanstalk.com/api/:path*',
      },
    ];
  },
};

export default nextConfig;
