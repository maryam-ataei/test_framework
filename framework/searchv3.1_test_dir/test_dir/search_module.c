/*
 *****************************************************************************
 *  Automatically Generated search_module.c
 *  ----------------------------------------------------------------------------
 * This file was automatically generated by the `generate_module.py` script.
 * It extracts the `SEARCH_begin` to `SEARCH_end` module section
 * from the **source file**: `tcp_cubic_search3.0_withu16_without_log_app_limited.c` and was generated on 2025-03-18 11:25:12.
 *
 * This file is part of a test framework designed for evaluating TCP module implementations.
 *  
 *  ⚠ WARNING: 
 * If you modify this file directly, rerunning `generate_module.py` will overwrite your changes.
 *  
 *  ✅ To prevent losing your modifications:
 * - Modify the **source file** `tcp_cubic_search3.0_withu16_without_log_app_limited.c` instead.
 *****************************************************************************
*/

#include <string.h>
#include "tcp.h"
#include "search_defs.h"
#include "cc_helper_function.h"

int search_window_duration_factor  = 35;
int search_thresh  = 35;
int cwnd_rollback  = 0;
int search_alpha = 2;

void bictcp_search_reset(struct bictcp *ca, enum unset_bin_duration flag)
{
	memset(ca->search.bin, 0, sizeof(ca->search.bin));
	ca->search.curr_idx = -1;
	ca->search.bin_end_us = 0;
	ca->search.scale_factor = 0;
	if (flag == UNSET_BIN_DURATION_FALSE)
		ca->search.bin_duration_us = 0; 
}

u32 bictcp_clock_us(const struct sock *sk)
{
	return tcp_sk(sk)->tcp_mstamp;
}

/* Scale bin value to fit bin size, rescale previous bins.
 * Return amount scaled.
 */
u8 search_bit_shifting(struct sock *sk, u64 bin_value) 
{

	struct bictcp *ca = inet_csk_ca(sk);
	u8 num_shift = 0; 
	u32 i = 0;


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
void search_init_bins(struct sock *sk, u32 now_us, u32 rtt_us)
{
	struct bictcp *ca = inet_csk_ca(sk);
	struct tcp_sock *tp = tcp_sk(sk);
	u8 amount_scaled = 0; 
	u64 bin_value = 0;

	if (ca->search.bin_duration_us == 0)
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

/**
 * search_update_bins - Update the bins in the SEARCH algorithm
 * 
 * This function updates the bins in the SEARCH algorithm when the bin boundary
 * has been crossed. It calculates how many bins have been passed since the last
 * bin update, handles missed bins, and assigns a value to the current bin based
 * on acknowledged bytes.
 *
 * Key steps:
 * - Calculate the number of bins that have passed since the last update.
 * - Reset SEARCH and reinitialize bins if the number of passed bins exceeds the
 *   threshold (`search_missed_bins_threshold`).
 * - Copy the value of the last bin into the missed bins, ensuring continuity.
 * - Update the bin end time and current index to reflect the number of passed bins.
 * - Compute the value for the current bin by scaling the total acknowledged bytes
 *   (`bytes_acked`) using the scaling factor (`scale_factor`).
 * - Ensure the computed bin value does not exceed the maximum allowed value.
 *   If it does, scale it down further using bit-shifting
 *   via the `search_bit_shifting` helper function.
 * - Assign the computed value to the current bin.
 *
 * Special considerations:
 * - The maximum representable bin value is constrained by `MAX_US_INT` (0xffff).
 *   If the bin value exceeds this threshold, it is scaled down to fit within
 *   the limit. This ensures proper representation and avoids overflow.
 */

void search_update_bins(struct sock *sk, u32 now_us, u32 rtt_us)
{
	struct bictcp *ca = inet_csk_ca(sk);
	struct tcp_sock *tp = tcp_sk(sk);
	u32 passed_bins = 0;
	u32 i = 0;
	u64 bin_value = 0;
	u8 amount_scaled = 0; 
	u32 initial_rtt = 0; 

	/* 
	*  The flow is application-limited: reset SEARCH while preserving the
	* existing bin duration.
	*/
	if (tp->app_limited) {
		bictcp_search_reset(ca, UNSET_BIN_DURATION_TRUE); 
		printf("app limited, reset search: %d\n ",tp->app_limited);
		return;
	}

	/* If passed_bins greater than 1, it means we have some missed bins */
	passed_bins = ((now_us - ca->search.bin_end_us) / ca->search.bin_duration_us) + 1;

	if (passed_bins > 1)
		printf("passed_bins %d\n ", passed_bins);
	/*
	 * If the RTT / bin duration is greater than the number of missed
	 * bins, that means it has been at least one RTT since the last bin
	 * was filled.  In this case, computing the delivered bytes over an
	 * RTT is unreliable so SEARCH should be reset.
	 *
	 * When this condition is met:
	 *   - If passed_bins exceeds SEARCH_BINS, perform a complete SEARCH reset including unseting bin_duration. The bin_duration will be reset upon receiving the next ack..
	 *   - Otherwise, perform a partial SEARCH reset that preserves the existing bin duration.
	 *
	 * After resetting the SEARCH state, reinitialize the bins using the current timestamp
	 * and RTT.
	 *
	 */
	initial_rtt = ca->search.bin_duration_us * SEARCH_BINS * 10 / search_window_duration_factor;
	if (passed_bins > search_alpha * (initial_rtt / ca->search.bin_duration_us)) { 

		if (passed_bins > SEARCH_BINS){
			bictcp_search_reset(ca, UNSET_BIN_DURATION_FALSE);
		} else {
			bictcp_search_reset(ca, UNSET_BIN_DURATION_TRUE);
		}
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
u64 search_compute_delivered_window(struct sock *sk, s32 left, s32 right, u32 fraction)
{
	struct bictcp *ca = inet_csk_ca(sk);
	u64 delivered = 0;

	delivered = ca->search.bin[(right - 1) % SEARCH_TOTAL_BINS] - ca->search.bin[left % SEARCH_TOTAL_BINS];
	
	if (left == 0) /* If we are interpolating using the very first bin, the "previous" bin value is 0. */
		delivered += (ca->search.bin[left % SEARCH_TOTAL_BINS]) * fraction / 100;
	else
		delivered += (ca->search.bin[left % SEARCH_TOTAL_BINS] - ca->search.bin[(left - 1) % SEARCH_TOTAL_BINS]) * fraction / 100;

	delivered += (ca->search.bin[right % SEARCH_TOTAL_BINS] - ca->search.bin[(right - 1) % SEARCH_TOTAL_BINS]) * (100 - fraction) / 100;

	return delivered;
}

/* Handle slow start exit condition */
void search_exit_slow_start(struct sock *sk, u32 now_us, u32 rtt_us)
{
	struct tcp_sock *tp = tcp_sk(sk);
	struct bictcp *ca = inet_csk_ca(sk);
	s32 cong_idx = 0;
	u32 initial_rtt = 0;
	u64 overshoot_bytes = 0;
	u32 overshoot_cwnd = 0;
	
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
			tp->snd_cwnd = max(tp->snd_cwnd - overshoot_cwnd, (u32)TCP_INIT_CWND);
		else
			tp->snd_cwnd = TCP_INIT_CWND;
 	}
 	
 	tp->snd_ssthresh = tp->snd_cwnd;

 	/*  If TCP re-enters slow start, the missed_bin threshold will be 
  	*   exceeded upon a bin update, and SEARCH will reset automatically. 
	*/
}

/**
 * search_update - Update SEARCH bins and evaluate slow start exit conditions
 *
 * This function handles the periodic updates of the SEARCH algorithm's bins,
 * which track delivered bytes over defined time intervals. It ensures that
 * bins are updated when their boundaries are reached and computes delivered
 * bytes for the current and previous windows. If the delivered bytes in the
 * current window are significantly less than in the previous window, it exits
 * the slow start phase based on the normalized difference in delivered bytes.
 *
 * Key steps:
 * - Initialize bins if they are not yet set.
 * - Update bins when the current time exceeds the bin boundary.
 * - Check if there are enough bins to calculate previous window delivered bytes.
 * - Compute delivered bytes for current and previous windows, considering
 *   fractional adjustments for RTT overlaps.
 * - Evaluate exit condition using normalized difference in delivered bytes
 *   and invoke slow start exit if the condition is met.
 */
void search_update(struct sock *sk, u32 rtt_us)
{

	struct bictcp *ca = inet_csk_ca(sk);

	s32 prev_idx = 0;
	u64 curr_delv_bytes = 0, prev_delv_bytes = 0;
	s32 norm_diff = 0;
	u32 now_us = bictcp_clock_us(sk);
	u32 fraction = 0;

	/* by receiving the first ack packet, initialize bin duration and bin end time */
	if (ca->search.curr_idx < 0) {  
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
				printf("norm %d\n curr_delv %d\n prev_delv %d\n", norm_diff, curr_delv_bytes, prev_delv_bytes);

				/* check for exit condition */
				if ((2 * prev_delv_bytes) >= curr_delv_bytes && norm_diff >= search_thresh)
					search_exit_slow_start(sk, now_us, rtt_us);
			}
		}
	}
}