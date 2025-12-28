# dashboard/app.py

import os
import sys
import time
import json
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from sqlmodel import Session, select, desc
from database.db import engine
from database.models import SimulationRun, MarketData, LLMAdvice, PortfolioState, Order
from config import config

st.set_page_config(page_title="NexusQuant Dashboard", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    /* PURE Light Mode Base */
    [data-testid="stAppViewContainer"] { background-color: #ffffff; color: #000000; }
    [data-testid="stHeader"] { background-color: #ffffff; }
    [data-testid="stSidebar"] { background-color: #f8fafc; border-right: 1px solid #e2e8f0; }
    
    /* Neon Bright Metric Cards */
    [data-testid="stMetric"] { 
        background-color: #ffffff; 
        border: 2px solid #0066ff; 
        padding: 20px; 
        border-radius: 12px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    [data-testid="stMetricLabel"] p { color: #334155 !important; font-weight: 700 !important; font-size: 16px !important; }
    [data-testid="stMetricValue"] div { color: #ff0055 !important; font-weight: 900 !important; font-size: 32px !important; }
    
    /* Brighter Tab Styling */
    .stTabs [data-baseweb="tab-list"] { background-color: #f1f5f9; padding: 5px; border-radius: 10px; }
    .stTabs [data-baseweb="tab"] { color: #475569; font-weight: 700; }
    .stTabs [aria-selected="true"] { color: #ff0055 !important; background-color: #ffffff; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

st.title("NexusQuant")
st.caption("Multi-Asset Portfolio Intelligence Platform")

# Sidebar - Run Selection & Config
with st.sidebar:
    st.header("Simulation Control")
    with Session(engine) as session:
        runs = session.exec(select(SimulationRun).order_by(desc(SimulationRun.started_at))).all()
        run_ids = [r.id for r in runs]
        
        if not run_ids:
            st.warning("No runs found in PostgreSQL.")
            st.stop()
            
        selected_run_id = st.selectbox("Active Simulation", run_ids)
        run_info = next(r for r in runs if r.id == selected_run_id)
        
    st.divider()
    st.subheader("Run Configuration")
    st.json(run_info.config_snapshot)

# Main Dashboard Tabs
tab1, tab2, tab3 = st.tabs(["PORTFOLIO Intelligence", "ADVISOR Insights", "AUDIT Trail"])

with Session(engine) as session:
    # Fetch Latest State
    latest_state = session.exec(
        select(PortfolioState).where(PortfolioState.run_id == selected_run_id).order_by(desc(PortfolioState.tick_id))
    ).first()
    
    if not latest_state:
        st.info("Waiting for first tick data...")
        st.stop()

    # Tab 1: Portfolio View
    with tab1:
        # Key Metrics Row
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Equity", f"${latest_state.total_equity:,.2f}")
        m2.metric("Cash Balance", f"${latest_state.balance:,.2f}")
        
        pnl = latest_state.total_equity - config.INITIAL_CAPITAL
        pnl_pct = (pnl / config.INITIAL_CAPITAL) * 100
        m3.metric("Total PnL", f"${pnl:,.2f}", delta=f"{pnl_pct:.2f}%")
        
        dd_pct = latest_state.max_drawdown * 100
        m4.metric("Max Drawdown", f"{dd_pct:.2f}%", delta_color="inverse" if dd_pct > 10 else "normal")

        st.divider()
        
        c1, c2 = st.columns([2, 1])
        
        with c1:
            st.subheader("Market Performance")
            # Multi-Asset Price Chart
            market_data = session.exec(
                select(MarketData).where(MarketData.run_id == selected_run_id).order_by(desc(MarketData.tick_id)).limit(200)
            ).all()
            
            if market_data:
                df_m = pd.DataFrame([m.model_dump() for m in market_data])
                fig = px.line(df_m, x="timestamp", y="price", color="symbol", title="Asset Prices")
                fig.update_layout(template="plotly_dark", height=450)
                st.plotly_chart(fig, use_container_width=True)
        
        with c2:
            st.subheader("Asset Allocation")
            holdings = latest_state.holdings
            df_h = pd.DataFrame([{"Asset": k, "Value": v} for k, v in holdings.items() if v > 0])
            if not df_h.empty:
                fig_pie = px.pie(df_h, values="Value", names="Asset", hole=0.4)
                fig_pie.update_layout(showlegend=False, height=400)
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No active holdings (100% Cash)")

    # Tab 2: Advisor Insights
    with tab2:
        st.subheader("Batch Advisory Signals")
        advice = session.exec(
            select(LLMAdvice).where(LLMAdvice.run_id == selected_run_id).order_by(desc(LLMAdvice.tick_id)).limit(100)
        ).all()
        
        if advice:
            df_a = pd.DataFrame([a.model_dump() for a in advice])
            
            # Group by Advisor/Asset
            st.dataframe(
                df_a[['asset', 'advisor_name', 'outlook', 'confidence', 'rationale', 'created_at']],
                use_container_width=True,
                hide_index=True
            )
            
            # Confidence Distribution
            fig_conf = px.histogram(df_a, x="confidence", color="outlook", nbins=20, title="Advisor Confidence Distribution")
            st.plotly_chart(fig_conf, use_container_width=True)
        else:
            st.info("No advice recorded yet.")

    # Tab 3: Audit Trail (Orders)
    with tab3:
        st.subheader("Order Execution History")
        orders = session.exec(
            select(Order).where(Order.run_id == selected_run_id).order_by(desc(Order.created_at)).limit(50)
        ).all()
        
        if orders:
            df_o = pd.DataFrame([o.model_dump() for o in orders])
            st.dataframe(
                df_o[['symbol', 'side', 'quantity', 'filled_price', 'status', 'created_at']],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No orders executed yet.")

# Auto-refresh logic (Premium Style)
if st.sidebar.button("Force Refresh"):
    st.rerun()

time.sleep(5)
st.rerun()
