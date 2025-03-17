# Sepolia ETH Faucet API Documentation

This document provides detailed information about the Sepolia ETH Faucet API endpoints, request/response formats, and usage examples.

## Base URL

All API endpoints are relative to the base URL: `http://[your-host]:[port]/faucet/`

## Authentication

The API does not require authentication but has rate limiting mechanisms in place.

## Rate Limiting

The API implements rate limiting based on:
- Source IP address
- Destination wallet address

Users cannot request funds more than once per configurable timeout (default: 60 seconds) from the same IP address or to the same wallet address.

## Endpoints

### Fund a Wallet

Request Sepolia ETH to be sent to a specified wallet address.

- **URL**: `/fund/`
- **Method**: `POST`
- **Content-Type**: `application/json`

#### Request Body

```json
{
  "wallet_address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
}
```

| Field | Type | Description |
|-------|------|-------------|
| wallet_address | string | A valid Ethereum wallet address (42 characters, starts with '0x') |

#### Synchronous Response (when `USE_TRANSACTION_QUEUE=False`)

**Success Response (200 OK)**

```json
{
  "transaction_hash": "0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
  "transaction_id": 12345,
  "wallet_address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
  "amount": 0.0001,
  "status": "success"
}
```

#### Asynchronous Response (when `USE_TRANSACTION_QUEUE=True`)

**Accepted Response (202 Accepted)**

```json
{
  "transaction_id": 12345,
  "wallet_address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
  "amount": 0.0001,
  "status": "pending",
  "message": "Transaction submitted for processing"
}
```

#### Error Responses

**Invalid Input (400 Bad Request)**

```json
{
  "error": "Invalid Ethereum wallet address format"
}
```

**Rate Limited (429 Too Many Requests)**

```json
{
  "error": "Rate limit exceeded. Please try again in 45 seconds."
}
```

**Insufficient Funds (400 Bad Request)**

```json
{
  "error": "Insufficient funds in faucet wallet: 0.00005 ETH"
}
```

**Service Unavailable (503 Service Unavailable)**

```json
{
  "error": "Unable to connect to Ethereum network"
}
```

#### cURL Example

```bash
curl -X POST http://localhost:8000/faucet/fund/ \
  -H "Content-Type: application/json" \
  -d '{"wallet_address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"}'
```

### Get Statistics

Retrieve faucet usage statistics for the past 24 hours.

- **URL**: `/stats/`
- **Method**: `GET`

#### Optional Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| include_wallet_info | boolean | Set to 'true' to include faucet wallet balance information |

#### Response

**Success Response (200 OK)**

```json
{
  "successful_transactions": 150,
  "failed_transactions": 25,
  "pending_transactions": 5,
  "queue_size": 2,
  "time_period": "24 hours"
}
```

With wallet info:

```json
{
  "successful_transactions": 150,
  "failed_transactions": 25,
  "pending_transactions": 5,
  "queue_size": 2,
  "time_period": "24 hours",
  "faucet_balance": 0.523
}
```

#### cURL Example

```bash
curl http://localhost:8000/faucet/stats/
```

With wallet info:

```bash
curl "http://localhost:8000/faucet/stats/?include_wallet_info=true"
```

## Error Handling

The API handles various error conditions:

1. **Invalid input**: When the wallet address is invalid or missing
2. **Rate limiting**: When requests exceed the configured rate limit
3. **Network errors**: When there are issues connecting to the Ethereum network
4. **Insufficient funds**: When the faucet wallet doesn't have enough ETH

All error responses follow a consistent format:

```json
{
  "error": "Description of the error"
}
```

## Configuration

The API behavior can be modified through environment variables:

| Environment Variable | Description | Default |
|----------------------|-------------|---------|
| RATE_LIMIT_TIMEOUT | Timeout in seconds between requests from same IP/wallet | 60 |
| FAUCET_AMOUNT | Amount of ETH to send per request | 0.0001 |
| USE_TRANSACTION_QUEUE | Whether to use async queue for processing | True |
| ETHEREUM_MAX_RETRIES | Maximum retry attempts for failed transactions | 3 |
| ETHEREUM_RETRY_DELAY | Delay between retries in seconds | 1.0 |
