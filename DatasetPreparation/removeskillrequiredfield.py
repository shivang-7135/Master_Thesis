import pandas as pd

def drop_unused_column(df, column_name="skills_required", verbose=True):
    """
    Safely drops an unused column from a DataFrame if it exists.
    
    Parameters
    ----------
    df : pandas.DataFrame
        Input DataFrame.
    column_name : str, optional
        Column name to drop (default: 'skills_required').
    verbose : bool, optional
        Whether to print a message about the operation.
    
    Returns
    -------
    pandas.DataFrame
        Cleaned DataFrame (copy, not modified in place).
    """
    df = df.copy()
    if column_name in df.columns:
        df = df.drop(columns=[column_name])
        if verbose:
            print(f"🧹 Dropped unused column: '{column_name}'")
    else:
        if verbose:
            print(f"ℹ️ Column '{column_name}' not found — nothing to drop.")
    return df

# Example load
df = pd.read_csv("data/processed/jobs_with_skills_combined.csv")

# Drop 'skills_required' safely
df = drop_unused_column(df, "skills_required")

df.to_csv("data/processed/jobs_with_skills_combined.csv", index=False)

print(f"✅ Saved enriched file: data/processed/jobs_with_skills_combined.csv")
print(df.head())