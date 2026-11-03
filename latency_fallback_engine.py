import time
import random
import json
import pandas as pd
import numpy as np

class LatencyCircuitBreaker:
    """
    Simulates ad tag auction execution and applies an 850ms client-side
    circuit breaker to prevent HTTP 408 gateway drops at >1000ms.
    """
    def __init__(self, timeout_threshold_ms: float = 850.0, drop_cliff_ms: float = 1000.0):
        self.timeout_threshold_ms = timeout_threshold_ms
        self.drop_cliff_ms = drop_cliff_ms

    def simulate_ad_request(self, partner: str, request_id: str) -> dict:
        # Latency distribution: DV360 skews heavily past 800ms due to DSP handshake
        if partner == "DV360":
            latency = np.random.normal(loc=920, scale=180)
        elif partner == "The Trade Desk":
            latency = np.random.normal(loc=550, scale=120)
        else:
            latency = np.random.normal(loc=650, scale=150)
            
        latency = max(50.0, round(float(latency), 2))

        # Scenario A: Control (No Fallback Tag - hard drop at >1000ms)
        control_dropped = latency > self.drop_cliff_ms
        control_status = "DROPPED (Unbilled)" if control_dropped else "RENDERED"

        # Scenario B: Treatment (850ms Circuit Breaker Fallback Active)
        if latency <= self.timeout_threshold_ms:
            treatment_status = "RENDERED (Partner DSP)"
            creative_source = "DSP Live Auction"
            loss_prevented = False
        else:
            # Tag preemptively executes fallback before 1000ms drop cliff
            treatment_status = "RENDERED (Cached Fallback)"
            creative_source = "Edge Cache / House Tag"
            loss_prevented = True if control_dropped else False

        return {
            "request_id": request_id,
            "partner": partner,
            "latency_ms": latency,
            "control_status": control_status,
            "treatment_status": treatment_status,
            "creative_source": creative_source,
            "timeout_prevented": loss_prevented
        }

    def run_simulation(self, total_requests: int = 5000) -> pd.DataFrame:
        partners = ["DV360", "The Trade Desk", "Amazon DSP", "Xandr"]
        results = []
        
        for i in range(total_requests):
            p = np.random.choice(partners, p=[0.40, 0.25, 0.20, 0.15])
            req_id = f"req_{i+1:05d}"
            results.append(self.simulate_ad_request(p, req_id))

        df = pd.DataFrame(results)
        return df

if __name__ == "__main__":
    breaker = LatencyCircuitBreaker(timeout_threshold_ms=850.0, drop_cliff_ms=1000.0)
    df_sim = breaker.run_simulation(total_requests=5000)

    # Calculate metrics
    control_drops = df_sim[df_sim['control_status'] == 'DROPPED (Unbilled)'].shape[0]
    control_drop_rate = round((control_drops / len(df_sim)) * 100, 2)

    treatment_drops = df_sim[df_sim['treatment_status'] == 'DROPPED (Unbilled)'].shape[0]
    treatment_drop_rate = round((treatment_drops / len(df_sim)) * 100, 2)

    saved_impressions = df_sim['timeout_prevented'].sum()

    print("\n================== LATENCY CIRCUIT BREAKER AUDIT ==================")
    print(f"Total Ad Requests Evaluated : {len(df_sim):,}")
    print(f"Control Drop Rate (>1000ms)  : {control_drop_rate}% ({control_drops:,} dropped)")
    print(f"Treatment Drop Rate (850ms)  : {treatment_drop_rate}% ({treatment_drops:,} dropped)")
    print(f"Saved Impressions via Cache  : {saved_impressions:,} impressions")
    print(f"Drop Rate Reduction          : {round(((control_drops - treatment_drops) / control_drops) * 100, 2)}%")

    # Partner breakdown
    partner_summary = df_sim.groupby('partner').agg(
        requests=('request_id', 'count'),
        avg_latency_ms=('latency_ms', 'mean'),
        unmitigated_drops=('control_status', lambda x: (x == 'DROPPED (Unbilled)').sum()),
        mitigated_rescues=('timeout_prevented', 'sum')
    ).reset_index()
    partner_summary['avg_latency_ms'] = partner_summary['avg_latency_ms'].round(2)
    partner_summary['unmitigated_drop_rate_pct'] = (
        (partner_summary['unmitigated_drops'] / partner_summary['requests']) * 100
    ).round(2)

    print("\n------------------ PARTNER LATENCY BREAKDOWN ------------------")
    print(partner_summary.to_string(index=False))

    df_sim.to_csv("latency_simulation_results.csv", index=False)
    print("\n[✓] Results saved to: latency_simulation_results.csv")
