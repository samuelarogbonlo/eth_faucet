# Configuration Options

The application can be configured through environment variables in the `.env` file:

## Django Settings

| Variable | Description | Default |
|----------|-------------|---------|
| DJANGO_SECRET_KEY | Secret key for Django | random string |
| DJANGO_DEBUG | Enable debug mode | False |
| DJANGO_ALLOWED_HOSTS | Comma-separated list of allowed hosts | localhost,127.0.0.1 |
| DJANGO_LOG_LEVEL | Logging level | INFO |

## Database Settings

| Variable | Description | Default |
|----------|-------------|---------|
| POSTGRES_DB | PostgreSQL database name | eth_faucet |
| POSTGRES_USER | PostgreSQL username | postgres |
| POSTGRES_PASSWORD | PostgreSQL password | postgres |
| POSTGRES_HOST | PostgreSQL host | db |
| POSTGRES_PORT | PostgreSQL port | 5432 |

## Redis Settings

| Variable | Description | Default |
|----------|-------------|---------|
| REDIS_HOST | Redis host | redis |
| REDIS_PORT | Redis port | 6379 |

## Ethereum Settings

| Variable | Description | Default |
|----------|-------------|---------|
| ETHEREUM_PROVIDER_URL | Primary Ethereum RPC URL | https://sepolia.infura.io/v3/... |
| ETHEREUM_FALLBACK_PROVIDERS | Comma-separated fallback RPC URLs | empty |
| ETHEREUM_PRIVATE_KEY | Private key for the faucet wallet | required |
| ETHEREUM_FROM_ADDRESS | Address of the faucet wallet | required |
| ETHEREUM_CHAIN_ID | Chain ID for Sepolia | 11155111 |
| ETHEREUM_MAX_RETRIES | Maximum retry attempts for RPC calls | 3 |
| ETHEREUM_RETRY_DELAY | Delay between retries in seconds | 1.0 |

## Faucet Settings

| Variable | Description | Default |
|----------|-------------|---------|
| FAUCET_AMOUNT | Amount of ETH to send per request | 0.0001 |
| RATE_LIMIT_TIMEOUT | Timeout in seconds between requests | 60 |
| USE_TRANSACTION_QUEUE | Use async queue for transactions | True |