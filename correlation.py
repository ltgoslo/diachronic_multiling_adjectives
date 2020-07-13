# /bin/env/ python3
# coding: utf-8

from scipy.stats import pearsonr
import pandas as pd
import sys

df1 = pd.read_csv(sys.argv[1])
df2 = pd.read_csv(sys.argv[2])
df = pd.concat([df1, df2])

print(f"Correlation frequency-mean_dist_jaccard: "
      f"{pearsonr(df['frequency'], df['mean_dist_jaccard'])}")
print(f"Correlation frequency-mean_deltas_jaccard: "
      f"{pearsonr(df['frequency'], df['sum_deltas_jaccard'])}")
print(f"Correlation frequency-mean_dist_globalanchors: "
      f"{pearsonr(df['frequency'], df['mean_dist_globalanchors'])}")
print(f"Correlation frequency-mean_deltas_globalanchors: "
      f"{pearsonr(df['frequency'], df['sum_deltas_globalanchors'])}")
print(f"Correlation frequency-mean_dist_procrustes: "
      f"{pearsonr(df['frequency'], df['mean_dist_procrustes'])}")
print(f"Correlation frequency-mean_deltas_procrustes: "
      f"{pearsonr(df['frequency'], df['sum_deltas_procrustes'])}")
