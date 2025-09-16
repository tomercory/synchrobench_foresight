#!/bin/bash
 
# Define microbenchmark parameters (FTVS: fixed thread count, varying sizes. FSVT: fixed size, varying thread counts)
FTVS_threads="4 64 128"
FTVS_sizes="128 512 2048 8192 32768 131072 524288 2097152 8388608 33554432"
FSVT_sizes="512 131072 33554432"
FSVT_threads="1 2 8 16 32" # 4, 64, 128 threads already run as part of FTVS

iterations="1 2 3 4 5"

# Make sure that the benchmarks run up-to-date code
cd ..
make clean && make
cd scripts

# ### Sequential ###
#   # Define the output files and clear them if they already exists
#   output_file1="../results/results_sequential_foresight_SIMD_update_0p.txt"
#   output_file2="../results/results_sequential_foresight_SIMD_update_5p.txt"
#   output_file3="../results/results_sequential_foresight_SIMD_update_50p.txt"
#   output_file4="../results/results-cache_sequential_foresight_SIMD_update_0p.txt"
#   output_file5="../results/results-cache_sequential_foresight_SIMD_update_5p.txt"
#   output_file6="../results/results-cache_sequential_foresight_SIMD_update_50p.txt"
#   > "$output_file1"
#   > "$output_file2"
#   > "$output_file3"
#   > "$output_file4"
#   > "$output_file5"
#   > "$output_file6"
  
#   # iterate over initial sizes
#   for i in ${FTVS_sizes}; do
#     # repeat for multiple iterations
#     for j in ${iterations}; do
#       # Print a header with current parameters
#       date +"%H:%M:%S" >> "$output_file1"
#       echo "Running with parameters: -t 1 -i $i (Run $j of 5)" >> "$output_file1"
#       echo "----------------------------------------" >> "$output_file1"
#       # Run (readonly, no cache monitoring)
#       ./../bin/sequential-skiplist -t 1 -i "$i" -r "$(($i * 2))" -u 0 -f 0 -m 0 >> "$output_file1"
#       # Print a blank line after each command output
#       echo "" >> "$output_file1"

#       date +"%H:%M:%S" >> "$output_file2"
#       echo "Running with parameters: -t 1 -i $i (Run $j of 5)" >> "$output_file2"
#       echo "----------------------------------------" >> "$output_file2"
#       # Run (5% update, no cache monitoring)
#       ./../bin/sequential-skiplist -t 1 -i "$i" -r "$(($i * 2))" -u 5 -f 0 -m 0 >> "$output_file2"
#       # Print a blank line after each command output
#       echo "" >> "$output_file2"

#       date +"%H:%M:%S" >> "$output_file3"
#       echo "Running with parameters: -t 1 -i $i (Run $j of 5)" >> "$output_file3"
#       echo "----------------------------------------" >> "$output_file3"
#       # Run (50% update, no cache monitoring)
#       ./../bin/sequential-skiplist -t 1 -i "$i" -r "$(($i * 2))" -u 50 -f 0 -m 0 >> "$output_file3"
#       # Print a blank line after each command output
#       echo "" >> "$output_file3"

#       date +"%H:%M:%S" >> "$output_file4"
#       echo "Running with parameters: -t 1 -i $i (Run $j of 5)" >> "$output_file4"
#       echo "----------------------------------------" >> "$output_file4"
#       # Run (readonly, cache monitoring)
#       ./../bin/sequential-skiplist -t 1 -i "$i" -r "$(($i * 2))" -u 0 -f 0 -m 1 >> "$output_file4"
#       # Print a blank line after each command output
#       echo "" >> "$output_file4"

#       date +"%H:%M:%S" >> "$output_file5"
#       echo "Running with parameters: -t 1 -i $i (Run $j of 5)" >> "$output_file5"
#       echo "----------------------------------------" >> "$output_file5"
#       # Run (5% update, cache monitoring)
#       ./../bin/sequential-skiplist -t 1 -i "$i" -r "$(($i * 2))" -u 5 -f 0 -m 1 >> "$output_file5"
#       # Print a blank line after each command output
#       echo "" >> "$output_file5"

#       date +"%H:%M:%S" >> "$output_file6"
#       echo "Running with parameters: -t 1 -i $i (Run $j of 5)" >> "$output_file6"
#       echo "----------------------------------------" >> "$output_file6"
#       # Run (50% update, cache monitoring)
#       ./../bin/sequential-skiplist -t 1 -i "$i" -r "$(($i * 2))" -u 50 -f 0 -m 1 >> "$output_file6"
#       # Print a blank line after each command output
#       echo "" >> "$output_file6"
#     done
#   done
#   echo "Sequential foresight_SIMD case finished successfuly!" | mail -s "Skiplist Experiment Update" tomer.cory@campus.technion.ac.il

# ### Optimistic ###
#   # Define the output files and clear them if they already exists
#   output_file1="../results/results_optimistic_foresight_SIMD_update_0p.txt"
#   output_file2="../results/results_optimistic_foresight_SIMD_update_5p.txt"
#   output_file3="../results/results_optimistic_foresight_SIMD_update_50p.txt"
#   output_file4="../results/results-cache_optimistic_foresight_SIMD_update_0p.txt"
#   output_file5="../results/results-cache_optimistic_foresight_SIMD_update_5p.txt"
#   output_file6="../results/results-cache_optimistic_foresight_SIMD_update_50p.txt"
#   > "$output_file1"
#   > "$output_file2"
#   > "$output_file3"
#   > "$output_file4"
#   > "$output_file5"
#   > "$output_file6"
    
#   # iterate over initial sizes, thread counts - FTVS
#   for i in ${FTVS_sizes}; do
#   for t in ${FTVS_threads}; do 
#     # repeat for multiple iterations
#     for j in ${iterations}; do
#       # Print a header with current parameters
#       date +"%H:%M:%S" >> "$output_file1"
#       echo "Running with parameters: -t $t -i $i (Run $j of 5)" >> "$output_file1"
#       echo "----------------------------------------" >> "$output_file1"
#       # Run (readonly, no cache monitoring)
#       ./../bin/SPIN-skiplist -t "$t" -i "$i" -r "$(($i * 2))" -u 0 -f 0 -m 0 >> "$output_file1"
#       # Print a blank line after each command output
#       echo "" >> "$output_file1"

#       date +"%H:%M:%S" >> "$output_file2"
#       echo "Running with parameters: -t $t -i $i (Run $j of 5)" >> "$output_file2"
#       echo "----------------------------------------" >> "$output_file2"
#       # Run (5% update, no cache monitoring)
#       ./../bin/SPIN-skiplist -t "$t" -i "$i" -r "$(($i * 2))" -u 5 -f 0 -m 0 >> "$output_file2"
#       # Print a blank line after each command output
#       echo "" >> "$output_file2"

#       date +"%H:%M:%S" >> "$output_file3"
#       echo "Running with parameters: -t $t -i $i (Run $j of 5)" >> "$output_file3"
#       echo "----------------------------------------" >> "$output_file3"
#       # Run (50% update, no cache monitoring)
#       ./../bin/SPIN-skiplist -t "$t" -i "$i" -r "$(($i * 2))" -u 50 -f 0 -m 0 >> "$output_file3"
#       # Print a blank line after each command output
#       echo "" >> "$output_file3"

#       date +"%H:%M:%S" >> "$output_file4"
#       echo "Running with parameters: -t $t -i $i (Run $j of 5)" >> "$output_file4"
#       echo "----------------------------------------" >> "$output_file4"
#       # Run (readonly, cache monitoring)
#       ./../bin/SPIN-skiplist -t "$t" -i "$i" -r "$(($i * 2))" -u 0 -f 0 -m 1 >> "$output_file4"
#       # Print a blank line after each command output
#       echo "" >> "$output_file4"

#       date +"%H:%M:%S" >> "$output_file5"
#       echo "Running with parameters: -t $t -i $i (Run $j of 5)" >> "$output_file5"
#       echo "----------------------------------------" >> "$output_file5"
#       # Run (5% update, cache monitoring)
#       ./../bin/SPIN-skiplist -t "$t" -i "$i" -r "$(($i * 2))" -u 5 -f 0 -m 1 >> "$output_file5"
#       # Print a blank line after each command output
#       echo "" >> "$output_file5"

#       date +"%H:%M:%S" >> "$output_file6"
#       echo "Running with parameters: -t $t -i $i (Run $j of 5)" >> "$output_file6"
#       echo "----------------------------------------" >> "$output_file6"
#       # Run (50% update, cache monitoring)
#       ./../bin/SPIN-skiplist -t "$t" -i "$i" -r "$(($i * 2))" -u 50 -f 0 -m 1 >> "$output_file6"
#       # Print a blank line after each command output
#       echo "" >> "$output_file6"
#     done
#   done
#   done

#   # iterate over initial sizes, thread counts - FSVT
#   for i in ${FSVT_sizes}; do
#   for t in ${FSVT_threads}; do 
#     # repeat for multiple iterations
#     for j in ${iterations}; do
#       # Print a header with current parameters
#       date +"%H:%M:%S" >> "$output_file1"
#       echo "Running with parameters: -t $t -i $i (Run $j of 5)" >> "$output_file1"
#       echo "----------------------------------------" >> "$output_file1"
#       # Run (readonly, no cache monitoring)
#       ./../bin/SPIN-skiplist -t "$t" -i "$i" -r "$(($i * 2))" -u 0 -f 0 -m 0 >> "$output_file1"
#       # Print a blank line after each command output
#       echo "" >> "$output_file1"

#       date +"%H:%M:%S" >> "$output_file2"
#       echo "Running with parameters: -t $t -i $i (Run $j of 5)" >> "$output_file2"
#       echo "----------------------------------------" >> "$output_file2"
#       # Run (5% update, no cache monitoring)
#       ./../bin/SPIN-skiplist -t "$t" -i "$i" -r "$(($i * 2))" -u 5 -f 0 -m 0 >> "$output_file2"
#       # Print a blank line after each command output
#       echo "" >> "$output_file2"

#       date +"%H:%M:%S" >> "$output_file3"
#       echo "Running with parameters: -t $t -i $i (Run $j of 5)" >> "$output_file3"
#       echo "----------------------------------------" >> "$output_file3"
#       # Run (50% update, no cache monitoring)
#       ./../bin/SPIN-skiplist -t "$t" -i "$i" -r "$(($i * 2))" -u 50 -f 0 -m 0 >> "$output_file3"
#       # Print a blank line after each command output
#       echo "" >> "$output_file3"

#       date +"%H:%M:%S" >> "$output_file4"
#       echo "Running with parameters: -t $t -i $i (Run $j of 5)" >> "$output_file4"
#       echo "----------------------------------------" >> "$output_file4"
#       # Run (readonly, cache monitoring)
#       ./../bin/SPIN-skiplist -t "$t" -i "$i" -r "$(($i * 2))" -u 0 -f 0 -m 1 >> "$output_file4"
#       # Print a blank line after each command output
#       echo "" >> "$output_file4"

#       date +"%H:%M:%S" >> "$output_file5"
#       echo "Running with parameters: -t $t -i $i (Run $j of 5)" >> "$output_file5"
#       echo "----------------------------------------" >> "$output_file5"
#       # Run (5% update, cache monitoring)
#       ./../bin/SPIN-skiplist -t "$t" -i "$i" -r "$(($i * 2))" -u 5 -f 0 -m 1 >> "$output_file5"
#       # Print a blank line after each command output
#       echo "" >> "$output_file5"

#       date +"%H:%M:%S" >> "$output_file6"
#       echo "Running with parameters: -t $t -i $i (Run $j of 5)" >> "$output_file6"
#       echo "----------------------------------------" >> "$output_file6"
#       # Run (50% update, cache monitoring)
#       ./../bin/SPIN-skiplist -t "$t" -i "$i" -r "$(($i * 2))" -u 50 -f 0 -m 1 >> "$output_file6"
#       # Print a blank line after each command output
#       echo "" >> "$output_file6"
#     done
#   done
#   done
#   echo "Optimistic foresight_SIMD case finished successfuly!" | mail -s "Skiplist Experiment Update" tomer.cory@campus.technion.ac.il

### Fraser ###
# Define the output files and clear them if they already exists
  output_file1="../results/results_fraser_foresight_SIMD_update_0p.txt"
  output_file2="../results/results_fraser_foresight_SIMD_update_5p.txt"
  output_file3="../results/results_fraser_foresight_SIMD_update_50p.txt"
  output_file4="../results/results-cache_fraser_foresight_SIMD_update_0p.txt"
  output_file5="../results/results-cache_fraser_foresight_SIMD_update_5p.txt"
  output_file6="../results/results-cache_fraser_foresight_SIMD_update_50p.txt"
  > "$output_file1"
  > "$output_file2"
  > "$output_file3"
  > "$output_file4"
  > "$output_file5"
  > "$output_file6"
    
  # iterate over initial sizes, thread counts - FTVS
  for i in ${FTVS_sizes}; do
  for t in ${FTVS_threads}; do 
    # repeat for multiple iterations
    for j in ${iterations}; do
      # Print a header with current parameters
      date +"%H:%M:%S" >> "$output_file1"
      echo "Running with parameters: -t $t -i $i (Run $j of 5)" >> "$output_file1"
      echo "----------------------------------------" >> "$output_file1"
      # Run (readonly, no cache monitoring)
      ./../bin/lockfree-fraser-skiplist -t "$t" -i "$i" -r "$(($i * 2))" -u 0 -f 0 -m 0 >> "$output_file1"
      # Print a blank line after each command output
      echo "" >> "$output_file1"

      date +"%H:%M:%S" >> "$output_file2"
      echo "Running with parameters: -t $t -i $i (Run $j of 5)" >> "$output_file2"
      echo "----------------------------------------" >> "$output_file2"
      # Run (5% update, no cache monitoring)
      ./../bin/lockfree-fraser-skiplist -t "$t" -i "$i" -r "$(($i * 2))" -u 5 -f 0 -m 0 >> "$output_file2"
      # Print a blank line after each command output
      echo "" >> "$output_file2"

      date +"%H:%M:%S" >> "$output_file3"
      echo "Running with parameters: -t $t -i $i (Run $j of 5)" >> "$output_file3"
      echo "----------------------------------------" >> "$output_file3"
      # Run (50% update, no cache monitoring)
      ./../bin/lockfree-fraser-skiplist -t "$t" -i "$i" -r "$(($i * 2))" -u 50 -f 0 -m 0 >> "$output_file3"
      # Print a blank line after each command output
      echo "" >> "$output_file3"

      date +"%H:%M:%S" >> "$output_file4"
      echo "Running with parameters: -t $t -i $i (Run $j of 5)" >> "$output_file4"
      echo "----------------------------------------" >> "$output_file4"
      # Run (readonly, cache monitoring)
      ./../bin/lockfree-fraser-skiplist -t "$t" -i "$i" -r "$(($i * 2))" -u 0 -f 0 -m 1 >> "$output_file4"
      # Print a blank line after each command output
      echo "" >> "$output_file4"

      date +"%H:%M:%S" >> "$output_file5"
      echo "Running with parameters: -t $t -i $i (Run $j of 5)" >> "$output_file5"
      echo "----------------------------------------" >> "$output_file5"
      # Run (5% update, cache monitoring)
      ./../bin/lockfree-fraser-skiplist -t "$t" -i "$i" -r "$(($i * 2))" -u 5 -f 0 -m 1 >> "$output_file5"
      # Print a blank line after each command output
      echo "" >> "$output_file5"

      date +"%H:%M:%S" >> "$output_file6"
      echo "Running with parameters: -t $t -i $i (Run $j of 5)" >> "$output_file6"
      echo "----------------------------------------" >> "$output_file6"
      # Run (50% update, cache monitoring)
      ./../bin/lockfree-fraser-skiplist -t "$t" -i "$i" -r "$(($i * 2))" -u 50 -f 0 -m 1 >> "$output_file6"
      # Print a blank line after each command output
      echo "" >> "$output_file6"
    done
  done
  done

  # iterate over initial sizes, thread counts - FSVT
  for i in ${FSVT_sizes}; do
  for t in ${FSVT_threads}; do 
    # repeat for multiple iterations
    for j in ${iterations}; do
      # Print a header with current parameters
      date +"%H:%M:%S" >> "$output_file1"
      echo "Running with parameters: -t $t -i $i (Run $j of 5)" >> "$output_file1"
      echo "----------------------------------------" >> "$output_file1"
      # Run (readonly, no cache monitoring)
      ./../bin/lockfree-fraser-skiplist -t "$t" -i "$i" -r "$(($i * 2))" -u 0 -f 0 -m 0 >> "$output_file1"
      # Print a blank line after each command output
      echo "" >> "$output_file1"

      date +"%H:%M:%S" >> "$output_file2"
      echo "Running with parameters: -t $t -i $i (Run $j of 5)" >> "$output_file2"
      echo "----------------------------------------" >> "$output_file2"
      # Run (5% update, no cache monitoring)
      ./../bin/lockfree-fraser-skiplist -t "$t" -i "$i" -r "$(($i * 2))" -u 5 -f 0 -m 0 >> "$output_file2"
      # Print a blank line after each command output
      echo "" >> "$output_file2"

      date +"%H:%M:%S" >> "$output_file3"
      echo "Running with parameters: -t $t -i $i (Run $j of 5)" >> "$output_file3"
      echo "----------------------------------------" >> "$output_file3"
      # Run (50% update, no cache monitoring)
      ./../bin/lockfree-fraser-skiplist -t "$t" -i "$i" -r "$(($i * 2))" -u 50 -f 0 -m 0 >> "$output_file3"
      # Print a blank line after each command output
      echo "" >> "$output_file3"

      date +"%H:%M:%S" >> "$output_file4"
      echo "Running with parameters: -t $t -i $i (Run $j of 5)" >> "$output_file4"
      echo "----------------------------------------" >> "$output_file4"
      # Run (readonly, cache monitoring)
      ./../bin/lockfree-fraser-skiplist -t "$t" -i "$i" -r "$(($i * 2))" -u 0 -f 0 -m 1 >> "$output_file4"
      # Print a blank line after each command output
      echo "" >> "$output_file4"

      date +"%H:%M:%S" >> "$output_file5"
      echo "Running with parameters: -t $t -i $i (Run $j of 5)" >> "$output_file5"
      echo "----------------------------------------" >> "$output_file5"
      # Run (5% update, cache monitoring)
      ./../bin/lockfree-fraser-skiplist -t "$t" -i "$i" -r "$(($i * 2))" -u 5 -f 0 -m 1 >> "$output_file5"
      # Print a blank line after each command output
      echo "" >> "$output_file5"

      date +"%H:%M:%S" >> "$output_file6"
      echo "Running with parameters: -t $t -i $i (Run $j of 5)" >> "$output_file6"
      echo "----------------------------------------" >> "$output_file6"
      # Run (50% update, cache monitoring)
      ./../bin/lockfree-fraser-skiplist -t "$t" -i "$i" -r "$(($i * 2))" -u 50 -f 0 -m 1 >> "$output_file6"
      # Print a blank line after each command output
      echo "" >> "$output_file6"
    done
  done
  done
  echo "Fraser foresight_SIMD case finished successfuly!" | mail -s "Skiplist Experiment Update" tomer.cory@campus.technion.ac.il

### NHS ###
# Define the output files and clear them if they already exists
  output_file1="../results/results_nohotspot_foresight_SIMD_update_0p.txt"
  output_file2="../results/results_nohotspot_foresight_SIMD_update_5p.txt"
  output_file3="../results/results_nohotspot_foresight_SIMD_update_50p.txt"
  output_file4="../results/results-cache_nohotspot_foresight_SIMD_update_0p.txt"
  output_file5="../results/results-cache_nohotspot_foresight_SIMD_update_5p.txt"
  output_file6="../results/results-cache_nohotspot_foresight_SIMD_update_50p.txt"
  > "$output_file1"
  > "$output_file2"
  > "$output_file3"
  > "$output_file4"
  > "$output_file5"
  > "$output_file6"
    
  # iterate over initial sizes, thread counts - FTVS
  for i in ${FTVS_sizes}; do
  for t in ${FTVS_threads}; do 
    # repeat for multiple iterations
    for j in ${iterations}; do
      # Print a header with current parameters
      date +"%H:%M:%S" >> "$output_file1"
      echo "Running with parameters: -t $t -i $i (Run $j of 5)" >> "$output_file1"
      echo "----------------------------------------" >> "$output_file1"
      # Run (readonly, no cache monitoring)
      ./../bin/lockfree-nohotspot-skiplist -t "$t" -i "$i" -r "$(($i * 2))" -u 0 -f 0 -m 0 >> "$output_file1"
      # Print a blank line after each command output
      echo "" >> "$output_file1"

      date +"%H:%M:%S" >> "$output_file2"
      echo "Running with parameters: -t $t -i $i (Run $j of 5)" >> "$output_file2"
      echo "----------------------------------------" >> "$output_file2"
      # Run (5% update, no cache monitoring)
      ./../bin/lockfree-nohotspot-skiplist -t "$t" -i "$i" -r "$(($i * 2))" -u 5 -f 0 -m 0 >> "$output_file2"
      # Print a blank line after each command output
      echo "" >> "$output_file2"

      date +"%H:%M:%S" >> "$output_file3"
      echo "Running with parameters: -t $t -i $i (Run $j of 5)" >> "$output_file3"
      echo "----------------------------------------" >> "$output_file3"
      # Run (50% update, no cache monitoring)
      ./../bin/lockfree-nohotspot-skiplist -t "$t" -i "$i" -r "$(($i * 2))" -u 50 -f 0 -m 0 >> "$output_file3"
      # Print a blank line after each command output
      echo "" >> "$output_file3"

      date +"%H:%M:%S" >> "$output_file4"
      echo "Running with parameters: -t $t -i $i (Run $j of 5)" >> "$output_file4"
      echo "----------------------------------------" >> "$output_file4"
      # Run (readonly, cache monitoring)
      ./../bin/lockfree-nohotspot-skiplist -t "$t" -i "$i" -r "$(($i * 2))" -u 0 -f 0 -m 1 >> "$output_file4"
      # Print a blank line after each command output
      echo "" >> "$output_file4"

      date +"%H:%M:%S" >> "$output_file5"
      echo "Running with parameters: -t $t -i $i (Run $j of 5)" >> "$output_file5"
      echo "----------------------------------------" >> "$output_file5"
      # Run (5% update, cache monitoring)
      ./../bin/lockfree-nohotspot-skiplist -t "$t" -i "$i" -r "$(($i * 2))" -u 5 -f 0 -m 1 >> "$output_file5"
      # Print a blank line after each command output
      echo "" >> "$output_file5"

      date +"%H:%M:%S" >> "$output_file6"
      echo "Running with parameters: -t $t -i $i (Run $j of 5)" >> "$output_file6"
      echo "----------------------------------------" >> "$output_file6"
      # Run (50% update, cache monitoring)
      ./../bin/lockfree-nohotspot-skiplist -t "$t" -i "$i" -r "$(($i * 2))" -u 50 -f 0 -m 1 >> "$output_file6"
      # Print a blank line after each command output
      echo "" >> "$output_file6"
    done
  done
  done

  # iterate over initial sizes, thread counts - FSVT
  for i in ${FSVT_sizes}; do
  for t in ${FSVT_threads}; do 
    # repeat for multiple iterations
    for j in ${iterations}; do
      # Print a header with current parameters
      date +"%H:%M:%S" >> "$output_file1"
      echo "Running with parameters: -t $t -i $i (Run $j of 5)" >> "$output_file1"
      echo "----------------------------------------" >> "$output_file1"
      # Run (readonly, no cache monitoring)
      ./../bin/lockfree-nohotspot-skiplist -t "$t" -i "$i" -r "$(($i * 2))" -u 0 -f 0 -m 0 >> "$output_file1"
      # Print a blank line after each command output
      echo "" >> "$output_file1"

      date +"%H:%M:%S" >> "$output_file2"
      echo "Running with parameters: -t $t -i $i (Run $j of 5)" >> "$output_file2"
      echo "----------------------------------------" >> "$output_file2"
      # Run (5% update, no cache monitoring)
      ./../bin/lockfree-nohotspot-skiplist -t "$t" -i "$i" -r "$(($i * 2))" -u 5 -f 0 -m 0 >> "$output_file2"
      # Print a blank line after each command output
      echo "" >> "$output_file2"

      date +"%H:%M:%S" >> "$output_file3"
      echo "Running with parameters: -t $t -i $i (Run $j of 5)" >> "$output_file3"
      echo "----------------------------------------" >> "$output_file3"
      # Run (50% update, no cache monitoring)
      ./../bin/lockfree-nohotspot-skiplist -t "$t" -i "$i" -r "$(($i * 2))" -u 50 -f 0 -m 0 >> "$output_file3"
      # Print a blank line after each command output
      echo "" >> "$output_file3"

      date +"%H:%M:%S" >> "$output_file4"
      echo "Running with parameters: -t $t -i $i (Run $j of 5)" >> "$output_file4"
      echo "----------------------------------------" >> "$output_file4"
      # Run (readonly, cache monitoring)
      ./../bin/lockfree-nohotspot-skiplist -t "$t" -i "$i" -r "$(($i * 2))" -u 0 -f 0 -m 1 >> "$output_file4"
      # Print a blank line after each command output
      echo "" >> "$output_file4"

      date +"%H:%M:%S" >> "$output_file5"
      echo "Running with parameters: -t $t -i $i (Run $j of 5)" >> "$output_file5"
      echo "----------------------------------------" >> "$output_file5"
      # Run (5% update, cache monitoring)
      ./../bin/lockfree-nohotspot-skiplist -t "$t" -i "$i" -r "$(($i * 2))" -u 5 -f 0 -m 1 >> "$output_file5"
      # Print a blank line after each command output
      echo "" >> "$output_file5"

      date +"%H:%M:%S" >> "$output_file6"
      echo "Running with parameters: -t $t -i $i (Run $j of 5)" >> "$output_file6"
      echo "----------------------------------------" >> "$output_file6"
      # Run (50% update, cache monitoring)
      ./../bin/lockfree-nohotspot-skiplist -t "$t" -i "$i" -r "$(($i * 2))" -u 50 -f 0 -m 1 >> "$output_file6"
      # Print a blank line after each command output
      echo "" >> "$output_file6"
    done
  done
  done
  echo "NHS foresight_SIMD case finished successfuly! (foresight_SIMD experiment is over)" | mail -s "Skiplist Experiment Update" tomer.cory@campus.technion.ac.il
