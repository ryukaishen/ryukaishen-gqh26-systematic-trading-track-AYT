# Research hypotheses: Gator Quant Hacks 2026

## Decision context

These are three prospective hypotheses, not demonstrated edges. Signals and holding periods below are proposed economic specifications, chosen without examining returns.

**Provisional recommendation:** Hypothesis 2 offers the best balance of rationale, sample size, and implementation effort. Hypothesis 1 offers the strongest Massive-specific story but has greater timestamp and event-coverage risk. Hypothesis 3 offers the most distinctive research angle but requires careful handling of correlated observations.

API access does not establish entitlement to every dataset or historical field. The hackathon deadline, data budget, and subtrack rubric remain unconfirmed; feasibility assessments assume a short hackathon and existing equity/options entitlements. Webull is optional for later paper execution and is not required for any hypothesis.

### Verified provider capabilities and limitations

- Massive offers parsed 8-K text, a SEC filings index, and categorized 8-K disclosures. Its disclosure product documents history starting January 2022, daily updates, and AI-assigned categories with supporting text. These are useful research labels, but not proof that those labels were available at historical filing time. [SEC endpoint announcement](https://massive.com/changelog), [disclosure coverage and limitations](https://www.massive.com/blog/tagging-8-k-disclosures-with-ai-corporate-events-labelled-by-what-actually-happened).
- Massive’s Benzinga earnings endpoint provides dates/times, actual and estimated EPS/revenue, surprise fields, methodology, and update timestamps. Historical records must be checked for revisions; the endpoint alone does not establish point-in-time consensus vintages. [Earnings documentation](https://www.massive.com/docs/rest/partners/benzinga/earnings).
- Databento offers OPRA historical data, including consolidated quote schemas and instrument definitions. We would request selected contracts and windows, using `metadata.get_cost` before acquisition. Schema-specific coverage must be checked rather than assuming every schema has identical history. [Historical API](https://databento.com/docs/api-reference-historical?historical=http), [quote schemas](https://databento.com/docs/schemas-and-data-formats/cbbo), [OPRA normalization changes](https://databento.com/blog/opra-migration).
- Massive offers options contract reference data and historical options quotes, subject to entitlement. Historical signals must come from historical quotes, not current snapshot Greeks or IV. [Options reference overview](https://massive.com/blog/introducing-stock-options-apis), [historical options coverage](https://www.massive.com/business-options).

### Shared proposed research conventions

- Use historically listed U.S. common stocks, including subsequently delisted names.
- At each decision, require previous-close price ≥ $10 and trailing 20-session median dollar volume ≥ $20 million. Never screen using future liquidity.
- Deduplicate events and allow at most one open position per issuer.
- Trade **stocks using options information**. This isolates predictive value and avoids making option execution the main project.
- Use SPY as the hedge. Estimate beta from the preceding 120 sessions, requiring at least 100 observations; clip beta to [0, 2].
- Give each position 1% initial equity notional, cap stock gross exposure at 50%, and scale simultaneous eligible positions proportionally. Include hedge exposure in risk reporting.
- Execute after signal completion, with observed equity spreads, fees, slippage, and participation limits. VWAP is a benchmark, not a guaranteed fill.
- Short recommendations are conditional on contemporaneous borrow availability. Without historical borrow evidence, short-side results are research diagnostics rather than fully executable performance.
- Use only standard, unadjusted 100-share options with valid two-sided quotes. Reject crossed/locked quotes, zero bids, zero displayed sizes, and spreads above 20% of midpoint.
- Use completed five-minute windows of Databento `cbbo-1m` observations. Require at least three valid observations per selected contract. Sparse quotes remain a measurement limitation.
- For long-dated option comparisons, choose an expiry 30–60 calendar days away, nearest 45 days. Use the same expiry before and after an event. Interpolate premiums at prescribed spot-relative strikes using bracketing strikes no more than five percentage points apart; do not extrapolate.
- These premium statistics are **observable proxies**, not pure implied-volatility or risk-neutral probability measures. Moneyness, dividends, time decay, and early exercise can affect them.

Sample counts below assume an illustrative **200 eligible issuers over three years**. They are budgeting estimates, not observed coverage or statistical power calculations.

## 1. Non-earnings 8-K risk repricing predicts continued equity deterioration

**Hypothesis:** Following a non-earnings 8-K, rising downside option premiums accompanied by a negative equity reaction identify adverse information whose stock-price adjustment continues over the next five sessions.

### Economic rationale and why an edge might exist

Unscheduled disclosures can require investors to interpret unfamiliar legal or operational information. Options may reflect informed hedging demand or heightened downside concern before slower equity investors finish adjusting positions.

The mechanism is delayed interpretation, not faster access to SEC filings. Alternative explanations include temporary insurance demand, illiquidity, or an increase in required returns rather than future price deterioration.

### Exact data required

**Massive:**

- SEC filings index: issuer CIK, accession number, form, filing/acceptance timestamp where supplied, original filing link.
- Original 8-K text and item identifiers.
- Disclosure categories and supporting text for explanatory labels and an outcome-blind quality audit; not historical intraday triggers.
- Historical ticker/CIK mappings, listing status and delistings.
- Stock and SPY daily/minute OHLCV; equity quotes at execution windows.
- Splits and dividends.
- Earnings records solely to identify concurrent earnings announcements.

**Databento:**

- `OPRA.PILLAR`, `definition`: instrument ID, underlying mapping, strike, expiry, put/call, multiplier and adjusted-contract identification.
- `cbbo-1m`: bid/ask prices, displayed sizes, timestamps, and quality flags for selected wing contracts.
- Pre-filing and post-filing windows for those contracts.

**Does it genuinely need options?** Yes for the proposed conditioning mechanism. A stock-reaction-only strategy is the required baseline. If options add no incremental information, the options hypothesis is rejected.

### Exact signal definition

1. Select original, non-amended 8-Ks whose item list does **not** include Item 2.02. Do not select favorable event categories after seeing outcomes.
2. Let `F` be the verified SEC acceptance time. Let `E` be the second regular trading session strictly after `F`’s Eastern calendar date.
3. Require the filing text to have become available through the chosen pipeline before `E`. Without historical availability logs, this is a conservative research timing assumption, not verified live replicability.
4. Measure pre-event quotes during 15:50–15:55 on the last session closing before `F`; post-event quotes during 10:00–10:05 on `E`.
5. Define downside wing imbalance:

   `W = [P(0.95 × spot) − C(1.05 × spot)] / spot`

   using the common selected expiry.
6. Calculate `ΔW = W_post − W_pre`.
7. Calculate the stock return minus beta × SPY return from the pre-event window to the post-event window.
8. Signal a short only when `ΔW > 0` and this residual equity return is negative.
9. Exclude a concurrently occurring earnings announcement only if it was already known by the decision time. Later overlapping news remains in the sample.

**Trade:** Short stock and buy beta-weighted SPY during 10:10–10:20 on `E`. Exit during 10:10–10:20 five sessions later. No performance-based stop or alternative horizon.

**Primary test:** Does positive `ΔW` predict more negative subsequent residual returns among negative-reaction non-earnings 8-Ks, after controlling for the initial equity reaction?

### Assessment

| Dimension | Assessment |
|---|---|
| Expected sample size | Budget roughly 1,000–4,000 eligible filings before options filters and 200–800 signals. Must verify with event counts; repeated filings are not independent observations. |
| Holding period | Five trading sessions after entry. |
| Leakage risks | Event date mistaken for filing time; press release preceding filing; hindsight taxonomy labels; missing vendor ingestion timestamps; amendments; option windows overlapping the trigger. |
| Survivorship risks | Present-day ticker universe, missing distressed/delisted issuers, ticker changes, excluding companies whose options later disappear. |
| P-hacking risks | Trying many disclosure categories, sentiment dictionaries, repricing thresholds, delays, or horizons. Freeze the broad non-2.02 definition; category breakdowns are descriptive only. |
| Transaction costs | Moderate stock turnover, but adverse-news shorts may have expensive borrow and sharp gaps. Options spreads affect signal reliability even though options are not traded. |
| Liquidity/capacity | Limited by borrow, stressed equity liquidity and thin wing quotes. Use small participation limits; do not infer capacity from daily volume alone. |
| Novelty | Relatively strong combination of unscheduled disclosures and cross-market risk repricing; novelty is not established by a literature review. |
| Deadline feasibility | Medium-low. Timestamp verification and filing deduplication are the main burdens. Stop if historical availability cannot be defended. |
| Massive subtrack fit | Excellent: SEC disclosures, reference data, corporate actions and stock data are essential. Formal rubric fit remains unverified. |
| Judges’ story | Strong: “Which disclosures still matter after the first reaction?” Compelling if supported by source-linked examples and an honest latency model. |

## 2. Post-earnings drift is stronger when the realized reaction exceeds the options-implied move

**Hypothesis:** Earnings reactions that exceed the pre-announcement ATM straddle-implied move exhibit stronger continuation over the next ten sessions than otherwise similar earnings reactions.

### Economic rationale and why an edge might exist

A large move relative to what options priced may indicate news outside investors’ anticipated range. Slow portfolio adjustment, analyst revisions, and investor attention constraints could produce continuation.

The important comparison is not merely large versus small earnings moves. Options must contribute information beyond the initial return and historical volatility. A straddle premium also contains a volatility risk premium and liquidity effects; it is not a calibrated expected absolute move.

### Exact data required

**Massive:**

- Benzinga earnings: event identifier, issuer, report date/time, fiscal period, actual/estimated EPS and revenue, methodology and `last_updated`.
- Event timestamp verification from contemporaneous release/news or original filing where available.
- Historical listing universe and ticker mappings.
- Stock/SPY daily and minute OHLCV, execution-window equity quotes.
- Splits and dividends.
- Options contract reference data, including expired contracts, to cross-check contract selection.

**Databento:**

- OPRA `definition`.
- `cbbo-1m` for the pre-announcement ATM call and put at the selected expiry.
- No full-chain tick history, historical Greeks, or trade-direction inference is required.

**Does it genuinely need options?** Yes for the surprise normalization. Plain earnings-reaction continuation and historical-volatility normalization are required comparison models.

### Exact signal definition

1. Restrict to verified earnings releases outside regular trading hours. Uncertain timestamps are excluded before returns are inspected.
2. Let `D` be the first regular session after the release.
3. During 15:50–15:55 of the last session closing before the release, select the earliest standard expiry at least seven calendar days after `D` and no more than 21 days after `D`.
4. Select the strike nearest contemporaneous spot with both call and put quotes; break equal-distance ties toward the lower strike.
5. Define `M = (call midpoint + put midpoint) / spot`.
6. At 10:05 on `D`, calculate raw stock return `r` since the pre-event window and beta-adjusted residual return `a`.
7. Define `X = |r| / M`.
8. Signal only if `X > 1` and `r` and `a` have the same nonzero sign. Direction is `sign(a)`.

EPS surprise is not an input to the primary signal. This avoids requiring historical consensus vintages; revised surprise fields must not silently enter later.

**Trade:** Long or short stock in the signal direction, with an offsetting beta-weighted SPY hedge. Enter 10:10–10:20 on `D`; exit the same window ten sessions later.

**Primary test:** Does `X > 1` predict stronger direction-aligned residual returns after controlling for absolute initial reaction and trailing realized volatility?

### Assessment

| Dimension | Assessment |
|---|---|
| Expected sample size | 200 × 4 × 3 = 2,400 scheduled quarterly events before filters. Budget 1,200–2,000 valid option/event observations and 200–600 signals; these are assumptions, not counts. |
| Holding period | Ten trading sessions. |
| Leakage risks | Revised earnings calendars, incorrect release time, using post-release quotes in the pre-event straddle, current snapshot IV, selecting expiry retrospectively. |
| Survivorship risks | Current large-cap lists, missing delisted issuers, restricting to companies with options today rather than at the event. |
| P-hacking risks | Sweeping surprise thresholds, expiry rules, entry times and horizons. Freeze `X > 1` and ten sessions; control for the raw reaction to avoid repackaging momentum. |
| Transaction costs | Moderate; longer holding period reduces turnover pressure, but event spreads, gap execution and borrow remain material. |
| Liquidity/capacity | Best of the three for liquid optionable stocks. Signal availability depends on valid near-ATM quotes; actual stock capacity depends on entry-window volume. |
| Novelty | Moderate. Earnings drift is established; the contribution is the prospective options-based conditioning test and careful execution. |
| Deadline feasibility | Highest. Requires a compact calendar dataset and two contracts per event, rather than text interpretation or broad chains. |
| Massive subtrack fit | Strong: earnings, stock/reference data and corporate actions drive the study. Earnings entitlement is a gating issue. |
| Judges’ story | Clear: “Not all earnings surprises are equally surprising relative to what investors paid to hedge.” Strong if options beat a raw-reaction baseline out of sample. |

## 3. Options-confirmed earnings spillovers predict drift in non-reporting industry peers

**Hypothesis:** A large industry member’s earnings reaction conveys sector information that diffuses into non-reporting peers. Peer options repricing helps distinguish economically relevant spillovers from indiscriminate stock sympathy moves.

### Economic rationale and why an edge might exist

An issuer’s earnings can reveal shared demand, pricing power, or input-cost conditions. Investors may first update the reporting issuer and only later revise peers. Agreement between peer stock movements and peer option wings could indicate durable information transfer.

The alternative is common market exposure, mechanical sympathy trading, or hedge demand. Firm-specific earnings can also benefit competitors, so the hypothesis can fail for sound economic reasons.

### Exact data required

**Massive:**

- Verified earnings events and timestamps as in Hypothesis 2.
- Historical ticker details: industry/SIC, CIK and listing status. Historical classification availability must be checked.
- Daily/minute equity and SPY OHLCV, execution-window quotes.
- Splits and dividends.
- Earnings calendar information available at each decision to establish whether a peer has already reported that day.

**Databento:**

- OPRA `definition`.
- `cbbo-1m` for the reporting stock’s pre-event ATM straddle.
- Pre-event and post-event wing quotes for eligible peers using the shared 30–60-day expiry rule.

**Does it genuinely need options?** Yes for the confirmation mechanism. The required baseline trades industry spillovers using only the reporter reaction and peer stock reaction.

### Exact signal definition

1. At each calendar month’s start, group eligible stocks by two-digit SIC using classification available then.
2. In each group, designate the stock with the highest previous-20-session median dollar volume as the reporter candidate. Require at least four other eligible industry members.
3. Use that reporter’s outside-hours earnings events. Require `X > 1` under Hypothesis 2’s pre-event straddle definition.
4. Let `d` be the sign of the reporter’s beta-adjusted reaction measured by 10:05 on `D`.
5. A peer is eligible if it has not released its own earnings from the pre-event measurement window through 10:05 on `D`, using information then available.
6. Require the peer’s beta-adjusted equity reaction to have sign `d`.
7. Measure peer `ΔW` between the pre-event and 10:00–10:05 windows, using Hypothesis 1’s definition.
8. Require `d × ΔW < 0`: downside wings strengthen for negative signals and weaken for positive signals.
9. Trade every qualifying peer equally. Retain one issuer position at a time; future peer earnings do not cause retrospective exclusion.

**Trade:** Stock positions in direction `d` with beta-weighted SPY hedges. Enter 10:10–10:20 on `D`; exit five sessions later.

**Primary test:** Within eligible reporter events, do options-confirmed peers have stronger direction-aligned subsequent residual returns than stock-confirmed peers without options confirmation?

### Assessment

| Dimension | Assessment |
|---|---|
| Expected sample size | With 15–25 eligible groups, about 180–300 reporter events over three years before filters. Budget 40–120 qualifying reporter events and 100–500 peer trades. Effective sample size is closer to reporter-event count than peer-trade count. |
| Holding period | Five trading sessions. |
| Leakage risks | Current industry classifications, selecting leaders using future size, future peer earnings exclusions, post-entry option measurements, hindsight identification of “bellwethers.” |
| Survivorship risks | Current peer sets and industry leaders; missing delisted or reclassified peers. |
| P-hacking risks | Trying alternate peer networks, SIC granularities, reporter definitions, and confirmation rules. Freeze two-digit SIC and the liquidity-based monthly leader. |
| Transaction costs | Moderate; multiple correlated stock entries and hedges add costs. Wing quotes may be wide enough to overwhelm the confirmation measure. |
| Liquidity/capacity | Smaller peers constrain capacity. Industry concentration limits bind before aggregate market capacity; enforce issuer and industry exposure limits. |
| Novelty | Highest within this shortlist: tests cross-firm information diffusion with options confirmation. No claim of being unprecedented. |
| Deadline feasibility | Medium. Feasible after a clean earnings pipeline exists, but classification history and peer quote acquisition add work. |
| Massive subtrack fit | Strong: earnings, company reference data and stock prices are central. |
| Judges’ story | Distinctive: “One company reports; which peers have not finished incorporating the news?” Requires clear event-level evidence and controls for common shocks. |

## Scores

Scores are prospective judgments, not performance forecasts. Higher means stronger; data feasibility incorporates unresolved entitlement and timestamp risks.

| Hypothesis | Economic rationale | Novelty | Data feasibility | Statistical testability | Robustness potential | Hackathon feasibility |
|---|---:|---:|---:|---:|---:|---:|
| 1. Non-earnings 8-K repricing | 7 | 8 | 5 | 6 | 5 | 5 |
| 2. Options-conditioned earnings drift | 8 | 5 | 8 | 8 | 7 | 8 |
| 3. Options-confirmed peer spillovers | 7 | 8 | 6 | 6 | 6 | 6 |

Hypothesis 2 leads on feasibility and testability. Hypothesis 1 is the strongest showcase of Massive’s disclosure product. Hypothesis 3 has the greatest novelty but fewer independent events.

## Selection and validation rules before examining returns

1. Select one primary hypothesis using economic rationale, verified coverage, estimated acquisition cost, deadline and outcome-blind data quality—not strategy returns.
2. Freeze the universe rule, event definitions, option selection, timing, costs, holding period and primary statistical test in a dated specification.
3. Reserve chronological train/validation/holdout periods. Purge overlapping holding periods at boundaries. Keep the final holdout untouched until implementation and methodology are frozen.
4. Treat optional-data missingness as part of the result. Report exclusions and coverage by issuer, year, liquidity and event type.
5. Use issuer/date clustering for Hypotheses 1–2 and reporter-event/date clustering for Hypothesis 3. Report effect sizes and uncertainty; raw trade count is not independent sample size.
6. If all three are tested, disclose all three and correct the three primary tests for multiple comparisons. Any added variants are exploratory and count toward the research search.
7. Test incremental options value against the specified stock-only baselines. Report market/industry exposure, concentration, turnover, drawdown and break-even transaction costs.
8. Do not replace a failed hypothesis with a tuned version and reuse the same holdout.

**Next decision:** Provisionally select Hypothesis 2, subject to verifying earnings entitlement, timestamps and compact historical option coverage. Reject or defer a candidate for missing data rather than changing its methodology after seeing returns.

Package installation, substantial downloads, and significant compute require user approval. No GPU is required.
