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
#include "hystartpp_defs.h"
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
    // Allocate memory for bictcp inside sock
    sk->bictcp = malloc(sizeof(struct bictcp));
    if (!sk->bictcp) {
        fprintf(stderr, "Failed to allocate memory for bictcp.\n");
        free(sk);
        fclose(file);
        return 1;
    }

    struct bictcp *ca = inet_csk_ca(sk);

    // -----------------------------------------------------------------------------
    // ⚠ USER NOTE: Add your reset function below, if applicable.
    // -----------------------------------------------------------------------------
    bictcp_reset(ca);
    hystartpp_reset(sk);

    // Initialize protocol-specific variables
    tp->snd_ssthresh = TCP_INFINITE_SSTHRESH;
    tp->snd_cwnd = TCP_INIT_CWND;
    int LOSS_FLAG = 0;
    u32 pre_acked = 0;

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
        
        // Variables to store parsed values
        u32 now_us, mss, rtt_us, tp_rate_interval_us, app_limited, tp_delivered_rate, tp_delivered, lost, retrans, snd_nxt, snd_una, sk_pacing_rate;
        u64 bytes_acked;

        // Parse the CSV line
        if (sscanf(line, "%u,%llu,%u,%u,%u,%u,%u,%u,%u,%u, %u, %u, %u", &now_us, &bytes_acked, &mss, &rtt_us, &tp_delivered_rate, 
                &tp_rate_interval_us, &tp_delivered, &lost, &retrans, &app_limited, &snd_nxt, &sk_pacing_rate,&snd_una) != 13) {
            fprintf(stderr, "Invalid line format at line %d: %s", line_number, line);
            continue;
        }                   

        // Call protocol-specific update functions
        // -----------------------------------------------------------------------------
        // ⚠ USER NOTE: Call the function(s) to start running your protocol.
        // -----------------------------------------------------------------------------  

        /* Update the TCP socket state with the current input values */
        tp->snd_nxt = snd_nxt;
        tp->snd_una = snd_una;
        sk->sk_pacing_rate = sk_pacing_rate;

        u32 acked;
        u32 delta_ack_pkt;
        u32 cumulative_ack_pkts;

        cumulative_ack_pkts = bytes_acked / mss;
        delta_ack_pkt = cumulative_ack_pkts - pre_acked;
        acked = delta_ack_pkt;

        pre_acked = cumulative_ack_pkts;

        if (line_number == 2 && line[0] != '#') {
            ca->hspp_end_seq = tp->snd_nxt;
            ca->hspp_current_round_minrtt = rtt_us;
            ca->hspp_last_round_minrtt = ca->hspp_current_round_minrtt; /* {RFC9406_L186} */
            ca->hspp_current_round_minrtt = ~0U;                /* {RFC9406_L187} */
            ca->hspp_flag = HSPP_IN_SS;
        }
        
        /* Use RTT sample from input; ensure non-zero delay 
         *  (avoid divide-by-zero or meaningless results)
         */
        u32 delay;
        delay = rtt_us;
        if (delay == 0)
            delay = 1;
        
        /* Update the minimum observed delay for HyStart */
        /* first time call or link delay decreases */
        if (ca->delay_min == 0 || ca->delay_min > delay)
            ca->delay_min = delay;

        if (LOSS_FLAG == 0 && lost > 0){
            LOSS_FLAG = 1;
            printf("First Loss is happened\n");
            break;
        }


        if (tcp_in_slow_start(tp) && (ca->hspp_flag != HSPP_DEACTIVE))
            hystartpp_adjust_params(sk, delay);

        if (ca->hspp_flag != HSPP_DEACTIVE)
            hystartpp_adjust_cwnd(sk, acked);
        // -----------------------------------------------------------------------------
        // ⚠ USER NOTE: Print results and info based on your requirements.
        // -----------------------------------------------------------------------------
        // Print details
        printf("Line %d:\n", line_number);
        printf("  now_us: %u\n", now_us);
        printf("  hspp_end_seq: %u\n", ca->hspp_end_seq);
        printf("  hspp_rttsample_counter: %u\n", ca->hspp_rttsample_counter);
        printf("  hspp_current_round_minrtt: %u\n", ca->hspp_current_round_minrtt);
        printf("  hspp_round_counter: %u\n", ca->hspp_round_counter);
        printf("  hspp_entered_css_at_round: %u\n", ca->hspp_entered_css_at_round);
        printf("  hspp_css_baseline_minrtt: %u\n", ca->hspp_css_baseline_minrtt);
        printf("  hspp_last_round_minrtt: %u\n", ca->hspp_last_round_minrtt);
        printf("  hspp_flag: %u\n", ca->hspp_flag);
        printf("  snd_una: %u\n", tp->snd_una);
        printf("  loss happen: %u\n", LOSS_FLAG);
        printf("  snd_cwnd: %u\n", tp->snd_cwnd);
        printf("  snd_cwnd_cnt: %u\n", tp->snd_cwnd_cnt);


        printf("\n");        

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
    // Clean up memory
    if (sk->bictcp) {
        free(sk->bictcp);
    }

    free(sk);
    fclose(file);

    printf("Finished processing.\n");
    return 0;
}
