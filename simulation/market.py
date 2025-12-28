# simulation/market.py

import time
import os
import sys
import pandas as pd
import yfinance as yf
from typing import Dict, Optional, List
from sqlmodel import Session
from database.db import engine
from database.models import MarketData
from config import config
from datetime import datetime, timedelta
from contextlib import contextmanager

class MarketReplay:
    def __init__(self, assets: List[str], days=30, interval="5m", load_data=True):
        self.assets = assets
        self.interval = interval
        self.data: Dict[str, pd.DataFrame] = {}
        self.current_index = 0
        self.current_tick_id = 0
        if load_data:
            self._load_all_data(days)

    def _load_all_data(self, days: int):
        print(f"DATA Loading market data for {len(self.assets)} assets...")
        for asset in self.assets:
            self.data[asset] = self._fetch_asset_data(asset, days)
        
        # Align indexes to the shortest common length
        min_len = min(len(df) for df in self.data.values())
        for asset in self.assets:
            self.data[asset] = self.data[asset].iloc[:min_len]
        print(f"SYNC Market data synchronized. Timeline length: {min_len} ticks.")

    def _fetch_asset_data(self, symbol: str, days: int) -> pd.DataFrame:
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            with self.suppress_output():
                df = yf.download(symbol, start=start_date, end=end_date, interval=self.interval, progress=False)
            
            if not df.empty:
                # Flatten MultiIndex if present (yfinance v0.2.x+ behavior)
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                
                df.reset_index(inplace=True)
                df.columns = [str(c).lower() for c in df.columns]
                return df
        except Exception as e:
            print(f"WARN Error fetching {symbol}: {e}")
        
        return pd.DataFrame()

    @contextmanager
    def suppress_output(self):
        with open(os.devnull, "w") as devnull:
            old_stdout, old_stderr = sys.stdout, sys.stderr
            sys.stdout, sys.stderr = devnull, devnull
            try:
                yield
            finally:
                sys.stdout, sys.stderr = old_stdout, old_stderr

    def tick(self) -> Optional[Dict[str, Dict]]:
        """
        Move to next portfolio-wide tick.
        Returns a map of asset -> candle data.
        """
        first_asset = self.assets[0]
        if self.current_index >= len(self.data[first_asset]):
            return None

        portfolio_tick = {}
        self.current_tick_id += 1
        
        with Session(engine) as session:
            for asset in self.assets:
                row = self.data[asset].iloc[self.current_index]
                
                # Robust Validation (Phase 14 Hardening)
                price = float(row.get('close', 0.0))
                volume = float(row.get('volume', 0.0))
                
                # Handle NaNs
                if pd.isna(price) or price <= 0:
                    # Try to use previous index price if available
                    if self.current_index > 0:
                        prev_row = self.data[asset].iloc[self.current_index - 1]
                        price = float(prev_row['close'])
                        print(f"WARN NaN/Invalid price for {asset} at idx {self.current_index}, forward-filling.")
                    else:
                        price = 0.01 # Safe floor
                
                candle = {
                    "symbol": asset,
                    "price": price,
                    "volume": volume,
                    "timestamp": row['datetime']
                }
                portfolio_tick[asset] = candle
                
                # Persistence
                session.add(MarketData(
                    run_id=config.RUN_ID,
                    tick_id=self.current_tick_id,
                    symbol=asset,
                    price=candle['price'],
                    volume=candle['volume'],
                    timestamp=candle['timestamp']
                ))
            session.commit()
            
        self.current_index += 1
        return portfolio_tick

