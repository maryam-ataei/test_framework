#ifndef SEARCH_DEFS_H
#define SEARCH_DEFS_H

#include <stdint.h>
#include <string.h>
#include "tcp.h"

void bictcp_search_reset(struct bictcp *ca);
uint32_t bictcp_clock_us(struct sock *sk);
uint8_t search_bit_shifting(struct sock *sk, uint64_t bin_value);
void search_init_bins(struct sock *sk, uint32_t now_us, uint32_t rtt_us);
void search_update_bins(struct sock *sk, uint32_t now_us, uint32_t rtt_us);
uint64_t search_compute_delivered_window(struct sock *sk, int32_t left, int32_t right, uint32_t fraction);
void search_exit_slow_start(struct sock *sk);
void search_update(struct sock *sk, uint32_t rtt_us);

// SEARCH_begin
#define MAX_US_INT 0xffff 
#define SEARCH_BINS 10		/* Number of bins in a window */
#define SEARCH_EXTRA_BINS 15 /* Number of additional bins to cover data after shiftting by RTT */
#define SEARCH_TOTAL_BINS 25 	/* Total number of bins containing essential bins to cover RTT shift */
// SEARCH_end

/* BIC TCP Parameters */
struct bictcp {
	uint32_t	cnt;		/* increase cwnd by 1 after ACKs */
	uint32_t	last_max_cwnd;	/* last maximum snd_cwnd */
	uint32_t	last_cwnd;	/* the last snd_cwnd */
	uint32_t	last_time;	/* time when updated last_cwnd */
	uint32_t	bic_origin_point;/* origin point of bic function */
	uint32_t	bic_K;		/* time to origin point
				   from the beginning of the current epoch */
	uint32_t	delay_min;	/* min delay (usec) */
	uint32_t	epoch_start;	/* beginning of an epoch */
	uint32_t	ack_cnt;	/* number of acks */
	uint32_t	tcp_cwnd;	/* estimated tcp cwnd */

	/* Union of HyStart and SEARCH variables */
	union {
		/* HyStart variables */
		struct {
			uint16_t	unused;
			uint8_t	sample_cnt;/* number of samples to decide curr_rtt */
			uint8_t	found;		/* the exit point is found? */
			uint32_t	round_start;	/* beginning of each round */
			uint32_t	end_seq;	/* end_seq of the round */
			uint32_t	last_ack;	/* last time when the ACK spacing is close */
			uint32_t	curr_rtt;	/* the minimum rtt of current round */
		}hystart;

		/* SEARCH variables */
		struct {
			uint32_t	bin_duration_us;	/* duration of each bin in microsecond */
			int32_t	curr_idx;	/* total number of bins */
			uint32_t	bin_end_us;	/* end time of the latest bin in microsecond */
			uint16_t	bin[SEARCH_TOTAL_BINS];	/* array to keep bytes for bins */
			uint8_t	unused;
			uint8_t	scale_factor;	/* scale factor to fit the value with bin size*/
		}search;
	};
};

#endif // SEARCH_DEFS_H
