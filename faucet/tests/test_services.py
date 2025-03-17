import time
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.core.cache import cache
from web3.exceptions import Web3Exception
from faucet.services.ethereum import EthereumService
from faucet.services.rate_limiter import RateLimiter
from faucet.services.transaction_queue import TransactionQueue


class EthereumServiceTests(TestCase):
    """Test cases for the EthereumService"""

    @patch('faucet.services.ethereum.Web3')
    def setUp(self, mock_web3):
        # Configure Web3 mock
        self.mock_w3_instance = MagicMock()
        self.mock_w3_instance.is_connected.return_value = True
        self.mock_w3_instance.is_address.return_value = True
        self.mock_w3_instance.eth.get_balance.return_value = 1000000000000000000  # 1 ETH in wei
        self.mock_w3_instance.from_wei.return_value = 1.0
        self.mock_w3_instance.to_wei.return_value = 100000000000000  # 0.0001 ETH in wei
        self.mock_w3_instance.eth.get_transaction_count.return_value = 1
        self.mock_w3_instance.eth.gas_price = 20000000000  # 20 gwei
        self.mock_w3_instance.eth.account.sign_transaction.return_value = MagicMock(
            rawTransaction=b'0x1234'
        )
        self.mock_w3_instance.eth.send_raw_transaction.return_value = b'0x5678'
        self.mock_w3_instance.to_hex.return_value = '0x5678'

        mock_web3.HTTPProvider.return_value = "http_provider"
        mock_web3.return_value = self.mock_w3_instance

        # Create service instance with test settings
        with self.settings(
            ETHEREUM_PROVIDER_URL='https://test-rpc-url.com',
            ETHEREUM_FALLBACK_PROVIDERS='https://fallback1.com,https://fallback2.com',
            ETHEREUM_PRIVATE_KEY='0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef',
            ETHEREUM_FROM_ADDRESS='0x742d35Cc6634C0532925a3b844Bc454e4438f44e',
            ETHEREUM_CHAIN_ID=11155111,
            FAUCET_AMOUNT='0.0001',
            ETHEREUM_MAX_RETRIES=3,
            ETHEREUM_RETRY_DELAY=1
        ):
            self.service = EthereumService()

    def test_validate_address(self):
        """Test address validation"""
        # Valid address
        self.assertTrue(self.service.validate_address('0x742d35Cc6634C0532925a3b844Bc454e4438f44e'))

        # Invalid address
        self.mock_w3_instance.is_address.return_value = False
        self.assertFalse(self.service.validate_address('invalid-address'))

    def test_get_balance(self):
        """Test getting wallet balance"""
        balance = self.service.get_balance()
        self.assertEqual(balance, 1.0)

        # Verify method calls
        self.mock_w3_instance.eth.get_balance.assert_called_once_with(
            '0x742d35Cc6634C0532925a3b844Bc454e4438f44e'
        )
        self.mock_w3_instance.from_wei.assert_called_once()

    def test_send_transaction(self):
        """Test sending a transaction"""
        tx_hash = self.service.send_transaction('0x742d35Cc6634C0532925a3b844Bc454e4438f44e')
        self.assertEqual(tx_hash, '0x5678')

        # Verify method calls
        self.mock_w3_instance.eth.get_transaction_count.assert_called_once()
        self.mock_w3_instance.eth.account.sign_transaction.assert_called_once()
        self.mock_w3_instance.eth.send_raw_transaction.assert_called_once()
        self.mock_w3_instance.to_hex.assert_called_once()

    def test_send_transaction_invalid_address(self):
        """Test sending to an invalid address"""
        self.mock_w3_instance.is_address.return_value = False

        with self.assertRaises(ValueError) as context:
            self.service.send_transaction('invalid-address')

        self.assertIn("Invalid Ethereum address format", str(context.exception))

    def test_send_transaction_insufficient_funds(self):
        """Test sending with insufficient funds"""
        # Configure mock to return low balance
        self.mock_w3_instance.from_wei.return_value = 0.00005  # Less than 0.0001

        with self.assertRaises(ValueError) as context:
            self.service.send_transaction('0x742d35Cc6634C0532925a3b844Bc454e4438f44e')

        self.assertIn("Insufficient funds", str(context.exception))

    def test_connection_error_with_fallback(self):
        """Test connection error with fallback"""
        # Configure primary provider to fail but fallback to succeed
        self.mock_w3_instance.is_connected.side_effect = [False, True]

        with patch('faucet.services.ethereum.Web3') as mock_web3:
            # Configure new Web3 instance for fallback
            mock_fallback_instance = MagicMock()
            mock_fallback_instance.is_connected.return_value = True
            mock_web3.return_value = mock_fallback_instance

            # Re-initialize with connection error on primary
            with self.settings(
                ETHEREUM_PROVIDER_URL='https://primary-down.com',
                ETHEREUM_FALLBACK_PROVIDERS='https://fallback-up.com',
                ETHEREUM_PRIVATE_KEY='0x0123',
                ETHEREUM_FROM_ADDRESS='0x0123',
                ETHEREUM_CHAIN_ID=11155111,
                ETHEREUM_MAX_RETRIES=3,
                ETHEREUM_RETRY_DELAY=1
            ):
                # This should succeed with fallback
                service = EthereumService()
                self.assertEqual(service.w3, mock_fallback_instance)

    def test_retry_on_web3_exception(self):
        """Test retrying on Web3 exception"""
        # Configure send_raw_transaction to fail first, then succeed
        self.mock_w3_instance.eth.send_raw_transaction.side_effect = [
            Web3Exception("RPC Error"),
            b'0x5678'
        ]

        # First attempt will fail, second will succeed
        tx_hash = self.service.send_transaction('0x742d35Cc6634C0532925a3b844Bc454e4438f44e')
        self.assertEqual(tx_hash, '0x5678')

        # Verify multiple calls
        self.assertEqual(self.mock_w3_instance.eth.send_raw_transaction.call_count, 2)


class RateLimiterTests(TestCase):
    """Test cases for the RateLimiter"""

    def setUp(self):
        # Clear cache before each test
        cache.clear()

        # Create limiter with test settings
        with self.settings(RATE_LIMIT_TIMEOUT=60):
            self.limiter = RateLimiter()

    def test_is_rate_limited_first_request(self):
        """Test rate limiting for the first request (should not be limited)"""
        is_limited, _ = self.limiter.is_rate_limited('127.0.0.1', '0x742d35Cc6634C0532925a3b844Bc454e4438f44e')
        self.assertFalse(is_limited)

    def test_is_rate_limited_subsequent_request(self):
        """Test rate limiting for a subsequent request within timeout"""
        # Record the first request
        self.limiter.record_request('127.0.0.1', '0x742d35Cc6634C0532925a3b844Bc454e4438f44e')

        # Check rate limiting
        is_limited, remaining_time = self.limiter.is_rate_limited('127.0.0.1', '0x742d35Cc6634C0532925a3b844Bc454e4438f44e')
        self.assertTrue(is_limited)
        self.assertGreater(remaining_time, 0)
        self.assertLessEqual(remaining_time, 60)

    def test_is_rate_limited_different_ip(self):
        """Test rate limiting for different IP (should not be limited)"""
        # Record a request for one IP
        self.limiter.record_request('127.0.0.1', '0x742d35Cc6634C0532925a3b844Bc454e4438f44e')

        # Check rate limiting for different IP
        is_limited, _ = self.limiter.is_rate_limited('192.168.1.1', '0x742d35Cc6634C0532925a3b844Bc454e4438f44e')
        self.assertTrue(is_limited)  # Still limited because same wallet

    def test_is_rate_limited_different_wallet(self):
        """Test rate limiting for different wallet (should not be limited)"""
        # Record a request for one wallet
        self.limiter.record_request('127.0.0.1', '0x742d35Cc6634C0532925a3b844Bc454e4438f44e')

        # Check rate limiting for different wallet
        is_limited, _ = self.limiter.is_rate_limited('127.0.0.1', '0x123456789abcdef0123456789abcdef01234567')
        self.assertTrue(is_limited)  # Still limited because same IP

    @override_settings(RATE_LIMIT_TIMEOUT=2)
    def test_rate_limit_expiration(self):
        """Test that rate limiting expires after timeout"""
        # Create limiter with shorter timeout
        limiter = RateLimiter()

        # Record the request
        limiter.record_request('127.0.0.1', '0x742d35Cc6634C0532925a3b844Bc454e4438f44e')

        # Should be rate limited immediately
        is_limited, _ = limiter.is_rate_limited('127.0.0.1', '0x742d35Cc6634C0532925a3b844Bc454e4438f44e')
        self.assertTrue(is_limited)

        # Wait for timeout to expire
        time.sleep(3)

        # Should no longer be rate limited
        is_limited, _ = limiter.is_rate_limited('127.0.0.1', '0x742d35Cc6634C0532925a3b844Bc454e4438f44e')
        self.assertFalse(is_limited)


class TransactionQueueTests(TestCase):
    """Test cases for the TransactionQueue"""

    @patch('faucet.services.transaction_queue.EthereumService')
    @patch('faucet.models.Transaction.objects.get')
    def setUp(self, mock_get_transaction, mock_eth_service):
        # Configure Transaction.objects.get mock
        self.mock_transaction = MagicMock()
        self.mock_transaction.status = 'pending'
        self.mock_transaction.id = 1
        self.mock_transaction.wallet_address = '0x742d35Cc6634C0532925a3b844Bc454e4438f44e'
        mock_get_transaction.return_value = self.mock_transaction

        # Configure EthereumService mock
        self.mock_eth_instance = MagicMock()
        self.mock_eth_instance.send_transaction.return_value = '0x1234'
        mock_eth_service.return_value = self.mock_eth_instance

        # Create queue instance
        self.queue = TransactionQueue()

    def test_enqueue_transaction(self):
        """Test enqueueing a transaction"""
        self.queue.enqueue_transaction(
            transaction_id=1,
            wallet_address='0x742d35Cc6634C0532925a3b844Bc454e4438f44e',
            ip_address='127.0.0.1'
        )

        # Queue should have one item
        self.assertEqual(self.queue.queue.qsize(), 1)

        # Get the item to verify contents
        priority, data = self.queue.queue.get()
        self.assertEqual(priority, 0)  # Default priority
        self.assertEqual(data['id'], 1)
        self.assertEqual(data['wallet_address'], '0x742d35Cc6634C0532925a3b844Bc454e4438f44e')
        self.assertEqual(data['ip_address'], '127.0.0.1')

    def test_enqueue_with_priority(self):
        """Test enqueueing with priority"""
        self.queue.enqueue_transaction(
            transaction_id=1,
            wallet_address='0x742d35Cc6634C0532925a3b844Bc454e4438f44e',
            ip_address='127.0.0.1',
            priority=-10  # Higher priority (lower number)
        )

        self.queue.enqueue_transaction(
            transaction_id=2,
            wallet_address='0x123456789abcdef0123456789abcdef01234567',
            ip_address='127.0.0.2',
            priority=0  # Normal priority
        )

        # First item should be the higher priority one
        priority, data = self.queue.queue.get()
        self.assertEqual(priority, -10)
        self.assertEqual(data['id'], 1)

        # Second item should be the normal priority one
        priority, data = self.queue.queue.get()
        self.assertEqual(priority, 0)
        self.assertEqual(data['id'], 2)

    @patch('threading.Thread')
    def test_start_worker(self, mock_thread):
        """Test starting worker thread"""
        self.queue.start_worker()

        # Thread should be started
        mock_thread.assert_called_once()
        mock_thread.return_value.start.assert_called_once()
        self.assertTrue(self.queue.is_running)

    def test_stop_worker(self):
        """Test stopping worker thread"""
        # Mock the worker thread
        self.queue.worker_thread = MagicMock()
        self.queue.is_running = True

        # Stop the worker
        self.queue.stop_worker()

        # Thread should be joined
        self.queue.worker_thread.join.assert_called_once()
        self.assertFalse(self.queue.is_running)