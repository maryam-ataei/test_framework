# Search Test Framework - Version 1
This is the first version of the Search Test Framework, designed to test the functionality of the SEARCH algorithm using a mock implementation. The framework processes input data from a CSV file and runs the search_update function on the data.

Files
The following files are included in this version:

1. search_module.c
Contains the implementation of the SEARCH algorithm, including functions like bictcp_search_reset, search_init_bins, search_update, and search_exit_slow_start.

2. test_search.c
This file contains the test code for running the SEARCH algorithm. It reads input data from a CSV file and processes it through the search_update function. It also prints the debug information, including the current bin index and bin values.

3. search.h
The header file containing the necessary structure definitions for the mock implementation, such as struct sock, struct tcp_sock, and struct bictcp.

## Compilation
To compile the framework, run the following command:

`gcc -o search_test search_module.c test_search.c -Wall -Wextra`

This will generate the search_test executable, which you can run with input data.

## Usage
Once compiled, you can run the test with the following command:

`./search_test data_sample_viasat_fixed.csv > output.txt`

This command reads the input CSV file (data_sample_viasat_fixed.csv), processes it with the SEARCH algorithm, and outputs the results to output.txt.

## Input CSV Format

The CSV file should have the following columns (in this order):

- Column 1: now_us - The current timestamp in microseconds.
- Column 2: bytes_acked - The number of bytes acknowledged.
- Column 3: mss - The maximum segment size.
- Column 4: rtt_us - The round-trip time in microseconds.
If the CSV file contains headers, the first line will be skipped.

## Output

The output will display the processed information, including the current bin index and the values for each bin. Here is an example output format:

## Cleanup
After running the test, the program frees the allocated memory for the bictcp structure and closes the input file.

