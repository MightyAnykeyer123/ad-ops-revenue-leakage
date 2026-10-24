# Digital Ad-Ops: Attribution Discrepancy & Revenue Leakage Engine
Automated Telemetry Audit & Attribution Discrepancy Engine.
Loading telemetry datasets into research memory engine...

=====================================================================================
RESEARCH AUDIT 1: DISCREPANCY & REVENUE LOSS BY PLACEMENT (Display vs Video)
Objective: Isolate which inventory formats suffer the worst ad-delivery leakage
=====================================================================================
placement_id                   placement_name  server_delivered  dsp_billed  unbilled_units  discrepancy_pct  unbilled_loss_usd
 PLC-MOBI-03 Mobile_InArticle_MediumRectangle             35992       33346            2646             7.35              10.31
 PLC-HERO-01       Desktop_Leaderboard_728x90             36048       33393            2655             7.37              10.28
 PLC-SIDE-02           Sidebar_Sticky_300x600             30064       27979            2085             6.94               8.12
  PLC-VID-04                Preroll_Video_15s             17896       16633            1263             7.06               5.02

=====================================================================================
RESEARCH AUDIT 2: MRC VIEWABILITY STANDARDS VS. DSP BILLING STATUS
Objective: Test whether dropped impressions are driven by non-viewable impressions
=====================================================================================
             viewability_status  total_impressions  dsp_billed_impressions  dropped_impressions  drop_rate_pct
Non-Viewable (<50% in viewport)              28602                   26540                 2062           7.21
    Viewable (MRC Standard Met)              91398                   84811                 6587           7.21

=====================================================================================
RESEARCH AUDIT 3: MULTI-TOUCH JOURNEY DEPTH PER USER
Objective: Examine how many ad touchpoints users see before converting
=====================================================================================
                   journey_depth  conversion_count  total_revenue_usd  avg_clicks_per_converting_user
                 2-4 Touchpoints                62            4623.82                            1.06
5+ Touchpoints (Complex Journey)                46            2861.74                            1.11
           1 Touchpoint (Direct)                19            1432.93                            1.00

=====================================================================================
RESEARCH AUDIT 4: CROSS-TAB DISCREPANCY MATRIX (DSP PARTNER X PLACEMENT)
Objective: Pinpoint if specific DSPs have chronic drop rates on specific formats
=====================================================================================
 dsp_partner placement_id  served  billed  discrepancy_pct
  Amazon_DSP  PLC-HERO-01    7199    6647             7.67
  Amazon_DSP   PLC-VID-04    3605    3352             7.02
  Amazon_DSP  PLC-MOBI-03    7169    6672             6.93
  Amazon_DSP  PLC-SIDE-02    6006    5602             6.73
       DV360  PLC-MOBI-03   10861   10048             7.49
       DV360  PLC-HERO-01   10854   10046             7.44
       DV360   PLC-VID-04    5331    4944             7.26
       DV360  PLC-SIDE-02    9246    8605             6.93
TheTradeDesk  PLC-MOBI-03   14329   13261             7.45
TheTradeDesk  PLC-HERO-01   14308   13257             7.35
TheTradeDesk   PLC-VID-04    7162    6652             7.12
TheTradeDesk  PLC-SIDE-02   11910   11077             6.99
       Xandr  PLC-MOBI-03    3633    3365             7.38
       Xandr  PLC-SIDE-02    2902    2695             7.13
       Xandr  PLC-HERO-01    3687    3443             6.62
       Xandr   PLC-VID-04    1798    1685             6.28

=====================================================================================
RESEARCH AUDIT 5: FIRST-TOUCH VS. LAST-TOUCH ATTRIBUTION RE-ALLOCATION
Objective: Quantify exact revenue shift when upper-funnel discovery is credited
=====================================================================================
campaign_id                      campaign_name  last_touch_credited_usd  first_touch_credited_usd  net_revenue_variance_usd
    CMP-103         Q3_DPA_Dynamic_Retargeting                  3795.80                   3820.81                     25.01
    CMP-102 Q3_Performance_Prospecting_Display                  3089.79                   3114.78                     24.99
    CMP-101           Q3_Brand_Awareness_Video                  1430.94                   1405.94                    -25.00
    CMP-104                Q3_App_Install_Push                   601.96                    576.96                    -25.00
Ready
