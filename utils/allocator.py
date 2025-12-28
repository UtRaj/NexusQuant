# utils/allocator.py

import numpy as np
from typing import Dict, List
from config import config

class CapitalAllocator:
    """
    deterministic Capital Allocator using Inverse Volatility Scaling (Risk Parity).
    Ensures that capital is distributed such that each asset contributes 
    equally to the portfolio's risk.
    """
    
    def __init__(self, max_position_pct: float = None, reserve_pct: float = None):
        self.max_position_pct = max_position_pct if max_position_pct is not None else config.MAX_POSITION_PCT
        self.reserve_pct = reserve_pct if reserve_pct is not None else config.PORTFOLIO_CASH_RESERVE

    def allocate(self, scores: Dict[str, float], volatilities: Dict[str, float], total_equity: float) -> Dict[str, float]:
        """
        Calculates target quantities for each asset.
        
        Args:
            scores: Map of asset -> sentiment score (-1 to 1)
            volatilities: Map of asset -> rolling volatility %
            total_equity: Total USD value of portfolio
            
        Returns:
            Map of asset -> target_usd_allocation
        """
        # 1. Filter for non-zero scores
        active_assets = [a for a, s in scores.items() if s != 0]
        if not active_assets:
            return {a: 0.0 for a in scores}

        # 2. Calculate Inverse Volatility Weights
        # W_i = (1/Vol_i) / Sum(1/Vol_k)
        inv_vols = {a: 1.0 / max(volatilities.get(a, 0.01), 0.001) for a in active_assets}
        total_inv_vol = sum(inv_vols.values())
        weights = {a: (v / total_inv_vol) for a, v in inv_vols.items()}

        # 3. Apply Sentiment Scaling & Direction
        # Final_W_i = Weight_i * Sentiment_Score_i
        allocations = {}
        available_capital = total_equity * (1.0 - self.reserve_pct)
        
        for asset in active_assets:
            # Scale the weight by the absolute sentiment (confidence-weighted)
            # and preserve the direction (BUY/SELL)
            sentiment = scores[asset]
            target_pct = weights[asset] * abs(sentiment)
            
            # Cap at individual asset limit
            target_pct = min(target_pct, self.max_position_pct)
            
            # Target USD value (Signed: positive is LONG, negative is SHORT)
            # Note: For now, NexusQuant maintains LONG-ONLY for simplicity unless directed otherwise
            # but the math supports directionality.
            direction = 1.0 if sentiment > 0 else 0.0 # Long only enforcement for v1
            
            allocations[asset] = target_pct * available_capital * direction
            
        return allocations
