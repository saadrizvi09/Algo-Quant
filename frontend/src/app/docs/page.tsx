"use client";

import React, { useState, useEffect } from "react";
import { ArrowLeft, Book, Code, Terminal, Cpu, TrendingUp, BarChart3, Activity, Zap, Shield, AlertCircle } from "lucide-react";
import { useRouter } from "next/navigation";

export default function DocsPage() {
  const router = useRouter();
  const [activeSection, setActiveSection] = useState("introduction");

  // Track scroll position and update active section
  useEffect(() => {
    const handleScroll = () => {
      const sections = [
        "introduction",
        "installation",
        "quickstart",
        "hmm-strategy",
        "backtesting",
        "risk-management",
        "live-trading",
        "api-endpoints",
        "code-examples"
      ];

      // Find which section is currently in view
      let currentSection = "introduction";
      let minDistance = Infinity;
      
      for (const sectionId of sections) {
        const element = document.getElementById(sectionId);
        if (element) {
          const rect = element.getBoundingClientRect();
          // Calculate distance from top of viewport (with offset)
          const distance = Math.abs(rect.top - 100);
          
          // If section is above the viewport center and closer than previous
          if (rect.top <= 100 && distance < minDistance) {
            minDistance = distance;
            currentSection = sectionId;
          }
        }
      }
      
      setActiveSection(currentSection);
    };

    // Add scroll listener with throttle for better performance
    let timeoutId: NodeJS.Timeout;
    const throttledScroll = () => {
      if (timeoutId) clearTimeout(timeoutId);
      timeoutId = setTimeout(handleScroll, 50);
    };

    window.addEventListener("scroll", throttledScroll, { passive: true });
    // Call once on mount to set initial state
    handleScroll();

    // Cleanup
    return () => {
      window.removeEventListener("scroll", throttledScroll);
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, []);

  const scrollToSection = (id: string) => {
    setActiveSection(id);
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  return (
    <div className="min-h-screen bg-[#0B0E14] text-slate-300 font-sans selection:bg-cyan-500/30">
      {/* Navigation */}
      <nav className="sticky top-0 z-50 border-b border-white/10 bg-[#0B0E14]/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div 
            onClick={() => router.push("/")}
            className="flex items-center gap-2 cursor-pointer hover:opacity-80 transition-opacity"
          >
            <div className="w-8 h-8 bg-gradient-to-tr from-cyan-500 to-blue-600 rounded-lg flex items-center justify-center">
              <Cpu size={16} className="text-white" />
            </div>
            <span className="font-bold text-white tracking-tight">AlgoQuant <span className="text-cyan-400">Docs</span></span>
          </div>
          <button 
            onClick={() => router.push("/")}
            className="text-sm font-medium text-slate-400 hover:text-white flex items-center gap-2 transition-colors"
          >
            <ArrowLeft size={16} /> Back to Home
          </button>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-6 py-12 grid grid-cols-1 lg:grid-cols-4 gap-12">
        {/* Sidebar */}
        <aside className="hidden lg:block space-y-8 sticky top-28 h-fit">
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">Getting Started</h3>
            <ul className="space-y-2 border-l border-white/10 ml-1">
              <li 
                onClick={() => scrollToSection("introduction")}
                className={`pl-4 border-l ${activeSection === "introduction" ? "border-cyan-500 text-cyan-400" : "border-transparent hover:border-white/30 hover:text-white"} font-medium cursor-pointer transition-all`}
              >
                Introduction
              </li>
              <li 
                onClick={() => scrollToSection("installation")}
                className={`pl-4 border-l ${activeSection === "installation" ? "border-cyan-500 text-cyan-400" : "border-transparent hover:border-white/30 hover:text-white"} cursor-pointer transition-all`}
              >
                Installation
              </li>
              <li 
                onClick={() => scrollToSection("quickstart")}
                className={`pl-4 border-l ${activeSection === "quickstart" ? "border-cyan-500 text-cyan-400" : "border-transparent hover:border-white/30 hover:text-white"} cursor-pointer transition-all`}
              >
                Quick Start
              </li>
            </ul>
          </div>
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">Core Concepts</h3>
            <ul className="space-y-2 border-l border-white/10 ml-1">
              <li 
                onClick={() => scrollToSection("hmm-strategy")}
                className={`pl-4 border-l ${activeSection === "hmm-strategy" ? "border-cyan-500 text-cyan-400" : "border-transparent hover:border-white/30 hover:text-white"} cursor-pointer transition-all`}
              >
                HMM Strategy
              </li>
              <li 
                onClick={() => scrollToSection("backtesting")}
                className={`pl-4 border-l ${activeSection === "backtesting" ? "border-cyan-500 text-cyan-400" : "border-transparent hover:border-white/30 hover:text-white"} cursor-pointer transition-all`}
              >
                Backtesting Engine
              </li>
              <li 
                onClick={() => scrollToSection("risk-management")}
                className={`pl-4 border-l ${activeSection === "risk-management" ? "border-cyan-500 text-cyan-400" : "border-transparent hover:border-white/30 hover:text-white"} cursor-pointer transition-all`}
              >
                Risk Management
              </li>
              <li 
                onClick={() => scrollToSection("live-trading")}
                className={`pl-4 border-l ${activeSection === "live-trading" ? "border-cyan-500 text-cyan-400" : "border-transparent hover:border-white/30 hover:text-white"} cursor-pointer transition-all`}
              >
                Live Trading
              </li>
            </ul>
          </div>
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">API Reference</h3>
            <ul className="space-y-2 border-l border-white/10 ml-1">
              <li 
                onClick={() => scrollToSection("api-endpoints")}
                className={`pl-4 border-l ${activeSection === "api-endpoints" ? "border-cyan-500 text-cyan-400" : "border-transparent hover:border-white/30 hover:text-white"} cursor-pointer transition-all`}
              >
                Endpoints
              </li>
              <li 
                onClick={() => scrollToSection("code-examples")}
                className={`pl-4 border-l ${activeSection === "code-examples" ? "border-cyan-500 text-cyan-400" : "border-transparent hover:border-white/30 hover:text-white"} cursor-pointer transition-all`}
              >
                Code Examples
              </li>
            </ul>
          </div>
        </aside>

        {/* Main Content */}
        <main className="lg:col-span-3 space-y-16">
          {/* Section: Intro */}
          <section id="introduction" className="space-y-6 scroll-mt-20">
            <div className="flex items-center gap-3 text-cyan-400 mb-2">
              <Book size={24} />
              <span className="font-mono text-sm">DOCS / INTRO</span>
            </div>
            <h1 className="text-4xl md:text-5xl font-bold text-white">Introduction to AlgoQuant</h1>
            <p className="text-lg leading-relaxed text-slate-400">
              AlgoQuant is a high-performance algorithmic trading platform designed for quantitative analysts and developers. 
              It leverages <strong>Hidden Markov Models (HMM)</strong> to detect market regimes and adjust trading strategies dynamically.
            </p>
            
          </section>

          {/* Section: Installation */}
          <section id="installation" className="space-y-6 pt-8 border-t border-white/5 scroll-mt-20">
            <h2 className="text-3xl font-bold text-white">Installation</h2>
            <p className="text-slate-400">
              Get started with AlgoQuant in under 2 minutes. No complex setup required.
            </p>
            
            <div className="space-y-4">
              <h3 className="text-xl font-semibold text-white flex items-center gap-2">
                <Terminal size={20} className="text-cyan-400" />
                1. Clone the Repository
              </h3>
              <div className="bg-[#151B26] border border-white/10 rounded-xl p-4 font-mono text-sm text-slate-300">
                <code>git clone https://github.com/saadrizvi09/Algo-Quant.git</code>
              </div>
            </div>

            <div className="space-y-4">
              <h3 className="text-xl font-semibold text-white">2. Install Backend Dependencies</h3>
              <div className="bg-[#151B26] border border-white/10 rounded-xl p-4 font-mono text-sm text-slate-300">
                <code>cd backend && pip install -r requirements.txt</code>
              </div>
            </div>

            <div className="space-y-4">
              <h3 className="text-xl font-semibold text-white">3. Install Frontend Dependencies</h3>
              <div className="bg-[#151B26] border border-white/10 rounded-xl p-4 font-mono text-sm text-slate-300">
                <code>cd frontend && npm install</code>
              </div>
            </div>

            <div className="p-6 bg-blue-500/5 border border-blue-500/10 rounded-2xl">
              <h4 className="text-blue-400 font-bold mb-2 flex items-center gap-2">
                <AlertCircle size={18} />
                Environment Variables
              </h4>
              <p className="text-sm text-slate-400 mb-3">
                Create a <code className="bg-white/5 px-2 py-1 rounded">.env</code> file in the backend directory with your API keys:
              </p>
              <div className="bg-[#151B26] border border-white/10 rounded-xl p-4 font-mono text-xs text-slate-300">
                <code>
                  DATABASE_URL=postgresql://user:pass@localhost/algoquant<br/>
                  BINANCE_API_KEY=your_api_key<br/>
                  BINANCE_SECRET_KEY=your_secret_key
                </code>
              </div>
            </div>
          </section>

          {/* Section: Quick Start */}
          <section id="quickstart" className="space-y-6 pt-8 border-t border-white/5 scroll-mt-20">
            <h2 className="text-3xl font-bold text-white">Quick Start</h2>
            <p className="text-slate-400">
              Get your first backtest running in under 5 minutes.
            </p>
            
            <div className="space-y-6">
              <div className="space-y-3">
                <h3 className="text-xl font-semibold text-white">1. Start the Backend</h3>
                <div className="bg-[#151B26] border border-white/10 rounded-xl p-4 font-mono text-sm text-slate-300">
                  <code>uvicorn main:app --reload</code>
                </div>
                <p className="text-sm text-slate-400">Backend runs on <code className="bg-white/5 px-2 py-1 rounded">http://localhost:8000</code></p>
              </div>

              <div className="space-y-3">
                <h3 className="text-xl font-semibold text-white">2. Start the Frontend</h3>
                <div className="bg-[#151B26] border border-white/10 rounded-xl p-4 font-mono text-sm text-slate-300">
                  <code>npm run dev</code>
                </div>
                <p className="text-sm text-slate-400">Frontend runs on <code className="bg-white/5 px-2 py-1 rounded">http://localhost:3000</code></p>
              </div>

              <div className="space-y-3">
                <h3 className="text-xl font-semibold text-white">3. Navigate to Backtest Page</h3>
                <p className="text-slate-400">
                  Go to <code className="bg-white/5 px-2 py-1 rounded">/backtest</code> and configure your first HMM strategy with BTC/USDT pair.
                </p>
              </div>
            </div>
          </section>

          {/* Section: HMM Strategy In-Depth */}
          <section id="hmm-strategy" className="space-y-8 pt-8 border-t border-white/5 scroll-mt-20">
            <div>
              <h2 className="text-3xl font-bold text-white mb-4 flex items-center gap-3">
                <Activity size={32} className="text-cyan-400" />
                Hidden Markov Model Strategy
              </h2>
              <p className="text-lg text-slate-400">
                The HMM strategy is our flagship algorithm for regime-based trading. It identifies hidden market states and adapts positions accordingly.
              </p>
            </div>

            {/* What is HMM? */}
            <div className="space-y-4">
              <h3 className="text-2xl font-bold text-white">What is a Hidden Markov Model?</h3>
              <p className="text-slate-400 leading-relaxed">
                A Hidden Markov Model is a statistical model where the system being modeled is assumed to be a Markov process with <strong>unobservable (hidden) states</strong>. In trading, these hidden states represent different <strong>market regimes</strong> like "trending", "mean-reverting", "high volatility", or "low volatility".
              </p>
              <div className="p-6 bg-gradient-to-br from-purple-500/5 to-blue-500/5 border border-purple-500/10 rounded-2xl">
                <h4 className="text-purple-400 font-bold mb-3">Key Components</h4>
                <ul className="space-y-2 text-sm text-slate-400">
                  <li className="flex items-start gap-2">
                    <span className="text-cyan-400 mt-1">•</span>
                    <span><strong>Hidden States:</strong> Unobservable market regimes (e.g., bull/bear, high/low volatility)</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-cyan-400 mt-1">•</span>
                    <span><strong>Observable Data:</strong> Price returns, volume, volatility metrics</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-cyan-400 mt-1">•</span>
                    <span><strong>Transition Matrix:</strong> Probabilities of switching between states</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-cyan-400 mt-1">•</span>
                    <span><strong>Emission Probabilities:</strong> Likelihood of observing data given a hidden state</span>
                  </li>
                </ul>
              </div>
            </div>

            {/* How It Works */}
            <div className="space-y-4">
              <h3 className="text-2xl font-bold text-white">How Our HMM Strategy Works</h3>
              <div className="space-y-6">
                <div className="p-6 bg-[#151B26] border border-white/10 rounded-2xl">
                  <div className="flex items-start gap-4">
                    <div className="w-8 h-8 rounded-full bg-cyan-500/20 text-cyan-400 flex items-center justify-center font-bold flex-shrink-0">1</div>
                    <div>
                      <h4 className="text-white font-bold mb-2">Data Collection & Preprocessing</h4>
                      <p className="text-sm text-slate-400">
                        Historical price data is fetched from Binance API. We calculate log returns and rolling volatility (20-period standard deviation) as observable features for the model.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="p-6 bg-[#151B26] border border-white/10 rounded-2xl">
                  <div className="flex items-start gap-4">
                    <div className="w-8 h-8 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center font-bold flex-shrink-0">2</div>
                    <div>
                      <h4 className="text-white font-bold mb-2">Model Training (Baum-Welch Algorithm)</h4>
                      <p className="text-sm text-slate-400 mb-3">
                        We train a <strong>2-state Gaussian HMM</strong> using the Baum-Welch expectation-maximization algorithm. The model learns:
                      </p>
                      <ul className="space-y-1 text-sm text-slate-400 ml-4">
                        <li>• <strong>State 0:</strong> Low volatility regime (mean-reverting behavior)</li>
                        <li>• <strong>State 1:</strong> High volatility regime (trending behavior)</li>
                        <li>• Transition probabilities between states</li>
                        <li>• Emission distributions (Gaussian parameters for each state)</li>
                      </ul>
                    </div>
                  </div>
                </div>

                <div className="p-6 bg-[#151B26] border border-white/10 rounded-2xl">
                  <div className="flex items-start gap-4">
                    <div className="w-8 h-8 rounded-full bg-purple-500/20 text-purple-400 flex items-center justify-center font-bold flex-shrink-0">3</div>
                    <div>
                      <h4 className="text-white font-bold mb-2">Regime Detection (Viterbi Decoding)</h4>
                      <p className="text-sm text-slate-400">
                        For each new observation, the Viterbi algorithm determines the most likely sequence of hidden states. This tells us which regime the market is currently in.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="p-6 bg-[#151B26] border border-white/10 rounded-2xl">
                  <div className="flex items-start gap-4">
                    <div className="w-8 h-8 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold flex-shrink-0">4</div>
                    <div>
                      <h4 className="text-white font-bold mb-2">Trading Logic Execution</h4>
                      <p className="text-sm text-slate-400 mb-3">Based on the detected regime, we execute different strategies:</p>
                      <div className="space-y-3">
                        <div className="bg-emerald-500/5 border border-emerald-500/10 rounded-lg p-3">
                          <p className="text-emerald-400 font-mono text-sm mb-1"><strong>State 0 (Low Volatility):</strong></p>
                          <p className="text-xs text-slate-400">Use RSI-based mean reversion. Buy when RSI &lt; 30, sell when RSI &gt; 70.</p>
                        </div>
                        <div className="bg-orange-500/5 border border-orange-500/10 rounded-lg p-3">
                          <p className="text-orange-400 font-mono text-sm mb-1"><strong>State 1 (High Volatility):</strong></p>
                          <p className="text-xs text-slate-400">Reduce position size or stay in cash to avoid whipsaws during choppy markets.</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Mathematical Foundation */}
            <div className="space-y-4">
              <h3 className="text-2xl font-bold text-white">Mathematical Foundation</h3>
              <div className="bg-[#151B26] border border-white/10 rounded-2xl p-6 space-y-4">
                <div>
                  <h4 className="text-cyan-400 font-mono text-sm mb-2">Transition Matrix A</h4>
                  <p className="text-slate-400 text-sm mb-2">Probability of transitioning from state i to state j:</p>
                  <div className="bg-[#0B0E14] p-4 rounded-lg font-mono text-xs text-slate-300">
                    A = [a<sub>ij</sub>] where a<sub>ij</sub> = P(state<sub>t+1</sub> = j | state<sub>t</sub> = i)
                  </div>
                </div>
                <div>
                  <h4 className="text-cyan-400 font-mono text-sm mb-2">Emission Probability B</h4>
                  <p className="text-slate-400 text-sm mb-2">Gaussian distribution for each state:</p>
                  <div className="bg-[#0B0E14] p-4 rounded-lg font-mono text-xs text-slate-300">
                    B<sub>i</sub>(x) = N(x | μ<sub>i</sub>, σ<sub>i</sub>²) = (1/√(2πσ<sub>i</sub>²)) exp(-(x-μ<sub>i</sub>)²/(2σ<sub>i</sub>²))
                  </div>
                </div>
                <div>
                  <h4 className="text-cyan-400 font-mono text-sm mb-2">Viterbi Algorithm</h4>
                  <p className="text-slate-400 text-sm">
                    Finds the most likely sequence of hidden states given the observed data using dynamic programming.
                  </p>
                </div>
              </div>
            </div>

            {/* Performance Metrics */}
            <div className="space-y-4">
              <h3 className="text-2xl font-bold text-white">Backtest Performance (BTC-USD, Jan 2020 - Dec 2025)</h3>
              
              {/* Top Row - Main Metrics */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-6 bg-gradient-to-br from-emerald-500/10 to-cyan-500/10 border border-emerald-500/20 rounded-2xl">
                  <div className="flex items-center gap-2 mb-3">
                    <TrendingUp size={20} className="text-emerald-400" />
                    <div className="text-xs uppercase tracking-wider text-emerald-400 font-bold">Strategy Return</div>
                  </div>
                  <div className="text-4xl font-bold text-emerald-400">2102.34%</div>
                </div>

                <div className="p-6 bg-gradient-to-br from-blue-500/10 to-cyan-500/10 border border-blue-500/20 rounded-2xl">
                  <div className="flex items-center gap-2 mb-3">
                    <Activity size={20} className="text-blue-400" />
                    <div className="text-xs uppercase tracking-wider text-blue-400 font-bold">Buy & Hold</div>
                  </div>
                  <div className="text-4xl font-bold text-blue-400">1155.26%</div>
                </div>

                <div className="p-6 bg-gradient-to-br from-purple-500/10 to-pink-500/10 border border-purple-500/20 rounded-2xl">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-2xl">$</span>
                    <div className="text-xs uppercase tracking-wider text-purple-400 font-bold">Final Balance</div>
                  </div>
                  <div className="text-3xl font-bold text-purple-400">$220,234.46</div>
                </div>

                <div className="p-6 bg-gradient-to-br from-cyan-500/10 to-blue-500/10 border border-cyan-500/20 rounded-2xl">
                  <div className="flex items-center gap-2 mb-3">
                    <BarChart3 size={20} className="text-cyan-400" />
                    <div className="text-xs uppercase tracking-wider text-cyan-400 font-bold">Win Rate</div>
                  </div>
                  <div className="text-4xl font-bold text-cyan-400">41.0%</div>
                </div>
              </div>

              {/* Bottom Row - Risk Metrics */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-5 bg-[#151B26] border border-white/10 rounded-xl">
                  <div className="text-sm text-slate-400 mb-1">Sharpe Ratio</div>
                  <div className="text-3xl font-bold text-white">1.12</div>
                </div>

                <div className="p-5 bg-[#151B26] border border-white/10 rounded-xl">
                  <div className="text-sm text-slate-400 mb-1">Sortino Ratio</div>
                  <div className="text-3xl font-bold text-white">1.27</div>
                </div>

                <div className="p-5 bg-[#151B26] border border-white/10 rounded-xl">
                  <div className="text-sm text-slate-400 mb-1">Max DD (Strategy)</div>
                  <div className="text-3xl font-bold text-red-400">-54.36%</div>
                </div>

                <div className="p-5 bg-[#151B26] border border-white/10 rounded-xl">
                  <div className="text-sm text-slate-400 mb-1">Max DD (B&H)</div>
                  <div className="text-3xl font-bold text-red-400">-76.63%</div>
                </div>
              </div>

              <div className="p-4 bg-blue-500/5 border border-blue-500/10 rounded-xl">
                <p className="text-sm text-slate-400 italic">
                  📊 <strong>Backtest Period:</strong> January 1st, 2020 → December 16th, 2025 (2176 days) • <strong>Initial Capital:</strong> $10,000 • <strong>Strategy:</strong> HMM Regime Filter with RSI signals
                </p>
              </div>
            </div>

            {/* Advantages & Limitations */}
            <div className="grid md:grid-cols-2 gap-6">
              <div className="space-y-3">
                <h3 className="text-xl font-bold text-white flex items-center gap-2">
                  <Shield size={20} className="text-emerald-400" />
                  Advantages
                </h3>
                <ul className="space-y-2 text-sm text-slate-400">
                  <li className="flex items-start gap-2">
                    <span className="text-emerald-400 mt-1">✓</span>
                    <span>Automatically adapts to changing market conditions</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-emerald-400 mt-1">✓</span>
                    <span>No need to manually define market regimes</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-emerald-400 mt-1">✓</span>
                    <span>Works well with mean-reverting assets</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-emerald-400 mt-1">✓</span>
                    <span>Reduces drawdowns during high volatility</span>
                  </li>
                </ul>
              </div>
              <div className="space-y-3">
                <h3 className="text-xl font-bold text-white flex items-center gap-2">
                  <AlertCircle size={20} className="text-orange-400" />
                  Limitations
                </h3>
                <ul className="space-y-2 text-sm text-slate-400">
                  <li className="flex items-start gap-2">
                    <span className="text-orange-400 mt-1">⚠</span>
                    <span>Requires sufficient historical data for training</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-orange-400 mt-1">⚠</span>
                    <span>May lag during sudden regime changes</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-orange-400 mt-1">⚠</span>
                    <span>Assumes Gaussian distributions (may not fit all assets)</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-orange-400 mt-1">⚠</span>
                    <span>Model retraining needed periodically</span>
                  </li>
                </ul>
              </div>
            </div>
          </section>

          {/* Section: Backtesting */}
          <section id="backtesting" className="space-y-6 pt-8 border-t border-white/5 scroll-mt-20">
            <h2 className="text-3xl font-bold text-white flex items-center gap-3">
              <BarChart3 size={32} className="text-purple-400" />
              Backtesting Engine
            </h2>
            <p className="text-slate-400">
              Our backtesting engine simulates historical trades with realistic slippage, fees, and execution delays.
            </p>
            
            <div className="space-y-4">
              <h3 className="text-xl font-semibold text-white">Features</h3>
              <div className="grid md:grid-cols-2 gap-4">
                <div className="p-4 bg-[#151B26] border border-white/10 rounded-xl">
                  <h4 className="text-white font-bold mb-2">Walk-Forward Analysis</h4>
                  <p className="text-sm text-slate-400">Retrain the model every 3 months on rolling windows to prevent overfitting.</p>
                </div>
                <div className="p-4 bg-[#151B26] border border-white/10 rounded-xl">
                  <h4 className="text-white font-bold mb-2">Transaction Costs</h4>
                  <p className="text-sm text-slate-400">Includes 0.1% trading fees and 0.05% slippage on each trade.</p>
                </div>
                <div className="p-4 bg-[#151B26] border border-white/10 rounded-xl">
                  <h4 className="text-white font-bold mb-2">Performance Metrics</h4>
                  <p className="text-sm text-slate-400">Sharpe ratio, max drawdown, win rate, and profit factor calculated automatically.</p>
                </div>
                <div className="p-4 bg-[#151B26] border border-white/10 rounded-xl">
                  <h4 className="text-white font-bold mb-2">Visual Analytics</h4>
                  <p className="text-sm text-slate-400">Interactive equity curves, drawdown charts, and trade distribution plots.</p>
                </div>
              </div>
            </div>
          </section>

          {/* Section: Risk Management */}
          <section id="risk-management" className="space-y-6 pt-8 border-t border-white/5 scroll-mt-20">
            <h2 className="text-3xl font-bold text-white flex items-center gap-3">
              <Shield size={32} className="text-emerald-400" />
              Risk Management
            </h2>
            <p className="text-slate-400">
              Built-in risk controls to protect your capital during adverse market conditions.
            </p>
            
            <div className="space-y-4">
              <div className="p-6 bg-[#151B26] border border-white/10 rounded-2xl">
                <h4 className="text-white font-bold mb-3">Position Sizing</h4>
                <p className="text-sm text-slate-400 mb-2">
                  Default position size is 10% of portfolio per trade. Automatically reduces to 5% during high volatility regimes.
                </p>
              </div>
              <div className="p-6 bg-[#151B26] border border-white/10 rounded-2xl">
                <h4 className="text-white font-bold mb-3">Stop Loss</h4>
                <p className="text-sm text-slate-400 mb-2">
                  Hard stop at -5% from entry price. Trailing stop activated at +3% profit.
                </p>
              </div>
              <div className="p-6 bg-[#151B26] border border-white/10 rounded-2xl">
                <h4 className="text-white font-bold mb-3">Max Daily Loss</h4>
                <p className="text-sm text-slate-400 mb-2">
                  Trading halts if portfolio loses more than 2% in a single day.
                </p>
              </div>
            </div>
          </section>

          {/* Section: Live Trading */}
          <section id="live-trading" className="space-y-6 pt-8 border-t border-white/5 scroll-mt-20">
            <h2 className="text-3xl font-bold text-white flex items-center gap-3">
              <Zap size={32} className="text-yellow-400" />
              Live Trading
            </h2>
            <p className="text-slate-400">
              Deploy your backtested strategies to live markets with paper trading or real funds.
            </p>
            
            <div className="p-6 bg-yellow-500/5 border border-yellow-500/10 rounded-2xl">
              <h4 className="text-yellow-400 font-bold mb-2 flex items-center gap-2">
                <AlertCircle size={18} />
                Paper Trading Available
              </h4>
              <p className="text-sm text-slate-400">
                Start with $10,000 virtual capital on Binance Testnet. No real money at risk.
              </p>
            </div>

            <div className="space-y-3">
              <h3 className="text-xl font-semibold text-white">How to Start Live Trading</h3>
              <ol className="space-y-3">
                <li className="flex items-start gap-3">
                  <span className="text-cyan-400 font-bold">1.</span>
                  <span className="text-slate-400">Navigate to <code className="bg-white/5 px-2 py-1 rounded">/livetrading</code> page</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-cyan-400 font-bold">2.</span>
                  <span className="text-slate-400">Select HMM strategy and BTC/USDT pair</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-cyan-400 font-bold">3.</span>
                  <span className="text-slate-400">Set initial capital and risk parameters</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-cyan-400 font-bold">4.</span>
                  <span className="text-slate-400">Click "Start Session" to begin automated trading</span>
                </li>
              </ol>
            </div>
          </section>

          {/* Section: API Endpoints */}
          <section id="api-endpoints" className="space-y-6 pt-8 border-t border-white/5 scroll-mt-20">
            <h2 className="text-3xl font-bold text-white">API Reference</h2>
            <p className="text-slate-400">
              RESTful API endpoints for programmatic access to backtesting and live trading.
            </p>
            
            <div className="space-y-4">
              <div className="bg-[#151B26] border border-white/10 rounded-xl overflow-hidden">
                <div className="flex items-center gap-3 px-4 py-3 border-b border-white/5 bg-white/5">
                  <span className="px-2 py-1 bg-emerald-500/20 text-emerald-400 rounded text-xs font-bold">POST</span>
                  <code className="text-sm text-slate-300">/backtest</code>
                </div>
                <div className="p-4 text-sm text-slate-400">
                  Run a backtest with specified parameters. Returns performance metrics and trade history.
                </div>
              </div>

              <div className="bg-[#151B26] border border-white/10 rounded-xl overflow-hidden">
                <div className="flex items-center gap-3 px-4 py-3 border-b border-white/5 bg-white/5">
                  <span className="px-2 py-1 bg-emerald-500/20 text-emerald-400 rounded text-xs font-bold">POST</span>
                  <code className="text-sm text-slate-300">/live-trading/start</code>
                </div>
                <div className="p-4 text-sm text-slate-400">
                  Start a live trading session with selected strategy.
                </div>
              </div>

              <div className="bg-[#151B26] border border-white/10 rounded-xl overflow-hidden">
                <div className="flex items-center gap-3 px-4 py-3 border-b border-white/5 bg-white/5">
                  <span className="px-2 py-1 bg-blue-500/20 text-blue-400 rounded text-xs font-bold">GET</span>
                  <code className="text-sm text-slate-300">/sessions</code>
                </div>
                <div className="p-4 text-sm text-slate-400">
                  Retrieve all live trading sessions for authenticated user.
                </div>
              </div>

              <div className="bg-[#151B26] border border-white/10 rounded-xl overflow-hidden">
                <div className="flex items-center gap-3 px-4 py-3 border-b border-white/5 bg-white/5">
                  <span className="px-2 py-1 bg-orange-500/20 text-orange-400 rounded text-xs font-bold">DELETE</span>
                  <code className="text-sm text-slate-300">/live-trading/stop/:session_id</code>
                </div>
                <div className="p-4 text-sm text-slate-400">
                  Stop an active live trading session.
                </div>
              </div>
            </div>
          </section>

          {/* Section: Code Examples */}
          <section id="code-examples" className="space-y-6 pt-8 border-t border-white/5 scroll-mt-20">
            <h2 className="text-3xl font-bold text-white flex items-center gap-3">
              <Code size={32} className="text-purple-400" />
              Code Examples
            </h2>
            <p className="text-slate-400">
              Complete implementation of the HMM strategy in Python.
            </p>
            
            <div className="bg-[#151B26] border border-white/10 rounded-xl overflow-hidden">
              <div className="flex items-center gap-2 px-4 py-3 border-b border-white/5 bg-white/5">
                <div className="w-3 h-3 rounded-full bg-red-500/50" />
                <div className="w-3 h-3 rounded-full bg-yellow-500/50" />
                <div className="w-3 h-3 rounded-full bg-green-500/50" />
                <span className="ml-2 text-xs text-slate-500 font-mono">hmm_strategy.py</span>
              </div>
              <div className="p-6 overflow-x-auto">
                <pre className="font-mono text-xs text-slate-300 leading-relaxed">
{`import numpy as np
import pandas as pd
from hmmlearn import hmm
from ta.momentum import RSIIndicator

class HMMRegimeSwitchingStrategy:
    def __init__(self, n_states=2, lookback=500):
        self.n_states = n_states
        self.lookback = lookback
        self.model = hmm.GaussianHMM(n_components=n_states, covariance_type="full", n_iter=100)
        
    def prepare_features(self, df):
        """Calculate log returns and volatility"""
        df['returns'] = np.log(df['close'] / df['close'].shift(1))
        df['volatility'] = df['returns'].rolling(20).std()
        return df[['returns', 'volatility']].dropna()
    
    def train(self, df):
        """Train HMM on historical data"""
        features = self.prepare_features(df)
        self.model.fit(features[-self.lookback:])
        return self
    
    def predict_regime(self, df):
        """Predict current market regime"""
        features = self.prepare_features(df)
        hidden_states = self.model.predict(features)
        return hidden_states[-1]
    
    def generate_signal(self, df):
        """Generate trading signal based on regime"""
        regime = self.predict_regime(df)
        rsi = RSIIndicator(df['close'], window=14).rsi().iloc[-1]
        
        # State 0: Low Volatility - Mean Reversion
        if regime == 0:
            if rsi < 30:
                return "BUY"
            elif rsi > 70:
                return "SELL"
        
        # State 1: High Volatility - Stay in Cash
        elif regime == 1:
            return "HOLD"
        
        return "HOLD"

# Usage Example
strategy = HMMRegimeSwitchingStrategy(n_states=2, lookback=500)
strategy.train(historical_data)

# On new data
signal = strategy.generate_signal(latest_data)
print(f"Trading Signal: {signal}")`}
                </pre>
              </div>
            </div>

            <div className="p-6 bg-cyan-500/5 border border-cyan-500/10 rounded-2xl">
              <h4 className="text-cyan-400 font-bold mb-2">💡 Pro Tip</h4>
              <p className="text-sm text-slate-400">
                Retrain your HMM model every 3 months on rolling windows to adapt to changing market dynamics. Use walk-forward validation to prevent overfitting.
              </p>
            </div>
          </section>

          {/* Footer CTA */}
          <section className="pt-8 border-t border-white/5">
            <div className="p-8 bg-gradient-to-br from-cyan-500/10 to-blue-500/10 border border-cyan-500/20 rounded-2xl text-center">
              <h3 className="text-2xl font-bold text-white mb-3">Ready to Start Trading?</h3>
              <p className="text-slate-400 mb-6">
                Deploy your first HMM strategy in minutes with our platform.
              </p>
              <button 
                onClick={() => router.push("/auth")}
                className="px-8 py-3 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-bold rounded-xl transition-all transform hover:scale-105 shadow-lg shadow-cyan-500/20 inline-flex items-center gap-2"
              >
                Get Started Free
                <ArrowLeft className="rotate-180" size={18} />
              </button>
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}
