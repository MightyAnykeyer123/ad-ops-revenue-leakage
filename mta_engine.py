import os
import pandas as pd
import numpy as np

class MultiTouchAttribution:
    def __init__(self, data_path: str = "conversion_journeys.csv"):
        self.data_path = data_path
        self.df = None
        self.attributed_df = None

    def load_or_generate_data(self):
        """Loads journey data or synthesizes multi-touch paths if file does not exist."""
        if os.path.exists(self.data_path):
            self.df = pd.read_csv(self.data_path)
            self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
        else:
            print("[!] Synthesizing multi-touch conversion journey dataset...")
            np.random.seed(42)
            channels = ['Programmatic Display', 'Paid Search', 'Paid Social', 'Video (DV360)', 'Direct/Organic']
            
            records = []
            for user_id in range(1001, 1501):
                # Journey path length between 1 and 6 touchpoints
                path_len = np.random.choice([1, 2, 3, 4, 5, 6], p=[0.15, 0.25, 0.30, 0.15, 0.10, 0.05])
                conv_value = round(float(np.random.uniform(25.0, 250.0)), 2)
                base_time = pd.Timestamp("2026-10-01 08:00:00") + pd.Timedelta(hours=int(np.random.randint(1, 500)))

                for step in range(path_len):
                    touch_time = base_time + pd.Timedelta(hours=step * int(np.random.randint(4, 24)))
                    # Prospecting channels skew earlier; Search/Direct skew later
                    if step == 0 and path_len > 1:
                        ch = np.random.choice(['Programmatic Display', 'Video (DV360)', 'Paid Social'])
                    elif step == path_len - 1 and path_len > 1:
                        ch = np.random.choice(['Paid Search', 'Direct/Organic', 'Paid Social'])
                    else:
                        ch = np.random.choice(channels)
                        
                    records.append({
                        "user_id": f"USR_{user_id}",
                        "touchpoint_order": step + 1,
                        "path_length": path_len,
                        "channel": ch,
                        "timestamp": touch_time,
                        "conversion_value": conv_value
                    })

            self.df = pd.DataFrame(records)
            self.df.to_csv(self.data_path, index=False)
            print(f"[+] Generated {len(self.df)} touchpoints across 500 conversion journeys.")

    def calculate_position_based_credit(self) -> pd.DataFrame:
        """Applies 40/40/20 position-based attribution logic across user paths."""
        if self.df is None:
            self.load_or_generate_data()

        df = self.df.sort_values(by=['user_id', 'touchpoint_order']).copy()

        def assign_weight(row):
            n = row['path_length']
            step = row['touchpoint_order']

            if n == 1:
                return 1.0
            elif n == 2:
                return 0.50
            else:
                # n >= 3
                if step == 1:
                    return 0.40  # First touch
                elif step == n:
                    return 0.40  # Last touch
                else:
                    return 0.20 / (n - 2)  # Middle touchpoints split 20% evenly

        df['mta_weight'] = df.apply(assign_weight, axis=1)
        df['attributed_revenue_mta'] = np.round(df['conversion_value'] * df['mta_weight'], 2)

        # Baseline comparisons: First-Touch and Last-Touch
        df['first_touch_weight'] = np.where(df['touchpoint_order'] == 1, 1.0, 0.0)
        df['attributed_revenue_ft'] = np.round(df['conversion_value'] * df['first_touch_weight'], 2)

        df['last_touch_weight'] = np.where(df['touchpoint_order'] == df['path_length'], 1.0, 0.0)
        df['attributed_revenue_lt'] = np.round(df['conversion_value'] * df['last_touch_weight'], 2)

        self.attributed_df = df
        return self.attributed_df

    def channel_comparison_summary(self) -> pd.DataFrame:
        """Aggregates revenue and credit variance across attribution models."""
        if self.attributed_df is None:
            self.calculate_position_based_credit()

        summary = self.attributed_df.groupby('channel').agg(
            total_touchpoints=('user_id', 'count'),
            first_touch_rev=('attributed_revenue_ft', 'sum'),
            last_touch_rev=('attributed_revenue_lt', 'sum'),
            position_based_rev=('attributed_revenue_mta', 'sum')
        ).reset_index()

        summary['mta_vs_last_touch_delta_pct'] = np.round(
            ((summary['position_based_rev'] - summary['last_touch_rev']) / summary['last_touch_rev']) * 100, 2
        )

        return summary.sort_values(by='position_based_rev', ascending=False)

if __name__ == "__main__":
    mta = MultiTouchAttribution()
    attributed_raw = mta.calculate_position_based_credit()
    summary = mta.channel_comparison_summary()

    print("\n================== CHANNEL ATTRIBUTION COMPARISON ==================")
    print(summary.to_string(index=False))

    # Export clean summary
    summary.to_csv("mta_attribution_summary.csv", index=False)
    print("\n[✓] Attribution report written to: mta_attribution_summary.csv")
