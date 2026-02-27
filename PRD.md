# Master Product Requirements Document: Wealthsimple Financial OS (Prototype)

## 1. Product Overview
The Wealthsimple Financial OS is a monthly AI decision engine that evaluates a user’s complete financial state and identifies the single highest-leverage financial action they can take. 

It replaces fragmented financial advice, spreadsheet tracking, and reactive decision-making with one clear, data-backed directive. **This system is not a chatbot.** It runs autonomously on a monthly cadence and surfaces one prioritized action requiring human approval.

### Core Promise
Every month, the system identifies **the single highest-leverage financial action** available to the user.

---

## 2. Problem Space & Target Persona

### The Problem
Retail investors currently face significant hurdles in managing their wealth effectively:
* Information overload and fragmented advice.
* Emotional decision-making, leading to anxiety during market volatility.
* No clear prioritization of tasks.
* Lack of a unified system that integrates cash flow, portfolio allocation, risk exposure, goal progress, tax efficiency, and liquidity into one ranked action.

### User Persona
* **Profile:** Retail investor
* **Assets:** $50k–$500k
* **Account Types:** Registered + non-registered accounts
* **Risk Profile:** Medium risk tolerance
* **Timeline:** Medium-term goal (e.g., home purchase, retirement)

---

## 3. System Architecture & Technical Specifications

The system strictly isolates deterministic math from generative AI. The LLM **does not** perform math or financial calculations; all projections are deterministic and structured.
 
### System Components
1.  **Deterministic Financial Core:** Handles all calculations and current state evaluations.
2.  **Scenario Simulation Engine:** Runs structured projections and stress tests.
3.  **Action Scoring Framework:** Evaluates and ranks potential actions.
4.  **LLM Explanation Layer:** Interprets the output into plain language.
5.  **Lightweight UI:** Displays the snapshot, ranked action, and approval mechanism.

### Data Inputs & Outputs
**Inputs:** Income, Expenses, Savings, Asset allocation, Goal timeline, Risk profile.
**Outputs:** Savings rate, Liquidity ratio, Goal funding gap, Risk exposure.

---

## 4. Core Capabilities & Mechanics

### 1. Scenario Simulation Engine
The engine uses a Simplified Monte Carlo method (100 runs) with assumed return bands by asset class and volatility adjustments.
* **Scenarios Modeled:**
    * Base case
    * Recession case (-20% equity shock)
    * Bull case (+15% growth)
    * Rate spike case
* **Outputs:** Probability of goal achievement, drawdown exposure, and liquidity stress.

### 2. Action Generation
The system dynamically generates 5–7 candidate actions based on the user's current state.
* *Example:* If liquidity is < 3 months → Generate "Increase emergency fund" action.
* *Candidate Actions:* Increase monthly contribution, reallocate asset mix, increase emergency fund, pay down debt, optimize tax contribution.

### 3. Action Scoring Framework
Each generated action is objectively evaluated using a weighted formula:
> **Score =** (Goal Improvement Weight × Δ Goal Probability) + (Risk Adjustment Weight × Δ Risk Reduction) + (Tax Efficiency Weight × Δ Tax Impact)

### 4. LLM Explanation Layer
The LLM takes the ranked action, supporting metrics, tradeoffs, and scenario deltas as input to generate:
* A clear, <150-word explanation.
* Explicit risk warnings and tradeoff disclosures.
* An explanation of why alternatives ranked lower.

---

## 5. AI System Design & Governance

### Division of Responsibilities
**AI Owns:**
* Interpreting structured financial outputs and scenario deltas.
* Ranking actions based on the deterministic scoring framework.
* Communicating tradeoffs, explaining uncertainty, and formatting the narrative.

**Human Owns (System Guardrails):**
* Defining risk tolerance and value judgments.
* Executing/approving the final action.
* **Critical Decision:** Any major capital reallocation that materially alters the risk profile (e.g., altering asset allocation beyond a 15% equity shift requires explicit human approval). *Reason: Risk tolerance reflects emotional capacity and life context, not just expected return.*

### Strict Guardrails
* No auto-execution of trades or asset movements.
* No dynamic trading.
* No tax interpretation beyond predefined logic.
* No hallucinated financial assumptions or overriding user intent.

### Failure Modes & Mitigations
| Failure Mode | Mitigation Strategy |
| :--- | :--- |
| Edge case financial complexity | Rely exclusively on the deterministic core. |
| Regulatory constraints | Strict schema-based LLM prompts and compliance checks. |
| Model explanation hallucination | Implement confidence scoring and audit logging. |
| Over-personalization drift | Keep boundaries rigid; AI does not redefine user intent. |

---

## 6. Success Criteria & Demo Flow

### Prototype Success Criteria
* Displays a clear financial snapshot.
* Successfully evaluates 5 dynamic actions.
* Surfaces 1 clearly ranked action.
* Provides an LLM explanation under 150 words.
* Includes a clear, un-hallucinated tradeoff disclosure.

### 3-Minute Demo Script Outline
1.  **Intro:** Introduce the user profile.
2.  **Snapshot:** Show the current financial state.
3.  **Behind the Scenes:** Show the 5 evaluated actions and the math/ranking logic behind them.
4.  **The Reveal:** Highlight the #1 recommended action.
5.  **Impact:** Show the before/after projection based on the simulation engine.
6.  **Context:** Explain the tradeoffs and why other actions failed to take the #1 spot.
7.  **Execution:** Show the human approval step.
8.  **Wrap-up:** Explain the AI boundary (deterministic math vs. generative explanation).
9.  **Closing Line:** *"This system reduces complexity to one clear lever per month."*