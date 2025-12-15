"use client";

import React from "react";
import { ArrowLeft, Shield, Lock, Eye, Database, UserCheck, AlertCircle } from "lucide-react";
import { useRouter } from "next/navigation";

export default function PrivacyPage() {
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
              <Shield size={16} className="text-white" />
            </div>
            <span className="font-bold text-white tracking-tight">AlgoQuant <span className="text-cyan-400">Privacy Policy</span></span>
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
          <div className="inline-flex items-center gap-3 px-4 py-2 rounded-full bg-gradient-to-r from-cyan-500/10 to-blue-500/10 border border-cyan-500/20 text-cyan-400 text-sm font-mono mb-6">
            <Lock size={16} />
            <span>Your Privacy Matters</span>
          </div>
          <h1 className="text-5xl font-bold text-white mb-4">Privacy Policy</h1>
          <p className="text-slate-400 text-lg">
            Last updated: December 16, 2025
          </p>
        </div>

        {/* Content */}
        <div className="space-y-12">
          
          {/* Introduction */}
          <section className="space-y-4">
            <div className="p-6 bg-blue-500/5 border border-blue-500/10 rounded-2xl">
              <p className="text-slate-400 leading-relaxed">
                At AlgoQuant, we take your privacy seriously. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our algorithmic trading platform. Please read this policy carefully.
              </p>
            </div>
          </section>

          {/* Information We Collect */}
          <section className="space-y-4">
            <h2 className="text-3xl font-bold text-white flex items-center gap-3">
              <Database size={28} className="text-cyan-400" />
              Information We Collect
            </h2>
            
            <div className="space-y-6">
              <div className="p-6 bg-[#151B26] border border-white/10 rounded-2xl">
                <h3 className="text-xl font-bold text-white mb-3">1. Personal Information</h3>
                <p className="text-slate-400 mb-3">
                  When you create an account, we collect:
                </p>
                <ul className="space-y-2 text-sm text-slate-400 ml-6">
                  <li className="flex items-start gap-2">
                    <span className="text-cyan-400 mt-1">•</span>
                    <span><strong>Account Details:</strong> Email address, username, hashed password</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-cyan-400 mt-1">•</span>
                    <span><strong>Profile Information:</strong> Display name, profile picture (optional)</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-cyan-400 mt-1">•</span>
                    <span><strong>Verification Data:</strong> Email verification tokens</span>
                  </li>
                </ul>
              </div>

              <div className="p-6 bg-[#151B26] border border-white/10 rounded-2xl">
                <h3 className="text-xl font-bold text-white mb-3">2. Trading Data</h3>
                <p className="text-slate-400 mb-3">
                  To provide our services, we collect:
                </p>
                <ul className="space-y-2 text-sm text-slate-400 ml-6">
                  <li className="flex items-start gap-2">
                    <span className="text-cyan-400 mt-1">•</span>
                    <span><strong>Backtest Results:</strong> Strategy configurations, performance metrics, trade history</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-cyan-400 mt-1">•</span>
                    <span><strong>Live Trading Sessions:</strong> Active strategies, portfolio balances, executed trades</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-cyan-400 mt-1">•</span>
                    <span><strong>API Keys:</strong> Encrypted exchange API keys (Binance, Coinbase) for live trading</span>
                  </li>
                </ul>
              </div>

              <div className="p-6 bg-[#151B26] border border-white/10 rounded-2xl">
                <h3 className="text-xl font-bold text-white mb-3">3. Technical Information</h3>
                <p className="text-slate-400 mb-3">
                  We automatically collect:
                </p>
                <ul className="space-y-2 text-sm text-slate-400 ml-6">
                  <li className="flex items-start gap-2">
                    <span className="text-cyan-400 mt-1">•</span>
                    <span><strong>Device Information:</strong> IP address, browser type, operating system</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-cyan-400 mt-1">•</span>
                    <span><strong>Usage Data:</strong> Pages visited, features used, session duration</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-cyan-400 mt-1">•</span>
                    <span><strong>Cookies:</strong> Session tokens, authentication cookies, analytics cookies</span>
                  </li>
                </ul>
              </div>
            </div>
          </section>

          {/* How We Use Your Information */}
          <section className="space-y-4">
            <h2 className="text-3xl font-bold text-white flex items-center gap-3">
              <Eye size={28} className="text-purple-400" />
              How We Use Your Information
            </h2>
            
            <div className="grid md:grid-cols-2 gap-4">
              <div className="p-5 bg-gradient-to-br from-cyan-500/5 to-blue-500/5 border border-cyan-500/10 rounded-xl">
                <h4 className="text-white font-bold mb-2 flex items-center gap-2">
                  <UserCheck size={18} className="text-cyan-400" />
                  Service Delivery
                </h4>
                <p className="text-sm text-slate-400">
                  Process backtests, execute live trades, maintain your account, and provide customer support.
                </p>
              </div>

              <div className="p-5 bg-gradient-to-br from-purple-500/5 to-pink-500/5 border border-purple-500/10 rounded-xl">
                <h4 className="text-white font-bold mb-2 flex items-center gap-2">
                  <Shield size={18} className="text-purple-400" />
                  Security & Fraud Prevention
                </h4>
                <p className="text-sm text-slate-400">
                  Monitor for suspicious activity, prevent unauthorized access, and protect against fraud.
                </p>
              </div>

              <div className="p-5 bg-gradient-to-br from-emerald-500/5 to-cyan-500/5 border border-emerald-500/10 rounded-xl">
                <h4 className="text-white font-bold mb-2 flex items-center gap-2">
                  <AlertCircle size={18} className="text-emerald-400" />
                  Platform Improvement
                </h4>
                <p className="text-sm text-slate-400">
                  Analyze usage patterns to improve features, optimize performance, and develop new strategies.
                </p>
              </div>

              <div className="p-5 bg-gradient-to-br from-orange-500/5 to-red-500/5 border border-orange-500/10 rounded-xl">
                <h4 className="text-white font-bold mb-2 flex items-center gap-2">
                  <Lock size={18} className="text-orange-400" />
                  Legal Compliance
                </h4>
                <p className="text-sm text-slate-400">
                  Comply with legal obligations, enforce our Terms of Service, and respond to legal requests.
                </p>
              </div>
            </div>
          </section>

          {/* Data Security */}
          <section className="space-y-4">
            <h2 className="text-3xl font-bold text-white flex items-center gap-3">
              <Lock size={28} className="text-emerald-400" />
              Data Security
            </h2>
            
            <div className="p-6 bg-emerald-500/5 border border-emerald-500/10 rounded-2xl">
              <p className="text-slate-400 mb-4 leading-relaxed">
                We implement industry-standard security measures to protect your data:
              </p>
              <ul className="space-y-3 text-sm text-slate-400">
                <li className="flex items-start gap-3">
                  <span className="text-emerald-400 font-bold">✓</span>
                  <span><strong>Encryption:</strong> All data is encrypted in transit (TLS 1.3) and at rest (AES-256)</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-emerald-400 font-bold">✓</span>
                  <span><strong>Password Security:</strong> Passwords are hashed using bcrypt with salt rounds</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-emerald-400 font-bold">✓</span>
                  <span><strong>API Key Protection:</strong> Exchange API keys are encrypted and never stored in plain text</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-emerald-400 font-bold">✓</span>
                  <span><strong>Access Controls:</strong> Role-based access and multi-factor authentication (MFA) available</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="text-emerald-400 font-bold">✓</span>
                  <span><strong>Regular Audits:</strong> Security audits and penetration testing conducted quarterly</span>
                </li>
              </ul>
            </div>
          </section>

          {/* Data Sharing */}
          <section className="space-y-4">
            <h2 className="text-3xl font-bold text-white">Data Sharing & Disclosure</h2>
            
            <div className="p-6 bg-[#151B26] border border-white/10 rounded-2xl">
              <p className="text-slate-400 mb-4">
                <strong className="text-white">We do NOT sell your personal information.</strong> We may share your data only in these limited circumstances:
              </p>
              <ul className="space-y-2 text-sm text-slate-400 ml-6">
                <li className="flex items-start gap-2">
                  <span className="text-cyan-400 mt-1">•</span>
                  <span><strong>Service Providers:</strong> Third-party services that help us operate (e.g., hosting, analytics, email delivery)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-cyan-400 mt-1">•</span>
                  <span><strong>Legal Requirements:</strong> When required by law, court order, or government request</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-cyan-400 mt-1">•</span>
                  <span><strong>Business Transfers:</strong> In case of merger, acquisition, or sale of assets</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-cyan-400 mt-1">•</span>
                  <span><strong>With Your Consent:</strong> When you explicitly authorize us to share your information</span>
                </li>
              </ul>
            </div>
          </section>

          {/* Your Rights */}
          <section className="space-y-4">
            <h2 className="text-3xl font-bold text-white">Your Privacy Rights</h2>
            
            <div className="grid md:grid-cols-2 gap-4">
              <div className="p-5 bg-[#151B26] border border-white/10 rounded-xl">
                <h4 className="text-white font-bold mb-2">Access & Portability</h4>
                <p className="text-sm text-slate-400">
                  Request a copy of your personal data in a machine-readable format.
                </p>
              </div>

              <div className="p-5 bg-[#151B26] border border-white/10 rounded-xl">
                <h4 className="text-white font-bold mb-2">Correction</h4>
                <p className="text-sm text-slate-400">
                  Update or correct inaccurate information in your account settings.
                </p>
              </div>

              <div className="p-5 bg-[#151B26] border border-white/10 rounded-xl">
                <h4 className="text-white font-bold mb-2">Deletion</h4>
                <p className="text-sm text-slate-400">
                  Request deletion of your account and associated data (subject to legal obligations).
                </p>
              </div>

              <div className="p-5 bg-[#151B26] border border-white/10 rounded-xl">
                <h4 className="text-white font-bold mb-2">Opt-Out</h4>
                <p className="text-sm text-slate-400">
                  Unsubscribe from marketing emails or disable non-essential cookies.
                </p>
              </div>
            </div>

            <div className="p-4 bg-cyan-500/5 border border-cyan-500/10 rounded-xl">
              <p className="text-sm text-slate-400">
                <strong className="text-cyan-400">To exercise your rights:</strong> Email us at <a href="mailto:privacy@algoquant.io" className="text-cyan-400 underline">privacy@algoquant.io</a> or contact support through your dashboard.
              </p>
            </div>
          </section>

          {/* Cookies */}
          <section className="space-y-4">
            <h2 className="text-3xl font-bold text-white">Cookies & Tracking</h2>
            
            <div className="p-6 bg-[#151B26] border border-white/10 rounded-2xl">
              <p className="text-slate-400 mb-4">
                We use cookies and similar technologies for:
              </p>
              <ul className="space-y-2 text-sm text-slate-400 ml-6">
                <li className="flex items-start gap-2">
                  <span className="text-cyan-400 mt-1">•</span>
                  <span><strong>Essential Cookies:</strong> Required for authentication and security (cannot be disabled)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-cyan-400 mt-1">•</span>
                  <span><strong>Analytics Cookies:</strong> Track usage patterns to improve the platform (can be disabled)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-cyan-400 mt-1">•</span>
                  <span><strong>Preference Cookies:</strong> Remember your settings and preferences</span>
                </li>
              </ul>
              <p className="text-sm text-slate-400 mt-4">
                You can manage cookie preferences in your browser settings or through our Cookie Consent Manager.
              </p>
            </div>
          </section>

          {/* Data Retention */}
          <section className="space-y-4">
            <h2 className="text-3xl font-bold text-white">Data Retention</h2>
            
            <div className="p-6 bg-[#151B26] border border-white/10 rounded-2xl">
              <p className="text-slate-400 mb-3">
                We retain your data for as long as your account is active or as needed to provide services:
              </p>
              <ul className="space-y-2 text-sm text-slate-400 ml-6">
                <li className="flex items-start gap-2">
                  <span className="text-cyan-400 mt-1">•</span>
                  <span><strong>Account Data:</strong> Until account deletion + 30 days backup retention</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-cyan-400 mt-1">•</span>
                  <span><strong>Trading History:</strong> 7 years (required by financial regulations)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-cyan-400 mt-1">•</span>
                  <span><strong>Logs & Analytics:</strong> 90 days rolling retention</span>
                </li>
              </ul>
            </div>
          </section>

          {/* Children's Privacy */}
          <section className="space-y-4">
            <h2 className="text-3xl font-bold text-white">Children's Privacy</h2>
            
            <div className="p-6 bg-orange-500/5 border border-orange-500/10 rounded-2xl">
              <p className="text-slate-400">
                AlgoQuant is not intended for users under 18 years of age. We do not knowingly collect personal information from children. If you believe we have collected data from a minor, please contact us immediately at <a href="mailto:privacy@algoquant.io" className="text-orange-400 underline">privacy@algoquant.io</a>.
              </p>
            </div>
          </section>

          {/* Changes to Policy */}
          <section className="space-y-4">
            <h2 className="text-3xl font-bold text-white">Changes to This Policy</h2>
            
            <div className="p-6 bg-[#151B26] border border-white/10 rounded-2xl">
              <p className="text-slate-400">
                We may update this Privacy Policy from time to time. We will notify you of significant changes via email or a prominent notice on our platform. Your continued use of AlgoQuant after changes constitutes acceptance of the updated policy.
              </p>
            </div>
          </section>

          {/* Contact */}
          <section className="space-y-4">
            <h2 className="text-3xl font-bold text-white">Contact Us</h2>
            
            <div className="p-6 bg-gradient-to-br from-cyan-500/10 to-blue-500/10 border border-cyan-500/20 rounded-2xl">
              <p className="text-slate-400 mb-4">
                If you have questions or concerns about this Privacy Policy, please contact us:
              </p>
              <div className="space-y-2 text-sm text-slate-400">
                <p><strong className="text-white">Email:</strong> <a href="mailto:privacy@algoquant.io" className="text-cyan-400 underline">privacy@algoquant.io</a></p>
                <p><strong className="text-white">Support:</strong> <a href="mailto:support@algoquant.io" className="text-cyan-400 underline">support@algoquant.io</a></p>
                <p><strong className="text-white">Address:</strong> AlgoQuant Inc., 123 Trading Street, New York, NY 10001, USA</p>
              </div>
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
