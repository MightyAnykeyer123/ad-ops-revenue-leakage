import pandas as pd
import numpy as np

np.random.seed(42)

partners = ['DV360', 'The Trade Desk', 'Amazon DSP', 'Xandr']
placements = ['PL-3001', 'PL-3002', 'PL-3003', 'PL-3004']
cpms = {'DV360': 3.50, 'The Trade Desk': 4.20, 'Amazon DSP': 2.80, 'Xandr': 2.80}

records = []
for i in range(10000):
    p = np.random.choice(partners)
    pl = np.random.choice(placements)
    records.append({
        'impression_id': f'imp_{i+1:06d}',
        'partner_name': p,
        'placement_id': pl,
        'cpm': cpms[p]
    })

df_srv = pd.DataFrame(records)
df_srv.to_csv('ad_server_impressions.csv', index=False)

billed = []
for idx, row in df_srv.iterrows():
    # DV360 drops ~7.5%, others drop ~1.5%
    drop_p = 0.075 if row['partner_name'] == 'DV360' else 0.015
    if np.random.rand() > drop_p:
        billed.append(row.to_dict())

df_dsp = pd.DataFrame(billed)
df_dsp.to_csv('dsp_billing_logs.csv', index=False)

print("[✓] Both ad_server_impressions.csv and dsp_billing_logs.csv created successfully!")
