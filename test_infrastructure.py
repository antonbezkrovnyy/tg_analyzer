"""Test script to verify tg_analyzer integration with shared infrastructure."""

import os
import sys

import httpx
import redis
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway


def test_redis():
    """Test Redis connection."""
    print("=" * 60)
    print("Testing Redis Connection")
    print("=" * 60)

    try:
        redis_url = os.getenv("REDIS_URL", "redis://tg-redis:6379")
        redis_password = os.getenv("REDIS_PASSWORD", "")

        r = redis.Redis.from_url(
            redis_url,
            password=redis_password if redis_password else None,
            decode_responses=True,
        )

        # Test PING
        result = r.ping()
        print(f"✅ Redis PING: {result}")

        # Test SET/GET
        r.set("tg_analyzer:test", "infrastructure_integration")
        value = r.get("tg_analyzer:test")
        print(f"✅ Redis SET/GET: {value}")

        # Test PubSub
        pubsub = r.pubsub()
        pubsub.subscribe("tg_analyzer:events")
        r.publish("tg_analyzer:events", "test_message")
        print("✅ Redis PubSub: Published test message")

        return True
    except Exception as e:
        print(f"❌ Redis Error: {e}")
        return False


def test_loki():
    """Test Loki connection."""
    print("\n" + "=" * 60)
    print("Testing Loki Connection")
    print("=" * 60)

    try:
        loki_url = os.getenv("LOKI_URL", "http://tg-loki:3100")

        # Test ready endpoint
        response = httpx.get(f"{loki_url}/ready", timeout=5.0)
        print(f"✅ Loki Ready: {response.status_code} {response.text}")

        # Test metrics endpoint
        response = httpx.get(f"{loki_url}/metrics", timeout=5.0)
        print(f"✅ Loki Metrics: {response.status_code} (available)")

        return True
    except Exception as e:
        print(f"❌ Loki Error: {e}")
        return False


def test_pushgateway():
    """Test Prometheus Pushgateway."""
    print("\n" + "=" * 60)
    print("Testing Prometheus Pushgateway")
    print("=" * 60)

    try:
        pushgateway_url = os.getenv(
            "PROMETHEUS_PUSHGATEWAY_URL", "http://tg-pushgateway:9091"
        )

        # Test metrics endpoint
        response = httpx.get(f"{pushgateway_url}/metrics", timeout=5.0)
        print(f"✅ Pushgateway Metrics: {response.status_code}")

        # Push test metric
        registry = CollectorRegistry()
        gauge = Gauge(
            "tg_analyzer_test_metric",
            "Test metric from tg_analyzer",
            registry=registry,
        )
        gauge.set(42)

        push_to_gateway(
            pushgateway_url.replace("http://", ""),
            job="tg_analyzer_test",
            registry=registry,
        )
        print("✅ Pushgateway: Test metric pushed successfully")

        return True
    except Exception as e:
        print(f"❌ Pushgateway Error: {e}")
        return False


def test_data_volume():
    """Test data volume from python-tg."""
    print("\n" + "=" * 60)
    print("Testing Data Volume (from python-tg)")
    print("=" * 60)

    try:
        data_path = os.getenv("TG_FETCHER_DATA_PATH", "/data")

        # Check if directory exists
        if not os.path.exists(data_path):
            print(f"❌ Data path does not exist: {data_path}")
            return False

        # List chats
        chats = [
            d
            for d in os.listdir(data_path)
            if os.path.isdir(os.path.join(data_path, d))
        ]
        print(f"✅ Data path exists: {data_path}")
        print(f"✅ Found {len(chats)} chats: {', '.join(chats[:3])}...")

        # Check for JSON files
        total_files = 0
        for chat in chats:
            chat_path = os.path.join(data_path, chat)
            json_files = [f for f in os.listdir(chat_path) if f.endswith(".json")]
            total_files += len(json_files)

        print(f"✅ Total JSON files: {total_files}")

        return True
    except Exception as e:
        print(f"❌ Data Volume Error: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("TG Analyzer - Infrastructure Integration Test")
    print("=" * 60)

    results = {
        "Redis": test_redis(),
        "Loki": test_loki(),
        "Pushgateway": test_pushgateway(),
        "Data Volume": test_data_volume(),
    }

    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:20s}: {status}")

    all_passed = all(results.values())
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All tests PASSED! Infrastructure integration is working.")
        print("=" * 60)
        sys.exit(0)
    else:
        print("⚠️  Some tests FAILED. Check errors above.")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
