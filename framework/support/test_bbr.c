/*
 *****************************************************************************
 *  bbr_test.c
 *  ----------------------------------------------------------------------------
 *  This file is designed to test the `BBR` module using CSV input.
 *  This test file allows you to validate and verify your module.
 * 
 *  You can process CSV input, simulate various network conditions, and print relevant results.
 *  Modify this file to adjust parameters, conditions, or outputs for custom testing.
 *  
 *
 *  ⚠ WARNING: 
 *  If you modify this file directly, rerunning `cc_extract.py` will overwrite your changes.
 *****************************************************************************
 */


#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include "tcp.h"
#include "bbr_defs.h"
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

    // Allocate memory for bbr inside sock
    sk->bbr = malloc(sizeof(struct bbr));
    if (!sk->bbr) {
        fprintf(stderr, "Failed to allocate memory for bbr.\n");
        free(sk);
        fclose(file);
        return 1;
    }

    struct tcp_sock *tp = tcp_sk(sk);
    struct bbr *bbr = inet_csk_ca(sk);

    // -----------------------------------------------------------------------------
    // ⚠ USER NOTE: Add your reset function below, if applicable.
    // -----------------------------------------------------------------------------
    bbr_init(sk);            

    int EXIT_FLAG = 0;
    int LOSS_FLAG = 0;

    char line[256];
    int line_number = 0;

    printf("Processing CSV input: %s\n\n", argv[1]);

    u32 prev_lost_out = 0;
    u32 prev_retrans_out = 0;

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
                    
        // Variables to store parsed values
        u32 now_us, mss, rtt_us, tp_rate_interval_us, app_limited, tp_delivered_rate, tp_delivered, lost, retrans, snd_nxt, sk_pacing_rate;
        u64 bytes_acked;

        // Parse the CSV line
        if (sscanf(line, "%u,%llu,%u,%u,%u,%u,%u,%u,%u,%u, %u, %u", &now_us, &bytes_acked, &mss, &rtt_us, &tp_delivered_rate, 
                &tp_rate_interval_us, &tp_delivered, &lost, &retrans, &app_limited, &snd_nxt, &sk_pacing_rate) != 12) {
            fprintf(stderr, "Invalid line format at line %d: %s", line_number, line);
            continue;
        }

        tp->delivered = tp_delivered;

        // Create a mock rate sample structure
        struct rate_sample rs;
        memset(&rs, 0, sizeof(rs));
        rs.is_app_limited = app_limited;

        // Determine if we just entered recovery 
        bool in_recovery_now = (retrans > 0 || lost > 0);
        bool was_not_in_recovery = (prev_lost_out == 0 && prev_retrans_out == 0);

        /* If we just enter recovery and was not there exactly before it, 
         * update next_rtt_delivered with tp->delivered 
        */
        if (in_recovery_now && was_not_in_recovery) {
            bbr->next_rtt_delivered = tp->delivered;
        }

        /* Update previous loss and retransmission 
         * values for the next iteration
        */
        prev_lost_out = lost;
        prev_retrans_out = retrans;

        // Update round_start
        if (tp_delivered - tp_delivered_rate >= bbr->next_rtt_delivered) {
            bbr->next_rtt_delivered = tp_delivered; // Move RTT boundary forward
            bbr->rtt_cnt++;
            bbr->round_start = 1;
        }
        else{
            bbr->round_start = 0;
        }

        // Bandwidth estimation
        u64 new_bw = 0;
        u64 delivered_bytes = 0;
        u32 bbr_bw_rtts = 10;
        if (tp_rate_interval_us > 0) {
            
            // Compute a new bandwidth sample
            delivered_bytes = tp_delivered_rate * (u64)BW_UNIT;

            new_bw = delivered_bytes / tp_rate_interval_us;

            // Update if new_bw > max_bw and if tp_rate_interval_us is lower (meaning a new valid sample)
            if (new_bw > bbr_max_bw(sk) || tp_rate_interval_us < bbr->bw.s[0].t) {
                minmax_running_max(&bbr->bw, bbr_bw_rtts, bbr->rtt_cnt, new_bw);
            }

            // If the RTT count has reached 10, reset it for the next sampling window
            if (bbr->rtt_cnt >= bbr_bw_rtts)
                bbr->rtt_cnt = 0;
        }

        if (LOSS_FLAG == 0 && lost > 0)
            LOSS_FLAG = 1;

        // Call protocol-specific update functions
        // -----------------------------------------------------------------------------
        // ⚠ USER NOTE: Call the function(s) to start running your protocol.
        // -----------------------------------------------------------------------------     
        // Check if BBR has exited the STARTUP phase
        bbr_check_full_bw_reached(sk, &rs);


        // -----------------------------------------------------------------------------
        // ⚠ USER NOTE: Print results and info based on your requirements.
        // -----------------------------------------------------------------------------

        if (bbr_full_bw_reached(sk) && EXIT_FLAG == 0) {
            printf("BBR Exits STARTUP Phase at %u us\n", now_us);
            EXIT_FLAG = 1;
        }

        // Print details
        printf("Line %d:\n", line_number);
        printf("  now_us: %u\n", now_us);
        printf("  bbr_full_bw: %u\n", bbr->full_bw);
        printf("  bbr_max_bw: %u\n", bbr_max_bw(sk));
        printf("  full_bw_cnt: %u\n", bbr->full_bw_cnt);
        printf("  round_start: %u\n", bbr->round_start);
        printf("  app_limited: %llu\n", rs.is_app_limited);
        printf("  loss_happen: %u\n", LOSS_FLAG);
        printf("  full_bw_reached: %s\n", bbr_full_bw_reached(sk) ? "Yes" : "No");
        printf("\n");
    }
    // Clean up memory
    if (sk->bbr) {
        free(sk->bbr);
    }
    free(sk);
    fclose(file);

    printf("Finished processing.\n");
    return 0;
}
