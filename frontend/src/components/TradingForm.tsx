"use client";

import {
  Play,
  ChevronDown,
  DollarSign,
  Target,
  Timer,
  Zap,
} from "lucide-react";
import { useState }from "react";

interface Strategy {
  id: string;
  name: string;
  description: string;
  risk_level: string;
  requires_symbol?: boolean;
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

interface TradingFormProps {
  strategies: Strategy[];
  selectedStrategy: string;
  setSelectedStrategy: (strategy: string) => void;
  selectedSymbol: string;
  setSelectedSymbol: (symbol: string) => void;
  tradeAmount: number;
  setTradeAmount: (amount: number) => void;
  duration: number;
  setDuration: (duration: number) => void;
  durationUnit: string;
  setDurationUnit: (unit: string) => void;
  startTrading: () => void;
  loading: boolean;
}

export default function TradingForm({
  strategies,
  selectedStrategy,
  setSelectedStrategy,
  selectedSymbol,
  setSelectedSymbol,
  tradeAmount,
  setTradeAmount,
  duration,
  setDuration,
  durationUnit,
  setDurationUnit,
  startTrading,
  loading,
}: TradingFormProps) {
  const [showStrategyDropdown, setShowStrategyDropdown] = useState(false);
  const [showSymbolDropdown, setShowSymbolDropdown] = useState(false);
  
  const selectedStrategyData = strategies.find((s) => s.id === selectedStrategy);
  const selectedSymbolData = CRYPTO_PAIRS.find((p) => p.symbol === selectedSymbol);
  const requiresSymbol = selectedStrategyData?.requires_symbol !== false;

  return (
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
  );
}