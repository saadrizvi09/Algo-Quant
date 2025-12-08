"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Activity, LayoutDashboard, LogOut, Zap } from "lucide-react";

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();

  const handleLogout = () => {
    localStorage.removeItem("token");
    router.push("/");
  };

  const isActive = (path: string) => pathname === path;

  return (
    <nav className="w-full bg-[#0B0E14] border-b border-white/10 sticky top-0 z-50 backdrop-blur-md bg-opacity-80">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center text-white font-bold">
            <Zap size={18} fill="currentColor" />
          </div>
          <span className="text-xl font-bold text-white tracking-tight">
            Algo<span className="text-cyan-400">Quant</span>
          </span>
        </div>

        {/* Navigation Links */}
        <div className="flex items-center gap-1 bg-white/5 p-1 rounded-full border border-white/5">
          <Link href="/dashboard">
            <div
              className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all flex items-center gap-2 ${
                isActive("/dashboard")
                  ? "bg-[#1E293B] text-cyan-400 shadow-sm border border-white/5"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <LayoutDashboard size={16} />
              Dashboard
            </div>
          </Link>
          <Link href="/backtest">
            <div
              className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all flex items-center gap-2 ${
                isActive("/backtest")
                  ? "bg-[#1E293B] text-cyan-400 shadow-sm border border-white/5"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <Activity size={16} />
              Backtest Engine
            </div>
          </Link>
        </div>

        {/* Logout Button */}
        <button
          onClick={handleLogout}
          className="text-slate-400 hover:text-red-400 transition-colors flex items-center gap-2 text-sm font-medium"
        >
          <LogOut size={16} />
          <span className="hidden sm:inline">Logout</span>
        </button>
      </div>
    </nav>
  );
}