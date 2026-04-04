import yfinance as yf
import pandas as pd
import time
from datetime import datetime
import requests

# ==========================================
# 🛑 PASTE YOUR TELEGRAM CREDENTIALS HERE 🛑
# ==========================================
TELEGRAM_TOKEN = "8792463504:AAFgMsp66g6d4MrJuCscLZDh1Mik4CwkTvs" 
TELEGRAM_CHAT_ID = "5549364804"
# ==========================================

# Only monitoring EUR/USD
ASSETS = {"EURUSD=X": "EUR/USD"}
last_alerted_time = {"EURUSD=X": None}

def send_telegram_alert(message):
    """Sends a message to your Telegram app."""
    # If you haven't set up the token yet, just print to console
    if TELEGRAM_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("⚠️ Telegram Token not set. Please add it to receive messages on your phone.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            print(f"Telegram error: {response.text}")
    except Exception as e:
        print(f"Failed to connect to Telegram: {e}")

def check_market_conditions():
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking EUR/USD...")
    
    for ticker, name in ASSETS.items():
        try:
            # Download live 1-hour data
            df = yf.download(ticker, period="30d", interval="1h", progress=False)
            
            if df.empty:
                print("Failed to fetch data.")
                continue
                
            # Clean Columns
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [col[0].lower() for col in df.columns]
            else:
                df.columns = [c.lower() for c in df.columns]

            # Calculate Indicators
            df['weekly_h'] = df['high'].resample('W').max().reindex(df.index).ffill().bfill()
            df['weekly_l'] = df['low'].resample('W').min().reindex(df.index).ffill().bfill()
            df['daily_h'] = df['high'].resample('D').max().reindex(df.index).ffill().bfill()
            df['daily_l'] = df['low'].resample('D').min().reindex(df.index).ffill().bfill()
            
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            df['rsi'] = 100 - (100 / (1 + (gain / loss)))
            
            # Get the current live candle
            curr = df.iloc[-1]
            candle_time = curr.name

            # Skip if we already alerted you for this specific candle
            if candle_time == last_alerted_time[ticker]:
                continue
            
            # --- STRATEGY LOGIC ---
            is_at_support = (curr['low'] <= curr['weekly_l'] or curr['low'] <= curr['daily_l'])
            is_at_resist  = (curr['high'] >= curr['weekly_h'] or curr['high'] >= curr['daily_h'])
            
            # Bullish Setup
            if is_at_support and curr['close'] > curr['open'] and curr['rsi'] < 35:
                msg = (f"🟢 *BULLISH REVERSAL SETUP*\n\n"
                       f"Asset: *{name}*\n"
                       f"Price: `{curr['close']:.4f}`\n"
                       f"RSI: `{curr['rsi']:.1f}`\n\n"
                       f"💡 _Target 1:2.5 RRR. Ensure stop-loss is placed below the recent wick._")
                
                print("🚨 BULLISH ALERT TRIGGERED!")
                send_telegram_alert(msg)
                last_alerted_time[ticker] = candle_time

            # Bearish Setup
            elif is_at_resist and curr['close'] < curr['open'] and curr['rsi'] > 65:
                msg = (f"🔴 *BEARISH REVERSAL SETUP*\n\n"
                       f"Asset: *{name}*\n"
                       f"Price: `{curr['close']:.4f}`\n"
                       f"RSI: `{curr['rsi']:.1f}`\n\n"
                       f"💡 _Target 1:2.5 RRR. Ensure stop-loss is placed above the recent wick._")
                
                print("🚨 BEARISH ALERT TRIGGERED!")
                send_telegram_alert(msg)
                last_alerted_time[ticker] = candle_time

        except Exception as e:
            print(f"Error processing {name}: {e}")

def start_screener():
    print("=====================================================")
    print("🤖 EUR/USD TELEGRAM SCREENER ONLINE")
    print("Waiting for Weekly/Daily level rejections...")
    print("=====================================================")
    
    # Send test message to confirm connection
    send_telegram_alert("🤖 *Bot Online!* I am now monitoring EUR/USD for Turning Points. I will message you when a setup occurs.")
    
    while True:
        check_market_conditions()
        # Wait 15 minutes before checking again
        time.sleep(900)

if __name__ == "__main__":
    start_screener()