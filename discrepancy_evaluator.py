import json
import os
import pandas as pd
import numpy as np
from datetime import datetime

class DiscrepancyEvaluator:
    def __init__(self, server_logs_path: str, partner_logs_path: str, sla_threshold: float = 2.0):
        self.server_logs_path = server_logs_path
        self.partner_logs_path = partner_logs_path
        self.sla_threshold = sla_threshold
        self.df_server = None
        self.df_partner = None
        self.reconciliation_df = None

    def load_data(self):
        """Loads and normalizes ad server and DSP partner logs."""
        if not os.path.exists(self.server_logs_path) or not os.path.exists(self.partner_logs_path):
            raise FileNotFoundError("Input log files not found.")
        
        self.df_server = pd.read_csv(self.server_logs_path)
        self.df_partner = pd.read_csv(self.partner_logs_path)
        
        # Standardize column naming
        self.df_server.columns = [c.strip().lower() for c in self.df_server.columns]
        self.df_partner.columns = [c.strip().lower() for c in self.df_partner.columns]

    def evaluate(self) -> pd.DataFrame:
        """Executes matching, SLA evaluation, and financial leakage calculation."""
        if self.df_server is None or self.df_partner is None:
            self.load_data()

        # Aggregate server logs
        server_agg = self.df_server.groupby(['partner_name', 'placement_id', 'cpm']).agg(
            server_impressions=('impression_id', 'count')
        ).reset_index()

        # Aggregate partner logs (billed)
        partner_agg = self.df_partner.groupby(['partner_name', 'placement_id']).agg(
            billed_impressions=('billed_impression_id', 'count')
        ).reset_index()

        # Outer join to capture discrepancies and unbilled volume
        merged = pd.merge(server_agg, partner_agg, on=['partner_name', 'placement_id'], how='left')
        merged['billed_impressions'] = merged['billed_impressions'].fillna(0).astype(int)

        # Discrepancy metrics
        merged['unbilled_impressions'] = merged['server_impressions'] - merged['billed_impressions']
        merged['discrepancy_rate_pct'] = np.round(
            (merged['unbilled_impressions'] / merged['server_impressions']) * 100, 2
        )
        
        # Contractual financial leakage = (Unbilled Impressions / 1,000) * Contracted CPM
        merged['revenue_leakage_usd'] = np.round(
            (merged['unbilled_impressions'] / 1000.0) * merged['cpm'], 2
        )

        # SLA Compliance Status
        merged['sla_breach'] = merged['discrepancy_rate_pct'] > self.sla_threshold
        merged['status'] = np.where(merged['sla_breach'], 'BREACH (Sev-2)', 'COMPLIANT')

        self.reconciliation_df = merged
        return self.reconciliation_df

    def generate_incident_payload(self) -> dict:
        """Generates a structured incident JSON payload for breached partners."""
        if self.reconciliation_df is None:
            self.evaluate()

        breaches = self.reconciliation_df[self.reconciliation_df['sla_breach']]
        total_server = int(self.reconciliation_df['server_impressions'].sum())
        total_billed = int(self.reconciliation_df['billed_impressions'].sum())
        total_lost_revenue = float(self.reconciliation_df['revenue_leakage_usd'].sum())
        overall_discrepancy = round(((total_server - total_billed) / total_server) * 100, 2) if total_server else 0.0

        payload = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "audit_metric": "Ad-Ops 2.0% MSA SLA Discrepancy Evaluation",
            "overall_summary": {
                "server_impressions": total_server,
                "billed_impressions": total_billed,
                "discrepancy_rate_pct": overall_discrepancy,
                "net_revenue_leakage_usd": total_lost_revenue,
                "sla_breach_count": int(breaches.shape[0])
            },
            "breached_line_items": []
        }

        for _, row in breaches.iterrows():
            payload["breached_line_items"].append({
                "partner": row['partner_name'],
                "placement_id": row['placement_id'],
                "server_impressions": int(row['server_impressions']),
                "billed_impressions": int(row['billed_impressions']),
                "discrepancy_rate_pct": float(row['discrepancy_rate_pct']),
                "contract_cpm": float(row['cpm']),
                "unbilled_loss_usd": float(row['revenue_leakage_usd']),
                "recommended_action": "Issue formal partner credit dispute memo"
            })

        return payload

if __name__ == "__main__":
    server_path = "ad_server_impressions.csv"
    partner_path = "dsp_billing_logs.csv"

    evaluator = DiscrepancyEvaluator(server_path, partner_path, sla_threshold=2.0)
    results = evaluator.evaluate()
    
    print("\n======================= RECONCILIATION AUDIT SUMMARY =======================")
    print(results.to_string(index=False))
    
    payload = evaluator.generate_incident_payload()
    with open("sla_breach_alert_payload.json", "w") as f:
        json.dump(payload, f, indent=2)

    print("\n[✓] Incident payload written to: sla_breach_alert_payload.json")
    print(f"[✓] Total Breaches Detected: {payload['overall_summary']['sla_breach_count']}")
    print(f"[✓] Net Revenue at Risk: ${payload['overall_summary']['net_revenue_leakage_usd']:,.2f}")
