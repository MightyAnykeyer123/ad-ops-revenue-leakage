# Digital Ad-Ops: Attribution Discrepancy & Revenue Leakage Engine

Automated telemetry auditing, SLA reconciliation, and multi-touch attribution analysis designed to detect ad-delivery leakage between ad server logs and DSP billing feeds, isolate root-cause latency drops, and evaluate multi-touch conversion journeys.

---

## Executive Summary & Key Audit Findings

Based on an audit of 120,000 ad server delivered impressions and 127 converting journey paths ($8,918.49 total GMV) across Amazon DSP, DV360, The Trade Desk, and Xandr:

* **Systemic SLA Breaches:** Total delivery revealed a 7.21% net discrepancy (8,649 unbilled units), breaching the standard 2.0% MSA tolerance across 100% of placement and partner combinations.
* **Root-Cause Isolation (MRC Standards):** Viewable impressions and non-viewable impressions both exhibited an identical 7.21% drop rate. This proves delivery loss is driven by transport-layer latency and gateway timeouts before beacon firing, rather than viewability filtering.
* **Attribution Journey Depth:** 85.0% of all conversions (108 out of 127) involved multi-touch interaction paths (2+ touches), accounting for 83.9% ($7,485.56) of total conversion value.
* **Upper-Funnel Shifts:** Reallocating credit from last-touch to first-touch demonstrates the shift in credited value toward prospecting and dynamic retargeting campaigns.

---

## Research Audit 1: Discrepancy & Revenue Loss by Placement

Objective: Isolate which inventory formats suffer the highest volume of unbilled delivery leakage.

| Placement ID | Placement Name | Server Delivered | DSP Billed | Unbilled Units | Discrepancy Rate (%) | Unbilled Loss (USD) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| PLC-MOBI-03 | Mobile InArticle MediumRectangle | 35,992 | 33,346 | 2,646 | 7.35% | $10.31 |
| PLC-HERO-01 | Desktop Leaderboard 728x90 | 36,048 | 33,393 | 2,655 | 7.37% | $10.28 |
| PLC-SIDE-02 | Sidebar Sticky 300x600 | 30,064 | 27,979 | 2,085 | 6.94% | $8.12 |
| PLC-VID-04 | Preroll Video 15s | 17,896 | 16,633 | 1,263 | 7.06% | $5.02 |
| **Total** | **All Placements** | **120,000** | **111,351** | **8,649** | **7.21%** | **$33.73** |

---

## Research Audit 2: MRC Viewability Standards vs. DSP Billing Status

Objective: Test whether dropped impressions are driven by MRC non-viewable inventory thresholds.

| Viewability Status | Total Impressions | DSP Billed Impressions | Dropped Impressions | Drop Rate (%) |
| :--- | :--- | :--- | :--- | :--- |
| Viewable (MRC Standard Met) | 91,398 | 84,811 | 6,587 | 7.21% |
| Non-Viewable (<50% in Viewport) | 28,602 | 26,540 | 2,062 | 7.21% |

Finding: Drop rates are completely invariant to viewability compliance (7.21% vs. 7.21%). Delivery discrepancies occur upstream in the client handshake prior to the viewability measurement timer.

---

## Research Audit 3: Multi-Touch Journey Depth per User

Objective: Examine path length and interaction volume across converting users.

| Journey Depth | Conversion Count | Total Revenue (USD) | Revenue Share | Avg Clicks per Converter |
| :--- | :--- | :--- | :--- | :--- |
| 1 Touchpoint (Direct) | 19 | $1,432.93 | 16.07% | 1.00 |
| 2-4 Touchpoints | 62 | $4,623.82 | 51.85% | 1.06 |
| 5+ Touchpoints (Complex Journey) | 46 | $2,861.74 | 32.09% | 1.11 |
| **Total** | **127** | **$8,918.49** | **100.00%** | **1.07** |

---

## Research Audit 4: Cross-Tab Discrepancy Matrix (DSP Partner x Placement)

Objective: Pinpoint whether specific demand partners experience localized delivery drops.

| DSP Partner | Placement ID | Served | Billed | Discrepancy Rate (%) | SLA Status (> 2.0%) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Amazon DSP | PLC-HERO-01 | 7,199 | 6,647 | 7.67% | Breached |
| Amazon DSP | PLC-VID-04 | 3,605 | 3,352 | 7.02% | Breached |
| Amazon DSP | PLC-MOBI-03 | 7,169 | 6,672 | 6.93% | Breached |
| Amazon DSP | PLC-SIDE-02 | 6,006 | 5,602 | 6.73% | Breached |
| DV360 | PLC-MOBI-03 | 10,861 | 10,048 | 7.49% | Breached |
| DV360 | PLC-HERO-01 | 10,854 | 10,046 | 7.44% | Breached |
| DV360 | PLC-VID-04 | 5,331 | 4,944 | 7.26% | Breached |
| DV360 | PLC-SIDE-02 | 9,246 | 8,605 | 6.93% | Breached |
| The Trade Desk | PLC-MOBI-03 | 14,329 | 13,261 | 7.45% | Breached |
| The Trade Desk | PLC-HERO-01 | 14,308 | 13,257 | 7.35% | Breached |
| The Trade Desk | PLC-VID-04 | 7,162 | 6,652 | 7.12% | Breached |
| The Trade Desk | PLC-SIDE-02 | 11,910 | 11,077 | 6.99% | Breached |
| Xandr | PLC-MOBI-03 | 3,633 | 3,365 | 7.38% | Breached |
| Xandr | PLC-SIDE-02 | 2,902 | 2,695 | 7.13% | Breached |
| Xandr | PLC-HERO-01 | 3,687 | 3,443 | 6.62% | Breached |
| Xandr | PLC-VID-04 | 1,798 | 1,685 | 6.28% | Breached |

---

## Research Audit 5: First-Touch vs. Last-Touch Attribution Re-Allocation

Objective: Quantify budget and revenue variance when upper-funnel discovery touchpoints receive credit.

| Campaign ID | Campaign Name | Last-Touch Credited (USD) | First-Touch Credited (USD) | Net Revenue Variance (USD) |
| :--- | :--- | :--- | :--- | :--- |
| CMP-103 | Q3 DPA Dynamic Retargeting | $3,795.80 | $3,820.81 | +$25.01 |
| CMP-102 | Q3 Performance Prospecting Display | $3,089.79 | $3,114.78 | +$24.99 |
| CMP-101 | Q3 Brand Awareness Video | $1,430.94 | $1,405.94 | -$25.00 |
| CMP-104 | Q3 App Install Push | $601.96 | $576.96 | -$25.00 |

---

## Reproduction & Pipeline Execution

To regenerate the telemetry analysis and run the reconciliation audits locally:

1. Generate raw telemetry files: `python3 generate_data.py`
2. Run the SLA discrepancy evaluation: `python3 discrepancy_evaluator.py`
3. Run the multi-touch attribution engine: `python3 mta_engine.py`
4. Run the latency fallback simulation: `python3 latency_fallback_engine.py`
