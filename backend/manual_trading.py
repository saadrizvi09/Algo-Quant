"""
Manual Trading Service
Handles manual buy/sell operations for the Market page
Operates independently from automated trading bot strategies
"""
from typing import Optional, Tuple, List
from datetime import datetime
from sqlmodel import Session, select
from database import engine
from models import PortfolioAsset, Trade
import uuid

# Trading fee (0.1% as typical exchange fee)
TRADING_FEE = 0.001

# Supported trading pairs for manual trading
SUPPORTED_ASSETS = ["BTC", "ETH", "SOL", "LINK", "DOGE", "BNB"]


def get_current_price_from_binance(symbol: str, quote: str = "USDT") -> Optional[float]:
    """
    Fetch current market price from Binance API
    
    Args:
        symbol: Base asset (e.g., 'BTC', 'ETH')
        quote: Quote asset (e.g., 'USDT')
    
    Returns:
        Current price or None if error
    """
    try:
        from binance.client import Client
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        
        api_key = os.getenv("BINANCE_API_KEY", "")
        api_secret = os.getenv("BINANCE_SECRET_KEY", "")
        
        client = Client(api_key, api_secret, testnet=True)
        trading_pair = f"{symbol}{quote}"
        ticker = client.get_symbol_ticker(symbol=trading_pair)
        return float(ticker['price'])
    except Exception as e:
        print(f"[ManualTrading] Binance fetch failed for {symbol}/{quote}: {e}")
        
        # Fallback to Yahoo Finance
        try:
            import yfinance as yf
            ticker_symbol = f"{symbol}-USD"
            ticker = yf.Ticker(ticker_symbol)
            price_data = ticker.history(period="1d", interval="1m")
            
            if not price_data.empty:
                return float(price_data['Close'].iloc[-1])
            return None
        except Exception as yf_error:
            print(f"[ManualTrading] Yahoo Finance fallback failed: {yf_error}")
            return None


def get_user_balance(symbol: str, user_email: str) -> float:
    """
    Get current balance of an asset from user's portfolio
    
    Args:
        symbol: Asset symbol (e.g., 'USDT', 'BTC')
        user_email: User identifier
    
    Returns:
        Current balance (0.0 if asset not found)
    """
    with Session(engine) as session:
        statement = select(PortfolioAsset).where(
            PortfolioAsset.symbol == symbol,
            PortfolioAsset.user_email == user_email
        )
        asset = session.exec(statement).first()
        return asset.balance if asset else 0.0


def get_asset_cost_basis(symbol: str, user_email: str) -> dict:
    """
    Get the average cost basis and investment info for an asset
    
    Args:
        symbol: Asset symbol (e.g., 'BTC', 'ETH')
        user_email: User identifier
    
    Returns:
        Dict with avg_cost_basis, total_invested, and balance
    """
    with Session(engine) as session:
        statement = select(PortfolioAsset).where(
            PortfolioAsset.symbol == symbol,
            PortfolioAsset.user_email == user_email
        )
        asset = session.exec(statement).first()
        
        if asset:
            return {
                'symbol': symbol,
                'balance': asset.balance,
                'avg_cost_basis': getattr(asset, 'avg_cost_basis', 0.0) or 0.0,
                'total_invested': getattr(asset, 'total_invested', 0.0) or 0.0
            }
        return {
            'symbol': symbol,
            'balance': 0.0,
            'avg_cost_basis': 0.0,
            'total_invested': 0.0
        }


def record_trade(
    session: Session,
    user_email: str,
    symbol: str,
    side: str,
    price: float,
    quantity: float,
    total: float,
    fee: float = 0.0,
    pnl: Optional[float] = None
) -> Trade:
    """
    Record a trade in the database
    
    Args:
        session: Database session
        user_email: User identifier
        symbol: Trading pair (e.g., 'BTCUSDT')
        side: 'BUY' or 'SELL'
        price: Execution price
        quantity: Amount traded
        total: Total value in quote currency
        fee: Trading fee
        pnl: Profit/Loss (for SELL trades)
    
    Returns:
        Created Trade object
    """
    trade = Trade(
        session_id=f"manual_{uuid.uuid4().hex[:8]}",
        user_email=user_email,
        symbol=symbol,
        side=side,
        price=price,
        quantity=quantity,
        total=total,
        pnl=pnl,
        order_id=f"MANUAL_{uuid.uuid4().hex[:12].upper()}",
        executed_at=datetime.now()
    )
    session.add(trade)
    return trade


def execute_manual_buy(
    symbol: str,
    usdt_amount: float,
    user_email: str,
    current_price: Optional[float] = None
) -> Tuple[bool, Optional[dict], Optional[str]]:
    """
    Execute a manual BUY order
    
    Args:
        symbol: Asset to buy (e.g., 'BTC', 'ETH')
        usdt_amount: Amount in USDT to spend
        user_email: User identifier
        current_price: Optional price (fetched if not provided)
    
    Returns:
        Tuple of (success: bool, trade_info: dict or None, error_message: str or None)
    """
    # Validate symbol
    if symbol.upper() not in SUPPORTED_ASSETS:
        return False, None, f"Asset {symbol} is not supported for manual trading"
    
    symbol = symbol.upper()
    
    # Get current market price if not provided
    price = current_price or get_current_price_from_binance(symbol, "USDT")
    if price is None:
        return False, None, f"Could not fetch price for {symbol}/USDT"
    
    # Calculate quantity to buy and fees
    fee = usdt_amount * TRADING_FEE
    usdt_after_fee = usdt_amount - fee
    quantity_to_buy = usdt_after_fee / price
    
    # Check if user has enough USDT
    usdt_balance = get_user_balance("USDT", user_email)
    
    if usdt_balance < usdt_amount:
        return False, None, f"Insufficient USDT balance. Required: {usdt_amount:.2f}, Available: {usdt_balance:.2f}"
    
    # Execute trade in database transaction
    try:
        with Session(engine) as session:
            # Deduct USDT
            usdt_stmt = select(PortfolioAsset).where(
                PortfolioAsset.symbol == "USDT",
                PortfolioAsset.user_email == user_email
            )
            usdt_asset = session.exec(usdt_stmt).first()
            usdt_asset.balance -= usdt_amount
            session.add(usdt_asset)
            
            # Add purchased asset and update cost basis
            asset_stmt = select(PortfolioAsset).where(
                PortfolioAsset.symbol == symbol,
                PortfolioAsset.user_email == user_email
            )
            asset = session.exec(asset_stmt).first()
            
            if asset:
                # Calculate new weighted average cost basis
                old_balance = asset.balance
                old_total_invested = getattr(asset, 'total_invested', 0.0) or 0.0
                new_total_invested = old_total_invested + usdt_amount
                new_balance = old_balance + quantity_to_buy
                
                # Weighted average: (old_invested + new_invested) / new_total_quantity
                asset.avg_cost_basis = new_total_invested / new_balance if new_balance > 0 else 0.0
                asset.total_invested = new_total_invested
                asset.balance = new_balance
                session.add(asset)
            else:
                new_asset = PortfolioAsset(
                    symbol=symbol,
                    balance=quantity_to_buy,
                    user_email=user_email,
                    avg_cost_basis=usdt_amount / quantity_to_buy if quantity_to_buy > 0 else 0.0,
                    total_invested=usdt_amount
                )
                session.add(new_asset)
                asset = new_asset
            
            # Record the trade
            trade = record_trade(
                session=session,
                user_email=user_email,
                symbol=f"{symbol}USDT",
                side="BUY",
                price=price,
                quantity=quantity_to_buy,
                total=usdt_amount,
                fee=fee
            )
            
            session.commit()
            
            trade_info = {
                'order_id': trade.order_id,
                'symbol': f"{symbol}USDT",
                'side': 'BUY',
                'price': price,
                'quantity': quantity_to_buy,
                'usdt_spent': usdt_amount,
                'fee': fee,
                'net_quantity': quantity_to_buy,
                'executed_at': trade.executed_at.isoformat(),
                'new_balance': {
                    'USDT': usdt_asset.balance,
                    symbol: asset.balance if asset else quantity_to_buy
                }
            }
            
            print(f"[ManualTrading] ✅ BUY executed: {quantity_to_buy:.8f} {symbol} @ ${price:.2f}")
            print(f"  Spent: ${usdt_amount:.2f} USDT (Fee: ${fee:.4f})")
            
            return True, trade_info, None
            
    except Exception as e:
        print(f"[ManualTrading] ❌ BUY transaction failed: {e}")
        return False, None, f"Transaction failed: {str(e)}"


def execute_manual_sell(
    symbol: str,
    quantity: float,
    user_email: str,
    current_price: Optional[float] = None
) -> Tuple[bool, Optional[dict], Optional[str]]:
    """
    Execute a manual SELL order
    
    Args:
        symbol: Asset to sell (e.g., 'BTC', 'ETH')
        quantity: Amount of asset to sell
        user_email: User identifier
        current_price: Optional price (fetched if not provided)
    
    Returns:
        Tuple of (success: bool, trade_info: dict or None, error_message: str or None)
    """
    # Validate symbol
    if symbol.upper() not in SUPPORTED_ASSETS:
        return False, None, f"Asset {symbol} is not supported for manual trading"
    
    symbol = symbol.upper()
    
    # Get current market price if not provided
    price = current_price or get_current_price_from_binance(symbol, "USDT")
    if price is None:
        return False, None, f"Could not fetch price for {symbol}/USDT"
    
    # Check if user has enough of the asset to sell
    asset_balance = get_user_balance(symbol, user_email)
    
    if asset_balance < quantity:
        return False, None, f"Insufficient {symbol} balance. Required: {quantity:.8f}, Available: {asset_balance:.8f}"
    
    # Calculate proceeds after fee
    gross_proceeds = price * quantity
    fee = gross_proceeds * TRADING_FEE
    net_proceeds = gross_proceeds - fee
    
    # Execute trade in database transaction
    try:
        with Session(engine) as session:
            # Deduct sold asset and calculate PnL
            asset_stmt = select(PortfolioAsset).where(
                PortfolioAsset.symbol == symbol,
                PortfolioAsset.user_email == user_email
            )
            asset = session.exec(asset_stmt).first()
            
            # Calculate PnL based on cost basis
            avg_cost_basis = getattr(asset, 'avg_cost_basis', 0.0) or 0.0
            total_invested = getattr(asset, 'total_invested', 0.0) or 0.0
            
            # Cost of the sold portion
            cost_of_sold = avg_cost_basis * quantity
            # PnL = What we received - What we paid (including fees)
            pnl = net_proceeds - cost_of_sold
            pnl_percent = ((net_proceeds / cost_of_sold) - 1) * 100 if cost_of_sold > 0 else 0.0
            
            # Update asset balance and total invested
            old_balance = asset.balance
            new_balance = old_balance - quantity
            
            # Proportionally reduce total invested
            if old_balance > 0:
                proportion_sold = quantity / old_balance
                invested_sold = total_invested * proportion_sold
                asset.total_invested = total_invested - invested_sold
            else:
                asset.total_invested = 0.0
            
            asset.balance = new_balance
            # Keep avg_cost_basis the same (it's still relevant for remaining holdings)
            session.add(asset)
            
            # Add USDT proceeds
            usdt_stmt = select(PortfolioAsset).where(
                PortfolioAsset.symbol == "USDT",
                PortfolioAsset.user_email == user_email
            )
            usdt_asset = session.exec(usdt_stmt).first()
            
            if usdt_asset:
                usdt_asset.balance += net_proceeds
                session.add(usdt_asset)
            else:
                new_usdt = PortfolioAsset(
                    symbol="USDT",
                    balance=net_proceeds,
                    user_email=user_email
                )
                session.add(new_usdt)
            
            # Record the trade with PnL
            trade = record_trade(
                session=session,
                user_email=user_email,
                symbol=f"{symbol}USDT",
                side="SELL",
                price=price,
                quantity=quantity,
                total=net_proceeds,
                fee=fee,
                pnl=pnl
            )
            
            session.commit()
            
            trade_info = {
                'order_id': trade.order_id,
                'symbol': f"{symbol}USDT",
                'side': 'SELL',
                'price': price,
                'quantity': quantity,
                'gross_proceeds': gross_proceeds,
                'fee': fee,
                'net_proceeds': net_proceeds,
                'avg_cost_basis': avg_cost_basis,
                'cost_of_sold': cost_of_sold,
                'pnl': pnl,
                'pnl_percent': pnl_percent,
                'executed_at': trade.executed_at.isoformat(),
                'new_balance': {
                    'USDT': usdt_asset.balance if usdt_asset else net_proceeds,
                    symbol: asset.balance
                }
            }
            
            pnl_emoji = "📈" if pnl >= 0 else "📉"
            print(f"[ManualTrading] ✅ SELL executed: {quantity:.8f} {symbol} @ ${price:.2f}")
            print(f"  Received: ${net_proceeds:.2f} USDT (Fee: ${fee:.4f})")
            print(f"  {pnl_emoji} PnL: ${pnl:.2f} ({pnl_percent:+.2f}%)")
            
            return True, trade_info, None
            
    except Exception as e:
        print(f"[ManualTrading] ❌ SELL transaction failed: {e}")
        return False, None, f"Transaction failed: {str(e)}"


def get_manual_trade_history(user_email: str, limit: int = 50) -> List[dict]:
    """
    Get manual trade history for a user
    
    Args:
        user_email: User identifier
        limit: Maximum number of trades to return
    
    Returns:
        List of trade dictionaries
    """
    with Session(engine) as session:
        statement = select(Trade).where(
            Trade.user_email == user_email,
            Trade.session_id.startswith("manual_")
        ).order_by(Trade.executed_at.desc()).limit(limit)
        
        trades = session.exec(statement).all()
        
        result = []
        for trade in trades:
            # Calculate pnl_percent for sell trades
            pnl_percent = None
            if trade.side == "SELL" and trade.pnl is not None:
                # cost_basis = total - pnl (what we got minus profit = what we paid)
                cost_basis = trade.total - trade.pnl
                if cost_basis > 0:
                    pnl_percent = (trade.pnl / cost_basis) * 100
            
            result.append({
                'id': trade.id,
                'order_id': trade.order_id,
                'symbol': trade.symbol,
                'side': trade.side,
                'price': trade.price,
                'quantity': trade.quantity,
                'total': trade.total,
                'pnl': trade.pnl,
                'pnl_percent': pnl_percent,
                'time': trade.executed_at.isoformat() if trade.executed_at else None
            })
        
        return result


def get_prices_for_assets(assets: List[str] = None) -> dict:
    """
    Get current prices for multiple assets
    
    Args:
        assets: List of asset symbols (defaults to SUPPORTED_ASSETS)
    
    Returns:
        Dictionary mapping symbol to price data
    """
    if assets is None:
        assets = SUPPORTED_ASSETS
    
    prices = {}
    for asset in assets:
        price = get_current_price_from_binance(asset, "USDT")
        if price:
            prices[asset] = {
                'symbol': asset,
                'price': price,
                'pair': f"{asset}USDT"
            }
    
    return prices


# ============================================
# PLACEHOLDER: Real Binance Order Execution
# ============================================

def execute_binance_order(
    symbol: str,
    side: str,  # 'BUY' or 'SELL'
    order_type: str,  # 'MARKET', 'LIMIT'
    quantity: float,
    price: Optional[float] = None,  # Required for LIMIT orders
    api_key: Optional[str] = None,
    api_secret: Optional[str] = None
) -> Tuple[bool, Optional[dict], Optional[str]]:
    """
    PLACEHOLDER: Execute a real order on Binance exchange
    
    This function is a placeholder for when you want to execute
    real orders on Binance. Uncomment and configure the code below.
    
    Args:
        symbol: Trading pair (e.g., 'BTCUSDT')
        side: 'BUY' or 'SELL'
        order_type: 'MARKET' or 'LIMIT'
        quantity: Amount to trade
        price: Limit price (required for LIMIT orders)
        api_key: Binance API key
        api_secret: Binance API secret
    
    Returns:
        Tuple of (success: bool, order_info: dict or None, error_message: str or None)
    """
    
    # ===== UNCOMMENT THIS CODE TO ENABLE REAL TRADING =====
    #
    # from binance.client import Client
    # from binance.exceptions import BinanceAPIException
    # import os
    # from dotenv import load_dotenv
    #
    # load_dotenv()
    #
    # # Use provided keys or fall back to environment variables
    # key = api_key or os.getenv("BINANCE_API_KEY")
    # secret = api_secret or os.getenv("BINANCE_SECRET_KEY")
    #
    # if not key or not secret:
    #     return False, None, "Binance API credentials not configured"
    #
    # try:
    #     client = Client(key, secret)
    #     
    #     if order_type == 'MARKET':
    #         if side == 'BUY':
    #             order = client.create_order(
    #                 symbol=symbol,
    #                 side=Client.SIDE_BUY,
    #                 type=Client.ORDER_TYPE_MARKET,
    #                 quantity=quantity
    #             )
    #         else:
    #             order = client.create_order(
    #                 symbol=symbol,
    #                 side=Client.SIDE_SELL,
    #                 type=Client.ORDER_TYPE_MARKET,
    #                 quantity=quantity
    #             )
    #     elif order_type == 'LIMIT':
    #         if price is None:
    #             return False, None, "Price required for LIMIT orders"
    #         
    #         if side == 'BUY':
    #             order = client.create_order(
    #                 symbol=symbol,
    #                 side=Client.SIDE_BUY,
    #                 type=Client.ORDER_TYPE_LIMIT,
    #                 timeInForce=Client.TIME_IN_FORCE_GTC,
    #                 quantity=quantity,
    #                 price=str(price)
    #             )
    #         else:
    #             order = client.create_order(
    #                 symbol=symbol,
    #                 side=Client.SIDE_SELL,
    #                 type=Client.ORDER_TYPE_LIMIT,
    #                 timeInForce=Client.TIME_IN_FORCE_GTC,
    #                 quantity=quantity,
    #                 price=str(price)
    #             )
    #     
    #     return True, order, None
    #     
    # except BinanceAPIException as e:
    #     return False, None, f"Binance API Error: {e.message}"
    # except Exception as e:
    #     return False, None, f"Order execution failed: {str(e)}"
    #
    # ===== END OF REAL TRADING CODE =====
    
    # For now, return a message indicating this is a placeholder
    return False, None, "Real Binance trading not enabled. Using simulated trading."
