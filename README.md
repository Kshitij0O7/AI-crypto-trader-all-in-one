# AI Trading Bot for Polymarket - Simulation Mode

An autonomous cryptocurrency trading bot that uses AI (GPT-4o or Claude) to make trading decisions on Polymarket prediction markets. The bot operates in **simulation mode** - it tracks positions and calculates PnL without executing actual blockchain transactions.

## Features

- **Simulation Mode**: No actual transactions - records buy/sell prices and calculates PnL
- **AI-powered decision making** using GPT-4o or Claude Sonnet
- **Polymarket Integration**: Trades on Polymarket prediction markets via Polygon network
- **Odds Interpretation**: Understands that prices represent prediction odds (0-1 probability)
- **Asset ID Tracking**: Tracks specific prediction tokens (e.g., YES token IDs for questions)
- **Liquidity Analysis**: Monitors OrdersMatched events to track liquidity provision activity
- **Automated position management** (buy, hold, sell)
- **Portfolio tracking** with PnL calculations every 5 minutes
- **Excel Logging**: Comprehensive logging to Excel files for analysis

## Architecture

The bot operates in continuous cycles, performing the following steps:

1. Fetches trade data from Polymarket (via Bitquery)
2. Analyzes OrdersMatched events to detect liquidity provision activity
3. Sends market data to AI for analysis and decision making
4. Records AI-recommended trades (simulated - no actual transactions)
5. Manages open positions and risk limits
6. Calculates and logs PnL every 5 minutes
7. Tracks portfolio performance and success metrics
8. Exports all data to Excel files for analysis

## Key Concepts

### Polymarket Trading
- **Prices = Odds**: The `PriceInUSD` field represents the probability (0-1) that a prediction will be true
  - Example: `price=0.75` means 75% probability the prediction is true
  - Example: `price=0.25` means 25% probability (75% probability it's false)
- **Asset IDs**: Each prediction token has a unique asset ID (e.g., YES token ID for a specific question)
- **OrdersMatched Events**: Show liquidity provision activity on Polymarket's order book

### Simulation Mode
- **No Blockchain Transactions**: All trades are simulated and recorded
- **Position Tracking**: Records entry/exit prices and calculates PnL
- **PnL Reports**: Generated every 5 minutes and on program exit
- **Excel Logs**: All trading activity is logged to Excel files in the `logs/` directory

## Safety Features

- Portfolio value limit: $10.00 (configurable)
- Maximum position size: $1.00 (configurable)
- Daily loss limit: $2.00 (configurable)
- Minimum confidence threshold: 30% (configurable, lowered for testing)
- Maximum open positions: 2 (configurable)
- Automatic position closure on stop-loss or target

## Requirements

- Python 3.8+
- [BitQuery Access Token](https://account.bitquery.io/user/api_v2/access_tokens/?utm_source=github&utm_medium=readme&utm_campaign=polymarket_openAI_bot) for market and liquidity data
- OpenAI API key or Anthropic API key
- **No wallet or RPC required** (simulation mode)

> 📚 **API Documentation**: For detailed information on Polymarket APIs, queries, and data structures, see the [Bitquery Polymarket API Documentation](https://docs.bitquery.io/docs/examples/polymarket-api/?utm_source=github&utm_medium=readme&utm_campaign=polymarket_openAI_bot)

## Installation

1. Clone the repository
```bash
git clone https://github.com/Kshitij0O7/AI-crypto-trader-all-in-one
cd AI-crypto-trader-all-in-one
```

2. Install dependencies
```bash
pip3 install -r requirements.txt
```

3. Get API Keys
- **BitQuery**: Create an API key at https://account.bitquery.io/user/api_v2/access_tokens
- **OpenAI**: Get your API key from https://platform.openai.com/api-keys
- **Anthropic** (optional): Get from https://console.anthropic.com/

4. Configure environment variables
Copy `.env_example` to `.env` and fill in your values:
```
# AI Provider API Keys (at least one required)
OPENAI_API_KEY=sk-proj-your_openai_key_here
ANTHROPIC_API_KEY=sk-ant-your_anthropic_key_here

# Market Data API
BITQUERY_API_KEY=ory_at_your_bitquery_key_here

# Portfolio and Risk Management
PORTFOLIO_SIZE_USD=10
MAX_POSITION_SIZE_USD=1.5
DAILY_LOSS_LIMIT_USD=3
MAX_OPEN_POSITIONS=2
MIN_CONFIDENCE_THRESHOLD=30
```

## Usage

Run the bot with:
```bash
python3 main.py
```

The bot will:
- Load environment variables and validate configuration
- Initialize in simulation mode (no wallet connection needed)
- Display safety limits and configuration
- Start the trading loop with 60-second intervals
- Calculate and display PnL every 5 minutes
- Log all activity to Excel files in the `logs/` directory

## Configuration

Key settings can be configured via environment variables:

- **BITQUERY_API_KEY**: Required for fetching Polymarket trade and liquidity data
- **AI provider**: Supports OpenAI (GPT-4o) or Anthropic (Claude)
- **PORTFOLIO_SIZE_USD**: Maximum portfolio value in USD (default: 10)
- **MAX_POSITION_SIZE_USD**: Maximum size per position in USD (default: 1.5)
- **DAILY_LOSS_LIMIT_USD**: Maximum daily loss before stopping (default: 3)
- **MAX_OPEN_POSITIONS**: Maximum number of concurrent positions (default: 2)
- **MIN_CONFIDENCE_THRESHOLD**: Minimum AI confidence % to execute trades (default: 30)

**Note**: RPC_URL, CHAIN_ID, and PRIVATE_KEY are not required for simulation mode.

## Trading Logic

The AI analyzes multiple data sources:
- **Trade Data**: Recent Polymarket trades with volumes and prices (odds)
- **Asset IDs**: Unique identifiers for prediction tokens
- **OrdersMatched Events**: Liquidity provision activity on the order book
  - `takerAssetId`: Asset ID being traded
  - `takerAmountFilled`: Amount trader wants to buy
  - `makerAmountFilled`: Amount liquidity provider can provide
- **Buy vs sell pressure**: Volume analysis
- **Market confidence**: Interprets prices as odds/probabilities

Based on this analysis, the AI generates trading actions with:
- Confidence level (0-100%)
- Reasoning for the decision
- Entry price (odds) and position size
- Target price (odds) for profit taking
- Stop loss price (odds) for risk management
- Asset ID for tracking specific predictions

## Performance Tracking

The bot tracks:
- Number of open positions
- Daily PnL (Profit and Loss) - realized and unrealized
- AI success rate
- Individual trade outcomes
- PnL calculated every 5 minutes
- All data exported to Excel files

## Excel Logging

All trading activity is automatically logged to Excel files in the `logs/` directory:

- **open_positions_YYYYMMDD.xlsx**: Open positions with current PnL
- **closed_positions_YYYYMMDD.xlsx**: Closed positions with final PnL
- **pnl_reports_YYYYMMDD.xlsx**: Periodic PnL snapshots (every 5 minutes)
- **signal_history_YYYYMMDD.xlsx**: AI decision history
- **trading_summary_YYYYMMDD.xlsx**: Complete summary with all metrics

Each log file includes:
- Timestamps
- Market symbols
- **Asset IDs** (for tracking specific predictions)
- Entry/exit prices (odds)
- PnL calculations
- AI confidence and reasoning

## Example Output

```
🤖 AI Trading Bot V2 - SIMULATION MODE
============================================================
⚠️  SIMULATION MODE: No actual transactions will be executed
============================================================
✨ Features:
   • Trade simulation (records buy/sell prices)
   • PnL calculation every 5 minutes
   • Liquidity flow analysis (smart money tracking)
   • Enhanced AI prompting (better context)
   • Performance tracking (AI learns from results)
============================================================

✅ AI Trading Bot V2 Initialized - SIMULATION MODE
📍 Wallet: 0x0000000000000000000000000000000000000000
⛓️  Chain ID: 137 (Polygon/Matic)
⚠️  SIMULATION MODE: No actual transactions will be executed

🚀 Starting AI Trading Bot V2 - SIMULATION MODE (interval: 60s)
============================================================
⚠️  SIMULATION MODE: No actual transactions will be executed
============================================================

📊 Cycle 1 - 2026-02-02 12:00:00
============================================================
📡 Fetching trade data...
💧 Fetching liquidity events...

🤖 Asking AI to analyze markets and decide actions...
✨ AI generated 1 action(s)

🤖 AI Action: BUY MARKET_SYMBOL
   Confidence: 45%
   Reasoning: Found opportunity based on [analysis]
   💱 Simulating BUY trade
   📊 Entry Price: $0.65
   ✅ Position recorded (SIMULATED)

📈 Portfolio Status:
   Open Positions: 1/2
   Daily PnL (Realized): $0.00
   AI Success Rate: 0.0%

============================================================
📊 PnL Report - 2026-02-02 12:05:00
============================================================
Total Open Positions: 1
Total Unrealized PnL: $0.15
Daily PnL (Realized + Unrealized): $0.15
...
```

## Risk Disclaimer

This bot operates in **simulation mode** - no actual transactions are executed:
- All trades are simulated and tracked for analysis
- No real cryptocurrency is traded
- PnL calculations are based on recorded prices
- Use this for testing and learning trading strategies
- Results may differ from actual trading due to execution delays and slippage

## Technical Details

- **Blockchain**: Polygon (Matic) Network (Chain ID: 137)
- **Market**: Polymarket Prediction Markets
- **Data Source**: [Bitquery GraphQL API](https://docs.bitquery.io/docs/examples/polymarket-api/?utm_source=github&utm_medium=readme&utm_campaign=polymarket_openAI_bot)
- **Liquidity Events**: OrdersMatched events from Polymarket order book contract
- **Order Book Contract**: `0xC5d563A36AE78145C45a50134d48A1215220f80a` (CTF Exchange)
- **Simulation Mode**: No Web3 transactions, all trades are recorded only

For detailed information on Polymarket contract addresses, events, and query examples, see the [Bitquery Polymarket API Documentation](https://docs.bitquery.io/docs/examples/polymarket-api/?utm_source=github&utm_medium=readme&utm_campaign=polymarket_openAI_bot).

## Data Structure

### Trade Data
- `symbol`: Market symbol
- `recent_price`: Current odds (0-1 probability)
- `asset_id`: Unique asset token ID
- `volume`: Trading volume
- `buy_volume` / `sell_volume`: Buy/sell pressure

### Liquidity Events (OrdersMatched)
- `takerAssetId`: Asset ID being traded
- `takerOrderMaker`: Trader address
- `takerAmountFilled`: Amount trader wants to buy
- `makerAmountFilled`: Amount liquidity provider can provide

## License

MIT License

## Contributing

Contributions welcome. Please test thoroughly before submitting pull requests.

## Additional Resources

- **[Bitquery Polymarket API Documentation](https://docs.bitquery.io/docs/examples/polymarket-api/?utm_source=github&utm_medium=readme&utm_campaign=polymarket_openAI_bot)**: Complete guide to Polymarket APIs, including:
  - Getting market prices and trades
  - Querying OrderFilled and OrdersMatched events
  - Market lifecycle tracking
  - Contract addresses and event structures
  - Step-by-step query examples

- **[Bitquery Access Tokens](https://account.bitquery.io/user/api_v2/access_tokens/?utm_source=github&utm_medium=readme&utm_campaign=polymarket_openAI_bot)**: Get your API key for accessing Bitquery GraphQL APIs

## Support

For issues or questions, please open an issue on GitHub.
