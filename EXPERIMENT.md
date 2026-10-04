# Preregistration: Options-Conditioned Post-Earnings Drift

Registration date: October 3, 2026
Status: Approved methodological specification; split remains conditional on verified coverage/calendar constraints; pre-return feasibility gate not yet performed.
Primary hypothesis: Hypothesis 2 in `RESEARCH_IDEAS.md`

## 1. Research decision and hypothesis

The user selected this hypothesis before examining strategy returns, based on prospective economic rationale, data feasibility, and statistical testability.

**Primary hypothesis:** Earnings reactions exceeding the pre-announcement ATM straddle-premium move proxy predict stronger direction-aligned stock-price continuation over the following ten trading sessions, beyond the information in the initial stock reaction and trailing realized volatility.

A straddle premium reflects expected variability, volatility risk premia, liquidity, and remaining time to expiration. It is an observable normalization proxy, not a calibrated forecast of absolute earnings-day movement.

No backtest, substantial market-data acquisition, package installation, or significant compute is authorized by this specification.

## 2. Primary versus exploratory analysis

The primary analysis consists of:

- The fixed universe, event eligibility, option selection, signal, timing, and stock/SPY implementation below.
- One prespecified statistical test of incremental conditional predictability.
- One prespecified net executable performance metric.
- The approved primary transaction-cost model.

Secondary benchmarks and descriptive risk measures are identified separately.

Any change to **`X > 1`**, the **ten-session holding period**, **10:10–10:20 ET entry window**, or **option-selection rule** after results are inspected must be explicitly labeled exploratory. It cannot replace the primary specification.

Hypotheses 1 and 3, additional features, alternative thresholds, maturities, entry times, horizons, hedges, or fitted nonlinear models are exploratory unless separately preregistered against a fresh holdout.

## 3. Universe definition

Use historically listed U.S. exchange-listed common stocks, including securities that subsequently delist.

Exclude ETFs, mutual and closed-end funds, preferred shares, warrants, units, OTC securities, and ADRs.

At the decision time, require:

- Previous regular-session unadjusted closing price of at least **$10**.
- Median daily dollar volume over the preceding **20 completed regular sessions** of at least **$20 million**.
- All 20 volume observations available.
- Required historical stock/SPY prices, option reference records, and valid option quotes.

Calculate daily dollar volume from regular-session price-times-volume observations. Use the same documented calculation throughout the experiment.

Do not impose a fixed universe of 200 stocks. That figure in the research proposal was a sample-planning illustration.

Use historical security identifiers and ticker mappings. Allow at most one position per issuer. Where multiple common share classes qualify, choose the class with the highest trailing 20-session median dollar volume; break ties using a stable security identifier.

Universe membership must not depend on subsequent survival, returns, option availability, or future liquidity.

## 4. Earnings-event eligibility

Include verified original quarterly earnings releases occurring outside regular trading hours.

Exclude:

- Projected or unconfirmed calendar events.
- Earnings calls without an identifiable earnings release.
- Amendments or corrections treated as new earnings events.
- Releases during regular trading hours.
- Releases with uncertain timing.
- Releases exactly at the regular-session opening or closing boundary.

Deduplicate by issuer and fiscal period. Use the original public release, not a later filing or revised vendor record.

Let **D** be the first regular session opening after the verified release.

Known later events do not retrospectively remove an eligible observation. Once a trade is entered, later earnings updates, news, halts, or adverse outcomes remain part of its outcome.

EPS and revenue surprises are not primary signal inputs.

## 5. Event timestamp rules

FMP earnings records identify candidate events, replacing Massive/Benzinga as the candidate earnings-event source. Treat FMP `time` values `bmo` (before market open) and `amc` (after market close) as the event-session classification, using the event date and exchange calendar to determine D. These categories are not exact publication timestamps. Missing, unknown, or other timing values are unusable for this classification; do not infer them from prices, returns, or `lastUpdated`.

Verify the original release and timing against contemporaneous release/news evidence or original filing evidence where appropriate. All original event-eligibility, boundary, disagreement, pre-event quote-window, and decision-time availability requirements remain in force. A usable FMP classification alone does not establish those requirements.

Preserve:

- Source and event identifier.
- Original publication timestamp.
- Original timezone.
- UTC and America/New_York conversion.
- Vendor ingestion timestamp when available.
- Record update timestamp and revision history when available, including FMP `lastUpdated` unchanged for provenance. `lastUpdated` is not evidence of historical record vintages, original publication time, or availability at the decision time.
- Evidence establishing when the event was publicly knowable.

Do not automatically equate SEC filing acceptance time with earnings release time.

Use exchange calendars, holidays, early closes, and daylight-saving rules.

Exclude an event if sources disagree in a way that changes the eligible trading session, or if the evidence cannot establish that the pre-event quote window preceded the public release.

Event confirmation must be available by **10:05 ET on D**. Retrospectively revised timestamps alone do not establish historical executability.

If historical vendor availability cannot be established, disclose that limitation. A reconstruction depending on retrospectively unavailable information belongs in a labeled diagnostic, not primary executable performance.

## 6. Pre-event option quote window

Use the last regular session closing before the earnings release.

The fixed pre-event window is:

**[15:50, 15:55) ET**

Exclude early-close sessions that lack this window. Do not substitute another window after examining outcomes.

Use completed historical Databento `OPRA.PILLAR` `cbbo-1m` observations. Verify schema timestamp semantics before implementation so that every selected observation was available before the release.

No current options snapshots, current Greeks, or current implied-volatility fields may reconstruct historical signals.

## 7. ATM contract-selection rule

At the pre-event window:

1. Identify standard, unadjusted options with a **100-share multiplier** that existed at that time.
2. Select the **earliest expiration date** between **D + 7 calendar days and D + 21 calendar days, inclusive**.
3. Within that expiry, select the strike nearest contemporaneous stock spot with both call and put contracts in the historical reference set.
4. Break equal-distance strike ties toward the **lower strike**.
5. Select using historical reference records before assessing quote quality.
6. If the selected pair fails quote-quality requirements, exclude the event. Do not substitute a farther strike or later expiry.

Define pre-event spot **S₀** as the median valid underlying NBBO midpoint in the pre-event window. Require valid observations in at least three distinct minute bins.

No strike interpolation is used for this hypothesis.

## 8. Option quote-quality requirements

For both selected contracts, require:

- Bid strictly greater than zero.
- Ask strictly greater than bid.
- Positive displayed size on both sides.
- Spread divided by midpoint no greater than **20%**.
- Valid timestamps and no identified invalid-feed condition.

Reject crossed or locked markets.

Require at least **three shared valid minute observations** for the call, put, and underlying within the pre-event window.

Do not forward-fill quotes across the earnings release, substitute trades for missing quotes, or treat missing premiums as zero.

Minute sampling does not prove continuous liquidity. Report that measurement limitation.

## 9. Implied-move proxy

At each shared valid pre-event minute, calculate:

`M_t = (call midpoint_t + put midpoint_t) / underlying midpoint_t`

Define:

`M = median(M_t)`

Require **M** to be finite and strictly positive.

This is the ATM straddle-premium move proxy. It contains remaining non-event time value and risk premia. Do not relabel it as a pure earnings variance estimate.

## 10. Stock reaction and beta

Use the completed post-event window:

**[10:00, 10:05) ET on D**

Require at least three shared valid minute observations for the stock and SPY.

Define:

- **S₁:** median stock NBBO midpoint in that window.
- **SPY₁:** median SPY NBBO midpoint in that window.
- **SPY₀:** median SPY NBBO midpoint in the pre-event window.

Calculate the raw stock price reaction:

`r = S₁ / S₀ − 1`

Make stock prices comparable across any intervening split using the action effective at that time. Do not compare incompatible share bases.

Estimate beta using OLS with an intercept on paired daily stock and SPY total returns over the preceding **120 regular sessions**, ending before D.

Require at least **100 valid paired observations**.

Clip estimated beta to:

`[0, 2]`

Calculate the residual reaction:

`a = stock total-return reaction − beta × SPY total-return reaction`

Account consistently for dividends and splits in total-return calculations. The price reaction **r**, rather than dividend-inclusive total return, remains the numerator used in X.

## 11. Signal definition

Define:

`X = |r| / M`

Require:

- Finite r, a, and X.
- Nonzero r and a.
- Matching signs for r and a.

The primary trade signal is:

`X > 1`

Equality does not qualify.

Trade direction is:

`d = sign(a)`

Positive direction means long stock. Negative direction means short stock.

No analyst-surprise field, later price, subsequent event, or post-entry option information enters the signal.

## 12. Entry and exit timing

Complete signal construction at **10:05 ET on D**.

Enter only during:

**[10:10, 10:20) ET on D**

Exit during:

**[10:10, 10:20) ET on the tenth regular trading session after D**

D is session zero.

The holding period is exactly **ten trading sessions**. No performance-based stop-loss, take-profit, or discretionary exit is included.

The execution simulator must distinguish observable prices from attainable fills. Execution-window VWAP is a benchmark, not a guaranteed fill.

If a scheduled exit is prevented by a halt or insufficient liquidity, retain and report the unresolved exposure. Do not delete the original trade or pretend that it exited on schedule.

## 13. Research adjustment and trading implementations

### Primary predictive analysis

Use mathematical beta adjustment without assuming a physical SPY position.

For each otherwise-valid, sign-consistent earnings event:

`d = sign(a)`

`Y_research = d × (R_stock_10d − beta × R_SPY_10d)`

Where:

- Beta is estimated using the frozen pre-event procedure.
- Stock and SPY total returns span the prescribed entry and exit windows, ten regular trading sessions apart.
- Reference prices are median valid NBBO midpoints during **[10:10, 10:20) ET**, with valid observations in at least three distinct minute bins.
- Total returns account for intervening dividends, splits, and other corporate actions.

**Do not subtract commissions, spread, slippage, fees, borrow, financing, or physical hedge costs from `Y_research`.** These are research reference returns, not attainable execution prices.

Include otherwise-valid observations from both `X > 1` and `X ≤ 1`.

Borrow availability, portfolio allocation, existing positions, and execution capacity must not determine inclusion in predictive inference.

### Primary executable implementation: directional stock trade

Trade the stock in direction d when **`X > 1`**.

- Initial stock notional: **1% of initial reference equity** per issuer position.
- Maximum one open position per issuer.
- Aggregate stock gross exposure cap: **50% of initial reference equity**.
- Scale simultaneous new entries proportionally to remaining allocation capacity using information available before execution.
- Hold share quantities fixed, subject to corporate-action adjustments.
- No discretionary stops, take-profits, or performance-dependent exits.
- Scheduled exits precede new entries on the same day.

Subsequent price changes may cause exposure to drift above the allocation cap. Report that drift; do not introduce an unregistered rebalancing rule.

Executable short entries require contemporaneous historical borrow availability and rates. Missing borrow excludes the trade from executable performance, **not predictive inference**.

### Secondary implementation: physical stock/SPY hedge

Implement the same stock signals with an offsetting SPY position:

`stock notional = d × allocated stock notional`

`SPY notional = −d × beta × allocated stock notional`

Freeze beta and share quantities at entry, subject to corporate actions.

Apply execution costs, capacity limits, and borrow requirements separately to both legs. A short SPY hedge requires SPY borrow evidence.

Report this portfolio separately, including coverage differences. It cannot replace the primary directional strategy even if its results are more favorable.

## 14. Transaction-cost model

Apply costs to simulated executions of the primary directional strategy and secondary physical-hedge portfolio. Costs do not enter the primary predictive outcome.

### Spread and adverse slippage

Each entry and exit pays:

`half contemporaneous median NBBO spread + 2 bps adverse slippage`

Calculate the median spread from valid quotes during the applicable execution window. Apply costs adversely to buys and sells.

Do not double-count spread crossing when execution prices already incorporate it. Document the reference-price and execution-price construction.

### Primary commission assumption

**$0.001 per executed share, with no minimum.**

This is an explicit modeling assumption, **not a verified broker quote** or a claim about Webull pricing.

### Conservative commission sensitivity

**$0.005 per executed share, with a $1 minimum per order.**

Apply the minimum consistently to stock entries and exits and to separate SPY orders in the secondary implementation.

This is a prespecified sensitivity case, not an alternative primary schedule.

### Regulatory and exchange fees

Include applicable historical regulatory and exchange fees separately, consistent with the documented execution-route assumption and effective dates.

Avoid double counting. If a material fee component is unresolved, disclose it and do not describe incomplete accounting as net of all applicable costs.

### Borrow and short dividends

For executable shorts:

- Require documented contemporaneous borrow availability.
- Use applicable historical borrow rates.
- Accrue borrow over actual calendar days held using ACT/365 and the applicable short market value.
- Include dividends owed on short positions separately.

If required borrow evidence is unavailable, exclude the trade from executable performance and retain its otherwise-valid observation in predictive inference.

A **3% annual fallback borrow rate** may be used only in a labeled diagnostic. It does not establish that the security was locatable or executable.

Do not assume interest income on short proceeds. Any financing required by an implementation must be explicitly documented rather than silently omitted.

## 15. Capital normalization and execution capacity

Report capital-normalized results.

Use **$1,000,000 reference capital only for capacity and accounting**, including:

- Translating allocation fractions into shares.
- Whole-share rounding.
- Commission minimums in the conservative sensitivity.
- Partial fills.
- Portfolio accounting and exposure limits.

This is not required starting capital and does not establish scalability.

Maximum participation:

**1% of observed execution-window volume per traded security.**

The limit applies to entry and exit executions. All orders in the same security and window share the participation budget; order splitting cannot circumvent it.

Order intentions must use information available before execution. Observed execution-window volume constrains simulated fills but cannot alter the signal.

Record full fills, partial fills, and unfilled orders. For the secondary portfolio, fill only jointly supported stock/hedge quantities, preserving the intended hedge ratio subject to rounding.

Missing entry execution prices or spreads prevent primary executable entry. They do not automatically invalidate an otherwise measurable predictive observation.

An exit liquidity failure cannot retrospectively erase an entry. Retain unresolved exposure and report incomplete outcomes.

Show capacity separately from normalized returns. Do not extrapolate capacity from daily volume alone.

## 16. Chronological split and boundary purging

Use the agreed entry-session windows:

| Split | Entry-session dates |
|---|---|
| Train | April 3, 2023–December 31, 2024 |
| Validation | January 1–December 31, 2025 |
| Final holdout | January 1–September 18, 2026 |

Market holidays have no entries.

Purge observations whose prescribed **ten-session holding periods cross split boundaries**. Apply the same scheduled boundary treatment to predictive observations and executable trades.

The last proposed holdout entry, September 18, 2026, has its scheduled tenth-session exit on October 2, 2026, subject to exchange-calendar verification.

Dates may change **only because of verified historical data coverage or calendar constraints, never because of returns**. Record supporting evidence and the amendment before outcome analysis.

Required pre-entry history may precede a split’s start because it was available at the decision time. No later-split information may enter earlier decisions or estimates.

Train supports implementation verification and explicitly secondary model estimation. Validation assesses the unchanged primary specification. Performance-driven revisions remain exploratory.

## 17. Final holdout protection

Keep the final holdout untouched until the specification, feasibility status, and implementation are frozen.

Before that point, do not inspect holdout:

- Event counts or eligibility.
- Universe screens.
- Contract availability or quote-quality distributions.
- X values or signal counts.
- Subsequent returns.
- Trades, regression outcomes, or performance.

Provider entitlement and broad coverage metadata may be checked without querying holdout observations.

The feasibility gate applies to **train and validation only**. It does not authorize holdout counts or a holdout pilot.

Before opening the holdout, record:

- Approved specification and amendments.
- Fixed split dates.
- Implementation commit/hash.
- Data-processing and timestamp rules.
- Costs and execution assumptions.
- Feasibility findings and unresolved limitations.

Evaluate the holdout once. Insufficient holdout observations yield an inconclusive result, not permission to extend dates or change the signal.

If a material defect requires correction after inspection, disclose that the holdout is no longer pristine. Do not present a corrected rerun as an untouched first evaluation.

## 18. Primary predictive statistical test

Use one prespecified final-holdout event-level OLS regression.

Include otherwise-valid, sign-consistent events from both `X > 1` and `X ≤ 1`, regardless of:

- Borrow availability.
- Executed-trade status.
- Portfolio allocation.
- Existing positions.
- Execution capacity.
- Physical hedge availability.

Require measurable research reference returns. Log missing or unresolved outcomes; do not silently delete adverse halts, bankruptcies, or delistings.

Estimate:

`Y_research = α + γ I(X > 1) + δ|r| + θRV20 + ε`

Where:

`Y_research = d × (R_stock_10d − beta × R_SPY_10d)`

- `|r|` controls for initial reaction magnitude.
- `RV20` is the sample standard deviation of the preceding 20 completed daily stock total returns.
- All 20 volatility observations are required.

No transaction or borrow costs enter this outcome.

Use linear controls without interactions, winsorization, outcome-based trimming, or threshold searches.

Use **two-way cluster-robust inference by issuer and entry date**.

Report γ, its two-sided 95% confidence interval, two-sided p-value, sample size, threshold-group counts, and cluster counts.

The preregistered evidence criterion is:

**γ > 0 with two-sided p < 0.05.**

Do not change tests to chase significance.

If either threshold group is absent, the regression is rank-deficient, or inference is unsupported, report the primary test as inconclusive. Flag fewer than 30 clusters in either dimension as unreliable asymptotic inference.

Predictive evidence and executable profitability are separate findings.

## 19. Primary executable performance metric

For the **directional stock strategy**, the primary executable metric is:

**Equal-weight mean net ten-session stock-trade P&L per initial executed stock dollar across executed `X > 1` trades.**

Include all applicable:

- Dividends received or owed.
- Primary commissions.
- Spread and adverse slippage.
- Historical regulatory and exchange fees.
- Historical borrow charges for executable shorts.

Do not mathematically subtract SPY returns from executable P&L. The primary executable strategy holds no SPY position.

Report trade count, uncertainty, long/short contributions, and executable coverage alongside predictive coverage.

Coverage logs must distinguish exclusions from borrow, existing positions, allocation limits, participation limits, and missing execution data.

Unresolved entered trades make executable performance incomplete. Do not report only conveniently completed trades.

The physical stock/SPY portfolio, conservative commission schedule, and 3% fallback-borrow diagnostic are separately labeled results.

Portfolio daily returns, drawdown, turnover, exposures, concentration, and capacity are supplementary descriptive measures. They cannot replace the primary metric because they look better.

## 20. Pre-return data-feasibility gate

### Purpose and authorization

Before examining subsequent strategy returns, complete a coverage/count audit and document every feasibility item as **passed, failed, or unresolved**.

This specification does not authorize API calls, package installation, substantial downloads, a backtest, or significant compute. A later approved audit must remain limited to metadata and a bounded historical pilot.

Use train and validation only. Keep the holdout untouched.

The audit may inspect the initial earnings reaction and calculate X because these are pre-entry signal inputs. It must not inspect subsequent holding-period returns, strategy P&L, regression outcomes, or performance rankings.

### Required feasibility checks

| Item | Required evidence |
|---|---|
| Earnings timestamps | Access, historical coverage, publication-time semantics, revision handling, and verification against contemporaneous evidence. |
| Historical references | Then-listed securities, historical ticker/security mappings, expired contracts, and corporate-action records; no dependence on present-day membership. |
| Stock and SPY NBBO access | Entitlement, historical coverage, timestamp semantics, usable pre-event/reaction windows, and access to the prescribed later reference/execution windows. Verify later-window access through metadata or unrelated non-event samples without calculating strategy outcomes. |
| Historical options | Availability of the prescribed expiries and ATM call/put pairs at historical observation times. |
| Databento OPRA coverage | Actual account entitlement, `definition` and `cbbo-1m` availability, schema-specific history, and timestamp semantics from the required start date. |
| Quote quality | Valid two-sided quotes, displayed sizes, spread filters, and synchronized call/put/underlying observations. |
| Tiny-pilot costs | Estimated charges, bytes, request volume, storage, and compute for a bounded pilot, followed by recorded actual usage if approved. No full OPRA-chain download. |

A pilot must have a documented scope and user-approved spending limit before acquisition. Estimate larger-audit costs before expanding it.

### Coverage and count audit

Report separately for train and validation:

1. Candidate original quarterly earnings events in the historical universe.
2. Percentage with verified release timestamps.
3. Count with verified outside-hours eligibility.
4. Percentage of timestamp-eligible events with the prescribed historical option contracts.
5. Percentage of contract-covered events with valid synchronized option quotes.
6. Count with complete pre-decision inputs and nonzero, sign-consistent r and a.
7. Counts of `X > 1` and `X ≤ 1`.
8. Unique issuers and entry dates.
9. Attrition at each stage.

Keep timestamp verification separate from outside-hours eligibility so legitimate regular-hours releases are not mislabeled as missing data.

Borrow availability is reported separately for executable coverage. It is not a predictive feasibility requirement.

### Prospective minimum requirements

These minimums are practical safeguards selected before outcome inspection. They are **not power calculations or guarantees of significance**.

Require in each development split:

- Verified timestamps for at least **90%** of candidate events.
- Prescribed historical contract pairs for at least **80%** of timestamp-eligible events.
- Valid synchronized quotes for at least **75%** of contract-covered events.

After calendar-based boundary purging, require:

| Signal-measurable sample requirement | Train | Validation |
|---|---:|---:|
| Total sign-consistent events | ≥600 | ≥200 |
| `X > 1` events | ≥100 | ≥40 |
| `X ≤ 1` events | ≥100 | ≥40 |
| Unique issuers | ≥50 | ≥30 |
| Unique entry dates | ≥60 | ≥30 |

These counts require only pre-decision inputs and scheduled exit dates, not subsequent returns.

Do not alter minimums using observed returns, significance, Sharpe ratios, or profitability.

### Gate decision

Before any outcome analysis:

- Record each feasibility item’s status and supporting evidence.
- Confirm whether the count and coverage requirements pass.
- Resolve correctable acquisition defects without examining outcomes.
- Record all unresolved limitations explicitly.

An unresolved status is **not an automatic pass**. Unresolved timestamps, historical references, required NBBO/options coverage, or quote semantics block confirmatory analysis if they prevent defensible measurement. Unresolved costs block claims of fully costed executable performance.

Any limited analysis despite unresolved items requires a documented, prospective decision identifying what conclusions remain supportable. It cannot silently become the full preregistered result.

If genuine data deficiencies fail the approved requirements, declare the experiment infeasible under this specification. Another hypothesis may be chosen solely on data availability and prospective rationale, before examining strategy returns.

Do not loosen the signal, coverage minimums, or sample requirements merely to force a pass. Record any coverage/calendar-driven date amendment. The holdout remains untouched throughout.

## 21. Secondary benchmarks and descriptive measures

Prespecified secondary benchmarks:

1. Earnings-reaction continuation without the `X > 1` filter.
2. Initial reaction normalized by trailing realized volatility.

Use the same eligible inputs, sign-consistency rule, timing, ten-session horizon, and corresponding implementation costs. Predictive comparisons use cost-free research outcomes; executable comparisons use the applicable cost and borrow rules.

For the realized-volatility benchmark, report the normalized reaction as a continuous predictor; do not search for a favorable trading threshold. Any fitted secondary model uses train only.

Report separately:

- Conservative commission sensitivity.
- Portfolio daily returns.
- Annualized return and volatility.
- Sharpe ratio.
- Maximum drawdown.
- Turnover.
- Long and short contributions.
- Gross/net and market exposures.
- Issuer concentration.
- Fill rates and capacity.
- Break-even additional transaction costs.

These measures cannot replace the primary metric or statistical test because they look better.

## 22. Exclusion rules

Log exclusions at separate stages.

### Event eligibility

- Invalid security classification.
- Insufficient trailing history.
- Uncertain or ineligible release timing.
- Duplicate issuer/fiscal-period event.
- Missing evidence of historical event availability.

### Signal eligibility

- Missing selected expiry or ATM pair.
- Invalid or insufficient synchronized option quotes.
- Missing pre-decision stock/SPY prices.
- Missing beta or trailing volatility.
- Nonfinite values.
- Zero or sign-disagreeing r and a.

Events with `X ≤ 1` are predictive controls, not signal-data exclusions.

### Research-outcome measurement

Log missing prescribed research reference prices or unresolved corporate-action/terminal outcomes separately. Do not condition research inclusion on borrow, execution capacity, an existing issuer position, allocation limits, or physical hedge availability. Do not silently delete unresolved outcomes or claim that incomplete measurement is complete.

### Execution eligibility

- Existing issuer position.
- Portfolio capacity unavailable.
- Missing executable entry prices/spreads.
- Inadequate execution-window capacity.
- Missing required short borrow evidence.
- Unexecutable physical hedge, for the secondary implementation only.

Report exclusions and unfilled signals, including partial fills.

Do not exclude an entered trade because of later poor returns, news, halts, bankruptcy, or delisting.

## 23. Missing-data treatment

Missing observations are not zero.

Do not:

- Impute option premiums.
- Forward-fill across earnings announcements.
- Replace the prescribed expiry or strike.
- Infer borrow availability from a broker’s current list.
- Substitute favorable exit prices.
- Treat missing delisting returns as zero.

Preserve provider missingness and acquisition failures separately.

Report coverage and attrition by split, year, issuer, and liquidity after the relevant split is authorized for inspection.

If missingness prevents defensible primary analysis, report the experiment as infeasible or incomplete rather than silently changing its methodology.

## 24. Leakage controls

Maintain immutable raw records and a manifest containing provider, query parameters, acquisition time, version, and transformation history.

Every signal input must be demonstrably available before the decision time.

Prohibit:

- Current options snapshots as historical inputs.
- Revised analyst estimates as primary features.
- Future earnings calendars.
- Future liquidity screens.
- Present-day option-chain membership.
- Future corporate actions in historical price eligibility.
- Post-entry information in event selection.

Use consistent UTC/Eastern conversions and documented schema timestamp semantics.

Separate event publication, vendor ingestion, decision, order, and fill times.

Purge overlapping outcomes at chronological split boundaries.

Log every exploratory variant and which splits had already been inspected.

## 25. Survivorship and corporate-action controls

Construct the universe using securities listed at each historical decision date.

Retain:

- Subsequently delisted stocks.
- Historical ticker changes.
- Mergers and reorganizations.
- Securities whose options later disappear.

Do not require survival to the study endpoint.

Account for effective splits, dividends, merger consideration, and verified terminal proceeds. Include dividends owed on executable shorts.

An entered position lacking verifiable terminal proceeds or exit data remains unresolved. Report it explicitly and mark executable performance incomplete. Apply the same transparent unresolved-outcome accounting to research observations lacking verifiable total returns; missing borrow alone does not make a research outcome unresolved.

Any adverse-bound or alternative-terminal-value calculation is a labeled diagnostic.

## 26. Exploratory analysis policy

Exploratory analyses may include:

- Alternative X thresholds.
- Different expiries, strikes, or quote windows.
- Different holding periods or entry times.
- EPS/revenue surprises.
- Historical IV or additional options features.
- Industry and size subdivisions.
- Alternative hedges beyond the prespecified secondary SPY implementation.
- Nonlinear models.
- Fallback borrow assumptions.
- Hypotheses 1 and 3.

Before running an exploratory variant, record:

- Its definition.
- Economic motivation.
- Date.
- Previously inspected data splits.
- Relationship to the primary specification.

Disclose all tested variants. Do not reuse the final holdout to promote an exploratory change into a new confirmatory result.

The current primary statistical family contains one test. If additional hypotheses become confirmatory, preregister the testing family and multiplicity correction against a fresh holdout.

## 27. Approval gates and amendments

The user approved the methodology, cost assumptions, reference-capital convention, feasibility requirements, and integration of this document before writing. Actual data feasibility and schema-specific coverage remain unverified.

Remaining gates:

1. Separate authorization for any provider access, bounded pilot, spending, installation, substantial download, or significant compute as required.
2. Pre-return feasibility audit and resolution/documentation of its findings.
3. Actual Databento entitlement and schema-specific coverage verification.
4. Calendar confirmation and subsequent freezing of the coverage-conditional split.
5. Implementation freeze before final holdout access.

Approval of this document does not authorize a backtest or substantial download.

Ask before installing packages, downloading substantial market data, running significant compute, or launching large/long-running Slurm jobs. GPU use requires explicit approval.

Record amendments with:

- Previous and replacement text.
- Reason.
- Date.
- User approval where required.
- Whether strategy returns had been inspected.
- Primary, secondary, or exploratory classification.

Freeze the completed specification before examining strategy returns.


### Amendment A1 — candidate earnings source and session classification

Date: October 3, 2026.
Authorization: User explicitly requested this prospective amendment.
Classification: Primary data-source amendment; no strategy-rule change.

Previous text in Section 5: “Massive’s earnings records identify candidate events. Verify actual release timing using contemporaneous release/news evidence or original filing evidence where appropriate.”

Replacement: FMP identifies candidate earnings events; FMP `time` (`bmo`/`amc`) supplies event-session classification as specified in Section 5. Preserve `lastUpdated` for provenance without treating it as historical vintage evidence. Contemporaneous verification and historical availability requirements remain mandatory.

Reason: Recorded Stage A Massive/Benzinga earnings probes were entitlement-limited (HTTP 403). FMP is the user-selected replacement candidate source. FMP access evidence and representative timing coverage are recorded separately in `results/FMP_FEASIBILITY.md`; no coverage pass is inferred from source selection.

This amendment occurred before any strategy returns were inspected. No holdout observations or strategy returns were accessed in preparing it. Every other hypothesis, signal, option-selection rule, split date, boundary purge, holdout protection, feasibility threshold, statistical test, and outcome rule is preserved.

The prepared `FMP_COVERAGE_AUDIT.md` is a train+validation-only timing-coverage protocol, not execution authorization. The existing ≥90% requirement remains unchanged in each development split. Its usable-`bmo`/`amc` fraction is a necessary timing-coverage check, not a substitute for the existing verified-timestamp and historical-availability requirements. The full feasibility gate remains pending.
