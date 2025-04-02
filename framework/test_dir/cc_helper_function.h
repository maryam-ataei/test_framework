/*
 *****************************************************************************
 * Helper Functions
 * ----------------------------------------
 * This file contains helper functions and macros for TCP calculations.
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
#include <time.h>

typedef unsigned char        u8;
typedef unsigned short       u16;
typedef unsigned int         u32;
typedef unsigned long long   u64;
typedef signed char          s8;
typedef short                s16;
typedef int                  s32;
typedef long long            s64;

/* Parameters used to convert time values */
#define MSEC_PER_SEC    1000L
#define USEC_PER_MSEC   1000L
#define NSEC_PER_USEC   1000L
#define NSEC_PER_MSEC   1000000L
#define USEC_PER_SEC    1000000L
#define NSEC_PER_SEC    1000000000L
#define FSEC_PER_SEC    1000000000000000LL

#define SK_PACING_NONE 0
#define SK_PACING_NEEDED 1
#define TCP_CA_Open 0
#define HZ  1024
#define BITS_PER_LONG 64
#define LONG_MAX    ((long)(~0UL >> 1))
#define GSO_MAX_SIZE 65536
#define LINUX_MIB_TCPHYSTARTTRAINDETECT 0
#define LINUX_MIB_TCPHYSTARTTRAINCWND 0
#define LINUX_MIB_TCPHYSTARTDELAYCWND 0
#define LINUX_MIB_TCPHYSTARTDELAYDETECT 0

#define sock_net(sk) (NULL)

#define before(seq1, seq2)    ((s32)((seq1) - (seq2)) < 0)
#define before_eq(seq1, seq2) ((s32)((seq1) - (seq2)) <= 0)
#define after(seq1, seq2)     ((s32)((seq1) - (seq2)) > 0)
#define after_eq(seq1, seq2)  ((s32)((seq1) - (seq2)) >= 0)

#define min(x, y) ((x) < (y) ? (x) : (y))
#define max(x, y) ((x) > (y) ? (x) : (y))
#define min_t(type, x, y) ((type)(x) < (type)(y) ? (type)(x) : (type)(y))

#define MAX_JIFFY_OFFSET ((LONG_MAX >> 1)-1)

/* This forces the compiler to read x only once */
#define READ_ONCE(x) (*(volatile typeof(x) *)&(x))

#define NET_INC_STATS(net, field) do { (void)(net); (void)(field); } while (0)
#define NET_ADD_STATS(net, field, value) do { (void)(net); (void)(field); (void)(value); } while (0)

// Define pr_debug as printf for user-space
#ifndef pr_debug
#define pr_debug(fmt, ...) printf(fmt, ##__VA_ARGS__)
#endif

#ifndef clamp
#define clamp(val, min, max) ((val < min) ? min : (val > max) ? max : val)
#endif

/* unsigned 64bit divide with 32bit divisor */
static inline u64 div_u64(u64 dividend, u32 divisor) {
    return dividend / divisor;
}

/* Unsigned 64bit divide with 64bit divisor */
static inline u64 div64_u64(u64 dividend, u64 divisor) {
    return dividend / divisor;
}

static inline u32 div64_ul(u64 dividend, u32 divisor)
{
    return (u32)(dividend / divisor);
}


#define do_div(n, base) ({                  \
    u32 __base = (base);                    \
    u32 __rem;                               \
    __rem = ((u64)(n)) % __base;            /* Get remainder */  \
    (n) = ((u64)(n)) / __base;              /* Update n with quotient */  \
    __rem;                                  /* Return remainder */  \
})


/* Atomic compare-and-exchange operation */
#define cmpxchg(ptr, old, new) (__sync_val_compare_and_swap(ptr, old, new))

/* Structure for minmax filtering */
struct minmax_sample {
    u32 t;
    u32 v;
};

struct minmax {
    struct minmax_sample s[3];
};

static inline u32 minmax_get(const struct minmax *m)
{
    // printf("minmax_get: returning %u\n", m->s[0].v);
    return m->s[0].v;
}


static inline void minmax_reset(struct minmax *m, u32 t, u32 meas) {
    m->s[0].t = t;
    m->s[0].v = meas;
    m->s[1].t = t;
    m->s[1].v = meas;
    m->s[2].t = t;
    m->s[2].v = meas;
}

/* Fake replacement for jiffies */
static inline u32 get_mock_jiffies() {
    return (u32)(clock() / (CLOCKS_PER_SEC / 1000));  // Simulate jiffies in milliseconds
}

/* Define a global variable for jiffies (simulating the kernel's tcp_jiffies32) */
static u32 tcp_jiffies32 = 0;

/* Function to update jiffies */
static inline void update_jiffies() {
    tcp_jiffies32 = get_mock_jiffies();
}

/* Define a fake placeholder function that compiles but does nothing */
struct tcp_sock; // Forward declaration
static inline u32 tcp_min_rtt(const struct tcp_sock *tp) {
    (void)tp; // Prevents "unused parameter" warnings
    return 500; // Fake minimum RTT value (adjust if needed)
}

static u32 minmax_subwin_update(struct minmax *m, u32 win, struct minmax_sample *val)
{
    if (val->t - m->s[0].t > win / 4)
        m->s[0] = m->s[1];  // Move second-best value up
    if (val->t - m->s[1].t > win / 2)
        m->s[1] = m->s[2];  // Move third-best value up

    return m->s[0].v;
}


static u32 minmax_running_max(struct minmax *m, u32 win, u32 rtt_cnt, u32 sample)
{
    struct minmax_sample val = { .t = rtt_cnt, .v = sample };

    if (sample >= m->s[0].v || (rtt_cnt - m->s[2].t > win)) {
        minmax_reset(m, rtt_cnt, sample);
        return sample;
    }

    if (sample >= m->s[1].v) {
        m->s[2] = m->s[1];
        m->s[1] = val;
    } else if (sample >= m->s[2].v) {
        m->s[2] = val;
    }

    return minmax_subwin_update(m, win, &val);
}


static inline int fls64(unsigned long word)
{
    if (word == 0)
        return 0;
    return 1 + ((63 - __builtin_clzl(word)) ^ (BITS_PER_LONG - 1));
}


#endif /* CC_HELPER_FUNCTION_H */
