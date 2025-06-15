"""Tests for rate limiting module."""

from datetime import datetime, timedelta

import pytest

from alicemultiverse.core.exceptions import ValidationError
from alicemultiverse.interface.rate_limiter import RateLimitConfig, RateLimiter


class TestRateLimiter:
    """Test rate limiter functionality."""

    def test_basic_rate_limiting(self):
        """Test basic rate limiting within minute window."""
        config = RateLimitConfig(requests_per_minute=3)
        limiter = RateLimiter(config)

        # First 3 requests should succeed
        for i in range(3):
            limiter.check_request("client1")

        # 4th request should fail (with burst allowance, 5th fails)
        limiter.check_request("client1")  # 4th - allowed due to burst

        with pytest.raises(ValidationError, match="Rate limit exceeded"):
            limiter.check_request("client1")  # 5th - should fail

    def test_different_clients(self):
        """Test rate limiting is per-client."""
        config = RateLimitConfig(requests_per_minute=2)
        limiter = RateLimiter(config)

        # Client 1 uses their quota
        limiter.check_request("client1")
        limiter.check_request("client1")

        # Client 2 should still be able to make requests
        limiter.check_request("client2")
        limiter.check_request("client2")

        # Client 1 should be rate limited
        limiter.check_request("client1")  # Burst allowance
        with pytest.raises(ValidationError):
            limiter.check_request("client1")

    def test_operation_specific_limits(self):
        """Test operation-specific rate limits."""
        config = RateLimitConfig(
            requests_per_minute=10,
            search_per_minute=2
        )
        limiter = RateLimiter(config)

        # Regular requests
        limiter.check_request("client1")
        limiter.check_request("client1")

        # Search requests - limited to 2
        limiter.check_request("client1", "search")
        limiter.check_request("client1", "search")

        # 3rd search should fail (with burst, 4th fails)
        limiter.check_request("client1", "search")  # Burst
        with pytest.raises(ValidationError, match="searches per minute"):
            limiter.check_request("client1", "search")

        # Regular requests should still work
        limiter.check_request("client1")

    def test_organize_operation_limits(self):
        """Test organize operation rate limits."""
        config = RateLimitConfig(
            requests_per_hour=100,
            organize_per_hour=2
        )
        limiter = RateLimiter(config)

        # First 2 organize operations should succeed
        limiter.check_request("client1", "organize")
        limiter.check_request("client1", "organize")

        # 3rd should succeed due to burst allowance
        limiter.check_request("client1", "organize")

        # 4th should fail
        with pytest.raises(ValidationError, match="organize operations per hour"):
            limiter.check_request("client1", "organize")

    def test_window_reset(self):
        """Test that rate limit windows reset properly."""
        config = RateLimitConfig(requests_per_minute=2)
        limiter = RateLimiter(config)

        # Use up the quota
        limiter.check_request("client1")
        limiter.check_request("client1")
        limiter.check_request("client1")  # Burst

        # Should be rate limited
        with pytest.raises(ValidationError):
            limiter.check_request("client1")

        # Manually reset the window by modifying tracker
        with limiter._lock:
            tracker = limiter._minute_trackers["client1"]
            tracker.window_start = datetime.now() - timedelta(minutes=2)

        # Should work again after window reset
        limiter.check_request("client1")

    def test_get_remaining_quota(self):
        """Test getting remaining quota for a client."""
        config = RateLimitConfig(
            requests_per_minute=5,
            requests_per_hour=50,
            requests_per_day=500
        )
        limiter = RateLimiter(config)

        # Initial quota
        quota = limiter.get_remaining_quota("client1")
        assert quota["requests_per_minute"] == 5
        assert quota["requests_per_hour"] == 50
        assert quota["requests_per_day"] == 500

        # Use some quota
        limiter.check_request("client1")
        limiter.check_request("client1")

        quota = limiter.get_remaining_quota("client1")
        assert quota["requests_per_minute"] == 3
        assert quota["requests_per_hour"] == 48
        assert quota["requests_per_day"] == 498

    def test_reset_client(self):
        """Test resetting a client's rate limits."""
        config = RateLimitConfig(requests_per_minute=2)
        limiter = RateLimiter(config)

        # Use up quota
        limiter.check_request("client1")
        limiter.check_request("client1")
        limiter.check_request("client1")  # Burst

        # Should be rate limited
        with pytest.raises(ValidationError):
            limiter.check_request("client1")

        # Reset the client
        limiter.reset_client("client1")

        # Should work again
        limiter.check_request("client1")
        limiter.check_request("client1")

    def test_burst_allowance(self):
        """Test burst allowance calculation."""
        config = RateLimitConfig(
            requests_per_minute=10,
            burst_multiplier=1.5
        )
        limiter = RateLimiter(config)

        # Should allow 15 requests (10 * 1.5)
        for i in range(15):
            limiter.check_request("client1")

        # 16th should fail
        with pytest.raises(ValidationError):
            limiter.check_request("client1")

    def test_cleanup_old_entries(self):
        """Test cleanup of old tracking entries."""
        config = RateLimitConfig(
            requests_per_minute=5,
            cleanup_interval_minutes=0  # Force immediate cleanup
        )
        limiter = RateLimiter(config)

        # Create some entries
        limiter.check_request("client1")
        limiter.check_request("client2")
        limiter.check_request("client3")

        # Manually age the entries
        with limiter._lock:
            for client_id in ["client1", "client2"]:
                limiter._minute_trackers[client_id].window_start = (
                    datetime.now() - timedelta(minutes=3)
                )

        # Trigger cleanup
        limiter._cleanup_old_entries()

        # Old entries should be removed
        with limiter._lock:
            assert "client1" not in limiter._minute_trackers
            assert "client2" not in limiter._minute_trackers
            assert "client3" in limiter._minute_trackers

    def test_concurrent_requests(self):
        """Test thread safety with concurrent requests."""
        import threading

        config = RateLimitConfig(requests_per_minute=100)
        limiter = RateLimiter(config)

        errors = []
        success_count = [0]

        def make_requests(client_id):
            try:
                for _ in range(20):
                    limiter.check_request(client_id)
                    success_count[0] += 1
            except ValidationError as e:
                errors.append(str(e))

        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_requests, args=(f"client{i}",))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # All requests should succeed (5 clients * 20 requests = 100 total)
        assert success_count[0] == 100
        assert len(errors) == 0
