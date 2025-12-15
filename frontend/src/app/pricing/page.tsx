"use client";

import React from "react";
import { ArrowLeft, Check, Cpu, Zap } from "lucide-react";
import { useRouter } from "next/navigation";

export default function PricingPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-[#0B0E14] text-slate-200 font-sans selection:bg-cyan-500/30 relative overflow-hidden">
      
      {/* Background Effects */}
      <div className="absolute top-[-10%] left-1/2 -translate-x-1/2 w-[800px] h-[800px] bg-cyan-500/10 rounded-full blur-[120px] pointer-events-none" />
      
      {/* Navigation */}
      <nav className="relative z-50 border-b border-white/10 bg-[#0B0E14]/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div 
            onClick={() => router.push("/")}
            className="flex items-center gap-2 cursor-pointer hover:opacity-80 transition-opacity"
          >
            <div className="w-8 h-8 bg-gradient-to-tr from-cyan-500 to-blue-600 rounded-lg flex items-center justify-center">
              <Cpu size={16} className="text-white" />
            </div>
            <span className="font-bold text-white tracking-tight">AlgoQuant <span className="text-cyan-400">Pricing</span></span>
          </div>
          <button 
            onClick={() => router.push("/")}
            className="text-sm font-medium text-slate-400 hover:text-white flex items-center gap-2 transition-colors"
          >
            <ArrowLeft size={16} /> Back to Home
          </button>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-6 py-20 relative z-10">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h1 className="text-4xl md:text-6xl font-bold text-white mb-6">
            Simple, Transparent <span className="text-cyan-400">Pricing</span>
          </h1>
          <p className="text-xl text-slate-400">
            We are currently in <span className="text-white font-semibold">Public Beta</span>. All features are completely free while we refine our HMM models.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          
          {/* Free Tier */}
          <div className="relative p-8 rounded-3xl bg-[#151B26] border border-cyan-500/50 shadow-[0_0_40px_-10px_rgba(6,182,212,0.3)] flex flex-col">
            <div className="absolute top-0 right-0 bg-cyan-500 text-black text-xs font-bold px-3 py-1 rounded-bl-xl rounded-tr-2xl">
              CURRENTLY ACTIVE
            </div>
            <h3 className="text-2xl font-bold text-white mb-2">Beta Access</h3>
            <div className="flex items-baseline gap-1 mb-6">
              <span className="text-4xl font-bold text-white">$0</span>
              <span className="text-slate-500">/month</span>
            </div>
            <p className="text-slate-400 mb-8 text-sm">Full access to our institutional-grade backtesting engine and paper trading environment.</p>
            
            <ul className="space-y-4 mb-8 flex-1">
              {['Unlimited Backtests', 'HMM Regime Detection', '$10k Paper Trading Account', 'Python & Rust SDK Access', 'Community Support'].map((feature) => (
                <li key={feature} className="flex items-center gap-3 text-sm text-slate-300">
                  <div className="w-5 h-5 rounded-full bg-cyan-500/20 flex items-center justify-center">
                    <Check size={12} className="text-cyan-400" />
                  </div>
                  {feature}
                </li>
              ))}
            </ul>

            <button onClick={() => router.push('/auth')} className="w-full py-4 bg-cyan-500 hover:bg-cyan-400 text-black font-bold rounded-xl transition-all">
              Start Trading Now
            </button>
          </div>

          {/* Pro Tier (Coming Soon) */}
          <div className="relative p-8 rounded-3xl bg-[#151B26]/50 border border-white/5 flex flex-col opacity-70 hover:opacity-100 transition-opacity">
            <div className="absolute top-6 right-8 flex items-center gap-2 text-purple-400 text-xs font-bold border border-purple-500/30 px-3 py-1 rounded-full bg-purple-500/10">
              <Zap size={12} /> COMING SOON
            </div>
            <h3 className="text-2xl font-bold text-white mb-2">Pro Quant</h3>
            <div className="flex items-baseline gap-1 mb-6">
              <span className="text-4xl font-bold text-white">$4.99</span>
              <span className="text-slate-500">/month</span>
            </div>
            <p className="text-slate-400 mb-8 text-sm">For serious quants requiring dedicated infrastructure and lower latency.</p>
            
            <ul className="space-y-4 mb-8 flex-1">
              {['Everything in Beta', 'Dedicated GPU Nodes', 'Sub-millisecond Latency', 'Priority Support', 'Live Trading Execution'].map((feature) => (
                <li key={feature} className="flex items-center gap-3 text-sm text-slate-500">
                  <Check size={16} className="text-slate-600" />
                  {feature}
                </li>
              ))}
            </ul>

            <button disabled className="w-full py-4 bg-white/5 border border-white/10 text-slate-400 font-bold rounded-xl cursor-not-allowed">
              Join Waitlist
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
