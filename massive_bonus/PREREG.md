# Massive bonus preregistration: repurchase disclosures → cash-secured put

Status: hypothesis and user-specified configuration frozen before any bonus results are inspected. Execution is blocked until the official organizer starter is obtained and its unchanged implementation details are verified. This is separate from the sealed main DriftMaxx analysis.

## Signal and taxonomy

Actual signal: Massive `/stocks/filings/8-K/vX/disclosures` records with exact `tertiary_category=share_repurchase_program`, taxonomy `1.0`.

The taxonomy-only lookup returned all 119 categories before any bonus filing/outcome queries. The exact definition is **“Share buyback program authorization, expansion, or update with amount and timing.”** Hierarchy: `capital_and_financing` → `shareholder_returns` → `share_repurchase_program`. The tag includes expansions and updates as well as new authorizations; it must not be represented as exclusively new authorizations. No category was selected using returns.

## Economic hypothesis and competing hypothesis

A newly authorized repurchase creates a credible source of future equity demand and downside support, but the filing itself may temporarily elevate perceived event uncertainty. After the disclosure becomes public, the market may therefore price downside protection more richly than subsequent realized downside warrants. A cash-secured put should benefit if the stock remains flat-to-up and event volatility normalizes. The competing hypothesis is that repurchase announcements contain no incremental support or coincide with deteriorating fundamentals, in which case short-put returns should not outperform ordinary days. This mechanism has not been demonstrated.

## Exact permitted strategy

**Cash-secured put.** The five organizer-permitted strategies, supplied and verified by the user, are Long call, Covered call, Protective put, Collar, and Cash-secured put. Only the cash-secured put hypothesis is selected; no strategy search is authorized.

## Frozen configuration

- Entry: official starter `ENTRY="post"`, close of filing session `t_0`. Do not change to pre-filing or next-session entry. Filing-session alignment, public-availability checks and any exclusions must follow verified starter rules; same-day close must not be presented as attainable for an after-close announcement.
- Headline expiry: **3–6 months**. Exact contract ranking, month-to-day conventions, expiry/strike tie-breaks and standard-contract rules must be those of the official starter, without replacement or outcome-dependent fallback.
- Sold-put OTM distance: **5%**. Exact strike rounding follows the starter, unchanged.
- Holding horizons: **1, 2, 3, 5, 10, 21, 42, 63 sessions, plus expiry**. Report every horizon, including unavailable/unattractive results. Headline configuration cannot be changed after results.
- In-sample: **2024-01-01 through 2025-12-31**.
- OOS: **2026-01-01 through 2026-08-31**. Evaluate once only after all required implementation definitions and inputs are frozen; preserve a durable pre-evaluation claim. The requested 63-session and expiry endpoints may extend beyond data available at the submission deadline and must remain unmeasured/censored, never fabricated or replaced.
- Universe: exact official static **TOP_100**, no substitutes. Disclose survivorship and historical-identity limitations. No unofficial index constituent list is acceptable.
- Costs: **official starter cost model unchanged**. Its numerical parameters/formulas have not yet been obtained; execution is forbidden until they are verified and recorded with the starter code hash. Do not invent spread, commission or assignment assumptions.
- Baseline: exact official ordinary-day/placebo baseline for the **same names**, unchanged. Its date-selection, matching, overlap and seed rules require verification from the starter before execution. Do not choose placebo dates using returns.
- Sensitivity: report the complete **3 × 3** grid of expiry buckets **1m / 2m / 3–6m** and OTM distances **3% / 5% / 10%**, retaining every fixed horizon. No headline reselection.
- Market data: Massive only. Required routes are `/stocks/filings/8-K/vX/disclosures`, `/v3/reference/options/contracts?as_of=...`, and `/v2/aggs/ticker/O:.../range/1/day/...`; all equity inputs must also come from Massive. Main-study Databento/FMP checkpoints cannot substitute for bonus traded-option prices.

## Exclusions and trade realism

Preserve all exclusions in the fixed denominator. No backfilling missing/failed events, changing categories, picking favorable horizons, adjusting OTM distance or expiry, or retuning after observing results. Apply the official starter's verified rules for deduplication, event availability, option identity, missing aggregates, corporate actions, collateral/assignment, and split boundaries. If required rules, data, timestamps, costs or baseline cannot be verified, stop and report incomplete rather than manufacturing an equivalent result. Option aggregate closes are benchmark prices and do not establish executable bid/ask fills; disclose the starter's limitations explicitly. Cash collateral and assignment obligations must not be omitted from claimed cash-secured-put performance.

## Reproducibility and timeout

The runner must accept start/end dates for judges' sealed-window execution. Organizer starter or a faithful equivalent must be source-grounded and hash recorded before outcomes; notebook outputs must not be inspected or executed during configuration lookup. Shared existing acquisition caps remain in force. No new packages or GPUs are authorized. Small CPU Slurm jobs only; stop if required results cannot complete with time to commit/push before 11:00 EDT. Do not append a bonus PDF or claim eligibility for incomplete analysis.

## Before-results declaration

**This bonus hypothesis, exact taxonomy tag, strategy, headline settings, horizon list, date splits and sensitivity grid were specified before any bonus results were inspected.** To date only the semantic taxonomy endpoint has been queried. No bonus disclosures, options returns, placebo returns or OOS outcomes have been queried or evaluated. The official starter's unresolved details are a hard execution gate, not permission to improvise methodology.

## Starter verification before bonus disclosures or outcomes

The user supplied the official starter at `starter/gqh-massive-8k-starter/gator-quant-hacks-8k-options-challenge.ipynb`. Only source cells were inspected; notebook outputs were not inspected. A source-only copy accompanies this module; both original and source-copy SHA256 hashes are recorded in config.json. Original organizer functions will be loaded directly, not recreated.

The exact static TOP_100 is the source list, as of September 2026, with the original survivorship caveat. Expiry buckets (calendar days from pre-event session; min/max/target) are 1m=(21,45,30), 2m=(46,80,60), 3–6m=(90,180,120). `pick_expiry`, `select_strikes`, `locate_spot`, `Leg.mark`, `evaluate`, `scoreboard`, `difference_board`, and `sample_placebo` remain the organizer implementations. Flat parity carry=4%, strike window=25%, maximum mark age=3 sessions. The cash-secured-put output is short-put mark-to-market P&L divided by synthetic entry stock spot; it is not collateral-based portfolio performance and does not model early assignment as an executed brokerage ledger.

Cost model: `COST_HAIRCUT=0.05`; round-trip cost = absolute entry put premium / synthetic entry spot × 0.05 × 2. Preserve this exact formula; any all-horizon cost reporting is the same formula, not a tuned cost model. Ordinary-day sampling uses official sample_placebo: seed=7, same event names, >30 calendar days from that name's sampled events, unchanged sampling code.

Outcome-blind deadline cap: **first one chronological event in each split**, using the official `max_events=1` parameter, no replacements. **N_PLACEBO=1**, using the official configurable sampler argument; `RUN_PLACEBO=True` for the submitted pilot. This is an explicitly small pilot, not a full-window or powered test; bootstrap intervals remain N/A below five observations. A reduced baseline size must not be described as the starter's default 120-placebo run. All nine horizons and the full 3×3 sensitivity grid remain exported, with unavailable outcomes marked N/A.

Timing realism: the starter exposes an optional EDGAR acceptance-time lookup separately from run_study; its run_study does not perform that correction. The wrapper must obtain acceptance metadata before pricing and use the starter's existing after-16:00 next-session correction before any result evaluation. If metadata fails, retain the exclusion; do not infer that a date-only filing preceded the close. Metadata is not market data. OOS is durably claimed before any OOS disclosure query and is not reopened after partial failure.

This verification and pilot cap were recorded before any bonus disclosure records, market-price outcomes, OOS returns, or placebo returns were fetched. If historical plan entitlement or budget prevents the exact pilot, stop and report incomplete; no alternate dates or instruments may be substituted.
