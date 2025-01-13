#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include "search.h"

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
    struct tcp_sock *tp = &sk.tcp_sock;
    struct bictcp *ca = &sk.bictcp;

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
        tp->bytes_acked = bytes_acked;
        tp->mss_cache = mss;

        // Call the search_update function
        search_update(&sk, now_us, rtt_us);

        // Print debug information
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

    fclose(file);

    printf("Finished processing.\n");
    return 0;
}