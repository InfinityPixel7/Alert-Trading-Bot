import os
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime

# Pulls tokens from GitHub Secrets
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def main():
    ticker = "EURUSD=X"
    df = yf.download(ticker, period="30d", interval="1h", progress=False)
    
    # Flatten columns
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0].lower() for c in df.columns]
    else:
        df.columns = [c.lower() for c in df.columns]

    # Institutional Levels
    wh = df['high'].resample('W').max().ffill().bfill().iloc[-1]
    wl = df['low'].resample('W').min().ffill().bfill().iloc[-1]
    dh = df['high'].resample('D').max().ffill().bfill().iloc[-1]
    dl = df['low'].resample('D').min().ffill().bfill().iloc[-1]
    
    # RSI
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['rsi'] = 100 - (100 / (1 + (gain / loss)))
    
    curr = df.iloc[-1]
    price = curr['close']
    rrr = 2.5
    buffer = 0.0010
    
    # Bullish Setup
    is_at_support = (curr['low'] <= wl or curr['low'] <= dl)
    if is_at_support and curr['close'] > curr['open'] and curr['rsi'] < 35:
        sl = curr['low'] - buffer
        tp = price + ((price - sl) * rrr)
        send_telegram_alert(
            f"🟢 *BULLISH REVERSAL SETUP (EUR/USD)*\n"
            f"Entry: `{price:.5f}`\n"
            f"Stop Loss: `{sl:.5f}`\n"
            f"Take Profit: `{tp:.5f}`\n"
            f"RSI: `{curr['rsi']:.1f}`\n\n"
            f"💡 *Action:* Open Long on MT5"
        )
    
    # Bearish Setup
    is_at_resist = (curr['high'] >= wh or curr['high'] >= dh)
    if is_at_resist and curr['close'] < curr['open'] and curr['rsi'] > 65:
        sl = curr['high'] + buffer
        tp = price - ((sl - price) * rrr)
        send_telegram_alert(
            f"🔴 *BEARISH REVERSAL SETUP (EUR/USD)*\n"
            f"Entry: `{price:.5f}`\n"
            f"Stop Loss: `{sl:.5f}`\n"
            f"Take Profit: `{tp:.5f}`\n"
            f"RSI: `{curr['rsi']:.1f}`\n\n"
            f"💡 *Action:* Open Short on MT5"
        )

if __name__ == "__main__":
    main()