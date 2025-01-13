#ifndef TCP_H
#define TCP_H

#include <stdint.h>

#define TCP_INIT_CWND 10
#define TCP_INFINITE_SSTHRESH   0x7fffffff

/** Mock implementation of the Linux kernel's tcp_sock structure */
struct tcp_sock {
    uint32_t snd_cwnd; // Simulated snd_cwnd
    uint32_t bytes_acked; // Simulated bytes_acked
    uint32_t lsndtime; // Simulated lsndtime
    uint32_t snd_ssthresh; // Simulated snd_ssthresh
    uint32_t mss_cache; // Simulated mss_cache
    uint32_t tcp_mstamp; // Simulated tcp_mstamp
    uint32_t snd_nxt; // Simulated snd_nxt
};
/** Mock implementation of the Linux kernel's sock structure */
struct sock {
    struct bictcp *bictcp;
    struct tcp_sock tcp_sock;
};

/* Mock functions to simulate Linux kernel behavior */
#define tcp_sk(sk) (&(sk->tcp_sock))
#define inet_csk_ca(sk) ((sk)->bictcp)

#ifndef max
#define max(a, b) ((a) > (b) ? (a) : (b))
#endif

// If additional functions or structures are needed, add them here.

#endif // TCP_H
