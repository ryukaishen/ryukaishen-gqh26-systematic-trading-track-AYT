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

Operationalize the liquidity screen using Massive grouped daily aggregates with `adjusted=false` and unadjusted `close × volume`, as prospectively authorized in Amendment A3. Grouped-daily volume may include extended-hours trading; disclose this operational approximation to the originally stated regular-session dollar-volume measure. Use the preceding 20 completed exchange sessions with all observations available. The ≥$10 previous unadjusted close and ≥$20 million median dollar-volume thresholds remain unchanged.

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


### Amendment A2 — Stage B liquidity measurement source and acquisition ceiling

Recorded at: 2026-10-03T23:30:42.706110-04:00
Authorization: Explicit user instruction before acquisition and outcome inspection.
Classification: Prospective primary universe-measurement amendment and Stage B acquisition-plan amendment; not a threshold change.

Previous Section 3 text: “Calculate daily dollar volume from regular-session price-times-volume observations. Use the same documented calculation throughout the experiment.”
Replacement: FMP EOD Bulk unadjusted `close × volume` operationalizes daily dollar volume over the preceding 20 completed exchange sessions. Use the previous completed session's `close` for the price filter. Do not use `adjClose`. FMP does not explicitly guarantee regular-session-only volume; this is a prospective measurement-source limitation, not evidence that the original regular-session semantics were verified. It may affect universe membership and must accompany reported findings.

Preserve previous close ≥$10, trailing-20-session median dollar volume ≥$20M, all 20 observations required, and all other universe requirements. Early-close sessions count as completed sessions. No future prices, shortened histories, or present-day eligibility substitutions enter the screen.

Stage B acquisition transfer ceiling changes from 2,000,000,000 to 4,000,000,000 bytes; the 1,500-request ceiling is unchanged. Conservatively count completed Stage B1 and the three Massive pilot requests/bytes against these totals. Scope: development data and required pre-start 20-session lookback through 2025-12-31 only. Retain only symbol/date/close/volume from EOD Bulk. Massive remains the source for historical reference/corporate-action/stock quotes; Databento remains the options source.

This amendment occurred before any strategy returns were inspected. No holdout observations or post-entry returns/P&L were accessed. All other hypotheses, signals, split dates, purging, holdout protections, cost assumptions, feasibility thresholds and outcome rules remain unchanged. A liquidity-screen pass does not establish common-stock type, historical identity, quarterly-event provenance, timing coverage or full feasibility.


### Amendment A3 — Massive grouped-daily liquidity approximation

Recorded at: 2026-10-03T23:40:47.713258-04:00
Authorization: Explicit user instruction, before acquisition and outcome inspection.
Classification: Prospective primary universe-measurement source amendment; no threshold change.

Previous source: FMP EOD Bulk `close × volume` under A2. Replacement source: Massive `/v2/aggs/grouped/locale/us/market/stocks/{date}?adjusted=false&include_otc=false`, using unadjusted `c` (close) × `v` (volume). Never use adjusted closes or returns. Massive grouped-daily volume may include extended-hours trading, so this is an operational approximation to the originally stated regular-session dollar-volume measure. It can affect universe membership and must be disclosed with all subsequent findings.

This amendment is made solely because the intended regular-session bulk source is unavailable: Massive cannot establish exclusively regular-session grouped volume, and the replacement FMP EOD Bulk request returned HTTP 402 under current entitlement. FMP EOD Bulk will not be retried. This amendment occurred before any strategy returns were inspected. No holdout observations or post-entry returns/P&L were inspected.

Preserve previous unadjusted close ≥$10, median `close × volume` over all preceding 20 completed exchange sessions ≥$20M, all 20 observations required, the 1,500-request / 4,000,000,000-byte cumulative Stage B caps, and every other hypothesis, signal, split, boundary purge, holdout protection, feasibility threshold, cost and outcome rule. Use only the 710 sessions from 2023-03-06 through 2025-12-31; verified cached pilot files may be reused within that range. No later-session prices may enter a candidate's screen.

Massive historical reference/corporate-action/stock quote and Databento options requirements remain unchanged. Liquidity survivors are provisional pending historical common-stock/type/issuer/security and event/fiscal-period validation; no full feasibility pass is inferred.


### Amendment A4 — total acquisition request budget

Recorded at: 2026-10-04T00:13:58.267693-04:00
Authorization: Explicit user instruction before remaining exact-date reference acquisition and before any outcome inspection.
Classification: Operational acquisition-budget amendment only.

Previous total acquisition request ceiling: 1,500 requests. Replacement total acquisition request ceiling: **2,500 requests**. The cumulative transfer ceiling remains **4,000,000,000 bytes**. Count all recorded Stage B acquisition requests/bytes, including unsuccessful calls and reused-file accounting without double counting.

Reason: Exact historical reference validation requires at least approximately 604 further date-specific requests, with actual pagination and exception work additional. This amendment occurred before any strategy returns were inspected. It does not change the hypothesis, signal, thresholds, universe rules, split dates, holdout protection, outcome rules, timestamp evidence requirements or fiscal/issuer deduplication requirements. No holdout or post-entry returns/P&L are authorized. The operational FMP bmo/amc gate remains passed; full historical timestamp/vintage verification remains unproven.


### Amendment A5 — operational historical-status bracketing

Recorded at: 2026-10-04T00:24:51.338451-04:00
Authorization: Explicit user instruction before outcome inspection; no further Massive historical-reference API requests are permitted.
Classification: Prospective operational historical-status approximation, not proof of uninterrupted listing.

Use the 34 completed Massive reference snapshots locally. At a candidate decision/entry session D equal to an anchor, retain exact-date common-stock and identifier evidence. Between consecutive anchors, require the candidate ticker to appear in both as qualifying U.S. common stock, with matching stable FIGI and issuer identity. Mark ticker/type/identifier changes, missing bracket endpoints or missing identity evidence unresolved/excluded from operational eligibility. Do not extrapolate outside the bracketing date range. Matching endpoints do not establish uninterrupted common-stock status or ticker ownership on every intervening day; disclose this limitation. Exact-date reference status does not verify earnings release timing or vendor vintage.

Preserve all original hypotheses, signals, thresholds, issuer/share-class selection, fiscal-period deduplication, split dates, purging, holdout and outcome rules. Fiscal/quarter labels and original-release verification limitations remain explicit. Operational FMP bmo/amc coverage remains passed; full historical timestamp/vintage proof remains unproven. No returns or holdout observations are authorized.


### Amendment A6 — frozen outcome-blind development sample

Recorded at: 2026-10-04T04:48:33.219599+00:00
Authorization: Explicit user instruction before any strategy returns or X values were inspected.

Full-universe NBBO acquisition is operationally impractical. From the 14,340 operationally eligible events, rank independently within each split by the ascending SHA256 hex digest of the UTF-8 literal `stable_issuer_id|event_date|fiscal_year|fiscal_quarter`. Define stable_issuer_id as the stored zero-padded issuer CIK (not ticker or share-class FIGI), event_date as the ISO earnings release_date, and fiscal labels as their stored canonical strings (year and Q1–Q4). No whitespace is added around pipes. Resolve a hash tie lexicographically by that same input string, then stable share-class identifier and ticker. Freeze the first 1,500 train and 600 validation events. Failures or missing data remain exclusions within the frozen denominator; never backfill or expand after X or returns are observed. Preserve this exact deterministic ranking rule for the eventual holdout; holdout sample size remains unspecified and no holdout access is authorized now.

Raise the cumulative operational acquisition request ceiling to 50,000 requests for this fixed sample, allowing quote pagination, cost metadata, historical definitions, selected-pair quotes and preregistered pre-decision stock/SPY/beta/action inputs. The 4,000,000,000-byte cumulative transfer ceiling remains unchanged. This authorization replaces pilot-only symbol restrictions with event-root Databento [ROOT].OPT historical definition queries, and authorizes only selected-pair cbbo-1m in the fixed pre-event window. Obtain provider cost/size estimates before billable retrieval; the existing USD 1.00 cost stop remains until a larger concrete estimate is approved.

Compute S0, M, the completed pre-decision reaction r and residual a, X and feasibility counts only on this sample. No subsequent ten-session returns, P&L, or holdout acquisition/inspection is authorized. This amendment precedes any strategy returns or X inspection. All hypotheses, signals, price/liquidity thresholds, contract selection, beta/action treatment, quote quality, splits, boundary purging, holdout protections and outcome rules remain unchanged. FMP timing and A5 historical-status approximations and their limitations remain explicit.


### Amendment A6 pause — benchmark before population decision

Recorded at: 2026-10-04T05:00:44.772652+00:00
The user paused A6 before any sample acquisition. Its local 2,100-event artifact and amendment had already been created, but are now inactive and preserved solely as an audit trail. No quotes, X, reactions, strategy outcomes or holdout data were acquired for that sample. The full 14,340-event universe remains the population for deciding between full acquisition and the proposed deterministic sample. Restore the prior 2,500-request ceiling during the 20-event benchmark; the 4 GB transfer ceiling remains.

Select 20 benchmark events independently of outcomes: 10 train and 10 validation. Within each split, sort by entry session, release date, issuer CIK and symbol and divide into five equal-count chronological strata. Within each stratum sort by the stored pre-event trailing-20-session median dollar volume, split into lower and upper halves, and select one event from each half by smallest SHA256 of issuer CIK|release date|fiscal year|quarter. No X or post-event inputs enter selection. Acquire complete fixed pre-event windows sequentially, including pagination, and measure actual transferred bytes and end-to-end runtime. Report split-specific S0 success and extrapolate by split weights to the full universe, with uncertainty and provider/transfer limits disclosed. Retain the full universe if projected acquisition is at most 90 minutes and operationally feasible; otherwise return to the proposed deterministic sample. No X, reaction, outcome or subsequent-return inspection during this benchmark.

### A6 benchmark decision — retain the full universe

Recorded after the 20-event benchmark, before any X, reactions, strategy outcomes or subsequent returns were inspected. Benchmark: 20 complete NBBO windows, 20 requests including pagination (no additional pages required), 843,676 transferred NBBO bytes, 4.781935 seconds of end-to-end NBBO processing, valid S0 for 10/10 train and 10/10 validation events. Two auxiliary quote-condition schema calls used 22,183 bytes, for 22 total Massive calls / 865,859 total bytes. No historical security-reference acquisition occurred.

Stratum-population weighting projects the full 14,340-event NBBO acquisition at 14,340 requests, 660,963,188 bytes and 59.002792 minutes. A heuristic 1.5× sensitivity gives 21,510 requests, 991,444,782 bytes and 88.504188 minutes; it is not a confidence bound. Projected central cumulative transfer, reusing benchmark windows, is 1,569,928,498 bytes under 4 GB. Existing historical quote access succeeded and Massive's official stock product page documents unlimited paid-plan API calls. Neither endpoint latency nor pagination tails are guaranteed by 20 observations.

Under the user's prospective 90-minute decision rule, **retain all 14,340 operationally eligible development events** (8,688 train / 5,652 validation). A6's 2,100-event sampling branch remains inactive; its prior artifact is audit-only and must not drive acquisition or change the population. Original hypotheses, signals, quote/contract rules, feasibility minimums, splits, holdout and outcomes remain unchanged. No full-universe acquisition was executed during this benchmark. The internal request ceiling is currently restored to 2,500; raise it prospectively before full acquisition using the measured request estimate and explicit operational authorization. Continue to enforce the unchanged cumulative 4 GB transfer ceiling. Options and pre-decision reaction/beta/action costs remain separate from this NBBO projection. See results/NBBO_REPRESENTATIVE_BENCHMARK.md and data/cache/nbbo_benchmark_results.json.


### Amendment A7 — full-universe pre-event NBBO acquisition budget

Recorded at: 2026-10-04T05:14:26.082925+00:00
Authorization: Explicit user instruction, justified by the completed representative benchmark, before any X values or strategy outcomes were inspected.

Raise the operational Massive acquisition request ceiling from 2,500 to **20,000 requests**. Preserve the cumulative **4,000,000,000-byte** transfer ceiling. Conservatively count all previously recorded acquisition calls against the 20,000 ceiling in the shared ledger; no provider counter reset or prior request subtraction. Subsequent Databento calls are also recorded against this conservative shared counter unless explicitly separated in a later authorization. This is solely an operational acquisition-budget amendment, with no change to hypotheses, signals, price/liquidity thresholds, universe, split dates, purging, holdout, outcome rules or sample size. The proposed deterministic sample remains inactive; retain all 14,340 operationally eligible development events.

Acquire complete underlying NBBO windows [15:50,15:55) ET using the benchmark implementation: valid SIP timestamps inside the window, positive bid, ask greater than bid, positive sizes, and no nonregular condition codes. Accept absent/empty conditions or code 1 (provider-labelled Regular Two-Sided Open), exactly as in the completed benchmark. Require at least three distinct valid minute bins and define S0 as the median of all valid quote midpoints. Reuse hash-verified complete benchmark windows. Checkpoint each page and complete event; count retries and failed requests/bytes; never use an incomplete page set for S0. Modest concurrency of two independent event windows is operationally permitted under the documented paid-plan request policy, within the existing Slurm compute allocation.

If S0 coverage is adequate for continued feasibility measurement, proceed directly to historical event-root Databento OPRA.PILLAR definitions, original D+7…D+21 earliest-expiry/nearest-strike/lower-tie/standard-unadjusted-100-share/matching-pair selection, and only selected-pair cbbo-1m in the fixed pre-event window to compute M and contract/quote coverage. The original contract and synchronized-quote thresholds are unchanged. Obtain concrete cost/transfer estimates before billable Databento retrieval, retaining the existing dollar-cost stop until explicitly amended. No post-event/outcome requests, X calculation, subsequent ten-session returns or holdout access are authorized in this acquisition step. Operational FMP timing remains passed with historical timestamp/vintage unproven.


### Stage C — authorized historical-definition cost stop

Recorded at: 2026-10-04T09:38:40.166619+00:00
Authorization: Explicit user approval to raise the Databento cost stop to **USD 12.00 for preregistered historical definitions only**, using the completed $11.407067812972 / 2,449,649,160-billable-byte estimate. Preserve the cumulative 20,000-request and 4,000,000,000-byte ceilings. Run billable retrieval only in a Slurm compute-node batch job, checkpoint complete date queries, and preserve unresolved roots as exclusions without substitutions.

After complete definitions, select the original earliest-expiry D+7 through D+21 inclusive / nearest-strike / lower-tie / standard-unadjusted-100-share matching call-put pairs before quote quality. Obtain selected-pair cbbo-1m cost and size estimates separately; this approval does not authorize quote retrieval. Stop before any acquisition that risks the dollar or cumulative-transfer ceiling. No holdout, ten-day outcomes or methodology changes are authorized.

### Submission-critical execution authorization

Recorded 2026-10-04 before outcome inspection. User explicitly authorized immediate selected-pair quote retrieval if completed estimates remain under cumulative $12 / 4 GB / 20,000 requests, followed by M, frozen downstream implementation, development analysis and one final holdout evaluation after implementation freeze. Estimate passed: $11.619009859801 combined conservative spend, 624,933,376-byte quote transfer bound, 581 retrieval requests. Preserve the original contract-selection, quality, signal, costs and feasibility thresholds.

Historical contract coverage fails the original 80% minimum in both development splits (73.94% train, 63.55% validation). The experiment remains infeasible under its original full-coverage specification. The user authorized transparent available-event hackathon analysis despite that failure; it does not turn feasibility into a pass.

The shared request cap permits only 406 requests after selected-pair quotes, insufficient for full-universe post-event NBBO and outcomes. Any reuse of the existing outcome-blind 20-event benchmark for a budget-bounded downstream demonstration is exploratory, not a replacement primary strategy population or evidence of full-universe predictive performance. Retain all full-universe M results and exclusions, and disclose demonstration attrition without replacement of failed events.

### Submission implementation choices before development outcomes

Core computations use a standard-library implementation with action-aware raw-price total returns (cash dividends retained without reinvestment), intercept OLS beta, fixed X thresholds, and two-way cluster covariance with finite-cluster corrections and t degrees of freedom equal to the smaller cluster count minus one. Fewer than 30 clusters in either dimension remains unreliable/inconclusive. The descriptive X plot uses fixed buckets (0,0.5], (0.5,1], (1,1.5], (1.5,2], (2,3], and >3; these bins do not define new strategies.

Intended shares use the completed S1, available before the execution window; historical midpoint execution with adverse half-spread plus 2 bps is a simulation benchmark. All same-security orders in an execution window share the participation budget. Daily marking uses raw closes with held-share corporate-action adjustments and accrues dividends as cash. Missing closes retain a previous mark with an explicit incomplete-mark flag; missing scheduled exits retain unresolved exposure. No-entry portfolio statistics are unmeasured rather than presented as evidence of zero-risk profitability.

Modeled agency sell-side SEC/FINRA pass-through fees follow their historical schedules. Exchange/CAT route fees and any unresolved 2026 fee component remain disclosed as incomplete accounting; results cannot claim net of all fees. Missing borrow prevents executable shorts and short-SPY hedge legs. A prospective one-shot holdout freeze hashes all implementation/specification files before any 2026 input access. An incomplete/budget-blocked holdout acquisition is reported as inconclusive, never as a completed inferential evaluation.

### Prospective budget-bounded holdout demonstration

Before any 2026 observation access, freeze a maximum-three-event exploratory holdout pilot because full primary holdout acquisition is not funded under the unchanged caps. This is not a replacement confirmatory population. After the implementation hash freeze, acquire the fixed-date raw calendar and select the three smallest original issuer/release/fiscal-year/quarter hashes among unambiguous source bmo/amc records with provided fiscal-year/quarter fields in the legacy development issuer/FIGI universe. Exact historical common-stock identity/status, original liquidity, S0, expiry/strike/100-share matching pair, quote quality/synchronization, beta/reaction, outcome, execution and cost rules still apply. No failed selected event is replaced. Historical metadata and explicit cost/transfer estimates precede any billable holdout definitions or selected-pair quotes. Stop on the existing $12/4GB/20,000 ceilings. Empty/insufficient/blocked observations remain inconclusive, and the full original holdout is disclosed as incomplete. The raw-calendar API's original timestamp/vintage/completeness limitations remain explicit.
