"use client";

import { Wallet, BarChart3, Clock, TrendingUp, TrendingDown } from "lucide-react";

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

interface PortfolioProps {
  portfolio: {
    total_value_usdt: number;
    holdings: Holding[];
  } | null;
  recentTrades: Trade[];
}

export default function Portfolio({ portfolio, recentTrades }: PortfolioProps) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Holdings */}
      <div className="bg-[#151B26] border border-white/5 rounded-2xl p-6 shadow-2xl">
        <h3 className="font-semibold text-white mb-6 flex items-center gap-2">
          <Wallet className="w-5 h-5 text-cyan-400" />
          Holdings
        </h3>
        {portfolio?.holdings && portfolio.holdings.length > 0 ? (
          <div className="space-y-4">
            {portfolio.holdings.map((holding) => (
              <div
                key={holding.asset}
                className="p-4 bg-[#0B0E14] rounded-xl border border-white/5 flex justify-between items-center"
              >
                <div>
                  <div className="font-semibold text-white">{holding.asset}</div>
                  <div className="text-xs text-slate-400">{holding.quantity.toFixed(6)}</div>
                </div>
                <div className="text-right">
                  <div className="font-semibold text-white">${holding.value_usdt.toFixed(2)}</div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12 text-slate-400">
            <BarChart3 className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>No holdings</p>
            <p className="text-sm text-slate-500 mt-1">Your assets will appear here</p>
          </div>
        )}
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
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs ${
                          trade.side === "BUY"
                            ? "bg-emerald-500/20 text-emerald-400"
                            : "bg-red-500/20 text-red-400"
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
    </div>
  );
}