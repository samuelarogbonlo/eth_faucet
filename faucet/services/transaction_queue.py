import time
import threading
import logging
import queue
from django.utils import timezone
from faucet.models import Transaction
from .ethereum import EthereumService

logger = logging.getLogger(__name__)

class TransactionQueue:
    """
    Queue system for processing Ethereum transactions asynchronously
    Helps with scalability under high demand by processing transactions in the background
    """
    def __init__(self):
        self.queue = queue.PriorityQueue()
        self.worker_thread = None
        self.is_running = False
        self.eth_service = None  # Will be initialized when processing starts

    def start_worker(self):
        """Start the background worker thread if not already running"""
        if self.worker_thread is None or not self.worker_thread.is_alive():
            self.is_running = True
            self.worker_thread = threading.Thread(target=self._process_queue)
            self.worker_thread.daemon = True  # Thread will exit when main program exits
            self.worker_thread.start()
            logger.info("Transaction queue worker started")

    def stop_worker(self):
        """Signal the worker thread to stop"""
        self.is_running = False
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5.0)
            logger.info("Transaction queue worker stopped")

    def enqueue_transaction(self, transaction_id, wallet_address, ip_address, priority=0):
        """
        Add a transaction to the processing queue
        Lower priority values are processed first (0 is default priority)
        """
        # Priority queue sorts by first item in tuple
        self.queue.put((priority, {
            'id': transaction_id,
            'wallet_address': wallet_address,
            'ip_address': ip_address,
            'enqueued_at': timezone.now(),
        }))
        logger.info(f"Transaction {transaction_id} enqueued with priority {priority}")

        # Ensure worker is running
        self.start_worker()

        return True

    def _process_queue(self):
        """Worker thread function to process queued transactions"""
        # Initialize Ethereum service for this thread
        try:
            self.eth_service = EthereumService()
        except Exception as e:
            logger.error(f"Failed to initialize Ethereum service in queue worker: {str(e)}")
            self.is_running = False
            return

        while self.is_running:
            try:
                # Get the next transaction from the queue with a timeout
                # This allows the thread to check is_running periodically
                try:
                    priority, tx_data = self.queue.get(timeout=5.0)
                except queue.Empty:
                    continue

                transaction_id = tx_data['id']
                wallet_address = tx_data['wallet_address']

                logger.info(f"Processing queued transaction {transaction_id} to {wallet_address}")

                try:
                    # Get the transaction from the database
                    transaction = Transaction.objects.get(id=transaction_id)

                    # Only process if it's still pending (not already processed by another worker)
                    if transaction.status == 'pending':
                        # Send the transaction
                        tx_hash = self.eth_service.send_transaction(wallet_address)

                        # Update the transaction record
                        transaction.status = 'success'
                        transaction.transaction_hash = tx_hash
                        transaction.save()

                        logger.info(f"Transaction {transaction_id} completed successfully: {tx_hash}")
                    else:
                        logger.info(f"Transaction {transaction_id} already processed, skipping")

                except Transaction.DoesNotExist:
                    logger.error(f"Transaction {transaction_id} not found in database")

                except Exception as e:
                    try:
                        # Get the transaction from the database
                        transaction = Transaction.objects.get(id=transaction_id)

                        # Mark as failed with error message
                        transaction.status = 'failed'
                        transaction.error_message = str(e)
                        transaction.save()

                        logger.error(f"Failed to process transaction {transaction_id}: {str(e)}")

                        # Re-queue with higher priority if it's a recoverable error (e.g., RPC issues)
                        if "connection" in str(e).lower() or "timeout" in str(e).lower():
                            # Wait a bit before retrying
                            time.sleep(5.0)
                            if transaction.retry_count < 3:  # Limit retries
                                transaction.retry_count += 1
                                transaction.status = 'pending'
                                transaction.save()

                                # Higher priority for retry (negative number = higher priority)
                                retry_priority = -1
                                self.enqueue_transaction(
                                    transaction_id,
                                    wallet_address,
                                    tx_data['ip_address'],
                                    priority=retry_priority
                                )
                                logger.info(f"Re-queued transaction {transaction_id} with priority {retry_priority}")

                    except Exception as inner_e:
                        logger.error(f"Error handling transaction failure: {str(inner_e)}")

                finally:
                    # Mark the task as done
                    self.queue.task_done()

            except Exception as e:
                logger.error(f"Error in transaction queue worker: {str(e)}")
                # Sleep briefly to avoid tight error loops
                time.sleep(1.0)

        logger.info("Transaction queue worker exiting")

# Singleton instance
transaction_queue = TransactionQueue()