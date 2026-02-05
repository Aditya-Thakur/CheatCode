class GapAndGoStrategy:
    def __init__(self, symbol, gap_min=0.04): # 4% minimum gap
        self.symbol = symbol
        self.gap_min = gap_min
        self.first_candle_high = None

    def check_signal(self, df, prev_close):
        # 1. Verify Gap Up
        open_price = df.iloc[0]['open']
        gap_percent = (open_price - prev_close) / prev_close
        
        if gap_percent < self.gap_min:
            return None

        # 2. [span_9](start_span)Strategy Logic: Buy first candle to make a new high[span_9](end_span)
        if self.first_candle_high is None:
            self.first_candle_high = df.iloc[0]['high']
            return None

        current_price = df.iloc[-1]['close']
        if current_price > self.first_candle_high:
            entry = current_price
            stop_loss = df.iloc[-1]['low']
            [span_10](start_span)tp = entry + ((entry - stop_loss) * 2) # 2:1 RR[span_10](end_span)
            
            return {"type": "BUY (Gap & Go)", "entry": entry, "sl": stop_loss, "tp": tp}
        return None
      
