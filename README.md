
# Wealthsimple Pulse

**Your monthly financial pulse check — powered by deterministic math and AI interpretation.**

Pulse is a prototype AI-native financial decision engine that identifies the single highest-leverage financial action a user can take each month. It replaces fragmented advice, reactive decision-making, and information overload with one clear, data-backed directive.

> *"This system reduces complexity to one clear lever per month."*

---

## The Problem

Retail investors managing $50K–$500K face a paradox: they have more financial tools than ever, yet still struggle with **what to actually do next**. The typical experience looks like this:

| Pain Point | What Users Do Today | What Pulse Does |
|---|---|---|
| **Information overload** | Scroll through news, Reddit, and 10 different dashboards | Surfaces one ranked action with supporting evidence |
| **Emotional decisions** | Panic-sell during dips, FOMO-buy at peaks | Deterministic scoring immune to market sentiment |
| **No prioritization** | "Should I increase my TFSA? Pay debt? Rebalance?" | Evaluates all options and picks the mathematically optimal one |
| **Fragmented advice** | Generic tips from blogs, robo-advisors that only rebalance | Personalized to income, expenses, goals, risk tolerance, and real market data |

### Who This Is For

A **mid-career professional** (25–45) with registered and non-registered accounts, saving toward a medium-term goal (home purchase, retirement), who wants clarity without becoming a finance expert.

---

## How It Works

Pulse runs a three-layer pipeline every time the user requests a monthly evaluation:

<img width="888" height="1477" alt="chart" src="https://github.com/user-attachments/assets/0c8a63a6-4435-439e-bd68-a2bb053eb7f1" />


### The Critical Design Decision

**The AI does not make financial decisions.** It interprets them. Every number the user sees — goal probability, projected portfolio value, risk scores, action rankings — comes from the deterministic engine. The LLM's only job is to translate structured data into a clear narrative. If the AI layer fails entirely, the system still works.

This architecture is intentional: financial advice has a regulatory surface area. By isolating the AI to interpretation-only, Pulse avoids the hallucination risk that plagues LLM-first financial tools.

---

## Live Example

Here's what Pulse produces for a sample user profile:

**Profile:** Sarah, 32 · $120K income · $4K/mo expenses · $85K portfolio (60/30/10 equity/bond/cash) · $500K home goal in 10 years · Medium risk

### Evaluation Results

| Metric | Value | Context |
|---|---|---|
| Savings Rate | 60.0% | $6,000/mo surplus after expenses |
| Liquidity Ratio | 6.25 months | Above the 6-month emergency threshold |
| Goal Probability (Base) | 100.0% | On track under normal conditions |
| Goal Probability (Recession) | 81.0% | Resilient even with -20% equity shock |
| Goal Probability (Bull) | 100.0% | Significant upside in strong markets |
| Risk Exposure | 43.5% | Moderate — aligned with medium tolerance |

### Ranked Actions

```
 #   Action                               Score    Why
 ─── ──────────────────────────────────── ──────── ────────────────────────────────────────
 ⭐ 1  Increase monthly contribution +10%   1.000   Strongest goal acceleration (+4.5% prob)
 2   Increase bond allocation +10%         0.928   Reduces volatility, small goal tradeoff
 3   Maintain emergency fund               0.909   Preserves existing strong liquidity
 4   Increase equity allocation +10%       0.829   Higher return potential, higher risk
 5   Pause contributions temporarily       0.000   Actively harmful to goal progress
```

### Scenario Projections

```
 Scenario      Return    Projected Value    Goal Probability
 ──────────── ──────── ──────────────────── ────────────────
 🔵 Base        9.0%     $503,387            100.0%
 🔴 Recession   5.5%     $404,900             81.0%
 🟢 Bull       11.7%     $597,252            100.0%
```

### AI Narrative (generated from deterministic output)

> *Sarah, increasing your monthly contribution by 10% to $1,650 accelerates your home purchase timeline with a projected 4.5% improvement in goal probability. Your current savings rate of 60.0% and 6.25 months of emergency reserves provide a strong foundation — this action builds on that momentum without introducing new risk. Under recession conditions, your goal probability remains 81.0%, demonstrating resilience across macro scenarios.*

---

## Real Market Data Integration

Pulse doesn't use hardcoded return assumptions. It fetches real historical data from Yahoo Finance for a preset portfolio of Canadian-relevant ETFs that mirror what a Wealthsimple user would actually hold:

### Equity Bucket

| ETF | Description | Weight | Role |
|---|---|---|---|
| **VFV.TO** | Vanguard S&P 500 Index ETF | 40% | Core US large-cap |
| **QQQ** | Invesco Nasdaq 100 ETF | 30% | Tech/growth exposure |
| **XEQT.TO** | iShares Core Equity ETF Portfolio | 30% | Global diversification |

### Bond Bucket

| ETF | Description | Weight | Role |
|---|---|---|---|
| **ZAG.TO** | BMO Aggregate Bond Index ETF | 60% | Canadian bond core |
| **XBB.TO** | iShares Core Canadian Bond ETF | 40% | Canadian bond diversification |

The blended returns from these ETFs replace static assumptions, meaning:
- **Projections say** "based on VFV.TO, QQQ, XEQT.TO 5-year historical performance" instead of "assumed 6%"
- **Scenario analysis** applies recession shocks to real base returns, not theoretical ones
- **The AI explanation** can reference actual tickers and market context

If Yahoo Finance is unavailable, the system gracefully falls back to conservative hardcoded returns and notes this in the UI. The engine never breaks.

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| **API** | FastAPI (Python 3.11) | Async, typed, auto-documented, fast |
| **Data Validation** | Pydantic v2 | Strict typing, serialization, clear model contracts |
| **Market Data** | yfinance | Real ETF prices and returns, no API key needed |
| **AI Layer** | OpenAI GPT-4o-mini | Cost-efficient, fast, structured JSON output |
| **Frontend** | Vanilla HTML/CSS/JS | Zero framework overhead, pure SVG charts, instant load |
| **Server** | Uvicorn ASGI | Production-grade async server |
| **Persistence** | localStorage (MVP) | Client-side profile storage, no database needed |

### Why No React / Next.js / Tailwind?

This is a deliberate choice. The frontend is a single page with ~835 lines of JavaScript that renders SVG charts, manages a multi-step wizard, calls two API endpoints, and handles all state. Adding a framework would increase bundle size, build complexity, and time-to-first-paint — all for zero functional benefit at this scope. The result loads instantly and has zero dependencies.

---

## Architecture

```
backend/
├── main.py                     # FastAPI app, CORS, static files
├── models/
│   ├── user_profile.py         # UserProfile with personal context fields
│   ├── financial_state.py      # FinancialState + ScenarioResult
│   ├── action.py               # Action + ScoredAction
│   ├── explanation.py          # ExplanationRequest + AIExplanation
│   ├── market_data.py          # Holding + MarketContext
│   └── response.py             # EvaluationResponse + TopRecommendation
├── services/
│   ├── state_engine.py         # Financial state computation + scenarios
│   ├── simulation_engine.py    # Action simulation (apply + project)
│   ├── action_generator.py     # Dynamic candidate action generation
│   ├── action_scorer.py        # Risk-profile-weighted scoring
│   ├── ranking_engine.py       # Full pipeline: generate → simulate → score → rank
│   ├── market_data.py          # Yahoo Finance integration + caching
│   └── llm_engine.py           # OpenAI integration + strict prompting
└── routes/
    ├── evaluate.py             # POST /api/evaluate
    └── explain.py              # POST /api/explain

frontend/
├── index.html                  # Onboarding wizard + dashboard layout
├── app.js                      # All rendering, charts, API calls, state
└── style.css                   # Wealthsimple-inspired design system
```

### API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/evaluate` | Accepts user profile, returns financial snapshot + ranked actions + market data |
| `POST` | `/api/explain` | Accepts pre-computed results, returns AI narrative explanation |
| `GET` | `/` | Serves the frontend application |

---

## How This Would Work on Wealthsimple's Platform

### Integration Points

Pulse is designed to slot into Wealthsimple's existing product surface:

1. **Data sources already exist.** Wealthsimple has income (via direct deposit), expenses (via spending categories), portfolio value and allocation (investment accounts), contribution history, and goal settings. Pulse's `UserProfile` maps directly to data Wealthsimple already collects.

2. **Monthly cadence fits the product.** Wealthsimple already sends monthly portfolio updates. Pulse replaces "your portfolio went up 2.3%" with "here's what you should do next month and why."

3. **Approval workflow aligns with compliance.** Pulse never auto-executes. The "Approve Action" button maps to existing order/contribution flows. The human-in-the-loop design satisfies regulatory requirements for investment recommendations.

4. **AI layer uses Wealthsimple's existing LLM infrastructure.** The explanation layer is a single API call with structured prompting — it can run on any LLM endpoint.

### User Journey on Wealthsimple

```
Monthly notification
    → "Your Pulse is ready"
    → Open app → See top action + confidence score
    → Tap to see supporting data (scenarios, alternatives)
    → "Approve" → Wealthsimple executes contribution increase / rebalance
    → Done. One decision. One tap. Back to life.
```

### Why This Matters for Retention

| Metric | Impact |
|---|---|
| **Monthly active engagement** | Users return monthly for their Pulse — not just when markets crash |
| **Decision fatigue reduction** | One action instead of 10 tabs of conflicting advice |
| **Trust through transparency** | Users see the math, the alternatives, the tradeoffs |
| **Premium differentiation** | No robo-advisor shows *why* it chose an action or what it rejected |
| **Reduced support tickets** | "What should I do?" is answered proactively |

### Competitive Positioning

No Canadian fintech currently offers this combination:

| Feature | Wealthsimple Today | Betterment | Pulse |
|---|---|---|---|
| Portfolio rebalancing | Automatic | Automatic | N/A (decision layer, not execution) |
| Goal tracking | Basic progress bar | Basic progress bar | Multi-scenario probability |
| Action recommendations | None | Tax-loss harvesting only | Dynamic ranked actions |
| AI explanations | None | None | Structured narrative with tradeoffs |
| Scenario analysis | None | None | Base / Recession / Bull projections |
| Human approval workflow | N/A | N/A | Explicit approve/defer controls |

---

## Running Locally

### Prerequisites

- Python 3.11+
- OpenAI API key (optional — the app works without it using deterministic fallback)

### Setup

```bash
# Clone the repository
git clone https://github.com/your-username/wealthsimple-pulse.git
cd wealthsimple-pulse

# Install dependencies
pip install -r requirements.txt

# (Optional) Set up AI layer
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Start the server
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

# Open in browser
# http://127.0.0.1:8000
```

### What You'll See

1. **Onboarding wizard** — 6-step guided setup (name, life stage, finances, investments, goal, review)
2. **Loading animation** — phased steps as market data is fetched and analysis runs
3. **Dashboard** — AI recommendation card, SVG charts (goal ring, allocation donut, metric bars), scenario cards, action comparison, collapsible analysis detail, portfolio performance chart, holdings table

### Without an OpenAI Key

The app still works. The AI brief is replaced with a deterministic fallback that generates a narrative from the computed data. The experience is identical — you just see "Deterministic analysis" instead of "AI interpretation" in the source label.

---

## AI Guardrails

Pulse takes AI safety seriously. The LLM is constrained at multiple levels:

| Guardrail | Implementation |
|---|---|
| **No calculation** | LLM receives pre-computed numbers only; prompt explicitly bans recalculation |
| **Banned phrases** | "I think", "I believe", "you should", "I recommend" are prohibited |
| **Few-shot example** | Full example output in system prompt eliminates format drift |
| **Temperature 0.15** | Tight variance for consistent tone and structure |
| **Confidence clamping** | LLM's confidence score is overridden by deterministic bounds based on score gap |
| **Forced JSON output** | `response_format={"type": "json_object"}` prevents free-form responses |
| **Mandatory disclaimer** | Server-side enforcement of disclaimer regardless of LLM output |
| **No auto-execution** | No endpoint triggers trades; all actions require explicit human approval |
| **Graceful degradation** | If AI fails, deterministic brief is generated client-side |

---

## Why Build This

Wealthsimple's mission is to make financial services accessible and simple. But "simple" today means *fewer features* — simpler portfolios, simpler UIs, simpler tools. Pulse redefines "simple" as *fewer decisions*:

- Not "here are your 7 account balances" → "here's the one thing to do"
- Not "your portfolio returned 8.2%" → "here's what that means for your home purchase goal"
- Not "consider rebalancing" → "increase your monthly contribution by $150 because it has the highest impact on your goal probability, and here's what happens if the market crashes"

This is the kind of product that turns passive investors into confident ones — without requiring them to learn finance.

---

## License

Built for the [Wealthsimple AI Builder](https://jobs.ashbyhq.com/wealthsimple/f7e4d9e1-2774-4a21-99b6-02e1e4120cef) submission.
