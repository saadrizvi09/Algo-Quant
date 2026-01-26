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
      // 1. "Double API" Fix: If URL has 'proxy/api', send just the end path to AWS
      // Maps /api/proxy/api/login -> http://aws.../api/login (Wait, your backend HAS /api prefix!)
      {
        source: '/api/proxy/api/:path*',
        destination: 'http://algoquant-env.eba-y7ktk2xn.eu-north-1.elasticbeanstalk.com/api/:path*',
      },
      // 2. Standard Proxy: Handles /api/proxy/login
      {
        source: '/api/proxy/:path*',
        destination: 'http://algoquant-env.eba-y7ktk2xn.eu-north-1.elasticbeanstalk.com/api/:path*',
      },
    ];
  },
};

export default nextConfig;
