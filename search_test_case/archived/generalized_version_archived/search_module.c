#include "tcp.h"
#include "search_defs.h"
#include <string.h>

#define MAX_US_INT 0xffff
#define SEARCH_TOTAL_BINS 25
#define SEARCH_BINS 10
#define SEARCH_EXTRA_BINS 15

uint32_t search_window_duration_factor = 35;
uint32_t search_thresh = 35;
uint32_t cwnd_rollback = 0;
uint32_t search_missed_bins_threshold = 2;

uint32_t bictcp_clock_us(struct sock *sk)
{
	return tcp_sk(sk)->tcp_mstamp;
}

void bictcp_search_reset(struct bictcp *ca)
{
	memset(ca->search.bin, 0, sizeof(ca->search.bin));
	ca->search.bin_duration_us = 0;
	ca->search.curr_idx = -1;
	ca->search.bin_end_us = 0;
	ca->search.scale_factor = 0;
}

/* Scale bin value to fit bin size, rescale previous bins.
 * Return amount scaled.
 */
uint8_t search_bit_shifting(struct sock *sk, uint64_t bin_value) 
{

	struct bictcp *ca = inet_csk_ca(sk);
	uint8_t num_shift = 0; 
	uint32_t i = 0;


	/* Adjust bin_value if it's greater than MAX_BIN_VALUE */
	while (bin_value > MAX_US_INT) {
		num_shift += 1;
		bin_value >>= 1;  /* divide bin_value by 2 */
	}

	/* Adjust all previous bins according to the new num_shift */
	for (i = 0; i < SEARCH_TOTAL_BINS; i++) {
		ca->search.bin[i] >>= num_shift;
	}

	/* Update the scale factor */
	ca->search.scale_factor += num_shift;

	return num_shift;
}

/* Initialize bin */
void search_init_bins(struct sock *sk, uint32_t now_us, uint32_t rtt_us)
{
	struct bictcp *ca = inet_csk_ca(sk);
	struct tcp_sock *tp = tcp_sk(sk);
	uint8_t amount_scaled = 0; 
	uint64_t bin_value = 0;

	ca->search.bin_duration_us = (rtt_us * search_window_duration_factor) / (SEARCH_BINS * 10);
	ca->search.bin_end_us = now_us + ca->search.bin_duration_us;
	ca->search.curr_idx = 0;


	bin_value = tp->bytes_acked;
	if (bin_value > MAX_US_INT){
		amount_scaled = search_bit_shifting(sk, bin_value);
		bin_value >>= amount_scaled;
	}
	ca->search.bin[0] = bin_value;
}

/* Update bins */
void search_update_bins(struct sock *sk, uint32_t now_us, uint32_t rtt_us)
{
	struct bictcp *ca = inet_csk_ca(sk);
	struct tcp_sock *tp = tcp_sk(sk);
	uint32_t passed_bins = 0;
	uint32_t i = 0;
	uint64_t bin_value = 0;
	uint8_t amount_scaled = 0; 

	/* If passed_bins greater than 1, it means we have some missed bins */
	passed_bins = ((now_us - ca->search.bin_end_us) / ca->search.bin_duration_us) + 1;

	/* If we passed more than search_missed_bins_threshold bins, need to reset SEARCH, and initialize bins*/
	if (passed_bins > search_missed_bins_threshold) {
		bictcp_search_reset(ca);
		search_init_bins(sk, now_us, rtt_us);
		return;
	}

	for (i = ca->search.curr_idx + 1; i < ca->search.curr_idx + passed_bins; i++)
		ca->search.bin[i % SEARCH_TOTAL_BINS] = ca->search.bin[ca->search.curr_idx % SEARCH_TOTAL_BINS];
	
	ca->search.bin_end_us += passed_bins * ca->search.bin_duration_us;
	ca->search.curr_idx += passed_bins;

	/* Calculate bin_value by dividing bytes_acked by 2^scale_factor */
	bin_value = tp->bytes_acked >> ca->search.scale_factor; 

	if (bin_value > MAX_US_INT) {
		amount_scaled  = search_bit_shifting(sk, bin_value);
		bin_value >>= amount_scaled;
	}

	/* Assign the bin_value to the current bin */
	ca->search.bin[ca->search.curr_idx % SEARCH_TOTAL_BINS] = bin_value;
}

/* Calculate delivered bytes for a window considering interpolation */
uint64_t search_compute_delivered_window(struct sock *sk, int32_t left, int32_t right, uint32_t fraction)
{
	struct bictcp *ca = inet_csk_ca(sk);
	uint64_t delivered = 0;

	delivered = ca->search.bin[(right - 1) % SEARCH_TOTAL_BINS] - ca->search.bin[left % SEARCH_TOTAL_BINS];
	
	if (left == 0) /* If we are interpolating using the very first bin, the "previous" bin value is 0. */
		delivered += (ca->search.bin[left % SEARCH_TOTAL_BINS]) * fraction / 100;
	else
		delivered += (ca->search.bin[left % SEARCH_TOTAL_BINS] - ca->search.bin[(left - 1) % SEARCH_TOTAL_BINS]) * fraction / 100;

	delivered += (ca->search.bin[right % SEARCH_TOTAL_BINS] - ca->search.bin[(right - 1) % SEARCH_TOTAL_BINS]) * (100 - fraction) / 100;

	return delivered;
}

/* Handle slow start exit condition */
void search_exit_slow_start(struct sock *sk)
{
	struct tcp_sock *tp = tcp_sk(sk);
	struct bictcp *ca = inet_csk_ca(sk);
	int32_t cong_idx = 0;
	uint32_t initial_rtt = 0;
	uint64_t overshoot_bytes = 0;
	uint32_t overshoot_cwnd = 0;
	
	/* If cwnd rollback is enabled, the code calculates the initial round-trip time (RTT)
	 * and determines the congestion index (`cong_idx`) from which to compute the overshoot.
	 * The overshoot represents the excess bytes delivered beyond the estimated target,
	 * which is calculated over a window defined by the current and the rollback indices.
	 * 
	 * The rollback logic adjusts the congestion window (`snd_cwnd`) based on the overshoot:
	 * 1. It first computes the overshoot congestion window (`overshoot_cwnd`), derived by
	 *    dividing the overshoot bytes by the maximum segment size (MSS).
	 * 2. It reduces `snd_cwnd` by the calculated overshoot while ensuring it does not fall
	 *    below the initial congestion window (`TCP_INIT_CWND`), which acts as a safety guard.
	 * 3. If the overshoot exceeds the current congestion window, it resets `snd_cwnd` to the 
	 *    initial value, providing a safeguard to avoid a drastic drop in case of miscalculations
	 *    or unusual network conditions (e.g., TCP reset).
	 * 
	 * After adjusting the congestion window, the slow start threshold (`snd_ssthresh`) is set 
	 * to the updated congestion window to finalize the rollback.
	 */
	
	/* If cwnd rollback is enabled */
 	if (cwnd_rollback == 1) {

 		initial_rtt = ca->search.bin_duration_us * SEARCH_BINS * 10 / search_window_duration_factor;
 		cong_idx = ca->search.curr_idx - ((2 * initial_rtt) / ca->search.bin_duration_us);

 		/* Calculate the overshoot based on the delivered bytes between cong_idx and the current index */
 		overshoot_bytes = search_compute_delivered_window(sk, cong_idx, ca->search.curr_idx, 0);

 		/* Calculate the rollback congestion window based on overshoot divided by MSS */
 		overshoot_cwnd = overshoot_bytes / tp->mss_cache;
		
 		/* Reduce the current congestion window (cwnd) with a safety guard:
		* It doesn't drop below the initial cwnd (TCP_INIT_CWND) or is not 
		* larger than the current cwnd (e.g., In the case of a TCP reset) 
  		*/	
		if (overshoot_cwnd < tp->snd_cwnd)
			tp->snd_cwnd = max(tp->snd_cwnd - overshoot_cwnd, (uint32_t)TCP_INIT_CWND);
		else
			tp->snd_cwnd = TCP_INIT_CWND;
 	}
 	
 	tp->snd_ssthresh = tp->snd_cwnd;

 	/*  If TCP re-enters slow start, the missed_bin threshold will be 
  	*   exceeded upon a bin update, and SEARCH will reset automatically. 
	*/
}

//////////////////////// SEARCH ////////////////////////
void search_update(struct sock *sk, uint32_t rtt_us)
{

	struct bictcp *ca = inet_csk_ca(sk);

	int32_t prev_idx = 0;
	uint64_t curr_delv_bytes = 0, prev_delv_bytes = 0;
	int32_t norm_diff = 0;
	uint32_t now_us = bictcp_clock_us(sk);
	uint32_t fraction = 0;

	/* by receiving the first ack packet, initialize bin duration and bin end time */
	if (ca->search.bin_duration_us == 0) {
		search_init_bins(sk, now_us, rtt_us);
		return;
	}

	/* check if it's reached the bin boundary */
	if (now_us > ca->search.bin_end_us) {	

		/* Update bins */
		search_update_bins(sk, now_us, rtt_us);

		/* check if there is enough bins after shift for computing previous window */
		prev_idx = ca->search.curr_idx - (rtt_us/ca->search.bin_duration_us);

		if (prev_idx >= SEARCH_BINS && (ca->search.curr_idx - prev_idx) < SEARCH_EXTRA_BINS - 1) { 
			
			/* Calculate delivered bytes for the current and previous windows */
			curr_delv_bytes = search_compute_delivered_window(sk, ca->search.curr_idx - SEARCH_BINS, ca->search.curr_idx, 0);
			fraction = ((rtt_us % ca->search.bin_duration_us) * 100 / ca->search.bin_duration_us);
			prev_delv_bytes = search_compute_delivered_window(sk, prev_idx - SEARCH_BINS, prev_idx, fraction);

			if (prev_delv_bytes > 0) {
				norm_diff = ((2 * prev_delv_bytes) - curr_delv_bytes)*100 / (2 * prev_delv_bytes);

				/* check for exit condition */
				if ((2 * prev_delv_bytes) >= curr_delv_bytes && norm_diff >= search_thresh)
					search_exit_slow_start(sk);
			}
		}
	}
}

