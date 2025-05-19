#!/usr/bin/env python3
import os
import re
import pandas as pd

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

def concat_csvs_with_folder_labels(base_folder):
    """
    Traverse subfolders of base_folder, read all CSVs,
    add 'label' column = folder name, convert K/M/T suffix values,
    and concatenate into one DataFrame.
    """
    all_dfs = []
    for folder_name in sorted(os.listdir(base_folder)):
        folder_path = os.path.join(base_folder, folder_name)
        if not os.path.isdir(folder_path):
            continue
        label = folder_name
        for fname in sorted(os.listdir(folder_path)):
            if not fname.lower().endswith('.csv'):
                continue
            df = pd.read_csv(os.path.join(folder_path, fname))
            df['label'] = label
            # Convert any object columns containing K/M/T suffixes
            for col in df.columns:
                if df[col].dtype == object:
                    sample = df[col].dropna().astype(str).head(5)
                    if any(re.search(r'[\d\.]+[KMTkmt]$', v) for v in sample):
                        df[col] = df[col].apply(parse_size)
            all_dfs.append(df)
    if not all_dfs:
        return pd.DataFrame()
    return pd.concat(all_dfs, ignore_index=True)

if __name__ == '__main__':
    BASE_FOLDER = './'  # parent directory of your folders where CSV files are stored for all the cases (normal, incast, memory contention, and CPU interference)
    df_all = concat_csvs_with_folder_labels(BASE_FOLDER)
    df_all.to_csv('merged_labeled_data.csv', index=False)
    print(f"Concatenated {len(df_all)} rows into 'merged_labeled_data.csv'")
