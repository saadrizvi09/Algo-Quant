"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { API_URL } from "@/lib/config";
import {
  Play,
  Square,
  Wallet,
  TrendingUp,
  TrendingDown,
  Clock,
  Activity,
  ChevronDown,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  Zap,
  BarChart3,
  DollarSign,
  Target,
  Timer,
} from "lucide-react";
import Navbar from "@/components/navbar";

interface Strategy {
  id: string;
  name: string;
  description: string;
  risk_level: string;
  requires_symbol?: boolean;
}

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
  trade_amount: number;
  is_running: boolean;
  position: string;
  trades_count: number;
  pnl: number;
  elapsed_minutes: number;
  remaining_minutes: number;
}

const CRYPTO_PAIRS = [
  { symbol: "BTCUSDT", name: "Bitcoin", logo: "₿", color: "#F7931A" },
  { symbol: "ETHUSDT", name: "Ethereum", logo: "Ξ", color: "#627EEA" },
  { symbol: "BNBUSDT", name: "BNB", logo: "⬡", color: "#F3BA2F" },
  { symbol: "SOLUSDT", name: "Solana", logo: "◎", color: "#14F195" },
];

const RISK_COLORS: Record<string, string> = {
  "Low": "text-green-400",
  "Medium": "text-yellow-400",
  "Medium-High": "text-orange-400",
  "High": "text-red-400",
};

export default function LiveTradingPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Data states
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [portfolio, setPortfolio] = useState<{ total_value_usdt: number; holdings: Holding[] } | null>(null);
  const [recentTrades, setRecentTrades] = useState<Trade[]>([]);
  const [activeSessions, setActiveSessions] = useState<Session[]>([]);

  // Form states
  const [selectedStrategy, setSelectedStrategy] = useState<string>("");
  const [selectedSymbol, setSelectedSymbol] = useState<string>("BTCUSDT");
  const [tradeAmount, setTradeAmount] = useState<number>(100);
  const [duration, setDuration] = useState<number>(60);
  const [durationUnit, setDurationUnit] = useState<string>("minutes");

  // UI states
  const [showStrategyDropdown, setShowStrategyDropdown] = useState(false);
  const [showSymbolDropdown, setShowSymbolDropdown] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const getAuthHeaders = useCallback(() => {
    const token = localStorage.getItem("token");
    return {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    };
  }, []);

  const fetchStrategies = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/live/strategies`, {
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        setStrategies(data.strategies);
        if (data.strategies.length > 0 && !selectedStrategy) {
          setSelectedStrategy(data.strategies[0].id);
        }
      }
    } catch (err) {
      console.error("Failed to fetch strategies", err);
    }
  }, [getAuthHeaders, selectedStrategy]);

  const fetchPortfolio = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/simulated/portfolio`, {
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        // Convert simulated portfolio format to live format
        const holdings = data.assets.map((asset: any) => ({
          asset: asset.symbol,
          quantity: asset.balance,
          value_usdt: asset.value_usdt
        }));
        setPortfolio({ 
          total_value_usdt: data.total_value_usdt,
          holdings: holdings 
        });
      } else if (res.status === 401) {
        // Silent fail on auth errors during initial load
        console.warn("Authentication required for portfolio");
        setPortfolio({ total_value_usdt: 0, holdings: [] });
      } else {
        // Set default portfolio on error
        setPortfolio({ total_value_usdt: 0, holdings: [] });
      }
    } catch (err) {
      // Silent fail on network errors during initial load
      console.warn("Failed to fetch portfolio", err);
      // Set default portfolio on error to prevent UI issues
      setPortfolio({ total_value_usdt: 0, holdings: [] });
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

    fetchStrategies();
    refreshAll();

    // Refresh data every 30 seconds
    const interval = setInterval(refreshAll, 30000);
    return () => clearInterval(interval);
  }, [router, fetchStrategies, refreshAll]);

  const startTrading = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const res = await fetch(`${API_URL}/api/simulated/start`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({
          strategy: selectedStrategy,
          symbol: selectedSymbol,
          trade_amount: tradeAmount,
          duration: duration,
          duration_unit: durationUnit,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Failed to start trading");
      }

      setSuccess(data.message);
      await fetchSessions();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const stopTrading = async (sessionId: string) => {
    try {
      const res = await fetch(`${API_URL}/api/simulated/stop/${sessionId}`, {
        method: "POST",
        headers: getAuthHeaders(),
      });

      if (res.ok) {
        setSuccess("Trading session stopped");
        await refreshAll();
      }
    } catch (err) {
      setError("Failed to stop trading session");
    }
  };

  const selectedStrategyData = strategies.find((s) => s.id === selectedStrategy);
  const selectedSymbolData = CRYPTO_PAIRS.find((p) => p.symbol === selectedSymbol);
  const requiresSymbol = selectedStrategyData?.requires_symbol !== false;

  return (
    <div className="min-h-screen bg-[#0B0E14] text-slate-200">
      <Navbar />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-8 space-y-6 sm:space-y-8">
        {/* Header */}
        <div className="flex justify-between items-end border-b border-white/10 pb-6">
          <div>
            <h1 className="text-4xl font-bold text-white">Live Trading</h1>
            <p className="text-slate-400 mt-2">
              Paper trading with $10,000 starting capital - Real strategies, simulated execution
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={refreshAll}
              disabled={refreshing}
              className="px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-slate-300 hover:bg-white/10 transition flex items-center gap-2"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin" : ""}`} />
              Refresh
            </button>
            <div className="px-3 py-1 bg-cyan-500/10 border border-cyan-500/20 rounded-lg text-cyan-400 text-sm flex items-center gap-2">
              <Wallet size={14} />
              Simulated Mode
            </div>
          </div>
        </div>

        {/* Alerts */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/20 rounded-2xl p-4 flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-400" />
            <p className="text-red-400">{error}</p>
          </div>
        )}
        {success && (
          <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-2xl p-4 flex items-center gap-3">
            <CheckCircle className="w-5 h-5 text-emerald-400" />
            <p className="text-emerald-400">{success}</p>
          </div>
        )}

        {/* Portfolio Overview */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-6 rounded-2xl bg-gradient-to-br from-cyan-500/10 to-cyan-500/5 border border-cyan-500/20">
            <div className="flex justify-between items-start mb-3">
              <div className="p-2.5 rounded-xl bg-cyan-500/20 text-cyan-400">
                <Wallet size={20} />
              </div>
            </div>
            <h3 className="text-slate-400 text-xs font-medium uppercase">Portfolio Value</h3>
            <p className="text-3xl font-bold text-cyan-400 mt-2">
              ${portfolio?.total_value_usdt?.toFixed(2) || "0.00"}
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-gradient-to-br from-purple-500/10 to-purple-500/5 border border-purple-500/20">
            <div className="flex justify-between items-start mb-3">
              <div className="p-2.5 rounded-xl bg-purple-500/20 text-purple-400">
                <Activity size={20} />
              </div>
            </div>
            <h3 className="text-slate-400 text-xs font-medium uppercase">Active Sessions</h3>
            <p className="text-3xl font-bold text-purple-400 mt-2">
              {activeSessions.filter((s) => s.is_running).length}
            </p>
          </div>

        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Trading Configuration */}
          <div className="bg-[#151B26] border border-white/5 rounded-2xl p-6 shadow-2xl">
            <h3 className="font-semibold text-white mb-6 flex items-center gap-2">
              <Target className="w-5 h-5 text-cyan-400" />
              Start New Trading Session
            </h3>

            <div className="space-y-5">
              {/* Strategy Selector */}
              <div>
                <label className="text-xs font-semibold text-slate-400 uppercase mb-3 block">
                  Select Strategy
                </label>
                <div className="relative">
                  <button
                    onClick={() => setShowStrategyDropdown(!showStrategyDropdown)}
                    className="w-full px-4 py-3 bg-[#0B0E14] border border-white/10 rounded-xl text-white flex items-center justify-between hover:border-cyan-500/50 transition"
                  >
                    <div className="text-left">
                      <div className="font-semibold">{selectedStrategyData?.name || "Select..."}</div>
                      {selectedStrategyData && (
                        <div className="text-xs text-slate-400 mt-1">
                          Risk: <span className={RISK_COLORS[selectedStrategyData.risk_level]}>{selectedStrategyData.risk_level}</span>
                        </div>
                      )}
                    </div>
                    <ChevronDown className={`w-5 h-5 text-slate-400 transition-transform ${showStrategyDropdown ? "rotate-180" : ""}`} />
                  </button>

                  {showStrategyDropdown && (
                    <div className="absolute top-full left-0 right-0 mt-2 bg-[#1a2332] border border-white/10 rounded-xl shadow-2xl overflow-hidden z-50">
                      {strategies.map((strategy) => (
                        <div
                          key={strategy.id}
                          onClick={() => {
                            setSelectedStrategy(strategy.id);
                            setShowStrategyDropdown(false);
                          }}
                          className="px-4 py-3 hover:bg-white/5 cursor-pointer"
                        >
                          <div className="font-medium text-white">{strategy.name}</div>
                          <div className="text-xs text-slate-400 mt-1">{strategy.description}</div>
                          <div className="text-xs mt-1">
                            Risk: <span className={RISK_COLORS[strategy.risk_level]}>{strategy.risk_level}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Symbol Selector - Only show for strategies that need it */}
              {requiresSymbol ? (
                <div>
                  <label className="text-xs font-semibold text-slate-400 uppercase mb-3 block">
                    Trading Pair
                  </label>
                  <div className="relative">
                    <button
                      onClick={() => setShowSymbolDropdown(!showSymbolDropdown)}
                      className="w-full px-4 py-3 bg-[#0B0E14] border border-white/10 rounded-xl text-white flex items-center justify-between hover:border-cyan-500/50 transition"
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-2xl" style={{ color: selectedSymbolData?.color }}>
                          {selectedSymbolData?.logo}
                        </span>
                        <div className="text-left">
                          <div className="font-semibold">{selectedSymbolData?.symbol}</div>
                          <div className="text-xs text-slate-400">{selectedSymbolData?.name}</div>
                        </div>
                      </div>
                      <ChevronDown className={`w-5 h-5 text-slate-400 transition-transform ${showSymbolDropdown ? "rotate-180" : ""}`} />
                    </button>

                    {showSymbolDropdown && (
                      <div className="absolute top-full left-0 right-0 mt-2 bg-[#1a2332] border border-white/10 rounded-xl shadow-2xl overflow-hidden z-50">
                        {CRYPTO_PAIRS.map((pair) => (
                          <div
                            key={pair.symbol}
                            onClick={() => {
                              setSelectedSymbol(pair.symbol);
                              setShowSymbolDropdown(false);
                            }}
                            className="px-4 py-3 hover:bg-white/5 cursor-pointer flex items-center gap-3"
                          >
                            <span className="text-xl" style={{ color: pair.color }}>
                              {pair.logo}
                            </span>
                            <div>
                              <div className="font-medium text-white">{pair.symbol}</div>
                              <div className="text-xs text-slate-400">{pair.name}</div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div className="p-4 bg-cyan-500/10 border border-cyan-500/20 rounded-xl">
                  <div className="flex items-start gap-3">
                    <Zap className="w-5 h-5 text-cyan-400 mt-0.5" />
                    <div>
                      <div className="font-medium text-cyan-400">Pairs Trading (ETH/BTC)</div>
                      <div className="text-sm text-slate-400 mt-1">
                        This strategy trades the ETH/BTC ratio using Z-Score mean reversion.
                        No coin selection needed - it monitors the pair relationship automatically.
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Trade Amount */}
              <div>
                <label className="text-xs font-semibold text-slate-400 uppercase mb-3 flex items-center gap-2">
                  <DollarSign className="w-4 h-4" />
                  Trade Amount (USDT)
                </label>
                <input
                  type="number"
                  value={tradeAmount}
                  onChange={(e) => setTradeAmount(parseFloat(e.target.value) || 0)}
                  className="w-full px-4 py-3 bg-[#0B0E14] border border-white/10 rounded-xl text-white focus:outline-none focus:border-cyan-500/50 transition"
                  placeholder="100"
                  min="10"
                  step="10"
                />
                <div className="flex gap-2 mt-2">
                  {[50, 100, 250, 500].map((amount) => (
                    <button
                      key={amount}
                      onClick={() => setTradeAmount(amount)}
                      className="px-3 py-1 bg-[#0B0E14] border border-white/10 rounded-lg text-xs text-slate-300 hover:border-cyan-500/50 transition"
                    >
                      ${amount}
                    </button>
                  ))}
                </div>
              </div>

              {/* Duration */}
              <div>
                <label className="text-xs font-semibold text-slate-400 uppercase mb-3 flex items-center gap-2">
                  <Timer className="w-4 h-4" />
                  Duration
                </label>
                
                {/* Unit Toggle */}
                <div className="flex p-1 bg-[#0B0E14] rounded-xl mb-3 border border-white/5">
                  <button
                    onClick={() => {
                      setDurationUnit("minutes");
                      setDuration(60);
                    }}
                    className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all ${
                      durationUnit === "minutes"
                        ? "bg-[#1E293B] text-cyan-400 shadow-sm"
                        : "text-slate-500 hover:text-slate-300"
                    }`}
                  >
                    Minutes
                  </button>
                  <button
                    onClick={() => {
                      setDurationUnit("days");
                      setDuration(1);
                    }}
                    className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all ${
                      durationUnit === "days"
                        ? "bg-[#1E293B] text-cyan-400 shadow-sm"
                        : "text-slate-500 hover:text-slate-300"
                    }`}
                  >
                    Days
                  </button>
                </div>

                <input
                  type="number"
                  value={duration}
                  onChange={(e) => setDuration(parseInt(e.target.value) || 0)}
                  className="w-full px-4 py-3 bg-[#0B0E14] border border-white/10 rounded-xl text-white focus:outline-none focus:border-cyan-500/50 transition"
                  placeholder={durationUnit === "minutes" ? "60" : "1"}
                  min={durationUnit === "minutes" ? 5 : 1}
                  step={durationUnit === "minutes" ? 5 : 1}
                />
                
                <div className="flex gap-2 mt-2">
                  {durationUnit === "minutes" ? (
                    <>
                      {[15, 30, 60, 120, 240].map((mins) => (
                        <button
                          key={mins}
                          onClick={() => setDuration(mins)}
                          className="px-3 py-1 bg-[#0B0E14] border border-white/10 rounded-lg text-xs text-slate-300 hover:border-cyan-500/50 transition"
                        >
                          {mins < 60 ? `${mins}m` : `${mins / 60}h`}
                        </button>
                      ))}
                    </>
                  ) : (
                    <>
                      {[1, 3, 7, 14, 30].map((days) => (
                        <button
                          key={days}
                          onClick={() => setDuration(days)}
                          className="px-3 py-1 bg-[#0B0E14] border border-white/10 rounded-lg text-xs text-slate-300 hover:border-cyan-500/50 transition"
                        >
                          {days}d
                        </button>
                      ))}
                    </>
                  )}
                </div>
              </div>

              {/* Start Button */}
              <button
                onClick={startTrading}
                disabled={loading || !selectedStrategy}
                className="w-full px-6 py-4 bg-gradient-to-r from-cyan-500 to-blue-500 text-white font-semibold rounded-xl hover:from-cyan-600 hover:to-blue-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-cyan-500/20 flex items-center justify-center gap-2"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Starting...
                  </span>
                ) : (
                  <>
                    <Play className="w-5 h-5" />
                    Start Trading
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Active Sessions */}
          <div className="bg-[#151B26] border border-white/5 rounded-2xl p-6 shadow-2xl">
            <h3 className="font-semibold text-white mb-6 flex items-center gap-2">
              <Activity className="w-5 h-5 text-cyan-400" />
              Active Trading Sessions
            </h3>

            {activeSessions.length === 0 ? (
              <div className="text-center py-12 text-slate-400">
                <Activity className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No active trading sessions</p>
                <p className="text-sm text-slate-500 mt-1">Start a new session to begin trading</p>
              </div>
            ) : (
              <div className="space-y-4">
                {activeSessions.map((session) => (
                  <div
                    key={session.session_id}
                    className="p-4 bg-[#0B0E14] rounded-xl border border-white/5"
                  >
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <div className="font-semibold text-white">{session.symbol}</div>
                        <div className="text-xs text-slate-400 capitalize">{session.strategy} Strategy</div>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className={`px-2 py-1 rounded-full text-xs ${session.is_running ? "bg-emerald-500/20 text-emerald-400" : "bg-slate-500/20 text-slate-400"}`}>
                          {session.is_running ? "Running" : "Stopped"}
                        </div>
                        {session.is_running && (
                          <button
                            onClick={() => stopTrading(session.session_id)}
                            className="p-1.5 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition"
                          >
                            <Square className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </div>

                    <div className="grid grid-cols-3 gap-3 text-sm">
                      <div>
                        <div className="text-slate-500 text-xs">Position</div>
                        <div className={session.position === "LONG" ? "text-emerald-400" : "text-slate-400"}>
                          {session.position}
                        </div>
                      </div>
                      <div>
                        <div className="text-slate-500 text-xs">Trades</div>
                        <div className="text-white">{session.trades_count}</div>
                      </div>
                      <div>
                        <div className="text-slate-500 text-xs">P&L</div>
                        <div className={session.pnl >= 0 ? "text-emerald-400" : "text-red-400"}>
                          {session.pnl >= 0 ? "+" : ""}${session.pnl.toFixed(2)}
                        </div>
                      </div>
                    </div>

                    {session.is_running && (
                      <div className="mt-3 pt-3 border-t border-white/5">
                        <div className="flex items-center gap-2 text-xs text-slate-400">
                          <Clock className="w-3 h-3" />
                          {session.remaining_minutes.toFixed(0)} min remaining
                        </div>
                        <div className="mt-2 h-1 bg-white/10 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-cyan-500 transition-all"
                            style={{
                              width: `${((session.elapsed_minutes) / (session.elapsed_minutes + session.remaining_minutes)) * 100}%`,
                            }}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Recent Trades */}
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
              <p className="text-sm text-slate-500 mt-1">Trades will appear here once executed</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-[#0B0E14]">
                  <tr>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase">Time</th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase">Symbol</th>
                    <th className="px-6 py-4 text-center text-xs font-semibold text-slate-400 uppercase">Side</th>
                    <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400 uppercase">Price</th>
                    <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400 uppercase">Quantity</th>
                    <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400 uppercase">Total</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {recentTrades.map((trade, idx) => (
                    <tr key={idx} className="hover:bg-white/5 transition">
                      <td className="px-6 py-4 text-sm text-slate-400">
                        {new Date(trade.time).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 font-medium text-white">{trade.symbol}</td>
                      <td className="px-6 py-4 text-center">
                        <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs ${trade.side === "BUY" ? "bg-emerald-500/20 text-emerald-400" : "bg-red-500/20 text-red-400"}`}>
                          {trade.side === "BUY" ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                          {trade.side}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right text-slate-300">${trade.price.toFixed(2)}</td>
                      <td className="px-6 py-4 text-right text-slate-300">{trade.quantity.toFixed(6)}</td>
                      <td className="px-6 py-4 text-right font-semibold text-white">${trade.total.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
