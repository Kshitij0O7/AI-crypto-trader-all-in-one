"""
DEX Configuration for Polygon (Matic) Chain
Uniswap V3 Router and common token addresses for Polymarket trading
"""

# Polygon Mainnet (Chain ID: 137)
POLYGON_MAINNET = {
    "chain_id": 137,
    "rpc_url": "https://polygon-rpc.com",

    # Uniswap V3 on Polygon
    "router_v3": "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45",  # SwapRouter02 on Polygon
    "quoter_v2": "0x61fFE014bA17989E743c5F6cB21bF9697530B21e",  # QuoterV2 on Polygon
    "factory": "0x1F98431c8aD98523631AE4a59f267346ea31F984",  # Uniswap V3 Factory on Polygon

    # Common tokens on Polygon
    "tokens": {
        "WETH": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",  # Wrapped ETH on Polygon
        "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",  # USDC on Polygon (used by Polymarket)
        "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",  # USDT on Polygon
        "DAI": "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",  # DAI on Polygon
        "MATIC": "0x0000000000000000000000000000000000001010",  # Native MATIC (not ERC20, but included for reference)
    }
}

# Alias for backward compatibility
BASE_MAINNET = POLYGON_MAINNET

# Uniswap V3 SwapRouter02 ABI (minimal)
SWAPROUTER_ABI = [
    {
        "inputs": [
            {
                "components": [
                    {"internalType": "address", "name": "tokenIn", "type": "address"},
                    {"internalType": "address", "name": "tokenOut", "type": "address"},
                    {"internalType": "uint24", "name": "fee", "type": "uint24"},
                    {"internalType": "address", "name": "recipient", "type": "address"},
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "uint256", "name": "amountOutMinimum", "type": "uint256"},
                    {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"}
                ],
                "internalType": "struct IV3SwapRouter.ExactInputSingleParams",
                "name": "params",
                "type": "tuple"
            }
        ],
        "name": "exactInputSingle",
        "outputs": [{"internalType": "uint256", "name": "amountOut", "type": "uint256"}],
        "stateMutability": "payable",
        "type": "function"
    }
]

# ERC20 ABI (minimal)
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [
            {"name": "_spender", "type": "address"},
            {"name": "_value", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [
            {"name": "_owner", "type": "address"},
            {"name": "_spender", "type": "address"}
        ],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    }
]

# Fee tiers for Uniswap V3 (in basis points)
FEE_TIERS = {
    "LOW": 500,      # 0.05%
    "MEDIUM": 3000,  # 0.3%
    "HIGH": 10000    # 1%
}
