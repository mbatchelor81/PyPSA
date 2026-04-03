# PyPSA Demo Environment — Utilities Vertical

A self-contained demo environment showcasing Devin's capabilities with [PyPSA](https://pypsa.org) (Python for Power System Analysis) for Utilities vertical leadership.

## Quick Start

```bash
# Install dependencies (one command)
cd /path/to/PyPSA && uv sync --all-extras

# Launch Jupyter Lab with the demo notebooks
uv run jupyter lab demo/notebooks/
```

Then run the notebooks in order:
1. **01_capacity_expansion.ipynb** — Least-cost decarbonization pathway (~30s to solve)
2. **02_grid_optimization.ipynb** — German grid power flow optimization (~20s to solve)

---

## What the Demo Shows

### Notebook 1: Capacity Expansion Planning

**Audience hook:** *"What is the least-cost generation mix to decarbonize Germany's grid by 2030?"*

```
┌──────────────────────────────────────────────────────────────────┐
│                    CAPACITY EXPANSION MODEL                      │
│                                                                  │
│   Inputs:                    Optimizer:         Outputs:          │
│   ┌──────────┐              ┌─────────┐       ┌──────────────┐  │
│   │ Wind CF  │──┐           │         │       │ Optimal Mix  │  │
│   │ Solar CF │──┤    ┌─────>│  LOPF   │──────>│ Dispatch     │  │
│   │ Demand   │──┤    │      │ (HiGHS) │       │ Storage SOC  │  │
│   │ Costs    │──┘────┘      │         │       │ Prices       │  │
│   └──────────┘              └─────────┘       │ Cost Brkdown │  │
│                                               └──────────────┘  │
│   Technologies: Wind, Solar, Battery (4h), H2 (seasonal), Gas   │
└──────────────────────────────────────────────────────────────────┘
```

**Visualizations produced:**
- Input time series (demand, wind/solar capacity factors)
- Optimal capacity bar chart (GW by technology)
- Hourly dispatch stack (winter vs summer weeks)
- Battery & hydrogen storage state-of-charge
- Cost breakdown (CAPEX vs OPEX, pie chart)
- Marginal price time series and duration curve

### Notebook 2: German Grid Optimization (SciGRID)

**Audience hook:** *"How do power flows look across a real 585-bus transmission network under N-1 constraints?"*

```
┌──────────────────────────────────────────────────────────────────┐
│                  GERMAN GRID (SciGRID) MODEL                     │
│                                                                  │
│   585 Buses ─── 852 Lines ─── 1,423 Generators ─── 489 Loads    │
│                                                                  │
│   ┌─────────┐     ┌──────────┐     ┌──────────────────────────┐ │
│   │ Network │────>│  LOPF    │────>│ Power Flow Maps          │ │
│   │  Data   │     │ (N-1)    │     │ Line Loading Heatmaps    │ │
│   │ (NetCDF)│     │ 70% cap  │     │ Congestion Analysis      │ │
│   └─────────┘     └──────────┘     │ Nodal Price Spreads      │ │
│                                    │ Dispatch by Technology    │ │
│                                    └──────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

**Visualizations produced:**
- Generation capacity by technology (bar chart)
- Geographic maps: load distribution, generation by fuel type
- Power flow visualization on the network
- Line loading distribution and top congested corridors
- Hourly dispatch stack area chart
- Nodal price distribution and congestion rent spreads

---

## 3-Prompt Demo Script

Following the Ask Devin → Ask Devin → Execute pattern:

### Prompt 1 — Ask Devin (Discover)

> What renewable energy scenarios can PyPSA model, and what built-in example networks are available for demonstrating grid optimization?

**Expected outcome:** Devin explores the codebase, identifies `pypsa.examples` (ac_dc_meshed, storage_hvdc, scigrid_de, model_energy, stochastic_network, carbon_management) and describes the modeling capabilities (ED, LOPF, SCLOPF, CEP, pathway planning, stochastic optimization, MGA, sector coupling).

### Prompt 2 — Ask Devin (Scope/Plan)

> Analyze our PyPSA repo's demo notebooks and recommend what changes would make them more compelling for a utility executive audience focused on decarbonization costs.

**Expected outcome:** Devin reads the demo notebooks, identifies the key charts and analysis, and produces a scoped plan for enhancements (e.g., add CO2 constraint sensitivity, include curtailment analysis, add sector coupling to the capacity model, enhance geographic visualizations with interactive maps).

### Prompt 3 — Devin Session (Execute)

> Run the capacity expansion notebook end-to-end and create an executive summary of the least-cost generation mix for Germany 2030, including charts for optimal capacity, dispatch, and cost breakdown.

**Expected outcome:** Devin runs the notebook, extracts the optimization results, generates publication-quality charts, and writes an executive summary with key findings (e.g., "Wind at 85 GW dominates the optimal mix; battery handles daily cycling; hydrogen provides seasonal balancing; system LCOE of ~EUR 55/MWh").

---

## Technical Details

### Dependencies
- **Python 3.11+** with `uv` package manager
- **PyPSA** (latest from repo) + all optional extras
- **HiGHS** solver (free, installed by default with PyPSA)
- **Cartopy** for geographic projections (optional but recommended)
- All data from PyPSA built-in examples — zero external data files needed

### Solver
Both notebooks use the [HiGHS](https://highs.dev/) open-source solver, which ships with PyPSA by default. No commercial solver licenses needed.

### Data Sources
- **Technology costs:** [PyPSA technology-data](https://github.com/PyPSA/technology-data) (2030 projections)
- **Time series:** TU Berlin cloud storage (wind, solar capacity factors + demand for Germany)
- **Grid data:** [SciGRID](https://openenergyplatform.org/factsheets/models/22/) (German transmission network from OpenStreetMap)

---

## Key PyPSA Concepts for Demo Presenters

| Concept | What It Means | Why Utilities Care |
|---------|--------------|-------------------|
| **LOPF** | Linear Optimal Power Flow | Least-cost dispatch respecting grid physics |
| **CEP** | Capacity Expansion Planning | Long-term investment optimization |
| **N-1 Security** | System survives any single line outage | Regulatory compliance requirement |
| **LMP** | Locational Marginal Price | Wholesale market price formation |
| **Sector Coupling** | Electricity + heat + hydrogen + transport | Future integrated energy planning |
| **Extendable** | Capacity as optimization variable | "How much should we build?" |
| **Snapshot Weighting** | Hours each timestep represents | Temporal resolution vs speed tradeoff |
