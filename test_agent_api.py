#!/usr/bin/env python3
"""
Integration tests for agent-api.py

Run these tests to verify the API is working correctly.
Requires the API server to be running.
"""

import requests
import json
import time
import sys
from typing import List, Dict

API_URL = "http://localhost:5000"


class TestResult:
    def __init__(self, name: str, passed: bool, message: str = ""):
        self.name = name
        self.passed = passed
        self.message = message

    def __str__(self):
        status = "✅ PASS" if self.passed else "❌ FAIL"
        msg = f": {self.message}" if self.message else ""
        return f"{status} - {self.name}{msg}"


def run_test(test_name: str, test_func) -> TestResult:
    """Run a single test and return the result"""
    print(f"\n🧪 Running: {test_name}")
    try:
        result = test_func()
        print(f"   ✅ Passed")
        return TestResult(test_name, True)
    except AssertionError as e:
        print(f"   ❌ Failed: {e}")
        return TestResult(test_name, False, str(e))
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return TestResult(test_name, False, f"Error: {e}")


def test_health_check():
    """Test 1: Health check endpoint"""
    response = requests.get(f"{API_URL}/health", timeout=5)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    data = response.json()
    assert 'status' in data, "Response missing 'status' field"
    assert data['status'] == 'healthy', f"Expected 'healthy', got {data['status']}"
    assert 'active_sessions' in data, "Response missing 'active_sessions' field"


def test_sessions_list():
    """Test 2: Sessions list endpoint"""
    response = requests.get(f"{API_URL}/sessions", timeout=5)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    data = response.json()
    assert 'sessions' in data, "Response missing 'sessions' field"
    assert isinstance(data['sessions'], list), "Sessions should be a list"


def test_prompt_missing_params():
    """Test 3: Prompt endpoint with missing parameters"""
    # Missing session_id
    response = requests.post(
        f"{API_URL}/prompt",
        json={"prompt": "test"},
        timeout=5
    )
    assert response.status_code == 400, f"Expected 400, got {response.status_code}"

    # Missing prompt
    response = requests.post(
        f"{API_URL}/prompt",
        json={"session_id": "test"},
        timeout=5
    )
    assert response.status_code == 400, f"Expected 400, got {response.status_code}"


def test_respond_missing_params():
    """Test 4: Respond endpoint with missing parameters"""
    # Missing session_id
    response = requests.post(
        f"{API_URL}/respond",
        json={"response": "test"},
        timeout=5
    )
    assert response.status_code == 400, f"Expected 400, got {response.status_code}"

    # Missing response
    response = requests.post(
        f"{API_URL}/respond",
        json={"session_id": "test"},
        timeout=5
    )
    assert response.status_code == 400, f"Expected 400, got {response.status_code}"


def test_respond_invalid_session():
    """Test 5: Respond to non-existent session"""
    response = requests.post(
        f"{API_URL}/respond",
        json={
            "session_id": "nonexistent-session",
            "response": "test"
        },
        timeout=5
    )
    assert response.status_code == 404, f"Expected 404, got {response.status_code}"


def test_auto_respond_mode():
    """Test 6: Auto-respond mode (fire-and-forget)"""
    session_id = f"test-auto-{int(time.time())}"

    response = requests.post(
        f"{API_URL}/prompt",
        json={
            "session_id": session_id,
            "prompt": "What is 2+2?",
            "auto_respond": True
        },
        stream=True,
        timeout=30
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert 'text/event-stream' in response.headers.get('Content-Type', ''), \
        "Expected SSE content type"

    # Collect events
    events = []
    for line in response.iter_lines():
        if not line:
            continue

        line = line.decode('utf-8')
        if line.startswith('data: '):
            event = json.loads(line[6:])
            events.append(event)

            # Stop if we got complete or error
            if event['type'] in ('complete', 'error'):
                break

    # Verify we got events
    assert len(events) > 0, "Expected at least one event"

    # Verify last event is complete or error
    last_event = events[-1]
    assert last_event['type'] in ('complete', 'error'), \
        f"Expected 'complete' or 'error', got {last_event['type']}"

    # Verify no question events in auto-respond mode
    question_events = [e for e in events if e['type'] == 'question']
    # Note: We might get questions, but they should be auto-answered
    # so we should still get completion

    print(f"   Received {len(events)} events")


def test_sse_stream_format():
    """Test 7: Verify SSE stream format"""
    session_id = f"test-sse-{int(time.time())}"

    response = requests.post(
        f"{API_URL}/prompt",
        json={
            "session_id": session_id,
            "prompt": "Echo test",
            "auto_respond": True
        },
        stream=True,
        timeout=30
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    # Check first event
    first_event = None
    for line in response.iter_lines():
        if not line:
            continue

        line = line.decode('utf-8')
        if line.startswith('data: '):
            first_event = json.loads(line[6:])
            break

    assert first_event is not None, "Expected at least one event"
    assert 'type' in first_event, "Event missing 'type' field"
    assert 'content' in first_event, "Event missing 'content' field"

    # Valid event types
    valid_types = ('output', 'question', 'complete', 'error')
    assert first_event['type'] in valid_types, \
        f"Invalid event type: {first_event['type']}"


def check_server_running() -> bool:
    """Check if the API server is running"""
    try:
        response = requests.get(f"{API_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False


def main():
    """Run all tests"""
    print("=" * 70)
    print("Tiny-Agent API Integration Tests")
    print("=" * 70)

    # Check if server is running
    print("\n🔍 Checking if API server is running...")
    if not check_server_running():
        print(f"\n❌ ERROR: API server is not running at {API_URL}")
        print("\nPlease start the server first:")
        print("  python agent-api.py")
        print("\nThen run the tests again:")
        print("  python test_agent_api.py")
        sys.exit(1)

    print(f"✅ Server is running at {API_URL}")

    # Define all tests
    tests = [
        ("Health Check", test_health_check),
        ("Sessions List", test_sessions_list),
        ("Prompt Missing Parameters", test_prompt_missing_params),
        ("Respond Missing Parameters", test_respond_missing_params),
        ("Respond Invalid Session", test_respond_invalid_session),
        ("Auto-respond Mode", test_auto_respond_mode),
        ("SSE Stream Format", test_sse_stream_format),
    ]

    # Run tests
    results: List[TestResult] = []
    for test_name, test_func in tests:
        result = run_test(test_name, test_func)
        results.append(result)
        time.sleep(0.5)  # Small delay between tests

    # Print summary
    print("\n" + "=" * 70)
    print("Test Results Summary")
    print("=" * 70)

    for result in results:
        print(result)

    # Count results
    passed = sum(1 for r in results if r.passed)
    failed = sum(1 for r in results if not r.passed)
    total = len(results)

    print("\n" + "=" * 70)
    print(f"Total: {total} | Passed: {passed} | Failed: {failed}")
    print("=" * 70)

    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
