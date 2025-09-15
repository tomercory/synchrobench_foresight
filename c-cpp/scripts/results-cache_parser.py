import re
import argparse
import pandas as pd
from collections import defaultdict

def parse_experiment_results(input_file, output_file):
    """
    Parses the experiment results file and generates multiple 2D xlsx sheets based on "-i" and "-t" values.
    
    The script extracts transaction counts and cache statistics to compute:
    1. Transactions per run (txs)
    2. L1 cache accesses per transaction (L1ref/tx)
    3. L1 cache misses per transaction (L1miss/tx)
    4. L3 cache accesses per transaction (L3ref/tx)
    5. L3 cache misses per transaction (L3miss/tx)
    
    Parameters:
        input_file (str): Path to the input results file.
        output_file (str): Path to the output xlsx file.
    """
    # Regex patterns to extract required data
    param_pattern = re.compile(r"Running with parameters: -t (\d+) -i (\d+)")
    txs_pattern = re.compile(r"#txs\s+: (\d+)")
    l1_ref_pattern = re.compile(r"#L1 cache accesses\s+: (\d+)")
    l1_miss_pattern = re.compile(r"#L1 cache misses\s+: (\d+)")
    l3_ref_pattern = re.compile(r"#L3 cache accesses\s+: (\d+)")
    l3_miss_pattern = re.compile(r"#L3 cache misses\s+: (\d+)")

    # Data structure to store results
    results = defaultdict(list)

    # Read the file and parse the data
    with open(input_file, 'r') as file:
        lines = file.readlines()

    current_t, current_i = None, None

    for line in lines:
        # Match parameters line
        param_match = param_pattern.search(line)
        if param_match:
            current_t = int(param_match.group(1))
            current_i = int(param_match.group(2))

        # Match transactions
        txs_match = txs_pattern.search(line)
        if txs_match and current_t is not None and current_i is not None:
            txs = int(txs_match.group(1))
            results[(current_t, current_i)].append({'txs': txs})

        # Match cache statistics
        if (current_t, current_i) in results and results[(current_t, current_i)]:
            entry = results[(current_t, current_i)][-1]  # Get the latest entry
            l1_ref_match = l1_ref_pattern.search(line)
            l1_miss_match = l1_miss_pattern.search(line)
            l3_ref_match = l3_ref_pattern.search(line)
            l3_miss_match = l3_miss_pattern.search(line)

            if l1_ref_match:
                entry['L1_ref'] = int(l1_ref_match.group(1))
            if l1_miss_match:
                entry['L1_miss'] = int(l1_miss_match.group(1))
            if l3_ref_match:
                entry['L3_ref'] = int(l3_ref_match.group(1))
            if l3_miss_match:
                entry['L3_miss'] = int(l3_miss_match.group(1))

    # Prepare data for output
    def compute_average(metric_key):
        """Computes the average of metric_key for each (t, i) pair."""
        data = defaultdict(dict)
        for (t, i), runs in results.items():
            metric_values = [entry[metric_key] for entry in runs if metric_key in entry]
            if metric_values:
                data[t][i] = sum(metric_values) / len(metric_values)
        return data

    def compute_average_per_tx(metric_key, tx_key):
        """Computes the average of metric_key / tx_key for each (t, i) pair."""
        data = defaultdict(dict)
        for (t, i), runs in results.items():
            metric_values = [entry[metric_key]  for entry in runs if metric_key in entry]
            tx_values = [entry[tx_key] for entry in runs if tx_key in entry]
            if metric_values and tx_values:
                data[t][i] = sum(metric_values) / sum(tx_values)
        return data


    metrics = {
        "txs": compute_average("txs"),
        "L1ref_per_tx": compute_average_per_tx("L1_ref", "txs"),
        "L1miss_per_tx": compute_average_per_tx("L1_miss", "txs"),
        "L3ref_per_tx": compute_average_per_tx("L3_ref", "txs"),
        "L3miss_per_tx": compute_average_per_tx("L3_miss", "txs"),
    }

    # Write to an Excel file with multiple sheets
    with pd.ExcelWriter(output_file) as writer:
        for metric_name, metric_data in metrics.items():
            df = pd.DataFrame.from_dict(metric_data, orient='index').sort_index()
            df = df.sort_index(axis=1)  # Sort columns (i values) in ascending order
            df.to_excel(writer, sheet_name=metric_name)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse experiment results and output cache statistics.")
    parser.add_argument("-input", required=True, help="Path to input results file")
    parser.add_argument("-output", required=True, help="Path to output file")
    args = parser.parse_args()

    parse_experiment_results(args.input, args.output)
