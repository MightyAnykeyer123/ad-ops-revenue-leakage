import sqlite3
import pandas as pd

conn = sqlite3.connect(":memory:")

print("Loading telemetry datasets into research memory engine...")
pd.read_csv("data/ad_server_impressions.csv").to_sql("ad_server", conn, index=False)
pd.read_csv("data/dsp_network_reports.csv").to_sql("dsp_reports", conn, index=False)
pd.read_csv("data/attribution_conversions.csv").to_sql("conversions", conn, index=False)

print("\n" + "="*85)
print("RESEARCH AUDIT 1: DISCREPANCY & REVENUE LOSS BY PLACEMENT (Display vs Video)")
print("Objective: Isolate which inventory formats suffer the worst ad-delivery leakage")
print("="*85)
q1 = """
SELECT 
    s.placement_id,
    s.placement_name,
    COUNT(s.impression_id) AS server_delivered,
    COUNT(d.impression_id) AS dsp_billed,
    COUNT(s.impression_id) - COUNT(d.impression_id) AS unbilled_units,
    ROUND((1.0 - (COUNT(d.impression_id)*1.0 / COUNT(s.impression_id))) * 100, 2) AS discrepancy_pct,
    ROUND(SUM(CASE WHEN d.impression_id IS NULL THEN (
        CASE 
            WHEN s.campaign_id = 'CMP-101' THEN 6.50
            WHEN s.campaign_id = 'CMP-102' THEN 3.80
            WHEN s.campaign_id = 'CMP-103' THEN 1.20
            ELSE 4.50
        END / 1000.0) ELSE 0 END), 2) AS unbilled_loss_usd
FROM ad_server s
LEFT JOIN dsp_reports d ON s.impression_id = d.impression_id
GROUP BY s.placement_id, s.placement_name
ORDER BY unbilled_loss_usd DESC;
"""
print(pd.read_sql_query(q1, conn).to_string(index=False))

print("\n" + "="*85)
print("RESEARCH AUDIT 2: MRC VIEWABILITY STANDARDS VS. DSP BILLING STATUS")
print("Objective: Test whether dropped impressions are driven by non-viewable impressions")
print("="*85)
q2 = """
SELECT 
    CASE WHEN s.is_viewable = 1 THEN 'Viewable (MRC Standard Met)' ELSE 'Non-Viewable (<50% in viewport)' END AS viewability_status,
    COUNT(s.impression_id) AS total_impressions,
    COUNT(d.impression_id) AS dsp_billed_impressions,
    COUNT(s.impression_id) - COUNT(d.impression_id) AS dropped_impressions,
    ROUND((1.0 - (COUNT(d.impression_id)*1.0 / COUNT(s.impression_id))) * 100, 2) AS drop_rate_pct
FROM ad_server s
LEFT JOIN dsp_reports d ON s.impression_id = d.impression_id
GROUP BY s.is_viewable;
"""
print(pd.read_sql_query(q2, conn).to_string(index=False))

print("\n" + "="*85)
print("RESEARCH AUDIT 3: MULTI-TOUCH JOURNEY DEPTH PER USER")
print("Objective: Examine how many ad touchpoints users see before converting")
print("="*85)
q3 = """
WITH user_touchpoints AS (
    SELECT 
        c.user_pseudo_id,
        c.conversion_id,
        c.order_revenue_usd,
        COUNT(s.impression_id) AS total_impressions_exposed,
        SUM(s.has_click) AS total_clicks_engaged
    FROM conversions c
    JOIN ad_server s ON c.user_pseudo_id = s.user_pseudo_id
    WHERE s.timestamp <= c.conversion_timestamp
    GROUP BY c.user_pseudo_id, c.conversion_id, c.order_revenue_usd
)
SELECT 
    CASE 
        WHEN total_impressions_exposed = 1 THEN '1 Touchpoint (Direct)'
        WHEN total_impressions_exposed BETWEEN 2 AND 4 THEN '2-4 Touchpoints'
        ELSE '5+ Touchpoints (Complex Journey)'
    END AS journey_depth,
    COUNT(conversion_id) AS conversion_count,
    ROUND(SUM(order_revenue_usd), 2) AS total_revenue_usd,
    ROUND(AVG(total_clicks_engaged), 2) AS avg_clicks_per_converting_user
FROM user_touchpoints
GROUP BY 1
ORDER BY conversion_count DESC;
"""
print(pd.read_sql_query(q3, conn).to_string(index=False))

print("\n" + "="*85)
print("RESEARCH AUDIT 4: CROSS-TAB DISCREPANCY MATRIX (DSP PARTNER X PLACEMENT)")
print("Objective: Pinpoint if specific DSPs have chronic drop rates on specific formats")
print("="*85)
q4 = """
SELECT 
    s.dsp_partner,
    s.placement_id,
    COUNT(s.impression_id) AS served,
    COUNT(d.impression_id) AS billed,
    ROUND((1.0 - (COUNT(d.impression_id)*1.0 / COUNT(s.impression_id))) * 100, 2) AS discrepancy_pct
FROM ad_server s
LEFT JOIN dsp_reports d ON s.impression_id = d.impression_id
GROUP BY s.dsp_partner, s.placement_id
ORDER BY s.dsp_partner, discrepancy_pct DESC;
"""
print(pd.read_sql_query(q4, conn).to_string(index=False))

print("\n" + "="*85)
print("RESEARCH AUDIT 5: FIRST-TOUCH VS. LAST-TOUCH ATTRIBUTION RE-ALLOCATION")
print("Objective: Quantify exact revenue shift when upper-funnel discovery is credited")
print("="*85)
q5 = """
WITH ranked_touchpoints AS (
    SELECT 
        c.conversion_id,
        c.order_revenue_usd,
        s.campaign_id,
        s.campaign_name,
        s.timestamp,
        ROW_NUMBER() OVER(PARTITION BY c.conversion_id ORDER BY s.timestamp ASC) as rn_first,
        ROW_NUMBER() OVER(PARTITION BY c.conversion_id ORDER BY s.timestamp DESC) as rn_last
    FROM conversions c
    JOIN ad_server s ON c.user_pseudo_id = s.user_pseudo_id
    WHERE s.timestamp <= c.conversion_timestamp AND s.has_click = 1
),
first_touch AS (
    SELECT campaign_id, campaign_name, SUM(order_revenue_usd) as ft_revenue
    FROM ranked_touchpoints
    WHERE rn_first = 1
    GROUP BY campaign_id, campaign_name
),
last_touch AS (
    SELECT campaign_id, campaign_name, SUM(order_revenue_usd) as lt_revenue
    FROM ranked_touchpoints
    WHERE rn_last = 1
    GROUP BY campaign_id, campaign_name
)
SELECT 
    lt.campaign_id,
    lt.campaign_name,
    ROUND(lt.lt_revenue, 2) AS last_touch_credited_usd,
    ROUND(COALESCE(ft.ft_revenue, 0), 2) AS first_touch_credited_usd,
    ROUND(COALESCE(ft.ft_revenue, 0) - lt.lt_revenue, 2) AS net_revenue_variance_usd
FROM last_touch lt
LEFT JOIN first_touch ft ON lt.campaign_id = ft.campaign_id
ORDER BY net_revenue_variance_usd DESC;
"""
print(pd.read_sql_query(q5, conn).to_string(index=False))
