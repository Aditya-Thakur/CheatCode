import pandas as pd
import numpy as np

class VWAPStrategy:
    def __init__(self, symbol, rvol_threshold=5.0):
        self.symbol = symbol
        self.rvol_threshold = rvol_threshold

    def calculate_vwap(self, df):
        """
        Calculates the Volume Weighted Average Price.
        Formula: sum(Price * Volume) / sum(Volume)
        """
        v = df['volume'].values
        p = (df['high'] + df['low'] + df['close']) / 3
        df['vwap'] = (p * v).cumsum() / v.cumsum()
        return df

    def check_signal(self, df, current_rvol):
        """
        Checks for a 'VWAP Pullback' entry signal.
        """
        latest = df.iloc[-1]
        previous = df.iloc[-2]

        # 1. [span_7](start_span)[span_8](start_span)Filter for High Demand (Relative Volume > 5x)[span_7](end_span)[span_8](end_span)
        if current_rvol < self.rvol_threshold:
            return None

        # 2. Identify the Pullback to VWAP
        # Condition: Price was above VWAP, now touching it from above
        is_above_vwap = previous['close'] > previous['vwap']
        is_touching_vwap = latest['low'] <= latest['vwap'] <= latest['high']
        
        if is_above_vwap and is_touching_vwap:
            entry_price = latest['vwap']
            
            # 3. [span_9](start_span)Risk Management: 2:1 Profit/Loss Ratio[span_9](end_span)
            # Stop loss set slightly below the previous candle's low
            stop_loss = previous['low'] * 0.998 
            risk_amount = entry_price - stop_loss
            
            if risk_amount <= 0: return None # Safety check
            
            take_profit = entry_price + (risk_amount * 2)
            
            return {
                "type": "BUY (VWAP Pullback)",
                "entry": round(entry_price, 2),
                "sl": round(stop_loss, 2),
                "tp": round(take_profit, 2),
                "rvol": current_rvol
            }

        return None

# Example usage within your CheatCode framework:
# vwap_strat = VWAPStrategy("AVTX", rvol_threshold=5.0)
# df_with_vwap = vwap_strat.calculate_vwap(market_data)
# trade_signal = vwap_strat.check_signal(df_with_vwap, 10.5)
