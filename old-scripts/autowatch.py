import time
import yfinance as yf
from rich.live import Live
from rich.table import Table
from rich.console import Console
from plyer import notification

# ======================================================
# CONFIGURATION
# ======================================================

# NSE universe (expand anytime – 100–300 stocks ideal)
UNIVERSE = [
# PSU / Infra / Rail / Power
"RVNL.NS","IRFC.NS","IRCON.NS","NBCC.NS","HUDCO.NS","NHPC.NS","SJVN.NS",
"NTPC.NS","POWERGRID.NS","RECLTD.NS","PFC.NS","IOB.NS","PNB.NS",
"CANBK.NS","BANKBARODA.NS","UCOBANK.NS","CENTRALBK.NS","INDIANB.NS",

# Energy / Metals
"ADANIPOWER.NS","TATASTEEL.NS","JSWSTEEL.NS","SAIL.NS",
"HINDALCO.NS","COALINDIA.NS","ONGC.NS","OIL.NS","IOC.NS","BPCL.NS",
"GAIL.NS","PETRONET.NS","VEDL.NS","NMDC.NS",

# Financials / NBFC
"YESBANK.NS","IDFCFIRSTB.NS","IDBI.NS","FEDERALBNK.NS","RBLBANK.NS",
"AUBANK.NS","BANDHANBNK.NS","SBIN.NS","LICHSGFIN.NS","MUTHOOTFIN.NS",
"MANAPPURAM.NS","IRCTC.NS",

# Auto / EV / Ancillaries
"TMPV.NS","ASHOKLEY.NS","TVSMOTOR.NS","EICHERMOT.NS",
"SONACOMS.NS","MOTHERSON.NS","EXIDEIND.NS",
"OLECTRA.NS",

# IT / Tech / New Age
"ETERNAL.NS","PAYTM.NS","NYKAA.NS","DELHIVERY.NS","INFIBEAM.NS",
"TATAELXSI.NS","COFORGE.NS","LTTS.NS",

# Defence / Manufacturing
"HAL.NS","BEL.NS","BDL.NS","MAZDOCK.NS","COCHINSHIP.NS",
"GRSE.NS","BEML.NS",

# Pharma / Chemicals
"IDEA.NS","BIOCON.NS","GLENMARK.NS","SUNPHARMA.NS","CIPLA.NS",
"ALKEM.NS","DIVISLAB.NS","LUPIN.NS","AUROPHARMA.NS",
"DEEPAKNTR.NS","SRF.NS","ATUL.NS","TATACHEM.NS",

# FMCG / Consumption
"ITC.NS","HINDUNILVR.NS","DABUR.NS","MARICO.NS","GODREJCP.NS",
"BRITANNIA.NS","COLPAL.NS","VBL.NS","UBL.NS",

# Small-cap Momentum Favorites
"SUZLON.NS","IREDA.NS","ETERNAL.NS","HFCL.NS","IRB.NS",
"JPPOWER.NS","TRIDENT.NS","RPOWER.NS","ADANIGREEN.NS","ADANIENSOL.NS","ADANIPORTS.NS",

# Realty / Infra
"DLF.NS","LODHA.NS","OBEROIRLTY.NS","PRESTIGE.NS","GODREJPROP.NS",
"PHOENIXLTD.NS","BRIGADE.NS"
]


SCANNER_MODE = "INTRADAY"  # PREMARKET | INTRADAY
MAX_WATCHLIST = 10
CHECK_INTERVAL = 60
ALERT_COOLDOWN = 300

# Warrior rules
MIN_GAP_PCT = 5
MIN_GAIN_PCT = 10
MIN_RVOL = 5
PRICE_MIN = 10        # adjusted for NSE sanity
PRICE_MAX = 500
MAX_FLOAT = 10_000_000

console = Console()
_last_alert_time = {}

# ======================================================
# ALERT SYSTEM
# ======================================================

def notify(symbol, message):
    notification.notify(
        title=f"⚔️ Warrior Alert: {symbol}",
        message=message,
        timeout=5
    )

def alert_if_allowed(symbol, message):
    now = time.time()
    last = _last_alert_time.get(symbol, 0)
    if now - last >= ALERT_COOLDOWN:
        notify(symbol, message)
        _last_alert_time[symbol] = now

# ======================================================
# INTRADAY SCANNER
# ======================================================

def scan_intraday(symbol):
    try:
        t = yf.Ticker(symbol)
        hist = t.history(period="30d")
        if len(hist) < 20:
            return None

        info = t.info or {}
        news = t.news or []

        price = hist["Close"].iloc[-1]
        prev_close = hist["Close"].iloc[-2]
        pct = ((price - prev_close) / prev_close) * 100

        if pct < MIN_GAIN_PCT:
            return None

        avg_vol = hist["Volume"].mean()
        rvol = hist["Volume"].iloc[-1] / avg_vol if avg_vol else 0
        if rvol < MIN_RVOL:
            return None

        float_shares = info.get("floatShares") or info.get("sharesOutstanding")
        if float_shares and float_shares > MAX_FLOAT:
            return None

        if not (PRICE_MIN <= price <= PRICE_MAX) and pct < 20:
            return None

        has_news = bool(news)

        alert_if_allowed(
            symbol,
            f"+{pct:.2f}% | RVOL {rvol:.1f}x | ₹{price:.2f}"
        )

        return {
            "symbol": symbol,
            "status": "[bold green]INTRADAY[/bold green]",
            "price": round(price, 2),
            "change": round(pct, 2),
            "rvol": round(rvol, 2),
            "float": f"{round(float_shares / 1e6,1)}M" if float_shares else "N/A",
            "news": news[0]["title"][:70] + "..."
        }

    except Exception:
        return None

# ======================================================
# PRE-MARKET SCANNER
# ======================================================

def scan_premarket(symbol):
    try:
        t = yf.Ticker(symbol)
        hist = t.history(period="5d")
        if len(hist) < 2:
            return None

        info = t.info or {}
        news = t.news or []

        prev_close = hist["Close"].iloc[-2]
        price = hist["Close"].iloc[-1]
        gap = ((price - prev_close) / prev_close) * 100

        if gap < MIN_GAP_PCT:
            return None

        if not (PRICE_MIN <= price <= PRICE_MAX):
            return None

        float_shares = info.get("floatShares") or info.get("sharesOutstanding")
        if float_shares and float_shares > MAX_FLOAT:
            return None

        has_news = bool(news)

        alert_if_allowed(
            symbol,
            f"PRE-MKT GAP +{gap:.2f}% | ₹{price:.2f}"
        )

        return {
            "symbol": symbol,
            "status": "[bold cyan]PRE-MKT[/bold cyan]",
            "price": round(price, 2),
            "change": round(gap, 2),
            "rvol": "—",
            "float": f"{round(float_shares / 1e6,1)}M" if float_shares else "N/A",
            "news": news[0]["title"][:70] + "..."
        }

    except Exception:
        return None

# ======================================================
# AUTO WATCHLIST BUILDER
# ======================================================

def build_watchlist():
    results = []

    for symbol in UNIVERSE:
        data = (
            scan_premarket(symbol)
            if SCANNER_MODE == "PREMARKET"
            else scan_intraday(symbol)
        )
        if data:
            results.append(data)

    # Warrior focuses on TOP gainers only
    results.sort(key=lambda x: x["change"], reverse=True)

    return results[:MAX_WATCHLIST]

# ======================================================
# DASHBOARD
# ======================================================

def generate_dashboard():
    table = Table(
        title=f"⚔️ Warrior Auto-Watchlist — {SCANNER_MODE} — {time.strftime('%H:%M:%S')}"
    )

    table.add_column("Symbol", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Price", justify="right")
    table.add_column("%", justify="right", style="green")
    table.add_column("RVOL", justify="right")
    table.add_column("Float", justify="right")
    table.add_column("News", overflow="fold")
    table.add_column("Target +2%", justify="right", style="bold green")

    watchlist = build_watchlist()

    for s in watchlist:
        target = round(s["price"] * 1.02, 2)
        table.add_row(
            s["symbol"],
            s["status"],
            str(s["price"]),
            f"{s['change']}%",
            str(s["rvol"]),
            s["float"],
            s["news"],
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
