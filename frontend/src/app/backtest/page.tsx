"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Activity, Calendar, TrendingUp, DollarSign, Percent, ChevronDown, Search, Star, Clock, BarChart3, AlertCircle, Cpu, Zap } from "lucide-react";
import Navbar from "@/components/navbar";

const TICKERS = [
  { symbol: "BNB-USD", name: "BNB", logo: "⬡", color: "#F3BA2F" },
  { symbol: "BTC-USD", name: "Bitcoin", logo: "₿", color: "#F7931A" },
  { symbol: "ETH-USD", name: "Ethereum", logo: "Ξ", color: "#627EEA" },
  { symbol: "SOL-USD", name: "Solana", logo: "◎", color: "#14F195" },
];

const BACKTEST_STRATEGIES = [
  {
    id: "hmm",
    name: "HMM Regime Filter",
    description: "Hidden Markov Model that detects market regimes and filters trades during high volatility",
    requires_ticker: true,
    icon: "🧠"
  },
  {
    id: "pairs",
    name: "Pairs Trading (Test)",
    description: "ETH/BTC mean reversion using Z-Score. High frequency strategy for live trading testing.",
    requires_ticker: false,
    icon: "⚡"
  }
];

const REGIME_COLORS: Record<number, string> = {
  0: "#10b981",
  1: "#f59e0b",
  2: "#ef4444",
};

const REGIME_NAMES: Record<number, string> = {
  0: "Low Vol",
  1: "Med Vol",
  2: "High Vol"
};

export default function BacktestPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [showTickerDropdown, setShowTickerDropdown] = useState(false);
  const [showStrategyDropdown, setShowStrategyDropdown] = useState(false);
  const [searchTicker, setSearchTicker] = useState("");
  const [favorites, setFavorites] = useState<string[]>(["BNB-USD"]);
  
  const [strategy, setStrategy] = useState("hmm");
  const [ticker, setTicker] = useState("SOL-USD");
  const [startDate, setStartDate] = useState("2022-01-01");
  const [endDate, setEndDate] = useState(new Date().toISOString().split('T')[0]);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      router.push("/");
    }
  }, [router]);

  const quickRanges = [
    { label: "1M", days: 30 },
    { label: "3M", days: 90 },
    { label: "6M", days: 180 },
    { label: "1Y", days: 365 },
    { label: "YTD", days: -1 },
  ];

  const setQuickRange = (days: number) => {
    const end = new Date();
    const start = new Date();
    
    if (days === -1) {
      start.setMonth(0);
      start.setDate(1);
    } else {
      start.setDate(start.getDate() - days);
    }
    
    setStartDate(start.toISOString().split('T')[0]);
    setEndDate(end.toISOString().split('T')[0]);
  };

  const selectedTicker = TICKERS.find(t => t.symbol === ticker) || TICKERS[0];
  const selectedStrategy = BACKTEST_STRATEGIES.find(s => s.id === strategy) || BACKTEST_STRATEGIES[0];
  
  const filteredTickers = TICKERS.filter(t => 
    t.symbol.toLowerCase().includes(searchTicker.toLowerCase()) ||
    t.name.toLowerCase().includes(searchTicker.toLowerCase())
  );

  const toggleFavorite = (symbol: string) => {
    setFavorites(prev => 
      prev.includes(symbol) 
        ? prev.filter(s => s !== symbol)
        : [...prev, symbol]
    );
  };

  const runBacktest = async () => {
    const token = localStorage.getItem("token");
    if (!token) {
      alert("Please login first");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await fetch("http://127.0.0.1:8000/api/backtest", {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({
          ticker: ticker,
          start_date: startDate,
          end_date: endDate,
          strategy: strategy
        }),
      });

      if (res.status === 401) {
        alert("Session expired. Please login again.");
        localStorage.removeItem("token");
        window.location.href = "/";
        return;
      }

      if (!res.ok) {
        throw new Error("Backtest failed");
      }

      const result = await res.json();
      
      if (result.error) {
        setError(result.error);
        setData(null);
        return;
      }

      setData(result);
    } catch (error) {
      console.error("Failed to fetch", error);
      setError("Error running backtest. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-[#1a2332] border border-white/10 rounded-xl p-4 shadow-2xl">
          <p className="text-slate-400 text-xs mb-2">{data.date}</p>
          <div className="space-y-1">
            <p className="text-cyan-400 font-semibold">
              Strategy: ${(data.strategy * 10000).toFixed(2)}
            </p>
            {strategy === "hmm" && (
              <>
                <p className="text-slate-400 font-semibold">
                  Buy & Hold: ${(data.buy_hold * 10000).toFixed(2)}
                </p>
                <p className="text-xs text-slate-500 mt-2 pt-2 border-t border-white/5">
                  Regime: <span style={{ color: REGIME_COLORS[data.regime as number] || '#94a3b8' }}>
                    {REGIME_NAMES[data.regime as number] || `State ${data.regime}`}
                  </span>
                </p>
              </>
            )}
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="min-h-screen bg-[#0B0E14] text-slate-200">
      <Navbar />
      
      <main className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {/* Header Section */}
        <div className="flex justify-between items-end border-b border-white/10 pb-6">
          <div>
            <h1 className="text-4xl font-bold text-white">
              Backtest Engine
            </h1>
            <p className="text-slate-400 mt-2">Test strategies on historical data</p>
          </div>
          <div className="flex gap-2">
            <div className="px-3 py-1 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-emerald-400 text-sm">
              Live Data
            </div>
          </div>
        </div>

        {/* Controls Card */}
        <div className="bg-[#151B26] border border-white/5 rounded-2xl p-6 shadow-2xl">
          <div className="space-y-6">
            
            {/* Strategy Selector */}
            <div>
              <label className="text-xs font-semibold text-slate-400 uppercase mb-3 flex items-center gap-2">
                <Cpu className="w-4 h-4" />
                Select Strategy
              </label>
              <div className="relative">
                <button
                  onClick={() => setShowStrategyDropdown(!showStrategyDropdown)}
                  className="w-full px-4 py-3 bg-[#0B0E14] border border-white/10 rounded-xl text-white flex items-center justify-between hover:border-cyan-500/50 transition group"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{selectedStrategy.icon}</span>
                    <div className="text-left">
                      <div className="font-semibold">{selectedStrategy.name}</div>
                      <div className="text-xs text-slate-400">{selectedStrategy.description.slice(0, 50)}...</div>
                    </div>
                  </div>
                  <ChevronDown className={`w-5 h-5 text-slate-400 transition-transform ${showStrategyDropdown ? 'rotate-180' : ''}`} />
                </button>

                {showStrategyDropdown && (
                  <div className="absolute top-full left-0 right-0 mt-2 bg-[#1a2332] border border-white/10 rounded-xl shadow-2xl overflow-hidden z-50">
                    {BACKTEST_STRATEGIES.map((s) => (
                      <div
                        key={s.id}
                        className="px-4 py-3 hover:bg-white/5 cursor-pointer flex items-start gap-3"
                        onClick={() => {
                          setStrategy(s.id);
                          setShowStrategyDropdown(false);
                        }}
                      >
                        <span className="text-xl">{s.icon}</span>
                        <div>
                          <div className="font-medium text-white">{s.name}</div>
                          <div className="text-xs text-slate-400 mt-1">{s.description}</div>
                          {!s.requires_ticker && (
                            <div className="text-xs text-cyan-400 mt-1">Auto-selects coin pairs</div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Ticker Selector - Only show for strategies that need it */}
            {selectedStrategy.requires_ticker && (
              <div>
                <label className="text-xs font-semibold text-slate-400 uppercase mb-3 flex items-center gap-2">
                  <BarChart3 className="w-4 h-4" />
                  Select Trading Pair
                </label>
                <div className="relative">
                  <button
                    onClick={() => setShowTickerDropdown(!showTickerDropdown)}
                    className="w-full px-4 py-3 bg-[#0B0E14] border border-white/10 rounded-xl text-white flex items-center justify-between hover:border-cyan-500/50 transition group"
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-2xl" style={{ color: selectedTicker.color }}>
                        {selectedTicker.logo}
                      </span>
                      <div className="text-left">
                        <div className="font-semibold">{selectedTicker.symbol}</div>
                        <div className="text-xs text-slate-400">{selectedTicker.name}</div>
                      </div>
                    </div>
                    <ChevronDown className={`w-5 h-5 text-slate-400 transition-transform ${showTickerDropdown ? 'rotate-180' : ''}`} />
                  </button>

                  {showTickerDropdown && (
                    <div className="absolute top-full left-0 right-0 mt-2 bg-[#1a2332] border border-white/10 rounded-xl shadow-2xl overflow-hidden z-50">
                      <div className="p-3 border-b border-white/5">
                        <div className="relative">
                          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                          <input
                            type="text"
                            placeholder="Search coins..."
                            value={searchTicker}
                            onChange={(e) => setSearchTicker(e.target.value)}
                            className="w-full pl-10 pr-4 py-2 bg-[#0B0E14] border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:border-cyan-500/50"
                          />
                        </div>
                      </div>

                      <div className="max-h-64 overflow-y-auto">
                        {filteredTickers.map((t) => (
                          <div
                            key={t.symbol}
                            className="w-full px-4 py-3 flex items-center justify-between hover:bg-white/5 transition group cursor-pointer"
                            onClick={() => {
                              setTicker(t.symbol);
                              setShowTickerDropdown(false);
                              setSearchTicker("");
                            }}
                          >
                            <div className="flex items-center gap-3">
                              <span className="text-xl" style={{ color: t.color }}>
                                {t.logo}
                              </span>
                              <div className="text-left">
                                <div className="font-medium text-white">{t.symbol}</div>
                                <div className="text-xs text-slate-400">{t.name}</div>
                              </div>
                            </div>
                            <div
                              onClick={(e) => {
                                e.stopPropagation();
                                toggleFavorite(t.symbol);
                              }}
                              className="p-1 cursor-pointer"
                            >
                              <Star
                                className={`w-4 h-4 ${
                                  favorites.includes(t.symbol)
                                    ? 'fill-yellow-400 text-yellow-400'
                                    : 'text-slate-600 hover:text-yellow-400'
                                } transition`}
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Pairs Trading Info Box */}
            {!selectedStrategy.requires_ticker && (
              <div className="p-4 bg-cyan-500/10 border border-cyan-500/20 rounded-xl">
                <div className="flex items-start gap-3">
                  <Zap className="w-5 h-5 text-cyan-400 mt-0.5" />
                  <div>
                    <div className="font-medium text-cyan-400">Pairs Trading (ETH/BTC)</div>
                    <div className="text-sm text-slate-400 mt-1">
                      This strategy trades the ETH/BTC ratio using Z-Score mean reversion.
                      When the ratio deviates from its mean, it opens positions expecting reversion.
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Date Range Selector */}
            <div>
              <label className="text-xs font-semibold text-slate-400 uppercase mb-3 flex items-center gap-2">
                <Calendar className="w-4 h-4 text-cyan-400" />
                Backtest Period
              </label>
              
              <div className="flex gap-2 mb-3">
                {quickRanges.map((range) => (
                  <button
                    key={range.label}
                    onClick={() => setQuickRange(range.days)}
                    className="px-4 py-2 bg-[#0B0E14] border border-white/10 rounded-lg text-sm text-slate-300 hover:border-cyan-500/50 hover:text-white transition"
                  >
                    {range.label}
                  </button>
                ))}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-slate-500 mb-2 block">Start Date</label>
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="w-full px-4 py-3 bg-[#31343a] border border-white/10 rounded-xl text-white focus:outline-none focus:border-cyan-500/50 transition cursor-pointer"
                  />
                </div>

                <div>
                  <label className="text-xs text-slate-500 mb-2 block">End Date</label>
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="w-full px-4 py-3 bg-[#31343a] border border-white/10 rounded-xl text-white focus:outline-none focus:border-cyan-500/50 transition cursor-pointer"
                  />
                </div>
              </div>
            </div>

            {/* Run Button */}
            <button
              onClick={runBacktest}
              disabled={loading}
              className="w-full px-6 py-4 bg-linear-to-r from-cyan-500 to-blue-500 text-white font-semibold rounded-xl hover:from-cyan-600 hover:to-blue-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-cyan-500/20 hover:shadow-cyan-500/40"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Running Simulation...
                </span>
              ) : (
                `Run ${selectedStrategy.name} Backtest`
              )}
            </button>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/20 rounded-2xl p-4 flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-400" />
            <p className="text-red-400">{error}</p>
          </div>
        )}

        {/* KPI Cards */}
        {data && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="p-6 rounded-2xl bg-linear-to-br from-emerald-500/10 to-emerald-500/5 border border-emerald-500/20 hover:border-emerald-500/40 transition-all group">
                <div className="flex justify-between items-start mb-3">
                  <div className="p-2.5 rounded-xl bg-emerald-500/20 text-emerald-400">
                    <TrendingUp size={20} />
                  </div>
                </div>
                <h3 className="text-slate-400 text-xs font-medium uppercase">Strategy Return</h3>
                <p className="text-3xl font-bold text-emerald-400 mt-2">{data.metrics.strategy_return}</p>
              </div>

              <div className="p-6 rounded-2xl bg-linear-to-br from-blue-500/10 to-blue-500/5 border border-blue-500/20 hover:border-blue-500/40 transition-all group">
                <div className="flex justify-between items-start mb-3">
                  <div className="p-2.5 rounded-xl bg-blue-500/20 text-blue-400">
                    <Percent size={20} />
                  </div>
                </div>
                <h3 className="text-slate-400 text-xs font-medium uppercase">
                  {strategy === "pairs" ? "Trades/Day" : "Buy & Hold"}
                </h3>
                <p className="text-3xl font-bold text-blue-400 mt-2">
                  {strategy === "pairs" ? data.metrics.trades_per_day : data.metrics.buy_hold_return}
                </p>
              </div>

              <div className="p-6 rounded-2xl bg-linear-to-br from-purple-500/10 to-purple-500/5 border border-purple-500/20 hover:border-purple-500/40 transition-all group">
                <div className="flex justify-between items-start mb-3">
                  <div className="p-2.5 rounded-xl bg-purple-500/20 text-purple-400">
                    <DollarSign size={20} />
                  </div>
                </div>
                <h3 className="text-slate-400 text-xs font-medium uppercase">Final Balance</h3>
                <p className="text-3xl font-bold text-purple-400 mt-2">{data.metrics.final_value}</p>
              </div>

              <div className="p-6 rounded-2xl bg-linear-to-br from-cyan-500/10 to-cyan-500/5 border border-cyan-500/20 hover:border-cyan-500/40 transition-all group">
                <div className="flex justify-between items-start mb-3">
                  <div className="p-2.5 rounded-xl bg-cyan-500/20 text-cyan-400">
                    <Activity size={20} />
                  </div>
                </div>
                <h3 className="text-slate-400 text-xs font-medium uppercase">Win Rate</h3>
                <p className="text-3xl font-bold text-cyan-400 mt-2">{data.metrics.win_rate}</p>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 rounded-xl bg-[#151B26] border border-white/5">
                <div className="text-slate-400 text-xs font-medium uppercase mb-1">Sharpe Ratio</div>
                <div className="text-2xl font-bold text-white">{data.metrics.sharpe_ratio}</div>
              </div>
              <div className="p-4 rounded-xl bg-[#151B26] border border-white/5">
                <div className="text-slate-400 text-xs font-medium uppercase mb-1">Sortino Ratio</div>
                <div className="text-2xl font-bold text-cyan-400">{data.metrics.sortino_ratio}</div>
              </div>
              <div className="p-4 rounded-xl bg-[#151B26] border border-white/5">
                <div className="text-slate-400 text-xs font-medium uppercase mb-1">Max DD (Strategy)</div>
                <div className="text-2xl font-bold text-red-400">{data.metrics.max_drawdown}</div>
              </div>
              <div className="p-4 rounded-xl bg-[#151B26] border border-white/5">
                <div className="text-slate-400 text-xs font-medium uppercase mb-1">
                  {strategy === "pairs" ? "Max DD (Ratio)" : "Max DD (B&H)"}
                </div>
                <div className="text-2xl font-bold text-orange-400">{data.metrics.max_drawdown_bh}</div>
              </div>
              <div className="p-4 rounded-xl bg-[#151B26] border border-white/5">
                <div className="text-slate-400 text-xs font-medium uppercase mb-1">Profit Factor</div>
                <div className="text-2xl font-bold text-emerald-400">{data.metrics.profit_factor}</div>
              </div>
              <div className="p-4 rounded-xl bg-[#151B26] border border-white/5">
                <div className="text-slate-400 text-xs font-medium uppercase mb-1">Avg Risk:Reward</div>
                <div className="text-2xl font-bold text-purple-400">{data.metrics.risk_reward}</div>
              </div>
              <div className="p-4 rounded-xl bg-[#151B26] border border-white/5">
                <div className="text-slate-400 text-xs font-medium uppercase mb-1">Recovery Factor</div>
                <div className="text-2xl font-bold text-yellow-400">{data.metrics.recovery_factor}</div>
              </div>
              <div className="p-4 rounded-xl bg-[#151B26] border border-white/5">
                <div className="text-slate-400 text-xs font-medium uppercase mb-1">Total Trades</div>
                <div className="text-2xl font-bold text-white">{data.metrics.total_trades}</div>
              </div>
            </div>
          </>
        )}

        {/* Main Chart */}
        <div className="bg-[#151B26] border border-white/5 rounded-2xl overflow-hidden shadow-2xl">
          <div className="p-6 border-b border-white/5 flex items-center justify-between">
            <h3 className="font-semibold text-white flex items-center gap-2">
              <Activity className="w-5 h-5 text-cyan-400" />
              Performance (Normalized to $10,000)
            </h3>
            {data && (
              <div className="flex gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-cyan-500 rounded-full" />
                  <span className="text-slate-400">{selectedStrategy.name}</span>
                </div>
                {strategy === "hmm" && (
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 bg-slate-500 rounded-full border-2 border-slate-700" />
                    <span className="text-slate-400">Buy & Hold</span>
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="p-6 h-[450px]">
            {data ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data.chart_data}>
                  <defs>
                    <linearGradient id="strategyGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#06b6d4" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#1e293b" />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 11, fill: '#94a3b8' }}
                    tickLine={false}
                    axisLine={false}
                    minTickGap={40}
                  />
                  <YAxis
                    domain={['auto', 'auto']}
                    tick={{ fontSize: 11, fill: '#94a3b8' }}
                    tickLine={false}
                    axisLine={false}
                    tickFormatter={(val) => `$${(val * 10000).toFixed(0)}`}
                  />
                  <Tooltip content={<CustomTooltip />} />

                  {strategy === "hmm" && (
                    <Line
                      type="monotone"
                      dataKey="buy_hold"
                      stroke="#64748b"
                      strokeWidth={2}
                      strokeDasharray="5 5"
                      dot={false}
                      name="Buy & Hold"
                    />
                  )}

                  <Line
                    type="monotone"
                    dataKey="strategy"
                    stroke="#06b6d4"
                    strokeWidth={3}
                    dot={false}
                    name="Strategy"
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-slate-400 gap-3">
                <div className="p-4 rounded-2xl bg-cyan-500/10">
                  <Calendar className="w-12 h-12 text-cyan-400" />
                </div>
                <p className="text-lg font-medium">Ready to Backtest</p>
                <p className="text-sm text-slate-500">Select your parameters and run simulation</p>
              </div>
            )}
          </div>
        </div>

        {/* Regime Legend - Only for HMM */}
        {data && strategy === "hmm" && (
          <div className="bg-[#151B26] border border-white/5 rounded-2xl p-6">
            <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-cyan-400" />
              Market Regime Indicators (HMM States)
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="flex items-center gap-3 p-3 rounded-lg bg-[#0B0E14]">
                <div className="w-4 h-4 rounded-full" style={{ backgroundColor: REGIME_COLORS[0] }} />
                <div>
                  <div className="text-sm font-medium text-white">Low Volatility</div>
                  <div className="text-xs text-slate-400">Stable market conditions</div>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 rounded-lg bg-[#0B0E14]">
                <div className="w-4 h-4 rounded-full" style={{ backgroundColor: REGIME_COLORS[1] }} />
                <div>
                  <div className="text-sm font-medium text-white">Medium Volatility</div>
                  <div className="text-xs text-slate-400">Moderate price swings</div>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 rounded-lg bg-[#0B0E14]">
                <div className="w-4 h-4 rounded-full" style={{ backgroundColor: REGIME_COLORS[2] }} />
                <div>
                  <div className="text-sm font-medium text-white">High Volatility</div>
                  <div className="text-xs text-slate-400">Trading blocked in this regime</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Trades Log Table */}
        {data && data.trades && data.trades.length > 0 && (
          <div className="bg-[#151B26] border border-white/5 rounded-2xl overflow-hidden">
            <div className="p-6 border-b border-white/5">
              <h3 className="font-semibold text-white flex items-center gap-2">
                <Clock className="w-5 h-5 text-cyan-400" />
                Trade History ({data.trades.length} trades)
              </h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-[#0B0E14]">
                  <tr>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase">Date</th>
                    {strategy === "pairs" ? (
                      <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase">Type</th>
                    ) : (
                      <>
                        <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400 uppercase">Entry</th>
                        <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400 uppercase">Exit</th>
                        <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400 uppercase">Duration</th>
                      </>
                    )}
                    <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400 uppercase">P&L</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {data.trades.map((trade: any, i: number) => (
                    <tr key={i} className="hover:bg-white/5 transition">
                      <td className="px-6 py-4 text-sm text-slate-300">{trade.entry_date}</td>
                      {strategy === "pairs" ? (
                        <td className="px-6 py-4 text-sm text-white font-mono">{trade.type} (Z: {trade.z_score})</td>
                      ) : (
                        <>
                          <td className="px-6 py-4 text-right text-sm font-medium text-white">
                            ${trade.entry_price?.toFixed(2) || '-'}
                          </td>
                          <td className="px-6 py-4 text-right text-sm font-medium text-white">
                            ${trade.exit_price?.toFixed(2) || '-'}
                          </td>
                          <td className="px-6 py-4 text-right text-sm text-slate-300">
                            {trade.duration_days} days
                          </td>
                        </>
                      )}
                      <td className="px-6 py-4 text-right text-sm font-semibold">
                        <span className={trade.trade_pnl > 0 ? "text-emerald-400" : "text-red-400"}>
                          {trade.trade_pnl > 0 ? "+" : ""}{trade.trade_pnl_percent?.toFixed(3)}%
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
