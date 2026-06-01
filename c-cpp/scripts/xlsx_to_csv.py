#!/usr/bin/env python3
import argparse
import sys
import shutil
import re
from pathlib import Path
import pandas as pd

def safe(raw: str) -> str:
    """
    Make a filesystem-friendly name:
    - convert '-' to '_'
    - replace any non [A-Za-z0-9_.] with '_'
    - collapse consecutive underscores
    - strip leading/trailing underscores
    """
    s = raw.replace("-", "_")
    s = "".join(c if (c.isalnum() or c in {"_", "."}) else "_" for c in s)
    s = re.sub(r"_+", "_", s)
    return s.strip("_")

def convert_file(xlsx_path: Path, outdir: Path, sep: str = ",", na_rep: str = ""):
    try:
        xl = pd.ExcelFile(xlsx_path, engine="openpyxl")
    except Exception as e:
        print(f"[WARN] Skipping '{xlsx_path}': cannot open ({e})", file=sys.stderr)
        return

    wb_stem = safe(xlsx_path.stem)
    for sheet_name in xl.sheet_names:
        try:
            df = xl.parse(sheet_name=sheet_name)
            csv_name = f"{wb_stem}_{safe(sheet_name)}.csv"
            out_path = outdir / csv_name
            df.to_csv(out_path, index=False, sep=sep, na_rep=na_rep)
            print(f"[OK] {xlsx_path.name} :: '{sheet_name}' -> {out_path.name}")
        except Exception as e:
            print(f"[WARN]   Sheet '{sheet_name}' failed: {e}", file=sys.stderr)

def main():
    ap = argparse.ArgumentParser(
        description="Convert all .xlsx files in a directory to CSV (one CSV per sheet)."
    )
    ap.add_argument("indir", help="Directory containing .xlsx files")
    ap.add_argument("-o", "--outdir", default="csv_out",
                    help="Output directory (default: csv_out)")
    ap.add_argument("--sep", default=",",
                    help="CSV separator (default: ,)")
    ap.add_argument("--na", dest="na_rep", default="",
                    help="NA representation (default: empty string)")
    args = ap.parse_args()

    indir = Path(args.indir).expanduser().resolve()
    outdir = Path(args.outdir).expanduser().resolve()

    if not indir.exists() or not indir.is_dir():
        print(f"[ERROR] Input directory not found: {indir}", file=sys.stderr)
        sys.exit(1)

    # Overwrite: remove output directory if it exists, then recreate
    if outdir.exists():
        try:
            shutil.rmtree(outdir)
        except Exception as e:
            print(f"[ERROR] Cannot remove existing output directory '{outdir}': {e}",
                  file=sys.stderr)
            sys.exit(1)
    outdir.mkdir(parents=True, exist_ok=True)

    xlsx_files = sorted(indir.glob("*.xlsx"))
    if not xlsx_files:
        print(f"[INFO] No .xlsx files found in {indir}")
        return

    for x in xlsx_files:
        convert_file(x, outdir, sep=args.sep, na_rep=args.na_rep)

if __name__ == "__main__":
    main()
