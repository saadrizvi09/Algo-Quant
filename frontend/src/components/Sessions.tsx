"use client";

import { Activity, Clock, Square } from "lucide-react";

interface Session {
  session_id: string;
  strategy: string;
  symbol: string;
  is_running: boolean;
  position: string;
  trades_count: number;
  pnl: number;
  elapsed_minutes: number;
  remaining_minutes: number;
}

interface SessionsProps {
  activeSessions: Session[];
  stopTrading: (sessionId: string) => void;
}

export default function Sessions({ activeSessions, stopTrading }: SessionsProps) {
  return (
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
                  <div
                    className={`px-2 py-1 rounded-full text-xs ${
                      session.is_running
                        ? "bg-emerald-500/20 text-emerald-400"
                        : "bg-slate-500/20 text-slate-400"
                    }`}
                  >
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
                        width: `${
                          ((session.elapsed_minutes) / (session.elapsed_minutes + session.remaining_minutes)) * 100
                        }%`,
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
  );
}