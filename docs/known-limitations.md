# Known limitations

- Demo borrowers are fictional. Quarterly phasing is simplified and derived from annual projections rather than a monthly operating model.
- Taxes, depreciation, working capital, and lease fixed charges are simplified proxies rather than full accounting schedules.
- Revolver mechanics do not include borrowing bases, intra-quarter draws, letters of credit, or springing availability tests.
- Multi-tranche schedules do not model SOFR floors, hedges, OID yield, tax shields, or exact day count.
- Optional repayment uses a simplified 25% excess-cash-flow sweep.
- Scenario shocks are parallel annual shocks, not probabilistic forecasts or correlated macro paths.
- Memo output is print-optimized HTML, not a server-rendered PDF file.
- SQLite persistence has no authentication, authorization, approval workflow, or multi-user isolation.
- SQLite requires a single stateful backend instance and a persistent disk. Ephemeral or serverless filesystems will lose saved analyses, and horizontal application replicas are unsupported.
- Covenant thresholds are illustrative and are not calibrated to a real lender's policy.
- Legal covenant documents are not parsed; baskets, cure rights, EBITDA add-backs, and legal definitions are not modeled.
- Recommendation rules are intentionally preliminary and require human review.
- Audit explanations trace implemented rules but cannot capture undocumented judgment, policy exceptions, or legal interpretation.
- Deal-comparison safety scores are relative educational heuristics and are not statistically calibrated or lender-approved.
- `npm audit` reports two moderate PostCSS advisories through Next.js's internally bundled PostCSS 8.4.31. The direct PostCSS dependency is patched at 8.5.10, but the current stable Next.js 16.2.10 bundle cannot be overridden without upstream changes.

## Disclaimer

CovenantIQ is an educational portfolio project. It does not constitute lending, investment, accounting, legal, or financial advice, and it does not replace professional credit judgment, lender policy, legal-document review, or independent verification of borrower information.
