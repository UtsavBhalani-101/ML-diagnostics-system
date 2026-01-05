import numpy as np
import pandas as pd

#& Helper function
def classify_non_numeric(df):
    n = len(df)
    non_num_cols = df.select_dtypes(exclude=["number"]).columns

    valid_categories = []

    for col in non_num_cols:
        s = df[col].dropna().astype(str)
        if s.empty:
            continue

        nunique = s.nunique()
        unique_ratio = nunique / n if n else 0

        avg_len = s.str.len().mean()
        max_len = s.str.len().max()
        space_ratio = s.str.contains(" ").mean()

        # Detect numeric-like object columns (dirty ingestion)
        numeric_ratio = pd.to_numeric(s, errors="coerce").notna().mean()

        # Reject ID-like columns
        if unique_ratio > 0.8 and nunique > max(50, 0.1 * n):
            continue

        # Reject free text
        if avg_len > 30 or max_len > 100 or space_ratio > 0.3:
            continue

        # Reject mixed numeric/string columns
        if 0 < numeric_ratio < 1:
            continue

        valid_categories.append(col)

    return valid_categories

#^ Memory Usage
def get_memory_usage(df: pd.DataFrame):
    """
    Calculate memory usage of the DataFrame.
    Uses deep=True to get accurate memory for object (string) types.
    Returns memory usage in MB.
    """
    usage_bytes = df.memory_usage(deep=True)
    total_mb = usage_bytes.sum() / (1024 ** 2)
    return round(total_mb, 4)

#^ Metadata 
def get_metadata(df):
    rows, cols = df.shape

    num_count = len(df.select_dtypes(include=["number"]).columns)
    valid_cat_count = len(classify_non_numeric(df))
    memory_mb = get_memory_usage(df)

    return {
        "Rows": rows,
        "Columns": cols,
        "Numerical Columns Ratio": num_count / cols if cols else 0,
        "Valid Categorical Columns Ratio": valid_cat_count / cols if cols else 0,
        "Feature to Row Ratio": cols / rows if rows else 0,
        "Memory (MB)": memory_mb
    }
   
#^ constant ratio  
def get_global_constant_ratio(df: pd.DataFrame):
    if df.empty:
        return 0.0

    max_ratio = 0.0

    for col in df.columns:
        s = df[col].dropna()
        if s.empty:
            continue

        ratio = s.value_counts(normalize=True).iloc[0]
        max_ratio = max(max_ratio, ratio)

    return round(max_ratio, 4)
    
    
#^ Health Signals
def get_health_signals(df: pd.DataFrame, target: pd.Series):
    rows, cols = df.shape

    missing_ratio = df.isnull().sum().sum() / df.size if df.size else 0.0
    constant_ratio = get_global_constant_ratio(df)
    duplicated_ratio = df.duplicated().mean() if rows else 0.0

    target_dist = target.value_counts(normalize=True)

    return {
        "missing_ratio": round(missing_ratio, 4),
        "constant_ratio": round(constant_ratio, 4),
        "duplicated_ratio": round(duplicated_ratio, 4),
    }

    
#^ Multicollinearity
def get_global_multicollinearity(df, threshold=0.8):
    num_df = df.select_dtypes(include=["number"])

    # Drop constant columns
    num_df = num_df.loc[:, num_df.nunique() > 1]

    if num_df.shape[1] < 2:
        return 0.0

    corr = num_df.corr().abs()
    upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))

    high_corr_pairs = (upper > threshold).sum().sum()
    total_pairs = (num_df.shape[1] * (num_df.shape[1] - 1)) / 2

    return round(high_corr_pairs / total_pairs, 4) if total_pairs else 0.0

#^ Cardinality
def get_global_cardinality(df, valid_cat_cols=None):
    if valid_cat_cols is None:
        valid_cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    if not valid_cat_cols:
        return 0.0

    n = len(df)
    ratios = [
        df[col].nunique(dropna=True) / n
        for col in valid_cat_cols
        if n > 0
    ]

    return round(sum(ratios) / len(ratios), 4) if ratios else 0.0

#^ Outliers
def get_global_outlier_ratio(df):
    num_df = df.select_dtypes(include=["number"])

    # Drop constant columns
    num_df = num_df.loc[:, num_df.nunique() > 1]

    if num_df.empty:
        return 0.0

    q1 = num_df.quantile(0.25)
    q3 = num_df.quantile(0.75)
    iqr = q3 - q1

    outlier_mask = (num_df < (q1 - 1.5 * iqr)) | (num_df > (q3 + 1.5 * iqr))

    return round(outlier_mask.any(axis=1).mean(), 4)

#^ Mixed type ratio
def get_global_mixed_type_ratio(df):
    cols = df.select_dtypes(include=["object", "category"]).columns
    if len(cols) == 0:
        return 0.0

    mixed_count = 0

    for col in cols:
        s = df[col].dropna()
        if s.empty:
            continue

        # Numeric coercion test
        coerced = pd.to_numeric(s, errors="coerce")
        numeric_ratio = coerced.notna().mean()

        # Mixed if partially numeric
        if 0 < numeric_ratio < 1:
            mixed_count += 1

    return round(mixed_count / df.shape[1], 4)

#^ Complexity Profile
def get_complexity_profile(df: pd.DataFrame):
    mlc = get_global_multicollinearity(df)
    cardinal = get_global_cardinality(df)
    outliers = get_global_outlier_ratio(df)
    mixed = get_global_mixed_type_ratio(df)
    
    return{
        "Multicollinearity":mlc,
        "Cardinality": cardinal,
        "Outliers": outliers,
        "Mixed": mixed
    }
    
def get_target_concentration_ratio(y: pd.Series):
    y = y.dropna()
    if y.empty:
        return 0.0

    dist = y.value_counts(normalize=True)
    return round(dist.max(), 4)

def get_target_profile(df:pd.DataFrame, target:pd.Series):
    if target.dtype == 'category':
        imbalance_ratio = target_dist.min() if len(target_dist) > 1 else 0.0
        return imbalance_ratio
    else:
        concentration = get_target_concentration_ratio(target)
        return concentration
    

    
        

def run_signals_extraction(df: pd.DataFrame, target:pd.Series):
    """
    The Orchestrator calls this function. 
    It passes the DataFrame, and this function distributes it to the helpers.
    """
    # Define a default target (pragmatic approach: use the last column)
    target = target
    features = df.drop(['SalePrice'], axis=1)

    final_result = {}
    final_result['Metadata'] = get_metadata(df)
    final_result['Health Check'] = get_health_signals(features, target)
    final_result['Complexity profile'] = get_complexity_profile(features)
    
    # Logic for target profile depends on data type
    final_result['Target Profile'] = get_target_profile(features, target)
    
    return final_result

if __name__ == "__main__":
    run_signals_extraction()