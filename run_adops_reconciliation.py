import sqlite3
import pandas as pd

conn = sqlite3.connect(":memory:")

print("Loading ad-ops telemetry tables into SQLite engine...")
pd.read_csv("data/ad_server_impressions.csv").to_sql("ad_server", conn, index=False)
pd.read_csv("data/dsp_network_reports.csv").to_sql("dsp_reports", conn, index=False)
pd.read_csv("data/attribution_conversions.csv").to_sql("conversions", conn, index=False)

print("\n" + "="*80)
print("1. PARTNER DISCREPANCY & REVENUE LEAKAGE AUDIT (BY DSP)")
print("Objective: Isolate unbilled impressions and financial loss against 2% SLA threshold")
print("="*80)

q1 = """
SELECT 
    s.dsp_partner,
    COUNT(s.impression_id) AS server_impressions,
    COUNT(d.impression_id) AS dsp_billed_impressions,
    COUNT(s.impression_id) - COUNT(d.impression_id) AS dropped_impressions,
    ROUND((1.0 - (COUNT(d.impression_id) * 1.0 / COUNT(s.impression_id))) * 100, 2) AS discrepancy_pct,
    ROUND(SUM(CASE WHEN d.impression_id IS NULL THEN (
        CASE 
            WHEN s.campaign_id = 'CMP-101' THEN 6.50
            WHEN s.campaign_id = 'CMP-102' THEN 3.80
            WHEN s.campaign_id = 'CMP-103' THEN 1.20
            ELSE 4.50
        END / 1000.0) ELSE 0 END), 2) AS estimated_revenue_leakage_usd
FROM ad_server s
LEFT JOIN dsp_reports d ON s.impression_id = d.impression_id
GROUP BY s.dsp_partner
ORDER BY discrepancy_pct DESC;
"""
print(pd.read_sql_query(q1, conn).to_string(index=False))

print("\n" + "="*80)
print("2. TECHNICAL ROOT-CAUSE: LATENCY TIERS VS. DROPPED IMPRESSION RATE")
print("Objective: Prove whether network timeout (>1000ms) is breaking win-notice callbacks")
print("="*80)

q2 = """
SELECT 
    CASE 
        WHEN s.latency_ms < 300 THEN '1. Optimal (<300ms)'
        WHEN s.latency_ms BETWEEN 300 AND 600 THEN '2. Normal (300-600ms)'
        WHEN s.latency_ms BETWEEN 601 AND 1000 THEN '3. High Latency (601-1000ms)'
        ELSE '4. Critical Timeout (>1000ms)'
    END AS latency_tier,
    COUNT(s.impression_id) AS total_impressions,
    COUNT(s.impression_id) - COUNT(d.impression_id) AS unbilled_impressions,
    ROUND((1.0 - (COUNT(d.impression_id) * 1.0 / COUNT(s.impression_id))) * 100, 2) AS drop_rate_pct
FROM ad_server s
LEFT JOIN dsp_reports d ON s.impression_id = d.impression_id
GROUP BY 1
ORDER BY 1;
"""
print(pd.read_sql_query(q2, conn).to_string(index=False))

print("\n" + "="*80)
print("3. ATTRIBUTION CANNIBALIZATION: RETARGETING VS. PROSPECTING CREDIT")
print("Objective: Measure revenue credited via Last-Touch vs. Upper-Funnel Assisted Clicks")
print("="*80)

q3 = """
SELECT 
    s.campaign_id,
    s.campaign_name,
    COUNT(DISTINCT c.conversion_id) AS direct_last_touch_conversions,
    ROUND(SUM(c.order_revenue_usd), 2) AS credited_revenue_usd,
    ROUND(AVG(c.order_revenue_usd), 2) AS avg_conversion_aov
FROM conversions c
JOIN ad_server s ON c.last_touch_impression_id = s.impression_id
GROUP BY s.campaign_id, s.campaign_name
ORDER BY credited_revenue_usd DESC;
"""
print(pd.read_sql_query(q3, conn).to_string(index=False))
