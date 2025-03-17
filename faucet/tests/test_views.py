import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from faucet.models import Transaction
from faucet.services.ethereum import EthereumService
from faucet.services.rate_limiter import RateLimiter


class FundViewTests(TestCase):
    """Test cases for the FundView API endpoint"""

    def setUp(self):
        self.client = APIClient()
        self.url = reverse('fund')
        self.valid_payload = {
            'wallet_address': '0x742d35Cc6634C0532925a3b844Bc454e4438f44e'
        }

        # Mock the EthereumService
        self.eth_service_patcher = patch('faucet.views.EthereumService')
        self.mock_eth_service = self.eth_service_patcher.start()

        # Configure the mock
        self.mock_eth_instance = MagicMock()
        self.mock_eth_instance.send_transaction.return_value = '0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef'
        self.mock_eth_instance.amount = 0.0001
        self.mock_eth_service.return_value = self.mock_eth_instance

        # Mock the RateLimiter
        self.rate_limiter_patcher = patch('faucet.views.RateLimiter')
        self.mock_rate_limiter = self.rate_limiter_patcher.start()

        # Configure the mock
        self.mock_rate_limiter_instance = MagicMock()
        self.mock_rate_limiter_instance.is_rate_limited.return_value = (False, 0)
        self.mock_rate_limiter.return_value = self.mock_rate_limiter_instance

    def tearDown(self):
        self.eth_service_patcher.stop()
        self.rate_limiter_patcher.stop()

    @override_settings(USE_TRANSACTION_QUEUE=False)
    def test_fund_valid_address(self):
        """Test funding with a valid Ethereum address"""
        response = self.client.post(
            self.url,
            data=json.dumps(self.valid_payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('transaction_hash', response.data)
        self.assertIn('wallet_address', response.data)
        self.assertIn('amount', response.data)

        # Verify the transaction was recorded
        self.assertEqual(Transaction.objects.count(), 1)
        transaction = Transaction.objects.first()
        self.assertEqual(transaction.status, 'success')
        self.assertEqual(transaction.wallet_address, self.valid_payload['wallet_address'])

    @override_settings(USE_TRANSACTION_QUEUE=True)
    def test_fund_with_queue(self):
        """Test funding with transaction queue enabled"""
        # Mock the transaction queue
        with patch('faucet.views.transaction_queue') as mock_queue:
            response = self.client.post(
                self.url,
                data=json.dumps(self.valid_payload),
                content_type='application/json'
            )

            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            self.assertIn('transaction_id', response.data)
            self.assertIn('status', response.data)
            self.assertEqual(response.data['status'], 'pending')

            # Verify the transaction was recorded
            self.assertEqual(Transaction.objects.count(), 1)
            transaction = Transaction.objects.first()
            self.assertEqual(transaction.status, 'pending')

            # Verify queue was called
            mock_queue.enqueue_transaction.assert_called_once()

    def test_fund_invalid_address(self):
        """Test funding with an invalid Ethereum address"""
        invalid_payload = {
            'wallet_address': 'not-a-valid-address'
        }

        response = self.client.post(
            self.url,
            data=json.dumps(invalid_payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_fund_rate_limited(self):
        """Test funding when rate limited"""
        # Configure mock to return rate limited
        self.mock_rate_limiter_instance.is_rate_limited.return_value = (True, 30)

        response = self.client.post(
            self.url,
            data=json.dumps(self.valid_payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn('error', response.data)

        # Verify a failed transaction was recorded
        self.assertEqual(Transaction.objects.count(), 1)
        transaction = Transaction.objects.first()
        self.assertEqual(transaction.status, 'failed')

    @override_settings(USE_TRANSACTION_QUEUE=False)
    def test_fund_ethereum_error(self):
        """Test funding when Ethereum service throws an error"""
        # Configure mock to raise an exception
        self.mock_eth_instance.send_transaction.side_effect = ValueError("Insufficient funds")

        response = self.client.post(
            self.url,
            data=json.dumps(self.valid_payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

        # Verify a failed transaction was recorded
        self.assertEqual(Transaction.objects.count(), 1)
        transaction = Transaction.objects.first()
        self.assertEqual(transaction.status, 'failed')


class StatsViewTests(TestCase):
    """Test cases for the StatsView API endpoint"""

    def setUp(self):
        self.client = APIClient()
        self.url = reverse('stats')

        # Create some test transactions
        Transaction.objects.create(
            wallet_address='0x742d35Cc6634C0532925a3b844Bc454e4438f44e',
            transaction_hash='0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef',
            status='success',
            ip_address='127.0.0.1',
            amount=0.0001
        )

        Transaction.objects.create(
            wallet_address='0x742d35Cc6634C0532925a3b844Bc454e4438f44e',
            status='failed',
            error_message='Insufficient funds',
            ip_address='127.0.0.1',
            amount=0.0001
        )

        Transaction.objects.create(
            wallet_address='0x742d35Cc6634C0532925a3b844Bc454e4438f44e',
            status='pending',
            ip_address='127.0.0.1',
            amount=0.0001
        )

        # Mock the transaction queue
        self.queue_patcher = patch('faucet.views.transaction_queue')
        self.mock_queue = self.queue_patcher.start()
        self.mock_queue.queue.qsize.return_value = 1

    def tearDown(self):
        self.queue_patcher.stop()

    def test_get_stats(self):
        """Test getting transaction statistics"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('successful_transactions', response.data)
        self.assertIn('failed_transactions', response.data)
        self.assertIn('pending_transactions', response.data)
        self.assertIn('queue_size', response.data)

        self.assertEqual(response.data['successful_transactions'], 1)
        self.assertEqual(response.data['failed_transactions'], 1)
        self.assertEqual(response.data['pending_transactions'], 1)
        self.assertEqual(response.data['queue_size'], 1)

    @patch('faucet.views.EthereumService')
    def test_get_stats_with_wallet_info(self, mock_eth_service):
        """Test getting statistics with wallet info"""
        # Configure the mock
        mock_instance = MagicMock()
        mock_instance.get_balance.return_value = 0.5
        mock_eth_service.return_value = mock_instance

        response = self.client.get(f"{self.url}?include_wallet_info=true")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('faucet_balance', response.data)
        self.assertEqual(response.data['faucet_balance'], 0.5)