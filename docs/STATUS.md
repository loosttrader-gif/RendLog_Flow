# RendLog Flow — Technical Status & Reference

> Real-time statistical analysis platform for multi-pair forex trading signals.
> Built on MetaTrader 5, Supabase, and Next.js 16. Current version: **v4.1**

---

## Table of Contents

1. [What is RendLog Flow?](#what-is-rendlog-flow)
2. [System Architecture](#system-architecture)
3. [Tech Stack](#tech-stack)
4. [Project Structure](#project-structure)
5. [Statistical Engine (v4.1)](#statistical-engine-v41)
6. [Mathematical Formulas](#mathematical-formulas)
7. [Backend — Modules & Functions](#backend--modules--functions)
8. [Frontend — Components & Pages](#frontend--components--pages)
9. [Database Schema](#database-schema)
10. [Data Flow](#data-flow)
11. [Configuration Parameters](#configuration-parameters)
12. [Authentication & Security](#authentication--security)
13. [Execution Flow](#execution-flow)
14. [Signal Logic](#signal-logic)
15. [OrderFlow Engine](#orderflow-engine)

---

## What is RendLog Flow?

**RendLog Flow** is a quantitative trading analysis platform that computes real-time statistical anomalies on log returns across **4 currency pairs and 6 timeframes simultaneously** (24 series in total). It identifies statistically extreme price movements — those that deviate significantly from the expected distribution — and classifies them as potential buy or sell signals.

The system operates on the premise that **log returns in ranging markets follow a heavy-tailed distribution**. When a return falls outside the ±2σ band under EWMA-calibrated volatility, and the market is confirmed to be in a ranging regime, it generates a directional signal. In trending markets, or when a systemic USD move is detected across all pairs, signals are suppressed.

### Core concepts

| Concept | What it means in practice |
|---|---|
| **Log returns** | Continuous compounding price changes: `ln(close[t] / close[t-1])` |
| **EWMA sigma** | Volatility that reacts faster to recent shocks than rolling std |
| **t-distribution** | Heavy-tailed model for forex returns — accounts for fat tails |
| **Efficiency Ratio** | Measures if market is trending or ranging (direction clarity) |
| **Signal suppression (ER)** | In trending markets, mean-reversion signals are discarded |
| **Signal suppression (PCA)** | In systemic USD moves, signals are discarded across all pairs |
| **GBM Monte Carlo** | Probability of mean-reversion within N candles after an anomaly |
| **PCA Factor Analysis** | Detects when multiple pairs move together driven by a single USD factor |
| **60-candle window** | Sliding buffer: one new candle in, oldest candle out |

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                            RENDLOG FLOW v4.1                             │
│                                                                          │
│   ┌──────────────┐     ┌──────────────────────┐     ┌───────────────┐   │
│   │  MT5 Broker  │────▶│  Python Backend v4.1  │────▶│   Supabase    │   │
│   │  (Tickmill)  │     │                       │     │  PostgreSQL   │   │
│   │  4 pairs ×   │     │  - EWMA, t-dist       │     │  + Realtime   │   │
│   │  6 timeframes│     │  - Regime filter (ER) │     │  + Auth       │   │
│   │  every 30s   │     │  - GBM Monte Carlo    │     └───────┬───────┘   │
│   └──────────────┘     │  - PCA multi-pair     │             │           │
│                        │  - OrderFlow          │             │realtime   │
│                        └──────────────────────┘             ▼           │
│                                                   ┌─────────────────┐   │
│                                                   │  Next.js 16.1   │   │
│                                                   │  React 18.2     │   │
│                                                   │  Dashboard      │   │
│                                                   │  Recharts 3     │   │
│                                                   └─────────────────┘   │
└──────────────────────────────────────────────────────────────────────────┘
```

### Active pairs

| Pair | Driver | Role in PCA |
|---|---|---|
| EURUSD | EUR vs USD | PC1 reference (loading always normalized positive) |
| GBPUSD | GBP vs USD | European bloc, high correlation with EURUSD |
| USDJPY | USD vs JPY | Risk-off / rates / carry trade |
| USDCAD | USD vs CAD | Commodities / regional correlation |

These 4 pairs cover the 3 main USD drivers: European bloc, Asia/risk-off, and commodities. This allows PCA to isolate whether a move is USD-systematic or pair-specific.

### Component responsibilities

| Component | Role |
|---|---|
| **MT5** | Source of historical OHLCV candle data for all 4 pairs |
| **Python backend** | Statistical computation engine, PCA cross-pair analysis, GBM simulation, Supabase writer |
| **Supabase** | Real-time database (PostgreSQL + RLS + Realtime), auth provider, Edge Functions |
| **Next.js frontend** | Interactive dashboard with symbol/TF selector, real-time subscriptions, charts |

---

## Tech Stack

### Backend

| Library | Version | Purpose |
|---|---|---|
| `MetaTrader5` | ≥5.0.5488 | MT5 broker API for OHLCV data |
| `pandas` | ≥2.1.0 | DataFrame operations, rolling windows |
| `numpy` | ≥1.26.0 | Vectorized math, log, matrix operations, PCA |
| `scipy` | ≥1.11.0 | `scipy.stats.t` for MLE and CDF, `linalg.eigh` for PCA |
| `arch` | ≥6.2.0 | GARCH model support (available, not primary) |
| `requests` | ≥2.31.0 | HTTP calls to Supabase REST API |
| `pytz` | ≥2023.3 | Timezone conversions |
| `python-dotenv` | ≥1.0.0 | `.env` file loading |

### Frontend

| Library | Version | Purpose |
|---|---|---|
| `next` | 16.1.6 | React full-stack framework |
| `react` / `react-dom` | 18.2.0 | UI component library |
| `recharts` | 3.7.0 | Chart visualization (LineChart, ComposedChart) |
| `@supabase/supabase-js` | 2.39.0 | DB client, auth, realtime subscriptions |
| `@supabase/auth-helpers-nextjs` | 0.8.7 | Server-side auth helpers |

### Infrastructure

| Service | Purpose |
|---|---|
| **Supabase** | PostgreSQL, Auth, Realtime, Edge Functions, RLS |
| **Vercel** (implied) | Next.js deployment host |
| **Tickmill-Demo** | MT5 broker server for multi-pair OHLCV data |

---

## Project Structure

```
Rendlog Flow/
├── backend/
│   ├── main.py                      ← Orchestrator v4.1 — outer=TF, inner=SYMBOL, PCA cross-pair
│   ├── config.py                    ← Constants, EWMA lambdas per symbol, GBM params, PCA thresholds
│   ├── conexion_mt5.py              ← MT5 connection, activates all 4 symbols, OHLCV fetch
│   ├── calculos_rendlog.py          ← EWMA, t-dist, regime filter, signal detection + PCA suppression
│   ├── calculos_gbm.py              ← GBM Monte Carlo engine (simular_gbm, calcular_gbm_anomalia)
│   ├── calculos_multipair.py        ← Linear algebra: covariance matrix, PCA, USD exposure
│   ├── calculos_orderflow.py        ← Volume delta, relative volume, anomaly detection
│   ├── api_client.py                ← Supabase REST client (RPC wrapper, symbol-aware)
│   ├── utils.py                     ← Timezone conversion, logging helpers
│   ├── requirements.txt             ← Python dependencies
│   ├── supabase_migrations.sql      ← DB schema: symbol column, constraint, updated RPCs
│   ├── .env                         ← Secrets (MT5 credentials, API_KEY)
│   ├── test_fase1_ewma.py           ← EWMA phase unit tests
│   ├── test_fase2_distribucion_t.py ← t-distribution tests
│   ├── test_fase3_regimen.py        ← Efficiency Ratio tests
│   ├── test_fase4_integracion.py    ← End-to-end integration tests
│   ├── test_fase5_gbm.py            ← GBM Monte Carlo unit tests
│   └── test_fase6_multipair.py      ← PCA / covariance matrix tests
│
├── frontend/
│   ├── app/
│   │   ├── layout.js                ← Root layout with Navbar
│   │   ├── page.js                  ← Redirect → /login
│   │   ├── globals.css              ← Global dark theme CSS
│   │   ├── login/page.js            ← Login form (email + password)
│   │   ├── register/page.js         ← Registration form (GIF background)
│   │   ├── settings/page.js         ← API Key display + backend setup guide
│   │   ├── dashboard/
│   │   │   ├── page.js              ← Main dashboard (symbol, TF, timezone state, subscriptions)
│   │   │   └── components/
│   │   │       ├── StatsPanel.jsx   ← 4 KPI cards (Symbol/TF, Z-score, Signal, Realtime)
│   │   │       ├── RendLogChart.jsx ← Log return chart + σ bands + GBM/PCA tooltip
│   │   │       ├── OrderFlowChart.jsx ← Volume bar chart + relative volume line
│   │   │       └── CorrelacionPanel.jsx ← Multi-pair table (Z-score, signal, PC1, régimen, USD exp.)
│   │   └── auth/callback/route.js   ← OAuth callback → create-profile Edge Function
│   ├── components/
│   │   └── Navbar.jsx               ← Top navigation (hidden on auth pages)
│   ├── lib/
│   │   ├── supabaseClient.js        ← Supabase JS client singleton
│   │   └── timezone.js              ← UTC offset formatter, timezone options
│   ├── tailwind.config.js           ← Custom dark palette + accent tokens
│   ├── jsconfig.json                ← Path alias @/ → project root
│   ├── .env.local                   ← Supabase URL + anon key (public)
│   └── package.json                 ← NPM dependencies
│
├── docs/
│   └── STATUS.md                    ← This file
├── README.md                        ← Installation + daily usage guide
└── openspec/                        ← Spec-Driven Development artifacts
    ├── specs/
    ├── changes/
    └── archive/
```

---

## Statistical Engine (v4.1)

The backend statistical engine runs 6 sequential phases per pair, plus a cross-pair PCA pass per timeframe:

```
Phase 1: Log Returns + EWMA Sigma (per pair)
        ↓
Phase 2: Student's t-Distribution Calibration (per pair)
        ↓
Phase 3: Market Regime Filter — Efficiency Ratio (per pair)
        ↓
Phase 4: Signal Detection + ER Suppression (per pair)
        ↓
Phase 5: GBM Monte Carlo — Reversal Probability (per pair, only on anomalies)
        ↓
Phase 6: PCA Cross-Pair — Systemic USD Detection + PCA Suppression (per TF, all pairs)
```

### Phase 1 — EWMA-Based Volatility

Classical rolling standard deviation treats all observations equally. EWMA assigns exponentially decreasing weights to older observations, making it more reactive to recent volatility shocks.

**Why it matters:** During a sudden news event (e.g., NFP, ECB decision), rolling std underestimates current risk. EWMA adapts within 2–5 candles. This prevents false signals during volatility spikes and correctly widens the sigma bands.

**Lambda values by pair and timeframe:**

| TF | EURUSD | GBPUSD | USDJPY | USDCAD |
|---|---|---|---|---|
| 1M | 0.94 | 0.94 | 0.93 | 0.94 |
| 5M | 0.95 | 0.95 | 0.94 | 0.95 |
| 15M | 0.96 | 0.96 | 0.95 | 0.96 |
| 30M | 0.97 | 0.97 | 0.96 | 0.97 |
| 1H | 0.97 | 0.97 | 0.97 | 0.97 |
| 4H | 0.98 | 0.98 | 0.97 | 0.98 |

USDJPY uses slightly lower lambdas across all TFs because it exhibits higher intraday volatility than the EUR/GBP/CAD pairs — faster decay is needed to stay calibrated.

### Phase 2 — Student's t-Distribution

Forex returns are not normally distributed — they exhibit **fat tails**. The t-distribution parameterized by degrees of freedom (ν) captures this. ν is estimated via MLE on the current 60-candle window.

- `percentil_real`: True probability of observing a return this extreme (not inflated by normal assumption)
- `nu_distribucion (ν)`: Fitted from real data. ν=5 → very fat tails. ν=30 → near-normal.
- `calibracion_activa`: Whether ≥50 returns exist to trust the fit

### Phase 3 — Market Regime Filter (Efficiency Ratio)

Kaufman's Efficiency Ratio measures how efficiently price moved. **ER ≈ 1.0** = trending; **ER ≈ 0.0** = ranging.

| ER Range | Regime | Signal Action |
|---|---|---|
| < 0.30 | RANGO | Generated if z-score exceeds threshold |
| 0.30 – 0.60 | AMBIGUO | Generated with reduced confidence |
| > 0.60 | TENDENCIA | Suppressed — `senal_suprimida = True` |

**Trader interpretation**: RANGO = the market is oscillating, mean-reversion works. TENDENCIA = the market is going somewhere with intent, fighting it loses money. AMBIGUO = signal exists but treat with caution.

### Phase 4 — Signal Detection + ER Suppression

Signal is generated on the latest candle using EWMA z-score. If regime is TENDENCIA, the signal is suppressed and `senal_suprimida = True` is recorded with the ER value.

### Phase 5 — GBM Monte Carlo (Reversal Probability)

**Only activates when `|z_score| > 2.0`**. For normal candles, all GBM fields are `null`.

When an anomaly is detected, 500 paths of a discrete GBM are simulated over a timeframe-specific horizon:

```
Horizonte por TF: 1M=20, 5M=15, 15M=12, 30M=10, 1H=8, 4H=5 velas
```

A path "reverts" if in any candle within the horizon, the simulated return falls back within 1σ of the mean.

**Trader interpretation**: `gbm_prob_reversion = 0.71` means that in 71% of 500 simulated scenarios, the price returns to normal within N candles. >65% = high reversal probability (green), 40–65% = moderate (yellow), <40% = price may continue (red).

### Phase 6 — PCA Multi-Pair Systemic Detection

After computing all 4 pairs for a given timeframe, the system builds a `[~57 × 4]` matrix of aligned log returns and performs eigendecomposition of the 4×4 covariance matrix.

**PC1** is the first principal component — the factor that explains the most variance across all 4 pairs simultaneously. When PC1 explains >60% of total variance, the market is being driven primarily by a single factor: the USD.

**Trader interpretation of PCA fields:**

| Field | Trader meaning |
|---|---|
| **PC1 Loading** | How much the USD factor explains THIS pair's move. Loading=0.80 means 80% of the pair's return is explained by the USD. Loading=0.20 means the pair has its own independent story. |
| **PC1 Varianza** | How coordinated ALL pairs are right now. >60% = the whole market is moving together (USD event). <40% = pairs are moving independently. |
| **pca_es_sistemico** | True if PC1_varianza>0.60 AND the pair's own loading>0.70. This specific pair is being dragged by the USD event. Signal is suppressed. |
| **Régimen (ER)** | RANGO = market oscillating, reversals work. TENDENCIA = market trending, don't fight it. AMBIGUO = mixed, lower confidence. |
| **Exp. USD (exposure_usd_alto)** | Correlation of this pair with EURUSD in the covariance matrix >0.85. If you trade this AND EURUSD at the same time, you're effectively doubling your USD exposure. |

**Why the "USD Sistémico" badge matters in trader language:**

When the badge appears, it means: *"What you're seeing in this pair is not a pair-specific anomaly — it's a USD event. All pairs are moving together. The z-score looks like a signal but it's not edge — it's the market moving in one direction because of macro news (NFP, Fed, CPI). Don't fade this."*

Without PCA suppression, RendLog would generate a VENTA signal on EURUSD precisely when the dollar is strengthening systematically — which is exactly when mean-reversion has the worst expected value.

---

## Mathematical Formulas

### Log Returns

```
log_return[t] = ln(close[t] / close[t-1])
```

Continuous compounding return. Additive over time, symmetric, and better-behaved statistically than simple returns.

---

### EWMA Conditional Variance

```
σ²[t] = λ · σ²[t-1] + (1 - λ) · r[t-1]²

Initialization:
  σ²[0] = Var(r[1], r[2], r[3], r[4], r[5])   ← first 5 valid returns

EWMA volatility:
  σ[t] = √(σ²[t])   clipped to [1e-12, ∞)

Where:
  λ = decay factor (pair + timeframe specific)
  r[t-1] = lagged return (causal — uses previous candle, not current)
```

**Note on causality**: Using `r[t-1]` instead of `r[t]` ensures the sigma estimate at time t was computed before observing the return at time t. This prevents look-ahead bias.

---

### Z-Score

```
z_score[t] = (r[t] - μ[t]) / σ_EWMA[t]

Where:
  r[t]          = current log return
  μ[t]          = rolling mean over window (default: 20 candles)
  σ_EWMA[t]     = EWMA volatility at time t

Reference (diagnostic):
z_score_static[t] = (r[t] - μ[t]) / σ_static[t]
  σ_static[t]   = rolling standard deviation (equal-weighted)
```

---

### Bollinger Bands

```
upper_2σ[t] = μ[t] + 2 · σ_EWMA[t]
lower_2σ[t] = μ[t] - 2 · σ_EWMA[t]
upper_3σ[t] = μ[t] + 3 · σ_EWMA[t]
lower_3σ[t] = μ[t] - 3 · σ_EWMA[t]
```

---

### Student's t-Distribution — MLE Fit

```
Parameters estimated via Maximum Likelihood:
  ν (nu)    = degrees of freedom ∈ [2.1, 30.0]
  μ         = location (mean)
  σ_t       = scale (not equal to std)

Excess Kurtosis:
  K = 6 / (ν - 4)    [valid only if ν > 4]

  K interpretation:
    ν = 5  → K = 6.0  (very fat tails)
    ν = 10 → K = 1.0  (moderately fat)
    ν = 30 → K = 0.25 (near-normal)

True percentile under t-distribution:
  P(|X| ≤ z | ν) = F_t(z; ν)   [scipy.stats.t.cdf]
```

---

### Efficiency Ratio

```
ER = |close[t] - close[t - w]| / Σ(i=t-w+1 to t) |close[i] - close[i-1]|

Where:
  w = window size (default: 14 candles)
  Numerator  = net displacement (straight-line distance)
  Denominator = total path length (sum of all individual moves)

Clipped to [0.0, 1.0]
```

---

### GBM Discrete (Monte Carlo)

```
Per simulated path, per candle k (dt=1):
  r_k = (μ - σ²/2) + σ · Z_k        Z_k ~ N(0,1)

Reversion condition:
  Path reverts if ∃k ∈ [1..horizonte]: |r_k - μ| ≤ σ

Reversal probability:
  P(reversión) = count(paths that revert) / N_PATHS

Price percentiles (end of horizon):
  S_k = S_0 · exp(Σ r_i, i=1..k)
  p5, p50, p95 = np.percentile(S_final, [5, 50, 95])

Parameters:
  N_PATHS  = 500
  μ        = rolling mean of log returns (20-candle window)
  σ        = σ_EWMA[latest]
  Horizonte by TF: 1M=20, 5M=15, 15M=12, 30M=10, 1H=8, 4H=5 candles
  Activation: |z_score| > 2.0
```

---

### Covariance Matrix + PCA

```
R: matrix [T × 4]   (inner join on aligned timestamps, ~57 rows typically)

Covariance matrix:
  R_centered = R - R.mean(axis=0)
  Σ = R_centered.T @ R_centered / (T - 1)    [4×4]

PCA via eigendecomposition:
  eigenvalues λ, eigenvectors V = np.linalg.eigh(Σ)
  (sorted descending by λ)

PC1 Loading per pair:
  PC1_loading[i] = V[i, 0]

Sign normalization (to avoid eigenvector sign ambiguity):
  If PC1_loading[EURUSD] < 0: flip all loadings
  (EURUSD loading is always positive by convention)

PC1 variance explained:
  PC1_varianza = λ[0] / Σλ

Systemic USD condition:
  pca_es_sistemico = (PC1_varianza > 0.60) AND (|PC1_loading[pair]| > 0.70)

USD exposure (pair-level):
  correlation[pair, EURUSD] = Σ[pair, EURUSD] / √(Σ[pair,pair] · Σ[EURUSD,EURUSD])
  exposure_usd_alto = correlation > 0.85
```

---

### Volatility Ratio

```
vol_ratio[t] = σ_EWMA[t] / σ_static[t]

Interpretation:
  > 1.3 → EWMA detects elevated volatility (volatile regime)
  < 0.7 → Unusually calm (suppressed volatility)
  ≈ 1.0 → Normal conditions
```

---

### Volume Delta

```
delta[t] = volume_bullish[t] - volume_bearish[t]

Where:
  volume_bullish[t] = tick_volume[t]  if close[t] > open[t]  else 0
  volume_bearish[t] = tick_volume[t]  if close[t] ≤ open[t]  else 0
```

---

### Relative Volume + Z-Score

```
vol_relativo[t] = tick_volume[t] / MA(tick_volume, window=20)[t]

z_score_vol[t] = (tick_volume[t] - μ_vol[t]) / σ_vol[t]
  [μ_vol, σ_vol rolling over 100 candles]

Anomaly: |z_score_vol| > 2.0
```

---

## Backend — Modules & Functions

### `config.py` — Constants & Configuration

```python
# Active symbols
SYMBOLS_ACTIVOS = ["EURUSD", "GBPUSD", "USDJPY", "USDCAD"]

# EWMA decay per symbol per TF
RENDLOG_LAMBDA_EWMA_SYMBOL = {
    "EURUSD": {"1M": 0.94, "5M": 0.95, "15M": 0.96, "30M": 0.97, "1H": 0.97, "4H": 0.98},
    "GBPUSD": {"1M": 0.94, "5M": 0.95, "15M": 0.96, "30M": 0.97, "1H": 0.97, "4H": 0.98},
    "USDJPY": {"1M": 0.93, "5M": 0.94, "15M": 0.95, "30M": 0.96, "1H": 0.97, "4H": 0.97},
    "USDCAD": {"1M": 0.94, "5M": 0.95, "15M": 0.96, "30M": 0.97, "1H": 0.97, "4H": 0.98},
}

# GBM Monte Carlo
GBM_N_PATHS = 500
GBM_HORIZONTE_VELAS = {"1M": 20, "5M": 15, "15M": 12, "30M": 10, "1H": 8, "4H": 5}
GBM_Z_UMBRAL_ACTIVACION = 2.0

# PCA thresholds
PCA_PC1_VARIANZA_UMBRAL = 0.60
PCA_PC1_LOADING_UMBRAL  = 0.70
PCA_CORRELACION_UMBRAL  = 0.85
PCA_MIN_FILAS_ALINEADAS = 30   # warn if < 30 aligned rows
```

---

### `conexion_mt5.py` — MetaTrader 5 Connection

**`conectar_mt5() → bool`**
- Calls `mt5.initialize()` and `mt5.login(login, password, server)`
- Loops over all `SYMBOLS_ACTIVOS`: verifies symbol info and calls `mt5.symbol_select(sym, True)`
- Returns `True` on success, logs error on failure

**`obtener_datos_historicos(symbol, timeframe_minutes, num_bars) → DataFrame`**
- Maps `timeframe_minutes` to MT5 constant
- Calls `mt5.copy_rates_from_pos(symbol, timeframe, 0, num_bars)`
- UTC correction: subtracts broker UTC offset from timestamps
- Returns `DataFrame[time, open, high, low, close, tick_volume]`

---

### `calculos_rendlog.py` — Core Statistical Engine

**`calcular_rendimientos_log(df) → df`**
- Adds `log_return` column: `np.log(df['close'] / df['close'].shift(1))`

**`_calcular_ewma_std(returns_series, lambda_decay) → pd.Series`** _(private)_
- Recursive EWMA variance, initialized from variance of first 5 valid returns
- Returns sigma series (square root of variance)

**`calcular_bandas_sigma(df, ventana=20, timeframe=None, symbol=None) → df`**
- Selects lambda from `RENDLOG_LAMBDA_EWMA_SYMBOL[symbol][timeframe]` when both provided
- Falls back to `RENDLOG_LAMBDA_EWMA[timeframe]` for backward compatibility
- Adds: `media`, `std_static`, `std` (EWMA), all 4 band columns, `vol_ratio`

**`detectar_anomalias(df, umbral_compra, umbral_venta, nu=None, pca_es_sistemico=False) → dict`**
- Computes z-score on most recent candle
- Applies ER regime filter (`senal_suprimida`)
- If `pca_es_sistemico=True`: also sets `senal=None`, `senal_suprimida_pca=True`
- Returns full signal metadata dict

---

### `calculos_gbm.py` — GBM Monte Carlo Engine

**`simular_gbm(precio_actual, mu, sigma_ewma, n_paths=500, n_horizonte=10) → dict`**
- Generates `Z ~ N(0,1)` matrix of shape `[n_paths × n_horizonte]`
- Computes drift-corrected log returns per path
- Reversion test: `|r_k - mu| ≤ sigma_ewma` for any candle k
- Returns `{gbm_prob_reversion, gbm_percentil_5, gbm_percentil_50, gbm_percentil_95}`

**`calcular_gbm_anomalia(z_score, mu, sigma_ewma, precio_close, timeframe=None) → dict`**
- Guard: if `|z_score| ≤ 2.0` → returns all-null dict (no simulation)
- Looks up `n_horizonte` from `GBM_HORIZONTE_VELAS[timeframe]`
- Calls `simular_gbm()` and adds `gbm_horizonte_velas`

**`_campos_nulos() → dict`**
- Returns `{gbm_prob_reversion: None, gbm_horizonte_velas: None, gbm_percentil_5/50/95: None}`

---

### `calculos_multipair.py` — Linear Algebra Engine

**`construir_matriz_retornos(dataframes: dict) → tuple[np.ndarray, list, pd.Index]`**
- Inner join of all 4 DataFrames on `time` column
- Returns `(R [T×4], symbols_list, aligned_timestamps)`

**`calcular_covarianza(R) → np.ndarray`**
- Centers R, computes `Σ = R_c.T @ R_c / (T-1)` → shape `[4×4]`

**`calcular_pca(cov_matrix, symbols) → dict`**
- `np.linalg.eigh(Σ)` → eigenvalues + eigenvectors (sorted descending)
- Sign normalization: EURUSD loading always positive
- Returns `{pc1_varianza, pc1_loadings: {sym: float}, es_sistemico: {sym: bool}}`

**`detectar_exposicion_usd(cov_matrix, symbols) → dict`**
- Computes pairwise correlation with EURUSD
- Returns `{sym: exposure_usd_alto: bool}` where threshold = 0.85

**`calcular_zscores_vectorizados(R, mu_vec, sigma_vec) → np.ndarray`**
- Vectorized: `(R[-1,:] - mu_vec) / sigma_vec` — no loops, pure numpy

**`es_movimiento_sistemico(pca_result, symbol) → bool`**
- `PC1_varianza > 0.60 AND |PC1_loading[symbol]| > 0.70`

---

### `api_client.py` — Supabase REST Client

| Method | RPC Endpoint | Purpose |
|---|---|---|
| `obtener_user_id()` | `GET /rpc/get_user_id_from_api_key` | Authenticate API key |
| `obtener_configuracion()` | `GET /rest/v1/user_config` | Load user thresholds |
| `enviar_datos(rows)` | `POST /rpc/sync_user_data` | Bulk upsert data rows |
| `delete_user_data()` | `POST /rpc/delete_user_data` | Full reset on startup |
| `delete_oldest_candle(tf, symbol)` | `POST /rpc/delete_oldest_candle` | Maintain 60-candle window per symbol |

`delete_oldest_candle` now accepts `symbol` parameter (defaults to `"EURUSD"` for backward compatibility).

---

### `main.py` — Orchestrator (v4.1)

#### Loop Structure

```
Every 30 seconds:
  for each timeframe in [1M, 5M, 15M, 30M, 1H, 4H]:

    dfs = {}
    for each symbol in [EURUSD, GBPUSD, USDJPY, USDCAD]:
      1. Fetch latest 1 candle from MT5
      2. If no new candle → skip this symbol/TF
      3. delete_oldest_candle(tf, symbol) from Supabase
      4. Fetch fresh 60 candles from MT5
      5. Compute EWMA, bands, delta, vol metrics (symbol-specific lambda)
      6. Re-estimate t-distribution
      7. Detect GBM anomaly (if |z_score| > 2.0)
      dfs[symbol] = df

    # Cross-pair PCA (after all 4 symbols computed)
    R, syms, ts = construir_matriz_retornos(dfs)
    if len(R) >= PCA_MIN_FILAS_ALINEADAS:
        cov = calcular_covarianza(R)
        pca = calcular_pca(cov, syms)
        exposure = detectar_exposicion_usd(cov, syms)
    else:
        pca, exposure = None, {}

    for each symbol:
      rows = build_rows(dfs[symbol], config, tf, symbol, pca, exposure)
      all_rows.extend(rows)

  supabase.enviar_datos(all_rows)  # batch per TF
```

#### Data Row Structure (`build_rows`)

```python
{
    "timeframe": "30M",
    "symbol": "GBPUSD",                   # NEW in v4.1
    "data_timestamp": "2026-03-02T10:00:00",
    "rendlog": {
        # Core statistical
        "z_score": float,
        "z_score_static": float,
        "log_return": float,
        "media": float,
        "std": float,                      # EWMA sigma
        "sigma_ewma": float,
        "sigma_static": float,
        "vol_ratio": float,
        "banda_2sigma_superior": float,
        "banda_2sigma_inferior": float,
        "banda_3sigma_superior": float,
        "banda_3sigma_inferior": float,
        "er": float | None,
        "regimen": "RANGO" | "TENDENCIA" | "AMBIGUO",
        "percentil_real": float,
        "nu_distribucion": float | None,
        "calibracion_activa": bool,

        # Signal
        "senal": "COMPRA" | "VENTA" | None,
        "senal_suprimida": bool,           # Suppressed by ER regime filter
        "senal_suprimida_pca": bool,       # NEW — Suppressed by PCA systemic detection

        # GBM Monte Carlo — NEW (null when |z_score| ≤ 2.0)
        "gbm_prob_reversion": float | None,
        "gbm_horizonte_velas": int | None,
        "gbm_percentil_5": float | None,
        "gbm_percentil_50": float | None,
        "gbm_percentil_95": float | None,

        # PCA multi-pair — NEW
        "pca_pc1_loading": float | None,
        "pca_pc1_varianza": float | None,
        "pca_es_sistemico": bool,
        "exposure_usd_alto": bool
    },
    "orderflow": {
        "delta": int,
        "vol_relativo": float,
        "anomalia_vol": bool,
        "z_score_vol": float,
        "tick_volume": int
    }
}
```

`last_sent_time` is keyed by `(symbol, tf_name)` tuple — 24 independent entries.

---

## Frontend — Components & Pages

### `lib/timezone.js`

Manual UTC offset handling:

```javascript
function formatTime(timestamp_iso, offsetStr, options = {})
  // Parses timestamp as UTC
  // Applies manual offset: +/- hours
  // Returns "DD/MM HH:mm:ss" (es-ES locale)
```

### `app/dashboard/page.js` — Dashboard State & Subscriptions

**State:**

| State | Type | Purpose |
|---|---|---|
| `data` | `Array` | Historical candle rows for selected symbol+TF (up to 100) |
| `multiPairLatest` | `Array` | Latest candle for each of 4 symbols (for CorrelacionPanel) |
| `selectedTF` | `string` | Active timeframe (default: `"30M"`) |
| `selectedSymbol` | `string` | Active pair (default: `"EURUSD"`) |
| `selectedTZ` | `string` | UTC offset string (default: `"0"`) |
| `isConnected` | `bool` | Supabase Realtime subscription status |
| `loading` | `bool` | Initial data load indicator |

**Data queries:**

```javascript
// Main chart data (symbol + TF specific)
supabase
  .from('user_data')
  .select('*')
  .eq('user_id', userId)
  .eq('timeframe', tf)
  .eq('symbol', symbol)
  .order('data_timestamp', { ascending: false })
  .limit(100)
// Result reversed → oldest first for chart rendering

// Multi-pair latest (for CorrelacionPanel)
// Parallel fetch: Promise.all over 4 symbols, limit(1) each
```

**Subscription model (corrected in v4.1):**

```javascript
// Cancellation flag pattern — prevents stale async closures
let cancelled = false

const init = async () => {
  ...
  if (cancelled) return           // checked after each await
  channel = supabase.channel(...)
    .on('postgres_changes', {...}, refresh)
    .subscribe(...)
  pollInterval = setInterval(refresh, 30000)
}

// Debounced refresh — batches 24 realtime events into 1 fetch
const refresh = () => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    fetchData(userRef.current.id, selectedTF, selectedSymbol)
    fetchMultiPair(userRef.current.id, selectedTF)
  }, 400)
}

return () => {
  cancelled = true                // kills any in-flight init()
  clearTimeout(debounceTimer)
  supabase.removeChannel(channel)
  clearInterval(pollInterval)
}
```

**Why this fix was necessary**: The backend inserts 24 rows per cycle (4 symbols × 6 TFs). Each row triggered a separate realtime event, causing 24 concurrent Supabase queries and chart instability. Additionally, if the user switched TF before `init()` completed (async), the old channel was never removed (local variable was still `null` at cleanup time), causing a stale channel with old closure values to persist indefinitely.

---

### `StatsPanel.jsx` — KPI Cards

| Card | Content |
|---|---|
| **Par / Timeframe** | Active symbol + TF + latest candle timestamp |
| **Z-Score** | Current EWMA z-score (4 decimal places) |
| **Señal** | COMPRA (green) / VENTA (red) / Suprimida PCA (orange) / Suprimida régimen (gray) / Sin señal |
| **Realtime** | Green pulse if subscribed, red if disconnected |

Signal priority: `senal_suprimida_pca` > `senal_suprimida` > active signal > none.

---

### `RendLogChart.jsx` — Log Return Chart

Built on Recharts `ComposedChart`:

| Visual element | Data mapping |
|---|---|
| Amber line | `log_return` |
| Red dashed lines | `banda_2sigma_superior/inferior` |
| Orange dashed lines | `banda_3sigma_superior/inferior` |
| Green dot | Return < lower_2σ (potential COMPRA) |
| Red dot | Return > upper_2σ (potential VENTA) |
| Brush | Windowed view, starts at last 50 candles |

**Custom tooltip sections:**

| Section | Fields shown | Visibility |
|---|---|---|
| Retorno | log_return, z_score EWMA, z_score_static | Always |
| Estadístico | percentil_real, ν (t-dist), vol_ratio | Always |
| Régimen | régimen (colored), ER value | Always |
| Señal | signal with PCA/ER suppression text, ±2σ bands | Always |
| Monte Carlo GBM | P(reversión) % (colored), horizonte, p5/p50/p95 | Only when `gbm_prob_reversion != null` |
| PCA Sistémico | PC1 Loading, PC1 Varianza, systemic badge | Only when `pca_pc1_loading != null` |

---

### `OrderFlowChart.jsx` — Volume Chart

| Visual element | Data mapping |
|---|---|
| Green bar | Positive delta candles |
| Red bar | Negative delta candles |
| Orange stroke | Volume anomaly (`anomalia_vol = true`) |
| Orange line (right axis) | `vol_relativo` |

Filter: `MAX_VALID_DELTA = 1,000,000` — removes outlier spikes.

---

### `CorrelacionPanel.jsx` — Multi-Pair Analysis Table

Visible when `multiPairLatest.length > 0`. Shows one row per symbol for the active timeframe.

**Header:** PC1 varianza explained (colored orange if >60%) + "USD Sistémico" badge if any pair is systemic.

**Table columns:**

| Column | What it shows | Trader meaning |
|---|---|---|
| **Par** | Symbol (highlighted if active) | Which pair |
| **Z-Score** | EWMA z-score (green if negative extreme, red if positive, yellow if between ±1.5–2) | How far outside the band |
| **Señal** | COMPRA / VENTA / Sup.PCA / Sup.ER / — | Signal state |
| **PC1 Loading** | Visual bar + decimal (orange if systemic) | How much the USD factor drives this pair. High = pair moves with the dollar. Low = independent. |
| **Régimen** | RANGO (green) / TENDENCIA (red) / AMBIGUO (yellow) | Market structure. RANGO = reversals work. TENDENCIA = don't fight it. |
| **Exp. USD** | Alta (orange dot) / — | Correlation >0.85 with EURUSD. Doubles USD exposure if traded simultaneously. |

**"USD Sistémico" badge logic**: Appears when `pca_es_sistemico = true` on ANY pair in the panel. Means all pairs are coordinated by a single USD factor — macro event in play, mean-reversion signals are unreliable across the board.

---

## Database Schema

### `user_data` (core table — v4.1)

```sql
CREATE TABLE user_data (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id          UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
  symbol           TEXT NOT NULL DEFAULT 'EURUSD',   -- NEW in v4.1
  timeframe        TEXT NOT NULL,
  data_timestamp   TIMESTAMP NOT NULL,
  rendlog          JSONB,
  orderflow        JSONB,
  created_at       TIMESTAMP DEFAULT now(),
  CONSTRAINT user_data_user_id_symbol_timeframe_timestamp_key
    UNIQUE(user_id, symbol, timeframe, data_timestamp)
);

CREATE INDEX idx_user_data_lookup
  ON user_data(user_id, symbol, timeframe, data_timestamp DESC);
```

### Other tables

**`user_profiles`**: `id UUID, api_key TEXT UNIQUE, created_at, updated_at`

**`user_config`**: `user_id, timeframe, timezone, umbral_sigma_compra/venta, ventana_estadistica, alertas_activas`

### RPC Functions

**`delete_user_data(api_key_param) → BOOLEAN`**
Validates API key → deletes all rows for that user. Called on backend startup.

**`delete_oldest_candle(api_key_param, timeframe_param, symbol_param DEFAULT 'EURUSD') → BOOLEAN`**
Deletes oldest `data_timestamp` row for given user + symbol + timeframe. Maintains 60-candle window.
`symbol_param` defaults to `'EURUSD'` for backward compatibility.

**`sync_user_data(api_key_param, rows_param JSONB) → VOID`**
Bulk upsert: `ON CONFLICT (user_id, symbol, timeframe, data_timestamp) DO UPDATE SET ...`

**`get_user_id_from_api_key(api_key_param) → UUID`**
Returns `user_profiles.id` for the given API key.

### Migration (v4.1)

Steps executed to migrate from v3.0 to v4.1 schema:

```sql
-- 1. Add symbol column
ALTER TABLE user_data ADD COLUMN symbol TEXT NOT NULL DEFAULT 'EURUSD';

-- 2. Drop old unique constraint (was named user_data_unique)
ALTER TABLE user_data DROP CONSTRAINT IF EXISTS user_data_unique;
ALTER TABLE user_data DROP CONSTRAINT IF EXISTS user_data_user_id_timeframe_data_timestamp_key;

-- 3. Add new constraint including symbol
ALTER TABLE user_data ADD CONSTRAINT user_data_user_id_symbol_timeframe_timestamp_key
  UNIQUE (user_id, symbol, timeframe, data_timestamp);

-- 4. Add index for symbol-aware queries
CREATE INDEX IF NOT EXISTS idx_user_data_symbol
  ON user_data(user_id, symbol, timeframe, data_timestamp DESC);

-- 5. Update delete_oldest_candle RPC to accept symbol_param
-- (CREATE OR REPLACE with DEFAULT 'EURUSD')
```

---

## Data Flow

### Backend → Supabase (v4.1)

```
MT5 Broker (4 pairs × 6 TFs OHLCV)
        │
        ▼ for each TF:
        │   for each symbol:
        │     obtener_datos_historicos(symbol, tf, 60)
        │       → calcular_rendimientos_log()
        │       → calcular_bandas_sigma(symbol, tf)   [EWMA λ per pair+TF]
        │       → calcular_delta_volumen()
        │       → calcular_volumen_relativo()
        │       → detectar_anomalia_volumen()
        │       → calcular_efficiency_ratio()
        │       → estimar_distribucion_t()
        │       → calcular_gbm_anomalia()             [only if |z| > 2.0]
        │
        ▼ construir_matriz_retornos(dfs)               [inner join 4 pairs]
        │     → calcular_covarianza()
        │     → calcular_pca()                        [eigendecomposition 4×4]
        │     → detectar_exposicion_usd()
        │
        ▼ for each symbol:
        │     → detectar_anomalias(pca_es_sistemico=...)
        │     → build_rows(...)
        │
        ▼ enviar_datos(all_rows)                       [batch upsert]
        │
        ▼ Supabase INSERT/UPSERT into user_data
```

### Supabase → Frontend

```
user_data (PostgreSQL)
        │
        ├── Initial REST query (page load)
        │     SELECT * FROM user_data
        │     WHERE user_id=$uid AND symbol=$sym AND timeframe=$tf
        │     ORDER BY data_timestamp DESC LIMIT 100
        │
        ├── Multi-pair fetch (CorrelacionPanel)
        │     SELECT symbol, rendlog, data_timestamp
        │     WHERE symbol IN (4 pairs) LIMIT 1 each
        │
        └── Realtime subscription (postgres_changes)
              Debounced 400ms → single re-fetch on batch arrival
                │
                ▼
        React state
          ├── data[]          → StatsPanel, RendLogChart, OrderFlowChart
          └── multiPairLatest → CorrelacionPanel
```

---

## Configuration Parameters

| Parameter | Default | Where | Description |
|---|---|---|---|
| `SYMBOLS_ACTIVOS` | 4 pairs | config.py | Active currency pairs |
| `VENTANA_VELAS` | 60 | config.py | Candles stored per symbol+TF |
| `umbral_sigma_compra` | -2.0 | config.py / user_config | Buy signal threshold |
| `umbral_sigma_venta` | +2.0 | config.py / user_config | Sell signal threshold |
| `ventana_estadistica` | 20 | config.py / user_config | Rolling mean window |
| `λ per pair/TF` | 0.93–0.98 | config.py | EWMA decay (see table above) |
| `ER_umbral_rango` | 0.30 | config.py | Below this → ranging |
| `ER_umbral_tendencia` | 0.60 | config.py | Above this → trending |
| `ER_ventana` | 14 | config.py | Candle lookback for ER |
| `GBM_N_PATHS` | 500 | config.py | Monte Carlo paths per anomaly |
| `GBM_Z_UMBRAL_ACTIVACION` | 2.0 | config.py | Min |z| to run GBM |
| `PCA_PC1_VARIANZA_UMBRAL` | 0.60 | config.py | Systemic USD: variance threshold |
| `PCA_PC1_LOADING_UMBRAL` | 0.70 | config.py | Systemic USD: loading threshold |
| `PCA_CORRELACION_UMBRAL` | 0.85 | config.py | High USD exposure threshold |
| `PCA_MIN_FILAS_ALINEADAS` | 30 | config.py | Min rows for valid PCA |
| `nu_min_datos` | 50 | config.py | Min returns for t-dist MLE |
| `BROKER_UTC_OFFSET` | 2h | config.py | Tickmill time vs UTC |
| `polling_interval` | 30s | main.py | Backend main loop sleep |
| `realtime_debounce` | 400ms | dashboard/page.js | Frontend event batching |
| `fallback_polling` | 30s | dashboard/page.js | Frontend fallback fetch |
| `MAX_VALID_DELTA` | 1,000,000 | OrderFlowChart.jsx | Delta outlier filter |

---

## Authentication & Security

### Authentication Flow

```
1. User registers → supabase.auth.signUp()
2. Email verified → auth.users record created
3. First login → create-profile Edge Function:
     - Generates unique api_key (UUID)
     - Inserts into user_profiles
4. /settings page displays api_key
5. User configures backend .env with api_key
6. Backend calls /rpc/get_user_id_from_api_key
7. All subsequent DB writes use validated user_id
```

### Secret Inventory

| Secret | Location | Exposed to |
|---|---|---|
| `MT5_LOGIN` | backend/.env | Backend only |
| `MT5_PASSWORD` | backend/.env | Backend only |
| `API_KEY` | backend/.env | Backend only → Supabase RPC |
| `SUPABASE_ANON_KEY` | frontend/.env.local | Browser (restricted by RLS) |
| `SUPABASE_URL` | frontend/.env.local | Browser (public endpoint) |

---

## Execution Flow

### Full System Startup (v4.1)

```
STEP 0 — Prerequisites
  ├── MT5 terminal running + logged into Tickmill-Demo
  ├── Backend .env configured: MT5_LOGIN, MT5_PASSWORD, API_KEY
  └── Frontend .env.local configured: SUPABASE_URL, SUPABASE_ANON_KEY

STEP 1 — Backend Initialization
  ├── mt5.initialize() + mt5.login()
  ├── Verify + activate all 4 symbols in MT5
  ├── api_client.obtener_user_id()        ← validate API_KEY
  ├── api_client.obtener_configuracion()  ← load user thresholds
  └── api_client.delete_user_data()       ← FULL RESET (clean start)

STEP 2 — Initial Load
  For each TF in [1M, 5M, 15M, 30M, 1H, 4H]:
    For each symbol in [EURUSD, GBPUSD, USDJPY, USDCAD]:
      ├── obtener_datos_historicos(symbol, tf, 60)
      ├── calcular_estadisticas(df, config, tf, symbol)
      └── dfs[symbol] = df

    construir_matriz_retornos(dfs) → PCA cross-pair

    For each symbol:
      ├── build_rows(df, config, tf, symbol, pca, exposure)
      └── all_rows.extend(rows)   [60 rows per symbol]

  enviar_datos(all_rows)   [1440 rows total: 60 × 4 × 6]

STEP 3 — Main Loop (∞, every 30 seconds)
  For each TF:
    For each symbol:
      ├── Check if new candle formed
      ├── If NO → skip
      └── If YES:
            ├── delete_oldest_candle(tf, symbol)
            ├── fetch fresh 60 candles
            ├── compute all phases (1–5)
            └── dfs[symbol] = df

    PCA cross-pair (Phase 6)

    For each symbol:
      └── build_rows(df.tail(1)) → 1 row

  enviar_datos(all_rows)   [up to 24 rows: 1 per symbol × TF with new candle]
```

---

## Signal Logic

### Signal Generation

```python
z_score = (log_return[latest] - rolling_mean) / sigma_EWMA[latest]

if z_score < umbral_compra (-2.0):
    senal_pre_filtro = "COMPRA"
elif z_score > umbral_venta (+2.0):
    senal_pre_filtro = "VENTA"
else:
    senal_pre_filtro = None
```

### Suppression Priority

```
1. PCA Systemic check (Phase 6 — cross-pair):
     if pca_es_sistemico:
         senal = None
         senal_suprimida_pca = True
         → Badge "USD Sistémico" shown in frontend
         → Tooltip: "Suprimida — movimiento sistémico USD (PCA)"

2. ER Regime check (Phase 3 — per pair):
     elif regimen == "TENDENCIA":
         senal = None
         senal_suprimida = True
         → Tooltip: "Filtrada (régimen ER)"

3. No suppression:
     senal = senal_pre_filtro   ("COMPRA" | "VENTA" | None)
```

**Signal suppression does NOT prevent recording.** All metrics are still stored in `rendlog`. Suppression only sets `senal = None` and the corresponding flag.

---

## OrderFlow Engine

MT5 does not provide true bid/ask volume for most brokers. `tick_volume` (number of price ticks per candle) is used as a proxy. It correlates strongly with real volume in liquid sessions and provides valid relative comparisons.

### Delta Interpretation

| Delta | Interpretation |
|---|---|
| Large positive + COMPRA signal | Buyers dominated a low-return candle → potential reversal up |
| Large negative + VENTA signal | Sellers dominated a high-return candle → potential reversal down |
| Delta disagreeing with signal | Lower confidence setup |

### Volume Anomaly

`anomalia_vol = true` (z-score > 2.0 on volume) indicates unusual activity — possible institutional participation, news event absorption, or stop-hunt. Warrants attention regardless of signal direction.

---

## Operational Specifications

| Specification | Value |
|---|---|
| **Instruments** | EURUSD, GBPUSD, USDJPY, USDCAD |
| **Broker** | Tickmill-Demo (UTC+2/+3) |
| **Timeframes** | 1M, 5M, 15M, 30M, 1H, 4H (all simultaneous) |
| **Total series** | 24 (4 pairs × 6 TFs) |
| **Candles per series** | 60 (sliding window, strict) |
| **Update cycle** | Every 30 seconds |
| **Signal threshold** | ±2.0σ (configurable per user) |
| **GBM activation** | \|z_score\| > 2.0 |
| **GBM paths** | 500 Monte Carlo paths |
| **PCA dimensions** | 4×4 covariance matrix, eigendecomposition |
| **PCA systemic threshold** | PC1_varianza > 60% AND \|loading\| > 70% |
| **Rolling mean window** | 20 candles (configurable) |
| **ER window** | 14 candles |
| **t-dist MLE min data** | 50 returns |
| **Frontend data limit** | 100 rows per query |
| **Realtime debounce** | 400ms (batches 24 events per cycle) |
| **Fallback polling** | 30s |
| **Auth method** | Email/password (Supabase) + API key (backend) |
| **Database** | PostgreSQL (Supabase) with JSONB metrics |
| **Theme** | Dark (#0a0a0a bg, #F59E0B accent) |
| **Chart library** | Recharts 3 (ComposedChart) |
