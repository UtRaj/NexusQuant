# agents/quant.py 

import ta
import json
import pandas as pd
from .base import BaseAgent

class QuantAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="Quant")

    def run(self, symbol: str, price_history: pd.DataFrame) -> dict:
        """
        Calculates technical signals for a specific asset.
        """
        if price_history.empty or len(price_history) < 20:
            return {"outlook": "NEUTRAL", "confidence": 0.0, "reasoning": "Insufficient history"}

        # Calculate RSI
        rsi = ta.momentum.rsi(price_history['close'], window=14).iloc[-1]
        
        # Simple Mean Reversion logic
        outlook = "NEUTRAL"
        confidence = 0.5
        reason = "RSI is in neutral territory."
        
        if rsi < 35:
            outlook = "BULLISH"
            confidence = (35 - rsi) / 35 + 0.5 # Higher confidence as it gets deeper oversold
            reason = f"RSI oversold ({rsi:.1f})"
        elif rsi > 65:
            outlook = "BEARISH"
            confidence = (rsi - 65) / 35 + 0.5
            reason = f"RSI overbought ({rsi:.1f})"

        return {
            "outlook": outlook,
            "confidence": min(1.0, float(confidence)),
            "reasoning": reason,
            "indicators": {"rsi": float(rsi)}
        }
