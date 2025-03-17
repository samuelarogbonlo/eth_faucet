from django.contrib import admin
from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Admin configuration for Transaction model"""
    list_display = ('wallet_address', 'status', 'amount', 'created_at', 'ip_address')
    list_filter = ('status', 'created_at')
    search_fields = ('wallet_address', 'transaction_hash', 'ip_address')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('wallet_address', 'transaction_hash', 'status', 'amount')
        }),
        ('Details', {
            'fields': ('ip_address', 'error_message', 'retry_count', 'priority')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )