# simulation/engine.py

import time
import json
import logging
import pandas as pd
from typing import Dict, List
from config import config
from sqlmodel import Session, select
from database.db import engine, init_db
from database.models import SimulationRun, MarketData, LLMAdvice, PortfolioState, Order

from simulation.market import MarketReplay
from agents.quant import QuantAgent
from agents.analyst import AnalystAgent
from utils.arbiter import DecisionArbiter
from utils.allocator import CapitalAllocator

class SimulationEngine:
    def __init__(self, load_data=True):
        print(f"[INIT] Initializing {config.PROJECT_NAME} v{config.VERSION}")
        self.run_id = config.RUN_ID
        print(f"[ID] Run ID: {self.run_id}")
        
        if load_data:
            init_db()
            self._start_run_record()
        
        self.market = MarketReplay(assets=config.ASSET_UNIVERSE, days=config.HISTORY_DAYS, load_data=load_data)
        self.quant = QuantAgent()
        self.analyst = AnalystAgent()
        self.arbiter = DecisionArbiter(config.CONFIDENCE_THRESHOLD)
        self.allocator = CapitalAllocator()
        
        self.tick_id = 0
        self.portfolio = self._init_portfolio()
        self.last_analyst_call = {} # {asset: tick_id}

    def _start_run_record(self):
        with Session(engine) as session:
            run = SimulationRun(
                id=self.run_id,
                config_snapshot=config.model_dump()
            )
            session.add(run)
            session.commit()

    def _init_portfolio(self):
        return {
            "balance": config.INITIAL_CAPITAL,
            "holdings": {asset: 0.0 for asset in config.ASSET_UNIVERSE},
            "total_equity": config.INITIAL_CAPITAL,
            "max_drawdown": 0.0,
            "peak_equity": config.INITIAL_CAPITAL
        }

    def _persist_portfolio(self):
        with Session(engine) as session:
            state = PortfolioState(
                run_id=self.run_id,
                tick_id=self.tick_id,
                balance=self.portfolio["balance"],
                holdings=self.portfolio["holdings"],
                total_equity=self.portfolio["total_equity"],
                max_drawdown=self.portfolio["max_drawdown"]
            )
            session.add(state)
            session.commit()

    def run_tick(self):
        # 1. Market Data
        tick_data = self.market.tick()
        if not tick_data:
            return False
            
        self.tick_id = self.market.current_tick_id
        
        # 2. Portfolio Valuation
        self._update_valuation(tick_data)
        
        # 3. Advisory Layer (Deterministic + AI)
        all_advice = []
        for asset, candle in tick_data.items():
            # Quant Analysis (Deterministic)
            history = self.market.data[asset].iloc[:self.market.current_index]
            q_advice = self.quant.run(asset, history)
            
            # Persist Quant Advice
            advice_obj = LLMAdvice(
                run_id=self.run_id,
                tick_id=self.tick_id,
                asset=asset,
                advisor_name="Quant",
                outlook=q_advice["outlook"],
                confidence=q_advice["confidence"],
                rationale=q_advice["reasoning"],
                raw_response=q_advice
            )
            all_advice.append(advice_obj)
            
            # LLM Analysis (Advisory) - Limited by cooldown
            last_call = self.last_analyst_call.get(asset, -config.LLM_COOLDOWN_TICKS)
            if (self.tick_id - last_call) >= config.LLM_COOLDOWN_TICKS:
                a_advice = self.analyst.run(asset, context=f"Price: {candle['price']}")
                self.last_analyst_call[asset] = self.tick_id
                all_advice.append(LLMAdvice(
                    run_id=self.run_id,
                    tick_id=self.tick_id,
                    asset=asset,
                    advisor_name="LLM_Analyst",
                    outlook=a_advice.get("outlook", "NEUTRAL"),
                    confidence=a_advice.get("confidence", 0.0),
                    rationale=a_advice.get("reasoning", a_advice.get("rationale", "No rationale")),
                    raw_response=a_advice
                ))

        # 4. Arbitration & Allocation (The Math Core)
        sentiment_scores = self.arbiter.aggregate_advice(all_advice)
        
        # Calculate Rolling Volatility (Simple proxy for allocator)
        vols = {}
        for asset in self.market.assets:
            history = self.market.data[asset].iloc[max(0, self.market.current_index-20):self.market.current_index]
            if len(history) > 1:
                vols[asset] = float(history['close'].pct_change().std())
            else:
                vols[asset] = 0.02 # default 2%
                
        target_allocations = self.allocator.allocate(
            sentiment_scores, vols, self.portfolio["total_equity"]
        )
        
        # 5. Execution (Rebalance to target)
        self._execute_rebalance(target_allocations, tick_data)
        
        # 6. Persistence
        with Session(engine) as session:
            for adv in all_advice:
                session.add(adv)
            session.commit()
            
        self._persist_portfolio()
        
        if self.tick_id % 10 == 0:
            print(f"TICK {self.tick_id:4} | Equity: ${self.portfolio['total_equity']:,.2f} | Drawdown: {self.portfolio['max_drawdown']:.2%}")
            
        return True

    def _update_valuation(self, tick_data):
        market_value = 0.0
        for asset, candle in tick_data.items():
            market_value += self.portfolio["holdings"].get(asset, 0.0) * candle["price"]
            
        self.portfolio["total_equity"] = self.portfolio["balance"] + market_value
        
        if self.portfolio["total_equity"] > self.portfolio["peak_equity"]:
            self.portfolio["peak_equity"] = self.portfolio["total_equity"]
            
        self.portfolio["max_drawdown"] = (self.portfolio["peak_equity"] - self.portfolio["total_equity"]) / self.portfolio["peak_equity"]

    def _execute_rebalance(self, targets: Dict[str, float], prices: Dict[str, Dict]):
        with Session(engine) as session:
            for asset, target_usd in targets.items():
                current_price = prices[asset]["price"]
                current_holding_usd = self.portfolio["holdings"].get(asset, 0.0) * current_price
                
                diff_usd = target_usd - current_holding_usd
                
                # Execution Threshold ($100 or ~0.1% of capital)
                if abs(diff_usd) > 100:
                    qty = diff_usd / current_price
                    side = "BUY" if qty > 0 else "SELL"
                    qty = abs(qty)
                    
                    # Update Memory
                    if side == "BUY":
                        self.portfolio["balance"] -= diff_usd
                        self.portfolio["holdings"][asset] += qty
                    else:
                        self.portfolio["balance"] += abs(diff_usd)
                        self.portfolio["holdings"][asset] -= qty
                        
                    # Persist Order
                    print(f"TRADE | {side:4} | {asset:8} | Qty: {qty:10.4f} | @ ${current_price:10.2f}")
                    session.add(Order(
                        run_id=self.run_id,
                        tick_id=self.tick_id,
                        symbol=asset,
                        side=side,
                        quantity=qty,
                        filled_price=current_price,
                        status="FILLED"
                    ))
            session.commit()

    def start_loop(self):
        print("STARTING Portfolio Intelligence Loop.")
        try:
            while self.run_tick():
                pass
            print("FINISHED Simulation Complete.")
        except KeyboardInterrupt:
            print("STOPPED Simulation Interrupted.")
