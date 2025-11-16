"""Rate limiter for HTTP requests to avoid being blocked by suppliers.

Implements token bucket algorithm with per-domain rate limiting.
"""
from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock
from typing import DefaultDict
from urllib.parse import urlparse


class RateLimiter:
    """Thread-safe rate limiter using token bucket algorithm.

    Limits requests per domain to avoid IP bans from supplier websites.

    Example:
        >>> rate_limiter = RateLimiter(requests_per_second=0.2)  # 1 req / 5 sec
        >>> rate_limiter.wait_if_needed("https://particulier.edf.fr/tarif.pdf")
        >>> # Makes HTTP request here
        >>> rate_limiter.wait_if_needed("https://particulier.edf.fr/autre.pdf")
        >>> # Waits ~5 seconds before allowing next request
    """

    def __init__(
        self,
        requests_per_second: float = 0.2,  # Default: 1 request per 5 seconds
        burst_size: int = 1,
    ):
        """Initialize rate limiter.

        Args:
            requests_per_second: Max requests per second per domain
            burst_size: Max burst size (tokens in bucket)
        """
        self.rate = requests_per_second
        self.burst_size = burst_size
        self._buckets: DefaultDict[str, dict] = defaultdict(self._new_bucket)
        self._lock = Lock()

    def _new_bucket(self) -> dict:
        """Create new token bucket for a domain."""
        return {
            "tokens": self.burst_size,
            "last_update": time.time(),
        }

    def _get_domain(self, url: str) -> str:
        """Extract domain from URL."""
        parsed = urlparse(url)
        return parsed.netloc or "default"

    def wait_if_needed(self, url: str) -> float:
        """Wait if rate limit exceeded for this domain.

        Args:
            url: URL to rate limit

        Returns:
            Time waited in seconds (0 if no wait needed)
        """
        domain = self._get_domain(url)

        with self._lock:
            bucket = self._buckets[domain]
            now = time.time()

            # Refill tokens based on elapsed time
            elapsed = now - bucket["last_update"]
            bucket["tokens"] = min(
                self.burst_size,
                bucket["tokens"] + elapsed * self.rate
            )
            bucket["last_update"] = now

            # Check if we have tokens
            if bucket["tokens"] >= 1.0:
                bucket["tokens"] -= 1.0
                return 0.0  # No wait needed

            # Calculate wait time
            wait_time = (1.0 - bucket["tokens"]) / self.rate

        # Wait outside the lock to allow other threads
        time.sleep(wait_time)
        return wait_time

    def get_stats(self) -> dict[str, dict]:
        """Get current rate limiter stats per domain.

        Returns:
            Dict mapping domain to {tokens, last_update}
        """
        with self._lock:
            return {
                domain: bucket.copy()
                for domain, bucket in self._buckets.items()
            }


# Global rate limiter instance
default_rate_limiter = RateLimiter(requests_per_second=0.2)  # 1 req / 5 sec
