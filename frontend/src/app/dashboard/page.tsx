"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import Navbar from "@/components/navbar";
import { API_URL } from "@/lib/config";
import {
  ArrowUpRight,
  ArrowDownRight,
  Wallet,
  TrendingUp,
  TrendingDown,
  Activity,
  RefreshCw,
  Clock,
  BarChart3,
  Zap,
} from "lucide-react";

interface Holding {
  asset: string;
  quantity: number;
  value_usdt: number;
}

interface Trade {
  symbol: string;
  side: string;
  price: number;
  quantity: number;
  total: number;
  time: string;
}

interface Session {
  session_id: string;
  strategy: string;
  symbol: string;
  is_running: boolean;
  pnl: number;
  trades_count: number;
}

export default function DashboardPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const [portfolio, setPortfolio] = useState<{
    total_value_usdt: number;
    holdings: Holding[];
  } | null>(null);
  const [recentTrades, setRecentTrades] = useState<Trade[]>([]);
  const [activeSessions, setActiveSessions] = useState<Session[]>([]);

  const getAuthHeaders = useCallback(() => {
    const token = localStorage.getItem("token");
    return {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    };
  }, []);

  const fetchPortfolio = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/simulated/portfolio`, {
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        // Convert simulated portfolio format to dashboard format
        const holdings = data.assets.map((asset: any) => ({
          asset: asset.symbol,
          quantity: asset.balance,
          value_usdt: asset.value_usdt
        }));
        setPortfolio({ 
          total_value_usdt: data.total_value_usdt,
          holdings: holdings 
        });
      }
    } catch (err) {
      console.error("Failed to fetch portfolio", err);
    }
  }, [getAuthHeaders]);

  const fetchRecentTrades = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/simulated/trades?limit=10`, {
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        setRecentTrades(data.trades || []);
      }
    } catch (err) {
      console.error("Failed to fetch trades", err);
    }
  }, [getAuthHeaders]);

  const fetchSessions = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/simulated/sessions`, {
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        setActiveSessions(data.sessions || []);
      }
    } catch (err) {
      console.error("Failed to fetch sessions", err);
    }
  }, [getAuthHeaders]);

  const refreshAll = useCallback(async () => {
    setRefreshing(true);
    await Promise.all([fetchPortfolio(), fetchRecentTrades(), fetchSessions()]);
    setRefreshing(false);
  }, [fetchPortfolio, fetchRecentTrades, fetchSessions]);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      router.push("/");
      return;
    }

    setLoading(false);
    
    // Add small delay to ensure backend is ready after login
    const initializeData = async () => {
      await new Promise(resolve => setTimeout(resolve, 200));
      refreshAll();
    };

    initializeData();

    const interval = setInterval(refreshAll, 30000);
    return () => clearInterval(interval);
  }, [router, refreshAll]);

  const totalPnL = activeSessions.reduce((sum, s) => sum + s.pnl, 0);
  const runningCount = activeSessions.filter((s) => s.is_running).length;

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0B0E14] flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0B0E14] text-slate-200">
      <Navbar />

      <main className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {/* Welcome Section */}
        <div className="flex justify-between items-end border-b border-white/10 pb-6">
          <div>
            <h1 className="text-3xl font-bold text-white">Dashboard</h1>
            <p className="text-slate-400 mt-1">Real-time portfolio overview</p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={refreshAll}
              disabled={refreshing}
              className="px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-slate-300 hover:bg-white/10 transition flex items-center gap-2"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin" : ""}`} />
              Refresh
            </button>
            <div className="px-3 py-2 bg-cyan-500/10 border border-cyan-500/20 rounded-lg text-cyan-400 text-sm flex items-center gap-2">
              <Wallet size={14} />
              Simulated Mode
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {/* Portfolio Value */}
          <div className="p-6 rounded-2xl bg-gradient-to-br from-cyan-500/10 to-cyan-500/5 border border-cyan-500/20 hover:border-cyan-500/40 transition-all group">
            <div className="flex justify-between items-start mb-4">
              <div className="p-3 rounded-lg bg-cyan-500/20 text-cyan-400">
                <Wallet size={24} />
              </div>
            </div>
            <h3 className="text-slate-400 text-sm font-medium">Portfolio Value</h3>
            <p className="text-2xl font-bold text-white mt-1">
              ${portfolio?.total_value_usdt?.toFixed(2) || "0.00"}
            </p>
          </div>

          {/* Holdings */}
          <div className="p-6 rounded-2xl bg-gradient-to-br from-purple-500/10 to-purple-500/5 border border-purple-500/20 hover:border-purple-500/40 transition-all group">
            <div className="flex justify-between items-start mb-4">
              <div className="p-3 rounded-lg bg-purple-500/20 text-purple-400">
                <BarChart3 size={24} />
              </div>
            </div>
            <h3 className="text-slate-400 text-sm font-medium">Assets Held</h3>
            <p className="text-2xl font-bold text-white mt-1">
              {portfolio?.holdings?.length || 0}
            </p>
          </div>

          {/* Active Sessions */}
          <div className="p-6 rounded-2xl bg-gradient-to-br from-blue-500/10 to-blue-500/5 border border-blue-500/20 hover:border-blue-500/40 transition-all group">
            <div className="flex justify-between items-start mb-4">
              <div className="p-3 rounded-lg bg-blue-500/20 text-blue-400">
                <Activity size={24} />
              </div>
              {runningCount > 0 && (
                <span className="text-emerald-400 flex items-center text-xs font-bold bg-emerald-400/10 px-2 py-1 rounded-full">
                  Live
                </span>
              )}
            </div>
            <h3 className="text-slate-400 text-sm font-medium">Active Bots</h3>
            <p className="text-2xl font-bold text-white mt-1">{runningCount} Running</p>
          </div>

          {/* Total P&L */}
          <div className={`p-6 rounded-2xl border transition-all group ${
            totalPnL >= 0 
              ? "bg-gradient-to-br from-emerald-500/10 to-emerald-500/5 border-emerald-500/20 hover:border-emerald-500/40"
              : "bg-gradient-to-br from-red-500/10 to-red-500/5 border-red-500/20 hover:border-red-500/40"
          }`}>
            <div className="flex justify-between items-start mb-4">
              <div className={`p-3 rounded-lg ${totalPnL >= 0 ? "bg-emerald-500/20 text-emerald-400" : "bg-red-500/20 text-red-400"}`}>
                {totalPnL >= 0 ? <TrendingUp size={24} /> : <TrendingDown size={24} />}
              </div>
              <span className={`flex items-center text-xs font-bold px-2 py-1 rounded-full ${
                totalPnL >= 0 ? "text-emerald-400 bg-emerald-400/10" : "text-red-400 bg-red-400/10"
              }`}>
                {totalPnL >= 0 ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
              </span>
            </div>
            <h3 className="text-slate-400 text-sm font-medium">Session P&L</h3>
            <p className={`text-2xl font-bold mt-1 ${totalPnL >= 0 ? "text-emerald-400" : "text-red-400"}`}>
              {totalPnL >= 0 ? "+" : ""}${totalPnL.toFixed(2)}
            </p>
          </div>
        </div>

        {/* Holdings Table */}
        {portfolio?.holdings && portfolio.holdings.length > 0 && (
          <div className="bg-[#151B26] border border-white/5 rounded-2xl overflow-hidden">
            <div className="p-6 border-b border-white/5">
              <h3 className="font-semibold text-white flex items-center gap-2">
                <Wallet className="w-5 h-5 text-cyan-400" />
                Current Holdings
              </h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-[#0B0E14] text-xs uppercase font-medium text-slate-400">
                  <tr>
                    <th className="px-6 py-4">Asset</th>
                    <th className="px-6 py-4 text-right">Quantity</th>
                    <th className="px-6 py-4 text-right">Value (USDT)</th>
                    <th className="px-6 py-4 text-right">% of Portfolio</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {portfolio.holdings.map((holding) => (
                    <tr key={holding.asset} className="hover:bg-white/5 transition">
                      <td className="px-6 py-4 font-medium text-white">{holding.asset}</td>
                      <td className="px-6 py-4 text-right text-slate-300">
                        {holding.quantity.toFixed(8)}
                      </td>
                      <td className="px-6 py-4 text-right font-semibold text-white">
                        ${holding.value_usdt.toFixed(2)}
                      </td>
                      <td className="px-6 py-4 text-right text-slate-400">
                        {((holding.value_usdt / (portfolio?.total_value_usdt || 1)) * 100).toFixed(1)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Recent Trades Table */}
        <div className="bg-[#151B26] border border-white/5 rounded-2xl overflow-hidden">
          <div className="p-6 border-b border-white/5">
            <h3 className="font-semibold text-white flex items-center gap-2">
              <Clock className="w-5 h-5 text-cyan-400" />
              Recent Trades
            </h3>
          </div>
          
          {recentTrades.length === 0 ? (
            <div className="text-center py-12 text-slate-400">
              <Clock className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No recent trades</p>
              <p className="text-sm text-slate-500 mt-1">Start a live trading session to see trades here</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-[#0B0E14] text-xs uppercase font-medium text-slate-400">
                  <tr>
                    <th className="px-6 py-4">Time</th>
                    <th className="px-6 py-4">Symbol</th>
                    <th className="px-6 py-4 text-center">Side</th>
                    <th className="px-6 py-4 text-right">Price</th>
                    <th className="px-6 py-4 text-right">Quantity</th>
                    <th className="px-6 py-4 text-right">Total</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {recentTrades.map((trade, idx) => (
                    <tr key={idx} className="hover:bg-white/5 transition">
                      <td className="px-6 py-4 text-slate-400">
                        {new Date(trade.time).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 font-medium text-white">{trade.symbol}</td>
                      <td className="px-6 py-4 text-center">
                        <span
                          className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-bold ${
                            trade.side === "BUY"
                              ? "bg-emerald-400/10 text-emerald-400"
                              : "bg-red-400/10 text-red-400"
                          }`}
                        >
                          {trade.side === "BUY" ? (
                            <TrendingUp className="w-3 h-3" />
                          ) : (
                            <TrendingDown className="w-3 h-3" />
                          )}
                          {trade.side}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right text-slate-300">
                        ${trade.price.toFixed(2)}
                      </td>
                      <td className="px-6 py-4 text-right text-slate-300">
                        {trade.quantity.toFixed(6)}
                      </td>
                      <td className="px-6 py-4 text-right font-semibold text-white">
                        ${trade.total.toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Active Sessions */}
        {activeSessions.length > 0 && (
          <div className="bg-[#151B26] border border-white/5 rounded-2xl overflow-hidden">
            <div className="p-6 border-b border-white/5">
              <h3 className="font-semibold text-white flex items-center gap-2">
                <Activity className="w-5 h-5 text-cyan-400" />
                Trading Sessions
              </h3>
            </div>
            <div className="p-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {activeSessions.map((session) => (
                <div
                  key={session.session_id}
                  className="p-4 bg-[#0B0E14] rounded-xl border border-white/5"
                >
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <div className="font-semibold text-white">{session.symbol}</div>
                      <div className="text-xs text-slate-400 capitalize">
                        {session.strategy} Strategy
                      </div>
                    </div>
                    <div
                      className={`px-2 py-1 rounded-full text-xs ${
                        session.is_running
                          ? "bg-emerald-500/20 text-emerald-400"
                          : "bg-slate-500/20 text-slate-400"
                      }`}
                    >
                      {session.is_running ? "Running" : "Stopped"}
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <div className="text-slate-500 text-xs">Trades</div>
                      <div className="text-white">{session.trades_count}</div>
                    </div>
                    <div>
                      <div className="text-slate-500 text-xs">P&L</div>
                      <div
                        className={
                          session.pnl >= 0 ? "text-emerald-400" : "text-red-400"
                        }
                      >
                        {session.pnl >= 0 ? "+" : ""}${session.pnl.toFixed(2)}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
