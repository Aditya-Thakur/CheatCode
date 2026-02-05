import yfinance as yf

def scan_stock(symbol, cfg):
    try:
        t = yf.Ticker(symbol)
        hist = t.history(period="15d")

        if len(hist) < 5:
            return None

        close = hist["Close"]
        volume = hist["Volume"]

        price = close.iloc[-1]
        prev_close = close.iloc[-2]
        prev_high = hist["High"].iloc[-2]

        pct_change = ((price - prev_close) / prev_close) * 100

        momentum = (
            pct_change >= cfg["min_gain_pct"] or
            price > prev_high
        )

        avg_vol = volume.tail(10).mean()
        rvol = volume.iloc[-1] / avg_vol if avg_vol else 0

        if not momentum:
            signal = "WAIT"
        elif rvol >= cfg["min_rvol"]:
            signal = "BUY"
        else:
            signal = "WAIT"

        return {
            "symbol": symbol,
            "price": round(price, 2),
            "pct_change": round(pct_change, 2),
            "rvol": round(rvol, 2),
            "signal": signal
        }
        

    except Exception:
        return None
