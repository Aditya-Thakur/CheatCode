import yfinance as yf
import pandas_ta as ta
import time
import os
from playsound import playsound
from rich.live import Live
from rich.table import Table
from rich.console import Console

# --- DYNAMIC SCANNING CONFIG ---
# For India, you might use a list of volatile mid/small caps or Nifty Next 50
WATCHLIST = ["TATAMOTORS.NS", "ZOMATO.NS", "SUZLON.NS", "IREDA.NS", "RVNL.NS", "HUDCO.NS", "JWL.NS"]
CHECK_INTERVAL = 60 
ALARM_FILE = "alert.mp3"

console = Console()

def get_warrior_stats(symbol):
    try:
        ticker = yf.Ticker(symbol)
        # 1. Fetch Supply Data (Float)
        info = ticker.info
        float_shares = info.get('floatShares', 0)
        
        # 2. Fetch Demand Data (Price and Volume)
        hist = ticker.history(period='30d') # 30 days for RVOL calculation
        if len(hist) < 30: return None
        
        current_price = hist['Close'].iloc[-1]
        prev_close = hist['Close'].iloc[-2]
        day_change_pct = ((current_price - prev_close) / prev_close) * 100
        
        # 3. Calculate Relative Volume (RVOL)
        avg_vol_30d = hist['Volume'].mean()
        current_vol = hist['Volume'].iloc[-1]
        rvol = current_vol / avg_vol_30d
        
        # --- APPLY WARRIOR FILTERS ---
        is_high_demand = (day_change_pct >= 10.0) and (rvol >= 5.0)
        is_low_supply = (float_shares < 100_000_000) # Adjusted for NSE liquidity
        is_right_price = (80 <= current_price <= 1700) # $1-$20 equivalent
        
        status = "[bold green]STRIKE[/bold green]" if (is_high_demand and is_right_price) else "[yellow]Scanning[/yellow]"
        
        if status == "[bold green]STRIKE[/bold green]" and os.path.exists(ALARM_FILE):
            playsound(ALARM_FILE, block=False)

        return {
            "symbol": symbol,
            "status": status,
            "price": round(current_price, 2),
            "change": round(day_change_pct, 2),
            "rvol": round(rvol, 2),
            "float": f"{round(float_shares/1e6, 2)}M" if float_shares else "N/A"
        }
    except Exception:
        return None

def generate_dashboard() -> Table:
    table = Table(title=f"Warrior Scanner (High Momentum) - {time.strftime('%H:%M:%S')}")
    table.add_column("Symbol", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Price", justify="right")
    table.add_column("% Change", justify="right", style="green")
    table.add_column("RVOL (5x Min)", justify="right", style="magenta")
    table.add_column("Float", justify="right")
    table.add_column("Stop Loss (0.5%)", justify="right", style="red")
    table.add_column("Target (1.0%)", justify="right", style="bold green")

    for symbol in WATCHLIST:
        stats = get_warrior_stats(symbol)
        if stats:
            # Warrior strategy uses tight stops for high-volatility breakouts
            sl = round(stats['price'] * 0.995, 2) 
            tp = round(stats['price'] * 1.01, 2) # 2:1 Ratio
            table.add_row(
                stats['symbol'], stats['status'], str(stats['price']), 
                f"{stats['change']}%", str(stats['rvol']), stats['float'],
                str(sl), str(tp)
            )
    return table

with Live(generate_dashboard(), refresh_per_second=0.05) as live:
    while True:
        live.update(generate_dashboard())
        time.sleep(CHECK_INTERVAL)
