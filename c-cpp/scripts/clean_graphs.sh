#!/usr/bin/env bash
set -euo pipefail

# Remove all directoriescreated by generate_graphs.sh

ROOT_DIR=".."
TIDY_DIR="$ROOT_DIR/tidy_tables"
TIDY_DIR_SEQ="$ROOT_DIR/seq_tidy_tables"
RAW_CACHE_DIR="$ROOT_DIR/raw_cache_tables"
TIDY_CACHE_DIR="$ROOT_DIR/tidy_cache_tables"
TIDY_CACHE_DIR_SEQ="$ROOT_DIR/seq_tidy_cache_tables"
GRAPHS_DIR="$ROOT_DIR/graphs"
GRAPHS_DIR_SEQ="$ROOT_DIR/seq_graphs"

echo "Cleaning generated directories..." >&2

for d in "$TIDY_DIR" "$TIDY_DIR_SEQ" "$RAW_CACHE_DIR" "$TIDY_CACHE_DIR" "$TIDY_CACHE_DIR_SEQ" "$GRAPHS_DIR" "$GRAPHS_DIR_SEQ"; do
  if [[ -d "$d" ]]; then
    echo " - Removing: $d" >&2
    rm -rf "$d"
  else
    echo " - Skipping (not found): $d" >&2
  fi
done

echo "Done." >&2