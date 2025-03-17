# Sepolia ETH Faucet

A Django REST API application that allows users to receive Sepolia ETH for free. This faucet application is designed to be robust, scalable, and production-ready.

## Features

- **Send Sepolia ETH** to specified wallet addresses
- **Rate limiting** by IP address and wallet address
- **Asynchronous transaction processing** to handle high demand
- **Comprehensive error handling** and retry mechanisms
- **Fallback RPC providers** for improved reliability
- **Detailed statistics** on faucet usage
- **Fully dockerized** with environment variable configuration
- **Complete test coverage** for all components

## Architecture

The application follows a modular architecture with the following components:

- **API Layer**: Django REST Framework views and serializers
- **Service Layer**: Dedicated services for Ethereum interactions, rate limiting, and transaction queue
- **Data Layer**: Django models for transaction tracking
- **Infrastructure**: Docker configuration for deployment

## Requirements

- Docker and Docker Compose
- A funded Sepolia ETH wallet
- Access to Sepolia RPC endpoints (e.g., Infura, Alchemy)

## Quick Start

1. **Clone the repository**

2. **Create a .env file from the example**
   ```bash
   cp .env.example .env
   ```

3. **Configure your Ethereum credentials**
   - Edit the `.env` file with your Sepolia wallet private key and RPC URLs

4. **Build and run the application**
   ```bash
   docker-compose up -d
   ```

5. **Check if the services are running**
   ```bash
   docker-compose ps
   ```

## Usage Examples

### Request ETH

```bash
curl -X POST http://localhost:8000/faucet/fund/ \
  -H "Content-Type: application/json" \
  -d '{"wallet_address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"}'
```

### Get Statistics

```bash
curl http://localhost:8000/faucet/stats/
```

For more detailed API documentation, see [API_DOCUMENTATION.md](API_DOCUMENTATION.md).

## Configuration Options

The application can be configured through environment variables in the `.env` file:

### Django Settings

| Variable | Description | Default |
|----------|-------------|---------|
| DJANGO_SECRET_KEY | Secret key for Django | random string |
| DJANGO_DEBUG | Enable debug mode | False |
| DJANGO_ALLOWED_HOSTS | Comma-separated list of allowed hosts | localhost,127.0.0.1 |
| DJANGO_LOG_LEVEL | Logging level | INFO |

### Database Settings

| Variable | Description | Default |
|----------|-------------|---------|
| POSTGRES_DB | PostgreSQL database name | eth_faucet |
| POSTGRES_USER | PostgreSQL username | postgres |
| POSTGRES_PASSWORD | PostgreSQL password | postgres |
| POSTGRES_HOST | PostgreSQL host | db |
| POSTGRES_PORT | PostgreSQL port | 5432 |

### Redis Settings

| Variable | Description | Default |
|----------|-------------|---------|
| REDIS_HOST | Redis host | redis |
| REDIS_PORT | Redis port | 6379 |

### Ethereum Settings

| Variable | Description | Default |
|----------|-------------|---------|
| ETHEREUM_PROVIDER_URL | Primary Ethereum RPC URL | https://sepolia.infura.io/v3/... |
| ETHEREUM_FALLBACK_PROVIDERS | Comma-separated fallback RPC URLs | empty |
| ETHEREUM_PRIVATE_KEY | Private key for the faucet wallet | required |
| ETHEREUM_FROM_ADDRESS | Address of the faucet wallet | required |
| ETHEREUM_CHAIN_ID | Chain ID for Sepolia | 11155111 |
| ETHEREUM_MAX_RETRIES | Maximum retry attempts for RPC calls | 3 |
| ETHEREUM_RETRY_DELAY | Delay between retries in seconds | 1.0 |

### Faucet Settings

| Variable | Description | Default |
|----------|-------------|---------|
| FAUCET_AMOUNT | Amount of ETH to send per request | 0.0001 |
| RATE_LIMIT_TIMEOUT | Timeout in seconds between requests | 60 |
| USE_TRANSACTION_QUEUE | Use async queue for transactions | True |

## Development

### Running Tests

```bash
docker-compose exec web python manage.py test
```

### Accessing Admin Interface

1. Create a superuser:
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

2. Access the admin interface at `http://localhost:8000/admin/`

## Troubleshooting

### Common Issues

1. **Connection to Ethereum Network**
   - Check your RPC URL and network connectivity
   - Verify the chain ID is correct for Sepolia (11155111)

2. **Insufficient Funds**
   - Ensure your faucet wallet has enough Sepolia ETH
   - Get more Sepolia ETH from a public faucet

3. **Rate Limiting Problems**
   - Adjust the `RATE_LIMIT_TIMEOUT` if needed
   - Check Redis connection for rate limiting storage

### Logs

To view logs from the application:

```bash
docker-compose logs -f web
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.