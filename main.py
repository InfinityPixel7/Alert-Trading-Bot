import yfinance as yf
import pandas as pd
import pandas_ta as ta
import requests
import time

# --- CONFIGURATION ---
SYMBOL = "GC=F" # Gold Futures (Use BTC-USD for Bitcoin, EURUSD=X for Euro)
TOKEN = "8792463504:AAFgMsp66g6d4MrJuCscLZDh1Mik4CwkTvs"
CHAT_ID = "5549364804"
RR_RATIO = 4
BIG_CANDLE_MULT = 1.2
EMA_PERIOD = 9
ZONE_THRESHOLD = 0.002 # 0.2% distance from weekly level

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}&parse_mode=Markdown"
    requests.get(url)

def get_data():
    # 1. Get Weekly Levels (HTF)
    weekly_data = yf.download(SYMBOL, period="2wk", interval="1wk")
    if len(weekly_data) < 2: return None
    
    last_week = weekly_data.iloc[-2] # The completed previous week
    w_high = last_week['High']
    w_low = last_week['Low']

    # 2. Get 15m Data (LTF)
    ltf_data = yf.download(SYMBOL, period="2d", interval="15m")
    ltf_data['ema'] = ta.ema(ltf_data['Close'], length=EMA_PERIOD)
    
    return ltf_data, w_high, w_low

def check_strategy():
    data, w_high, w_low = get_data()
    
    # Get last two completed 15m candles
    current = data.iloc[-1]
    prev = data.iloc[-2]
    lookback = data.iloc[-20:-1] # Look back 20 candles for the "Sweep"

    # Logic Variables
    body_size = abs(prev['Close'] - prev['Open'])
    avg_body = abs(data['Close'] - data['Open']).tail(10).mean()
    
    is_big_player = body_size > (avg_body * BIG_CANDLE_MULT)
    low_swept = any(lookback['Low'] < w_low)
    high_swept = any(lookback['High'] > w_high)

    # --- BUY SIGNAL ---
    # Low swept recently + Prev candle Bullish + Big Player + Above EMA
    if low_swept and prev['Close'] > prev['Open'] and is_big_player and prev['Close'] > prev['ema']:
        sl = prev['Low'] - (prev['Low'] * 0.001)
        risk = prev['Close'] - sl
        tp = prev['Close'] + (risk * RR_RATIO)
        
        msg = f"🚀 *BUY SIGNAL: {SYMBOL}*\nEntry: {prev['Close']:.2f}\nSL: {sl:.2f}\nTP: {tp:.2f}\nRRR: 1:{RR_RATIO}"
        send_telegram(msg)
        print("Buy Signal Sent")

    # --- SELL SIGNAL ---
    # High swept recently + Prev candle Bearish + Big Player + Below EMA
    elif high_swept and prev['Close'] < prev['Open'] and is_big_player and prev['Close'] < prev['ema']:
        sl = prev['High'] + (prev['High'] * 0.001)
        risk = sl - prev['Close']
        tp = prev['Close'] - (risk * RR_RATIO)
        
        msg = f"🔻 *SELL SIGNAL: {SYMBOL}*\nEntry: {prev['Close']:.2f}\nSL: {sl:.2f}\nTP: {tp:.2f}\nRRR: 1:{RR_RATIO}"
        send_telegram(msg)
        print("Sell Signal Sent")

if __name__ == "__main__":
    print("Bot is checking for Turning Points...")
    check_strategy()
