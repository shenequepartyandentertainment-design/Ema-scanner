import os
import requests
import yfinance as yf

WEBHOOK = os.environ["DISCORD_WEBHOOK_URL"]
INTERVAL = os.getenv("INTERVAL", "15m")
PERIOD = "10d" if INTERVAL != "1d" else "6mo"

with open("watchlist.txt") as f:
    tickers = [t.strip().upper() for t in f if t.strip()]

alerts = []
for t in tickers:
    try:
        df = yf.Ticker(t).history(period=PERIOD, interval=INTERVAL)
        if len(df) < 30:
            continue
        df = df.iloc[:-1]  # drop unfinished candle
        df["ema9"] = df["Close"].ewm(span=9, adjust=False).mean()
        df["ema21"] = df["Close"].ewm(span=21, adjust=False).mean()
        prev, now = df.iloc[-2], df.iloc[-1]
        price = now["Close"]
        if prev["ema9"] <= prev["ema21"] and now["ema9"] > now["ema21"]:
            alerts.append(f"🟢 **{t}** BULLISH (Calls) - 9 EMA crossed ABOVE 21 EMA @ ${price:.2f}")
        elif prev["ema9"] >= prev["ema21"] and now["ema9"] < now["ema21"]:
            alerts.append(f"🔴 **{t}** BEARISH (Puts) - 9 EMA crossed BELOW 21 EMA @ ${price:.2f}")
    except Exception as e:
        print(f"{t}: {e}")

if alerts:
    msg = f"📊 **EMA Scanner ({INTERVAL})**\n" + "\n".join(alerts)
    requests.post(WEBHOOK, json={"content": msg}, timeout=10)
    print(msg)
else:
    print("No crossovers this run.")
