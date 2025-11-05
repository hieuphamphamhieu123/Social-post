"""
Test script cho AI Market Range API
"""
import requests
import json
import time
from loguru import logger

API_URL = "http://localhost:8000"


def test_health():
    """Test health endpoint"""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            logger.info("✓ Health check passed")
            print(json.dumps(response.json(), indent=2))
            return True
        else:
            logger.error(f"✗ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"✗ Health check error: {e}")
        return False


def test_market_range():
    """Test market range endpoint"""
    try:
        response = requests.get(f"{API_URL}/market-range", timeout=5)
        if response.status_code == 200:
            logger.info("✓ Market range endpoint working")
            data = response.json()
            print(json.dumps(data, indent=2))
            return True
        elif response.status_code == 503:
            logger.warning("⚠ Market range not ready yet")
            return False
        else:
            logger.error(f"✗ Market range failed: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"✗ Market range error: {e}")
        return False


def test_market_range_simple():
    """Test simple market range endpoint"""
    try:
        response = requests.get(f"{API_URL}/market-range/simple", timeout=5)
        if response.status_code == 200:
            logger.info("✓ Simple market range endpoint working")
            data = response.json()
            print(json.dumps(data, indent=2))
            return True
        else:
            logger.error(f"✗ Simple market range failed: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"✗ Simple market range error: {e}")
        return False


def test_orderflow_metrics():
    """Test orderflow metrics endpoint"""
    try:
        response = requests.get(f"{API_URL}/orderflow/metrics", timeout=5)
        if response.status_code == 200:
            logger.info("✓ Orderflow metrics endpoint working")
            data = response.json()
            print(json.dumps(data, indent=2))
            return True
        else:
            logger.error(f"✗ Orderflow metrics failed: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"✗ Orderflow metrics error: {e}")
        return False


def test_model_status():
    """Test model status endpoint"""
    try:
        response = requests.get(f"{API_URL}/model/status", timeout=5)
        if response.status_code == 200:
            logger.info("✓ Model status endpoint working")
            data = response.json()
            print(json.dumps(data, indent=2))
            return True
        else:
            logger.error(f"✗ Model status failed: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"✗ Model status error: {e}")
        return False


def monitor_market_range(duration=60, interval=5):
    """Monitor market range for specified duration"""
    logger.info(f"Monitoring market range for {duration} seconds...")

    end_time = time.time() + duration
    while time.time() < end_time:
        try:
            response = requests.get(f"{API_URL}/market-range/simple", timeout=5)
            if response.status_code == 200:
                data = response.json()
                logger.info(
                    f"Market Range: {data['market_range']:.2f} | "
                    f"Time: {data['timestamp']}"
                )
            else:
                logger.warning(f"Status: {response.status_code}")

        except Exception as e:
            logger.error(f"Error: {e}")

        time.sleep(interval)


def main():
    """Main test function"""
    print("=" * 60)
    print("AI Market Range API Test Suite")
    print("=" * 60)
    print()

    # Test API connection
    print("1. Testing API connection...")
    if not test_health():
        logger.error("API is not running or not accessible!")
        logger.info("Please start the API with: python main.py api")
        return

    print("\n" + "=" * 60)
    print("2. Testing market range endpoint...")
    time.sleep(2)
    test_market_range()

    print("\n" + "=" * 60)
    print("3. Testing simple market range endpoint...")
    time.sleep(2)
    test_market_range_simple()

    print("\n" + "=" * 60)
    print("4. Testing orderflow metrics endpoint...")
    time.sleep(2)
    test_orderflow_metrics()

    print("\n" + "=" * 60)
    print("5. Testing model status endpoint...")
    time.sleep(2)
    test_model_status()

    print("\n" + "=" * 60)
    print("6. Monitoring market range (30 seconds)...")
    time.sleep(2)
    monitor_market_range(duration=30, interval=5)

    print("\n" + "=" * 60)
    print("✓ All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
