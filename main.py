import json
import asyncio
import importlib
import os
import pandas as pd
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
# Dynamic Strategy Loading
# ------------------------------------------------------

def load_strategy(strategy_name):
    """
    Dynamically load strategy class based on strategy name
    """
    try:
        # Mapping of display names to actual file names
        strategy_name_map = {
            "Opening Range Breakout (ORB)": "orb_strategy",
            "Mean Reversion": "mean_reversion_strategy",
            "MACD Crossover": "macd_strategy",
            "Gap and Go": "gap_and_go",
            "VWAP Pullback": "vwap_strategy",
            "Bull Flag Momentum": "bull_flag_strategy"
        }
        
        # Get the correct filename
        filename = strategy_name_map.get(strategy_name)
        
        if not filename:
            print(f"No mapping found for strategy: {strategy_name}")
            return None

        # Dynamically import the module
        module = importlib.import_module(f"strategies.{filename}")
        
        # Dynamically get the strategy class name 
        # Convert filename to PascalCase and append 'Strategy'
        strategy_class_name = ''.join(word.capitalize() for word in filename.replace('_', ' ').split()) + 'Strategy'
        
        # Get the strategy class from the module
        strategy_class = getattr(module, strategy_class_name)
        
        return strategy_class
    except (ImportError, AttributeError) as e:
        print(f"Error loading strategy {strategy_name}: {e}")
        return None

def get_strategies_info():
    """
    Read strategy details from strategies.json
    """
    with open("strategies/strategies.json") as f:
        return json.load(f)['strategies']

# ------------------------------------------------------
# WebSocket Scanner
# ------------------------------------------------------

@app.websocket("/ws/scan")
async def scan_market(ws: WebSocket):
    await ws.accept()
    print("✅ WebSocket client connected")

    # Initially send all available strategies
    strategies_info = get_strategies_info()
    await ws.send_json({
        "type": "strategies_list",
        "strategies": strategies_info
    })

    # Default configuration
    current_strategy_name = "Opening Range Breakout (ORB)"
    current_strategy_class = None
    current_strategy_config = {}

    try:
        while True:
            # Receive configuration updates
            try:
                msg = await ws.receive_json()
                
                if msg.get("type") == "strategy_update":
                    current_strategy_name = msg.get("strategy_name", current_strategy_name)
                    current_strategy_config = msg.get("config", {})
                    
                    # Dynamically load the strategy
                    strategy_class = load_strategy(current_strategy_name)
                    if strategy_class:
                        current_strategy_class = strategy_class(symbol="", **current_strategy_config)
                    
                    # Send confirmation of strategy change
                    await ws.send_json({
                        "type": "strategy_update_confirmation",
                        "strategy": current_strategy_name
                    })
                    continue
            except Exception as config_error:
                print(f"Error processing configuration: {config_error}")
                continue

            # Regular scanning process
            scanned = []
            total = len(UNIVERSE)

            for i, symbol in enumerate(UNIVERSE, start=1):
                # 1️⃣ Send status update
                await ws.send_json({
                    "type": "status",
                    "message": f"Scanning {symbol} ({i}/{total})"
                })

                # 2️⃣ Scan stock using standard scanner
                data = scan_stock(symbol, cfg)

                if data and current_strategy_class:
                    try:
                        # Additional strategy-specific processing
                        # Note: This assumes strategies have a method like check_signal
                        strategy_signal = current_strategy_class.check_signal(
                            pd.DataFrame([data]), 
                            data.get('rvol', 0)
                        )
                        
                        if strategy_signal:
                            data['strategy_signal'] = strategy_signal
                            scanned.append(data)

                        # 3️⃣ Send stock update
                        await ws.send_json({
                            "type": "stock_update",
                            "symbol": data["symbol"],
                            "price": data["price"],
                            "pct_change": data["pct_change"],
                            "rvol": data["rvol"],
                            "signal": data.get("strategy_signal", {}).get("type", "WAIT")
                        })
                    except Exception as strategy_error:
                        print(f"Strategy processing error for {symbol}: {strategy_error}")

                # Small delay so UI can breathe
                await asyncio.sleep(0.15)

            # 4️⃣ Allocate capital to BUY signals
            allocations = allocate_trades(scanned, cfg)

            # 5️⃣ Send final summary
            await ws.send_json({
                "type": "summary",
                "total_capital": cfg["total_capital"],
                "suggested_trades": allocations,
                "current_strategy": current_strategy_name
            })

            # Pause before next full scan cycle
            await asyncio.sleep(10)

    except WebSocketDisconnect:
        print("❌ WebSocket client disconnected")

    except Exception as e:
        print(f"🔥 WebSocket error: {e}")
        await ws.close()