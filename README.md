# OracleWatch

**OracleWatch** — утилита для мониторинга расхождений между ценами из Chainlink‑оракулов и on‑chain DEX‑пулы Uniswap V2.  
Позволяет вовремя обнаруживать манипуляции или арбитражные возможности.

## Возможности

- Подключение к любому Ethereum RPC (Infura, Alchemy, собственный узел).  
- Поддержка нескольких токенов одновременно.  
- Сравнение `Chainlink latestAnswer` и `UniswapV2Pair.getReserves()` (TWAP).  
- Вывод расхождения в процентах и статус: **OK** / **ALERT**.

## Установка

```bash
git clone https://github.com/ваш-профиль/OracleWatch.git
cd OracleWatch
pip install -r requirements.txt
