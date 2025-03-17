import os
import logging
import time
from decimal import Decimal
from web3 import Web3
from web3.middleware import geth_poa_middleware
from web3.exceptions import Web3Exception
from django.conf import settings

logger = logging.getLogger(__name__)

class EthereumService:
    """Service for interacting with Ethereum blockchain (Sepolia testnet)"""

    def __init__(self):
        # Get configuration from environment variables or settings
        self.primary_provider_url = settings.ETHEREUM_PROVIDER_URL
        self.fallback_provider_urls = settings.ETHEREUM_FALLBACK_PROVIDERS.split(',') if settings.ETHEREUM_FALLBACK_PROVIDERS else []
        self.private_key = settings.ETHEREUM_PRIVATE_KEY
        self.from_address = settings.ETHEREUM_FROM_ADDRESS
        self.chain_id = settings.ETHEREUM_CHAIN_ID  # Sepolia chain ID is 11155111
        self.amount = Decimal(settings.FAUCET_AMOUNT)  # Default 0.0001 ETH
        self.max_retries = settings.ETHEREUM_MAX_RETRIES
        self.retry_delay = settings.ETHEREUM_RETRY_DELAY

        # Initialize Web3 connection with primary provider
        self.w3 = self._initialize_web3(self.primary_provider_url)

        # Validate connection, try fallbacks if primary fails
        if not self._ensure_connection():
            logger.error("Failed to connect to any Ethereum node")
            raise ConnectionError("Failed to connect to any Ethereum node")

    def _initialize_web3(self, provider_url):
        """Initialize Web3 connection with given provider URL"""
        w3 = Web3(Web3.HTTPProvider(provider_url))

        # Inject middleware for Sepolia (PoA network)
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)

        return w3

    def _ensure_connection(self):
        """Ensure connection to an Ethereum node, try fallbacks if needed"""
        # First try primary provider
        if self.w3.is_connected():
            logger.info(f"Connected to primary Ethereum node at {self.primary_provider_url}")
            return True

        # If primary fails, try fallbacks
        for provider_url in self.fallback_provider_urls:
            logger.warning(f"Trying fallback Ethereum node at {provider_url}")
            self.w3 = self._initialize_web3(provider_url)
            if self.w3.is_connected():
                logger.info(f"Connected to fallback Ethereum node at {provider_url}")
                return True

        return False

    def validate_address(self, address):
        """Validate if the provided address is a valid Ethereum address"""
        return self.w3.is_address(address)

    def get_balance(self):
        """Get the balance of the faucet wallet"""
        for attempt in range(self.max_retries):
            try:
                balance_wei = self.w3.eth.get_balance(self.from_address)
                balance_eth = self.w3.from_wei(balance_wei, 'ether')
                return balance_eth
            except Web3Exception as e:
                logger.warning(f"Error getting balance (attempt {attempt+1}/{self.max_retries}): {str(e)}")
                if attempt < self.max_retries - 1:
                    # Try to reconnect
                    self._ensure_connection()
                    time.sleep(self.retry_delay)
                else:
                    raise

    def send_transaction(self, to_address):
        """Send ETH from the faucet wallet to the specified address"""
        try:
            # Validate address format
            if not self.validate_address(to_address):
                raise ValueError("Invalid Ethereum address format")

            # Check faucet balance
            balance = self.get_balance()
            if balance < self.amount:
                raise ValueError(f"Insufficient funds in faucet wallet: {balance} ETH")

            # Convert amount to Wei
            amount_wei = self.w3.to_wei(self.amount, 'ether')

            # Try multiple times with exponential backoff
            for attempt in range(self.max_retries):
                try:
                    # Get the nonce for the transaction
                    nonce = self.w3.eth.get_transaction_count(self.from_address)

                    # Estimate gas price (with flexibility for network congestion)
                    gas_price = self.w3.eth.gas_price
                    # Increase gas price slightly for faster confirmation when doing retries
                    if attempt > 0:
                        gas_price = int(gas_price * (1 + 0.1 * attempt))  # Increase by 10% per retry

                    # Build transaction
                    tx = {
                        'nonce': nonce,
                        'to': to_address,
                        'value': amount_wei,
                        'gas': 21000,  # Standard gas limit for ETH transfers
                        'gasPrice': gas_price,
                        'chainId': self.chain_id
                    }

                    # Sign the transaction
                    signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)

                    # Send the transaction
                    tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)

                    # Return the transaction hash as a hex string
                    return self.w3.to_hex(tx_hash)

                except Web3Exception as e:
                    logger.warning(f"Error sending transaction (attempt {attempt+1}/{self.max_retries}): {str(e)}")
                    if attempt < self.max_retries - 1:
                        # Try to reconnect before retrying
                        self._ensure_connection()
                        # Exponential backoff
                        wait_time = self.retry_delay * (2 ** attempt)
                        logger.info(f"Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        raise

        except Exception as e:
            logger.error(f"Error sending transaction to {to_address}: {str(e)}")
            raise