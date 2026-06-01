#!/usr/bin/env python3
import argparse
from pathlib import Path
import sys
import pandas as pd

def read_csv_loose(path: Path) -> pd.DataFrame:
    with path.open('rb') as f:
        raw = f.read()
    txt = raw.decode('utf-8', errors='replace')
    txt = txt.replace('\r\n', '\n').replace('\r', '\n')
    from io import StringIO
    return pd.read_csv(StringIO(txt), engine='python')

def normalize_header(df: pd.DataFrame) -> pd.DataFrame:
    first_col = df.columns[0]
    if first_col != 'threads':
        df = df.rename(columns={first_col: 'threads'})
    new_cols = []
    for c in df.columns:
        if c == 'threads':
            new_cols.append(c)
        else:
            try:
                new_cols.append(int(str(c).strip()))
            except Exception:
                new_cols.append(c)
    df.columns = new_cols
    return df

def to_tidy(df: pd.DataFrame) -> pd.DataFrame:
    tidy = df.melt(id_vars=['threads'], var_name='init_size', value_name='value')
    tidy['threads'] = pd.to_numeric(tidy['threads'], errors='coerce')
    tidy['init_size'] = pd.to_numeric(tidy['init_size'], errors='coerce')
    tidy['value'] = pd.to_numeric(tidy['value'], errors='coerce')
    tidy = tidy.dropna(subset=['value'])
    tidy = tidy.sort_values(['threads', 'init_size'], kind='mergesort')
    return tidy

def process_directory(input_dir: Path, output_dir: Path, output_dir_seq: Path) -> None:
    # Refuse to run in-place
    if input_dir.resolve() == output_dir.resolve() or input_dir.resolve() == output_dir_seq.resolve():
        print("[ERROR] input_dir and output_dir must be different to protect originals.", file=sys.stderr)
        sys.exit(2)

    output_dir.mkdir(parents=True, exist_ok=True)
    output_dir_seq.mkdir(parents=True, exist_ok=True)
    any_written = False
    for path in sorted(input_dir.glob('*.csv')):
        if path.name.startswith('._'):
            continue
        try:
            df = read_csv_loose(path)
        except Exception as e:
            print(f"[WARN] Skipping {path.name}: failed to read ({e})")
            continue
        df = normalize_header(df)
        tidy = to_tidy(df)
        if path.name.startswith('table_sequential') or path.name.startswith('table_cache_sequential'):
            out_path = output_dir_seq / path.name  # keep original filename
        else:
            out_path = output_dir / path.name  # keep original filename
        tidy.to_csv(out_path, index=False)
        print(f"[OK] Wrote {out_path}")
        any_written = True
    if not any_written:
        print("[INFO] No CSV files processed.")

def main():
    ap = argparse.ArgumentParser(description="Convert wide CSVs into tidy CSVs (keeps filenames, prevents in-place overwrite).")
    ap.add_argument("input_dir", type=Path, help="Directory containing original CSV files")
    ap.add_argument("output_dir", type=Path, help="Directory to write tidy CSVs (e.g., tidy_tables/)")
    ap.add_argument("output_dir_seq", type=Path, help="Directory to write tidy CSVs for sequential results (e.g., seq_tidy_tables/)")
    args = ap.parse_args()
    process_directory(args.input_dir, args.output_dir, args.output_dir_seq)

if __name__ == "__main__":
    main()
