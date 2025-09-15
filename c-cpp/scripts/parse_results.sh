#!/bin/bash

RESULTS_DIR="../results"

for file in "$RESULTS_DIR"/*.txt; do
    filename=$(basename -- "$file")

    if [[ $filename == results_*.txt ]]; then
        # remove prefix "results_" and extension ".txt"
        suffix=${filename#results_}
        suffix=${suffix%.txt}
        output="$RESULTS_DIR/table_${suffix}.csv"

        echo "Parsing $filename -> $(basename "$output")"
        python3 results_parser.py -input "$file" -output "$output"

    elif [[ $filename == results-cache_*.txt ]]; then
        suffix=${filename#results-cache_}
        suffix=${suffix%.txt}
        output="$RESULTS_DIR/table-cache_${suffix}.xlsx"

        echo "Parsing $filename -> $(basename "$output")"
        python3 results-cache_parser.py -input "$file" -output "$output"
    fi
done
