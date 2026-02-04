import yfinance as yf
import pandas_ta as ta
import time
from playsound import playsound

# Configuration
SYMBOL = "TATAMOTORS.NS"  # .NS for NSE
CHECK_INTERVAL = 60       # Check every minute

def get_signal():
    # Fetch 5-minute interval data for today
        data = yf.download(tickers=SYMBOL, period='1d', interval='5m')
            
                if data.empty: return
                    
                        # Calculate Indicators
                            data['VWAP'] = ta.vwap(data.High, data.Low, data.Close, data.Volume)
                                data['EMA200'] = ta.ema(data.Close, length=200)
                                    
                                        current_price = data['Close'].iloc[-1]
                                            current_vwap = data['VWAP'].iloc[-1]
                                                current_ema = data['EMA200'].iloc[-1]
                                                    
                                                        # Logic: Buy if price is above EMA200 AND just crossed above VWAP
                                                            if current_price > current_vwap and current_price > current_ema:
                                                                    trigger_trade(current_price)

                                                                    def trigger_trade(price):
                                                                        stop_loss = round(price * 0.99, 2)
                                                                            target = round(price * 102, 2)
                                                                                
                                                                                    print("\n" + "="*30)
                                                                                        print(f"🚨 SIGNAL DETECTED: {SYMBOL}")
                                                                                            print(f"Trigger Price: {round(price, 2)}")
                                                                                                print(f"Stop Loss:     {stop_loss}")
                                                                                                    print(f"Target:        {target}")
                                                                                                        print("="*30 + "\n")
                                                                                                            
                                                                                                                # Play your alarm sound
                                                                                                                    playsound('alert.mp3') 

                                                                                                                    print(f"Monitoring {SYMBOL}...")
                                                                                                                    while True:
                                                                                                                        get_signal()
                                                                                                                            time.sleep(CHECK_INTERVAL)
                                                                                                                            