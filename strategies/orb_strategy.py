import datetime
import pandas as pd

class OrbStrategy:
    def __init__(self, symbol, range_minutes=15, rvol_threshold=1.5):
        self.symbol = symbol
        self.range_minutes = range_minutes
        self.rvol_threshold = rvol_threshold
        self.opening_high = None
        self.opening_low = None
        self.range_established = False

    def calculate_opening_range(self, data):
        """
        Calculates the High and Low of the first 15 mins (9:30 - 9:45).
        """
        # Filter data for the first 15 minutes of the market
        start_time = datetime.time(9, 30)
        end_time = datetime.time(9, 30 + self.range_minutes)
        
        opening_data = data.between_time(start_time, end_time)
        
        if not opening_data.empty:
            self.opening_high = opening_data['high'].max()
            self.opening_low = opening_data['low'].min()
            self.range_established = True
            return self.opening_high, self.opening_low
        return None, None

    def check_signal(self, current_price, current_volume, avg_volume):
        """
        Checks for a breakout with high Relative Volume (RVOL).
        """
        if not self.range_established:
            return None

        rvol = current_volume / avg_volume
        
        # Bullish Breakout: Price > High AND Volume > 1.5x Average
        if current_price > self.opening_high and rvol > self.rvol_threshold:
            stop_loss = (self.opening_high + self.opening_low) / 2 # Midpoint SL
            take_profit = current_price + ((current_price - stop_loss) * 2) # 2:1 RR
            return {"type": "BUY", "entry": current_price, "sl": stop_loss, "tp": take_profit}

        # Bearish Breakdown: Price < Low AND Volume > 1.5x Average
        elif current_price < self.opening_low and rvol > self.rvol_threshold:
            stop_loss = (self.opening_high + self.opening_low) / 2
            take_profit = current_price - ((stop_loss - current_price) * 2) # 2:1 RR
            return {"type": "SELL", "entry": current_price, "sl": stop_loss, "tp": take_profit}

        return None

# Example Usage:
# strategy = ORBStrategy("AAPL")
# strategy.calculate_opening_range(historical_df)
# signal = strategy.check_signal(150.50, 500000, 200000)
