# test_framework

## Introduction

This framework is designed to evaluate the search-based protocol in TCP, implemented through the search module. It processes input data, applies the search algorithm, and outputs results.

In this update, we separate the search_defs.h and tcp.h files and automatically generate search_module.c. This ensures that the exact functions from the original source file are copied without any changes.

## Files Overview

The test framework consists of the following files:

- search_module.c - Contains the main logic for the SEARCH algorithm used to update TCP parameters.

- test_search.c - A test file that reads CSV input, initializes mock structures, and calls the appropriate SEARCH functions.

- search_defs.h - Contains the definitions for structures and declarations used in the SEARCH algorithm.

- tcp.h - Defines mock structures for simulating a kernel-like environment with tcp_sock and sock structures.

## Automatic Module Generation

generate_module.py Script:


You can automatically generate search_module.c using the generate_module.py script. This script processes the original code by extracting sections marked with //keyword_begin and //keyword_end, and generates the corresponding source and header files.

To generate the search_module.c file, run the script with the following command:

`python generate_module.py <input_file> <keyword> <output_file>`

- <input_file>: The source file that contains the necessary code to extract sections.
- <keyword>: A unique keyword to identify the protocol.
- <output_file>: Where the generated file will be saved.

For example, to generate the necessary files, use the following command:

`python generate_module.py tcp_cubic_search.c search search_module.c`

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

