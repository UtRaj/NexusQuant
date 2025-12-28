# NexusQuant - Agentic Portfolio Intelligence Platform

NexusQuant is a high-fidelity, production-hardened simulation platform where AI agents collaborate to manage a multi-asset trading portfolio. It features a sophisticated **Advisory-Arbitration-Allocation** architecture, combining Large Language Models (LLMs) with deterministic quantitative finance.

---

## 🚀 Core Features

- **Multi-Agent Synergy**: Four specialized layers (Quant, Analyst, Arbiter, Allocator) working in tandem.
- **Risk-Parity Allocation**: Mathematical inverse-volatility scaling ensures balanced risk exposure.
- **High-Fidelity Auditing**: Automated PDF Integrity Reports with objective-based validation.
- **Hybrid Intelligence**: Combines real-time technical analysis (RSI, Mean Reversion) with macro LLM sentiment.
- **Observability**: Real-time Streamlit dashboard with a premium high-contrast interface.
- **Resilience Tested**: Passes 25+ stress tests including volatility shocks, LLM cooldowns, and NaN fault tolerance.

---

## 🏗️ Architecture & Technical Pillars

NexusQuant operates on a **Synchronized Portfolio Loop**:
1. **Pulse**: Synchronized data ingestion across Crypto (24/7) and Equities (Market-Hours).
2. **Advise**: Strategic insights generated via **Groq LLM** and Technical Indicators.
3. **Arbitrate**: Mathematical aggregation of advisor signals with EMA smoothing.
4. **Allocate**: Dynamic capital distribution based on rolling asset volatility.
5. **Execute**: Hardened execution engine with rebalancing thresholds and full persistence.

### 🧩 System Modules
- **Advisory Layer**: Specialized agents providing hybrid signals.
- **Decision Logic**: Advanced arbitration with EMA smoothing.
- **Execution Engine**: Hardened multi-tick simulation loop.
- **Dashboard**: Real-time premium monitoring interface.

---

## 🛠️ Getting Started
[Detailed Setup Guide](DOCUMENTATION.md#setup)

- **Groq API Key Required**
- **Docker Recommended**

```bash
docker-compose up --build
```

- **Dashboard**: `http://localhost:8501`
- **Database**: PostgreSQL on `localhost:5432`

---

## 🧪 Simulation Integrity Audit

NexusQuant features a professional-grade test runner that generates an **Audit Ledger** PDF:

```powershell
# Run the full audit suite
python tests/test_runner.py host all
```

### Test Runner Commands
| Category | Command | Result |
| :--- | :--- | :--- |
| **Complete Audit** | `python tests/test_runner.py host all` | Full Pass + PDF Report |
| **Unit Only** | `python tests/test_runner.py host unit` | Rapid logic validation |
| **Integration** | `python tests/test_runner.py host integration` | DB & Concurrency check |

*Results are saved in the `REPORTS/` directory.*

---

## 🛡️ Stability & Reliability
- **93% Code Coverage**: Core simulation and risk logic are fully exercised by automated suites.
- **Pydantic V2 Enforcement**: Strict configuration schema validation.
- **SQLModel Persistence**: Type-safe relational database management using PostgreSQL.
- **NaN Resilience**: The engine continues operating even if data feeds return corrupted values.

