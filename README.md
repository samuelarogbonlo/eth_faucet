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

```bash
# Setup, build and start the application (creates .env file, builds containers, starts services)
make all

# View application logs
make logs

# Run tests
make test
```

Run `make help` to see all available commands.

## Usage Examples

### Request ETH

```bash
curl -X POST http://localhost:8000/faucet/fund/ \
  -H "Content-Type: application/json" \
  -d '{"wallet_address": "0x********"}'
```

### Get Statistics

```bash
curl http://localhost:8000/faucet/stats/
```

For more detailed API documentation, see [API_DOCUMENTATION.md](API_DOCUMENTATION.md).

For configuration options, see [CONFIG.md](CONFIG.md).

## Development

### Accessing Admin Interface

```bash
# Create a superuser
make superuser

# Access the admin interface at http://localhost:8000/admin/
```

## Future Enhancements

The current implementation satisfies all core requirements. For future development, we could consider the following:

- **Simple Frontend Interface**: Add a better web UI for users to request ETH without direct API interaction
- **Webhook Notifications**: Implement a webhook system to notify applications about transaction status changes
- **Metrics and Monitoring**: Add Prometheus metrics for monitoring faucet usage, performance, and wallet balance
- **Multiple Testnet Support**: Extend functionality to other Ethereum testnets beyond Sepolia
- **Enhanced Rate Limiting**: Implement more sophisticated anti-abuse mechanisms (e.g., captcha integration)
- **Admin Dashboard**: Create a management interface for monitoring transactions and faucet balance

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

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome!