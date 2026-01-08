import numpy as np
import pandas as pd

#& Helper function - root node decider
def find_dtype(df: pd.DataFrame):
    """
    First identify the dtype of cols
    Group them based on dtype = num, category, mixed, identifier-like, text-like, datetime    
    
    Returns:
        tuple: (numeric_cols, categorical_cols, mixed_cols, identifier_cols, text_cols, datetime_cols)
    """
    numeric_cols = []
    categorical_cols = []
    mixed_cols = []
    identifier_cols = []
    text_cols = []
    datetime_cols = []
    
    # 1. Numeric columns
    numeric_cols = list(df.select_dtypes(include='number').columns)
    
    # 2. Datetime columns (datetime64, timedelta64)
    datetime_cols = list(df.select_dtypes(include=['datetime64', 'timedelta64', 'datetime', 'timedelta']).columns)
    
    # Get non-numeric and non-datetime columns for further classification
    non_numeric_cols = df.select_dtypes(exclude=['number', 'datetime64', 'timedelta64', 'datetime', 'timedelta']).columns
    
    for col in non_numeric_cols:
        col_data = df[col]
        n_rows = len(col_data)
        n_unique = col_data.nunique()
        
        # Check for mixed types (contains multiple Python types)
        non_null_data = col_data.dropna()
        if len(non_null_data) > 0:
            types_in_col = set(type(x).__name__ for x in non_null_data)
            is_mixed = len(types_in_col) > 1
        else:
            is_mixed = False
        
        # Check if column might be datetime based on name patterns
        datetime_keywords = ['date', 'time', 'timestamp', 'datetime', 'created', 'updated', 
                             'modified', 'dt', 'dob', 'birth', 'year', 'month', 'day', 
                             'hour', 'minute', 'second', 'period', 'start', 'end']
        col_lower = col.lower()
        is_datetime_name = any(keyword in col_lower for keyword in datetime_keywords)
        
        # Try to parse as datetime if name suggests it
        if is_datetime_name and not is_mixed:
            try:
                pd.to_datetime(non_null_data, errors='raise', infer_datetime_format=True)
                datetime_cols.append(col)
                continue  # Skip to next column
            except (ValueError, TypeError):
                pass  # Not a valid datetime, continue with other checks
        
        if is_mixed:
            # 3. Mixed columns - contain multiple data types
            mixed_cols.append(col)
            
        elif col_data.dtype == 'object' or str(col_data.dtype) == 'category' or str(col_data.dtype).startswith('string'):
            # Calculate uniqueness ratio
            uniqueness_ratio = n_unique / n_rows if n_rows > 0 else 0
            
            # Calculate average string length (for text detection)
            avg_length = non_null_data.astype(str).str.len().mean() if len(non_null_data) > 0 else 0
            
            # 4. Identifier-like columns
            # Heuristics: high uniqueness (>90%), or column name contains 'id'
            is_identifier = (
                uniqueness_ratio > 0.9 or 
                'id' in col.lower() or
                col.lower().endswith('_id') or
                col.lower() == 'index'
            )
            
            if is_identifier and uniqueness_ratio > 0.5:
                identifier_cols.append(col)
                
            # 5. Text-like columns
            # Heuristics: high cardinality AND longer average text length
            elif uniqueness_ratio > 0.5 and avg_length > 20:
                text_cols.append(col)
                
            # 6. Categorical columns
            # Heuristics: low cardinality (few unique values relative to total rows)
            else:
                categorical_cols.append(col)
    
    return numeric_cols, categorical_cols, mixed_cols, identifier_cols, text_cols, datetime_cols
    

if __name__ == "__main__":
    data = pd.read_csv(r'D:\ML diagnose v1\tests\snapshot_normalized.csv')
    numeric_cols, categorical_cols, mixed_cols, identifier_cols, text_cols, datetime_cols = find_dtype(data)
    
    print("=" * 50)
    print("COLUMN GROUPING RESULTS")
    print("=" * 50)
    print(f"\nNUMERIC ({len(numeric_cols)} columns):\n  {numeric_cols}")
    print(f"\nCATEGORICAL ({len(categorical_cols)} columns):\n  {categorical_cols}")
    print(f"\nMIXED ({len(mixed_cols)} columns):\n  {mixed_cols}")
    print(f"\nIDENTIFIER ({len(identifier_cols)} columns):\n  {identifier_cols}")
    print(f"\nTEXT ({len(text_cols)} columns):\n  {text_cols}")
    print(f"\nDATETIME ({len(datetime_cols)} columns):\n  {datetime_cols}")
    
    
