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
};

export default nextConfig;
