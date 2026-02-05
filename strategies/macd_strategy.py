class MACDStrategy:
    def __init__(self, symbol, rvol_min=5.0):
        self.symbol = symbol
        self.rvol_min = rvol_min

    def calculate_indicators(self, df):
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = exp1 - exp2
        df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        return df

    def check_signal(self, df, current_rvol):
        # [span_6](start_span)Ensure high demand per Warrior Trading standards[span_6](end_span)
        if current_rvol < self.rvol_min:
            return None

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        # Bullish Crossover: MACD crosses above Signal
        if prev['macd'] < prev['signal'] and latest['macd'] > latest['signal']:
            entry = latest['close']
            stop_loss = df['low'].iloc[-5:].min() # 5-candle low
            [span_7](start_span)tp = entry + ((entry - stop_loss) * 2) # 2:1 RR Ratio[span_7](end_span)
            
            return {"type": "BUY (MACD Cross)", "entry": entry, "sl": stop_loss, "tp": tp}
        return None
