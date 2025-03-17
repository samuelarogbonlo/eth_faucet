from django.apps import AppConfig


class FaucetConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'faucet'

    def ready(self):
        """
        Start the transaction queue worker when Django is ready.
        This ensures the worker is started when running with gunicorn.
        """
        from .services.transaction_queue import transaction_queue

        # Start the worker only if running with Django server, not during migrations or other commands
        import sys
        if 'runserver' in sys.argv or 'gunicorn' in sys.argv[0]:
            transaction_queue.start_worker()