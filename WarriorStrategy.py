import yfinance as yf
import pandas_ta as ta
import time
import os
from playsound import playsound
from rich.live import Live
from rich.table import Table
from rich.console import Console

# --- CONFIG ---
# Added high-volatility Indian mid-caps that often fit "Warrior" criteria
WATCHLIST = ["SUZLON.NS", "IREDA.NS", "ZOMATO.NS", "RVNL.NS", "NBCC.NS", "SJVN.NS", "YESBANK.NS"]
CHECK_INTERVAL = 60 
ALARM_FILE = "alert.mp3"

console = Console()

def get_latest_news(symbol):
    """Fetches the most recent news headline for a symbol."""
    try:
        ticker = yf.Ticker(symbol)
        news = ticker.news
        if news:
            # Return the title of the most recent article
            return news[0]['title'][:50] + "..."
        return "No recent news found"
    except:
        return "News fetch error"

def get_warrior_stats(symbol):
    try:
        ticker = yf.Ticker(symbol)
        # 1. Supply Data (Float) - Note: yfinance float data for NSE can be spotty
        info = ticker.info
        float_shares = info.get('floatShares', info.get('sharesOutstanding', 0))
        
        # 2. Price/Volume Data
        hist = ticker.history(period='30d') 
        if len(hist) < 2: return None
        
        current_price = hist['Close'].iloc[-1]
        prev_close = hist['Close'].iloc[-2]
        day_change_pct = ((current_price - prev_close) / prev_close) * 100
        
        # 3. RVOL (Current Vol vs 30d Average)
        avg_vol_30d = hist['Volume'].mean()
        current_vol = hist['Volume'].iloc[-1]
        rvol = current_vol / avg_vol_30d
        
        # --- WARRIOR FILTERS ---
        # 10% gain, 5x Volume, Price under 1700 (Warrior's $20 cap)
        is_high_momentum = (day_change_pct >= 10.0) and (rvol >= 5.0)
        is_right_price = (50 <= current_price <= 1700) 
        
        status = "[bold green]STRIKE[/bold green]" if (is_high_momentum and is_right_price) else "[yellow]Scanning[/yellow]"
        
        news_headline = ""
        if status == "[bold green]STRIKE[/bold green]":
            news_headline = get_latest_news(symbol)
            if os.path.exists(ALARM_FILE):
                playsound(ALARM_FILE, block=False)

        return {
            "symbol": symbol,
            "status": status,
            "price": round(current_price, 2),
            "change": round(day_change_pct, 2),
            "rvol": round(rvol, 2),
            "float": f"{round(float_shares/1e6, 1)}M",
            "news": news_headline
        }
    except Exception:
        return None

def generate_dashboard() -> Table:
    table = Table(title=f"Warrior Strategy Scanner (News Integrated) - {time.strftime('%H:%M:%S')}")
    table.add_column("Symbol", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Price", justify="right")
    table.add_column("% Change", justify="right", style="green")
    table.add_column("RVOL", justify="right", style="magenta")
    table.add_column("News Catalyst", justify="left", style="white")
    table.add_column("Target (2:1)", justify="right", style="bold green")

    for symbol in WATCHLIST:
        stats = get_warrior_stats(symbol)
        if stats:
            tp = round(stats['price'] * 1.02, 2) # 2% Target based on 1% SL
            table.add_row(
                stats['symbol'], stats['status'], str(stats['price']), 
                f"{stats['change']}%", f"{stats['rvol']}x", stats['news'], str(tp)
            )
    return table

with Live(generate_dashboard(), refresh_per_second=0.05) as live:
    while True:
        live.update(generate_dashboard())
        time.sleep(CHECK_INTERVAL)
      
