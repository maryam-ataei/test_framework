#ifndef TCP_H
#define TCP_H

#include <stdint.h>

#define TCP_INIT_CWND 10
#define TCP_INFINITE_SSTHRESH   0x7fffffff


/* Mock implementation of the Linux kernel's sock structure */
struct tcp_sock {
    uint64_t bytes_acked; // Simulated bytes acknowledged
    uint32_t mss_cache;   // Maximum segment size cache
    uint32_t snd_cwnd;    // Simulated congestion window
    uint32_t snd_ssthresh; // Simulated slow-start threshold
    uint32_t tcp_mstamp; // Simulated timestamp
};


/* Mock implementation of the Linux kernel's sock structure */
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

#endif // TCP_H
