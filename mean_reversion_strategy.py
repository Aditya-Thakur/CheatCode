import pandas as pd
import numpy as np

class MeanReversionStrategy:
    def __init__(self, symbol, window=20, std_dev=2, rvol_min=5.0):
        self.symbol = symbol
        self.window = window
        self.std_dev = std_dev
        self.rvol_min = rvol_min

    def calculate_indicators(self, df):
        """Calculates Bollinger Bands and moving averages."""
        df['sma'] = df['close'].rolling(window=self.window).mean()
        df['std'] = df['close'].rolling(window=self.window).std()
        df['upper_band'] = df['sma'] + (self.std_dev * df['std'])
        df['lower_band'] = df['sma'] - (self.std_dev * df['std'])
        return df

    def check_signal(self, df, current_rvol):
        """
        Identifies oversold/overbought conditions with high volume.
        """
        latest = df.iloc[-1]
        
        # Filter for High Relative Volume (Warrior Trading Criteria)
        if current_rvol < self.rvol_min:
            return None

        # Long Signal: Price breaks below Lower Band (Oversold)
        if latest['close'] < latest['lower_band']:
            entry = latest['close']
            tp = latest['sma']  # Target is the mean (SMA)
            risk = (tp - entry) / 2 # 2:1 Reward-to-Risk ratio
            sl = entry - risk
            return {"type": "BUY (Reversion)", "entry": entry, "sl": sl, "tp": tp}

        # Short Signal: Price breaks above Upper Band (Overbought)
        elif latest['close'] > latest['upper_band']:
            entry = latest['close']
            tp = latest['sma']  # Target is the mean (SMA)
            risk = (entry - tp) / 2 # 2:1 Reward-to-Risk ratio
            sl = entry + risk
            return {"type": "SELL (Reversion)", "entry": entry, "sl": sl, "tp": tp}

        return None

# Example implementation logic
# strategy = MeanReversionStrategy("AMD", rvol_min=5.0)
# df_with_indicators = strategy.calculate_indicators(historical_data)
# signal = strategy.check_signal(df_with_indicators, current_relative_volume)
