import time
from django.core.cache import cache
from django.conf import settings
from faucet.models import Transaction


class RateLimiter:
    """Service for rate limiting faucet requests based on IP and wallet address"""

    def __init__(self):
        # Get rate limit timeout from settings (default 1 minute / 60 seconds)
        self.timeout = getattr(settings, 'RATE_LIMIT_TIMEOUT', 60)

    def is_rate_limited(self, ip_address, wallet_address):
        """
        Check if the request is rate limited
        Returns (is_limited, remaining_time) tuple
        """
        current_time = int(time.time())

        # Create cache keys for IP and wallet address
        ip_cache_key = f"faucet_ratelimit_ip_{ip_address}"
        wallet_cache_key = f"faucet_ratelimit_wallet_{wallet_address}"

        # Check if IP is rate limited
        ip_last_request = cache.get(ip_cache_key)
        if ip_last_request:
            time_elapsed = current_time - ip_last_request
            if time_elapsed < self.timeout:
                return True, self.timeout - time_elapsed

        # Check if wallet is rate limited
        wallet_last_request = cache.get(wallet_cache_key)
        if wallet_last_request:
            time_elapsed = current_time - wallet_last_request
            if time_elapsed < self.timeout:
                return True, self.timeout - time_elapsed

        return False, 0

    def record_request(self, ip_address, wallet_address):
        """Record a request to update rate limiting"""
        current_time = int(time.time())

        # Create cache keys for IP and wallet address
        ip_cache_key = f"faucet_ratelimit_ip_{ip_address}"
        wallet_cache_key = f"faucet_ratelimit_wallet_{wallet_address}"

        # Set the cache with expiration = timeout
        cache.set(ip_cache_key, current_time, self.timeout)
        cache.set(wallet_cache_key, current_time, self.timeout)