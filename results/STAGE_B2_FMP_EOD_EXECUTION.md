# Amended Stage B2 EOD acquisition execution

Status: Prospective amendment recorded; acquisition attempted and blocked by HTTP 402.

## Amendment and scope

EXPERIMENT.md Amendment A2 and DATA_AUDIT.md now record the user's explicit authorization to raise the cumulative Stage B transfer ceiling from 2 GB to 4,000,000,000 bytes, keeping 1,500 requests. FMP EOD Bulk close × volume operationalizes the liquidity screen; adjClose is never retained or used. FMP does not explicitly guarantee regular-session-only volume. This is a prospective measurement-source limitation, not a threshold change. Previous close ≥$10, median over all preceding 20 completed exchange sessions ≥$20M, and every other hypothesis/signal/split/holdout/outcome rule remain unchanged. The amendment was recorded before acquisition and before any strategy-return inspection.

## Calendar and projection

The bounded NYSE equity calendar was verified against ICE's official 2023–2025 holiday/early-close notice and the separate 2025-01-09 mourning closure. Acquisition includes 710 exchange sessions from 2023-03-06 through 2025-12-31: 20 completed sessions before the first train entry plus all development sessions. Early closes remain sessions. No 2026 observations or calendar extension is requested.

At the provider's approximate 4 MB/file allowance, initial cumulative acquisition projects to 1,006 requests and 2,907,654,974 bytes, within the amended caps. This is not a measured-size guarantee; the runner enforces actual cumulative limits and refuses automatic retries of an incomplete manifest.

## Actual execution

One request executed:

`GET https://financialmodelingprep.com/stable/eod-bulk?date=2023-03-06`

Authentication omitted intentionally. The credential was loaded from the project ignored .env file into process memory without printing or logging it.

Result: **HTTP 402**, 177 response-body bytes, no retained EOD records. The status indicates a payment/entitlement access restriction, but the exact account cause was not investigated through additional probes or exposed raw response material. A successful earnings-calendar entitlement does not establish EOD Bulk entitlement.

Cumulative recorded acquisition: **297 requests and 67,655,151 bytes**, including Stage B1 and the completed Massive pilot. No purchase, subscription change, retry, redirect, or request expansion occurred.

## Remaining work

Liquidity filters, survivor counts, historical-reference request estimates, and Stage C remain unexecuted because no complete EOD data were acquired. The timed subset and its one conflicting pair remain unchanged. No survival results were fabricated or inferred from the prior planning counts.

Ready implementation: scripts/fmp_eod_stage_b2.py; bounded calendar: scripts/development_calendar.py. Local syntax and calendar-boundary checks passed before execution. Screening evaluates each candidate using only the 20 strictly preceding completed sessions, requires every observation, uses Decimal threshold comparisons, excludes conflicting timing and outside-development D, and keeps historical reference and fiscal-period validation pending. It never calculates returns/P&L. No screening output is claimed to exist.

To resume, resolve EOD Bulk account access without exposing credentials or provide an authorized equivalent dataset. The current execution stopped on the first HTTP failure. No additional feasibility probes were added.

## Safeguards

No holdout observations, post-entry returns/P&L, EPS/revenue/estimates/surprises, backtest or strategy outcomes were inspected. No adjClose was used. No packages, GPU requests or Slurm jobs were launched. Raw responses, headers, credential-bearing URLs and exceptions were not displayed or retained.

Calendar evidence:
- https://ir.theice.com/press/news-details/2022/NYSE-Group-Announces-2023-2024-and-2025-Holiday-and-Early-Closings-Calendar/default.aspx
- https://ir.theice.com/press/news-details/2024/The-New-York-Stock-Exchange-Will-Close-Markets-on-January-9-to-Honor-the-Passing-of-Former-President-Jimmy-Carter-on-National-Day-of-Mourning/default.aspx
