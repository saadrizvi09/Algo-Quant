"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, Lock, Mail, Activity, Cpu, Zap } from "lucide-react";

export default function HomePage() {
  const router = useRouter();
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  // Form State
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setSuccessMsg("");

    const endpoint = isLogin ? "/api/login" : "/api/signup";
    const url = `http://127.0.0.1:8000${endpoint}`;

    try {
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Authentication failed");
      }

      if (isLogin) {
        // --- LOGIN SUCCESS ---
        // 1. Store Token
        localStorage.setItem("token", data.access_token);
        // 2. Wait a bit to ensure token is saved
        await new Promise(resolve => setTimeout(resolve, 100));
        // 3. Redirect to Backtest Page
        router.push("/backtest");
      } else {
        // --- SIGNUP SUCCESS ---
        // Auto-login after successful signup
        try {
          const loginRes = await fetch("http://127.0.0.1:8000/api/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(formData),
          });
          
          const loginData = await loginRes.json();
          
          if (loginRes.ok) {
            localStorage.setItem("token", loginData.access_token);
            await new Promise(resolve => setTimeout(resolve, 100));
            router.push("/backtest");
          } else {
            // Fallback to manual login
            setSuccessMsg("Account created! Logging you in...");
            setIsLogin(true);
          }
        } catch (err) {
          // Fallback to manual login
          setSuccessMsg("Account created! Please login.");
          setIsLogin(true);
          setFormData({ email: "", password: "" });
        }
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0B0E14] text-slate-200 font-sans selection:bg-cyan-500/30 flex items-center justify-center relative overflow-hidden">
      
      {/* --- Background Effects --- */}
      <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] bg-blue-600/10 rounded-full blur-[120px] pointer-events-none animate-pulse" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[500px] h-[500px] bg-cyan-500/10 rounded-full blur-[120px] pointer-events-none animate-pulse" />
      <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 pointer-events-none"></div>

      <div className="max-w-6xl w-full grid grid-cols-1 lg:grid-cols-2 gap-16 px-6 z-10">
        
        {/* --- Left Column: Hero Content --- */}
        <div className="flex flex-col justify-center space-y-8">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-linear-to-r from-cyan-500/10 to-blue-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-mono mb-6 animate-pulse">
              <Zap size={14} />
              <span>24/7 Live</span>
            </div>
            <h1 className="text-6xl font-bold tracking-tighter text-white leading-tight">
              Algo<span className="text-transparent bg-clip-text bg-linear-to-r from-cyan-400 via-blue-500 to-purple-500">Quant</span>
            </h1>
            <p className="text-slate-400 text-xl mt-4 leading-relaxed max-w-md">
              Quantitative algorithmic trading platform. Backtest my strategies, and if you love the results, execute paper trades using those strategies(real trading coming soon). Totally free for now.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 rounded-xl bg-linear-to-br from-cyan-500/10 to-transparent border border-cyan-500/20 backdrop-blur-sm hover:border-cyan-500/40 transition-all group">
              <Activity className="text-cyan-400 mb-2 group-hover:scale-110 transition-transform" />
              <h3 className="text-white font-semibold">Live Trading</h3>
              <p className="text-xs text-slate-500 mt-1">Real-time simulation</p>
            </div>
            <div className="p-4 rounded-xl bg-linear-to-br from-blue-500/10 to-transparent border border-blue-500/20 backdrop-blur-sm hover:border-blue-500/40 transition-all group">
              <Cpu className="text-blue-400 mb-2 group-hover:scale-110 transition-transform" />
              <h3 className="text-white font-semibold">Proven Strategy</h3>
              <p className="text-xs text-slate-500 mt-1">HMM Regime Switching</p>
            </div>
          </div>

          {/* Feature Pills */}
          <div className="flex flex-wrap gap-2">
            <div className="px-3 py-1 bg-emerald-500/10 border border-emerald-500/20 rounded-full text-emerald-400 text-xs">
              ✓ $10,000 Paper Trading
            </div>
            <div className="px-3 py-1 bg-purple-500/10 border border-purple-500/20 rounded-full text-purple-400 text-xs">
              ✓ No Credit Card
            </div>
            <div className="px-3 py-1 bg-blue-500/10 border border-blue-500/20 rounded-full text-blue-400 text-xs">
              ✓ Real Market Data
            </div>
          </div>
        </div>

        {/* --- Right Column: Auth Card --- */}
        <div className="flex items-center justify-center">
          <div className="w-full max-w-md bg-[#151B26]/80 backdrop-blur-xl border border-white/10 p-8 rounded-3xl shadow-2xl ring-1 ring-white/5">
            
            {/* Toggle Header */}
            <div className="flex p-1 bg-[#0B0E14] rounded-xl mb-8 border border-white/5">
              <button
                onClick={() => setIsLogin(true)}
                className={`flex-1 py-2.5 rounded-lg text-sm font-medium transition-all duration-300 ${
                  isLogin
                    ? "bg-[#1E293B] text-white shadow-lg"
                    : "text-slate-500 hover:text-slate-300"
                }`}
              >
                Login
              </button>
              <button
                onClick={() => setIsLogin(false)}
                className={`flex-1 py-2.5 rounded-lg text-sm font-medium transition-all duration-300 ${
                  !isLogin
                    ? "bg-[#1E293B] text-white shadow-lg"
                    : "text-slate-500 hover:text-slate-300"
                }`}
              >
                Sign Up
              </button>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-5">
              
              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider flex items-center gap-2">
                  <Mail size={14} /> Email
                </label>
                <input
                  name="email"
                  type="email"
                  required
                  value={formData.email}
                  onChange={handleChange}
                  className="w-full bg-[#0B0E14] border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all placeholder:text-slate-700"
                  placeholder="trader@algoquant.com"
                />
              </div>

              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider flex items-center gap-2">
                  <Lock size={14} /> Password
                </label>
                <input
                  name="password"
                  type="password"
                  required
                  value={formData.password}
                  onChange={handleChange}
                  className="w-full bg-[#0B0E14] border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 transition-all placeholder:text-slate-700"
                  placeholder="••••••••"
                />
              </div>

              {/* Messages */}
              {error && (
                <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm text-center">
                  {error}
                </div>
              )}
              {successMsg && (
                <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm text-center">
                  {successMsg}
                </div>
              )}

              <button
                disabled={loading}
                className="w-full bg-linear-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-bold py-4 rounded-xl transition-all transform hover:scale-[1.02] active:scale-[0.98] shadow-lg shadow-cyan-500/20 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <span className="flex items-center gap-2">
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Processing...
                  </span>
                ) : (
                  <>
                    {isLogin ? "Login" : "Create Free Account"}
                    <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
                  </>
                )}
              </button>
            </form>

            <div className="mt-6 space-y-3">
              <div className="flex items-center justify-center gap-2 text-xs text-slate-500">
                <Lock size={12} />
                <span>Secured with JWT & bcrypt encryption</span>
              </div>
              
              {/* Quick Stats */}
              <div className="grid grid-cols-3 gap-2 pt-4 border-t border-white/5">
                <div className="text-center">
                  <div className="text-cyan-400 font-bold">$10K</div>
                  <div className="text-xs text-slate-600">Starting Capital</div>
                </div>
                <div className="text-center">
                  <div className="text-emerald-400 font-bold">100%</div>
                  <div className="text-xs text-slate-600">Free </div>
                </div>
                <div className="text-center">
                  <div className="text-purple-400 font-bold">24/7</div>
                  <div className="text-xs text-slate-600">Auto Trading</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}