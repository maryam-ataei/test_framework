/*
 *****************************************************************************
 *  search_test.c
 *  ----------------------------------------------------------------------------
 *  This file is designed to test the `SEARCH` module using CSV input.
 *  This test file allows you to validate and verify your module.
 * 
 *  You can process CSV input, simulate various network conditions, and print relevant results.
 *  Modify this file to adjust parameters, conditions, or outputs for custom testing.
 *  
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
#include "search_defs.h"
#include "cc_helper_function.h"

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

    // Allocate memory for bictcp inside sock
    sk->bictcp = malloc(sizeof(struct bictcp));
    if (!sk->bictcp) {
        fprintf(stderr, "Failed to allocate memory for bictcp.\n");
        free(sk);
        fclose(file);
        return 1;
    }

    struct tcp_sock *tp = tcp_sk(sk);
    struct bictcp *ca = inet_csk_ca(sk);

    // -----------------------------------------------------------------------------
    // ⚠ USER NOTE: Add your reset function below, if applicable.
    // -----------------------------------------------------------------------------
    bictcp_search_reset(ca);            

    // Initialize protocol-specific variables
    tp->snd_ssthresh = TCP_INFINITE_SSTHRESH;
    tp->snd_cwnd = TCP_INIT_CWND;
    int EXIT_FLAG = 0;
    int LOSS_FLAG = 0;

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
                    
        u32 now_us, mss, rtt_us, tp_rate_interval_us, app_limited, tp_delivered_rate, tp_delivered, lost, retrans;
        u64 bytes_acked;

        // Parse the CSV line
        if (sscanf(line, "%u,%llu,%u,%u,%u,%u,%u,%u,%u,%u", &now_us, &bytes_acked, &mss, &rtt_us, &tp_delivered_rate, 
                &tp_rate_interval_us, &tp_delivered, &lost, &retrans, &app_limited) != 10) {
            fprintf(stderr, "Invalid line format at line %d: %s", line_number, line);
            continue;
        }

        // Set parsed values to the mock structure
        tp->tcp_mstamp = now_us;
        tp->bytes_acked = bytes_acked;
        tp->mss_cache = mss;

        if (LOSS_FLAG == 0 && lost > 0)
            LOSS_FLAG = 1;

        // Call protocol-specific update functions
        // -----------------------------------------------------------------------------
        // ⚠ USER NOTE: Call the function(s) to start running your protocol.
        // -----------------------------------------------------------------------------     
        search_update(sk, rtt_us);

        // -----------------------------------------------------------------------------
        // ⚠ USER NOTE: Print results and info based on your requirements.
        // -----------------------------------------------------------------------------

        if ((tp->snd_ssthresh == tp->snd_cwnd) && (EXIT_FLAG == 0)) {
            printf("Exit Slow Start at %u\n", now_us);
            EXIT_FLAG = 1;
        }

        // Print details
        printf("Line %d:\n", line_number);
        printf("  now_us: %u\n", now_us);
        printf("  bytes_acked: %llu\n", bytes_acked);
        printf("  mss: %u\n", mss);
        printf("  rtt_us: %u\n", rtt_us);
        printf("  loss happen: %u\n", LOSS_FLAG);
        printf("  Current bin index: %d\n", ca->search.curr_idx);
        printf("  Bin duration: %d\n", ca->search.bin_duration_us);
        printf("  Bin end time: %d\n", ca->search.bin_end_us);
        printf("  Scale factor: %d\n", ca->search.scale_factor);

        printf("  Bin values:\n");

        for (int i = 0; i < SEARCH_TOTAL_BINS; i++) {
            printf("    Bin[%d]: %u\n", i, ca->search.bin[i]);
        }
        printf("\n");
    }

    // Clean up memory
    if (sk->bictcp) {
        free(sk->bictcp);
    }
    free(sk);
    fclose(file);

    printf("Finished processing.\n");
    return 0;
}
