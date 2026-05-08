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
