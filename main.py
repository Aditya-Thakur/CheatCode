import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from scanner import scan_stock
from allocator import allocate_trades

app = FastAPI()

# ------------------------------------------------------
# Load config & universe once at startup
# ------------------------------------------------------

with open("config.json") as f:
    cfg = json.load(f)

with open("universe.json") as f:
    UNIVERSE = json.load(f)

# ------------------------------------------------------
# WebSocket Scanner
# ------------------------------------------------------

@app.websocket("/ws/scan")
async def scan_market(ws: WebSocket):
    await ws.accept()
    print("✅ WebSocket client connected")

    try:
        while True:
            scanned = []

            total = len(UNIVERSE)

            for i, symbol in enumerate(UNIVERSE, start=1):
                # 1️⃣ Send status update (AI-like thinking)
                await ws.send_json({
                    "type": "status",
                    "message": f"Scanning {symbol} ({i}/{total})"
                })

                # 2️⃣ Scan stock
                data = scan_stock(symbol, cfg)

                if data:
                    scanned.append(data)

                    # 3️⃣ Send stock update IMMEDIATELY
                    await ws.send_json({
                        "type": "stock_update",
                        "symbol": data["symbol"],
                        "price": data["price"],
                        "pct_change": data["pct_change"],
                        "rvol": data["rvol"],
                        "signal": data["signal"]
                    })

                # Small delay so UI can breathe
                await asyncio.sleep(0.15)

            # 4️⃣ Allocate capital to BUY signals
            allocations = allocate_trades(scanned, cfg)

            # 5️⃣ Send final summary
            await ws.send_json({
                "type": "summary",
                "total_capital": cfg["total_capital"],
                "suggested_trades": allocations
            })

            # Pause before next full scan cycle
            await asyncio.sleep(10)

    except WebSocketDisconnect:
        print("❌ WebSocket client disconnected")

    except Exception as e:
        print(f"🔥 WebSocket error: {e}")
        await ws.close()
