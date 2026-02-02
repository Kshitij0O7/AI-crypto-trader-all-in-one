"""
Liquidity Data Fetcher - Enhanced market data using Bitquery liquidity streams
This provides much richer data for AI-powered trading decisions
"""
import os
import requests
from typing import Dict, List, Optional


BITQUERY_API_KEY = os.getenv('BITQUERY_API_KEY')


def fetch_liquidity_events(limit: int = 200) -> List[Dict]:
    """
    Fetch OrdersMatched events from Polymarket order book
    This shows liquidity provision activity - when orders are matched on the order book
    
    Returns:
        List of processed order match events with:
        - takerOrderMaker: Trader address placing the order
        - takerAssetId: Asset ID being traded
        - takerAmountFilled: Amount of tokens trader wants to buy
        - makerAmountFilled: Amount of tokens liquidity provider can provide
    """
    url = "https://streaming.bitquery.io/graphql"

    query = """
    query PolymarketOrdersMatched {
      EVM(dataset: realtime, network: matic) {
        Events(
          orderBy: { descending: Block_Time }
          where: {
            Block: {Date: {after_relative: {days_ago: 1}}}
            Log: { Signature: { Name: { in: ["OrdersMatched"] } } }
            LogHeader: {
              Address: { is: "0xC5d563A36AE78145C45a50134d48A1215220f80a" }
            }
          }
          limit: { count: 200 }
        ) {
          Block {
            Time
          }
          Arguments {
            Name
            Value {
              ... on EVM_ABI_Integer_Value_Arg {
                integer
              }
              ... on EVM_ABI_Address_Value_Arg {
                address
              }
              ... on EVM_ABI_String_Value_Arg {
                string
              }
              ... on EVM_ABI_BigInt_Value_Arg {
                bigInteger
              }
              ... on EVM_ABI_Bytes_Value_Arg {
                hex
              }
              ... on EVM_ABI_Boolean_Value_Arg {
                bool
              }
            }
          }
        }
      }
    }
    """

    try:
        response = requests.post(
            url,
            json={
                'query': query
            },
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {BITQUERY_API_KEY}'
            },
            timeout=10
        )

        if response.status_code != 200:
            print(f"❌ Bitquery API error: {response.status_code}")
            return None

        data = response.json()

        # Check for API errors
        if 'errors' in data:
            print(f"⚠️  OrdersMatched API not available: {data['errors'][0].get('message', 'Unknown error')}")
            return None

        if not data.get('data'):
            print("⚠️  No liquidity data returned")
            return None

        events = data.get('data', {}).get('EVM', {}).get('Events', [])

        if not events:
            print("⚠️  No OrdersMatched events returned")
            return None

        # Process events to extract relevant fields from Arguments
        processed_events = []
        for event in events:
            try:
                # Extract arguments into a dictionary
                args = {}
                for arg in event.get('Arguments', []):
                    arg_name = arg.get('Name')
                    arg_value = arg.get('Value', {})
                    
                    # Extract value based on type
                    if 'bigInteger' in arg_value:
                        args[arg_name] = arg_value['bigInteger']
                    elif 'address' in arg_value:
                        args[arg_name] = arg_value['address']
                    elif 'integer' in arg_value:
                        args[arg_name] = arg_value['integer']
                    elif 'string' in arg_value:
                        args[arg_name] = arg_value['string']
                    elif 'hex' in arg_value:
                        args[arg_name] = arg_value['hex']
                    elif 'bool' in arg_value:
                        args[arg_name] = arg_value['bool']
                
                # Build processed event
                processed_event = {
                    'timestamp': event.get('Block', {}).get('Time'),
                    'takerOrderMaker': args.get('takerOrderMaker'),  # Trader address
                    'takerAssetId': args.get('takerAssetId'),  # Asset ID
                    'takerAmountFilled': args.get('takerAmountFilled'),  # Amount trader wants to buy
                    'makerAmountFilled': args.get('makerAmountFilled'),  # Amount liquidity provider can provide
                    'takerOrderHash': args.get('takerOrderHash'),  # Order hash for reference
                    'makerAssetId': args.get('makerAssetId')  # Maker asset ID
                }
                
                processed_events.append(processed_event)
            except Exception as e:
                # Skip events that can't be processed
                continue

        if not processed_events:
            print("⚠️  No valid OrdersMatched events processed")
            return None

        return processed_events

    except Exception as e:
        print(f"⚠️  Error fetching OrdersMatched events: {e}")
        return None


def get_enhanced_market_data() -> Dict:
    """
    Get raw market data from trade data and liquidity events - no processing, let AI decide
    Returns raw API responses for AI to interpret
    Note: Slippage data not available for Polymarkets
    """
    from market_data import fetch_polymarket_data

    # Get regular trade data (Polymarket on Polygon)
    print("📡 Fetching trade data...")
    trade_data = fetch_polymarket_data(limit=200)

    # Get liquidity events
    print("💧 Fetching liquidity events...")
    liquidity_data = fetch_liquidity_events()

    # Return raw responses - no processing, no combining
    return {
        'trade_data': trade_data,  # Raw trade data from market_data
        'liquidity_events': liquidity_data  # Raw liquidity events array
    }


if __name__ == "__main__":
    print("🔍 Testing Enhanced Market Data Fetcher...")
    data = get_enhanced_market_data()

    if data:
        print("\n✅ Enhanced data fetch successful")
    else:
        print("\n❌ Failed to fetch data")
