#ifndef SEARCH_DEFS_H
#define SEARCH_DEFS_H

#include <stdint.h>
#include "tcp.h"

#define MAX_US_INT 0xffff
#define SEARCH_TOTAL_BINS 25
#define SEARCH_BINS 10
#define SEARCH_EXTRA_BINS 15

struct bictcp {
    uint32_t cnt;
    uint32_t last_max_cwnd;
    uint32_t last_cwnd;
    uint32_t last_time;
    uint32_t bic_origin_point;
    uint32_t bic_K;
    uint32_t delay_min;
    uint32_t epoch_start;
    uint32_t ack_cnt;
    uint32_t tcp_cwnd;

    union {
        struct {
            uint16_t unused;
            uint8_t sample_cnt;
            uint8_t found;
            uint32_t round_start;
            uint32_t end_seq;
            uint32_t last_ack;
            uint32_t curr_rtt;
        } hystart;
        struct {
            uint32_t bin_duration_us;
            int32_t curr_idx;
            uint32_t bin_end_us;
            uint16_t bin[SEARCH_TOTAL_BINS];
            uint8_t unused;
            uint8_t scale_factor;
        } search;
    };
};

void bictcp_search_reset(struct bictcp *ca);
uint8_t search_bit_shifting(struct sock *sk, uint64_t bin_value);
void search_init_bins(struct sock *sk, uint32_t now_us, uint32_t rtt_us);
void search_update_bins(struct sock *sk, uint32_t now_us, uint32_t rtt_us);
uint64_t search_compute_delivered_window(struct sock *sk, int32_t left, int32_t right, uint32_t fraction);
void search_exit_slow_start(struct sock *sk);
void search_update(struct sock *sk, uint32_t rtt_us);

#endif // SEARCH_DEFS_H
