class BullFlagStrategy:
    def __init__(self, symbol, rvol_min=5.0):
        self.symbol = symbol
        self.rvol_min = rvol_min

    def check_signal(self, df, current_rvol):
        # 1. Selection Criteria (High Demand)
        if current_rvol < self.rvol_min:
            return None

        # 2. Bull Flag Logic (Simplified for Intraday)
        # Look for a sharp move up (Pole) followed by 3-5 lower-high candles (Flag)
        is_pole = df['close'].iloc[-6] < df['close'].iloc[-5] * 0.95 # 5% move
        is_flagging = (df['high'].iloc[-4] > df['high'].iloc[-3] > df['high'].iloc[-2])
        is_breakout = df['close'].iloc[-1] > df['high'].iloc[-2]

        if is_pole and is_flagging and is_breakout:
            entry = df['close'].iloc[-1]
            stop_loss = df['low'].iloc[-3] # Bottom of the flag
            risk = entry - stop_loss
            [span_3](start_span)tp = entry + (risk * 2) # 2:1 RR Ratio[span_3](end_span)
            
            return {"type": "BUY (Bull Flag)", "entry": entry, "sl": stop_loss, "tp": tp}
        return None
      
