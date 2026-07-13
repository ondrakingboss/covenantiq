# CovenantIQ portfolio talking points

## For finance recruiters

- I built CovenantIQ to show that I understand both the mechanics and the review process behind private-credit underwriting.
- The model covers debt roll-forwards, leverage, coverage, DSCR, liquidity, quarterly covenant compliance, downside cases, and Sources & Uses.
- Ironbridge demonstrates a distressed decline with a first quarterly breach; Vantage demonstrates a healthier approval case.
- Every recommendation can be challenged: the Audit Trail exposes the rule, value, threshold, period, scenario, and calculation reference.
- The borrower data, thresholds, and credit policies are fictional. This is an educational underwriting model, not a lender-calibrated system.

## For fintech and product reviewers

- The product is designed around a reviewer question: “Why did the system reach this conclusion?”
- Inputs flow once through calculation engines and are reused across the workspace, scenario views, comparison, Audit Trail, and memo.
- Guided demos reduce time-to-understanding for three stories: healthy approval, distressed decline, and conservative-versus-aggressive structure.
- Saved analyses preserve exact snapshots, so reopening a case does not silently run it through changed assumptions.
- The UI favors dense tables, explicit units, restrained status colors, and print output over decorative dashboard elements.

## For engineering reviewers

- FastAPI and React are presentation boundaries; deterministic Python services own the finance logic.
- Pydantic models validate debt tranches, covenants, scenarios, persistence payloads, and API responses.
- Ratio edge cases return structured statuses instead of misleading zeroes.
- The backend, not the browser, calculates sensitivity cells, comparison scores, safer-structure selection, and recommendation traces.
- The release has 26 passing backend tests and a verified Next.js production build.
- Deployment uses explicit CORS origins and a persistent-disk path for SQLite; managed PostgreSQL is the correct next step for multi-instance use.

## For internship networking messages

Short version:

> I built CovenantIQ, a full-stack private-credit analysis portfolio project. It models multi-tranche debt, quarterly covenant compliance, downside sensitivity, and saved deal comparisons, then explains a rules-based recommendation through an Audit Trail and IC memo. All financial calculations are deterministic Python functions. I’d value your perspective on whether the workflow reflects how an analyst would review a deal.

More technical version:

> I recently completed CovenantIQ v1.0, a Next.js and FastAPI private-credit workbench with independent Python finance engines, Pydantic validation, SQLite snapshots, 26 backend tests, and a production frontend build. I focused on traceability: every decision links to a metric, threshold, period, and scenario. It is an educational model rather than a production lending system, and I’d appreciate feedback on the architecture or credit workflow.

## LinkedIn post copy

I built **CovenantIQ v1.0**, an educational private-credit analysis platform designed around one question: can every credit conclusion be traced back to its inputs and rules?

The project models multi-tranche debt, annual and quarterly covenant compliance, downside scenarios, a 42-cell sensitivity grid, saved deal structures, and an investment-committee memo. A deterministic Python engine calculates every financial metric, covenant result, comparison score, and recommendation—no LLM is used for financial calculations.

Two demo cases make the workflow concrete: Vantage Services shows a healthier approval story, while Ironbridge Components shows a decline with an early quarterly breach. The Audit Trail explains the exact rule and threshold evidence behind each decision.

Stack: Next.js, TypeScript, Tailwind CSS, Recharts, FastAPI, Pydantic, SQLite, and Pytest. Verification: 26 backend tests passing and a successful frontend production build.

CovenantIQ is a portfolio project, not a production lending system or financial advice. I built it to demonstrate private-credit mechanics, explainable product design, and deterministic financial engineering. Feedback from credit, fintech, and engineering practitioners is welcome.
