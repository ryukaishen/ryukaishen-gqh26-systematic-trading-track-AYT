# Stage B2 grouped-daily pilot

Status: Three authorized requests completed; full acquisition blocked by session semantics.
Acquisition UTC time: 2026-10-04T03:22:49.874743+00:00

All requests used adjusted=false and include_otc=false. Dates were chosen locally from the timed FMP candidate set: low-volume 2025-12-31 has four pairs, high-volume 2023-06-30 has 3,723 pairs; 2023-03-01 is a pre-start lookback date. Holiday dates were not selected. No retries, redirects, pagination, or additional provider probes occurred.

| Role | Date | HTTP | Records | Response-body bytes |
|---|---|---:|---:|---:|
| low | 2025-12-31 | 200 | 11,824 | 1,222,183 |
| high | 2023-06-30 | 200 | 10,562 | 1,083,749 |
| lookback | 2023-03-01 | 200 | 10,846 | 1,112,082 |

Total: 3 requests, 3,418,014 response bytes. Saved only T, c, v, vw and t under data/raw/massive_grouped_pilot/ with hashes and sanitized manifest. No raw responses or credentials were persisted.

## Measured budget projection

Use 1.5 times the maximum measured body size, rounded upward: 1,833,275 bytes/date. This is a conservative planning allowance based on three examples, not a guarantee of future sizes. Runtime cumulative limits would still be required.

For at most 751 dates, reusing the three pilot files, projected cumulative acquisition including completed Stage B1 is **1,044 requests and 1,438,944,674 bytes**. Both fit 1,500 requests / 2 GB. The budget condition passes; the independent methodological suitability condition does not.

## Provider documentation and decision

The grouped daily endpoint documents daily OHLC, volume and VWAP, adjusted=false for unadjusted records, and no regular-session selection parameter:
https://massive.com/docs/rest/stocks/aggregates/daily-market-summary

The provider's extended-hours documentation states that U.S. stock data spans 04:00–20:00 Eastern, there is no session selector, and extended-hours trade conditions can update volume without updating bar prices. Its applicability explicitly includes /v2/aggs/...:
https://massive.com/knowledge-base/article/market-data-outside-of-normal-hours

The provider's stock flat-file overview also describes daily datasets covering pre-market, regular and after-hours activity; this corroborates the extended-session issue but is not itself an endpoint-specific regular-session guarantee:
https://massive.com/docs/flat-files/stocks/overview

Conclusion: these sources do not establish that grouped daily close, volume and VWAP are exclusively regular-session measurements. In particular, documented extended-hours volume inclusion prevents equating the reported volume with the preregistered regular-session volume. adjusted=false controls split adjustments, not session boundaries. No field in the acquired grouped records separates regular-session volume from extended-hours volume.

Therefore full grouped acquisition and the primary liquidity screen were not executed. It would silently change EXPERIMENT.md to use full-day volume as regular-session volume. No close threshold, dollar-volume median, survivor count or security-reference estimate is claimed. The conflicting timing pair remains flagged in the local candidate subset and must be excluded from session assignment.

To continue the unchanged primary specification, use a documented regular-session data source, or bounded intraday aggregates restricted to actual session hours (including early closes) with a fresh budget estimate. A full-day liquidity diagnostic or prospective change to the universe rule requires an explicit methodological decision; neither is assumed here. No extra acquisition probes were added.

## Safeguards

No 2026/holdout observations, post-entry return calculations, P&L, signals, or strategy outcomes were accessed. Pilot price/volume fields were acquired solely for liquidity capability assessment; no outcome comparisons were computed. No packages, GPUs, or Slurm jobs were used. All original methodology and outcome rules remain unchanged.
