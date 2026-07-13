# CovenantIQ v1.0 API

The API preserves the annual endpoints and extends them with private-credit, persistence, comparison, and guided-demo workflows. Interactive OpenAPI documentation is available at `/docs`.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Service identity and deterministic calculation-mode status |
| GET | `/borrowers` | Five checked-in fictional demo borrowers |
| GET | `/borrowers/{borrower_id}` | One normalized borrower dataset |
| POST | `/loans/analyze` | Legacy single-loan annual analysis |
| POST | `/scenarios/run` | Legacy scenario results |
| POST | `/covenants/test` | Legacy covenant test |
| POST | `/credit-memo/generate` | Legacy print-optimized memo |
| POST | `/private-credit/analyze` | Multi-tranche annual and quarterly analysis |
| POST | `/sensitivity/run` | Revenue and EBITDA-margin sensitivity matrix |
| POST | `/credit-memo/generate-v2` | Investment-committee HTML memo plus sensitivity |
| POST | `/analyses` | Calculate and save an analysis |
| GET | `/analyses` | List saved-analysis summaries |
| GET | `/analyses/{analysis_id}` | Reopen stored request and response |
| DELETE | `/analyses/{analysis_id}` | Delete a saved case |
| POST | `/analyses/compare` | Compare two to four saved structures for one borrower |
| GET | `/guided-demos` | Return validated reviewer walkthroughs and routes |

The private-credit request contains `borrower_id`, `debt_structure.tranches`, covenant definitions, scenario IDs, minimum cash, sweep percentage, and sources-and-uses inputs. FastAPI publishes complete schemas and validation errors at `/docs`.

`POST /private-credit/analyze` now includes an `audit_trail` object containing all evaluated rules, trigger state, exact evidence comparisons, covenant breaches, scenario drivers, first breach, calculation references, and a deterministic plain-language explanation.
