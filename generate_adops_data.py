import numpy as np
import pandas as pd
from datetime import datetime, timedelta

np.random.seed(42)
NUM_IMPRESSIONS = 120_000

print(f"Generating {NUM_IMPRESSIONS:,} ad server telemetry events...")

start_date = datetime(2026, 9, 1)
timestamps = [start_date + timedelta(seconds=int(s)) for s in np.random.randint(0, 30 * 86400, NUM_IMPRESSIONS)]
timestamps.sort()

campaigns = [
    {"campaign_id": "CMP-101", "name": "Q3_Brand_Awareness_Video", "model": "CPM", "base_rate": 6.50},
    {"campaign_id": "CMP-102", "name": "Q3_Performance_Prospecting_Display", "model": "CPM", "base_rate": 3.80},
    {"campaign_id": "CMP-103", "name": "Q3_DPA_Dynamic_Retargeting", "model": "CPC", "base_rate": 1.20},
    {"campaign_id": "CMP-104", "name": "Q3_App_Install_Push", "model": "CPM", "base_rate": 4.50},
]
placements = [
    {"placement_id": "PLC-HERO-01", "name": "Desktop_Leaderboard_728x90", "type": "Display", "base_viewability": 0.82},
    {"placement_id": "PLC-SIDE-02", "name": "Sidebar_Sticky_300x600", "type": "Display", "base_viewability": 0.74},
    {"placement_id": "PLC-MOBI-03", "name": "Mobile_InArticle_MediumRectangle", "type": "Display", "base_viewability": 0.65},
    {"placement_id": "PLC-VID-04", "name": "Preroll_Video_15s", "type": "Video", "base_viewability": 0.91},
]
dsps = ["TheTradeDesk", "DV360", "Amazon_DSP", "Xandr"]

user_pool = [f"USR_{np.random.randint(10000, 99999):05d}" for _ in range(25_000)]
users = np.random.choice(user_pool, NUM_IMPRESSIONS)
campaign_choices = np.random.choice(campaigns, NUM_IMPRESSIONS, p=[0.25, 0.35, 0.25, 0.15])
placement_choices = np.random.choice(placements, NUM_IMPRESSIONS, p=[0.30, 0.25, 0.30, 0.15])
dsp_choices = np.random.choice(dsps, NUM_IMPRESSIONS, p=[0.40, 0.30, 0.20, 0.10])

imp_ids = [f"IMP-2026-{i:07d}" for i in range(1, NUM_IMPRESSIONS + 1)]

latencies = np.random.exponential(scale=350, size=NUM_IMPRESSIONS) + 120
viewability_scores = np.random.rand(NUM_IMPRESSIONS)
base_viewabilities = [p["base_viewability"] for p in placement_choices]
viewable_flags = (viewability_scores < base_viewabilities).astype(int)

ctrs = [0.012 if p["type"] == "Display" else 0.028 for p in placement_choices]
ctrs = [ctr * 2.2 if c["campaign_id"] == "CMP-103" else ctr for ctr, c in zip(ctrs, campaign_choices)]
click_flags = (np.random.rand(NUM_IMPRESSIONS) < ctrs).astype(int)

ad_server_df = pd.DataFrame({
    "impression_id": imp_ids,
    "timestamp": timestamps,
    "user_pseudo_id": users,
    "campaign_id": [c["campaign_id"] for c in campaign_choices],
    "campaign_name": [c["name"] for c in campaign_choices],
    "placement_id": [p["placement_id"] for p in placement_choices],
    "placement_name": [p["name"] for p in placement_choices],
    "dsp_partner": dsp_choices,
    "latency_ms": np.round(latencies, 1),
    "is_viewable": viewable_flags,
    "has_click": click_flags,
    "server_status": "DELIVERED"
})

print("Injecting DSP discrepancy vectors (ad-blockers, timeouts, dropped win notices)...")

dsp_records = []
for idx, row in ad_server_df.iterrows():
    drop_prob = 0.04
    if row["latency_ms"] > 1000:
        drop_prob += 0.40
    
    if np.random.rand() < drop_prob:
        continue
    
    base_rate = next(c["base_rate"] for c in campaigns if c["campaign_id"] == row["campaign_id"])
    cpm_variance = np.random.normal(loc=1.0, scale=0.03)
    billed_cpm = round(base_rate * cpm_variance, 4)
    
    dsp_records.append({
        "dsp_record_id": f"DSP-LOG-{len(dsp_records)+1:07d}",
        "impression_id": row["impression_id"],
        "dsp_partner": row["dsp_partner"],
        "dsp_timestamp": row["timestamp"] + timedelta(milliseconds=int(row["latency_ms"])),
        "campaign_id": row["campaign_id"],
        "placement_id": row["placement_id"],
        "recorded_cpm": billed_cpm,
        "media_cost_usd": round(billed_cpm / 1000.0, 5),
        "dsp_billing_status": "BILLED"
    })

dsp_df = pd.DataFrame(dsp_records)

print("Simulating conversions and multi-touch user journeys...")
clicked_impressions = ad_server_df[ad_server_df["has_click"] == 1].copy()
conversion_mask = np.random.rand(len(clicked_impressions)) < 0.06
converters = clicked_impressions[conversion_mask].copy()

conversions = []
for i, (_, row) in enumerate(converters.iterrows()):
    conv_time = row["timestamp"] + timedelta(hours=int(np.random.exponential(scale=18) + 1))
    order_val = float(np.random.choice([25.0, 49.99, 89.0, 149.0, 240.0], p=[0.25, 0.35, 0.20, 0.15, 0.05]))
    
    conversions.append({
        "conversion_id": f"CNV-{i+1:06d}",
        "user_pseudo_id": row["user_pseudo_id"],
        "last_touch_impression_id": row["impression_id"],
        "last_touch_campaign_id": row["campaign_id"],
        "conversion_timestamp": conv_time,
        "order_revenue_usd": order_val,
        "conversion_type": "PURCHASE"
    })

conversions_df = pd.DataFrame(conversions)

import os
os.makedirs("data", exist_ok=True)

ad_server_df.to_csv("data/ad_server_impressions.csv", index=False)
dsp_df.to_csv("data/dsp_network_reports.csv", index=False)
conversions_df.to_csv("data/attribution_conversions.csv", index=False)

print("\n" + "="*60)
print("SUCCESS: 3 Core Ad-Ops Datasets Generated in data/")
print("="*60)
print(f"1. ad_server_impressions.csv  : {len(ad_server_df):,} rows")
print(f"2. dsp_network_reports.csv    : {len(dsp_df):,} rows")
print(f"3. attribution_conversions.csv: {len(conversions_df):,} rows")

raw_gap = len(ad_server_df) - len(dsp_df)
gap_pct = (raw_gap / len(ad_server_df)) * 100
print(f"\nObserved Impression Discrepancy Rate: {gap_pct:.2f}% (Industry standard tolerance: < 2.0%)")
print("Ready for SQL reconciliation and root-cause queries.\n")
