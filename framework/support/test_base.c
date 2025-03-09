/*
 *****************************************************************************
 *  test_yourmodule.c
 *  ----------------------------------------------------------------------------
 *  This file is designed to test the your module using CSV input.
 *  This test file allows you to validate and verify your module.
 * 
 *  You can process CSV input, simulate various network conditions, and print relevant results.
 *  Modify this file to adjust parameters, conditions, or outputs for custom testing.
 *  
 *  ⚠ WARNING: 
 *  If you modify this file directly, rerunning `ss_extract.py` will overwrite your changes.
 *****************************************************************************
 */


#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include "tcp.h"
#include "cc_helper_function.h"
// -----------------------------------------------------------------------------
// ⚠ USER NOTE: 
// Include the header file for the your module definitions
// Example: #include "search_defs.h"
// It contains the necessary structures, constants, and function
// prototypes used by the congestion control algorithm. 
// -----------------------------------------------------------------------------

int main(int argc, char *argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <input.csv>\n", argv[0]);
        return 1;
    }

    // Open the CSV file
    FILE *file = fopen(argv[1], "r");
    if (!file) {
        perror("Failed to open file");
        return 1;
    }

    // Allocate memory for sock structure
    struct sock *sk = malloc(sizeof(struct sock));
    if (!sk) {
        fprintf(stderr, "Failed to allocate memory for sock.\n");
        fclose(file);
        return 1;
    }
    memset(sk, 0, sizeof(struct sock));  // Initialize struct to zero

    struct tcp_sock *tp = tcp_sk(sk);

    // -----------------------------------------------------------------------------
    // ⚠ USER NOTE: 
    // Ensure that memory for congestion control structures (e.g., `bictcp`, `bbr`, etc.)
    // is allocated inside the socket structure (`sock`). 
    // Example: 
    //     sk->bictcp = malloc(sizeof(struct bictcp)); 
    //     struct bictcp *ca = inet_csk_ca(sk);
    // 
    // This allocation should be done for each socket to maintain separate state
    // for congestion control algorithms. Make sure to free the allocated memory
    // when the socket is closed to avoid memory leaks.
    // -----------------------------------------------------------------------------


    // -----------------------------------------------------------------------------
    // ⚠ USER NOTE: Add your reset function below, if applicable.
    // -----------------------------------------------------------------------------
    
    char line[256];
    int line_number = 0;

    printf("Processing CSV input: %s\n\n", argv[1]);

    while (fgets(line, sizeof(line), file)) {
        line_number++;

        // Skip the header line or lines that start with '#'
        if (line_number == 1 || line[0] == '#') {
            continue;
        }

        // Variables to store parsed values
        // -----------------------------------------------------------------------------
        // ⚠ USER NOTE: Define the variables based on your protocol's input,
        // parse the CSV value, and set parsed values to the mock structure.
        // -----------------------------------------------------------------------------
                    

        // Call protocol-specific update functions
        // -----------------------------------------------------------------------------
        // ⚠ USER NOTE: Call the function(s) to start running your protocol.
        // -----------------------------------------------------------------------------     

        // -----------------------------------------------------------------------------
        // ⚠ USER NOTE: Print results and info based on your requirements.
        // -----------------------------------------------------------------------------

    }

    // -----------------------------------------------------------------------------
    // ⚠ USER NOTE:
    // Ensure that you clean up memory for congestion control structures
    // (e.g., `bictcp`, `bbr`, etc.) when the socket is being destroyed or closed.
    // Example cleanup for `bictcp`:
    //     if (sk->bictcp) {
    //         free(sk->bictcp); // Free memory for `bictcp`
    //     }
    // This ensures proper resource management and prevents memory leaks.
    // -----------------------------------------------------------------------------

    free(sk);
    fclose(file);

    printf("Finished processing.\n");
    return 0;
}
