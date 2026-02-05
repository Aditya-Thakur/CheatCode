import math

def allocate_trades(trades, cfg):
    buys = [t for t in trades if t["signal"] == "BUY"]
    max_positions = cfg["max_positions"]

    selected = buys[:max_positions]
    allocations = []

    if not selected:
        return []

    capital_per_trade = min(
        cfg["max_trade_value"],
        cfg["total_capital"] / len(selected)
    )

    for trade in selected:
        value = max(cfg["min_trade_value"], capital_per_trade)
        qty = math.floor(value / trade["price"])

        if qty <= 0:
            continue

        allocations.append({
            **trade,
            "trade_value": round(qty * trade["price"], 2),
            "quantity": qty,
            "action": "BUY"
        })

    return allocations
