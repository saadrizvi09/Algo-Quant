"use client";

import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { useRouter } from "next/navigation";
import { API_URL } from "@/lib/config";
import Navbar from "@/components/navbar";
import {
  TrendingUp,
  TrendingDown,
  Wallet,
  Activity,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  DollarSign,
  ShoppingCart,
  ArrowUpRight,
  ArrowDownRight,
  Loader2,
  X,
  Clock,
  Zap,
} from "lucide-react";

// ==================== TYPES ====================

interface Asset {
  symbol: string;
  name: string;
  logo: string;
  color: string;
}

interface PriceData {
  symbol: string;
  price: number;
  priceChange: number;
  priceChangePercent: number;
  high24h: number;
  low24h: number;
  volume: number;
  lastUpdate: number;
  prevPrice?: number;
}

interface Holding {
  asset: string;
  quantity: number;
  value_usdt: number;
}

interface Trade {
  id?: number;
  order_id?: string;
  symbol: string;
  side: string;
  price: number;
  quantity: number;
  total: number;
  pnl?: number;
  pnl_percent?: number;
  time: string;
}

// ==================== CONSTANTS ====================

const SUPPORTED_ASSETS: Asset[] = [
  { symbol: "BTC", name: "Bitcoin", logo: "₿", color: "#F7931A" },
  { symbol: "ETH", name: "Ethereum", logo: "Ξ", color: "#627EEA" },
  { symbol: "SOL", name: "Solana", logo: "◎", color: "#14F195" },
  { symbol: "LINK", name: "Chainlink", logo: "⬡", color: "#2A5ADA" },
  { symbol: "DOGE", name: "Dogecoin", logo: "Ð", color: "#C2A633" },
  { symbol: "BNB", name: "BNB", logo: "⬡", color: "#F3BA2F" },
];

const QUICK_BUY_AMOUNTS = [25, 50, 100, 250, 500];
const QUICK_SELL_PERCENTAGES = [25, 50, 75, 100];

// ==================== MAIN COMPONENT ====================

export default function MarketPage() {
  const router = useRouter();

  // WebSocket & Prices
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const [prices, setPrices] = useState<Record<string, PriceData>>({});
  const [wsStatus, setWsStatus] = useState<"connecting" | "connected" | "disconnected">("disconnected");

  // Portfolio & Trades
  const [portfolio, setPortfolio] = useState<{ total_value_usdt: number; holdings: Holding[] } | null>(null);
  const [portfolioLoading, setPortfolioLoading] = useState(true);
  const [recentTrades, setRecentTrades] = useState<Trade[]>([]);

  // UI States
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  // Buy Modal State
  const [buyModalOpen, setBuyModalOpen] = useState(false);
  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);
  const [buyAmount, setBuyAmount] = useState<string>("100");
  const [buyLoading, setBuyLoading] = useState(false);

  // Sell Modal State
  const [sellModalOpen, setSellModalOpen] = useState(false);
  const [sellAsset, setSellAsset] = useState<Asset | null>(null);
  const [sellQuantity, setSellQuantity] = useState<string>("");
  const [sellLoading, setSellLoading] = useState(false);
  const [costBasisInfo, setCostBasisInfo] = useState<{
    avg_cost_basis: number;
    total_invested: number;
    unrealized_pnl: number;
    unrealized_pnl_percent: number;
  } | null>(null);
  const [costBasisLoading, setCostBasisLoading] = useState(false);

  // ==================== AUTH HELPERS ====================

  const getAuthHeaders = useCallback(() => {
    const token = localStorage.getItem("token");
    return {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    };
  }, []);

  // ==================== DATA FETCHING ====================

  const fetchPortfolio = useCallback(async (isInitialLoad = false) => {
    if (isInitialLoad) setPortfolioLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/simulated/portfolio`, {
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        const holdings = data.assets.map((asset: { symbol: string; balance: number; value_usdt: number }) => ({
          asset: asset.symbol,
          quantity: asset.balance,
          value_usdt: asset.value_usdt,
        }));
        setPortfolio({
          total_value_usdt: data.total_value_usdt,
          holdings: holdings,
        });
      } else if (res.status === 401) {
        router.push("/auth");
      }
    } catch (err) {
      console.error("Failed to fetch portfolio", err);
    } finally {
      if (isInitialLoad) setPortfolioLoading(false);
    }
  }, [getAuthHeaders, router]);

  const fetchTrades = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/api/market/trades?limit=20`, {
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

  const handleRefresh = async () => {
    setRefreshing(true);
    await Promise.all([fetchPortfolio(false), fetchTrades()]);
    setRefreshing(false);
  };

  // ==================== WEBSOCKET ====================

  const connectWebSocket = useCallback(() => {
    // Prevent double connections in React Strict Mode
    if (wsRef.current?.readyState === WebSocket.OPEN || wsRef.current?.readyState === WebSocket.CONNECTING) {
      return;
    }

    setWsStatus("connecting");

    // Build combined stream URL for all assets
    const streams = SUPPORTED_ASSETS.map((a) => `${a.symbol.toLowerCase()}usdt@ticker`).join("/");
    const wsUrl = `wss://stream.binance.com:9443/ws/${streams}`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("[WebSocket] Connected to Binance");
      setWsStatus("connected");
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.s && data.c) {
          // data.s = symbol (e.g., "BTCUSDT")
          // data.c = current price
          // data.P = 24h price change percent
          // data.p = 24h price change
          // data.h = 24h high
          // data.l = 24h low
          // data.v = 24h volume

          const symbol = data.s.replace("USDT", "");
          const newPrice = parseFloat(data.c);

          setPrices((prev) => {
            const prevData = prev[symbol];
            return {
              ...prev,
              [symbol]: {
                symbol,
                price: newPrice,
                priceChange: parseFloat(data.p) || 0,
                priceChangePercent: parseFloat(data.P) || 0,
                high24h: parseFloat(data.h) || 0,
                low24h: parseFloat(data.l) || 0,
                volume: parseFloat(data.v) || 0,
                lastUpdate: Date.now(),
                prevPrice: prevData?.price,
              },
            };
          });
        }
      } catch (err) {
        console.error("[WebSocket] Parse error:", err);
      }
    };

    ws.onerror = () => {
      // WebSocket error events don't contain useful info in browsers
      // The actual error details come through onclose
      console.warn("[WebSocket] Connection error occurred");
      setWsStatus("disconnected");
    };

    ws.onclose = (event) => {
      console.log("[WebSocket] Disconnected", event.code ? `(Code: ${event.code})` : "");
      setWsStatus("disconnected");
      wsRef.current = null;

      // Auto-reconnect after 5 seconds
      if (!reconnectTimeoutRef.current) {
        reconnectTimeoutRef.current = setTimeout(() => {
          reconnectTimeoutRef.current = null;
          connectWebSocket();
        }, 5000);
      }
    };
  }, []);

  // ==================== BUY/SELL HANDLERS ====================

  const openBuyModal = (asset: Asset) => {
    setSelectedAsset(asset);
    setBuyAmount("100");
    setBuyModalOpen(true);
  };

  const fetchCostBasis = async (symbol: string) => {
    setCostBasisLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/market/cost-basis/${symbol}`, {
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        setCostBasisInfo({
          avg_cost_basis: data.avg_cost_basis,
          total_invested: data.total_invested,
          unrealized_pnl: data.unrealized_pnl,
          unrealized_pnl_percent: data.unrealized_pnl_percent,
        });
      }
    } catch (err) {
      console.error("Failed to fetch cost basis", err);
    } finally {
      setCostBasisLoading(false);
    }
  };

  const openSellModal = (asset: Asset) => {
    setSellAsset(asset);
    const holding = portfolio?.holdings.find((h) => h.asset === asset.symbol);
    setSellQuantity(holding ? holding.quantity.toString() : "0");
    setCostBasisInfo(null);
    setSellModalOpen(true);
    fetchCostBasis(asset.symbol);
  };

  const handleBuy = async () => {
    if (!selectedAsset || !buyAmount) return;

    const amount = parseFloat(buyAmount);
    if (isNaN(amount) || amount <= 0) {
      setError("Please enter a valid amount");
      return;
    }

    setBuyLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_URL}/api/market/buy`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({
          symbol: selectedAsset.symbol,
          usdt_amount: amount,
        }),
      });

      const data = await res.json();

      if (res.ok) {
        setSuccess(`Successfully bought ${data.trade.quantity.toFixed(8)} ${selectedAsset.symbol}`);
        setBuyModalOpen(false);
        await Promise.all([fetchPortfolio(), fetchTrades()]);
      } else {
        setError(data.detail || "Failed to execute buy order");
      }
    } catch (err) {
      setError("Network error. Please try again.");
    } finally {
      setBuyLoading(false);
    }
  };

  const handleSell = async () => {
    if (!sellAsset || !sellQuantity) return;

    const quantity = parseFloat(sellQuantity);
    if (isNaN(quantity) || quantity <= 0) {
      setError("Please enter a valid quantity");
      return;
    }

    setSellLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_URL}/api/market/sell`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({
          symbol: sellAsset.symbol,
          quantity: quantity,
        }),
      });

      const data = await res.json();

      if (res.ok) {
        const pnlText = data.trade.pnl !== undefined 
          ? ` | P&L: ${data.trade.pnl >= 0 ? '+' : ''}$${data.trade.pnl.toFixed(2)} (${data.trade.pnl_percent >= 0 ? '+' : ''}${data.trade.pnl_percent.toFixed(2)}%)`
          : '';
        setSuccess(`Successfully sold ${data.trade.quantity.toFixed(8)} ${sellAsset.symbol}${pnlText}`);
        setSellModalOpen(false);
        await Promise.all([fetchPortfolio(), fetchTrades()]);
      } else {
        setError(data.detail || "Failed to execute sell order");
      }
    } catch (err) {
      setError("Network error. Please try again.");
    } finally {
      setSellLoading(false);
    }
  };

  const handleSellPercent = async (percentage: number) => {
    if (!sellAsset) return;

    setSellLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_URL}/api/market/sell-percent`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({
          symbol: sellAsset.symbol,
          percentage: percentage,
        }),
      });

      const data = await res.json();

      if (res.ok) {
        const pnlText = data.trade.pnl !== undefined 
          ? ` | P&L: ${data.trade.pnl >= 0 ? '+' : ''}$${data.trade.pnl.toFixed(2)} (${data.trade.pnl_percent >= 0 ? '+' : ''}${data.trade.pnl_percent.toFixed(2)}%)`
          : '';
        setSuccess(`Successfully sold ${percentage}% of ${sellAsset.symbol}${pnlText}`);
        setSellModalOpen(false);
        await Promise.all([fetchPortfolio(), fetchTrades()]);
      } else {
        setError(data.detail || "Failed to execute sell order");
      }
    } catch (err) {
      setError("Network error. Please try again.");
    } finally {
      setSellLoading(false);
    }
  };

  // ==================== EFFECTS ====================

  useEffect(() => {
    // Check authentication
    const token = localStorage.getItem("token");
    if (!token) {
      router.push("/auth");
      return;
    }

    // Initial data fetch (parallel for faster loading)
    Promise.all([fetchPortfolio(true), fetchTrades()]);

    // Connect WebSocket
    connectWebSocket();

    // Cleanup on unmount
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
    };
  }, [connectWebSocket, fetchPortfolio, fetchTrades, router]);

  // Auto-clear notifications
  useEffect(() => {
    if (error || success) {
      const timer = setTimeout(() => {
        setError(null);
        setSuccess(null);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [error, success]);

  // ==================== COMPUTED VALUES ====================

  const usdtBalance = useMemo(() => {
    const holding = portfolio?.holdings.find((h) => h.asset === "USDT");
    return holding?.quantity || 0;
  }, [portfolio]);

  // Calculate real-time portfolio value using live WebSocket prices
  const livePortfolioValue = useMemo(() => {
    if (!portfolio) return null;

    let totalValue = 0;
    const updatedHoldings = portfolio.holdings.map(holding => {
      if (holding.asset === "USDT") {
        totalValue += holding.quantity;
        return holding;
      }

      // Use live price if available, otherwise use stored value
      const livePrice = prices[holding.asset]?.price;
      const value = livePrice ? holding.quantity * livePrice : holding.value_usdt;
      totalValue += value;

      return {
        ...holding,
        value_usdt: value,
      };
    });

    return {
      total_value_usdt: totalValue,
      holdings: updatedHoldings,
    };
  }, [portfolio, prices]);

  const getHoldingForAsset = (symbol: string) => {
    return livePortfolioValue?.holdings.find((h) => h.asset === symbol) || portfolio?.holdings.find((h) => h.asset === symbol);
  };

  // ==================== RENDER ====================

  return (
    <div className="min-h-screen bg-[#0B0E14] text-white">
      <Navbar />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-white flex items-center gap-3">
              <Activity className="w-8 h-8 text-cyan-400" />
              Market
            </h1>
            <p className="text-slate-400 mt-1">Live prices & manual trading</p>
          </div>

          <div className="flex items-center gap-4">
            {/* WebSocket Status */}
            <div className="flex items-center gap-2">
              <div
                className={`w-2 h-2 rounded-full ${
                  wsStatus === "connected"
                    ? "bg-green-500"
                    : wsStatus === "connecting"
                    ? "bg-yellow-500 animate-pulse"
                    : "bg-red-500"
                }`}
              />
              <span className="text-xs text-slate-400">
                {wsStatus === "connected" ? "Live" : wsStatus === "connecting" ? "Connecting..." : "Offline"}
              </span>
            </div>

            {/* Refresh Button */}
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? "animate-spin" : ""}`} />
              Refresh
            </button>
          </div>
        </div>

        {/* Notifications */}
        {(error || success) && (
          <div
            className={`mb-6 p-4 rounded-xl border flex items-center gap-3 ${
              error
                ? "bg-red-500/10 border-red-500/30 text-red-400"
                : "bg-green-500/10 border-green-500/30 text-green-400"
            }`}
          >
            {error ? <AlertCircle className="w-5 h-5" /> : <CheckCircle className="w-5 h-5" />}
            <span className="flex-1">{error || success}</span>
            <button onClick={() => { setError(null); setSuccess(null); }}>
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Balance Card */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
          <div className="bg-gradient-to-br from-cyan-500/10 to-blue-600/10 border border-cyan-500/20 rounded-2xl p-6">
            <div className="flex items-center gap-3 mb-2">
              <Wallet className="w-5 h-5 text-cyan-400" />
              <span className="text-slate-400 text-sm">Available USDT</span>
            </div>
            {portfolioLoading ? (
              <div className="h-8 w-32 bg-white/10 animate-pulse rounded" />
            ) : (
              <div className="text-2xl font-bold text-white">${usdtBalance.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
            )}
          </div>

          <div className="bg-[#151B26] border border-white/5 rounded-2xl p-6">
            <div className="flex items-center gap-3 mb-2">
              <DollarSign className="w-5 h-5 text-green-400" />
              <span className="text-slate-400 text-sm">Portfolio Value</span>
            </div>
            {portfolioLoading ? (
              <div className="h-8 w-32 bg-white/10 animate-pulse rounded" />
            ) : (
              <div className="text-2xl font-bold text-white">
                ${((livePortfolioValue?.total_value_usdt || portfolio?.total_value_usdt || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }))}
              </div>
            )}
          </div>

          <div className="bg-[#151B26] border border-white/5 rounded-2xl p-6">
            <div className="flex items-center gap-3 mb-2">
              <Zap className="w-5 h-5 text-yellow-400" />
              <span className="text-slate-400 text-sm">Active Assets</span>
            </div>
            {portfolioLoading ? (
              <div className="h-8 w-16 bg-white/10 animate-pulse rounded" />
            ) : (
              <div className="text-2xl font-bold text-white">
                {portfolio?.holdings.filter((h) => h.asset !== "USDT" && h.quantity > 0.00000001).length || 0}
              </div>
            )}
          </div>
        </div>

        {/* Live Prices Table */}
        <div className="bg-[#151B26] border border-white/5 rounded-2xl overflow-hidden mb-8">
          <div className="p-6 border-b border-white/5">
            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
              <Activity className="w-5 h-5 text-cyan-400" />
              Live Prices
            </h2>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-[#0B0E14]">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase">Asset</th>
                  <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400 uppercase">Price</th>
                  <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400 uppercase">24h Change</th>
                  <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400 uppercase">24h Volume</th>
                  <th className="px-6 py-4 text-right text-xs font-semibold text-slate-400 uppercase">Holdings</th>
                  <th className="px-6 py-4 text-center text-xs font-semibold text-slate-400 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {SUPPORTED_ASSETS.map((asset) => {
                  const priceData = prices[asset.symbol];
                  const holding = getHoldingForAsset(asset.symbol);
                  const isUp = priceData?.priceChangePercent >= 0;
                  const tickUp = priceData?.prevPrice && priceData.price > priceData.prevPrice;
                  const tickDown = priceData?.prevPrice && priceData.price < priceData.prevPrice;

                  return (
                    <tr key={asset.symbol} className="hover:bg-white/5 transition">
                      {/* Asset */}
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div
                            className="w-10 h-10 rounded-full flex items-center justify-center text-lg font-bold"
                            style={{ backgroundColor: `${asset.color}20`, color: asset.color }}
                          >
                            {asset.logo}
                          </div>
                          <div>
                            <div className="font-semibold text-white">{asset.symbol}</div>
                            <div className="text-xs text-slate-400">{asset.name}</div>
                          </div>
                        </div>
                      </td>

                      {/* Price with tick animation */}
                      <td className="px-6 py-4 text-right">
                        <div
                          className={`font-mono font-semibold text-lg transition-colors duration-300 ${
                            tickUp ? "text-green-400" : tickDown ? "text-red-400" : "text-white"
                          }`}
                        >
                          ${priceData?.price?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || "—"}
                        </div>
                      </td>

                      {/* 24h Change */}
                      <td className="px-6 py-4 text-right">
                        {priceData ? (
                          <div className={`flex items-center justify-end gap-1 ${isUp ? "text-green-400" : "text-red-400"}`}>
                            {isUp ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
                            <span className="font-medium">{Math.abs(priceData.priceChangePercent).toFixed(2)}%</span>
                          </div>
                        ) : (
                          <span className="text-slate-500">—</span>
                        )}
                      </td>

                      {/* Volume */}
                      <td className="px-6 py-4 text-right text-slate-400 text-sm">
                        {priceData?.volume
                          ? `${(priceData.volume / 1000000).toFixed(2)}M`
                          : "—"}
                      </td>

                      {/* Holdings */}
                      <td className="px-6 py-4 text-right">
                        {holding && holding.quantity > 0.00000001 ? (
                          <div>
                            <div className="font-medium text-white">{holding.quantity.toFixed(6)}</div>
                            <div className="text-xs text-slate-400">${holding.value_usdt.toFixed(2)}</div>
                          </div>
                        ) : (
                          <span className="text-slate-500">—</span>
                        )}
                      </td>

                      {/* Actions */}
                      <td className="px-6 py-4">
                        <div className="flex items-center justify-center gap-2">
                          <button
                            onClick={() => openBuyModal(asset)}
                            className="px-4 py-2 bg-green-500/10 hover:bg-green-500/20 text-green-400 rounded-lg text-sm font-medium transition-colors flex items-center gap-1"
                          >
                            <ShoppingCart className="w-4 h-4" />
                            Buy
                          </button>
                          {holding && holding.quantity > 0.00000001 && (
                            <button
                              onClick={() => openSellModal(asset)}
                              className="px-4 py-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-lg text-sm font-medium transition-colors flex items-center gap-1"
                            >
                              <TrendingDown className="w-4 h-4" />
                              Sell
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Portfolio & Recent Trades */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Holdings */}
          <div className="bg-[#151B26] border border-white/5 rounded-2xl p-6">
            <h3 className="font-semibold text-white mb-6 flex items-center gap-2">
              <Wallet className="w-5 h-5 text-cyan-400" />
              Your Holdings
            </h3>
            {portfolio?.holdings && portfolio.holdings.filter((h) => h.quantity > 0.00000001).length > 0 ? (
              <div className="space-y-3">
                {portfolio.holdings
                  .filter((h) => h.quantity > 0.00000001)
                  .sort((a, b) => b.value_usdt - a.value_usdt)
                  .map((holding) => {
                    const asset = SUPPORTED_ASSETS.find((a) => a.symbol === holding.asset);
                    return (
                      <div
                        key={holding.asset}
                        className="p-4 bg-[#0B0E14] rounded-xl border border-white/5 flex justify-between items-center"
                      >
                        <div className="flex items-center gap-3">
                          {asset ? (
                            <div
                              className="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold"
                              style={{ backgroundColor: `${asset.color}20`, color: asset.color }}
                            >
                              {asset.logo}
                            </div>
                          ) : (
                            <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center text-sm font-bold text-slate-300">
                              {holding.asset.charAt(0)}
                            </div>
                          )}
                          <div>
                            <div className="font-semibold text-white">{holding.asset}</div>
                            <div className="text-xs text-slate-400">
                              {holding.asset === "USDT" ? holding.quantity.toFixed(2) : holding.quantity.toFixed(6)}
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="font-semibold text-white">${holding.value_usdt.toFixed(2)}</div>
                        </div>
                      </div>
                    );
                  })}
              </div>
            ) : (
              <div className="text-center py-12 text-slate-400">
                <Wallet className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No holdings yet</p>
                <p className="text-sm text-slate-500 mt-1">Start trading to build your portfolio</p>
              </div>
            )}
          </div>

          {/* Recent Trades */}
          <div className="bg-[#151B26] border border-white/5 rounded-2xl overflow-hidden">
            <div className="p-6 border-b border-white/5">
              <h3 className="font-semibold text-white flex items-center gap-2">
                <Clock className="w-5 h-5 text-cyan-400" />
                Recent Manual Trades
              </h3>
            </div>

            {recentTrades.length === 0 ? (
              <div className="text-center py-12 text-slate-400">
                <Clock className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No recent trades</p>
                <p className="text-sm text-slate-500 mt-1">Your manual trades will appear here</p>
              </div>
            ) : (
              <div className="overflow-x-auto max-h-[400px] overflow-y-auto">
                <table className="w-full">
                  <thead className="bg-[#0B0E14] sticky top-0">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Time</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Pair</th>
                      <th className="px-4 py-3 text-center text-xs font-semibold text-slate-400 uppercase">Type</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-slate-400 uppercase">Amount</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-slate-400 uppercase">Price</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-slate-400 uppercase">P&L</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {recentTrades.map((trade, idx) => {
                      return (
                        <tr key={trade.order_id || idx} className="hover:bg-white/5 transition">
                          <td className="px-4 py-3 text-sm text-slate-400">
                            {new Date(trade.time).toLocaleString(undefined, {
                              month: "short",
                              day: "numeric",
                              hour: "2-digit",
                              minute: "2-digit",
                            })}
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-2">
                              <span className="font-semibold text-white text-sm">{trade.symbol.replace('USDT', '')}</span>
                              <span className="text-xs text-slate-500">/USDT</span>
                            </div>
                          </td>
                          <td className="px-4 py-3 text-center">
                            <span
                              className={`inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-bold ${
                                trade.side === "BUY"
                                  ? "bg-green-500/20 text-green-400 border border-green-500/30"
                                  : "bg-red-500/20 text-red-400 border border-red-500/30"
                              }`}
                            >
                              {trade.side === "BUY" ? (
                                <ArrowDownRight className="w-3 h-3" />
                              ) : (
                                <ArrowUpRight className="w-3 h-3" />
                              )}
                              {trade.side}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-right">
                            <div className="text-sm font-medium text-white">${trade.total.toFixed(2)}</div>
                            <div className="text-xs text-slate-500">{trade.quantity.toFixed(6)} {trade.symbol.replace('USDT', '')}</div>
                          </td>
                          <td className="px-4 py-3 text-right text-sm text-slate-300">
                            ${trade.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                          </td>
                          <td className="px-4 py-3 text-right">
                            {trade.side === "SELL" && trade.pnl !== undefined && trade.pnl !== null ? (
                              <div className={`flex flex-col items-end ${trade.pnl >= 0 ? "text-green-400" : "text-red-400"}`}>
                                <span className="font-bold text-sm">
                                  {trade.pnl >= 0 ? "+" : ""}${Math.abs(trade.pnl).toFixed(2)}
                                </span>
                                {trade.pnl_percent !== undefined && trade.pnl_percent !== null && (
                                  <span className={`text-xs font-medium px-1.5 py-0.5 rounded ${trade.pnl >= 0 ? "bg-green-500/20" : "bg-red-500/20"}`}>
                                    {trade.pnl_percent >= 0 ? "+" : ""}{trade.pnl_percent.toFixed(2)}%
                                  </span>
                                )}
                              </div>
                            ) : trade.side === "BUY" ? (
                              <span className="text-xs text-slate-500 bg-slate-500/10 px-2 py-1 rounded">OPEN</span>
                            ) : (
                              <span className="text-slate-500">—</span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Buy Modal */}
      {buyModalOpen && selectedAsset && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#151B26] border border-white/10 rounded-2xl w-full max-w-md p-6 shadow-2xl">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold text-white flex items-center gap-2">
                <ShoppingCart className="w-5 h-5 text-green-400" />
                Buy {selectedAsset.symbol}
              </h3>
              <button
                onClick={() => setBuyModalOpen(false)}
                className="text-slate-400 hover:text-white transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Current Price */}
            <div className="bg-[#0B0E14] rounded-xl p-4 mb-6 border border-white/5">
              <div className="text-sm text-slate-400 mb-1">Current Price</div>
              <div className="text-2xl font-bold text-white">
                ${prices[selectedAsset.symbol]?.price?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || "—"}
              </div>
            </div>

            {/* Available Balance */}
            <div className="flex justify-between text-sm mb-4">
              <span className="text-slate-400">Available:</span>
              <span className="text-white font-medium">{usdtBalance.toFixed(2)} USDT</span>
            </div>

            {/* Quick Amount Buttons */}
            <div className="flex flex-wrap gap-2 mb-4">
              {QUICK_BUY_AMOUNTS.map((amount) => (
                <button
                  key={amount}
                  onClick={() => setBuyAmount(amount.toString())}
                  disabled={amount > usdtBalance}
                  className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    buyAmount === amount.toString()
                      ? "bg-green-500/20 text-green-400 border border-green-500/30"
                      : "bg-white/5 text-slate-300 hover:bg-white/10 disabled:opacity-50 disabled:cursor-not-allowed"
                  }`}
                >
                  ${amount}
                </button>
              ))}
              <button
                onClick={() => setBuyAmount(usdtBalance.toFixed(2))}
                disabled={usdtBalance <= 0}
                className="px-3 py-2 rounded-lg text-sm font-medium bg-white/5 text-slate-300 hover:bg-white/10 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Max
              </button>
            </div>

            {/* Amount Input */}
            <div className="mb-6">
              <label className="block text-sm text-slate-400 mb-2">Amount (USDT)</label>
              <input
                type="number"
                value={buyAmount}
                onChange={(e) => setBuyAmount(e.target.value)}
                placeholder="Enter amount"
                className="w-full px-4 py-3 bg-[#0B0E14] border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50 transition"
              />
              {prices[selectedAsset.symbol]?.price && buyAmount && (
                <div className="mt-2 text-sm text-slate-400">
                  ≈ {(parseFloat(buyAmount) / prices[selectedAsset.symbol].price).toFixed(6)} {selectedAsset.symbol}
                </div>
              )}
            </div>

            {/* Error Message */}
            {error && (
              <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm flex items-center gap-2">
                <AlertCircle className="w-4 h-4" />
                {error}
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-3">
              <button
                onClick={() => setBuyModalOpen(false)}
                className="flex-1 px-4 py-3 bg-white/5 hover:bg-white/10 text-white rounded-xl font-medium transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleBuy}
                disabled={buyLoading || !buyAmount || parseFloat(buyAmount) <= 0 || parseFloat(buyAmount) > usdtBalance}
                className="flex-1 px-4 py-3 bg-green-500 hover:bg-green-600 text-white rounded-xl font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {buyLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <ShoppingCart className="w-4 h-4" />
                    Buy {selectedAsset.symbol}
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Sell Modal */}
      {sellModalOpen && sellAsset && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#151B26] border border-white/10 rounded-2xl w-full max-w-md p-6 shadow-2xl">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold text-white flex items-center gap-2">
                <TrendingDown className="w-5 h-5 text-red-400" />
                Sell {sellAsset.symbol}
              </h3>
              <button
                onClick={() => setSellModalOpen(false)}
                className="text-slate-400 hover:text-white transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Current Price */}
            <div className="bg-[#0B0E14] rounded-xl p-4 mb-4 border border-white/5">
              <div className="text-sm text-slate-400 mb-1">Current Price</div>
              <div className="text-2xl font-bold text-white">
                ${prices[sellAsset.symbol]?.price?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || "—"}
              </div>
            </div>

            {/* Cost Basis & PnL Info */}
            {costBasisLoading ? (
              <div className="bg-[#0B0E14] rounded-xl p-4 mb-4 border border-white/5 flex items-center justify-center">
                <Loader2 className="w-5 h-5 animate-spin text-slate-400" />
                <span className="ml-2 text-slate-400 text-sm">Loading cost basis...</span>
              </div>
            ) : costBasisInfo && costBasisInfo.avg_cost_basis > 0 ? (
              <div className="bg-[#0B0E14] rounded-xl p-4 mb-4 border border-white/5 space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Avg. Buy Price:</span>
                  <span className="text-white font-medium">
                    ${costBasisInfo.avg_cost_basis.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Total Invested:</span>
                  <span className="text-white font-medium">
                    ${costBasisInfo.total_invested.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </span>
                </div>
                <div className="border-t border-white/10 pt-3">
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400 text-sm">Unrealized P&L:</span>
                    <div className={`flex items-center gap-1 font-semibold ${costBasisInfo.unrealized_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {costBasisInfo.unrealized_pnl >= 0 ? (
                        <ArrowUpRight className="w-4 h-4" />
                      ) : (
                        <ArrowDownRight className="w-4 h-4" />
                      )}
                      <span>${Math.abs(costBasisInfo.unrealized_pnl).toFixed(2)}</span>
                      <span className="text-xs">({costBasisInfo.unrealized_pnl_percent >= 0 ? '+' : ''}{costBasisInfo.unrealized_pnl_percent.toFixed(2)}%)</span>
                    </div>
                  </div>
                </div>
              </div>
            ) : null}

            {/* Estimated PnL for Sale */}
            {prices[sellAsset.symbol]?.price && sellQuantity && parseFloat(sellQuantity) > 0 && costBasisInfo && costBasisInfo.avg_cost_basis > 0 && (
              <div className={`rounded-xl p-4 mb-4 border ${(() => {
                const qty = parseFloat(sellQuantity);
                const sellValue = qty * prices[sellAsset.symbol].price * (1 - 0.001); // after 0.1% fee
                const costBasis = qty * costBasisInfo.avg_cost_basis;
                const pnl = sellValue - costBasis;
                return pnl >= 0 ? 'bg-green-500/10 border-green-500/30' : 'bg-red-500/10 border-red-500/30';
              })()}`}>
                <div className="text-sm text-slate-400 mb-2">If you sell now:</div>
                {(() => {
                  const qty = parseFloat(sellQuantity);
                  const sellValue = qty * prices[sellAsset.symbol].price;
                  const fee = sellValue * 0.001;
                  const netValue = sellValue - fee;
                  const costBasis = qty * costBasisInfo.avg_cost_basis;
                  const pnl = netValue - costBasis;
                  const pnlPercent = costBasis > 0 ? ((netValue / costBasis) - 1) * 100 : 0;
                  
                  return (
                    <div className="flex items-center justify-between">
                      <span className={`text-lg font-bold ${pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {pnl >= 0 ? '+' : '-'}${Math.abs(pnl).toFixed(2)}
                      </span>
                      <span className={`text-sm font-medium ${pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        ({pnlPercent >= 0 ? '+' : ''}{pnlPercent.toFixed(2)}%)
                      </span>
                    </div>
                  );
                })()}
              </div>
            )}

            {/* Available Balance */}
            <div className="flex justify-between text-sm mb-4">
              <span className="text-slate-400">Available:</span>
              <span className="text-white font-medium">
                {getHoldingForAsset(sellAsset.symbol)?.quantity.toFixed(6) || "0"} {sellAsset.symbol}
              </span>
            </div>

            {/* Quick Sell Percentage Buttons */}
            <div className="flex flex-wrap gap-2 mb-4">
              {QUICK_SELL_PERCENTAGES.map((percent) => (
                <button
                  key={percent}
                  onClick={() => handleSellPercent(percent)}
                  disabled={sellLoading}
                  className="px-3 py-2 rounded-lg text-sm font-medium bg-white/5 text-slate-300 hover:bg-red-500/20 hover:text-red-400 transition-colors disabled:opacity-50"
                >
                  {percent === 100 ? "Sell All" : `${percent}%`}
                </button>
              ))}
            </div>

            {/* Quantity Input */}
            <div className="mb-6">
              <label className="block text-sm text-slate-400 mb-2">Quantity ({sellAsset.symbol})</label>
              <input
                type="number"
                value={sellQuantity}
                onChange={(e) => setSellQuantity(e.target.value)}
                placeholder="Enter quantity"
                step="0.000001"
                className="w-full px-4 py-3 bg-[#0B0E14] border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500/50 transition"
              />
              {prices[sellAsset.symbol]?.price && sellQuantity && (
                <div className="mt-2 text-sm text-slate-400">
                  ≈ ${(parseFloat(sellQuantity) * prices[sellAsset.symbol].price).toFixed(2)} USDT
                </div>
              )}
            </div>

            {/* Error Message */}
            {error && (
              <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm flex items-center gap-2">
                <AlertCircle className="w-4 h-4" />
                {error}
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-3">
              <button
                onClick={() => setSellModalOpen(false)}
                className="flex-1 px-4 py-3 bg-white/5 hover:bg-white/10 text-white rounded-xl font-medium transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSell}
                disabled={
                  sellLoading ||
                  !sellQuantity ||
                  parseFloat(sellQuantity) <= 0 ||
                  parseFloat(sellQuantity) > (getHoldingForAsset(sellAsset.symbol)?.quantity || 0)
                }
                className="flex-1 px-4 py-3 bg-red-500 hover:bg-red-600 text-white rounded-xl font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {sellLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <TrendingDown className="w-4 h-4" />
                    Sell {sellAsset.symbol}
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
