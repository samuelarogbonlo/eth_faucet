from rest_framework import serializers
from .models import Transaction


class WalletAddressSerializer(serializers.Serializer):
    """Serializer for wallet address input"""
    wallet_address = serializers.CharField(max_length=42)

    def validate_wallet_address(self, value):
        """Validate the wallet address format"""
        # Basic Ethereum address validation
        if not value.startswith('0x') or len(value) != 42:
            raise serializers.ValidationError("Invalid Ethereum wallet address format")

        # Additional validation could be added here

        return value


class TransactionResponseSerializer(serializers.Serializer):
    """Serializer for transaction response"""
    transaction_hash = serializers.CharField(max_length=66, required=False)
    transaction_id = serializers.IntegerField()
    wallet_address = serializers.CharField(max_length=42)
    amount = serializers.DecimalField(max_digits=18, decimal_places=10)
    status = serializers.CharField(max_length=10)


class StatsResponseSerializer(serializers.Serializer):
    """Serializer for stats response"""
    successful_transactions = serializers.IntegerField()
    failed_transactions = serializers.IntegerField()
    pending_transactions = serializers.IntegerField(required=False)
    queue_size = serializers.IntegerField(required=False)
    time_period = serializers.CharField(required=False)
    faucet_balance = serializers.FloatField(required=False)