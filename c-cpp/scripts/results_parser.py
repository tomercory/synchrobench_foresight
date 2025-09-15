import re
import csv
import argparse
from collections import defaultdict


def parse_experiment_results(input_file, output_csv):
    """
    Parses the experiment results file and generates a 2D CSV table based on "-i" and "-t" values.

    Parameters:
        input_file (str): Path to the input results file.
        output_csv (str): Path to the output CSV file.
    """
    # Regex patterns to extract required data
    param_pattern = re.compile(r"Running with parameters: -t (\d+) -i (\d+)")
    txs_pattern = re.compile(r"#txs\s+: (\d+)")

    # Data structure to store results
    results = defaultdict(lambda: defaultdict(list))

    # Read the file and parse the data
    with open(input_file, 'r') as file:
        lines = file.readlines()

    current_t = None
    current_i = None

    for line in lines:
        # Match parameters line
        param_match = param_pattern.search(line)
        if param_match:
            current_t = int(param_match.group(1))
            current_i = int(param_match.group(2))
            continue

        # Match #txs line
        txs_match = txs_pattern.search(line)
        if txs_match and current_t is not None and current_i is not None:
            txs_value = int(txs_match.group(1))
            results[current_t][current_i].append(txs_value)

    # Prepare data for CSV
    sorted_t_values = sorted(results.keys())
    sorted_i_values = sorted(set(i for t in results.values() for i in t.keys()))

    # Create the 2D table
    table = [["-i\\-t"] + sorted_i_values]

    for t in sorted_t_values:
        row = [t]
        for i in sorted_i_values:
            if i in results[t]:
                # Compute the mean of #txs for the given -t and -i
                mean_txs = sum(results[t][i]) / len(results[t][i])
                row.append(mean_txs)
            else:
                row.append(None)  # Fill with None if no data is available
        table.append(row)

    # Write to CSV
    with open(output_csv, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(table)


def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Parse experiment results and generate a CSV output.")
    parser.add_argument("-input", required=True, help="Path to the input results file.")
    parser.add_argument("-output", required=True, help="Path to the output CSV file.")

    # Parse arguments
    args = parser.parse_args()

    # Run the parsing function
    parse_experiment_results(args.input, args.output)


if __name__ == "__main__":
    main()
