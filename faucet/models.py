from django.db import models


class Transaction(models.Model):
    """Model to track all faucet transactions (successful and failed)"""

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    )

    wallet_address = models.CharField(max_length=42)  # Ethereum addresses are 42 chars (with '0x')
    transaction_hash = models.CharField(max_length=66, null=True, blank=True)  # Tx hashes are 66 chars (with '0x')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    amount = models.DecimalField(max_digits=18, decimal_places=10, default=0.0001)  # ETH amount with precision
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    retry_count = models.IntegerField(default=0)  # Track retry attempts for failed transactions
    priority = models.IntegerField(default=0)  # Lower numbers = higher priority

    def __str__(self):
        return f"{self.wallet_address} - {self.status} - {self.created_at}"

    class Meta:
        indexes = [
            models.Index(fields=['wallet_address']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['updated_at']),
            models.Index(fields=['priority']),  # For priority-based processing
        ]