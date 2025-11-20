# Hedera Logger API

A simple API server for logging messages to Hedera Consensus Service (HCS).

## Setup

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Configure environment variables:**
   - Copy `.env.example` to `.env`
   - Fill in your Hedera credentials:
   ```
   HEDERA_ACCOUNT_ID=your_account_id
   HEDERA_PRIVATE_KEY=your_private_key
   HEDERA_TOPIC_ID=your_topic_id
   ```

3. **Create a Hedera topic (if you don't have one):**
   ```bash
   npm run create-topic
   ```

4. **Run the development server:**
   ```bash
   npm run dev
   ```

The server will start on `http://localhost:3001`

## API Endpoints

### POST /api/log
Send a message to be logged to Hedera Consensus Service.

**Request:**
```json
{
  "log_message": "Your message here"
}
```

**Response:**
```json
{
  "status": "success",
  "sequenceNumber": "12345"
}
```

### GET /health
Health check endpoint.

## Integration with Aave Concierge API

The Aave Concierge API is configured to automatically log actions (supply, borrow, repay, simulate) to this Hedera Logger API. Make sure both services are running locally for testing.

1. Start the Hedera Logger API: `npm run dev` (runs on port 3001)
2. Start the Aave Concierge API (it will automatically send logs to the logger)