"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Activity, LayoutDashboard, LogOut, Zap, Bot, Menu, X, TrendingUp } from "lucide-react";
import { useState } from "react";

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = () => {
    localStorage.removeItem("token");
    router.push("/");
    setMobileMenuOpen(false);
  };

  const isActive = (path: string) => pathname === path;

  const navLinks = [
    { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { href: "/market", label: "Market", icon: TrendingUp },
    { href: "/backtest", label: "Backtest", icon: Activity },
    { href: "/livetrading", label: "Trading Bot", icon: Bot },
  ];

  return (
    <nav className="w-full bg-[#0B0E14] border-b border-white/10 sticky top-0 z-50 backdrop-blur-md bg-opacity-80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link href="/dashboard" className="flex items-center gap-2 flex-shrink-0">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center text-white font-bold">
            <Zap size={18} fill="currentColor" />
          </div>
          <span className="text-lg sm:text-xl font-bold text-white tracking-tight">
            Algo<span className="text-cyan-400">Quant</span>
          </span>
        </Link>

        {/* Desktop Navigation Links */}
        <div className="hidden md:flex items-center gap-1 bg-white/5 p-1 rounded-full border border-white/5">
          {navLinks.map(({ href, label, icon: Icon }) => (
            <Link key={href} href={href}>
              <div
                className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all flex items-center gap-2 ${
                  isActive(href)
                    ? "bg-[#1E293B] text-cyan-400 shadow-sm border border-white/5"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                <Icon size={16} />
                {label}
              </div>
            </Link>
          ))}
        </div>

        {/* Desktop Logout Button */}
        <button
          onClick={handleLogout}
          className="hidden md:flex text-slate-400 hover:text-red-400 transition-colors items-center gap-2 text-sm font-medium"
        >
          <LogOut size={16} />
          <span>Logout</span>
        </button>

        {/* Mobile Menu Button */}
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="md:hidden text-slate-400 hover:text-white transition-colors p-2"
          aria-label="Toggle menu"
        >
          {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden absolute top-16 left-0 right-0 bg-[#0B0E14] border-b border-white/10 shadow-xl">
          <div className="px-4 py-4 space-y-2">
            {navLinks.map(({ href, label, icon: Icon }) => (
              <Link key={href} href={href} onClick={() => setMobileMenuOpen(false)}>
                <div
                  className={`px-4 py-3 rounded-lg text-sm font-medium transition-all flex items-center gap-3 ${
                    isActive(href)
                      ? "bg-[#1E293B] text-cyan-400 border border-white/5"
                      : "text-slate-400 hover:text-white hover:bg-white/5"
                  }`}
                >
                  <Icon size={18} />
                  {label}
                </div>
              </Link>
            ))}
            <button
              onClick={handleLogout}
              className="w-full px-4 py-3 rounded-lg text-sm font-medium transition-all flex items-center gap-3 text-slate-400 hover:text-red-400 hover:bg-white/5"
            >
              <LogOut size={18} />
              Logout
            </button>
          </div>
        </div>
      )}
    </nav>
  );
}