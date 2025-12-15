"use client";

import React, { useRef, useState } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Stars, MeshDistortMaterial, Float, Environment, PerspectiveCamera } from "@react-three/drei";
import { 
  motion, 
  useScroll, 
  useTransform, 
  useSpring, 
  useMotionValue, 
  useMotionTemplate, 
  AnimatePresence 
} from "framer-motion";
import { ReactLenis } from "@studio-freight/react-lenis";
import { ArrowRight, Zap, Shield, Cpu, Activity, BarChart3, Lock } from "lucide-react";
import { useRouter } from "next/navigation";
import * as THREE from "three";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

// --- UTILS ---
function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// --- 3D COMPONENTS ---

// 1. Interactive Blob that reacts to mouse
function InteractiveShape() {
  const meshRef = useRef<THREE.Mesh>(null);
  const { mouse, viewport } = useThree();

  useFrame((state) => {
    if (meshRef.current) {
      // Rotate steadily
      meshRef.current.rotation.x = state.clock.getElapsedTime() * 0.2;
      meshRef.current.rotation.y = state.clock.getElapsedTime() * 0.3;

      // Slight parallax follow mouse
      const x = (mouse.x * viewport.width) / 4;
      const y = (mouse.y * viewport.height) / 4;
      meshRef.current.position.x = THREE.MathUtils.lerp(meshRef.current.position.x, x + 2, 0.1);
      meshRef.current.position.y = THREE.MathUtils.lerp(meshRef.current.position.y, y, 0.1);
    }
  });

  return (
    <Float speed={2} rotationIntensity={1.5} floatIntensity={2}>
      <mesh ref={meshRef} scale={2.5} position={[2, 0, 0]}>
        <icosahedronGeometry args={[1, 0]} />
        <MeshDistortMaterial
          color="#06b6d4"
          attach="material"
          distort={0.6}
          speed={2.5}
          roughness={0.1}
          metalness={1}
          bumpScale={0.005}
        />
      </mesh>
    </Float>
  );
}

function Scene3D() {
  return (
    <div className="fixed inset-0 z-0 pointer-events-none">
      <Canvas gl={{ antialias: true, alpha: true }} dpr={[1, 2]}>
        <PerspectiveCamera makeDefault position={[0, 0, 6]} />
        
        {/* Lights */}
        <ambientLight intensity={0.2} />
        <pointLight position={[10, 10, 10]} intensity={1.5} color="#06b6d4" />
        <spotLight position={[-10, -10, -10]} angle={0.15} penumbra={1} intensity={1} color="#ffffff" />
        
        {/* Environment for realistic metal reflections */}
        <Environment preset="city" />
        
        <Stars radius={50} depth={50} count={3000} factor={4} saturation={0} fade speed={1.5} />
        <InteractiveShape />
        
        {/* Fog for depth */}
        <fog attach="fog" args={['#050505', 5, 25]} />
      </Canvas>
    </div>
  );
}

// --- ADVANCED UI COMPONENTS ---

// 2. Magnetic Button (Sticks to cursor)
const MagneticButton = ({ children, className, onClick }: { children: React.ReactNode, className?: string, onClick?: () => void }) => {
  const ref = useRef<HTMLButtonElement>(null);
  const [position, setPosition] = useState({ x: 0, y: 0 });

  const handleMouse = (e: React.MouseEvent) => {
    const { clientX, clientY } = e;
    const { height, width, left, top } = ref.current!.getBoundingClientRect();
    const middleX = clientX - (left + width / 2);
    const middleY = clientY - (top + height / 2);
    setPosition({ x: middleX * 0.2, y: middleY * 0.2 });
  };

  const reset = () => {
    setPosition({ x: 0, y: 0 });
  };

  const { x, y } = position;

  return (
    <motion.button
      ref={ref}
      className={cn("relative z-10 cursor-pointer", className)}
      onMouseMove={handleMouse}
      onMouseLeave={reset}
      onClick={onClick}
      animate={{ x, y }}
      transition={{ type: "spring", stiffness: 150, damping: 15, mass: 0.1 }}
    >
      {children}
    </motion.button>
  );
};

// 3. Spotlight Tilt Card
function SpotlightCard({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  function handleMouseMove({ currentTarget, clientX, clientY }: React.MouseEvent) {
    const { left, top } = currentTarget.getBoundingClientRect();
    mouseX.set(clientX - left);
    mouseY.set(clientY - top);
  }

  // 3D Tilt Values
  const x = useSpring(0, { stiffness: 150, damping: 15 });
  const y = useSpring(0, { stiffness: 150, damping: 15 });
  const z = useSpring(0, { stiffness: 150, damping: 15 });

  function handleTilt(e: React.MouseEvent<HTMLDivElement>) {
    const rect = e.currentTarget.getBoundingClientRect();
    const width = rect.width;
    const height = rect.height;
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    const xPct = mouseX / width - 0.5;
    const yPct = mouseY / height - 0.5;
    x.set(xPct * 10); // Rotate Y axis
    y.set(yPct * -10); // Rotate X axis
  }

  function handleMouseEnter() {
    z.set(50);
  }

  function handleReset() {
    x.set(0);
    y.set(0);
    z.set(0);
  }

  return (
    <motion.div
      style={{ rotateX: y, rotateY: x, z, transformPerspective: 1000, transformStyle: "preserve-3d" }}
      onMouseMove={(e) => { handleMouseMove(e); handleTilt(e); }}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleReset}
      className={cn(
        "group relative border border-white/10 bg-[#111]/40 overflow-hidden rounded-3xl backdrop-blur-xl transition-colors duration-500 hover:border-cyan-500/30",
        className
      )}
    >
      <div className="absolute inset-0 z-0 opacity-0 transition-opacity duration-500 group-hover:opacity-100 pointer-events-none">
         {/* Spotlight Gradient */}
        <motion.div
          className="pointer-events-none absolute -inset-px rounded-3xl opacity-0 transition duration-300 group-hover:opacity-100"
          style={{
            background: useMotionTemplate`
              radial-gradient(
                650px circle at ${mouseX}px ${mouseY}px,
                rgba(6, 182, 212, 0.15),
                transparent 80%
              )
            `,
          }}
        />
      </div>
      <div className="relative z-10 h-full transform-style-3d">
        {children}
      </div>
    </motion.div>
  );
}

// --- PAGE STRUCTURE ---

export default function LandingPage() {
  const router = useRouter();

  return (
    <ReactLenis root options={{ lerp: 0.1, duration: 1.5, smoothWheel: true }}>
      <div className="bg-[#050505] text-slate-200 min-h-screen font-sans selection:bg-cyan-500/30 relative overflow-x-hidden cursor-default">
        
        {/* GLOBAL 3D SCENE */}
        <Scene3D />

        <Navbar router={router} />
        <HeroSection />
        <BentoGridFeatures />
        <CallToAction router={router} />
        <Footer />
        
      </div>
    </ReactLenis>
  );
}

function Navbar({ router }: { router: any }) {
  return (
    <nav className="fixed top-0 w-full px-6 py-6 flex justify-between items-center z-50">
      {/* Dynamic Island style blur */}
      <div className="absolute inset-x-0 top-0 h-24 bg-gradient-to-b from-[#050505] to-transparent pointer-events-none" />
      
      <div className="relative z-10 flex items-center gap-2 cursor-pointer group">
        <div className="w-10 h-10 bg-gradient-to-tr from-cyan-500 to-blue-600 rounded-xl flex items-center justify-center shadow-lg shadow-cyan-500/20 group-hover:shadow-cyan-500/40 transition-all duration-300">
            <Cpu size={20} className="text-white" />
        </div>
        <span className="text-xl font-bold tracking-tight text-white">
          Algo<span className="text-cyan-400">Quant</span>
        </span>
      </div>

      <div className="relative z-10 flex gap-6 text-sm font-medium items-center">
        {['Platform', 'Pricing', 'Docs'].map((item) => (
           <MagneticButton 
             key={item} 
             className="hidden md:block"
             onClick={() => {
               if (item === 'Platform') router.push('/auth');
               if (item === 'Docs') router.push('/docs');
               if (item === 'Pricing') router.push('/pricing');
             }}
           >
              <span className="hover:text-cyan-400 transition-colors px-2 py-1">{item}</span>
           </MagneticButton>
        ))}
        
        <MagneticButton onClick={() => router.push("/auth")}>
          <div className="relative px-6 py-2.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-full overflow-hidden group">
             {/* Shimmer Effect */}
             <div className="absolute top-0 -left-full w-full h-full bg-gradient-to-r from-transparent via-white/20 to-transparent transform skew-x-12 group-hover:animate-shimmer" />
             <span className="relative text-white font-semibold backdrop-blur-sm">Login</span>
          </div>
        </MagneticButton>
      </div>
    </nav>
  );
}

function HeroSection() {
  const router = useRouter();
  const { scrollY } = useScroll();
  const y1 = useTransform(scrollY, [0, 500], [0, 200]);
  const y2 = useTransform(scrollY, [0, 500], [0, -150]);

  return (
    <section className="relative min-h-screen flex items-center px-6 pt-20 overflow-hidden">
      <div className="max-w-7xl mx-auto w-full grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
        
        {/* Text Content */}
        <motion.div style={{ y: y1 }} className="space-y-8 relative z-10">
          <motion.div 
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 1, type: "spring" }}
            className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-cyan-500/30 bg-cyan-500/10 text-cyan-400 text-xs font-mono uppercase tracking-widest backdrop-blur-md"
          >
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse box-shadow-glow" />
            HMM Regime Switching
          </motion.div>

          <motion.h1 
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.8 }}
            className="text-5xl md:text-8xl font-bold tracking-tighter text-white leading-[1.1]"
          >
            Algorithmic <br />
            <span className="relative">
              <span className="absolute -inset-1 blur-2xl bg-gradient-to-r from-cyan-400 to-blue-600 opacity-30" />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-600 relative">
                Quantitative Trading
              </span>
            </span>
          </motion.h1>

          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4, duration: 0.8 }}
            className="text-lg text-slate-400 max-w-lg leading-relaxed"
          >
            Stop guessing. We combine <span className="text-white font-semibold">Machine Learning</span> and advanced strategies to consistently outperform buy-and-hold on major crypto coins. Verify our edge instantly with historical backtesting.
          </motion.p>

          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6, duration: 0.8 }}
            className="flex flex-wrap gap-4"
          >
            <MagneticButton>
              <div className="px-8 py-4 bg-cyan-500 hover:bg-cyan-400 text-black font-bold rounded-xl transition-all flex items-center gap-2 shadow-[0_0_40px_-10px_rgba(6,182,212,0.5)] group">
                Get Started 
                <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
              </div>
            </MagneticButton>
            
            <MagneticButton onClick={() => router.push('/docs')}>
              <div className="px-8 py-4 bg-white/5 hover:bg-white/10 border border-white/10 text-white font-semibold rounded-xl transition-all backdrop-blur-sm flex items-center gap-2">
                Documentation
              </div>
            </MagneticButton>
          </motion.div>
        </motion.div>

        {/* 3D Spacer for Desktop */}
        <motion.div style={{ y: y2 }} className="hidden md:block h-[600px] w-full relative z-0" />
        
      </div>
    </section>
  );
}

// --- BENTO GRID WITH TILT & SPOTLIGHT ---
function BentoGridFeatures() {
  return (
    <section className="relative py-32 px-6 z-10">
      <div className="max-w-7xl mx-auto">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mb-16"
        >
          <h2 className="text-3xl md:text-5xl font-bold text-white mb-6">
            Beyond <span className="text-cyan-400">Buy & Hold</span>.
          </h2>
          <p className="text-slate-400 max-w-2xl text-lg">
             Our Hidden Markov Models detect market regimes in real-time, dynamically adjusting risk exposure to preserve capital during volatility.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 auto-rows-[240px]">
          
          {/* Large Card (2x2) */}
          <SpotlightCard className="md:col-span-1 md:row-span-2 flex flex-col justify-end group">
             <div className="absolute inset-0 bg-gradient-to-b from-transparent to-black/90 z-0" />
             <div className="absolute top-8 right-8 p-4 bg-cyan-500/10 rounded-2xl text-cyan-400 border border-cyan-500/20 backdrop-blur-md shadow-lg shadow-cyan-900/20">
               <Activity size={32} />
             </div>
             
             <div className="relative z-10 p-10">
               <h3 className="text-3xl font-bold text-white mb-4">Real-Time Analytics</h3>
               <p className="text-slate-300 text-lg mb-8 max-w-md">
                 Visualize Profit & Loss, Sharpe Ratio, and Drawdown in real-time. 
               </p>
               
               {/* Animated Chart Simulation */}
               <div className="w-full h-48 bg-black/40 rounded-xl border border-white/5 overflow-hidden relative">
                 <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-cyan-500/10 to-transparent" />
                 {/* SVG Line with animation */}
                 <svg className="absolute bottom-0 left-0 right-0 w-full h-40 text-cyan-400" preserveAspectRatio="none">
                    <motion.path 
                      d="M0,100 C100,80 200,120 300,60 S500,80 800,20"
                      fill="none" 
                      stroke="currentColor" 
                      strokeWidth="3"
                      initial={{ pathLength: 0 }}
                      animate={{ pathLength: 1 }}
                      transition={{ duration: 3, ease: "easeInOut", repeat: Infinity }}
                    />
                 </svg>
                 {/* Scanning Line */}
                 <motion.div 
                    animate={{ x: ["0%", "100%"] }}
                    transition={{ repeat: Infinity, duration: 3, ease: "linear" }}
                    className="absolute top-0 bottom-0 w-[1px] bg-cyan-400/50 shadow-[0_0_10px_rgba(6,182,212,0.8)]"
                 />
               </div>
             </div>
          </SpotlightCard>

          {/* Backtest Engine - Moved & Resized to match Real-Time Analytics */}
          <SpotlightCard className="md:col-span-1 md:row-span-2 p-10 flex flex-col justify-between group">
             <div className="relative z-10">
                <h3 className="text-3xl font-bold text-white mb-4">Backtest Engine</h3>
                <p className="text-slate-300 text-lg mb-8">Prove the edge. Compare our ML strategies against buy-and-hold from any date in history.</p>
             </div>
             <div className="w-32 h-32 bg-gradient-to-br from-blue-600/20 to-cyan-500/20 rounded-full blur-2xl absolute top-10 right-10 pointer-events-none" />
             <div className="relative z-10 h-48 w-full flex items-end justify-between gap-1 p-4 bg-black/40 border border-white/5 rounded-xl overflow-hidden backdrop-blur-sm">
                {[20, 45, 30, 80, 55, 90, 70].map((h, i) => (
                  <motion.div
                    key={i}
                    animate={{
                      height: [
                        `${h}%`,
                        `${Math.max(10, h + (i % 2 === 0 ? 20 : -15))}%`,
                        `${Math.min(90, h + (i % 2 === 0 ? -10 : 25))}%`,
                        `${h}%`
                      ]
                    }}
                    transition={{
                      duration: 2 + (i % 3) * 0.5,
                      repeat: Infinity,
                      ease: "easeInOut",
                    }}
                    className="w-full bg-gradient-to-t from-cyan-600/80 to-cyan-400 rounded-t-sm"
                  />
                ))}
             </div>
          </SpotlightCard>

          {/* Small Card 1 */}
          <SpotlightCard className="p-8 flex flex-col justify-between">
            <div className="w-12 h-12 rounded-full bg-indigo-500/10 flex items-center justify-center border border-indigo-500/20">
              <Cpu size={24} className="text-indigo-400" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white mb-2">SVR Forecasting</h3>
              <p className="text-slate-400 text-sm">Support Vector Regression models predict price targets by analyzing high-dimensional market vectors.</p>
            </div>
          </SpotlightCard>

          {/* Small Card 2 */}
          <SpotlightCard className="p-8 flex flex-col justify-between">
            <div className="w-12 h-12 rounded-full bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20">
              <Shield size={24} className="text-emerald-400" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white mb-2">Adaptive Risk</h3>
              <p className="text-slate-400 text-sm">HMM-driven sizing with an automated <span className="text-emerald-400">Kill Switch</span> to exit during extreme volatility.</p>
            </div>
          </SpotlightCard>

           {/* Dynamic Leverage */}
           <SpotlightCard className="p-8 flex flex-col justify-between">
             <div className="w-12 h-12 rounded-full bg-orange-500/10 flex items-center justify-center border border-orange-500/20 mb-4">
              <Zap size={24} className="text-orange-400" />
            </div>
             <div>
               <h3 className="text-xl font-bold text-white mb-2">Dynamic Leverage</h3>
               <p className="text-slate-400 text-sm">Features our Dynamic Leverage Accelerator adjusted by live Risk Factors.</p>
             </div>
          </SpotlightCard>

          {/* Encryption */}
          <SpotlightCard className="p-8 flex flex-col justify-between">
            <div className="w-12 h-12 rounded-full bg-purple-500/10 flex items-center justify-center border border-purple-500/20 mb-4">
              <Lock size={24} className="text-purple-400" />
            </div>
            <div>
              <h3 className="text-xl font-bold text-white mb-2">AES-256 Encryption</h3>
              <p className="text-slate-400 text-sm">Your data is secured with military-grade AES-256 encryption and Argon2 hashing.</p>
            </div>
          </SpotlightCard>

        </div>
      </div>
    </section>
  );
}

function CallToAction({ router }: { router: any }) {
  return (
    <section className="py-32 px-6 relative z-10">
      <div className="max-w-5xl mx-auto text-center">
        <SpotlightCard className="p-16 md:p-24 border-cyan-500/30 bg-gradient-to-b from-[#111]/80 to-[#050505] overflow-hidden">
          
          {/* Background Glow */}
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-cyan-500/20 blur-[100px] rounded-full pointer-events-none" />

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="relative z-10"
          >
            <h2 className="text-4xl md:text-7xl font-bold text-white mb-8 tracking-tight">
              Start <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">Trading</span>
            </h2>
            <p className="text-xl text-slate-400 mb-12 max-w-2xl mx-auto">
              Validate the alpha with a <span className="text-white font-semibold">$10,000 paper trading account</span>. Backtest from any date, and if you love the results, deploy to live trading.
            </p>
            
            <MagneticButton onClick={() => router.push("/auth")}>
              <div className="px-12 py-5 bg-white text-black font-bold rounded-full text-lg hover:scale-105 transition-transform shadow-[0_0_50px_-10px_rgba(255,255,255,0.3)]">
                Create Free Account
              </div>
            </MagneticButton>
          </motion.div>
        </SpotlightCard>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="py-12 text-center text-slate-600 text-sm relative z-10 border-t border-white/5 bg-[#050505] backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-6">
        <p>© 2025 AlgoQuant Systems.</p>
        <div className="flex gap-6">
          <a href="#" className="hover:text-cyan-400 transition-colors">Privacy</a>
          <a href="#" className="hover:text-cyan-400 transition-colors">Terms</a>
          <a href="https://www.instagram.com/algoquant_official?igsh=c2cwODEzN3R3bDRq" className="hover:text-cyan-400 transition-colors">Instagram</a>
        </div>
      </div>
    </footer>
  );
}