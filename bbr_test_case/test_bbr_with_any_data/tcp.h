/*
 *****************************************************************************
 * Automatically Generated tcp.h
 * ----------------------------------
 * This file was automatically generated by the `generate_module.py` script
 * on 2025-02-20 12:34:30.
 *
 * It defines core TCP structures required for the test framework.
 * Note: This file does NOT include congestion control structures (e.g., bictcp, bbr).
 *
 * ⚠ WARNING: If you modify this file manually, be aware that rerunning
 * the `generate_module.py` script will overwrite any changes.
 * ✅ To customize the generated content, consider modifying `generate_module.py`.
 *****************************************************************************
*/

#ifndef TCP_H
#define TCP_H

#include <stdint.h>
#include "tcp_helper_function.h"

#define TCP_INIT_CWND 10
#define TCP_INFINITE_SSTHRESH   0x7fffffff

struct tcp_sock {
    u64 delivered;
    u64 srtt_us;
    u64 delivered_mstamp;
    u64 lost;
    u64 snd_cwnd;
    u64 snd_ssthresh;
    u64 tcp_mstamp;
    u64 mss_cache;
};

struct sock {
    u64 sk_pacing_status;
    struct bbr *bbr;
    u64 sk_pacing_rate;
    struct tcp_sock tcp_sock;
    u64 sk_max_pacing_rate;
};

struct rate_sample {
    u64 is_app_limited;
};

#define inet_csk_ca(sk) ((sk->bbr))
#define tcp_sk(sk) (&(sk->tcp_sock))

#endif /* TCP_H */
