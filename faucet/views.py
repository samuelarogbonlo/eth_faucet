import logging
from datetime import timedelta
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
from .models import Transaction
from .serializers import (
    WalletAddressSerializer,
    TransactionResponseSerializer,
    StatsResponseSerializer
)
from .services.ethereum import EthereumService
from .services.rate_limiter import RateLimiter
from .services.transaction_queue import transaction_queue

logger = logging.getLogger(__name__)


class FundView(APIView):
    """API View for sending Sepolia ETH from the faucet to a wallet"""

    def post(self, request):
        # Validate input data
        serializer = WalletAddressSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get client IP address
        ip_address = self.get_client_ip(request)
        wallet_address = serializer.validated_data['wallet_address']

        # Check rate limiting
        rate_limiter = RateLimiter()
        is_limited, remaining_time = rate_limiter.is_rate_limited(ip_address, wallet_address)

        if is_limited:
            error_msg = f"Rate limit exceeded. Please try again in {remaining_time} seconds."

            # Record failed transaction in database
            Transaction.objects.create(
                wallet_address=wallet_address,
                status='failed',
                error_message=error_msg,
                ip_address=ip_address
            )

            return Response(
                {"error": error_msg},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        # Initialize Ethereum service
        try:
            eth_service = EthereumService()
        except ConnectionError as e:
            error_msg = "Unable to connect to Ethereum network"

            # Record failed transaction in database
            Transaction.objects.create(
                wallet_address=wallet_address,
                status='failed',
                error_message=error_msg,
                ip_address=ip_address
            )

            return Response(
                {"error": error_msg},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        # Process transaction (either directly or via queue)
        try:
            # Use async queue if configured
            use_queue = getattr(settings, 'USE_TRANSACTION_QUEUE', True)

            if use_queue:
                # Record the request for rate limiting
                rate_limiter.record_request(ip_address, wallet_address)

                # Create pending transaction in database
                transaction = Transaction.objects.create(
                    wallet_address=wallet_address,
                    status='pending',
                    ip_address=ip_address,
                    amount=eth_service.amount
                )

                # Add transaction to the processing queue
                transaction_queue.enqueue_transaction(
                    transaction.id,
                    wallet_address,
                    ip_address
                )

                # Return accepted response
                response_data = {
                    "transaction_id": transaction.id,
                    "wallet_address": wallet_address,
                    "amount": eth_service.amount,
                    "status": "pending",
                    "message": "Transaction submitted for processing"
                }

                return Response(response_data, status=status.HTTP_202_ACCEPTED)

            else:
                # Process immediately (synchronous mode)
                tx_hash = eth_service.send_transaction(wallet_address)

                # Record the request for rate limiting
                rate_limiter.record_request(ip_address, wallet_address)

                # Record successful transaction in database
                transaction = Transaction.objects.create(
                    wallet_address=wallet_address,
                    transaction_hash=tx_hash,
                    status='success',
                    ip_address=ip_address,
                    amount=eth_service.amount
                )

                # Return success response
                response_data = {
                    "transaction_hash": tx_hash,
                    "transaction_id": transaction.id,
                    "wallet_address": wallet_address,
                    "amount": eth_service.amount,
                    "status": "success"
                }

                return Response(response_data, status=status.HTTP_200_OK)

        except ValueError as e:
            # Handle validation errors
            error_msg = str(e)

            # Record failed transaction in database
            Transaction.objects.create(
                wallet_address=wallet_address,
                status='failed',
                error_message=error_msg,
                ip_address=ip_address
            )

            return Response(
                {"error": error_msg},
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            # Handle other errors
            error_msg = f"Transaction failed: {str(e)}"
            logger.error(f"Error processing transaction: {str(e)}")

            # Record failed transaction in database
            Transaction.objects.create(
                wallet_address=wallet_address,
                status='failed',
                error_message=error_msg,
                ip_address=ip_address
            )

            return Response(
                {"error": error_msg},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_client_ip(self, request):
        """Extract client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # In case of multiple proxies, the real IP is the first one
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class StatsView(APIView):
    """API View for returning faucet statistics"""

    def get(self, request):
        # Calculate the time 24 hours ago
        time_threshold = timezone.now() - timedelta(hours=24)

        # Query the database for transactions in the last 24 hours
        successful_count = Transaction.objects.filter(
            created_at__gte=time_threshold,
            status='success'
        ).count()

        failed_count = Transaction.objects.filter(
            created_at__gte=time_threshold,
            status='failed'
        ).count()

        pending_count = Transaction.objects.filter(
            created_at__gte=time_threshold,
            status='pending'
        ).count()

        # Get queue size
        current_queue_size = transaction_queue.queue.qsize()

        # Prepare response data
        response_data = {
            "successful_transactions": successful_count,
            "failed_transactions": failed_count,
            "pending_transactions": pending_count,
            "queue_size": current_queue_size,
            "time_period": "24 hours"
        }

        # Add faucet wallet info if requested
        if request.query_params.get('include_wallet_info', '').lower() == 'true':
            try:
                eth_service = EthereumService()
                balance = eth_service.get_balance()
                response_data["faucet_balance"] = float(balance)
            except Exception as e:
                logger.error(f"Error getting faucet balance: {str(e)}")

        return Response(response_data, status=status.HTTP_200_OK)