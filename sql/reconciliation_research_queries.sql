-- ====================================================================
-- Ad-Ops Revenue Leakage & Discrepancy SQL Research Suite
-- Author: Shrey Gupta
-- Project: Ad-Ops Telemetry & Attribution Reconciliation Engine
-- ====================================================================

-- Query 1: Partner Discrepancy & Revenue Leakage Audit (Against 2% SLA)
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

-- Query 2: Technical Latency Tiers vs. Dropped Win-Notices (>1000ms Inflection Point)
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

-- Query 3: MRC Viewability Standards vs. Billing Status
SELECT 
    CASE WHEN s.is_viewable = 1 THEN 'Viewable (MRC Standard Met)' ELSE 'Non-Viewable (<50% in viewport)' END AS viewability_status,
    COUNT(s.impression_id) AS total_impressions,
    COUNT(d.impression_id) AS dsp_billed_impressions,
    COUNT(s.impression_id) - COUNT(d.impression_id) AS dropped_impressions,
    ROUND((1.0 - (COUNT(d.impression_id)*1.0 / COUNT(s.impression_id))) * 100, 2) AS drop_rate_pct
FROM ad_server s
LEFT JOIN dsp_reports d ON s.impression_id = d.impression_id
GROUP BY s.is_viewable;

-- Query 4: Multi-Touch User Journey Depth
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
