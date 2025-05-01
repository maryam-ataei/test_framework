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
#include "cc.h"
#include "cc_newreno_search.h"
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

    // Allocate memory
    struct newreno *nreno = calloc(1, sizeof(struct newreno));
    struct tcpcb *tp = calloc(1, sizeof(struct tcpcb));
    struct cc_var ccv = {0};

    // Initialize
    ccv.cc_data = nreno;
    ccv.ccvc.tcp = tp;
    int EXIT_FLAG = 0;
    int LOSS_FLAG = 0;

    // -----------------------------------------------------------------------------
    // ⚠ USER NOTE: Add your reset function below, if applicable.
    // -----------------------------------------------------------------------------
    search_reset(nreno, UNSET_BIN_DURATION_FALSE);          

    // Initialize protocol-specific variables
    tp->snd_ssthresh = TCP_INFINITE_SSTHRESH;
    tp->snd_cwnd = V_tcp_initcwnd_segments;
    int EXIT_FLAG = 0;
    int LOSS_FLAG = 0;

    char line[512];
    int line_number = 0;

    printf("Processing CSV input: %s\n\n", argv[1]);

    while (fgets(line, sizeof(line), file)) {
        line_number++;

        // Skip the header line or lines that start with '#'
        if (line_number == 1 || line[0] == '#') {
            continue;
        }

        // -----------------------------------------------------------------------------
        // ⚠ USER NOTE: Define the variables based on your protocol's input,
        // parse the CSV value, and set parsed values to the mock structure.
        // -----------------------------------------------------------------------------
        // Variables to store parsed values
        u32 now_us, mss, rtt_us, tp_rate_interval_us, app_limited, tp_delivered_rate, tp_delivered, lost, retrans, snd_nxt, sk_pacing_rate;
        u64 bytes_acked;

        // Parse the CSV line
        if (sscanf(line, "%u,%llu,%u,%u,%u,%u,%u,%u,%u,%u, %u, %u", &now_us, &bytes_acked, &mss, &rtt_us, &tp_delivered_rate, 
                &tp_rate_interval_us, &tp_delivered, &lost, &retrans, &app_limited, &snd_nxt, &sk_pacing_rate) != 12) {
            fprintf(stderr, "Invalid line format at line %d: %s", line_number, line);
            continue;
        }

        // Set parsed values to the mock structure
        mock_now_us = now_us;
        tp->t_srtt = (rtt_us << TCP_RTT_SHIFT) / tick;
        tp->t_maxseg = mss;
        ccv.bytes_this_ack = bytes_acked;

        if (LOSS_FLAG == 0 && lost > 0)
            LOSS_FLAG = 1;

        // Call protocol-specific update functions
        // -----------------------------------------------------------------------------
        // ⚠ USER NOTE: Call the function(s) to start running your protocol.
        // -----------------------------------------------------------------------------     
        search_update(ccv);

        // -----------------------------------------------------------------------------
        // ⚠ USER NOTE: Print results and info based on your requirements.
        // -----------------------------------------------------------------------------

        if ((tp->snd_ssthresh == tp->snd_cwnd) && (EXIT_FLAG == 0)) {
            printf("Exit Slow Start at %u\n", now_us);
            EXIT_FLAG = 1;
        }
    }

    // Cleanup
    free(tp);
    free(nreno);
    fclose(file);
    
    printf("Finished processing.\n");
    return 0;
}
