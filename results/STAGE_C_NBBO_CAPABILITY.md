# Stage C underlying NBBO capability and full-set budget gate

Both authorized pre-event capability requests succeeded with HTTP 200:

| Symbol / event date | Window (ET) | Records | Response bytes | Pagination |
|---|---|---:|---:|---|
| MSFT / 2023-04-25 | [15:50,15:55) | 5 | 1,406 | Yes |
| AAPL / 2023-05-04 | [15:50,15:55) | 5 | 1,578 | Yes |

Bid/ask prices, displayed sizes and SIP timestamps are available. These incomplete five-record responses establish historical access, not complete S0 measurement. No median from the first page was used.

The local eligible event extract contains 8,688 train and 5,652 validation events, representing 14,340 distinct ticker/pre-event-session windows. Pre-event sessions are the trading sessions immediately preceding the recorded decision/entry sessions; the [15:50,15:55) ET window is unchanged. No resulting windows coincide with the recorded early closes.

The full Massive acquisition requires **at least 14,340 additional requests**, before pagination. The current cumulative ledger is 1,219 requests / 908,943,127 bytes, leaving 1,281 requests / 3,091,056,873 bytes. Thus the request lower bound alone would reach **15,559 cumulative requests**, exceeding the existing 2,500-request ceiling by **13,059 requests**. Subsequent Databento parent definition, selected-pair quote, and cost-estimation requests would add further requests.

This is a hard acquisition-budget blocker, not a historical NBBO entitlement failure. Full acquisition was not executed and the budget was not silently amended. Full response bytes cannot be reliably projected from two paginated five-record responses; no invented full-volume estimate is supplied. The request lower bound already precludes execution under the current ceiling.

| Coverage measure | Train | Validation |
|---|---|---|
| Complete-window S0 coverage | Unmeasured | Unmeasured |
| Historically selected contract-pair coverage | Unmeasured | Unmeasured |
| Valid synchronized underlying/call/put quote coverage | Unmeasured | Unmeasured |

No zero-coverage inference is made from unacquired data. No primary contracts were selected without valid S0, and no quotes for arbitrary strikes were substituted. The new instruction authorizes Databento [ROOT].OPT parent definition acquisition once the blocker is resolved; the earliest-expiry, standard unadjusted 100-share, nearest-strike/lower-tie and matched-pair rules remain unchanged. Quote-quality assessment follows selection, with no farther-strike/later-expiry substitution.

Evidence: `data/raw/stage_c_stock_nbbo_probe/manifest.json`, sanitized probe quote files, `data/cache/stage_c_nbbo_estimate.json`, and `data/cache/acquisition_budget.json`. Scripts: `scripts/stage_c_stock_nbbo_probe.py` (no automatic reruns) and `scripts/stage_c_nbbo_estimate.py` (local only).

No Massive reference requests, holdout access, post-entry returns or P&L inspection occurred. The operational FMP timing gate remains passed; historical timestamp/vintage verification remains unproven.
