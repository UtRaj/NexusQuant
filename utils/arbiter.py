# utils/arbiter.py

import numpy
from typing import Dict, List
from database.models import LLMAdvice

class DecisionArbiter:
    def __init__(self, confidence_threshold: float = 0.6, smoothing_factor: float = 0.3):
        self.confidence_threshold = confidence_threshold
        self.smoothing_factor = smoothing_factor
        self.sentiment_memory: Dict[str, float] = {}
        
    def aggregate_advice(self, advice_list: List[LLMAdvice]) -> Dict[str, float]:
        asset_scores = {}
        grouped_advice = {}
        for advice in advice_list:
            if advice.asset not in grouped_advice:
                grouped_advice[advice.asset] = []
            grouped_advice[advice.asset].append(advice)
            
        # Combine current advice assets with memory assets for decay processing
        all_assets = set(grouped_advice.keys()) | set(self.sentiment_memory.keys())
            
        for asset in all_assets:
            signals = grouped_advice.get(asset, [])
            scores = []
            for sig in signals:
                side = 1.0 if sig.outlook == "BULLISH" else (-1.0 if sig.outlook == "BEARISH" else 0.0)
                weighted_score = side * sig.confidence
                if sig.confidence >= self.confidence_threshold:
                    scores.append(weighted_score)
            
            if scores:
                # 1. Calculate Raw Mean
                raw_score = float(numpy.mean(scores))
                
                # 2. Apply smoothing (EMA)
                prev_score = self.sentiment_memory.get(asset, 0.0)
                smoothed_score = (raw_score * self.smoothing_factor) + (prev_score * (1 - self.smoothing_factor))
                
                # 3. Hysteresis: Only update memory if delta is significant (> 0.1)
                if abs(smoothed_score - prev_score) > 0.1 or abs(smoothed_score) < 0.05:
                     self.sentiment_memory[asset] = smoothed_score
                
                asset_scores[asset] = self.sentiment_memory[asset]
            else:
                # Decay towards neutral if no new signals
                prev = self.sentiment_memory.get(asset, 0.0)
                self.sentiment_memory[asset] = prev * 0.8
                if abs(self.sentiment_memory[asset]) < 0.05: self.sentiment_memory[asset] = 0.0
                asset_scores[asset] = self.sentiment_memory[asset]
                
        return asset_scores
