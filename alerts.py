import time
import sys

_last_alert = {}

def notify(symbol, message, cooldown=300):
    """
    Safe alert system:
    - Tries OS notification
    - Falls back to terminal alert
    - Never crashes the scanner
    """

    now = time.time()
    last = _last_alert.get(symbol, 0)

    if now - last < cooldown:
        return

    alerted = False

    # Try OS notification (best effort)
    try:
        from plyer import notification
        notification.notify(
            title=f"⚔️ Warrior Alert: {symbol}",
            message=message,
            timeout=5
        )
        alerted = True
    except Exception:
        pass  # silently fail

    # Terminal fallback (ALWAYS works)
    if not alerted:
        print(f"\n🚨 ALERT → {symbol}: {message}\n", file=sys.stderr)

    _last_alert[symbol] = now