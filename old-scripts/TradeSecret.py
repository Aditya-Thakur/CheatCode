import yfinance as yf
import pandas_ta as ta
import time
import os
from plyer import notification
from rich.live import Live
from rich.table import Table
from rich.console import Console

def notify(title, message):
    notification.notify(
        title=title,
        message=message,
        timeout=5  # seconds
    )

# --- CONFIGURATION ---
SYMBOLS = ["TATAMOTORS.NS", "RELIANCE.NS", "INFY.NS", "HDFCBANK.NS", "TCS.NS"]
CHECK_INTERVAL = 60  # Seconds
ALARM_FILE = "alert.mp3"  # Ensure this file exists in your directory

console = Console()

def get_signal(symbol):
    try:
        # Fetch intraday 5m data
        df = yf.download(tickers=symbol, period='2d', interval='5m', progress=False)
        if df.empty or len(df) < 200: 
            return "Insufficient Data", 0, 0, 0
        
        # Calculate Indicators
        df['VWAP'] = ta.vwap(df.High, df.Low, df.Close, df.Volume)
        df['EMA200'] = ta.ema(df.Close, length=200)
        
        # Current Values
        last_row = df.iloc[-1]
        price = round(float(last_row['Close']), 2)
        vwap = round(float(last_row['VWAP']), 2)
        ema = round(float(last_row['EMA200']), 2)
        
        # Signal Logic: Price > VWAP and Price > EMA200
        if price > vwap and price > ema:
            status = "[bold green]BUY SIGNAL[/bold green]"
            # Only play sound if it's a fresh signal (logic can be expanded here)
            if os.path.exists(ALARM_FILE):
                playsound(ALARM_FILE, block=False)
        elif price < vwap and price < ema:
            status = "[bold red]SELL SIGNAL[/bold red]"
        else:
            status = "[yellow]Neutral[/yellow]"
            
        return status, price, vwap, ema
    except Exception as e:
        return f"[red]Error: {str(e)[:10]}[/red]", 0, 0, 0

def generate_table() -> Table:
    table = Table(title=f"Live Trading Dashboard - {time.strftime('%H:%M:%S')}")
    table.add_column("Symbol", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Price", justify="right")
    table.add_column("VWAP", justify="right", style="magenta")
    table.add_column("Stop Loss (1%)", justify="right", style="red")
    table.add_column("Target (2%)", justify="right", style="green")

    for symbol in SYMBOLS:
        status, price, vwap, ema = get_signal(symbol)
        sl = round(price * 0.99, 2) if price > 0 else 0
        tp = round(price * 1.02, 2) if price > 0 else 0
        table.add_row(symbol, status, str(price), str(vwap), str(sl), str(tp))
    
    return table

# --- MAIN LOOP ---
console.print("[bold cyan]Starting Live Monitor...[/bold cyan]")
with Live(generate_table(), refresh_per_second=0.1) as live:
    while True:
        live.update(generate_table())
        time.sleep(CHECK_INTERVAL)
