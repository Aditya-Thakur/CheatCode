import time
import os
import yfinance as yf
from rich.live import Live
from rich.table import Table
from rich.console import Console
from plyer import notification

# =========================
# CONFIG
# =========================
WATCHLIST = [
    "SUZLON.NS", "IREDA.NS", "ZOMATO.NS",
    "RVNL.NS", "NBCC.NS", "SJVN.NS", "YESBANK.NS"
]

CHECK_INTERVAL = 60  # seconds
PRICE_MIN = 50
PRICE_MAX = 1700
MIN_GAIN_PCT = 10.0
MIN_RVOL = 5.0
ALERT_COOLDOWN = 300  # seconds

console = Console()
_last_alert_time = {}

# =========================
# ALERT SYSTEM (NON-BLOCKING)
# =========================
def notify(symbol: str, message: str):
    notification.notify(
        title=f"🚨 Warrior STRIKE: {symbol}",
        message=message,
        timeout=5
    )

def alert_if_allowed(symbol: str, message: str):
    now = time.time()
    last = _last_alert_time.get(symbol, 0)
    if now - last >= ALERT_COOLDOWN:
        notify(symbol, message)
        _last_alert_time[symbol] = now

# =========================
# DATA HELPERS
# =========================
def get_latest_news(symbol: str) -> str:
    try:
        news = yf.Ticker(symbol).news
        if news:
            return news[0].get("title", "")[:60] + "..."
    except Exception:
        pass
    return ""

def fetch_market_data(symbol: str):
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period="30d")
    if len(hist) < 2:
        return None

    info = ticker.info or {}
    float_shares = info.get("floatShares", info.get("sharesOutstanding", 0))

    price = hist["Close"].iloc[-1]
    prev_close = hist["Close"].iloc[-2]
    change_pct = ((price - prev_close) / prev_close) * 100

    avg_vol = hist["Volume"].mean()
    current_vol = hist["Volume"].iloc[-1]
    rvol = current_vol / avg_vol if avg_vol else 0

    return {
        "price": round(price, 2),
        "change": round(change_pct, 2),
        "rvol": round(rvol, 2),
        "float": f"{round(float_shares / 1e6, 1)}M"
    }

# =========================
# STRATEGY LOGIC
# =========================
def evaluate_symbol(symbol: str):
    try:
        data = fetch_market_data(symbol)
        if not data:
            return None

        strike = (
            data["change"] >= MIN_GAIN_PCT and
            data["rvol"] >= MIN_RVOL and
            PRICE_MIN <= data["price"] <= PRICE_MAX
        )

        status = "[bold green]STRIKE[/bold green]" if strike else "[yellow]Scanning[/yellow]"
        news = ""

        if strike:
            news = get_latest_news(symbol)
            alert_if_allowed(
                symbol,
                f"Price ₹{data['price']} | +{data['change']}% | RVOL {data['rvol']}x"
            )

        return {
            "symbol": symbol,
            "status": status,
            "news": news,
            **data
        }

    except Exception:
        return None

# =========================
# DASHBOARD
# =========================
def generate_dashboard() -> Table:
    table = Table(
        title=f"⚔️ Warrior Strategy Scanner — {time.strftime('%H:%M:%S')}"
    )

    table.add_column("Symbol", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Price", justify="right")
    table.add_column("% Change", justify="right", style="green")
    table.add_column("RVOL", justify="right", style="magenta")
    table.add_column("Float", justify="right")
    table.add_column("News Catalyst", overflow="fold")
    table.add_column("Target (2%)", justify="right", style="bold green")

    for symbol in WATCHLIST:
        stats = evaluate_symbol(symbol)
        if not stats:
            continue

        target = round(stats["price"] * 1.02, 2)

        table.add_row(
            stats["symbol"],
            stats["status"],
            str(stats["price"]),
            f"{stats['change']}%",
            f"{stats['rvol']}x",
            stats["float"],
            stats["news"],
            str(target)
        )

    return table

# =========================
# MAIN LOOP
# =========================
with Live(generate_dashboard(), refresh_per_second=0.2) as live:
    while True:
        live.update(generate_dashboard())
        time.sleep(CHECK_INTERVAL)
