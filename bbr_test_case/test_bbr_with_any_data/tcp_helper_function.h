/*
 *****************************************************************************
 * Automatically Generated Helper Functions
 * ----------------------------------------
 * The following macros and helper functions were automatically generated 
 * by the `generate_module.py` script on 2025-02-20 12:34:30. 
 *
 * ⚠ WARNING: If you need to add new helper functions specific to your protocol, 
 * define them below. However, rerunning `generate_module.py` will overwrite 
 * this section unless you disable automatic regeneration.
 *
 * ✅ To preserve custom additions, set the `GENERATE_HELPER_FUNC` flag to 0 
 * in `generate_module.py` before rerunning the script.
 * Alternatively, you can modify `generate_module.py` to include your 
 * custom functions directly in the generated output.
 *****************************************************************************
 */

#ifndef TCP_HELPER_FUNCTION_H
#define TCP_HELPER_FUNCTION_H

#include <stdint.h>
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


#define SK_PACING_NONE 0
#define SK_PACING_NEEDED 1
#define TCP_CA_Open 0

#define before(seq1, seq2)    ((s32)((seq1) - (seq2)) < 0)
#define before_eq(seq1, seq2) ((s32)((seq1) - (seq2)) <= 0)
#define after(seq1, seq2)     ((s32)((seq1) - (seq2)) > 0)
#define after_eq(seq1, seq2)  ((s32)((seq1) - (seq2)) >= 0)

#define min(x, y) ((x) < (y) ? (x) : (y))
#define max(x, y) ((x) > (y) ? (x) : (y))
#define min_t(type, x, y) ((type)(x) < (type)(y) ? (type)(x) : (type)(y))

/* Safe inline function for division */
static inline u64 div_u64(u64 dividend, u32 divisor) {
    return dividend / divisor;
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

/* Parameters used to convert time values */
#define MSEC_PER_SEC    1000L
#define USEC_PER_MSEC   1000L
#define NSEC_PER_USEC   1000L
#define NSEC_PER_MSEC   1000000L
#define USEC_PER_SEC    1000000L
#define NSEC_PER_SEC    1000000000L
#define FSEC_PER_SEC    1000000000000000LL


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
static inline u32 tcp_min_rtt(const struct tcp_sock *tp) {
    (void)tp; // Prevents "unused parameter" warnings
    return 600; // Fake minimum RTT value (adjust if needed)
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
        m->s[2] = m->s[1]; // Shift s[1] to s[2]
        m->s[1] = val; // Place the new sample in s[1]
    } else if (sample >= m->s[2].v) {
        m->s[2] = val; // Place the new sample in s[2]
    }

    return minmax_subwin_update(m, win, &val);
}




#endif /* TCP_HELPER_FUNCTION_H */
