def evaluate_symbol(symbol: str):
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="30d")

        if len(hist) < 20:
            return None

        info = ticker.info or {}
        news = ticker.news or []

        # -------------------------
        # PRICE & % GAIN
        # -------------------------
        price = hist["Close"].iloc[-1]
        prev_close = hist["Close"].iloc[-2]
        pct_change = ((price - prev_close) / prev_close) * 100

        if pct_change < 10:
            return None  # Warrior: must already be moving

        # -------------------------
        # RELATIVE VOLUME (>= 5x)
        # -------------------------
        avg_vol_30d = hist["Volume"].mean()
        today_vol = hist["Volume"].iloc[-1]
        rvol = today_vol / avg_vol_30d if avg_vol_30d else 0

        if rvol < 5:
            return None

        # -------------------------
        # FLOAT FILTER (< 10M)
        # -------------------------
        float_shares = info.get("floatShares") or info.get("sharesOutstanding")
        if float_shares and float_shares > 10_000_000:
            return None

        # -------------------------
        # PRICE RANGE (Warrior preference)
        # -------------------------
        if not (1 <= price <= 20):
            # allowed ONLY if momentum is extreme
            if pct_change < 20:
                return None

        # -------------------------
        # NEWS CATALYST (REQUIRED)
        # -------------------------
        if not news:
            return None

        headline = news[0].get("title", "")[:70] + "..."

        # -------------------------
        # ALERT
        # -------------------------
        alert_if_allowed(
            symbol,
            f"+{round(pct_change,2)}% | RVOL {round(rvol,1)}x | Price {round(price,2)}"
        )

        return {
            "symbol": symbol,
            "status": "[bold green]WARRIOR SETUP[/bold green]",
            "price": round(price, 2),
            "change": round(pct_change, 2),
            "rvol": round(rvol, 2),
            "float": f"{round(float_shares / 1e6, 1)}M" if float_shares else "N/A",
            "news": headline
        }

    except Exception:
        return None
