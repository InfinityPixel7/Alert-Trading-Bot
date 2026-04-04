import os
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime

# Read from GitHub Secrets automatically
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def send_telegram_alert(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram credentials not found in environment.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def main():
    ticker = "EURUSD=X"
    print(f"[{datetime.now()}] Scanning {ticker}...")
    
    df = yf.download(ticker, period="30d", interval="1h", progress=False)
    
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0].lower() for col in df.columns]
    else:
        df.columns = [c.lower() for c in df.columns]

    df['weekly_h'] = df['high'].resample('W').max().reindex(df.index).ffill().bfill()
    df['weekly_l'] = df['low'].resample('W').min().reindex(df.index).ffill().bfill()
    df['daily_h'] = df['high'].resample('D').max().reindex(df.index).ffill().bfill()
    df['daily_l'] = df['low'].resample('D').min().reindex(df.index).ffill().bfill()
    
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['rsi'] = 100 - (100 / (1 + (gain / loss)))
    
    curr = df.iloc[-1]
    
    is_at_support = (curr['low'] <= curr['weekly_l'] or curr['low'] <= curr['daily_l'])
    is_at_resist  = (curr['high'] >= curr['weekly_h'] or curr['high'] >= curr['daily_h'])
    
    # Alert Logic
    if is_at_support and curr['close'] > curr['open'] and curr['rsi'] < 35:
        send_telegram_alert(f"🟢 *BULLISH SETUP EUR/USD*\nPrice: `{curr['close']:.4f}`\nRSI: `{curr['rsi']:.1f}`")
    elif is_at_resist and curr['close'] < curr['open'] and curr['rsi'] > 65:
        send_telegram_alert(f"🔴 *BEARISH SETUP EUR/USD*\nPrice: `{curr['close']:.4f}`\nRSI: `{curr['rsi']:.1f}`")
    else:
        print("No setup found.")

if __name__ == "__main__":
    main()