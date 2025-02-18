/*
 *****************************************************************************
 * Automatically Generated Helper Functions
 * ----------------------------------------
 * The following macros and helper functions were automatically generated 
 * by the `generate_module.py` script on 2025-02-12 15:25:27. 
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

typedef unsigned char        u8;
typedef unsigned short       u16;
typedef unsigned int         u32;
typedef unsigned long long   u64;
typedef signed char          s8;
typedef short                s16;
typedef int                  s32;
typedef long long            s64;


#define before(seq1, seq2)    ((s32)((seq1) - (seq2)) < 0)

#define before_eq(seq1, seq2) ((s32)((seq1) - (seq2)) <= 0)

#define after(seq1, seq2)     ((s32)((seq1) - (seq2)) > 0)

#define after_eq(seq1, seq2)  ((s32)((seq1) - (seq2)) >= 0)

#define max(x, y) ((x) > (y) ? (x) : (y))



#endif /* TCP_HELPER_FUNCTION_H */
