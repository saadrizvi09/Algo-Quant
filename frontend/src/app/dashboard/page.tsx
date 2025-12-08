"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Navbar from "@/components/navbar";
import { ArrowUpRight, Wallet, TrendingUp, Bell } from "lucide-react";

export default function DashboardPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);

  // --- PROTECT ROUTE ---
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      router.push("/");
    } else {
      setLoading(false);
    }
  }, [router]);

useEffect(() => {
  const token = localStorage.getItem("token");
  if (!token) {
    router.push("/");
  }
  // Remove setLoading(false)
}, [router]);

  return (
    <div className="min-h-screen bg-[#0B0E14] text-slate-200">
      <Navbar />

      <main className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {/* Welcome Section */}
        <div className="flex justify-between items-end border-b border-white/10 pb-6">
          <div>
            <h1 className="text-3xl font-bold text-white">Market Overview</h1>
            <p className="text-slate-400 mt-1">Welcome back, Trader.</p>
          </div>
          <div className="flex gap-3">
             <button className="px-4 py-2 bg-cyan-500/10 text-cyan-400 text-sm font-medium rounded-lg border border-cyan-500/20 hover:bg-cyan-500/20 transition">
                + New Strategy
             </button>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card 1 */}
          <div className="p-6 rounded-2xl bg-[#151B26] border border-white/5 hover:border-white/10 transition-all group">
            <div className="flex justify-between items-start mb-4">
              <div className="p-3 rounded-lg bg-blue-500/10 text-blue-400 group-hover:bg-blue-500/20 transition">
                <Wallet size={24} />
              </div>
              <span className="text-emerald-400 flex items-center text-xs font-bold bg-emerald-400/10 px-2 py-1 rounded-full">
                +12.5% <ArrowUpRight size={12} className="ml-1" />
              </span>
            </div>
            <h3 className="text-slate-400 text-sm font-medium">Total Portfolio</h3>
            <p className="text-2xl font-bold text-white mt-1">$124,592.00</p>
          </div>

          {/* Card 2 */}
          <div className="p-6 rounded-2xl bg-[#151B26] border border-white/5 hover:border-white/10 transition-all group">
            <div className="flex justify-between items-start mb-4">
              <div className="p-3 rounded-lg bg-purple-500/10 text-purple-400 group-hover:bg-purple-500/20 transition">
                <TrendingUp size={24} />
              </div>
              <span className="text-emerald-400 flex items-center text-xs font-bold bg-emerald-400/10 px-2 py-1 rounded-full">
                +5.2% <ArrowUpRight size={12} className="ml-1" />
              </span>
            </div>
            <h3 className="text-slate-400 text-sm font-medium">Active Strategies</h3>
            <p className="text-2xl font-bold text-white mt-1">8 Running</p>
          </div>

          {/* Card 3 */}
          <div className="p-6 rounded-2xl bg-[#151B26] border border-white/5 hover:border-white/10 transition-all group">
            <div className="flex justify-between items-start mb-4">
              <div className="p-3 rounded-lg bg-orange-500/10 text-orange-400 group-hover:bg-orange-500/20 transition">
                <Bell size={24} />
              </div>
            </div>
            <h3 className="text-slate-400 text-sm font-medium">Recent Alerts</h3>
            <p className="text-2xl font-bold text-white mt-1">3 New Signals</p>
          </div>
        </div>

        {/* Recent Activity Table (Mock) */}
        <div className="bg-[#151B26] border border-white/5 rounded-2xl overflow-hidden">
          <div className="p-6 border-b border-white/5">
            <h3 className="font-semibold text-white">Recent Backtests</h3>
          </div>
          <table className="w-full text-left text-sm text-slate-400">
            <thead className="bg-white/5 text-xs uppercase font-medium text-slate-300">
              <tr>
                <th className="px-6 py-4">Strategy</th>
                <th className="px-6 py-4">Ticker</th>
                <th className="px-6 py-4">Return</th>
                <th className="px-6 py-4">Date</th>
                <th className="px-6 py-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              <tr className="hover:bg-white/5 transition">
                <td className="px-6 py-4 font-medium text-white">HMM Momentum</td>
                <td className="px-6 py-4">BTC-USD</td>
                <td className="px-6 py-4 text-emerald-400">+154.2%</td>
                <td className="px-6 py-4">Dec 08, 2025</td>
                <td className="px-6 py-4"><span className="px-2 py-1 rounded-full bg-emerald-400/10 text-emerald-400 text-xs font-bold">Completed</span></td>
              </tr>
              <tr className="hover:bg-white/5 transition">
                <td className="px-6 py-4 font-medium text-white">Mean Reversion</td>
                <td className="px-6 py-4">AAPL</td>
                <td className="px-6 py-4 text-red-400">-2.1%</td>
                <td className="px-6 py-4">Dec 07, 2025</td>
                <td className="px-6 py-4"><span className="px-2 py-1 rounded-full bg-emerald-400/10 text-emerald-400 text-xs font-bold">Completed</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </main>
    </div>
  );
}