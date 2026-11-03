import json
import pandas as pd
import numpy as np

class DiscrepancyEvaluator:
    def __init__(self, server_path="ad_server_impressions.csv", partner_path="dsp_billing_logs.csv", sla_threshold_pct=2.0):
        self.server_path = server_path
        self.partner_path = partner_path
        self.sla_threshold_pct = sla_threshold_pct
        self.df_server = None
        self.df_partner = None

    def load_data(self):
        self.df_server = pd.read_csv(self.server_path)
        self.df_partner = pd.read_csv(self.partner_path)

        # Normalize ID column if needed
        if "billed_impression_id" not in self.df_partner.columns and "impression_id" in self.df_partner.columns:
            self.df_partner = self.df_partner.rename(columns={"impression_id": "billed_impression_id"})
        if "billed_impression_id" not in self.df_partner.columns:
            self.df_partner["billed_impression_id"] = self.df_partner.iloc[:, 0]

    def evaluate(self):
        self.load_data()

        server_agg = self.df_server.groupby(['partner_name', 'placement_id']).agg(
            server_impressions=('impression_id', 'count'),
            contract_cpm=('cpm', 'mean')
        ).reset_index()

        partner_agg = self.df_partner.groupby(['partner_name', 'placement_id']).agg(
            billed_impressions=('billed_impression_id', 'count')
        ).reset_index()

        recon = pd.merge(server_agg, partner_agg, on=['partner_name', 'placement_id'], how='left').fillna(0)
        recon['billed_impressions'] = recon['billed_impressions'].astype(int)

        recon['unbilled_impressions'] = recon['server_impressions'] - recon['billed_impressions']
        recon['discrepancy_rate_pct'] = np.round(
            (recon['unbilled_impressions'] / recon['server_impressions']) * 100, 2
        )
        recon['unbilled_loss_usd'] = np.round(
            (recon['unbilled_impressions'] / 1000.0) * recon['contract_cpm'], 2
        )
        recon['sla_breached'] = recon['discrepancy_rate_pct'] > self.sla_threshold_pct

        # Build Sev-2 alert payload
        breaches = recon[recon['sla_breached']].copy()
        alert_payload = {
            "timestamp": pd.Timestamp.utcnow().isoformat() + "Z",
            "audit_metric": f"Ad-Ops {self.sla_threshold_pct}% MSA SLA Discrepancy Evaluation",
            "overall_summary": {
                "server_impressions": int(recon['server_impressions'].sum()),
                "billed_impressions": int(recon['billed_impressions'].sum()),
                "discrepancy_rate_pct": float(round(((recon['server_impressions'].sum() - recon['billed_impressions'].sum()) / recon['server_impressions'].sum()) * 100, 2)),
                "net_revenue_leakage_usd": float(round(recon['unbilled_loss_usd'].sum(), 2)),
                "sla_breach_count": int(breaches.shape[0])
            },
            "breached_line_items": [
                {
                    "partner": row['partner_name'],
                    "placement_id": row['placement_id'],
                    "server_impressions": int(row['server_impressions']),
                    "billed_impressions": int(row['billed_impressions']),
                    "discrepancy_rate_pct": float(row['discrepancy_rate_pct']),
                    "contract_cpm": float(row['contract_cpm']),
                    "unbilled_loss_usd": float(row['unbilled_loss_usd']),
                    "recommended_action": "Issue formal partner credit dispute memo"
                }
                for _, row in breaches.iterrows()
            ]
        }

        with open("sla_breach_alert_payload.json", "w") as f:
            json.dump(alert_payload, f, indent=2)

        return recon

if __name__ == "__main__":
    evaluator = DiscrepancyEvaluator()
    recon_df = evaluator.evaluate()

    print("\n================== 2.0% MSA SLA RECONCILIATION AUDIT ==================")
    print(recon_df[['partner_name', 'placement_id', 'server_impressions', 'billed_impressions', 'discrepancy_rate_pct', 'sla_breached', 'unbilled_loss_usd']].to_string(index=False))

    breaches = recon_df[recon_df['sla_breached']]
    print(f"\n[!] Breaches detected (> 2.0% SLA threshold): {len(breaches)} placement(s) flagged.")
    print("[✓] Webhook dispute payload saved to: sla_breach_alert_payload.json")
