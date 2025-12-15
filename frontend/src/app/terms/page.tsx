"use client";

import React from "react";
import { ArrowLeft, FileText, Scale, AlertTriangle, Shield, CheckCircle, XCircle } from "lucide-react";
import { useRouter } from "next/navigation";

export default function TermsPage() {
  const router = useRouter();

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
              <Scale size={16} className="text-white" />
            </div>
            <span className="font-bold text-white tracking-tight">AlgoQuant <span className="text-cyan-400">Terms of Service</span></span>
          </div>
          <button 
            onClick={() => router.push("/")}
            className="text-sm font-medium text-slate-400 hover:text-white flex items-center gap-2 transition-colors"
          >
            <ArrowLeft size={16} /> Back to Home
          </button>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="max-w-4xl mx-auto px-6 py-16">
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-3 px-4 py-2 rounded-full bg-gradient-to-r from-purple-500/10 to-blue-500/10 border border-purple-500/20 text-purple-400 text-sm font-mono mb-6">
            <FileText size={16} />
            <span>Legal Agreement</span>
          </div>
          <h1 className="text-5xl font-bold text-white mb-4">Terms of Service</h1>
          <p className="text-slate-400 text-lg">
            Last updated: December 16, 2025
          </p>
        </div>

        {/* Content */}
        <div className="space-y-12">
          
          {/* Introduction */}
          <section className="space-y-4">
            <div className="p-6 bg-purple-500/5 border border-purple-500/10 rounded-2xl">
              <p className="text-slate-400 leading-relaxed">
                Welcome to AlgoQuant. By accessing or using our algorithmic trading platform, you agree to be bound by these Terms of Service ("Terms"). Please read them carefully before using our services. If you do not agree to these Terms, do not use AlgoQuant.
              </p>
            </div>
          </section>

          {/* Acceptance of Terms */}
          <section className="space-y-4">
            <h2 className="text-3xl font-bold text-white flex items-center gap-3">
              <CheckCircle size={28} className="text-emerald-400" />
              1. Acceptance of Terms
            </h2>
            
            <div className="p-6 bg-[#151B26] border border-white/10 rounded-2xl">
              <p className="text-slate-400 mb-4">
                By creating an account or using AlgoQuant, you represent that:
              </p>
              <ul className="space-y-2 text-sm text-slate-400 ml-6">
                <li className="flex items-start gap-2">
                  <span className="text-emerald-400 mt-1">✓</span>
                  <span>You are at least <strong>18 years of age</strong></span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-emerald-400 mt-1">✓</span>
                  <span>You have the legal capacity to enter into binding contracts</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-emerald-400 mt-1">✓</span>
                  <span>You will comply with all applicable laws and regulations</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-emerald-400 mt-1">✓</span>
                  <span>All information you provide is accurate and up-to-date</span>
                </li>
              </ul>
            </div>
          </section>

          {/* Account Registration */}
          <section className="space-y-4">
            <h2 className="text-3xl font-bold text-white">2. Account Registration & Security</h2>
            
            <div className="space-y-4">
              <div className="p-6 bg-[#151B26] border border-white/10 rounded-2xl">
                <h3 className="text-xl font-bold text-white mb-3">Account Creation</h3>
                <p className="text-slate-400 mb-3">
                  You must provide accurate and complete information when creating an account. You are responsible for:
                </p>
                <ul className="space-y-2 text-sm text-slate-400 ml-6">
                  <li className="flex items-start gap-2">
                    <span className="text-cyan-400 mt-1">•</span>
                    <span>Maintaining the confidentiality of your password and API keys</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-cyan-400 mt-1">•</span>
                    <span>All activities that occur under your account</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-cyan-400 mt-1">•</span>
                    <span>Notifying us immediately of unauthorized access</span>
                  </li>
                </ul>
              </div>

              <div className="p-6 bg-[#151B26] border border-white/10 rounded-2xl">
                <h3 className="text-xl font-bold text-white mb-3">Account Suspension & Termination</h3>
                <p className="text-slate-400 text-sm">
                  We reserve the right to suspend or terminate your account at any time for violations of these Terms, fraudulent activity, or other legitimate reasons. You may close your account at any time through your account settings.
                </p>
              </div>
            </div>
          </section>

          {/* Trading Services */}
          <section className="space-y-4">
            <h2 className="text-3xl font-bold text-white flex items-center gap-3">
              <AlertTriangle size={28} className="text-orange-400" />
              3. Trading Services & Risk Disclosure
            </h2>
            
            <div className="p-6 bg-red-500/10 border border-red-500/20 rounded-2xl">
              <h3 className="text-red-400 font-bold mb-3 flex items-center gap-2">
                <AlertTriangle size={20} />
                IMPORTANT RISK WARNING
              </h3>
              <p className="text-slate-300 font-semibold mb-4">
                Trading cryptocurrencies and other financial instruments involves substantial risk of loss and is not suitable for all investors.
              </p>
              <ul className="space-y-2 text-sm text-slate-400">
                <li className="flex items-start gap-2">
                  <span className="text-red-400 mt-1">⚠</span>
                  <span><strong>Past performance is NOT indicative of future results.</strong> Backtested results do not guarantee real trading profits.</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-red-400 mt-1">⚠</span>
                  <span><strong>You can lose your entire investment.</strong> Only trade with capital you can afford to lose.</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-red-400 mt-1">⚠</span>
                  <span><strong>Market volatility</strong> can result in rapid and substantial losses, especially in cryptocurrency markets.</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-red-400 mt-1">⚠</span>
                  <span><strong>Technical failures</strong> may occur. We are not liable for losses due to platform downtime, API errors, or exchange issues.</span>
                </li>
              </ul>
            </div>

            <div className="p-6 bg-[#151B26] border border-white/10 rounded-2xl">
              <h3 className="text-xl font-bold text-white mb-3">Service Scope</h3>
              <p className="text-slate-400 mb-3">
                AlgoQuant provides:
              </p>
              <ul className="space-y-2 text-sm text-slate-400 ml-6">
                <li className="flex items-start gap-2">
                  <span className="text-cyan-400 mt-1">✓</span>
                  <span><strong>Backtesting Tools:</strong> Test trading strategies on historical data</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-cyan-400 mt-1">✓</span>
                  <span><strong>Paper Trading:</strong> Simulate trades with virtual capital</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-cyan-400 mt-1">✓</span>
                  <span><strong>Live Trading Integration:</strong> Connect to exchanges via your own API keys</span>
                </li>
              </ul>
              <p className="text-sm text-slate-400 mt-4">
                <strong className="text-white">We are NOT:</strong> A financial advisor, broker, or investment fund. We do not provide investment advice or manage funds on your behalf.
              </p>
            </div>
          </section>

          {/* User Responsibilities */}
          <section className="space-y-4">
            <h2 className="text-3xl font-bold text-white">4. User Responsibilities</h2>
            
            <div className="grid md:grid-cols-2 gap-4">
              <div className="p-5 bg-emerald-500/5 border border-emerald-500/10 rounded-xl">
                <h4 className="text-emerald-400 font-bold mb-2 flex items-center gap-2">
                  <CheckCircle size={18} />
                  You MUST
                </h4>
                <ul className="space-y-1 text-sm text-slate-400">
                  <li>• Use the platform lawfully</li>
                  <li>• Secure your API keys</li>
                  <li>• Monitor your trades</li>
                  <li>• Comply with tax regulations</li>
                  <li>• Keep account info updated</li>
                </ul>
              </div>

              <div className="p-5 bg-red-500/5 border border-red-500/10 rounded-xl">
                <h4 className="text-red-400 font-bold mb-2 flex items-center gap-2">
                  <XCircle size={18} />
                  You MUST NOT
                </h4>
                <ul className="space-y-1 text-sm text-slate-400">
                  <li>• Share your account</li>
                  <li>• Manipulate markets</li>
                  <li>• Use automated bots (except our platform)</li>
                  <li>• Reverse engineer our code</li>
                  <li>• Overload our servers</li>
                </ul>
              </div>
            </div>
          </section>

          {/* Intellectual Property */}
          <section className="space-y-4">
            <h2 className="text-3xl font-bold text-white">5. Intellectual Property</h2>
            
            <div className="p-6 bg-[#151B26] border border-white/10 rounded-2xl">
              <p className="text-slate-400 mb-3">
                All content, features, and functionality of AlgoQuant (including but not limited to software, algorithms, text, graphics, logos) are owned by AlgoQuant and protected by copyright, trademark, and other intellectual property laws.
              </p>
              <p className="text-sm text-slate-400 mt-3">
                <strong className="text-white">You may NOT:</strong>
              </p>
              <ul className="space-y-1 text-sm text-slate-400 ml-6 mt-2">
                <li>• Copy, modify, or distribute our algorithms or code</li>
                <li>• Create derivative works based on our platform</li>
                <li>• Use our trademarks without written permission</li>
                <li>• Remove copyright or proprietary notices</li>
              </ul>
            </div>
          </section>

          {/* Fees & Payments */}
          <section className="space-y-4">
            <h2 className="text-3xl font-bold text-white">6. Fees & Payments</h2>
            
            <div className="p-6 bg-[#151B26] border border-white/10 rounded-2xl">
              <h3 className="text-xl font-bold text-white mb-3">Current Pricing</h3>
              <ul className="space-y-2 text-sm text-slate-400 ml-6">
                <li className="flex items-start gap-2">
                  <span className="text-cyan-400 mt-1">•</span>
                  <span><strong>Free Tier:</strong> Unlimited backtesting, $10,000 paper trading account</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-cyan-400 mt-1">•</span>
                  <span><strong>Pro Tier:</strong> Live trading, advanced analytics, priority support (pricing TBD)</span>
                </li>
              </ul>
              <p className="text-sm text-slate-400 mt-4">
                We reserve the right to change fees with 30 days' notice. Continued use after fee changes constitutes acceptance.
              </p>
            </div>
          </section>

          {/* Liability Limitation */}
          <section className="space-y-4">
            <h2 className="text-3xl font-bold text-white flex items-center gap-3">
              <Shield size={28} className="text-purple-400" />
              7. Limitation of Liability
            </h2>
            
            <div className="p-6 bg-purple-500/5 border border-purple-500/10 rounded-2xl">
              <p className="text-slate-300 font-semibold mb-4">
                TO THE MAXIMUM EXTENT PERMITTED BY LAW:
              </p>
              <ul className="space-y-3 text-sm text-slate-400">
                <li className="flex items-start gap-2">
                  <span className="text-purple-400 mt-1">•</span>
                  <span><strong>No Warranty:</strong> The platform is provided "AS IS" without warranties of any kind, express or implied.</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-purple-400 mt-1">•</span>
                  <span><strong>No Liability for Trading Losses:</strong> We are not liable for losses resulting from your trading decisions, even if using our strategies.</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-purple-400 mt-1">•</span>
                  <span><strong>Indirect Damages:</strong> We are not liable for indirect, incidental, or consequential damages (lost profits, data loss, etc.)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-purple-400 mt-1">•</span>
                  <span><strong>Maximum Liability:</strong> Our total liability to you for any claim shall not exceed the amount you paid us in the past 12 months (or $100 if using free tier).</span>
                </li>
              </ul>
            </div>
          </section>

          {/* Indemnification */}
          <section className="space-y-4">
            <h2 className="text-3xl font-bold text-white">8. Indemnification</h2>
            
            <div className="p-6 bg-[#151B26] border border-white/10 rounded-2xl">
              <p className="text-slate-400">
                You agree to indemnify, defend, and hold harmless AlgoQuant, its officers, directors, employees, and agents from any claims, damages, losses, or expenses (including legal fees) arising from:
              </p>
              <ul className="space-y-2 text-sm text-slate-400 ml-6 mt-3">
                <li>• Your use of the platform</li>
                <li>• Your violation of these Terms</li>
                <li>• Your violation of any law or regulation</li>
                <li>• Your trading activities and decisions</li>
              </ul>
            </div>
          </section>

          {/* Third-Party Services */}
          <section className="space-y-4">
            <h2 className="text-3xl font-bold text-white">9. Third-Party Services</h2>
            
            <div className="p-6 bg-[#151B26] border border-white/10 rounded-2xl">
              <p className="text-slate-400 mb-3">
                AlgoQuant integrates with third-party services (Binance, Coinbase, etc.). Your use of these services is subject to their own terms and conditions.
              </p>
              <p className="text-sm text-slate-400">
                <strong className="text-white">Important:</strong> We are not responsible for the performance, availability, or security of third-party exchanges. Issues with exchange APIs, deposits, withdrawals, or account restrictions are outside our control.
              </p>
            </div>
          </section>

          {/* Data & Privacy */}
          <section className="space-y-4">
            <h2 className="text-3xl font-bold text-white">10. Data & Privacy</h2>
            
            <div className="p-6 bg-cyan-500/5 border border-cyan-500/10 rounded-2xl">
              <p className="text-slate-400 mb-2">
                Your use of AlgoQuant is also governed by our <a onClick={() => router.push("/privacy")} className="text-cyan-400 underline cursor-pointer">Privacy Policy</a>, which explains how we collect, use, and protect your data.
              </p>
              <p className="text-sm text-slate-400">
                By using our platform, you consent to data processing as described in the Privacy Policy.
              </p>
            </div>
          </section>

          {/* Dispute Resolution */}
          <section className="space-y-4">
            <h2 className="text-3xl font-bold text-white">11. Dispute Resolution & Governing Law</h2>
            
            <div className="space-y-4">
              <div className="p-6 bg-[#151B26] border border-white/10 rounded-2xl">
                <h3 className="text-xl font-bold text-white mb-3">Governing Law</h3>
                <p className="text-slate-400 text-sm">
                  These Terms are governed by the laws of the State of New York, USA, without regard to conflict of law principles.
                </p>
              </div>

              <div className="p-6 bg-[#151B26] border border-white/10 rounded-2xl">
                <h3 className="text-xl font-bold text-white mb-3">Arbitration</h3>
                <p className="text-slate-400 text-sm mb-2">
                  Any disputes arising from these Terms shall be resolved through binding arbitration in New York, NY, rather than in court, except:
                </p>
                <ul className="space-y-1 text-sm text-slate-400 ml-6">
                  <li>• Small claims court disputes (under $10,000)</li>
                  <li>• Intellectual property disputes</li>
                </ul>
              </div>
            </div>
          </section>

          {/* Changes to Terms */}
          <section className="space-y-4">
            <h2 className="text-3xl font-bold text-white">12. Changes to Terms</h2>
            
            <div className="p-6 bg-[#151B26] border border-white/10 rounded-2xl">
              <p className="text-slate-400">
                We may modify these Terms at any time. Material changes will be notified via email or a prominent notice on the platform at least 30 days before taking effect. Continued use after changes indicates acceptance of the new Terms.
              </p>
            </div>
          </section>

          {/* Severability */}
          <section className="space-y-4">
            <h2 className="text-3xl font-bold text-white">13. Severability & Waiver</h2>
            
            <div className="p-6 bg-[#151B26] border border-white/10 rounded-2xl">
              <p className="text-slate-400 mb-3">
                If any provision of these Terms is found to be unenforceable, the remaining provisions will continue in full force.
              </p>
              <p className="text-slate-400 text-sm">
                Our failure to enforce any right or provision does not constitute a waiver of that right or provision.
              </p>
            </div>
          </section>

          {/* Contact */}
          <section className="space-y-4">
            <h2 className="text-3xl font-bold text-white">14. Contact Information</h2>
            
            <div className="p-6 bg-gradient-to-br from-purple-500/10 to-blue-500/10 border border-purple-500/20 rounded-2xl">
              <p className="text-slate-400 mb-4">
                Questions about these Terms? Contact us:
              </p>
              <div className="space-y-2 text-sm text-slate-400">
                <p><strong className="text-white">Email:</strong> <a href="mailto:legal@algoquant.io" className="text-purple-400 underline">legal@algoquant.io</a></p>
                <p><strong className="text-white">Support:</strong> <a href="mailto:support@algoquant.io" className="text-purple-400 underline">support@algoquant.io</a></p>
                <p><strong className="text-white">Address:</strong> AlgoQuant Inc., 123 Trading Street, New York, NY 10001, USA</p>
              </div>
            </div>
          </section>

          {/* Acknowledgment */}
          <section className="space-y-4">
            <div className="p-6 bg-gradient-to-br from-cyan-500/10 to-blue-500/10 border border-cyan-500/20 rounded-2xl text-center">
              <h3 className="text-xl font-bold text-white mb-3">Acknowledgment</h3>
              <p className="text-slate-400">
                BY USING ALGOQUANT, YOU ACKNOWLEDGE THAT YOU HAVE READ, UNDERSTOOD, AND AGREE TO BE BOUND BY THESE TERMS OF SERVICE.
              </p>
            </div>
          </section>

        </div>
      </div>

      {/* Footer */}
      <footer className="py-12 px-6 border-t border-white/5 text-center text-slate-600 text-sm">
        <p>© 2024 AlgoQuant. All rights reserved.</p>
      </footer>
    </div>
  );
}
