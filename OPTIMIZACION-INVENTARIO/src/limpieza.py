# Funciones de limpieza, imputación y feature engineering

# Funcion de limpieza para sale_price y unit_margin
import numpy as np
import pandas as pd

import numpy as np
import pandas as pd

def impute_inventory_pricing(df, min_sales=5, cv_threshold=0.15):
    df = df.copy()
    
    sold_df = df[df["sale_price"].notna()]
    
    product_stats = (sold_df.groupby("product_id")["sale_price"]
        .agg(n_sales="count", 
             mean_price="mean", 
             median_price="median", 
             std_price="std")
        .reset_index()
    )
    
    product_stats["cv"] = (product_stats["std_price"] / product_stats["mean_price"]).replace([np.inf, -np.inf], np.nan)
    
    category_stats = sold_df.groupby("category")["sale_price"].median().rename("category_median_price")
    
    df = df.merge(product_stats, on="product_id", how="left")
    df = df.merge(category_stats, on="category", how="left")
    
    df["estimated_sale_price"] = df["sale_price"]
    df["imputation_source"] = "REAL"
    
    mask_na = df["sale_price"].isna()
    mask_has_stats = (df["n_sales"] >= min_sales)
    
    stable_mask = mask_na & mask_has_stats & (df["cv"] < cv_threshold)
    volatile_mask = mask_na & mask_has_stats & (df["cv"] >= cv_threshold)
    fallback_mask = mask_na & (~mask_has_stats | df["n_sales"].isna())
    
    df.loc[stable_mask, "estimated_sale_price"] = df.loc[stable_mask, "median_price"]
    df.loc[volatile_mask, "estimated_sale_price"] = df.loc[volatile_mask, "median_price"]
    df.loc[fallback_mask, "estimated_sale_price"] = df.loc[fallback_mask, "category_median_price"]
    
    df.loc[stable_mask, "imputation_source"] = "PRODUCT_STABLE_MEDIAN"
    df.loc[volatile_mask, "imputation_source"] = "PRODUCT_VOLATILE_MEDIAN"
    df.loc[fallback_mask, "imputation_source"] = "CATEGORY_MEDIAN"
    
    df["estimated_unit_margin"] = df["estimated_sale_price"] - df["cost"]
    
    drop_cols = ["n_sales", "mean_price", "median_price", "std_price", "cv", "category_median_price"]
    df.drop(columns=drop_cols, inplace=True)
    
    return df

def detect_inventory_age_outlier_categories(df):
    outlier_categories = []

    for category, group in df.groupby("category"):
        q1 = group["days_in_inventory"].quantile(0.25)
        q3 = group["days_in_inventory"].quantile(0.75)
        iqr = q3 - q1

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        if ((group["days_in_inventory"] < lower_bound) | 
            (group["days_in_inventory"] > upper_bound)).any():
            outlier_categories.append(category)

    return outlier_categories



def detect_inventory_cost_outlier_categories(df):
    outlier_categories = []

    for category, group in df.groupby("category"):
        q1 = group["cost"].quantile(0.25)
        q3 = group["cost"].quantile(0.75)
        iqr = q3 - q1

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        if ((group["cost"] < lower_bound) | 
            (group["cost"] > upper_bound)).any():
            outlier_categories.append(category)

    return outlier_categories

def detect_inventory_cost_outlier_categories(df, value_col="log_cost",outlier_threshold=0.05):
    results = []

    for category, group in df.groupby("category"):

        q1 = group[value_col].quantile(0.25)
        q3 = group[value_col].quantile(0.75)

        iqr = q3 - q1

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        outliers = group[
            (group[value_col] < lower_bound) |
            (group[value_col] > upper_bound)
        ]

        outlier_rate = len(outliers) / len(group)

        results.append({
            "category": category,
            "n_records": len(group),
            "n_outliers": len(outliers),
            "outlier_rate": outlier_rate,
            "has_high_outliers": outlier_rate > outlier_threshold
        })

    return pd.DataFrame(results).sort_values(
        "outlier_rate",
        ascending=False
    )