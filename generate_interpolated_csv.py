import pandas as pd
import numpy as np
import os

csv_path = r'C:/Users/paulo/Documents/GEOM_CSV_TEST/Survey_plan__Honeywell_oil_and_gas_limited.csv'
df = pd.read_csv(csv_path)
# Try to convert columns to float, drop rows with errors
try:
    x = pd.to_numeric(df.iloc[:,0], errors='coerce')
    y = pd.to_numeric(df.iloc[:,1], errors='coerce')
    valid = ~(x.isna() | y.isna())
    x = x[valid].values
    y = y[valid].values
except Exception as e:
    print('Error converting columns to float:', e)
    exit(1)
print('First few X:', x[:5])
print('First few Y:', y[:5])
n_points = 10
t = np.linspace(0, 1, len(x))
t_new = np.linspace(0, 1, n_points)
x_new = np.interp(t_new, t, x)
y_new = np.interp(t_new, t, y)
df_new = pd.DataFrame({'X': x_new, 'Y': y_new})
out_path = os.path.join(os.path.dirname(csv_path), 'Survey_plan__Honeywell_oil_and_gas_limited_10pts.csv')
print('Writing to:', out_path)
df_new.to_csv(out_path, index=False)
print('Done, file exists:', os.path.exists(out_path)) 