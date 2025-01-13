#ifndef SEARCH_H
#define SEARCH_H

#include <stdint.h>

#define SEARCH_TOTAL_BINS 25
#define MAX_US_INT 0xFFFF
#define TCP_INIT_CWND 10
#define SEARCH_BINS 10
#define SEARCH_EXTRA_BINS 15
#define search_window_duration_factor 35
#define search_missed_bins_threshold 2
#define search_thresh 35
#define cwnd_rollback 0


/* Mock implementation of the Linux kernel's sock structure */
struct tcp_sock {
    uint64_t bytes_acked; // Simulated bytes acknowledged
    uint32_t mss_cache;   // Maximum segment size cache
    uint32_t snd_cwnd;    // Simulated congestion window
    uint32_t snd_ssthresh; // Simulated slow-start threshold
};

struct bictcp {
    struct {
        uint32_t bin_duration_us; // Duration of each bin in microseconds
        int32_t curr_idx;         // Current index in the bins array
        uint32_t bin_end_us;      // End time of the latest bin in microseconds
        uint16_t bin[SEARCH_TOTAL_BINS]; // Array to store bytes per bin
        uint8_t unused;
        uint8_t scale_factor;     // Scale factor to fit the value within bin size
    } search;
};

/* Mock implementation of the Linux kernel's sock structure */
struct sock {
    struct tcp_sock tcp_sock; // Simulated TCP sock
    struct bictcp bictcp;     // Simulated congestion control state
};

/* Mock functions to simulate Linux kernel behavior */
#define tcp_sk(sk) (&(sk->tcp_sock))
#define inet_csk_ca(sk) (&(sk->bictcp))

void bictcp_search_reset(struct sock *sk);
uint8_t search_bit_shifting(struct sock *sk, uint64_t bin_value);
void search_init_bins(struct sock *sk, uint32_t now_us, uint32_t rtt_us);
void search_update_bins(struct sock *sk, uint32_t now_us, uint32_t rtt_us);
uint64_t search_compute_delivered_window(struct sock *sk, int32_t left, int32_t right, uint32_t fraction);
void search_exit_slow_start(struct sock *sk, uint32_t now_us, uint32_t rtt_us);
void search_update(struct sock *sk, uint32_t now_us, uint32_t rtt_us);

#endif // SEARCH_H