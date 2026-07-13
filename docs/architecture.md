# Architecture

CovenantIQ is a portfolio-oriented monorepo with a Next.js presentation layer and a FastAPI calculation service. It runs locally or as a split Vercel frontend and stateful backend deployment.

## Request flow

1. The frontend loads a normalized borrower dossier from `GET /borrowers/{id}`.
2. The analyst submits loan terms, covenant thresholds, and scenarios to `POST /loans/analyze`.
3. The backend loads immutable JSON demo inputs and normalizes all six periods.
4. Each scenario transforms projected operating statements and working capital.
5. The debt engine rolls debt and interest using scenario-adjusted rates.
6. The ratio engine calculates structured metrics with explicit statuses.
7. The covenant engine applies direction-aware headroom and breach logic.
8. The recommendation engine evaluates transparent decision rules.
9. The same response drives tables, charts, explanations, and memo HTML.

The private-credit path is additive. `/loans/analyze` retains the verified single-loan behavior. `/private-credit/analyze` orchestrates tranche schedules, annual consolidated ratios, eight quarterly periods, and quarterly covenants. `/sensitivity/run` evaluates a deterministic two-dimensional grid. `/analyses` persists exact request and response JSON in SQLite.

## Module boundaries

- `financial_engine.py`: source loading, statement normalization, reconciliation checks
- `debt_engine.py`: term-loan funding, refinancing, amortization, optional sweep, interest
- `ratio_engine.py`: formula-level metrics and edge-case statuses
- `covenant_engine.py`: covenant mapping, headroom, severity, first breach
- `scenario_engine.py`: statement and working-capital transformations
- `recommendation_engine.py`: preliminary rule-based outcome
- `memo_engine.py`: print-optimized HTML projection of calculated results
- `quarterly_engine.py`: annual-to-quarter phasing, quarterly cash roll-forward, and covenant period adapters
- `private_credit_service.py`: multi-tranche annual and quarterly orchestration
- `sensitivity_engine.py`: revenue and margin grid evaluation
- `persistence.py`: SQLite schema initialization and saved-analysis CRUD
- `audit_engine.py`: recommendation rules, exact evidence comparisons, breach inventory, and calculation references
- `comparison_engine.py`: saved-structure metrics, safety scoring, and safer-structure rationale
- `guided_demo_service.py`: validated reviewer walkthrough metadata
- `analysis_service.py`: orchestration only
- `routers/api.py`: validation, HTTP concerns, and readable errors

Calculation services have no FastAPI dependency and can be tested directly.

## Persistence

Fictional borrower assumptions are stored in `backend/app/data/borrowers.json`. Saved private-credit cases are stored in SQLite. There is no authentication or multi-user isolation.

Saved comparison is server-side. The API loads exact stored responses, extracts base metrics and quarterly covenant tests, calculates each disclosed safety-score component, and returns the safer structure. The frontend does not recreate financial or scoring logic.
