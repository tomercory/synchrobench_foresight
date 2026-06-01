#!/usr/bin/env bash
set -euo pipefail

# This script runs tidy.py to produce tidy tables and then uses them as input to plot_graphs.py.

ROOT_DIR=".."
RAW_DIR="$ROOT_DIR/results"
TIDY_DIR="$ROOT_DIR/tidy_tables"
TIDY_DIR_SEQ="$ROOT_DIR/seq_tidy_tables"
RAW_CACHE_DIR="$ROOT_DIR/raw_cache_tables"
TIDY_CACHE_DIR="$ROOT_DIR/tidy_cache_tables"
TIDY_CACHE_DIR_SEQ="$ROOT_DIR/seq_tidy_cache_tables"
GRAPHS_DIR="$ROOT_DIR/graphs"
GRAPHS_DIR_SEQ="$ROOT_DIR/seq_graphs"

if [[ ! -d "$RAW_DIR" ]]; then
  echo "ERROR: raw_tables directory not found at $RAW_DIR" >&2
  exit 1
fi

echo "[1/5] Running raw_tables_to_tidy.py on: $RAW_DIR -> $TIDY_DIR, $TIDY_DIR_SEQ" >&2
# Ensure tidy output does not contain leftovers from previous runs
if [[ -d "$TIDY_DIR" ]]; then
  rm -rf "$TIDY_DIR"
fi
if [[ -d "$TIDY_DIR_SEQ" ]]; then
  rm -rf "$TIDY_DIR_SEQ"
fi
# raw_tables_to_tidy.py expects positional args: input_dir output_dir
python3 raw_tables_to_tidy.py "$RAW_DIR" "$TIDY_DIR" "$TIDY_DIR_SEQ"

echo "[2/5] Converting cache XLSX/CSV from: $RAW_DIR -> $RAW_CACHE_DIR" >&2
if [[ -d "$RAW_CACHE_DIR" ]]; then
  rm -rf "$RAW_CACHE_DIR"
fi
mkdir -p "$RAW_CACHE_DIR"
# xlsx_to_csv.py expects positional args: input_dir output_dir
python3 xlsx_to_csv.py "$RAW_DIR" -o "$RAW_CACHE_DIR"

echo "[3/5] Tidy cache tables: $RAW_CACHE_DIR -> $TIDY_CACHE_DIR, $TIDY_CACHE_DIR_SEQ" >&2
if [[ -d "$TIDY_CACHE_DIR" ]]; then
  rm -rf "$TIDY_CACHE_DIR"
fi
if [[ -d "$TIDY_CACHE_DIR_SEQ" ]]; then
  rm -rf "$TIDY_CACHE_DIR_SEQ"
fi
python3 raw_tables_to_tidy.py "$RAW_CACHE_DIR" "$TIDY_CACHE_DIR" "$TIDY_CACHE_DIR_SEQ"

echo "[4/5] Generating plots from: tp=$TIDY_DIR, cache=$TIDY_CACHE_DIR -> $GRAPHS_DIR" >&2
python3 plot_graphs.py --tp_indir "$TIDY_DIR" --cache_indir "$TIDY_CACHE_DIR" --outdir "$GRAPHS_DIR" --verbose

echo "[5/5] Generating plots from: tp=$TIDY_DIR_SEQ, cache=$TIDY_CACHE_DIR_SEQ -> $GRAPHS_DIR" >&2
python3 plot_graphs.py --tp_indir "$TIDY_DIR_SEQ" --cache_indir "$TIDY_CACHE_DIR_SEQ" --outdir "$GRAPHS_DIR_SEQ" --verbose

echo "Done. Graphs available at: $GRAPHS_DIR, $GRAPHS_DIR" >&2


