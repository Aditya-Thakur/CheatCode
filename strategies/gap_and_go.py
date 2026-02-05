class GapAndGoStrategy:
    def __init__(self, symbol="", gap_min=0.04): # 4% minimum gap
        self.symbol = symbol
        self.gap_min = gap_min
        self.first_candle_high = None

    def check_signal(self, df, current_rvol):
        # Ensure sufficient data
        if len(df) == 0:
            return None

        # Get the latest price and historical information
        latest = df.iloc[-1]
        current_price = latest['price']
        
        # Get previous close for gap calculation
        # Assuming we're passing in historical data that includes previous close
        if 'prev_close' not in latest:
            return None

        prev_close = latest['prev_close']
        
        # 1. Verify Gap Up
        open_price = current_price  # Using current price as entry point
        gap_percent = (open_price - prev_close) / prev_close
        
        if gap_percent < self.gap_min:
            return None

        # 2. Strategy Logic: Buy first candle to make a new high
        if self.first_candle_high is None:
            self.first_candle_high = current_price
            return None

        # Check if current price is higher than first candle's high
        if current_price > self.first_candle_high:
            entry = current_price
            stop_loss = latest['low']  # Using the low of the current candle
            tp = entry + ((entry - stop_loss) * 2)  # 2:1 RR
            
            return {
                "type": "BUY (Gap & Go)", 
                "entry": entry, 
                "sl": stop_loss, 
                "tp": tp
            }
        return None