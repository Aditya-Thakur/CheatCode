from scanner import scan_intraday

def build_watchlist(universe, cfg, verbose=True):
    results = []
    total = len(universe)

    for i, symbol in enumerate(universe, start=1):
        print(f"🔍 [{i}/{total}] Scanning {symbol}...", end=" ")

        data, reason = scan_intraday(symbol, cfg)

        if data:
            print("✅ QUALIFIED")
            results.append(data)
        else:
            print(f"❌ {reason}")

    results.sort(key=lambda x: x["change"], reverse=True)
    return results[:cfg["max_watchlist"]]
