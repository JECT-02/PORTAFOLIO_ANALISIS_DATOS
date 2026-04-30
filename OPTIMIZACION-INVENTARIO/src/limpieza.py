# Funciones de limpieza, imputación y feature engineering

# Funcion de limpieza para sale_price y unit_margin
import numpy as np
import pandas as pd


def impute_inventory_pricing(df, min_sales=5, cv_threshold=0.15):
    df = df.copy()

    sold_df = df[df["sale_price"].notna()].copy() #obtenemos solo los productos vendidos

    product_stats = (sold_df.groupby("product_id")["sale_price"]
        .agg(n_sales="count", mean_price="mean", median_price="median", std_price="std")
        .reset_index()
    )

    product_stats["cv"] = (product_stats["std_price"] / product_stats["mean_price"]).replace([np.inf, -np.inf], np.nan)

    category_stats = (sold_df.groupby("category")["sale_price"].median().rename("category_median_price").reset_index())

    df = df.merge(product_stats, on="product_id", how="left")
    df = df.merge(category_stats, on="category", how="left")

    df["estimated_sale_price"] = df["sale_price"]
    df["imputation_source"] = "REAL"

    stable_mask = (df["sale_price"].isna() & (df["n_sales"] >= min_sales) & (df["cv"] < cv_threshold))

    volatile_mask = (df["sale_price"].isna() & (df["n_sales"] >= min_sales) & (df["cv"] >= cv_threshold))

    fallback_mask = (df["sale_price"].isna() & (df["n_sales"].isna() | (df["n_sales"] < min_sales)))

    df.loc[stable_mask, "estimated_sale_price"] = df.loc[stable_mask, "mean_price"]
    df.loc[volatile_mask, "estimated_sale_price"] = df.loc[volatile_mask, "median_price"]
    df.loc[fallback_mask, "estimated_sale_price"] = df.loc[fallback_mask, "category_median_price"]

    df.loc[stable_mask, "imputation_source"] = "PRODUCT_MEAN"
    df.loc[volatile_mask, "imputation_source"] = "PRODUCT_MEDIAN"
    df.loc[fallback_mask, "imputation_source"] = "CATEGORY_MEDIAN"

    df["estimated_unit_margin"] = df["estimated_sale_price"] - df["cost"]

    drop_cols = [
    "n_sales",
    "mean_price",
    "median_price",
    "std_price",
    "cv",
    "category_median_price"
    ] # es importante eliminar las columnas que no se usaran mas alla de la imputacion

    df.drop(columns=drop_cols, inplace=True)

    return df