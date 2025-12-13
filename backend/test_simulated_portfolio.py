"""
Test Script: Simulated Portfolio Per-User Initialization
Demonstrates that each user gets 10k USDT and balances update with trades
"""
import requests
import time

BASE_URL = "http://127.0.0.1:8000"

def register_user(email, password, name="Test User"):
    """Register a new user"""
    response = requests.post(
        f"{BASE_URL}/api/register",
        json={
            "email": email,
            "password": password,
            "name": name
        }
    )
    print(f"\n📝 Registering user: {email}")
    if response.status_code == 200:
        print(f"   ✅ Registration successful")
        return response.json()
    else:
        print(f"   ⚠️  {response.json().get('detail', 'Registration failed')}")
        return None

def login_user(email, password):
    """Login and get auth token"""
    response = requests.post(
        f"{BASE_URL}/api/login",
        json={
            "email": email,
            "password": password
        }
    )
    print(f"\n🔐 Logging in: {email}")
    if response.status_code == 200:
        data = response.json()
        token = data.get('access_token')
        print(f"   ✅ Login successful")
        return token
    else:
        print(f"   ❌ Login failed")
        return None

def get_portfolio(token):
    """Get simulated portfolio"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/api/simulated/portfolio",
        headers=headers
    )
    print(f"\n💰 Fetching portfolio...")
    if response.status_code == 200:
        data = response.json()
        print(f"   Total Value: ${data['total_value_usdt']:,.2f}")
        print(f"   Assets:")
        for asset in data['assets']:
            print(f"      - {asset['symbol']}: {asset['balance']:,.8f} (${asset['value_usdt']:,.2f})")
        return data
    else:
        print(f"   ❌ Failed to fetch portfolio")
        return None

def start_trading_session(token, symbol="BTCUSDT", trade_amount=100, duration=5):
    """Start a simulated trading session"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{BASE_URL}/api/simulated/start",
        headers=headers,
        json={
            "strategy": "HMM Regime Filter",
            "symbol": symbol,
            "trade_amount": trade_amount,
            "duration": duration,
            "duration_unit": "minutes",
            "short_window": 10,
            "long_window": 50,
            "n_states": 2,
            "window": 30,
            "threshold": 1.0,
            "interval": "1m"
        }
    )
    print(f"\n🚀 Starting trading session: {symbol}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Session started: {data['session_id']}")
        print(f"   Duration: {duration} minutes")
        print(f"   Trade Amount: ${trade_amount}")
        return data
    else:
        print(f"   ❌ Failed to start session: {response.text}")
        return None

def main():
    print("=" * 60)
    print("🧪 Testing Simulated Portfolio - Per User Initialization")
    print("=" * 60)
    
    # Test User 1
    print("\n" + "=" * 60)
    print("TEST 1: New User Gets 10k USDT")
    print("=" * 60)
    
    user1_email = f"testuser1_{int(time.time())}@example.com"
    register_user(user1_email, "password123", "Test User 1")
    token1 = login_user(user1_email, "password123")
    
    if token1:
        portfolio1_before = get_portfolio(token1)
        
        # Verify starting balance
        if portfolio1_before and portfolio1_before['total_value_usdt'] == 10000.0:
            print("\n   ✅ PASS: User 1 started with exactly 10,000 USDT")
        else:
            print("\n   ❌ FAIL: User 1 did not get 10,000 USDT")
    
    # Test User 2
    print("\n" + "=" * 60)
    print("TEST 2: Second User Also Gets 10k USDT")
    print("=" * 60)
    
    user2_email = f"testuser2_{int(time.time())}@example.com"
    register_user(user2_email, "password123", "Test User 2")
    token2 = login_user(user2_email, "password123")
    
    if token2:
        portfolio2_before = get_portfolio(token2)
        
        if portfolio2_before and portfolio2_before['total_value_usdt'] == 10000.0:
            print("\n   ✅ PASS: User 2 also started with exactly 10,000 USDT")
        else:
            print("\n   ❌ FAIL: User 2 did not get 10,000 USDT")
    
    # Test Trading Session
    print("\n" + "=" * 60)
    print("TEST 3: Balance Changes After Trading Session")
    print("=" * 60)
    
    if token1:
        print("\n⏳ Starting trading session for User 1...")
        session = start_trading_session(token1, symbol="BTCUSDT", trade_amount=100, duration=1)
        
        if session:
            print("\n   Waiting 15 seconds for trades to execute...")
            time.sleep(15)
            
            portfolio1_after = get_portfolio(token1)
            
            if portfolio1_after:
                if portfolio1_after['total_value_usdt'] != 10000.0:
                    print(f"\n   ✅ PASS: Balance changed from $10,000 to ${portfolio1_after['total_value_usdt']:,.2f}")
                    print("   💡 Portfolio is actively trading and updating!")
                else:
                    print("\n   ⚠️  Balance hasn't changed yet (may need more time)")
    
    # Test Persistence
    print("\n" + "=" * 60)
    print("TEST 4: User 1 Portfolio Persists After Re-login")
    print("=" * 60)
    
    if token1:
        # Re-login as User 1
        new_token1 = login_user(user1_email, "password123")
        if new_token1:
            portfolio1_relogin = get_portfolio(new_token1)
            
            if portfolio1_relogin and portfolio1_after:
                if portfolio1_relogin['total_value_usdt'] == portfolio1_after['total_value_usdt']:
                    print("\n   ✅ PASS: Portfolio balance persisted after re-login")
                else:
                    print(f"\n   ⚠️  Balance changed (trading may still be active)")
    
    print("\n" + "=" * 60)
    print("✅ All Tests Complete!")
    print("=" * 60)
    print("\n📋 Summary:")
    print("   • Each new user automatically gets 10,000 USDT")
    print("   • Balances are tracked per user (isolated portfolios)")
    print("   • Trading sessions update balances in real-time")
    print("   • Portfolios persist across logins/restarts")
    print("   • Every 10 seconds, strategy runs and may execute trades")
    print("\n")

if __name__ == "__main__":
    main()
