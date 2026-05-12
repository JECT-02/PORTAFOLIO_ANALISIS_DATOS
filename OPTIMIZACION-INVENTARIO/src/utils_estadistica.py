import pandas as pd
import numpy as np
from scipy import stats

def get_log_normal_categories(df, skew_limit=1.0, kurtosis_limit=2.0):
    normal_categories = []
    
    # Usamos apply para obtener skew y kurtosis de forma robusta
    stats_df = df.groupby("category")["log_cost"].apply(
        lambda x: pd.Series({
            "count": x.count(),
            "skew": x.skew(),
            "kurtosis": x.kurtosis()
        })
    ).unstack().dropna()
    
    for category, row in stats_df.iterrows():
        if row["count"] < 30:
            continue
            
        is_normal = (abs(row["skew"]) < skew_limit and 
                     abs(row["kurtosis"]) < kurtosis_limit)
        
        if is_normal:
            normal_categories.append(category)
            
    return normal_categories

def detect_outliers_zscore(df, value_col="log_cost", threshold=3):
    df = df.copy()
    
    z_scores = df.groupby("category")[value_col].transform(
        lambda x: (x - x.mean()) / x.std()
    )
    
    return df[abs(z_scores) > threshold]

def get_sigma_segmentation(df, value_col="log_cost"):
    def segment_group(x):
        m, s = x.mean(), x.std()
        
        bins = [-np.inf, m - s, m + s, m + 2*s, np.inf]
        labels = ["Bajo", "Medio", "Alto", "Premium"]
        
        return pd.cut(x, bins=bins, labels=labels)
    
    return df.groupby("category", group_keys=False)[value_col].apply(segment_group)
