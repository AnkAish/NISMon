#!/usr/bin/env python3
import re
import pandas as pd
from pathlib import Path

def parse_size(value):
    """
    Convert strings like '32K', '33M', '1T' to integer values:
      K → *1_000
      M → *1_000_000
      T → *1_000_000_000_000
    Leaves other values unchanged.
    """
    if pd.isna(value):
        return value
    if isinstance(value, (int, float)):
        return int(value)
    s = str(value).strip()
    match = re.match(r'^([\d\.]+)\s*([KMT])$', s, re.IGNORECASE)
    if not match:
        return value
    num, suffix = match.groups()
    num = float(num)
    suffix = suffix.upper()
    if suffix == 'K':
        num *= 1_000
    elif suffix == 'M':
        num *= 1_000_000
    elif suffix == 'T':
        num *= 1_000_000_000_000
    return int(num)

def concat_and_label(base_folder):
    """
    Read all CSVs directly under base_folder, convert K/M/T suffix values,
    and assign a string 'label' column based on the integer in the existing 'fault' column:
      0 = 'normal'
      1 = 'incast'
      2 = 'memory_contention'
      3 = 'cpu_interference'

    If drop_pct(%) != 0 but fault == 0, assign the label from the nearest non-zero
    fault code in the same CSV (previous or next row). Finally, concatenate
    all files into one cleaned DataFrame.
    """
    all_dfs = []
    fault_col = 'fault'
    drop_col = 'drop_pct(%)'

    # Mapping from fault code to label string
    code_to_label = {
        0: 'normal',
        1: 'incast',
        2: 'memory_contention',
        3: 'cpu_interference'
    }

    for csv_path in sorted(Path(base_folder).glob('*.csv')):
        df = pd.read_csv(csv_path)

        # 1) Parse K/M/T suffixes in object columns
        for col in df.select_dtypes(include='object').columns:
            sample = df[col].dropna().astype(str).head(5)
            if sample.str.contains(r"[\d\.]+[KMTkmt]$").any():
                df[col] = df[col].apply(parse_size)

        # 2) Ensure 'fault' and 'drop_pct(%)' numeric; fill missing columns
        if fault_col in df.columns:
            df[fault_col] = pd.to_numeric(df[fault_col], errors='coerce').fillna(0).astype(int)
        else:
            df[fault_col] = pd.Series(0, index=df.index, dtype=int)

        if drop_col in df.columns:
            df[drop_col] = pd.to_numeric(df[drop_col], errors='coerce').fillna(0)
        else:
            df[drop_col] = pd.Series(0.0, index=df.index)

        # 3) For rows where fault == 0 and drop_pct != 0,
        #    assign from nearest non-zero fault in that CSV.
        fault_nonzero = df[fault_col].replace(0, pd.NA)
        fwd = fault_nonzero.ffill()
        bwd = fault_nonzero.bfill()
        nearest = fwd.where(fwd.notna(), bwd)

        def resolve_label_code(idx, row):
            orig = row[fault_col]
            if orig != 0:
                return orig
            if row[drop_col] != 0 and pd.notna(nearest.iloc[idx]):
                return int(nearest.iloc[idx])
            return 0

        df['resolved_code'] = [
            resolve_label_code(i, r) for i, r in df.iterrows()
        ]

        # 4) Map resolved codes to label strings
        df['label'] = df['resolved_code'].map(code_to_label).fillna('normal')

        all_dfs.append(df)

    # Concatenate all DataFrames
    if not all_dfs:
        return pd.DataFrame()
    df_all = pd.concat(all_dfs, ignore_index=True)

    # 5) Drop 'Timestamp', original 'fault', and 'resolved_code' columns
    df_all = df_all.drop(columns=['Timestamp'], errors='ignore')
    df_all = df_all.drop(columns=[fault_col, 'resolved_code'], errors='ignore')

    # 6) Coerce remaining object-type columns (except 'label') to numeric; drop invalid rows
    obj_cols = [c for c in df_all.select_dtypes(include='object').columns if c != 'label']
    for col in obj_cols:
        df_all[col] = pd.to_numeric(df_all[col], errors='coerce')
    df_all = df_all.dropna(subset=obj_cols)
    for col in obj_cols:
        df_all[col] = df_all[col].astype(int)

    return df_all

if __name__ == '__main__':
    BASE_FOLDER = Path.cwd()
    merged_df = concat_and_label(BASE_FOLDER)
    out_file = BASE_FOLDER / 'dataset_testing.csv'
    merged_df.to_csv(out_file, index=False)
    print(f"Saved {len(merged_df)} rows to '{out_file.name}'")
