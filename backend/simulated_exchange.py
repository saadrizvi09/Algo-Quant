"""
Simulated Exchange Service
Manages internal portfolio and executes simulated trades against database
"""
from typing import Optional, Tuple
from sqlmodel import Session, select
from database import engine
from models import PortfolioAsset
from binance.client import Client
import os
from dotenv import load_dotenv

load_dotenv()

# Trading fee (0.1% as typical exchange fee)
TRADING_FEE = 0.001

# Binance client for fetching real-time prices
TESTNET_API_KEY = os.getenv("BINANCE_API_KEY", "")
TESTNET_API_SECRET = os.getenv("BINANCE_SECRET_KEY", "")


def get_binance_client():
    """Get Binance client for fetching real-time market prices"""
    return Client(TESTNET_API_KEY, TESTNET_API_SECRET, testnet=True)


def get_current_price(symbol: str, quote: str = "USDT") -> Optional[float]:
    """
    Fetch current market price from Binance testnet (free) or Yahoo Finance fallback
    
    Args:
        symbol: Base asset (e.g., 'BTC', 'ETH')
        quote: Quote asset (e.g., 'USDT')
    
    Returns:
        Current price or None if error
    """
    # Try Binance testnet first (free API, no paid subscription needed)
    try:
        client = get_binance_client()
        trading_pair = f"{symbol}{quote}"
        ticker = client.get_symbol_ticker(symbol=trading_pair)
        return float(ticker['price'])
    except Exception as e:
        print(f"[SimEx] Binance fetch failed for {symbol}/{quote}, trying Yahoo Finance: {e}")
        
        # Fallback to Yahoo Finance (completely free, no API key needed)
        try:
            import yfinance as yf
            ticker_symbol = f"{symbol}-{quote}" if quote == "USD" else f"{symbol}-USD"
            ticker = yf.Ticker(ticker_symbol)
            price_data = ticker.history(period="1d", interval="1m")
            
            if not price_data.empty:
                price = float(price_data['Close'].iloc[-1])
                # Convert to USDT if needed (assuming USD ≈ USDT)
                return price
            else:
                print(f"[SimEx] ❌ No price data available for {symbol}/{quote}")
                return None
        except Exception as yf_error:
            print(f"[SimEx] ❌ Yahoo Finance fallback failed: {yf_error}")
            return None


def get_balance(symbol: str, user_email: str = "default_user") -> float:
    """
    Get current balance of an asset from internal portfolio
    
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


def update_balance(symbol: str, amount: float, user_email: str = "default_user") -> bool:
    """
    Update balance of an asset (internal helper)
    
    Args:
        symbol: Asset symbol
        amount: Amount to add (positive) or subtract (negative)
        user_email: User identifier
    
    Returns:
        True if successful, False otherwise
    """
    try:
        with Session(engine) as session:
            statement = select(PortfolioAsset).where(
                PortfolioAsset.symbol == symbol,
                PortfolioAsset.user_email == user_email
            )
            asset = session.exec(statement).first()
            
            if asset:
                asset.balance += amount
                session.add(asset)
            else:
                # Create new asset entry
                asset = PortfolioAsset(
                    symbol=symbol,
                    balance=amount,
                    user_email=user_email
                )
                session.add(asset)
            
            session.commit()
            return True
    except Exception as e:
        print(f"[SimEx] Error updating balance for {symbol}: {e}")
        return False


def execute_buy(
    symbol: str, 
    quote_symbol: str, 
    amount_to_buy: float, 
    user_email: str = "default_user"
) -> Tuple[bool, Optional[dict]]:
    """
    Execute a simulated BUY order
    
    Args:
        symbol: Asset to buy (e.g., 'BTC', 'ETH')
        quote_symbol: Asset to pay with (e.g., 'USDT')
        amount_to_buy: Quantity of symbol to buy
        user_email: User identifier
    
    Returns:
        Tuple of (success: bool, trade_info: dict or None)
    """
    # Get current market price
    price = get_current_price(symbol, quote_symbol)
    if price is None:
        print(f"[SimEx] ❌ BUY failed: Could not fetch price for {symbol}/{quote_symbol}")
        return False, None
    
    # Calculate cost including fee
    cost_before_fee = price * amount_to_buy
    fee = cost_before_fee * TRADING_FEE
    total_cost = cost_before_fee + fee
    
    # Check if we have enough quote currency
    quote_balance = get_balance(quote_symbol, user_email)
    
    if quote_balance < total_cost:
        print(f"[SimEx] ❌ BUY failed: Insufficient {quote_symbol}")
        print(f"  Required: {total_cost:.2f} {quote_symbol}")
        print(f"  Available: {quote_balance:.2f} {quote_symbol}")
        return False, None
    
    # Execute trade in database transaction
    try:
        with Session(engine) as session:
            # Deduct quote currency
            quote_stmt = select(PortfolioAsset).where(
                PortfolioAsset.symbol == quote_symbol,
                PortfolioAsset.user_email == user_email
            )
            quote_asset = session.exec(quote_stmt).first()
            quote_asset.balance -= total_cost
            session.add(quote_asset)
            
            # Add purchased asset
            symbol_stmt = select(PortfolioAsset).where(
                PortfolioAsset.symbol == symbol,
                PortfolioAsset.user_email == user_email
            )
            symbol_asset = session.exec(symbol_stmt).first()
            
            if symbol_asset:
                symbol_asset.balance += amount_to_buy
                session.add(symbol_asset)
            else:
                new_asset = PortfolioAsset(
                    symbol=symbol,
                    balance=amount_to_buy,
                    user_email=user_email
                )
                session.add(new_asset)
            
            session.commit()
            
            trade_info = {
                'symbol': f"{symbol}{quote_symbol}",
                'side': 'BUY',
                'price': price,
                'quantity': amount_to_buy,
                'cost': cost_before_fee,
                'fee': fee,
                'total': total_cost
            }
            
            print(f"[SimEx] ✅ BUY executed: {amount_to_buy:.8f} {symbol} @ {price:.2f} {quote_symbol}")
            print(f"  Cost: {cost_before_fee:.2f} + Fee: {fee:.2f} = {total_cost:.2f} {quote_symbol}")
            
            return True, trade_info
            
    except Exception as e:
        print(f"[SimEx] ❌ BUY transaction failed: {e}")
        return False, None


def execute_sell(
    symbol: str, 
    quote_symbol: str, 
    amount_to_sell: float, 
    user_email: str = "default_user"
) -> Tuple[bool, Optional[dict]]:
    """
    Execute a simulated SELL order
    
    Args:
        symbol: Asset to sell (e.g., 'BTC', 'ETH')
        quote_symbol: Asset to receive (e.g., 'USDT')
        amount_to_sell: Quantity of symbol to sell
        user_email: User identifier
    
    Returns:
        Tuple of (success: bool, trade_info: dict or None)
    """
    # Get current market price
    price = get_current_price(symbol, quote_symbol)
    if price is None:
        print(f"[SimEx] ❌ SELL failed: Could not fetch price for {symbol}/{quote_symbol}")
        return False, None
    
    # Check if we have enough asset to sell
    symbol_balance = get_balance(symbol, user_email)
    
    if symbol_balance < amount_to_sell:
        print(f"[SimEx] ❌ SELL failed: Insufficient {symbol}")
        print(f"  Required: {amount_to_sell:.8f} {symbol}")
        print(f"  Available: {symbol_balance:.8f} {symbol}")
        return False, None
    
    # Calculate proceeds after fee
    proceeds_before_fee = price * amount_to_sell
    fee = proceeds_before_fee * TRADING_FEE
    net_proceeds = proceeds_before_fee - fee
    
    # Execute trade in database transaction
    try:
        with Session(engine) as session:
            # Deduct sold asset
            symbol_stmt = select(PortfolioAsset).where(
                PortfolioAsset.symbol == symbol,
                PortfolioAsset.user_email == user_email
            )
            symbol_asset = session.exec(symbol_stmt).first()
            symbol_asset.balance -= amount_to_sell
            session.add(symbol_asset)
            
            # Add quote currency proceeds
            quote_stmt = select(PortfolioAsset).where(
                PortfolioAsset.symbol == quote_symbol,
                PortfolioAsset.user_email == user_email
            )
            quote_asset = session.exec(quote_stmt).first()
            
            if quote_asset:
                quote_asset.balance += net_proceeds
                session.add(quote_asset)
            else:
                new_asset = PortfolioAsset(
                    symbol=quote_symbol,
                    balance=net_proceeds,
                    user_email=user_email
                )
                session.add(new_asset)
            
            session.commit()
            
            trade_info = {
                'symbol': f"{symbol}{quote_symbol}",
                'side': 'SELL',
                'price': price,
                'quantity': amount_to_sell,
                'proceeds': proceeds_before_fee,
                'fee': fee,
                'total': net_proceeds
            }
            
            print(f"[SimEx] ✅ SELL executed: {amount_to_sell:.8f} {symbol} @ {price:.2f} {quote_symbol}")
            print(f"  Proceeds: {proceeds_before_fee:.2f} - Fee: {fee:.2f} = {net_proceeds:.2f} {quote_symbol}")
            
            return True, trade_info
            
    except Exception as e:
        print(f"[SimEx] ❌ SELL transaction failed: {e}")
        return False, None


def get_portfolio_summary(user_email: str = "default_user") -> dict:
    """
    Get complete portfolio summary with current values
    
    Args:
        user_email: User identifier
    
    Returns:
        Dictionary with portfolio details
    """
    with Session(engine) as session:
        statement = select(PortfolioAsset).where(PortfolioAsset.user_email == user_email)
        assets = session.exec(statement).all()
        
        portfolio = []
        total_value_usdt = 0.0
        
        for asset in assets:
            if asset.balance > 0.00000001:  # Ignore dust
                if asset.symbol == "USDT":
                    value_usdt = asset.balance
                else:
                    price = get_current_price(asset.symbol, "USDT")
                    value_usdt = asset.balance * price if price else 0.0
                
                portfolio.append({
                    'symbol': asset.symbol,
                    'balance': asset.balance,
                    'value_usdt': value_usdt
                })
                total_value_usdt += value_usdt
        
        return {
            'assets': portfolio,
            'total_value_usdt': total_value_usdt,
            'user_email': user_email
        }
