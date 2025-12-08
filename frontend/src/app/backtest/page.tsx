"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend, ScatterChart, Scatter } from 'recharts';
import { Activity, Calendar, TrendingUp, DollarSign, Percent, ChevronDown, Search, Star, Clock, BarChart3, AlertCircle, TrendingDown } from "lucide-react";
import Navbar from "@/components/navbar";

// Popular crypto tickers with logos
const TICKERS = [
    { symbol: "BNB-USD", name: "BNB", logo: "⬡", color: "#F3BA2F" },
  { symbol: "BTC-USD", name: "Bitcoin", logo: "₿", color: "#F7931A" },
  { symbol: "ETH-USD", name: "Ethereum", logo: "Ξ", color: "#627EEA" },
  { symbol: "SOL-USD", name: "Solana", logo: "◎", color: "#14F195" },
];

// Regime colors for HMM states
const REGIME_COLORS: Record<number, string> = {
  0: "#10b981", // Green - Low volatility
  1: "#f59e0b", // Orange - Medium volatility
  2: "#ef4444", // Red - High volatility
};

export default function BacktestPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [showTickerDropdown, setShowTickerDropdown] = useState(false);
  const [searchTicker, setSearchTicker] = useState("");
  const [favorites, setFavorites] = useState<string[]>(["BNB-USD"]);
  
  // Inputs state
  const [ticker, setTicker] = useState("SOL-USD");
  const [startDate, setStartDate] = useState("2022-01-01");
  const [endDate, setEndDate] = useState(new Date().toISOString().split('T')[0]);

  // Auth check on mount
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      router.push("/");
    }
  }, [router]);

  // Quick date ranges (Binance-style)
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
    setLoading(true);
    setError(null);
    
    const token = localStorage.getItem("token");
    if (!token) {
      alert("Please login first");
      return;
    }

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
          end_date: endDate
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

      // Calculate additional metrics from the data
      const strategyReturns = result.chart_data.map((d: any) => d.strategy);
      const buyHoldReturns = result.chart_data.map((d: any) => d.buy_hold);
      
      // Calculate max drawdown for strategy
      let peak = strategyReturns[0];
      let maxDrawdown = 0;
      strategyReturns.forEach((val: number) => {
        if (val > peak) peak = val;
        const drawdown = (peak - val) / peak;
        if (drawdown > maxDrawdown) maxDrawdown = drawdown;
      });

      // Count regime changes for trades proxy
      const regimes = result.chart_data.map((d: any) => d.regime);
      let trades = 0;
      for (let i = 1; i < regimes.length; i++) {
        if (regimes[i] !== regimes[i-1]) trades++;
      }

      // Calculate Sharpe Ratio (simplified - assumes daily data)
      const returns = [];
      for (let i = 1; i < strategyReturns.length; i++) {
        returns.push((strategyReturns[i] - strategyReturns[i-1]) / strategyReturns[i-1]);
      }
      const avgReturn = returns.reduce((a, b) => a + b, 0) / returns.length;
      const stdDev = Math.sqrt(returns.reduce((sum, r) => sum + Math.pow(r - avgReturn, 2), 0) / returns.length);
      const sharpeRatio = (avgReturn / stdDev) * Math.sqrt(252); // Annualized

      // Win rate calculation
      const positiveReturns = returns.filter(r => r > 0).length;
      const winRate = (positiveReturns / returns.length) * 100;

      // Generate detailed trades log
      const tradesLog: any[] = [];
      let position: 'cash' | 'holding' = 'cash';
      let entryPrice = 0;
      let entryValue = 0;

      result.chart_data.forEach((day: any, index: number) => {
        const prevDay = index > 0 ? result.chart_data[index - 1] : null;
        
        if (!prevDay) return;

        const prevStrategy = prevDay.strategy;
        const currStrategy = day.strategy;
        
        // Detect position change by checking if strategy equity increased more than market movement
        const strategyChange = currStrategy - prevStrategy;
        const buyHoldChange = day.buy_hold - prevDay.buy_hold;
        
        // Simple heuristic: if strategy significantly diverges from buy & hold, a trade occurred
        const changeRatio = Math.abs(strategyChange - buyHoldChange);
        
        if (position === 'cash' && changeRatio > 0.001) {
          // BUY Signal
          position = 'holding';
          entryPrice = day.buy_hold * 10000; // Approximate price
          entryValue = day.strategy * 10000;
          
          tradesLog.push({
            date: day.date,
            action: 'BUY',
            price: entryPrice,
            value: entryValue,
            profit: null,
            regime: day.regime
          });
        } else if (position === 'holding' && (day.regime === 2 || changeRatio > 0.002)) {
          // SELL Signal (either high volatility or strategy decision)
          const exitPrice = day.buy_hold * 10000;
          const exitValue = day.strategy * 10000;
          const profit = exitValue - entryValue;
          
          tradesLog.push({
            date: day.date,
            action: 'SELL',
            price: exitPrice,
            value: exitValue,
            profit: profit,
            profitPercent: ((profit / entryValue) * 100).toFixed(2),
            regime: day.regime
          });
          
          position = 'cash';
        }
      });

      const enrichedData = {
        ...result,
        metrics: {
          ...result.metrics,
          sharpe_ratio: sharpeRatio.toFixed(2),
          max_drawdown: `${(maxDrawdown * 100).toFixed(1)}%`,
          win_rate: `${winRate.toFixed(1)}%`,
          total_trades: tradesLog.length,
        },
        trades: tradesLog
      };

      setData(enrichedData);
    } catch (error) {
      console.error("Failed to fetch", error);
      setError("Error running backtest. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // Custom tooltip to show regime
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      const regimeNames = ["Low Vol", "Med Vol", "High Vol"];
      return (
        <div className="bg-[#1a2332] border border-white/10 rounded-xl p-4 shadow-2xl">
          <p className="text-slate-400 text-xs mb-2">{data.date}</p>
          <div className="space-y-1">
            <p className="text-cyan-400 font-semibold">
              Strategy: ${(data.strategy * 10000).toFixed(2)}
            </p>
            <p className="text-slate-400 font-semibold">
              Buy & Hold: ${(data.buy_hold * 10000).toFixed(2)}
            </p>
            <p className="text-xs text-slate-500 mt-2 pt-2 border-t border-white/5">
              Regime: <span style={{ color: REGIME_COLORS[data.regime as number] || '#94a3b8' }}>
                {regimeNames[data.regime as number] || `State ${data.regime}`}
              </span>
            </p>
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
            <h1 className="text-4xl font-bold text-white bg-gradient-to-r from-white via-cyan-200 to-cyan-400 bg-clip-text text-transparent">
              HMM Backtest Engine
            </h1>
            <p className="text-slate-400 mt-2">Hybrid AI Strategy with Hidden Markov Models</p>
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
            {/* Ticker Selector */}
            <div>
              <label className="text-xs font-semibold text-slate-400 uppercase mb-3 block flex items-center gap-2">
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

            {/* Date Range Selector */}
            <div>
              <label className="text-xs font-semibold text-slate-400 uppercase mb-3 block flex items-center gap-2">
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
                    className="w-full px-4 py-3 bg-[#31343a]  border border-white/10 rounded-xl text-white focus:outline-none focus:border-cyan-500/50 transition cursor-pointer"
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
              className="w-full px-6 py-4 bg-gradient-to-r from-cyan-500 to-blue-500 text-white font-semibold rounded-xl hover:from-cyan-600 hover:to-blue-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-cyan-500/20 hover:shadow-cyan-500/40"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Running Simulation...
                </span>
              ) : (
                "Run Backtest"
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
              <div className="p-6 rounded-2xl bg-gradient-to-br from-emerald-500/10 to-emerald-500/5 border border-emerald-500/20 hover:border-emerald-500/40 transition-all group">
                <div className="flex justify-between items-start mb-3">
                  <div className="p-2.5 rounded-xl bg-emerald-500/20 text-emerald-400">
                    <TrendingUp size={20} />
                  </div>
                </div>
                <h3 className="text-slate-400 text-xs font-medium uppercase">Strategy Return</h3>
                <p className="text-3xl font-bold text-emerald-400 mt-2">{data.metrics.strategy_return}</p>
              </div>

              <div className="p-6 rounded-2xl bg-gradient-to-br from-blue-500/10 to-blue-500/5 border border-blue-500/20 hover:border-blue-500/40 transition-all group">
                <div className="flex justify-between items-start mb-3">
                  <div className="p-2.5 rounded-xl bg-blue-500/20 text-blue-400">
                    <Percent size={20} />
                  </div>
                </div>
                <h3 className="text-slate-400 text-xs font-medium uppercase">Buy & Hold</h3>
                <p className="text-3xl font-bold text-blue-400 mt-2">{data.metrics.buy_hold_return}</p>
              </div>

              <div className="p-6 rounded-2xl bg-gradient-to-br from-purple-500/10 to-purple-500/5 border border-purple-500/20 hover:border-purple-500/40 transition-all group">
                <div className="flex justify-between items-start mb-3">
                  <div className="p-2.5 rounded-xl bg-purple-500/20 text-purple-400">
                    <DollarSign size={20} />
                  </div>
                </div>
                <h3 className="text-slate-400 text-xs font-medium uppercase">Final Balance</h3>
                <p className="text-3xl font-bold text-purple-400 mt-2">{data.metrics.final_value}</p>
              </div>

              <div className="p-6 rounded-2xl bg-gradient-to-br from-cyan-500/10 to-cyan-500/5 border border-cyan-500/20 hover:border-cyan-500/40 transition-all group">
                <div className="flex justify-between items-start mb-3">
                  <div className="p-2.5 rounded-xl bg-cyan-500/20 text-cyan-400">
                    <Activity size={20} />
                  </div>
                </div>
                <h3 className="text-slate-400 text-xs font-medium uppercase">Win Rate</h3>
                <p className="text-3xl font-bold text-cyan-400 mt-2">{data.metrics.win_rate}</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 rounded-xl bg-[#151B26] border border-white/5">
                <div className="text-slate-400 text-xs font-medium uppercase mb-1">Sharpe Ratio</div>
                <div className="text-2xl font-bold text-white">{data.metrics.sharpe_ratio}</div>
              </div>
              <div className="p-4 rounded-xl bg-[#151B26] border border-white/5">
                <div className="text-slate-400 text-xs font-medium uppercase mb-1">Max Drawdown</div>
                <div className="text-2xl font-bold text-red-400">{data.metrics.max_drawdown}</div>
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
              Performance Comparison (Normalized to $10,000)
            </h3>
            {data && (
              <div className="flex gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-cyan-500 rounded-full" />
                  <span className="text-slate-400">HMM Strategy</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-slate-500 rounded-full border-2 border-slate-700" />
                  <span className="text-slate-400">Buy & Hold</span>
                </div>
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

                  <Line
                    type="monotone"
                    dataKey="buy_hold"
                    stroke="#64748b"
                    strokeWidth={2}
                    strokeDasharray="5 5"
                    dot={false}
                    name="Buy & Hold"
                  />

                  <Line
                    type="monotone"
                    dataKey="strategy"
                    stroke="#06b6d4"
                    strokeWidth={3}
                    dot={false}
                    name="HMM Strategy"
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

        {/* Regime Legend */}
        {data && (
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
                Complete Trade History ({data.trades.length} trades)
              </h3>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-[#0B0E14]">
                  <tr>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase">Date</th>
                    <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase">Action</th>
                    <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400 uppercase">Price</th>
                    <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400 uppercase">Portfolio Value</th>
                    <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400 uppercase">Profit/Loss</th>
                    <th className="px-6 py-4 text-center text-xs font-semibold text-slate-400 uppercase">Regime</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  {data.trades.map((trade: any, i: number) => (
                    <tr key={i} className="hover:bg-white/5 transition">
                      <td className="px-6 py-4 text-sm text-slate-300">{trade.date}</td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold ${
                          trade.action === "BUY"
                            ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                            : "bg-red-500/10 text-red-400 border border-red-500/20"
                        }`}>
                          {trade.action === "BUY" ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                          {trade.action}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right text-sm font-medium text-white">
                        ${trade.price.toFixed(2)}
                      </td>
                      <td className="px-6 py-4 text-right text-sm font-medium text-slate-300">
                        ${trade.value.toFixed(2)}
                      </td>
                      <td className="px-6 py-4 text-right text-sm font-semibold">
                        {trade.profit !== null ? (
                          <div className="flex flex-col items-end">
                            <span className={trade.profit > 0 ? "text-emerald-400" : "text-red-400"}>
                              {trade.profit > 0 ? "+" : ""}${trade.profit.toFixed(2)}
                            </span>
                            <span className={`text-xs ${trade.profit > 0 ? "text-emerald-400/70" : "text-red-400/70"}`}>
                              ({trade.profit > 0 ? "+" : ""}{trade.profitPercent}%)
                            </span>
                          </div>
                        ) : (
                          <span className="text-slate-500">—</span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-center">
                        <div className="inline-flex items-center gap-2 px-2 py-1 rounded-full bg-white/5">
                          <div className="w-2 h-2 rounded-full" style={{ backgroundColor: REGIME_COLORS[trade.regime as number] || '#94a3b8' }} />
                          <span className="text-xs text-slate-400">
                            {trade.regime === 0 ? 'Low' : trade.regime === 1 ? 'Med' : 'High'}
                          </span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            
            {/* Trade Summary */}
            <div className="p-6 border-t border-white/5 bg-[#0B0E14]">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                  <div className="text-xs text-slate-400 mb-1">Total Trades</div>
                  <div className="text-lg font-bold text-white">{data.trades.length}</div>
                </div>
                <div>
                  <div className="text-xs text-slate-400 mb-1">Winning Trades</div>
                  <div className="text-lg font-bold text-emerald-400">
                    {data.trades.filter((t: any) => t.profit > 0).length}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-slate-400 mb-1">Losing Trades</div>
                  <div className="text-lg font-bold text-red-400">
                    {data.trades.filter((t: any) => t.profit !== null && t.profit < 0).length}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-slate-400 mb-1">Win Rate</div>
                  <div className="text-lg font-bold text-white">
                    {((data.trades.filter((t: any) => t.profit > 0).length / data.trades.filter((t: any) => t.profit !== null).length) * 100).toFixed(1)}%
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}