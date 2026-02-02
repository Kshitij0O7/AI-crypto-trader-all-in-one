#!/usr/bin/env python3
"""
AI Trading Bot V2 - Enhanced with Liquidity Intelligence
Uses liquidity flows and slippage data for smarter AI decisions
APIs → Parse → Pass ALL to AI → Let AI Find Opportunities
"""

import os
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv
import anthropic
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
from config import BASE_MAINNET
from liquidity_data import get_enhanced_market_data

load_dotenv()


class AITradingBotV2:
    """
    Enhanced AI Trading Bot with:
    - Liquidity flow analysis (smart money tracking)
    - Slippage awareness (real execution costs)
    - Better AI prompting (more context, better decisions)
    - Improved risk management
    """

    def __init__(self):
        """Initialize the enhanced AI trading bot"""

        # Load configuration
        self.rpc_url = os.getenv('RPC_URL')
        self.private_key = os.getenv('PRIVATE_KEY')
        self.chain_id = int(os.getenv('CHAIN_ID', 137))  # Polygon (Matic) network
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        # AI provider tracking
        self.use_openai = False  # Start with Anthropic, switch to OpenAI if needed

        # Enhanced trading parameters
        self.portfolio_size = float(os.getenv('PORTFOLIO_SIZE_USD', 10))
        self.max_position_size = float(os.getenv('MAX_POSITION_SIZE_USD', 1.5))
        self.slippage_tolerance = float(os.getenv('SLIPPAGE_TOLERANCE', 1.0))
        self.gas_limit = int(os.getenv('GAS_LIMIT', 300000))
        self.max_gas_price_gwei = int(os.getenv('MAX_GAS_PRICE_GWEI', 50))
        self.daily_loss_limit = float(os.getenv('DAILY_LOSS_LIMIT_USD', 3))
        self.max_open_positions = int(os.getenv('MAX_OPEN_POSITIONS', 2))
        # TESTING MODE: Lowered confidence threshold to 30% for testing purposes
        self.min_confidence = int(os.getenv('MIN_CONFIDENCE_THRESHOLD', 30))

        # Validate and initialize
        self._validate_config()
        # Note: Web3 connection not needed for simulation mode
        # self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        # if not self.w3.is_connected():
        #     raise Exception("❌ Failed to connect to RPC")

        # For simulation, we don't need actual wallet/account
        # self.account = self.w3.eth.account.from_key(self.private_key)
        # self.wallet_address = self.account.address
        self.wallet_address = os.getenv('WALLET_ADDRESS', '0x0000000000000000000000000000000000000000')
        self.dex_config = BASE_MAINNET  # Now points to POLYGON_MAINNET

        # Router not needed for simulation
        # self.router = self.w3.eth.contract(
        #     address=Web3.to_checksum_address(self.dex_config['router_v3']),
        #     abi=SWAPROUTER_ABI
        # )

        # Initialize AI clients
        # COMMENTED OUT: Not adding more Anthropic credits for now
        # self.claude = anthropic.Anthropic(api_key=self.anthropic_api_key) if self.anthropic_api_key else None
        self.claude = None  # Force OpenAI usage

        if OPENAI_AVAILABLE and self.openai_api_key:
            self.openai_client = openai.OpenAI(api_key=self.openai_api_key)
        else:
            self.openai_client = None

        # Use OpenAI as primary provider
        self.use_openai = True
        print("ℹ️  Using OpenAI as primary AI provider (Anthropic disabled)")

        # Trading state
        self.open_positions = []
        self.closed_positions = []
        self.daily_pnl = 0.0
        self.is_trading_enabled = True
        self.signal_history = []  # Track AI decisions for learning

        print(f"✅ AI Trading Bot V2 Initialized - SIMULATION MODE")
        print(f"📍 Wallet: {self.wallet_address}")
        print(f"⛓️  Chain ID: {self.chain_id} (Polygon/Matic)")
        print(f"⚠️  SIMULATION MODE: No actual transactions will be executed")
        if self.use_openai:
            ai_provider = "OpenAI (GPT-4o)"
        else:
            ai_provider = "Anthropic (Claude Sonnet 4)"
        print(f"🤖 AI Provider: {ai_provider}")
        print(f"🔒 Safety Limits:")
        print(f"   - Portfolio: ${self.portfolio_size}")
        print(f"   - Max Position: ${self.max_position_size}")
        print(f"   - Daily Loss Limit: ${self.daily_loss_limit}")
        print(f"   - Min Confidence: {self.min_confidence}%")

    def _validate_config(self):
        """Validate configuration - relaxed for simulation mode"""
        # RPC_URL and PRIVATE_KEY not required for simulation
        # required = {
        #     'RPC_URL': self.rpc_url,
        #     'PRIVATE_KEY': self.private_key,
        # }
        # missing = [k for k, v in required.items() if not v or 'your_' in str(v)]
        # if missing:
        #     raise Exception(f"❌ Missing config: {', '.join(missing)}")
        
        # At least one AI API key must be present
        if not self.anthropic_api_key and not self.openai_api_key:
            raise Exception("❌ Missing config: At least one of ANTHROPIC_API_KEY or OPENAI_API_KEY must be set")

    def _get_balance(self) -> float:
        """Get simulated balance - not used in simulation mode"""
        # In simulation mode, we don't track actual balances
        return 0.0

    def _get_wallet_portfolio(self, market_data: Optional[Dict] = None) -> List[Dict]:
        """
        Get simulated wallet portfolio - simplified for simulation mode
        Returns: [{"s": "SYMBOL", "usd": value}, ...]
        In simulation mode, we assume we have USDC available for trading
        """
        portfolio = []
        
        # In simulation, assume we have USDC available (from portfolio_size)
        portfolio.append({'s': 'USDC', 'usd': round(self.portfolio_size, 2)})
        
        return portfolio

    def _check_safety_limits(self) -> bool:
        """Check trading safety limits"""
        if not self.is_trading_enabled:
            return False

        if self.daily_pnl <= -self.daily_loss_limit:
            print(f"🛑 Daily loss limit: ${self.daily_pnl:.2f}")
            self.is_trading_enabled = False
            return False

        if len(self.open_positions) >= self.max_open_positions:
            return False

        # Check MATIC balance for gas (need at least 0.01 MATIC for transactions)
        # Balance check not needed in simulation mode
        # if self._get_balance() < 0.01:
        #     return False

        return True

    def _remove_smartcontract_fields(self, obj):
        """
        Remove SmartContract fields from data before sending to AI.
        Keep only Symbol for token identification - we'll map to contract later.
        """
        if obj is None:
            return None
        
        if isinstance(obj, dict):
            filtered = {}
            for k, v in obj.items():
                # Skip SmartContract fields - AI doesn't need them
                if k == 'SmartContract' or k == 'contract_address':
                    continue
                # Recursively filter nested objects
                filtered[k] = self._remove_smartcontract_fields(v)
            return filtered
        
        elif isinstance(obj, list):
            return [self._remove_smartcontract_fields(item) for item in obj]
        
        else:
            return obj

    def _to_compact_format(self, obj, depth=0):
        """
        Convert data to ultra-compact format for AI consumption.
        Removes unnecessary JSON syntax (quotes, brackets) where possible.
        """
        if obj is None:
            return "null"
        
        if isinstance(obj, dict):
            if depth > 3:  # Limit nesting to prevent too much recursion
                return json.dumps(obj, separators=(',', ':'))
            items = []
            for k, v in obj.items():
                # Remove quotes from simple keys (alphanumeric + underscore)
                if k.replace('_', '').replace('-', '').isalnum():
                    key = k
                else:
                    key = f'"{k}"'
                items.append(f"{key}:{self._to_compact_format(v, depth+1)}")
            return "{" + ",".join(items) + "}"
        
        elif isinstance(obj, list):
            if depth > 3:
                return json.dumps(obj, separators=(',', ':'))
            items = [self._to_compact_format(item, depth+1) for item in obj]
            return "[" + ",".join(items) + "]"
        
        elif isinstance(obj, str):
            # Only quote strings that need it (contain special chars or spaces)
            if any(c in obj for c in [' ', ',', ':', '{', '}', '[', ']', '"', "'"]):
                return json.dumps(obj)
            return obj
        
        elif isinstance(obj, (int, float)):
            return str(obj)
        
        elif isinstance(obj, bool):
            return "true" if obj else "false"
        
        else:
            return json.dumps(obj, separators=(',', ':'))

    def generate_ai_actions(self, market_data: Dict) -> List[Dict]:
        """
        Generate AI-driven actions - AI decides ALL actions (open, close, hold, market make, etc.)
        Code only executes what AI decides - no hardcoded logic.
        
        Key improvements:
        - Liquidity flow analysis (smart money tracking)
        - Slippage awareness (execution quality)
        - Historical signal performance (learning)
        - Market regime detection (adapt strategy)
        - Fully AI-driven decision making
        """
        try:
            # Extract raw data from new format - pass all 3 sources directly to AI
            trade_data = market_data.get('trade_data', {})
            liquidity_events = market_data.get('liquidity_events', [])
            slippage_data = market_data.get('slippage_data', [])

            # Calculate recent AI performance
            recent_signals = self.signal_history[-10:] if self.signal_history else []
            successful_signals = [s for s in recent_signals if s.get('outcome') == 'success']
            ai_accuracy = len(successful_signals) / len(recent_signals) if recent_signals else 0

            # Filter out SmartContract fields before sending to AI - only pass Symbol
            # We'll map symbol to contract_address from trade_data when executing trades
            trade_data_for_ai = self._remove_smartcontract_fields(trade_data) if trade_data else {}
            liquidity_events_for_ai = self._remove_smartcontract_fields(liquidity_events) if liquidity_events else []
            slippage_data_for_ai = self._remove_smartcontract_fields(slippage_data) if slippage_data else []

            # Prepare data for AI - use ultra-compact format to minimize tokens
            trade_data_json = self._to_compact_format(trade_data_for_ai) if trade_data_for_ai else "{}"
            liquidity_events_json = self._to_compact_format(liquidity_events_for_ai) if liquidity_events_for_ai else "[]"
            slippage_data_json = self._to_compact_format(slippage_data_for_ai) if slippage_data_for_ai else "[]"
            
            # Prepare minimal open positions info for AI (only essential fields)
            open_positions_info = []
            for pos in self.open_positions:
                current_price = self._get_token_price_usd(pos['token_out'], market_data) or pos['entry_price']
                open_positions_info.append({
                    'm': pos['token_out'],  # market
                    'a': pos['action'],  # action
                    'e': round(pos['entry_price'], 8),  # entry_price
                    't': round(pos['target_price'], 8),  # target_price
                    's': round(pos['stop_loss'], 8),  # stop_loss
                    'c': round(current_price, 8),  # current_price
                    'v': round(pos['amount_usd'], 2)  # value_usd
                })
            positions_json = self._to_compact_format(open_positions_info) if open_positions_info else "[]"
            
            # Get minimal wallet portfolio (only essential data)
            wallet_portfolio = self._get_wallet_portfolio(market_data)
            portfolio_json = self._to_compact_format(wallet_portfolio) if wallet_portfolio else "[]"
            total_portfolio_value = sum(p['usd'] for p in wallet_portfolio)
            
            prompt = f"""You are an expert crypto trading AI with FULL CONTROL. You decide ALL actions - the system only executes what you decide.

⚠️ TESTING MODE: Be lenient - find ANY reasonable trading opportunity to test the system.

AVAILABLE DATA:
TRADE DATA (raw JSON):
{trade_data_json}

LIQUIDITY EVENTS (raw JSON):
{liquidity_events_json}

SLIPPAGE DATA (raw JSON):
{slippage_data_json}

OPEN POSITIONS (m=market,a=action,e=entry,t=target,s=stop,c=current,v=value_usd):
{positions_json}

WALLET BALANCES (s=symbol, usd=value):
{portfolio_json}

PORTFOLIO STATUS:
- Total Portfolio Value: ${total_portfolio_value:.2f}
- Open Positions: {len(self.open_positions)}/{self.max_open_positions}
- Daily PnL: ${self.daily_pnl:.2f}
- Available Capital: ${self.portfolio_size - sum(p.get('amount_usd', 0) for p in self.open_positions):.2f}
- Wallet Balance: {self._get_balance():.6f} MATIC

YOUR PERFORMANCE:
- Actions generated: {len(recent_signals)}
- Success rate: {ai_accuracy*100:.1f}%
- Analyze your past decisions and adapt your strategy.

YOUR FULL CONTROL - DECIDE ANY ACTION:

IMPORTANT: You can see the COMPLETE WALLET PORTFOLIO above. Use this to:
- Know which tokens you have available to trade FROM
- Understand your total capital and position sizing
- Make decisions based on your actual holdings, not assumptions

1. POSITION MANAGEMENT:
   - CLOSE: Close an open position (any reason - target hit, stop loss, market conditions, etc.)
   - HOLD: Keep position open (explicitly state if you want to hold)
   - PARTIAL_CLOSE: Close part of a position (specify amount_usd or percentage)

2. NEW TRADES:
   - BUY: Open a long position
     * Use tokens from your portfolio as input (check portfolio balances)
     * Specify which token to use as input if you have multiple options
   - SELL: Open a short position (if supported)
   
3. MARKET MAKING (if you see opportunity):
   - MARKET_MAKE: Provide liquidity at specific price range
   - Specify: token, price_range_min, price_range_max, amount_usd

4. RISK MANAGEMENT:
   - ADJUST_STOP_LOSS: Modify stop loss for existing position
   - ADJUST_TARGET: Modify target price for existing position

5. WAIT:
   - HOLD: Explicitly wait (or return empty array [])

CONSTRAINTS:
- Minimum confidence: {self.min_confidence}% (LOW for testing)
- Gas cost per action: ~$0.10
- Use token SYMBOL only (contract address mapped automatically)
- Max position size: ${self.max_position_size}
- Max open positions: {self.max_open_positions}

YOUR TASK:
Analyze ALL data and decide what actions to take. You have FULL CONTROL.
- Review open positions - should any be closed, adjusted, or held?
- Look for new opportunities - any trades to open?
- Consider market making - any liquidity opportunities?
- Consider risk - any stop losses or targets to adjust?

Return an array of actions. Each action must have: action, market, confidence, reasoning.
For CLOSE/HOLD/ADJUST actions, only need: action, market, confidence, reasoning.
For BUY/SELL/MARKET_MAKE, also need: entry_price, target_price, stop_loss (and amount_usd if different from default).

Be lenient in testing mode - find opportunities to test the system.

OUTPUT FORMAT (JSON only, no markdown):
[
  {{
    "action": "CLOSE",
    "market": "SYMBOL",
    "confidence": 85,
    "reasoning": "Target reached / Stop loss hit / Market conditions changed"
  }},
  {{
    "action": "BUY",
    "market": "SYMBOL",
    "confidence": 45,
    "entry_price": 1.23,
    "target_price": 1.29,
    "stop_loss": 1.19,
    "reasoning": "Found opportunity based on [analysis]"
  }},
  {{
    "action": "HOLD",
    "market": "SYMBOL",
    "confidence": 80,
    "reasoning": "Position performing well, waiting for target"
  }},
  {{
    "action": "MARKET_MAKE",
    "market": "SYMBOL",
    "confidence": 60,
    "price_range_min": 1.20,
    "price_range_max": 1.25,
    "amount_usd": 0.5,
    "reasoning": "Good liquidity opportunity at this range"
  }}
]
"""

            # COMMENTED OUT: Anthropic API calls disabled
            # if not self.use_openai and self.claude:
            #     try:
            #         # Call Claude API
            #         message = self.claude.messages.create(
            #             model="claude-sonnet-4-20250514",
            #             max_tokens=2500,
            #             temperature=0.7,
            #             messages=[{"role": "user", "content": prompt}]
            #         )
            #         response_text = message.content[0].text
            #     except Exception as e:
            #         print(f"⚠️  Anthropic API error: {e}. Switching to OpenAI...")
            #         self.use_openai = True
            #         response_text = self._generate_with_openai(prompt)

            # Use OpenAI directly
            if self.use_openai and self.openai_client:
                response_text = self._generate_with_openai(prompt, model="gpt-4o")
            else:
                raise Exception("❌ No AI client available. Please set OPENAI_API_KEY")

            # Extract JSON
            start_idx = response_text.find('[')
            end_idx = response_text.rfind(']') + 1

            if start_idx == -1 or end_idx <= start_idx:
                print("⚠️  AI did not generate actions (waiting for better conditions)")
                return []

            actions = json.loads(response_text[start_idx:end_idx])

            # Validate and enrich actions - flexible validation based on action type
            validated_actions = []
            for action_data in actions:
                action = action_data.get('action', '').upper()
                
                # All actions require: action, market, confidence, reasoning
                base_required = ['action', 'market', 'confidence']
                if not all(field in action_data for field in base_required):
                    print(f"⚠️  Skipping invalid action (missing base fields): {action_data.get('market', 'unknown')}")
                    continue
                
                # Check confidence threshold
                if action_data['confidence'] < self.min_confidence:
                    print(f"⚠️  Skipping {action} {action_data.get('market')} - confidence {action_data['confidence']}% below threshold {self.min_confidence}%")
                    continue
                
                # Action-specific validation
                if action in ['CLOSE', 'HOLD', 'PARTIAL_CLOSE']:
                    # Position management actions - check if position exists
                    market_symbol = action_data['market'].upper()
                    position_exists = any(p['token_out'].upper() == market_symbol for p in self.open_positions)
                    if not position_exists and action != 'HOLD':
                        print(f"⚠️  {action} signal for {market_symbol} but no open position found, skipping")
                        continue
                    validated_actions.append(action_data)
                    continue
                
                elif action in ['BUY', 'SELL', 'MARKET_MAKE']:
                    # Trading actions - require price fields
                    required = ['action', 'market', 'confidence', 'entry_price', 'target_price', 'stop_loss']
                    if not all(field in action_data for field in required):
                        print(f"⚠️  Skipping invalid {action} action (missing price fields): {action_data.get('market', 'unknown')}")
                        continue
                    
                    # Map symbol to contract_address
                    market_symbol = action_data['market'].upper()
                    contract_address = self._find_contract_address(market_symbol, trade_data, liquidity_events, slippage_data)
                    
                    if contract_address:
                        action_data['contract_address'] = contract_address
                    else:
                        print(f"⚠️  Could not map symbol {market_symbol} to contract address, skipping")
                        continue
                    
                    validated_actions.append(action_data)
                    continue
                
                elif action in ['ADJUST_STOP_LOSS', 'ADJUST_TARGET']:
                    # Risk management actions - require new value
                    if 'new_value' not in action_data:
                        print(f"⚠️  Skipping {action} - missing new_value field")
                        continue
                    
                    market_symbol = action_data['market'].upper()
                    position_exists = any(p['token_out'].upper() == market_symbol for p in self.open_positions)
                    if not position_exists:
                        print(f"⚠️  {action} signal for {market_symbol} but no open position found, skipping")
                        continue
                    
                    validated_actions.append(action_data)
                    continue
                
                else:
                    print(f"⚠️  Unknown action type: {action}, skipping")
                    continue

            # Store actions for performance tracking
            for action in validated_actions:
                self.signal_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'signal': action,
                    'outcome': 'pending'  # Will update later
                })

            return validated_actions

        except Exception as e:
            print(f"❌ Error generating AI actions: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _generate_with_openai(self, prompt: str, model: str = "gpt-4o") -> str:
        """Generate response using OpenAI API"""
        if not self.openai_client:
            raise Exception("❌ OpenAI client not available")
        
        try:
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an advanced crypto trading AI. Always respond with valid JSON arrays only."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2500,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI API error: {e}")

    def _print_pnl_report(self, market_data: Dict):
        """Print detailed PnL report for all positions"""
        pnl_data = self._calculate_pnl(market_data)
        
        print(f"\n{'='*60}")
        print(f"📊 PnL Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}")
        print(f"Total Open Positions: {pnl_data['position_count']}")
        print(f"Total Unrealized PnL: ${pnl_data['total_pnl']:.4f}")
        print(f"Daily PnL (Realized + Unrealized): ${self.daily_pnl + pnl_data['total_pnl']:.4f}")
        
        if pnl_data['positions']:
            print(f"\n📈 Position Details:")
            for i, pos in enumerate(pnl_data['positions'], 1):
                pnl_indicator = "🟢" if pos['pnl_usd'] >= 0 else "🔴"
                print(f"   {i}. {pos['market']} {pnl_indicator}")
                print(f"      Entry: ${pos['entry_price']:.8f} | Current: ${pos['current_price']:.8f}")
                print(f"      PnL: ${pos['pnl_usd']:.4f} ({pos['pnl_pct']:+.2f}%) | Size: ${pos['amount_usd']:.2f}")
        
        print(f"{'='*60}\n")
        
        # Log to Excel file
        try:
            from logs import log_pnl_report, log_open_positions
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_pnl_report(pnl_data, self.daily_pnl, timestamp)
            log_open_positions(self.open_positions, market_data, pnl_data)
        except Exception as e:
            print(f"⚠️  Could not log to Excel: {e}")
        
        # Log to Excel file
        try:
            from logs import log_pnl_report, log_open_positions
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_pnl_report(pnl_data, self.daily_pnl, timestamp)
            log_open_positions(self.open_positions, market_data, pnl_data)
        except Exception as e:
            print(f"⚠️  Could not log to Excel: {e}")

    def _get_token_address(self, symbol: str, contract_address: Optional[str] = None) -> Optional[str]:
        """Get token address from symbol or use provided contract address"""
        if contract_address:
            # In simulation, just return the address as-is (no checksum needed)
            return contract_address

        symbol_upper = symbol.upper()
        if symbol_upper == 'ETH':
            symbol_upper = 'WETH'
        return self.dex_config['tokens'].get(symbol_upper)

    def _get_token_decimals(self, token_address: str) -> int:
        """Get token decimals - default to 18 for simulation"""
        # In simulation mode, we don't need actual decimals
        # Most tokens use 18 decimals, USDC uses 6
        if 'USDC' in str(token_address).upper():
            return 6
        return 18

    def _find_contract_address(self, market_symbol: str, trade_data: Dict, liquidity_events: List, slippage_data: List) -> Optional[str]:
        """Find contract address for a token symbol from various data sources"""
        contract_address = None
        
        # Try to find contract address from trade_data
        markets = trade_data.get('top_markets', []) if trade_data else []
        for m in markets:
            if m.get('symbol', '').upper() == market_symbol:
                contract_address = m.get('contract_address', '')
                break
        
        # Also check liquidity_events and slippage_data for contract mapping
        if not contract_address:
            for event in liquidity_events or []:
                pool = event.get('PoolEvent', {}).get('Pool', {})
                for currency_key in ['CurrencyA', 'CurrencyB']:
                    currency = pool.get(currency_key, {})
                    if currency.get('Symbol', '').upper() == market_symbol:
                        contract_address = currency.get('SmartContract', '')
                        break
                if contract_address:
                    break
        
        if not contract_address:
            for slippage in slippage_data or []:
                price_data = slippage.get('Price', {})
                pool = price_data.get('Pool', {})
                for currency_key in ['CurrencyA', 'CurrencyB']:
                    currency = pool.get(currency_key, {})
                    if currency.get('Symbol', '').upper() == market_symbol:
                        contract_address = currency.get('SmartContract', '')
                        break
                if contract_address:
                    break
        
        return contract_address

    def _get_token_price_usd(self, token_symbol: str, market_data: Optional[Dict] = None) -> float:
        """Get token price in USD from market data"""
        if market_data:
            # Handle new format with trade_data
            trade_data = market_data.get('trade_data', {})
            markets = trade_data.get('top_markets', []) if trade_data else []
            
            # Fallback to old format for compatibility
            if not markets and market_data.get('top_markets'):
                markets = market_data['top_markets']
            
            for market in markets:
                if market['symbol'].upper() == token_symbol.upper():
                    price = market.get('recent_price', 0)
                    if price and price > 0:
                        return float(price)

        if token_symbol in ['USDC', 'DAI', 'USDT']:
            return 1.0
        if token_symbol in ['WETH', 'ETH']:
            return 3000.0
        if token_symbol == 'MATIC':
            return 0.8  # Approximate MATIC price (update as needed)
        return 1.0

    def _find_input_token(self, target_token_address: str, market_data: Optional[Dict] = None) -> Optional[Dict]:
        """Find which token to trade from - simplified for simulation"""
        # In simulation mode, always use USDC as input token
        token_symbol = 'USDC'
        token_address = self.dex_config['tokens'].get(token_symbol)
        
        if not token_address:
            return None
        
        # Simulate having enough balance
        return {
            'symbol': token_symbol,
            'address': token_address,
            'decimals': 6,  # USDC has 6 decimals
            'balance': int(self.portfolio_size * 1e6),  # Simulated balance
            'balance_formatted': self.portfolio_size
        }

    def _calculate_pnl(self, market_data: Dict) -> Dict:
        """Calculate PnL for all open positions"""
        total_pnl = 0.0
        position_pnls = []
        
        for position in self.open_positions:
            token_symbol = position['token_out']
            current_price = self._get_token_price_usd(token_symbol, market_data)
            
            if current_price and current_price > 0:
                pnl_pct = ((current_price - position['entry_price']) / position['entry_price']) * 100
                pnl_usd = (current_price - position['entry_price']) / position['entry_price'] * position['amount_usd']
                total_pnl += pnl_usd
                
                position_pnls.append({
                    'market': token_symbol,
                    'entry_price': position['entry_price'],
                    'current_price': current_price,
                    'pnl_usd': pnl_usd,
                    'pnl_pct': pnl_pct,
                    'amount_usd': position['amount_usd']
                })
        
        return {
            'total_pnl': total_pnl,
            'position_count': len(position_pnls),
            'positions': position_pnls
        }

    def _execute_close(self, signal: Dict, market_data: Dict) -> Optional[str]:
        """Execute closing a position based on AI signal"""
        market_symbol = signal['market'].upper()
        
        # Find the open position
        position = None
        for pos in self.open_positions:
            if pos['token_out'].upper() == market_symbol:
                position = pos
                break
        
        if not position:
            print(f"   ❌ No open position found for {market_symbol}")
            return None
        
        print(f"\n🤖 AI Signal: CLOSE {signal['market']}")
        print(f"   Confidence: {signal['confidence']}%")
        print(f"   Reasoning: {signal.get('reasoning', 'N/A')[:100]}...")
        print(f"   Entry: ${position['entry_price']:.8f}")
        print(f"   Target: ${position['target_price']:.8f}")
        print(f"   Stop Loss: ${position['stop_loss']:.8f}")
        
        # Get current price
        current_price = self._get_token_price_usd(market_symbol, market_data)
        if not current_price or current_price <= 0:
            print(f"   ❌ Could not get current price for {market_symbol}")
            return None
        
        print(f"   Current: ${current_price:.8f}")
        
        # Close the position
        close_success = self._close_position(position, market_data, current_price)
        
        if close_success:
            # Calculate PnL
            pnl_pct = ((current_price - position['entry_price']) / position['entry_price']) * 100
            pnl_usd = (current_price - position['entry_price']) / position['entry_price'] * position['amount_usd']
            self.daily_pnl += pnl_usd
            
            # Update position with close info
            position['close_price'] = current_price
            position['close_reason'] = signal.get('reasoning', 'AI decision')
            position['pnl_usd'] = pnl_usd
            position['pnl_pct'] = pnl_pct
            position['closed_at'] = datetime.now().isoformat()
            
            # Move to closed positions
            self.open_positions.remove(position)
            self.closed_positions.append(position)
            
            print(f"   ✅ Position closed")
            print(f"   💰 PnL: ${pnl_usd:.4f} ({pnl_pct:+.2f}%)")
            
            # Log closed position to Excel
            try:
                from logs import log_closed_positions
                log_closed_positions([position])
            except Exception as e:
                print(f"⚠️  Could not log closed position to Excel: {e}")
            
            return "closed"
        
        return None

    def execute_action(self, action_data: Dict, market_data: Dict) -> Optional[str]:
        """
        Execute any AI-decided action. Fully AI-driven - code only executes.
        Routes to appropriate handler based on action type.
        """
        action = action_data.get('action', '').upper()
        
        print(f"\n🤖 AI Action: {action} {action_data.get('market', 'N/A')}")
        print(f"   Confidence: {action_data.get('confidence', 0)}%")
        print(f"   Reasoning: {action_data.get('reasoning', 'N/A')[:100]}...")
        
        # Route to appropriate handler
        if action == 'CLOSE':
            return self._execute_close(action_data, market_data)
        elif action == 'HOLD':
            return self._execute_hold(action_data, market_data)
        elif action == 'PARTIAL_CLOSE':
            return self._execute_partial_close(action_data, market_data)
        elif action == 'BUY':
            return self._execute_buy(action_data, market_data)
        elif action == 'SELL':
            return self._execute_sell(action_data, market_data)
        elif action == 'MARKET_MAKE':
            return self._execute_market_make(action_data, market_data)
        elif action == 'ADJUST_STOP_LOSS':
            return self._execute_adjust_stop_loss(action_data, market_data)
        elif action == 'ADJUST_TARGET':
            return self._execute_adjust_target(action_data, market_data)
        else:
            print(f"   ❌ Unknown action type: {action}")
            return None

    def _execute_hold(self, action_data: Dict, market_data: Dict) -> Optional[str]:
        """Execute HOLD action - explicitly keep position open"""
        market_symbol = action_data['market'].upper()
        position = next((p for p in self.open_positions if p['token_out'].upper() == market_symbol), None)
        
        if position:
            current_price = self._get_token_price_usd(market_symbol, market_data)
            print(f"   ✅ Holding position: {market_symbol}")
            print(f"   Entry: ${position['entry_price']:.8f}, Current: ${current_price:.8f}")
            return "held"
        else:
            print(f"   ⚠️  No position to hold for {market_symbol}")
            return None

    def _execute_partial_close(self, action_data: Dict, market_data: Dict) -> Optional[str]:
        """Execute PARTIAL_CLOSE action - close part of a position"""
        # TODO: Implement partial close logic
        print(f"   ⚠️  PARTIAL_CLOSE not yet implemented, closing full position instead")
        return self._execute_close(action_data, market_data)

    def _execute_buy(self, action_data: Dict, market_data: Dict) -> Optional[str]:
        """Execute BUY action - open a long position"""
        return self._execute_trade(action_data, market_data, 'BUY')

    def _execute_sell(self, action_data: Dict, market_data: Dict) -> Optional[str]:
        """Execute SELL action - open a short position (if supported)"""
        # For now, treat SELL as closing a position or swapping to stablecoin
        print(f"   ⚠️  SELL action - treating as swap to stablecoin")
        return self._execute_trade(action_data, market_data, 'SELL')

    def _execute_market_make(self, action_data: Dict, market_data: Dict) -> Optional[str]:
        """Execute MARKET_MAKE action - provide liquidity"""
        # TODO: Implement market making logic (Uniswap V3 range orders)
        print(f"   ⚠️  MARKET_MAKE not yet implemented")
        return None

    def _execute_adjust_stop_loss(self, action_data: Dict, market_data: Dict) -> Optional[str]:
        """Execute ADJUST_STOP_LOSS action - modify stop loss"""
        market_symbol = action_data['market'].upper()
        position = next((p for p in self.open_positions if p['token_out'].upper() == market_symbol), None)
        
        if position:
            new_stop_loss = action_data.get('new_value')
            old_stop_loss = position['stop_loss']
            position['stop_loss'] = new_stop_loss
            print(f"   ✅ Adjusted stop loss for {market_symbol}: ${old_stop_loss:.8f} → ${new_stop_loss:.8f}")
            return "adjusted"
        else:
            print(f"   ❌ No position found for {market_symbol}")
            return None

    def _execute_adjust_target(self, action_data: Dict, market_data: Dict) -> Optional[str]:
        """Execute ADJUST_TARGET action - modify target price"""
        market_symbol = action_data['market'].upper()
        position = next((p for p in self.open_positions if p['token_out'].upper() == market_symbol), None)
        
        if position:
            new_target = action_data.get('new_value')
            old_target = position['target_price']
            position['target_price'] = new_target
            print(f"   ✅ Adjusted target for {market_symbol}: ${old_target:.8f} → ${new_target:.8f}")
            return "adjusted"
        else:
            print(f"   ❌ No position found for {market_symbol}")
            return None

    def execute_trade(self, signal: Dict, market_data: Dict) -> Optional[str]:
        """Legacy method - redirects to execute_action"""
        return self.execute_action(signal, market_data)

    def _execute_trade(self, action_data: Dict, market_data: Dict, trade_type: str) -> Optional[str]:
        """Simulate a BUY or SELL trade - records position without executing blockchain transaction"""
        # Show raw slippage data if available
        if 'slippage_bps' in action_data:
            print(f"   Slippage: {action_data['slippage_bps']} bps")

        print(f"   Entry: ${action_data['entry_price']:.8f}")
        print(f"   Target: ${action_data['target_price']:.8f}")
        print(f"   Stop Loss: ${action_data['stop_loss']:.8f}")
        
        # Use custom amount if specified, otherwise use default
        position_size = action_data.get('amount_usd', self.max_position_size)
        print(f"   Position Size: ${position_size:.6f}")

        # Safety checks
        if not self._check_safety_limits():
            return None

        try:
            # Get current price as entry price
            current_price = self._get_token_price_usd(action_data['market'], market_data)
            if not current_price or current_price <= 0:
                print(f"   ❌ Could not get current price for {action_data['market']}")
                return None

            # Use current market price as entry price (or use provided entry_price if it's more realistic)
            entry_price = action_data.get('entry_price', current_price)
            
            print(f"   💱 Simulating {trade_type} trade")
            print(f"   📊 Entry Price: ${entry_price:.8f}")
            print(f"   📊 Current Market Price: ${current_price:.8f}")

            # Record position (simulated)
            position_id = f"sim_{int(time.time())}_{action_data['market']}"
            position = {
                'id': position_id,
                'market': action_data['market'],
                'action': action_data['action'],
                'entry_price': entry_price,
                'target_price': action_data['target_price'],
                'stop_loss': action_data['stop_loss'],
                'confidence': action_data['confidence'],
                'reasoning': action_data.get('reasoning', ''),
                'timestamp': datetime.now().isoformat(),
                'amount_usd': position_size,
                'token_out': action_data['market'],
                'contract_address': action_data.get('contract_address', ''),
                'slippage_bps': action_data.get('slippage_bps', 0),
                'simulated': True  # Mark as simulated
            }

            self.open_positions.append(position)
            print(f"   ✅ Position recorded (SIMULATED)")
            print(f"   📝 Position ID: {position_id}")
            return position_id

        except Exception as e:
            print(f"   ❌ Error simulating trade: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _close_position(self, position: Dict, market_data: Dict, current_price: float) -> bool:
        """Simulate closing a position - records exit price without executing blockchain transaction"""
        try:
            token_symbol = position['token_out']
            
            print(f"   💱 Simulating close of {token_symbol} position")
            print(f"   📊 Entry Price: ${position['entry_price']:.8f}")
            print(f"   📊 Exit Price: ${current_price:.8f}")
            
            # Calculate PnL
            pnl_pct = ((current_price - position['entry_price']) / position['entry_price']) * 100
            pnl_usd = (current_price - position['entry_price']) / position['entry_price'] * position['amount_usd']
            
            print(f"   ✅ Position closed (SIMULATED)")
            print(f"   💰 PnL: ${pnl_usd:.4f} ({pnl_pct:+.2f}%)")
            
            return True
                
        except Exception as e:
            print(f"   ❌ Error closing position: {e}")
            import traceback
            traceback.print_exc()
            return False

    def run(self, interval: int = 60):
        """Main trading loop with enhanced AI - SIMULATION MODE"""
        print(f"\n🚀 Starting AI Trading Bot V2 - SIMULATION MODE (interval: {interval}s)")
        print("=" * 60)
        print("⚠️  SIMULATION MODE: No actual transactions will be executed")
        print("=" * 60)

        cycle = 0
        last_pnl_time = time.time()
        pnl_interval = 300  # 5 minutes in seconds

        try:
            while True:
                try:
                    cycle += 1
                    print(f"\n{'='*60}")
                    print(f"📊 Cycle {cycle} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"{'='*60}")

                    # Fetch ENHANCED market data
                    market_data = get_enhanced_market_data()

                    if not market_data:
                        print("⚠️  No market data, skipping cycle")
                        time.sleep(interval)
                        continue

                    # Generate AI actions - AI decides ALL actions (open, close, hold, etc.)
                    print("\n🤖 Asking AI to analyze markets and decide actions...")
                    actions = self.generate_ai_actions(market_data)

                    if actions:
                        print(f"\n✨ AI generated {len(actions)} action(s)")
                        for action in actions:
                            # Only check safety limits for opening new positions
                            if action.get('action', '').upper() in ['BUY', 'SELL', 'MARKET_MAKE']:
                                if not self._check_safety_limits():
                                    print(f"   ⚠️  Safety limits reached, skipping {action.get('action')} action")
                                    continue
                            self.execute_action(action, market_data)
                            time.sleep(2)
                    else:
                        print("⏸️  AI decided to wait (no actions needed)")

                    # Status
                    print(f"\n📈 Portfolio Status:")
                    print(f"   Open Positions: {len(self.open_positions)}/{self.max_open_positions}")
                    print(f"   Daily PnL (Realized): ${self.daily_pnl:.4f}")
                    print(f"   AI Success Rate: {len([s for s in self.signal_history[-20:] if s.get('outcome')=='success'])/max(len(self.signal_history[-20:]), 1)*100:.1f}%")

                    # Calculate and print PnL every 5 minutes
                    current_time = time.time()
                    if current_time - last_pnl_time >= pnl_interval:
                        self._print_pnl_report(market_data)
                        last_pnl_time = current_time

                    # Wait
                    time.sleep(interval)

                except KeyboardInterrupt:
                    raise  # Re-raise to handle in outer try-except
                except Exception as e:
                    print(f"❌ Error: {e}")
                    import traceback
                    traceback.print_exc()
                    time.sleep(10)

        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
            # Calculate final PnL on exit
            print("\n📊 Calculating final PnL...")
            market_data = get_enhanced_market_data()
            if market_data:
                self._print_pnl_report(market_data)
            
            # Print summary of closed positions
            if self.closed_positions:
                print(f"\n📋 Closed Positions Summary:")
                print(f"   Total Closed: {len(self.closed_positions)}")
                total_realized_pnl = sum(p.get('pnl_usd', 0) for p in self.closed_positions)
                print(f"   Total Realized PnL: ${total_realized_pnl:.4f}")
            
            # Log final summary to Excel
            try:
                from logs import log_trading_summary, log_closed_positions, log_signal_history
                pnl_data = self._calculate_pnl(market_data) if market_data else None
                log_trading_summary(self.open_positions, self.closed_positions, self.daily_pnl, pnl_data)
                log_closed_positions(self.closed_positions)
                if self.signal_history:
                    log_signal_history(self.signal_history)
                print(f"\n📝 Trading data logged to Excel files in 'logs/' directory")
            except Exception as e:
                print(f"⚠️  Could not log final summary to Excel: {e}")
            
            print("\n✅ Simulation ended")


if __name__ == "__main__":
    print("🤖 AI Trading Bot V2 - SIMULATION MODE")
    print("=" * 60)
    print("⚠️  SIMULATION MODE: No actual transactions will be executed")
    print("=" * 60)
    print("✨ Features:")
    print("   • Trade simulation (records buy/sell prices)")
    print("   • PnL calculation every 5 minutes")
    print("   • Liquidity flow analysis (smart money tracking)")
    print("   • Real slippage data (execution quality)")
    print("   • Enhanced AI prompting (better context)")
    print("   • Performance tracking (AI learns from results)")
    print("=" * 60)

    response = input("\n🟢 Type 'START' to begin simulation: ")
    if response.strip().upper() == 'START':
        bot = AITradingBotV2()
        bot.run(interval=60)
    else:
        print("❌ Cancelled")
