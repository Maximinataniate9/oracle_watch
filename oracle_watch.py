#!/usr/bin/env python3
"""
OracleWatch — мониторинг расхождений между Chainlink‑оракулами и ценами Uniswap V2 пулов.
"""

import os
import time
from decimal import Decimal
from web3 import Web3

# --- Чтение настроек из окружения ---
RPC_URL               = os.getenv("ETH_RPC_URL")
SYMBOLS               = os.getenv("SYMBOLS", "").split(",")  # напр. "USDC,DAI"
AGGREGATOR_ADDRESSES  = os.getenv("AGGREGATOR_ADDRESSES", "").split(",")
POOL_ADDRESSES        = os.getenv("POOL_ADDRESSES", "").split(",")
THRESHOLD_PERCENT     = Decimal(os.getenv("THRESHOLD_PERCENT", "1.0"))  # %
POLL_INTERVAL         = int(os.getenv("POLL_INTERVAL", "60"))           # сек

# Проверка
if not (RPC_URL and SYMBOLS and AGGREGATOR_ADDRESSES and POOL_ADDRESSES):
    print("❗ Задайте ETH_RPC_URL, SYMBOLS, AGGREGATOR_ADDRESSES и POOL_ADDRESSES")
    exit(1)
if not (len(SYMBOLS)==len(AGGREGATOR_ADDRESSES)==len(POOL_ADDRESSES)):
    print("❗ SYMBOLS, AGGREGATOR_ADDRESSES и POOL_ADDRESSES должны быть одинаковой длины")
    exit(1)

w3 = Web3(Web3.HTTPProvider(RPC_URL))
if not w3.is_connected():
    print("❗ Не удалось подключиться к RPC‑узлу")
    exit(1)

# ABI для Chainlink AggregatorV3 и UniswapV2Pair.getReserves()
AGGREGATOR_ABI = [
    {"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"latestAnswer","outputs":[{"internalType":"int256","name":"","type":"int256"}],"stateMutability":"view","type":"function"}
]
PAIR_ABI = [
    {"constant":True,"inputs":[],"name":"getReserves","outputs":[
        {"internalType":"uint112","name":"_reserve0","type":"uint112"},
        {"internalType":"uint112","name":"_reserve1","type":"uint112"},
        {"internalType":"uint32","name":"_blockTimestampLast","type":"uint32"}],
     "stateMutability":"view","type":"function"}
]

def fetch_oracle_price(addr):
    agg = w3.eth.contract(address=addr, abi=AGGREGATOR_ABI)
    dec = agg.functions.decimals().call()
    ans = agg.functions.latestAnswer().call()
    return Decimal(ans) / (Decimal(10) ** dec)

def fetch_dex_price(addr):
    pair = w3.eth.contract(address=addr, abi=PAIR_ABI)
    r0, r1, _ = pair.functions.getReserves().call()
    if r0 == 0 or r1 == 0:
        return None
    # предполагаем, что reserve0 = token, reserve1 = WETH
    # цена token в ETH = reserve1 / reserve0
    return Decimal(r1) / Decimal(r0)

def main():
    print(f"🔍 OracleWatch запущен. Порог расхождения {THRESHOLD_PERCENT}%\n")
    while True:
        for sym, agg_addr, pool_addr in zip(SYMBOLS, AGGREGATOR_ADDRESSES, POOL_ADDRESSES):
            try:
                oracle_price = fetch_oracle_price(agg_addr)
                dex_price    = fetch_dex_price(pool_addr)
                if dex_price is None:
                    print(f"{sym}: Не удалось получить резервы пула.")
                    continue
                deviation = abs(dex_price - oracle_price) / oracle_price * 100
                status = "OK" if deviation < THRESHOLD_PERCENT else "ALERT"
                print(f"{sym}: Oracle={oracle_price:.6f} ETH  DEX={dex_price:.6f} ETH  Δ={deviation:.2f}% → {status}")
            except Exception as e:
                print(f"{sym}: Ошибка при запросе данных: {e}")
        print()
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
