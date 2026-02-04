# bitcoin-bruteforce
A Go program designed to create private keys, derive corresponding public keys from the private keys, and then check that the generated wallet addresses have funds. This is the most recent up to date FREE bruteforcer.

# how to use

go build bitcoin-wallet-bruteforce.go

(To use on all systems to ensure proper GCLIB: go build -ldflags '-extldflags "-static"' -o bitcoin-wallet-bruteforce

./bitcoin-wallet-bruteforce threads out-file.txt

Example: ./bitcoin-wallet-bruteforce 1000 wallets.txt

Offline Version: ./bitcoin-wallet-bruteforce threads out-file.txt btc-data-file.txt

Example: ./bitcoin-wallet-bruteforce 1000000 out.txt btc_aa.txt

# Information

All bitcoin addresses with funds in them will be recorded to the out-file.txt you choose. You can also rename this to anything you want. I advise you to run this in a screen and leave it for running for days on end. This is an efficient method of trying to obtain free funds.

Make sure Golang 1.2.1 is installed or latest version.

![LMAO](https://github.com/v0rl0x/bitcoin-bruteforce/assets/148959415/9f5cc5e5-0161-4554-ba45-f17a85324543)

Bitcoin bech32 addresses are generated with the bech32 version of the script.

The scripts come with the option to use telegram bots to save any bitcoin wallets automatically. If you do not whish to use this feature then put 123 as both values for the chat id and bot token.

## MT5 Trading Bot (Strategy + Risk Management + News Filters)

This repo now includes a Python-based MT5 trading bot skeleton that blends ICT/TJR/Casper SMC concepts (liquidity sweeps, order blocks, fair value gaps) with professional risk management and an economic news filter. The bot is fully configurable (risk per trade, max trades per day, lot sizing, symbols, timeframes, etc.) and can connect to MetaTrader 5 for execution.

### Features

- Strategy built around price-action structure (trend filter, liquidity sweep detection, order blocks, fair value gaps).
- Risk controls: max daily loss, max open positions, position sizing by risk %, min R:R enforcement.
- Economic news filter (TradingEconomics calendar) to pause trading around high-impact events.
- MT5 broker integration and configurable execution settings.

### Setup

1. Install Python dependencies:

```bash
pip install -r requirements-trading-bot.txt
```

2. Copy and edit the configuration:

```bash
cp trading_bot/config.example.yaml trading_bot/config.yaml
```

3. Set your TradingEconomics API key (optional, for news filtering):

```bash
export TRADING_ECONOMICS_API_KEY=\"your_key_here\"
```

4. Configure MT5 credentials inside `trading_bot/config.yaml`.

### Run

```bash
python trading_bot/bot.py --config trading_bot/config.yaml --interval 60
```

### Notes

- The strategy is a starting point and should be tuned for your broker, symbol, and risk tolerance.
- MT5 must be installed and logged in on the machine running the bot.
- News filtering is optional but recommended during high-impact releases.
