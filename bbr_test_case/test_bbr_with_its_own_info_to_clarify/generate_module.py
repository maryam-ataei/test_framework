import sys
import re
import os
import datetime
import textwrap
from collections import defaultdict

def apply_replacements(content, replacements):
    """Apply type and attribute replacements to the content."""
    for pattern, replacement in replacements.items():
        content = re.sub(pattern, replacement, content)
    return content


def extract_function_declarations(module_content):
    """
    Extract function declarations from module content.
    :param module_content: The content of the module file.
    :return: A list of function declarations.
    """
    try:
        # Match function definitions and extract their declarations
        function_pattern = r"^[a-zA-Z_][a-zA-Z0-9_]*\s+\**[a-zA-Z_][a-zA-Z0-9_]*\([^)]*\)"

        matches = re.findall(function_pattern, module_content, re.MULTILINE)

        # Convert function definitions to declarations by adding 'extern' and a semicolon
        declarations = [f"extern {match.strip()};" for match in matches]
        return declarations

    except Exception as e:
        print(f"Error extracting function declarations: {e}")
        return []


def extract_marked_sections(input_file, keyword, marker_type):
    """
    Extract marked sections from the input file.
    :param input_file: The source file to process.
    :param keyword: The keyword identifying the protocol.
    :param marker_type: Either "module" or "defs" to identify the section.
    :return: Extracted content as a string.
    """
    try:
        with open(input_file, 'r') as infile:
            content = infile.read()

        # Identify the section markers
        if marker_type == "module":
            pattern = rf"// {keyword.upper()}_begin(.*?)// {keyword.upper()}_end"
        elif marker_type == "defs":
            pattern = rf"// {keyword.upper()}_defs_begin(.*?)// {keyword.upper()}_defs_end"
        else:
            raise ValueError(f"Unknown marker type: {marker_type}")

        matches = re.findall(pattern, content, re.DOTALL)
        if matches:
            return "".join(matches).strip()
        else:
            print(f"No content found for marker type: {marker_type}")
            return ""

    except Exception as e:
        print(f"Error extracting marked sections: {e}")
        return ""

def extract_structs_and_fields(module_content, module_defs_content):
    """
    Extracts structure definitions, field accesses, and macro mappings from the module content.
    - Identifies struct pointers (`struct sock *sk`).
    - Finds fields accessed through these pointers (`sk->field`).
    - Detects congestion control structures (`bictcp`, `bbr`, etc.).
    - Generates necessary macros (`tcp_sk(sk)`, `inet_csk_ca(sk)`).

    :param module_content: The content of the module file.
    :param module_defs_content: The content of the module_defs.h file.
    :return: Dictionary of structures and their accessed fields, plus detected macros, and CC structs.
    """
    try:
        # Extract structures from module_defs.h (already defined, ignore these for struct content)
        defined_structs = set(re.findall(r"struct\s+(\w+)\s*{", module_defs_content))

        # Dictionary to store struct fields
        struct_fields = {}

        # Dictionary to store detected macro relationships (e.g., `tcp_sk -> tcp_sock`)
        struct_macros = {}

        # Step 1: Detect struct pointers in function parameters (e.g., `struct sock *sk`)
        pointer_pattern = r"struct\s+(\w+)\s*\*\s*(\w+)"
        pointer_matches = re.findall(pointer_pattern, module_content)

        # Map pointer names to struct types (e.g., `sk` → `sock`)
        pointer_map = {ptr_name: struct_name for struct_name, ptr_name in pointer_matches if struct_name not in defined_structs}

        # Step 2: Find field accesses (e.g., `sk->field_name`, `tp->tcp_mstamp`)
        field_access_pattern = r"(\w+)\s*->\s*([\w]+)"
        field_matches = re.findall(field_access_pattern, module_content)

        # Step 3: Assign detected fields to their corresponding structures
        for pointer, field in field_matches:
            if pointer in pointer_map:  # Check if the pointer belongs to a known struct
                struct_name = pointer_map[pointer]
                if struct_name not in struct_fields:
                    struct_fields[struct_name] = set()
                struct_fields[struct_name].add(field)

        # Step 4: Detect congestion control structures (`bictcp`, `bbr`, etc.)
        cc_structs_used = set()
        cc_detection_pattern = r"struct\s+(\w+)\s*\*\s*\w+\s*=\s*inet_csk_ca\(\w+\);"
        cc_matches = re.findall(cc_detection_pattern, module_content)

        for cc_struct in cc_matches:
            if cc_struct in defined_structs:
                cc_structs_used.add(cc_struct)  # Only add if it is in module_defs.h

        # Step 5: Ensure `struct sock` contains both `tcp_sock` and the correct CC struct
        if "sock" not in struct_fields:
            struct_fields["sock"] = set()
        struct_fields["sock"].add("struct tcp_sock tcp_sock")  # Always needed

        for cc_struct in cc_structs_used:
            struct_fields["sock"].add(f"struct {cc_struct} *{cc_struct}")  # Dynamically add detected CC struct

        # Step 6: Detect implicit macro usages like `struct tcp_sock *tp = tcp_sk(sk);`
        implicit_macro_pattern = r"struct\s+(\w+)\s*\*\s*(\w+)\s*=\s*(\w+)\((\w+)\)"
        implicit_macro_matches = re.findall(implicit_macro_pattern, module_content)

        for struct_type, var_name, macro, macro_arg in implicit_macro_matches:
            if macro not in struct_macros:  # Ensure it's not already added
                struct_macros[macro] = struct_type

        # Step 7: Detect macro-based struct field accesses (e.g., `tcp_sk(sk)->tcp_mstamp`)
        for macro, struct_name in struct_macros.items():
            macro_access_pattern = rf"{macro}\(\w+\)\s*->\s*([\w]+)"
            macro_field_matches = re.findall(macro_access_pattern, module_content)

            # Add these fields to the corresponding struct
            for field in macro_field_matches:
                if struct_name in struct_fields:
                    struct_fields[struct_name].add(field)
                else:
                    struct_fields[struct_name] = {field}

        return struct_fields, struct_macros, cc_structs_used

    except Exception as e:
        print(f"Error extracting struct fields: {e}")
        return {}, {}, set()

def extract_test_details(module_content):
    """
    Extracts the required details to generate a test file from the given module content.
    It looks for:
    - The primary congestion control structure (e.g., bictcp, bbr, dctcp).
    - Key function calls that should be tested.
    """
    try:
        # Step 1: Detect primary congestion control structure (e.g., struct bbr, struct bictcp)
        struct_match = re.findall(r"struct\s+(\w+)\s*\*", module_content)
        congestion_control_struct = None

        for struct in struct_match:
            if struct.lower() not in ["sock", "tcp_sock", "inet_connection_sock"]:  # Ignore common structs
                congestion_control_struct = struct
                break  # Pick the first detected congestion control structure

        if not congestion_control_struct:
            raise ValueError("No congestion control structure (e.g., bictcp, bbr) found!")

        return congestion_control_struct

    except Exception as e:
        print(f"Error extracting test details: {e}")
        return None, None

############################################# TCP.H ###################################################################
def generate_tcp_h(module_file, module_defs_file, output_tcp_h="tcp.h"):
    """
    Generate the tcp.h file with a mock implementation of Linux kernel's TCP structures.
    - Automatically detects struct pointers and field accesses.
    - Ensures correct struct nesting (e.g., `sock` contains `tcp_sock`, `bictcp`, `bbr`, etc.).
    - Dynamically generates necessary macros based on actual usage.
    - Provides comments for users to manually add any undefined macros/functions.

    :param module_file: The module file to process.
    :param module_defs_file: The module_defs.h file to check for pre-defined structures.
    :param output_tcp_h: The output tcp.h file.
    """
    try:
        # Read the input files
        with open(module_file, 'r') as infile:
            module_content = infile.read()

        with open(module_defs_file, 'r') as defsfile:
            module_defs_content = defsfile.read()

        # Extract dynamically detected struct fields and macros
        extracted_fields, struct_macros, cc_structs_used = extract_structs_and_fields(module_content, module_defs_content)

        # Get current date and time
        current_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Header file content
        header_comment = textwrap.dedent(f"""\
            /*
             *****************************************************************************
             * Automatically Generated {output_tcp_h}
             * ----------------------------------
             * This file was automatically generated by the `generate_module.py` script
             * on {current_datetime}.
             *
             * It defines core TCP structures required for the test framework.
             * Note: This file does NOT include congestion control structures (e.g., bictcp, bbr).
             *
             * ⚠ WARNING: If you modify this file manually, be aware that rerunning
             * the `generate_module.py` script will overwrite any changes.
             * ✅ To customize the generated content, consider modifying `generate_module.py`.
             *****************************************************************************
            */
            """)

        include_guard = textwrap.dedent("""\
            #ifndef TCP_H
            #define TCP_H

            #include <stdint.h>
            #include "tcp_helper_function.h"
            """)

        tcp_needed_definitions = textwrap.dedent("""\
            #define TCP_INIT_CWND 10
            #define TCP_INFINITE_SSTHRESH   0x7fffffff
        """)

        # Step 1: Build Dependency Graph
        struct_dependencies = defaultdict(set)
        for struct_name, fields in extracted_fields.items():
            for field in fields:
                field_parts = field.split()
                if not field_parts:  # Skip empty or malformed fields
                    continue

                field_type = field_parts[0]  # Extract type
                if field_type.startswith("struct") and len(field_parts) > 1:
                    dep_struct = field_parts[1]  # Get actual struct name

                    # Ignore congestion control structures in dependency resolution
                    if dep_struct in cc_structs_used:
                        continue  

                    if dep_struct in extracted_fields:
                        struct_dependencies[struct_name].add(dep_struct)



        # Step 2: Topological Sort (Order Structs Based on Dependencies)
        sorted_structs = []
        visited = set()

        def visit(struct):
            """ Recursively visit dependencies and sort them correctly. """
            if struct in visited:
                return
            visited.add(struct)
            for dep in struct_dependencies[struct]:
                visit(dep)
            sorted_structs.append(struct)

        # Visit all structs in the extracted fields
        for struct in extracted_fields:
            visit(struct)

        # Step 3: Generate structure definitions dynamically
        struct_definitions = []
        for struct_name in sorted_structs:
            fields = extracted_fields[struct_name]
            struct_body = "\n".join([f"    u64 {field};" if " " not in field else f"    {field};" for field in fields])
            struct_definitions.append(f"struct {struct_name} {{\n{struct_body}\n}};\n")

        # Step 4: Generate detected macros dynamically
        macro_definitions = []
        for macro, struct_type in struct_macros.items():
            if struct_type in cc_structs_used:
                macro_definitions.append(f"#define {macro}(sk) ((sk->{struct_type}))")
            else:
                macro_definitions.append(f"#define {macro}(sk) (&(sk->{struct_type}))")

        footer = "\n#endif /* TCP_H */\n"

        # Combine everything into the final tcp.h content
        tcp_h_content = (
            header_comment + "\n" +
            include_guard + "\n" +
            tcp_needed_definitions + "\n" +
            "\n".join(struct_definitions) + "\n" +
            "\n".join(macro_definitions) + "\n" +
            footer
        )

        # Write to tcp.h
        with open(output_tcp_h, 'w') as outfile:
            outfile.write(tcp_h_content)

        print(f"Generated: {output_tcp_h}")

    except Exception as e:
        print(f"Error generating tcp.h: {e}")


############################################# TCP_HELPER_FUNCTION.H ###################################################################
def generate_tcp_helper():
    """
    Generate tcp_helper_function.h file with:
    - Kernel-style type definitions (u8, u16, s32, etc.)
    - Inline sequence number comparison functions
    """
    try:

        output_file="tcp_helper_function.h" 

        # Get current date and time
        current_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        header_comment = textwrap.dedent(f"""\
            /*
             *****************************************************************************
             * Automatically Generated Helper Functions
             * ----------------------------------------
             * The following macros and helper functions were automatically generated 
             * by the `generate_module.py` script on {current_datetime}. 
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
                """)

        include_guard = textwrap.dedent("""\
            #ifndef TCP_HELPER_FUNCTION_H
            #define TCP_HELPER_FUNCTION_H

            #include <stdint.h>
            #include <stdbool.h>
            #include <time.h>
        """)

        # Define kernel-style types
        typedefs = textwrap.dedent("""\
            typedef unsigned char        u8;
            typedef unsigned short       u16;
            typedef unsigned int         u32;
            typedef unsigned long long   u64;
            typedef signed char          s8;
            typedef short                s16;
            typedef int                  s32;
            typedef long long            s64;

        """)

        # Define sequence number helper functions
        helper_functions = textwrap.dedent("""\
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

            static inline u32 minmax_get(const struct minmax *m) {
                return (m->s[0].v > m->s[1].v) ? 
                        ((m->s[0].v > m->s[2].v) ? m->s[0].v : m->s[2].v) :
                        ((m->s[1].v > m->s[2].v) ? m->s[1].v : m->s[2].v);
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
                return 500; // Fake minimum RTT value (adjust if needed)
            }

        """)

        footer = "\n#endif /* TCP_HELPER_FUNCTION_H */\n"

        # Combine all parts
        file_content = (
            header_comment + "\n" +
            include_guard + "\n" +
            typedefs + "\n" +
            helper_functions + "\n" +
            footer
        )

        # Write to output file
        with open(output_file, "w") as outfile:
            outfile.write(file_content)

        print(f"Generated: {output_file}")

    except Exception as e:
        print(f"Error generating tcp_helper_function.h: {e}")

############################################# MODULE.C &  MODULE_DEFS.H ###################################################
def generate_files(input_file, keyword):
    """
    Generate the module, defs, and tcp.h files from the input file.
    :param input_file: The source file to process.
    :param keyword: The keyword identifying the protocol.
    """
    try:

        # Extract and process module content
        module_content = extract_marked_sections(input_file, keyword, "module")
        if module_content:
            # Apply replacements
            replacements = {
                r'static inline ': '',
                r'static ': '',
                r'__attribute__': '',
                r'__always_inline': '',
                r'__maybe_unused':'',
                r'__section__': '',
                r'__read_mostly': '',
            }

            module_content = apply_replacements(module_content, replacements)

            # Write to module file
            cwd = os.getcwd()
            module_file = os.path.join(cwd, f"{keyword}_module.c")

            # Get current date and time
            current_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Generate uppercase keyword
            keyword_upper = keyword.upper()

            with open(module_file, 'w') as outfile:
                # Write the header comment block
                header_comment = textwrap.dedent(f"""\
                    /*
                     *****************************************************************************
                     *  Automatically Generated {keyword}_module.c
                     *  ----------------------------------------------------------------------------
                     * This file was automatically generated by the `generate_module.py` script.
                     * It extracts the `{keyword_upper}_begin` to `{keyword_upper}_end` module section
                     * from the **source file**: `{input_file}` and was generated on {current_datetime}.
                     *
                     * This file is part of a test framework designed for evaluating TCP module implementations.
                     *  
                     *  ⚠ WARNING: 
                     * If you modify this file directly, rerunning `generate_module.py` will overwrite your changes.
                     *  
                     *  ✅ To prevent losing your modifications:
                     * - Modify the **source file** `{input_file}` instead.
                     *****************************************************************************
                    */
                    """)

                # Write the module content
                includes = textwrap.dedent(f"""\
                    #include <string.h>
                    #include "tcp.h"
                    #include "{keyword}_defs.h"
                    #include "tcp_helper_function.h"
        
                    """)

                # Write all components to the file
                outfile.write(header_comment + "\n" + includes + module_content)

            print(f"Generated: {f"{keyword}_module.c"}")

        # Extract and process defs content
        defs_content = extract_marked_sections(input_file, keyword, "defs")
        if defs_content:
            # Apply replacements
            replacements = {
                r'static inline ': '',
                r'static ': '',
                r'__read_mostly': '',
            }
            defs_content = apply_replacements(defs_content, replacements)
        if defs_content or module_content:
            # Extract function declarations from module content
            function_declarations = extract_function_declarations(module_content)

            # Write to defs file
            cwd = os.getcwd()
            defs_file = os.path.join(cwd, f"{keyword}_defs.h")

            with open(defs_file, 'w') as outfile:
                # Write the header comment block
                header_comment = textwrap.dedent(f"""\
                    /*
                     *****************************************************************************
                     *  Automatocally generated {keyword}_defs.h
                     *  ----------------------------------------------------------------------------
                     *  This header file was automatically generated by the `generate_module.py` script
                     *  on {current_datetime}.
                     *  It defines constants, structures, and function declarations for the {keyword_upper} module.
                     *
                     *  These contents are extracted automatically from the **source file**: `{input_file}`,
                     *  specifically from sections labeled `{keyword_upper}_DEFS`.
                     *  
                     *  ⚠ WARNING: 
                     *  If you modify this file directly, rerunning `generate_module.py` will overwrite your changes.
                     *  
                     *  ✅ To prevent losing your modifications:
                     *  You can only modify the **source file**.
                     *****************************************************************************
                     */
                    """)

                # Write include guards and headers
                include_guard = textwrap.dedent(f"""\
                    #ifndef {keyword_upper}_DEFS_H
                    #define {keyword_upper}_DEFS_H

                    #include <stdint.h>
                    #include <string.h>
                    #include "tcp.h"
                    #include "tcp_helper_function.h"

                    """)

                # Convert function declarations into a single formatted string
                function_declarations_str = "\n".join(function_declarations) + "\n" if function_declarations else ""

                # Write all components to the file
                outfile.write(header_comment + "\n" + include_guard + function_declarations_str)

                # Add any additional defs content
                if defs_content:
                    outfile.write("\n" + defs_content + "\n")

                outfile.write(f"\n#endif // {keyword.upper()}_DEFS_H\n")
            print(f"Generated: {f"{keyword}_defs.h"}")

        # Generate tcp.h
        generate_tcp_h(module_file,defs_file)

    except Exception as e:
        print(f"Error generating files: {e}")


############################################# TEST.C ###################################################################

def generate_test_file(module_file, keyword):
    """
    Generates a test C file based on extracted congestion control structures and function calls.
    """
    try:
        # Read module file content
        with open(module_file, "r") as infile:
            module_content = infile.read()

        # Extract congestion control structure and function calls
        congestion_control_struct = extract_test_details(module_content)
        if not congestion_control_struct:
            raise ValueError("Failed to extract necessary test details.")

        output_test_file= f"{keyword}_test.c"
        # Get current date and time
        current_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Generate the header comment
        header_comment = textwrap.dedent(f"""\
            /*
             *****************************************************************************
             *  Automatically Generated {output_test_file}
             *  ----------------------------------------------------------------------------
             *  This file was automatically generated by `generate_module.py` on {current_datetime}.
             *  It is designed to test the `{keyword.upper()}` module using CSV input.
             *  This test file allows you to validate and verify your module.
             * 
             *  You can process CSV input, simulate various network conditions, and print relevant results.
             *  Modify this file to adjust parameters, conditions, or outputs for custom testing.
             *  
             *
             *  ⚠ WARNING: 
             *  If you modify this file directly, rerunning `generate_module.py` will overwrite your changes.
             *
             *  ✅ To prevent losing your modifications:
             *  - Modify `generate_module.py` to include your changes.
             *  - Set `GENERATE_TEST_FILE = 0` in `generate_module.py` to disable regeneration.
             *****************************************************************************
             */
        """)

        # Generate test file content
        test_content = f"""\

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include "tcp.h"
#include "{keyword.lower()}_defs.h"
#include "tcp_helper_function.h"

int main(int argc, char *argv[]) {{
    if (argc < 2) {{
        fprintf(stderr, "Usage: %s <input.csv>\\n", argv[0]);
        return 1;
    }}

    // Open the CSV file
    FILE *file = fopen(argv[1], "r");
    if (!file) {{
        perror("Failed to open file");
        return 1;
    }}

    // Allocate memory for sock structure
    struct sock *sk = malloc(sizeof(struct sock));
    if (!sk) {{
        fprintf(stderr, "Failed to allocate memory for sock.\\n");
        fclose(file);
        return 1;
    }}
    memset(sk, 0, sizeof(struct sock));  // Initialize struct to zero

    // Allocate memory for {congestion_control_struct} inside sock
    sk->{congestion_control_struct} = malloc(sizeof(struct {congestion_control_struct}));
    if (!sk->{congestion_control_struct}) {{
        fprintf(stderr, "Failed to allocate memory for {congestion_control_struct}.\\n");
        free(sk);
        fclose(file);
        return 1;
    }}

    struct tcp_sock *tp = tcp_sk(sk);
    struct {congestion_control_struct} *bbr = inet_csk_ca(sk);

    // -----------------------------------------------------------------------------
    // ⚠ USER NOTE: Add your reset function below, if applicable.
    // Example: bictcp_search_reset(ca);
    // -----------------------------------------------------------------------------
    bbr_init(sk);            

    // Initialize protocol-specific variables
    tp->snd_ssthresh = TCP_INFINITE_SSTHRESH;
    tp->snd_cwnd = TCP_INIT_CWND;
    int EXIT_FLAG = 0;

    char line[256];
    int line_number = 0;

    printf("Processing CSV input: %s\\n\\n", argv[1]);

    while (fgets(line, sizeof(line), file)) {{
        line_number++;

        // Skip the header line or lines that start with '#'
        if (line_number == 1 || line[0] == '#') {{
            continue;
        }}

        // Variables to store parsed values
        // -----------------------------------------------------------------------------
        // ⚠ USER NOTE: Define the variables based on your protocol's input,
        // parse the CSV value, and set parsed values to the mock structure.
        // -----------------------------------------------------------------------------
                    
        // Variables to store parsed values
        u32 now_us, bbr_full_bw, bbr_full_bw_cnt, bbr_max_bw, round_start, app_limited, bbr_min_rtt, bbr_state; 

        // Parse CSV line with ONLY the required variables
        if (sscanf(line, "%u,%u,%u,%u,%u,%u, %u, %u",
                   &now_us, &bbr_full_bw, &bbr_full_bw_cnt, &bbr_max_bw, &round_start, &app_limited, &bbr_min_rtt, &bbr_state) != 8) {{
            fprintf(stderr, "Invalid line format at line %d: %s", line_number, line);
            continue;
        }}

        // Set mock BBR state
        bbr->round_start = round_start;

        // Set bbr_max_bw directly from input
        minmax_reset(&bbr->bw, 0, bbr_max_bw);

        // Create a mock rate sample structure
        struct rate_sample rs;
        memset(&rs, 0, sizeof(rs));
        rs.is_app_limited = app_limited;

        // Call protocol-specific update functions
        // -----------------------------------------------------------------------------
        // ⚠ USER NOTE: Call the function(s) to start running your protocol.
        // -----------------------------------------------------------------------------     
        // Check if BBR has exited the STARTUP phase
        bbr_check_full_bw_reached(sk, &rs);


        // -----------------------------------------------------------------------------
        // ⚠ USER NOTE: Print results and info based on your requirements.
        // -----------------------------------------------------------------------------

        if (bbr_full_bw_reached(sk) && EXIT_FLAG == 0) {{
            printf("BBR Exits STARTUP Phase at %u us\\n", now_us);
            EXIT_FLAG = 1;
        }}

        // Print details
        printf("Line %d:\\n", line_number);
        printf("  now_us: %u\\n", now_us);
        printf("  bbr_full_bw: %u\\n", bbr->full_bw);
        printf("  bbr_max_bw: %u\\n", bbr_max_bw);
        printf("  full_bw_cnt: %u\\n", bbr->full_bw_cnt);
        printf("  round_start: %u\\n", bbr->round_start);
        printf("  app_limited: %llu\\n", rs.is_app_limited);
        printf("  full_bw_reached: %s\\n", bbr_full_bw_reached(sk) ? "Yes" : "No");
        printf("  bbr_state: %u\\n", bbr_state);
        printf("\\n");
    }}
    // Clean up memory
    if (sk->bbr) {{
        free(sk->bbr);
    }}
    free(sk);
    fclose(file);

    printf("Finished processing.\\n");
    return 0;
}}
"""

        # Write the generated test file
        with open(output_test_file, "w") as outfile:
            outfile.write(header_comment + "\n" +test_content)

        print(f"Generated: {output_test_file}")

    except Exception as e:
        print(f"Error generating test file: {e}")


############################################# MAKEFILE ###################################################################
def generate_makefile(keyword ,output_file="Makefile"):
    """
    Generates a Makefile automatically based on the detected C source files.
    """
    try:
        executable_name=f"{keyword}_test"

        # Compiler and flags
        cc = "gcc"
        cflags = "-Wall -Wextra"

        # Get current date and time
        current_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Write the header comment block
        header_comment = textwrap.dedent(f"""\
        # *****************************************************************************
        # * Automatically Generated Makefile
        # * --------------------------------
        # * This Makefile was generated by the `generate_module.py` script 
        # * on {current_datetime}.
        # *
        # * ⚠ WARNING: 
        # * Any manual modifications may be overwritten if the script is run again.
        # *
        # * ✅ If you need to customize the build process, modify `generate_module.py`
        # * or create a separate custom Makefile that includes this one.
        # *****************************************************************************
        """ )

        # Construct the Makefile content
        makefile_content = f"""\
# Variables
CC = {cc}
CFLAGS = {cflags}
EXEC = {executable_name}
SRC = {keyword}_module.c {keyword}_test.c

# The default rule
all: $(EXEC)

# Rule to compile the program
$(EXEC): $(SRC)
\t$(CC) -o $(EXEC) $(SRC) $(CFLAGS)

# Clean up compiled files
clean:
\trm -f $(EXEC)

# Run the program
run: $(EXEC)
\t./$(EXEC)

.PHONY: all clean run
"""

        # Write the Makefile
        with open(output_file, "w") as f:
            f.write(header_comment+ "\n" + makefile_content)

        print(f"Generated: {output_file}")

    except Exception as e:
        print(f"Error generating Makefile: {e}")


############################################# MAIN ###################################################################
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python generate_module.py <input_file> <keyword>")
        sys.exit(1)

    input_file = sys.argv[1]
    keyword = sys.argv[2]

    '''
    * ---------------------- IMPORTANT ----------------------
    * Set the following flag to 0 if you want to keep your custom functions
    '''
    GENERATE_HELPER_FUNC = 1
    GENERATE_TEST_FILE = 1

    # Generate module, defs, and tcp.h files
    generate_files(input_file, keyword)
    if GENERATE_HELPER_FUNC == 1:
        # Run function to generate helping functions
        generate_tcp_helper()

    if GENERATE_TEST_FILE == 1:
        # Generate the test file
        generate_test_file(input_file, keyword)

    # Run the function to generate the Makefile
    generate_makefile(keyword)
