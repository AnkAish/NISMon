#!/usr/bin/env python3
import os
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
    Traverse subfolders of base_folder, read all CSVs,
    convert K/M/T suffix values, then add 'label' column:
      - if drop_pct(%) != 0 or fault == 1 → folder's mapped fault label
      - else → 'normal'
    Finally, concatenate into one DataFrame and clean numeric columns.
    """
    label_map = {
        'Fault_incast': 'incast',
        'Fault_mem_contention': 'memory_contention',
        'cpu_interference': 'cpu_interference'
    }
    all_dfs = []
    drop_col = 'drop_pct(%)'
    fault_col = 'fault'

    for folder in sorted(Path(base_folder).iterdir()):
        if not folder.is_dir() or folder.name not in label_map:
            continue
        folder_label = label_map[folder.name]

        for csv_path in sorted(folder.glob('*.csv')):
            df = pd.read_csv(csv_path)

            # 1) Parse K/M/T suffixes in object columns
            for col in df.select_dtypes(include='object').columns:
                sample = df[col].dropna().astype(str).head(5)
                if sample.str.contains(r"[\d\.]+[KMTkmt]$").any():
                    df[col] = df[col].apply(parse_size)

            # 2) Ensure drop_pct and fault numeric
            if drop_col in df.columns:
                df[drop_col] = pd.to_numeric(df[drop_col], errors='coerce').fillna(0)
            if fault_col in df.columns:
                df[fault_col] = pd.to_numeric(df[fault_col], errors='coerce').fillna(0).astype(int)

            # 3) Assign labels
            df['label'] = df.apply(
                lambda row: folder_label if (row.get(drop_col,0) != 0 or row.get(fault_col,0) == 1) else 'normal',
                axis=1
            )

            all_dfs.append(df)

    # Concatenate all
    if not all_dfs:
        return pd.DataFrame()
    df_all = pd.concat(all_dfs, ignore_index=True)

    # 4) Drop Timestamp & fault if present
    df_all = df_all.drop(columns=['Timestamp'], errors='ignore')
    df_all = df_all.drop(columns=['fault'], errors='ignore')

    # 5) Clean remaining object columns (except label) to numeric, drop invalid rows
    obj_cols = [c for c in df_all.select_dtypes(include='object').columns if c != 'label']
    for col in obj_cols:
        df_all[col] = pd.to_numeric(df_all[col], errors='coerce')
    df_all = df_all.dropna(subset=obj_cols)
    for col in obj_cols:
        df_all[col] = df_all[col].astype(int)

    return df_all


if __name__ == '__main__':
    # Use current directory as base
    BASE_FOLDER = Path.cwd()
    merged_df = concat_and_label(BASE_FOLDER)
    out_file = BASE_FOLDER / 'merged_labeled_periodic_fault_data.csv'
    merged_df.to_csv(out_file, index=False)
    print(f"Saved {len(merged_df)} rows to '{out_file.name}'")
