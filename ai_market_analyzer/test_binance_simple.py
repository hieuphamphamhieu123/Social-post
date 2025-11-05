"""
Simple Binance API test without WebSocket
"""
from binance.client import Client
from config.config import BINANCE_API_KEY, BINANCE_API_SECRET

print("Testing Binance API connection...")
print(f"API Key configured: {'Yes' if BINANCE_API_KEY else 'No'}")

# Test without auth (public data)
try:
    client = Client()  # No auth needed for public data

    # Test ping
    print("\n1. Testing ping...")
    result = client.ping()
    print(f"✅ Ping successful: {result}")

    # Test server time
    print("\n2. Testing server time...")
    result = client.get_server_time()
    print(f"✅ Server time: {result}")

    # Test getting ticker
    print("\n3. Testing PAXGUSDT ticker...")
    result = client.get_symbol_ticker(symbol="PAXGUSDT")
    print(f"✅ Current price: {result}")

    # Test recent trades
    print("\n4. Testing recent trades...")
    result = client.get_recent_trades(symbol="PAXGUSDT", limit=5)
    print(f"✅ Got {len(result)} trades")
    if result:
        print(f"   Last trade: price={result[0]['price']}, qty={result[0]['qty']}")

    print("\n✅ All tests passed! Binance API is accessible.")

except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nPossible issues:")
    print("- Internet connection")
    print("- Firewall blocking Binance")
    print("- VPN/Proxy issues")
