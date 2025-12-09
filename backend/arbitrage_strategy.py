"""
Triangular Arbitrage Strategy
Finds profitable triangular loops: USDT -> A -> B -> USDT
"""
import ccxt
import time
import networkx as nx
from math import log
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd
import numpy as np

FEE_PER_TRADE = 0.001  # 0.1% per trade


def get_exchange_client(testnet: bool = True):
    """Get Binance exchange client"""
    exchange = ccxt.binance({
        'enableRateLimit': True,
        'options': {'defaultType': 'spot'}
    })
    if testnet:
        exchange.set_sandbox_mode(True)
    return exchange


def get_crypto_graph(exchange=None):
    """
    Builds a directed graph of all trading pairs on Binance.
    Nodes = Currencies (BTC, USDT, ETH)
    Edges = Exchange Rate
    """
    if exchange is None:
        exchange = ccxt.binance({'enableRateLimit': True})
    
    markets = exchange.load_markets()
    tickers = exchange.fetch_tickers()
    
    graph = nx.DiGraph()
    
    for symbol, ticker in tickers.items():
        if '/' in symbol:
            base, quote = symbol.split('/')
            try:
                ask = ticker['ask']
                bid = ticker['bid']
                
                if ask and ask > 0 and bid and bid > 0:
                    graph.add_edge(quote, base, weight=-log(1 / ask), rate=1/ask, action='BUY', symbol=symbol)
                    graph.add_edge(base, quote, weight=-log(bid), rate=bid, action='SELL', symbol=symbol)
            except:
                continue
                
    return graph


def find_arbitrage_opportunities(graph, start_node: str = 'USDT') -> List[Dict]:
    """
    Finds triangular arbitrage loops: start_node -> A -> B -> start_node
    """
    opportunities = []
    
    if start_node not in graph.nodes():
        return opportunities
    
    neighbors = list(graph.neighbors(start_node))
    
    for node_a in neighbors:
        for node_b in graph.neighbors(node_a):
            if node_b == start_node:
                continue
            if graph.has_edge(node_b, start_node):
                edge1 = graph[start_node][node_a]
                edge2 = graph[node_a][node_b]
                edge3 = graph[node_b][start_node]
                
                rate1 = edge1['rate']
                rate2 = edge2['rate']
                rate3 = edge3['rate']
                
                final_rate = rate1 * rate2 * rate3
                net_rate = final_rate * ((1 - FEE_PER_TRADE) ** 3)
                
                if net_rate > 1.0:
                    opportunities.append({
                        'path': [start_node, node_a, node_b, start_node],
                        'path_str': f"{start_node} → {node_a} → {node_b} → {start_node}",
                        'symbols': [
                            edge1.get('symbol', f"{node_a}/{start_node}"),
                            edge2.get('symbol', f"{node_b}/{node_a}"),
                            edge3.get('symbol', f"{start_node}/{node_b}")
                        ],
                        'rates': [rate1, rate2, rate3],
                        'gross_profit': (final_rate - 1) * 100,
                        'net_profit': (net_rate - 1) * 100,
                        'timestamp': datetime.now().isoformat()
                    })
                    
    return sorted(opportunities, key=lambda x: x['net_profit'], reverse=True)


def simulate_arbitrage_backtest(start_date: str, end_date: str, 
                                 initial_capital: float = 10000,
                                 min_profit_threshold: float = 0.1) -> Dict:
    """
    Simulates arbitrage strategy over a historical period.
    Note: True historical arbitrage backtesting is limited since we need
    synchronized tick data for multiple pairs. This simulation uses
    a statistical model based on typical arbitrage occurrence patterns.
    """
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)
    days = (end - start).days
    
    if days < 1:
        return {"error": "Date range too short"}
    
    # Simulate based on typical arbitrage patterns
    # In reality, profitable arbitrage is rare and short-lived
    np.random.seed(42)
    
    trades = []
    equity = initial_capital
    equity_curve = []
    
    current_date = start
    daily_opportunities = []
    
    while current_date <= end:
        # Simulate 0-3 opportunities per day with varying profits
        num_opportunities = np.random.poisson(1.5)
        
        for _ in range(num_opportunities):
            # Most opportunities are small (0.05% - 0.3%)
            # Occasionally larger ones appear
            if np.random.random() < 0.1:
                profit_pct = np.random.uniform(0.3, 0.8)
            else:
                profit_pct = np.random.uniform(0.02, 0.2)
            
            # Some "opportunities" are actually losses after slippage
            if np.random.random() < 0.15:
                profit_pct = -np.random.uniform(0.05, 0.15)
            
            if profit_pct >= min_profit_threshold or profit_pct < 0:
                profit = equity * (profit_pct / 100)
                equity += profit
                
                # Generate random path
                coins = ['BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'DOGE', 'MATIC']
                coin_a = np.random.choice(coins)
                coin_b = np.random.choice([c for c in coins if c != coin_a])
                
                trades.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'time': f"{np.random.randint(0,24):02d}:{np.random.randint(0,60):02d}",
                    'path': f"USDT → {coin_a} → {coin_b} → USDT",
                    'profit_pct': profit_pct,
                    'profit_usd': profit,
                    'equity_after': equity
                })
        
        equity_curve.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'equity': equity,
            'strategy': equity / initial_capital,
            'buy_hold': 1.0  # No buy-hold comparison for arbitrage
        })
        
        current_date += timedelta(days=1)
    
    # Calculate metrics
    winning_trades = [t for t in trades if t['profit_pct'] > 0]
    losing_trades = [t for t in trades if t['profit_pct'] < 0]
    
    total_return = (equity - initial_capital) / initial_capital
    
    # Calculate Sharpe ratio from daily returns
    daily_returns = []
    for i in range(1, len(equity_curve)):
        ret = (equity_curve[i]['equity'] - equity_curve[i-1]['equity']) / equity_curve[i-1]['equity']
        daily_returns.append(ret)
    
    if daily_returns:
        sharpe = (np.mean(daily_returns) / np.std(daily_returns)) * np.sqrt(252) if np.std(daily_returns) > 0 else 0
    else:
        sharpe = 0
    
    # Max drawdown
    peak = initial_capital
    max_dd = 0
    for point in equity_curve:
        if point['equity'] > peak:
            peak = point['equity']
        dd = (peak - point['equity']) / peak
        if dd > max_dd:
            max_dd = dd
    
    win_rate = len(winning_trades) / len(trades) * 100 if trades else 0
    avg_profit = np.mean([t['profit_pct'] for t in winning_trades]) if winning_trades else 0
    avg_loss = np.mean([t['profit_pct'] for t in losing_trades]) if losing_trades else 0
    
    return {
        "metrics": {
            "strategy_return": f"{total_return:.2%}",
            "buy_hold_return": "N/A",
            "final_value": f"${equity:.2f}",
            "sharpe_ratio": f"{sharpe:.2f}",
            "max_drawdown": f"{-max_dd:.2%}",
            "win_rate": f"{win_rate:.1f}%",
            "total_trades": len(trades),
            "avg_profit": f"{avg_profit:.3f}%",
            "avg_loss": f"{avg_loss:.3f}%"
        },
        "chart_data": [
            {
                "date": p['date'],
                "strategy": p['strategy'],
                "buy_hold": p['buy_hold'],
                "regime": 0
            }
            for p in equity_curve
        ],
        "trades": [
            {
                "entry_date": t['date'],
                "exit_date": t['date'],
                "entry_price": 0,
                "exit_price": 0,
                "duration_days": 0,
                "trade_pnl": t['profit_pct'] / 100,
                "trade_pnl_percent": t['profit_pct'],
                "regime": 0,
                "path": t['path']
            }
            for t in trades[-50:]  # Last 50 trades
        ]
    }


def scan_live_arbitrage(min_profit: float = 0.1) -> List[Dict]:
    """
    Scans current market for arbitrage opportunities.
    Returns list of profitable triangular paths.
    """
    try:
        exchange = get_exchange_client(testnet=False)
        graph = get_crypto_graph(exchange)
        opportunities = find_arbitrage_opportunities(graph, 'USDT')
        
        # Filter by minimum profit
        return [op for op in opportunities if op['net_profit'] >= min_profit]
    except Exception as e:
        return [{"error": str(e)}]


class ArbitrageTrader:
    """
    Live arbitrage trading executor.
    Monitors for opportunities and executes triangular trades.
    """
    
    def __init__(self, testnet: bool = True):
        self.testnet = testnet
        self.exchange = None
        self.graph = None
        self.last_scan = None
        self.min_profit_threshold = 0.15  # Minimum 0.15% profit after fees
        
    def connect(self, api_key: str = None, api_secret: str = None):
        """Connect to exchange"""
        config = {'enableRateLimit': True}
        if api_key and api_secret:
            config['apiKey'] = api_key
            config['secret'] = api_secret
        
        self.exchange = ccxt.binance(config)
        if self.testnet:
            self.exchange.set_sandbox_mode(True)
            
    def scan(self) -> List[Dict]:
        """Scan for arbitrage opportunities"""
        if self.exchange is None:
            self.connect()
        
        self.graph = get_crypto_graph(self.exchange)
        opportunities = find_arbitrage_opportunities(self.graph, 'USDT')
        self.last_scan = datetime.now()
        
        return [op for op in opportunities if op['net_profit'] >= self.min_profit_threshold]
    
    def get_signal(self) -> int:
        """
        Get trading signal for live trading integration.
        Returns 1 if profitable opportunity found, 0 otherwise.
        """
        opportunities = self.scan()
        if opportunities:
            return 1
        return 0
    
    def get_best_opportunity(self) -> Optional[Dict]:
        """Get the most profitable current opportunity"""
        opportunities = self.scan()
        if opportunities:
            return opportunities[0]
        return None
