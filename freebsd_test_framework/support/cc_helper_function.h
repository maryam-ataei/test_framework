/*
 *****************************************************************************
 * Helper Functions
 * ----------------------------------------
 * This file contains helper functions and macros for CC calculations.
 *
 * ⚠ WARNING: If you need to add new helper functions specific to your protocol, 
 * define them below. However, rerunning `ss_extract.py` will overwrite 
 * this section unless you disable automatic regeneration.
 *****************************************************************************
 */

#ifndef CC_HELPER_FUNCTION_H
#define CC_HELPER_FUNCTION_H

#include <stdint.h>
#include <stdio.h>
#include <stdbool.h>
#include "cc.h"

#define TCP_RTT_SHIFT       5   /* shift for srtt; 5 bits frac. */
#define tick 1000000  // Or another appropriate value depending on your model
#define V_tcp_initcwnd_segments 10
#define TCP_INFINITE_SSTHRESH    0x7fffffff

extern uint64_t mock_now_us;


// Override getmicrouptime using mock_now_us from test input
static inline void getmicrouptime(struct timeval *tv) {
    tv->tv_sec = mock_now_us / 1000000;
    tv->tv_usec = mock_now_us % 1000000;
}

#define max(a, b) ((a) > (b) ? (a) : (b))

#endif /* CC_HELPER_FUNCTION_H */
