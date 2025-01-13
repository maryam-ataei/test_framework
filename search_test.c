#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include "search.h"
#include "search_defs.h"


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

    // Initialize the mock structure
    struct sock sk = {0};
    struct sock *sk_ptr = &sk;

    // Allocate memory for bictcp
    sk_ptr->bictcp = malloc(sizeof(struct bictcp));
    if (!sk_ptr->bictcp) {
        fprintf(stderr, "Failed to allocate memory for bictcp.\n");
        fclose(file);
        return 1;
    }

    struct tcp_sock *tp = tcp_sk(sk_ptr);
    struct bictcp *ca = inet_csk_ca(sk_ptr);

    // Call reset function of the protocol here, if needed
    // Example: bictcp_search_reset(ca);
    bictcp_search_reset(ca);

    char line[256];
    int line_number = 0;

    printf("Processing CSV input: %s\n\n", argv[1]);

    while (fgets(line, sizeof(line), file)) {
        line_number++;

        // Skip the header line
        if (line_number == 1) {
            continue;
        }

        // Variables to store parsed values
        uint32_t now_us, mss, rtt_us;
        uint64_t bytes_acked;

        // Parse the CSV line
        if (sscanf(line, "%u,%lu,%u,%u", &now_us, &bytes_acked, &mss, &rtt_us) != 4) {
            fprintf(stderr, "Invalid line format at line %d: %s", line_number, line);
            continue;
        }

        // Set parsed values to the mock structure
        tp->tcp_mstamp = now_us;
        tp->bytes_acked = bytes_acked;
        tp->mss_cache = mss;

        // Call the function or the relevant function for the running protocol
        // Example: search_update(sk_ptr, rtt_us);
        search_update(sk_ptr, rtt_us);

        // Print debug information
        // Example:
        // printf("Line %d:\n", line_number);
        // printf("  now_us: %u\n", now_us);
        // printf("  bytes_acked: %lu\n", bytes_acked);
        // printf("  mss: %u\n", mss);
        // printf("  rtt_us: %u\n", rtt_us);
        // printf("  Current bin index: %d\n", ca->search.curr_idx);
        // printf("  Bin values:\n");
        // for (int i = 0; i < SEARCH_TOTAL_BINS; i++) {
        //     printf("    Bin[%d]: %u\n", i, ca->search.bin[i]);
        // }
        // printf("\n");
        printf("Line %d:\n", line_number);
        printf("  now_us: %u\n", now_us);
        printf("  bytes_acked: %lu\n", bytes_acked);
        printf("  mss: %u\n", mss);
        printf("  rtt_us: %u\n", rtt_us);
        printf("  Current bin index: %d\n", ca->search.curr_idx);
        printf("  Bin values:\n");
        for (int i = 0; i < SEARCH_TOTAL_BINS; i++) {
            printf("    Bin[%d]: %u\n", i, ca->search.bin[i]);
        }
        printf("\n");
    }

    // Clean up
    free(sk_ptr->bictcp);
    fclose(file);

    printf("Finished processing.\n");
    return 0;
}

// Add function call for the desired protocol, e.g., search_update(sk_ptr, rtt_us);
