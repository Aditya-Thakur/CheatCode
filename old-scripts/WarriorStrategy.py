import time
import yfinance as yf
from rich.live import Live
from rich.table import Table
from rich.console import Console
from plyer import notification

# ======================================================
# CONFIGURATION
# ======================================================

WATCHLIST = [
    "SUZLON.NS", "IREDA.NS", "ZOMATO.NS",
    "RVNL.NS", "NBCC.NS", "SJVN.NS", "YESBANK.NS"
]

SCANNER_MODE = "PREMARKET"  # PREMARKET | INTRADAY
CHECK_INTERVAL = 60  # seconds
ALERT_COOLDOWN = 300  # seconds

# Warrior Criteria
MIN_GAP_PCT = 5
MIN_GAIN_PCT = 10
MIN_RVOL = 5
PRICE_MIN = 1
PRICE_MAX = 20
MAX_FLOAT = 10_000_000

console = Console()
_last_alert_time = {}

# ======================================================
# ALERT SYSTEM (NON-BLOCKING)
# ======================================================

def notify(symbol: str, message: str):
    notification.notify(
        title=f"⚔️ Warrior Alert: {symbol}",
        message=message,
        timeout=5
    )

def alert_if_allowed(symbol: str, message: str):
    now = time.time()
    last = _last_alert_time.get(symbol, 0)
    if now - last >= ALERT_COOLDOWN:
        notify(symbol, message)
        _last_alert_time[symbol] = now

# ======================================================
# INTRADAY SCANNER (WARRIOR MOMENTUM)
# ======================================================

def evaluate_intraday(symbol: str):
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="30d")

        if len(hist) < 20:
            return None

        info = ticker.info or {}
        news = ticker.news or []

        price = hist["Close"].iloc[-1]
        prev_close = hist["Close"].iloc[-2]
        pct_change = ((price - prev_close) / prev_close) * 100

        if pct_change < MIN_GAIN_PCT:
            return None

        avg_vol = hist["Volume"].mean()
        today_vol = hist["Volume"].iloc[-1]
        rvol = today_vol / avg_vol if avg_vol else 0

        if rvol < MIN_RVOL:
            return None

        float_shares = info.get("floatShares") or info.get("sharesOutstanding")
        if float_shares and float_shares > MAX_FLOAT:
            return None

        if not (PRICE_MIN <= price <= PRICE_MAX) and pct_change < 20:
            return None

        if not news:
            return None

        headline = news[0].get("title", "")[:70] + "..."

        alert_if_allowed(
            symbol,
            f"+{pct_change:.2f}% | RVOL {rvol:.1f}x | ₹{price:.2f}"
        )

        return {
            "symbol": symbol,
            "status": "[bold green]WARRIOR[/bold green]",
            "price": round(price, 2),
            "change": round(pct_change, 2),
            "rvol": round(rvol, 2),
            "float": f"{round(float_shares / 1e6,1)}M" if float_shares else "N/A",
            "news": headline
        }

    except Exception:
        return None

# ======================================================
# PRE-MARKET SCANNER (GAP + CATALYST)
# ======================================================

def evaluate_premarket(symbol: str):
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="5d")

        if len(hist) < 2:
            return None

        info = ticker.info or {}
        news = ticker.news or []

        prev_close = hist["Close"].iloc[-2]
        current_price = hist["Close"].iloc[-1]
        gap_pct = ((current_price - prev_close) / prev_close) * 100

        if gap_pct < MIN_GAP_PCT:
            return None

        if not (PRICE_MIN <= current_price <= PRICE_MAX):
            return None

        float_shares = info.get("floatShares") or info.get("sharesOutstanding")
        if float_shares and float_shares > MAX_FLOAT:
            return None

        if not news:
            return None

        headline = news[0].get("title", "")[:70] + "..."

        alert_if_allowed(
            symbol,
            f"PRE-MKT GAP +{gap_pct:.2f}% | ₹{current_price:.2f}"
        )

        return {
            "symbol": symbol,
            "status": "[bold cyan]PRE-MKT[/bold cyan]",
            "price": round(current_price, 2),
            "change": round(gap_pct, 2),
            "rvol": "—",
            "float": f"{round(float_shares / 1e6,1)}M" if float_shares else "N/A",
            "news": headline
        }

    except Exception:
        return None

# ======================================================
# DASHBOARD
# ======================================================

def generate_dashboard():
    table = Table(
        title=f"⚔️ Warrior Strategy — {SCANNER_MODE} Scanner — {time.strftime('%H:%M:%S')}"
    )

    table.add_column("Symbol", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Price", justify="right")
    table.add_column("% Change", justify="right", style="green")
    table.add_column("RVOL", justify="right", style="magenta")
    table.add_column("Float", justify="right")
    table.add_column("News Catalyst", overflow="fold")
    table.add_column("Target (2%)", justify="right", style="bold green")

    results = []

    for symbol in WATCHLIST:
        stats = (
            evaluate_premarket(symbol)
            if SCANNER_MODE == "PREMARKET"
            else evaluate_intraday(symbol)
        )

        if stats:
            results.append(stats)

    # Sort by % change (Warrior focuses on top gainers)
    results.sort(key=lambda x: x["change"], reverse=True)

    for stats in results[:5]:
        target = round(stats["price"] * 1.02, 2)

        table.add_row(
            stats["symbol"],
            stats["status"],
            str(stats["price"]),
            f"{stats['change']}%",
            str(stats["rvol"]),
            stats["float"],
            stats["news"],
            str(target)
        )

    return table

# ======================================================
# MAIN LOOP
# ======================================================

with Live(generate_dashboard(), refresh_per_second=0.2) as live:
    while True:
        live.update(generate_dashboard())
        time.sleep(CHECK_INTERVAL)
