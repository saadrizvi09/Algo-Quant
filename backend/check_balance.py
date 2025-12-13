"""Quick script to check Binance Testnet balance"""
from binance.client import Client
import os
import time
from dotenv import load_dotenv

load_dotenv()

client = Client(os.getenv('BINANCE_API_KEY'), os.getenv('BINANCE_SECRET_KEY'), testnet=True)

# Sync timestamp
try:
    server_time = client.get_server_time()
    time_offset = server_time['serverTime'] - int(time.time() * 1000)
    client.timestamp_offset = time_offset - 1000
except Exception as e:
    print(f"Warning: Could not sync time: {e}")

account = client.get_account()

print("\n=== BINANCE TESTNET ACCOUNT BALANCES ===\n")

balances = [b for b in account['balances'] if float(b['free']) > 0 or float(b['locked']) > 0]

if balances:
    for b in balances:
        print(f"{b['asset']:8}  Free: {float(b['free']):12.4f}  Locked: {float(b['locked']):12.4f}")
else:
    print("⚠️  No balances found!")
    print("\n📝 NOTE: Binance Testnet accounts automatically receive test funds upon registration.")
    print("If you see no balances, please:")
    print("  1. Visit: https://testnet.binance.vision/")
    print("  2. Login with your account")
    print("  3. Check if test funds are visible in the web interface")

print("\n" + "="*50 + "\n")
