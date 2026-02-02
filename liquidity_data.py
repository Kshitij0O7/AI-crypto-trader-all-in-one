"""
Liquidity Data Fetcher - Enhanced market data using Bitquery liquidity streams
This provides much richer data for AI-powered trading decisions
"""
import os
import requests
from typing import Dict, List, Optional


BITQUERY_API_KEY = os.getenv('BITQUERY_API_KEY')


def fetch_liquidity_events(limit: int = 100) -> Dict:
    """
    Fetch liquidity add/remove events from Polygon network
    This shows smart money movements - much more valuable than just trades!
    """
    url = "https://streaming.bitquery.io/graphql"

    query = """
    query PolygonLiquidityEvents {
        EVM(network: matic) {
            DEXPoolEvents(
                limit: {count: 200}
                orderBy: {descending: Block_Time}
            ) {
                Block {
                    Time
                    Number
                }
                PoolEvent {
                    AtoBPrice
                    BtoAPrice
                    Liquidity {
                        AmountCurrencyA
                        AmountCurrencyB
                    }
                    Pool {
                        CurrencyA {
                            Symbol
                            SmartContract
                        }
                        CurrencyB {
                            Symbol
                            SmartContract
                        }
                        PoolId
                        SmartContract
                    }
                    Dex {
                        ProtocolName
                    }
                }
                Transaction {
                    Hash
                }
            }
        }
    }
    """

    try:
        response = requests.post(
            url,
            json={
                'query': query,
                'variables': {'limit': limit}
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
            print(f"⚠️  Liquidity API not available: {data['errors'][0].get('message', 'Unknown error')}")
            return None

        if not data.get('data'):
            print("⚠️  No liquidity data returned (feature may require different API endpoint)")
            return None

        events = data.get('data', {}).get('EVM', {}).get('DEXPoolEvents', [])

        if not events:
            print("⚠️  No liquidity events returned")
            return None

        # Return raw events - let AI decide what to do with them
        return events

    except Exception as e:
        print(f"⚠️  Liquidity data not available: {e}")
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
