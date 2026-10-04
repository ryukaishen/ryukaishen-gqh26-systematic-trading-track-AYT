# Stage A remediation results

Date: 2026-10-03
Scope: Five approved remediation requests, followed by one separately approved final direct-contract request. Execution stopped after Stage A.

## Sanitized results

| Request | Status | Sanitized result | Records | Response-body bytes |
|---|---|---|---:|---:|
| R1 | Succeeded, HTTP 200 | MSFT 2023-05-05 strike-150 call/put; American exercise; 100 shares per contract; primary exchange BATO | 2 | 534 |
| R2 | Empty, HTTP 200 | Adding `as_of=2023-04-25` to the R1 list query returned no records | 0 | 76 |
| R3 | Not executed | Initially omitted because the exact M10 call ticker had not been preserved in local sanitized Stage A evidence | — | — |
| R4 | Succeeded, HTTP 200 | Confirmed NVDA forward-split example dated 2024-06-10, ratio 1 → 10 | 1 | 298 |
| R5 | Succeeded, HTTP 200 | Confirmed AAPL recurring USD 0.24 dividend example, ex-date 2023-05-12 | 1 | 437 |
| R6 | Succeeded, HTTP 200 | Confirmed ATVI historical ticker detail for 2023-10-12: active common stock on XNAS with CIK and FIGIs | 1 | 1,276 |
| R3-final | Succeeded, HTTP 200 | Retrieved `O:MSFT230505C00150000` using `as_of=2023-04-25` | 1 | 303 |

The initial five-request run returned 5 records and 2,621 response-body bytes. The separately approved R3-final request returned 1 record and 303 bytes. Combined remediation totals: **6 executed requests, 6 records, and 2,924 response-body bytes**. No response reached its approved record or byte cap. No pagination was present or followed.

## Preserved allowlisted fields

R1 returned these exact identifiers:

- Call: `O:MSFT230505C00150000`
- Put: `O:MSFT230505P00150000`

Both R1 contracts had underlying MSFT, expiration 2023-05-05, strike 150, American exercise, 100 shares per contract, and primary exchange BATO.

R2 used the same list filters as R1 with `as_of=2023-04-25` added. Its HTTP 200 empty result does not establish absent historical coverage.

R3 was omitted before the initial remediation run because the local Stage A audit preserved M10's strike and expiry but not its exact call ticker. R1 subsequently preserved the exact call ticker. R3-final was separately approved and executed using that observed identifier.

R4 fields: ticker NVDA; execution date 2024-06-10; split_from 1; split_to 10; adjustment type forward_split.

R5 fields: ticker AAPL; ex-dividend date 2023-05-12; original cash amount USD 0.24; declaration date 2023-05-04; record date 2023-05-15; payment date 2023-05-18; frequency 4; distribution type recurring.

R6 fields: ticker ATVI; market stocks; locale us; primary exchange XNAS; security type CS; active true; CIK `0000718877`; composite FIGI `BBG000CVWGS6`; share-class FIGI `BBG001S6C009`; listing date 1993-10-22. This historical-detail example does not establish complete delisting or merger coverage.

R3-final fields: ticker `O:MSFT230505C00150000`; underlying MSFT; contract type call; expiration 2023-05-05; strike 150; American exercise; 100 shares per contract; primary exchange BATO.

## Conclusions

- Direct historical option-contract lookup is supported for this example.
- List-endpoint `as_of`/`expired` semantics remain unresolved.
- Complete historical chain provenance is not yet established.

The revised list queries avoided HTTP 400, but the original rejection's cause remains unproven. Successful direct lookup does not independently establish the contract's historical listing provenance or complete chain membership.

## Safeguards and execution history

No retries, redirects, pagination, request expansion, earnings-source requests, Stage B–D requests or data, holdout observations, prices or returns, signal-performance analysis, backtests, package installations, purchases, or subscription changes were performed during remediation. No credentials, raw responses, raw headers, Request objects, Authorization values, or raw exception objects were exposed. Authentication remained in process memory and only sanitized allowlisted fields/statuses were reported.

The earlier Stage A execution attempt was aborted without output; whether its requests reached the providers remains unknown. These remediation totals describe the completed remediation requests only and do not establish the total number of provider requests ever attempted.

EXPERIMENT.md and DATA_AUDIT.md were not modified. Execution stopped after Stage A.
