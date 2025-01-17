import sys
import re
import os


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

        # Convert function definitions to declarations by appending a semicolon
        declarations = [f"{match.strip()};" for match in matches]
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


def extract_tp_fields(module_content):
    """
    Extract fields accessed from struct tcp_sock (via tp->) in the module content.
    :param module_content: The content of the module file.
    :return: List of fields from struct tcp_sock.
    """
    try:
        # Regex pattern to find instances of tp->field or tcp_sk(sk)->field
        tp_pattern = r"(?:tp|tcp_sk\(sk\))->(\w+)"
        fields = re.findall(tp_pattern, module_content)

        # Remove duplicates and return the list of fields
        return list(set(fields))

    except Exception as e:
        print(f"Error extracting tp->fields: {e}")
        return []


def extract_tcp_sock_fields(module_content):
    """
    Extract the fields used in struct tcp_sock from the module content.
    :param module_content: The content of the module file.
    :return: List of fields accessed from struct tcp_sock.
    """
    try:
        # Find the fields accessed through tp->, i.e., fields used in functions
        fields = extract_tp_fields(module_content)
        return fields

    except Exception as e:
        print(f"Error extracting tcp_sock fields: {e}")
        return []


def generate_tcp_h(input_file, keyword):
    """
    Generate the tcp.h file with mock implementation of Linux kernel's sock structure.
    :param input_file: The source file to process.
    :param keyword: The keyword identifying the protocol.
    """
    try:
        # Read the input file to check for the structures used in search_module.c
        with open(input_file, 'r') as infile:
            content = infile.read()

        # Extract fields from struct tcp_sock
        tcp_sock_fields = extract_tcp_sock_fields(content)

        # Build the tcp_sock structure dynamically
        tcp_sock_structure = "/** Mock implementation of the Linux kernel's tcp_sock structure */\nstruct tcp_sock {\n"
        for field in tcp_sock_fields:
            tcp_sock_structure += f"    uint32_t {field}; // Simulated {field}\n"
        tcp_sock_structure += "};\n"

        # Build the sock structure dynamically
        sock_structure = "/** Mock implementation of the Linux kernel's sock structure */\nstruct sock {\n"
        sock_structure += "    struct bictcp *bictcp;\n"
        sock_structure += "    struct tcp_sock tcp_sock;\n"
        sock_structure += "};\n"

        # Generate mock functions like tcp_sk and inet_csk_ca based on existing usage
        mock_functions = """
/* Mock functions to simulate Linux kernel behavior */
#define tcp_sk(sk) (&(sk->tcp_sock))
#define inet_csk_ca(sk) ((sk)->bictcp)

#ifndef max
#define max(a, b) ((a) > (b) ? (a) : (b))
#endif
"""

        # Create output directory if not exists
        # os.makedirs(output_dir, exist_ok=True)

        # Write to tcp.h
        cwd = os.getcwd()
        tcp_h_file = os.path.join(cwd, f"tcp.h")
        with open(tcp_h_file, 'w') as outfile:
            outfile.write("#ifndef TCP_H\n#define TCP_H\n\n")
            outfile.write("#include <stdint.h>\n\n")
            outfile.write("#define TCP_INIT_CWND 10\n")
            outfile.write("#define TCP_INFINITE_SSTHRESH   0x7fffffff\n\n")

            # Write structures and mock functions
            outfile.write(tcp_sock_structure)
            outfile.write(sock_structure)
            outfile.write(mock_functions)

            # Provide a comment for the user to add any additional functions or structures
            outfile.write("\n// If additional functions or structures are needed, add them here.\n")

            outfile.write("\n#endif // TCP_H\n")

        print(f"Generated: {tcp_h_file}")

    except Exception as e:
        print(f"Error generating tcp.h file: {e}")


def generate_files(input_file, keyword):
    """
    Generate the module, defs, and tcp.h files from the input file.
    :param input_file: The source file to process.
    :param keyword: The keyword identifying the protocol.
    """
    try:
        # Create output directory if not exists
        # os.makedirs(output_dir, exist_ok=True)

        # Extract and process module content
        module_content = extract_marked_sections(input_file, keyword, "module")
        if module_content:
            # Apply replacements
            replacements = {
                r'\bu8\b': 'uint8_t',
                r'\bu16\b': 'uint16_t',
                r'\bu32\b': 'uint32_t',
                r'\bu64\b': 'uint64_t',
                r'\bs32\b': 'int32_t',
                r'\bint\b': 'int32_t',
                r'static inline ': '',
                r'static ': '',
                r'const ': '',
                r'__read_mostly': '',
            }
            module_content = apply_replacements(module_content, replacements)

            # Write to module file
            cwd = os.getcwd()
            module_file = os.path.join(cwd, f"{keyword}_module.c")
            with open(module_file, 'w') as outfile:
                outfile.write('#include "tcp.h"\n')
                outfile.write('#include <string.h>\n')
                outfile.write(f'#include "{keyword}_defs.h"\n\n')
                outfile.write(module_content)
            print(f"Generated: {module_file}")

        # Extract and process defs content
        defs_content = extract_marked_sections(input_file, keyword, "defs")
        if defs_content:
            # Apply replacements
            replacements = {
                r'\bu8\b': 'uint8_t',
                r'\bu16\b': 'uint16_t',
                r'\bu32\b': 'uint32_t',
                r'\bu64\b': 'uint64_t',
                r'\bs32\b': 'int32_t',
                r'\bint\b': 'int32_t',
                r'static inline ': '',
                r'static ': '',
                r'const ': '',
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
                outfile.write(f"#ifndef {keyword.upper()}_DEFS_H\n")
                outfile.write(f"#define {keyword.upper()}_DEFS_H\n\n")
                outfile.write("#include <stdint.h>\n#include <string.h>\n#include \"tcp.h\"\n\n")

                # Add function declarations
                for declaration in function_declarations:
                    outfile.write(declaration + "\n")

                # Add any additional defs content
                if defs_content:
                    outfile.write("\n" + defs_content + "\n")

                outfile.write(f"\n#endif // {keyword.upper()}_DEFS_H\n")
            print(f"Generated: {defs_file}")

        # Generate tcp.h
        generate_tcp_h(input_file, keyword)

    except Exception as e:
        print(f"Error generating files: {e}")

def extract_tcp_sock_fields_for_test(module_content):
    """
    Extract fields from struct tcp_sock in the module content.
    :param module_content: The content of the module file.
    :return: List of fields from struct tcp_sock.
    """
    try:
        # Regex to find struct tcp_sock and its fields
        tcp_sock_pattern = r"struct tcp_sock\s*{(.*?)};"
        match = re.search(tcp_sock_pattern, module_content, re.DOTALL)
        
        if not match:
            return []

        # Extract fields inside the struct
        fields = re.findall(r"\s*(\w+)\s*;", match.group(1))
        return fields

    except Exception as e:
        print(f"Error extracting tcp_sock fields: {e}")
        return []


def extract_bictcp_fields_for_test(module_content):
    """
    Extract fields from struct bictcp in the module content.
    :param module_content: The content of the module file.
    :return: List of fields from struct bictcp.
    """
    try:
        # Regex to find struct bictcp and its fields
        bictcp_pattern = r"struct bictcp\s*{(.*?)};"
        match = re.search(bictcp_pattern, module_content, re.DOTALL)
        
        if not match:
            return []

        # Extract fields inside the struct
        fields = re.findall(r"\s*(\w+)\s*;", match.group(1))
        return fields

    except Exception as e:
        print(f"Error extracting bictcp fields: {e}")
        return []


def generate_test_file(input_file, keyword):
    """
    Generate a test file that reads a CSV, initializes mock structures,
    and calls the appropriate protocol functions.
    :param input_file: The source file to process.
    :param keyword: The keyword identifying the protocol.
    """
    try:
        # Read the input file to check for the structures used in search_module.c
        with open(input_file, 'r') as infile:
            content = infile.read()

        # Extract fields from struct tcp_sock and struct bictcp
        tcp_sock_fields = extract_tcp_sock_fields_for_test(content)
        bictcp_fields = extract_bictcp_fields_for_test(content)

        # Build the tcp_sock structure dynamically
        tcp_sock_structure = "/** Mock implementation of the Linux kernel's tcp_sock structure */\nstruct tcp_sock {\n"
        for field in tcp_sock_fields:
            tcp_sock_structure += f"    uint32_t {field}; // Simulated {field}\n"
        tcp_sock_structure += "};\n"

        # Build the bictcp structure dynamically
        bictcp_structure = "/** Mock implementation of the Linux kernel's bictcp structure */\nstruct bictcp {\n"
        for field in bictcp_fields:
            bictcp_structure += f"    uint32_t {field}; // Simulated {field}\n"
        bictcp_structure += "};\n"

        # Create output directory if not exists
        # os.makedirs(output_dir, exist_ok=True)

        # Write to test file
        cwd = os.getcwd()
        test_file_path = os.path.join(cwd, f"{keyword}_test.c")
        with open(test_file_path, 'w') as outfile:
            outfile.write("#include <stdio.h>\n")
            outfile.write("#include <stdlib.h>\n")
            outfile.write("#include <stdint.h>\n")
            outfile.write("#include <string.h>\n")
            outfile.write(f"#include \"{keyword}.h\"\n")
            outfile.write(f"#include \"{keyword}_defs.h\"\n\n")

            # Write the mock structure initialization code dynamically
            outfile.write("""
int main(int argc, char *argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <input.csv>\\n", argv[0]);
        return 1;
    }

    // Open the CSV file
    FILE *file = fopen(argv[1], "r");
    if (!file) {
        perror("Failed to open file");
        return 1;
    }

    // Initialize the mock structure
    struct sock sk = {0};
    struct sock *sk_ptr = &sk;

    // Allocate memory for bictcp
    sk_ptr->bictcp = malloc(sizeof(struct bictcp));
    if (!sk_ptr->bictcp) {
        fprintf(stderr, "Failed to allocate memory for bictcp.\\n");
        fclose(file);
        return 1;
    }

    struct tcp_sock *tp = tcp_sk(sk_ptr);
    struct bictcp *ca = inet_csk_ca(sk_ptr);

    // NEED UPDATE: Call reset function of the protocol here, if needed
    // Example: bictcp_search_reset(ca);

    char line[256];
    int line_number = 0;

    printf("Processing CSV input: %s\\n\\n", argv[1]);

    while (fgets(line, sizeof(line), file)) {
        line_number++;

        // Skip the header line
        if (line_number == 1) {
            continue;
        }

        // NEED UPDATE: Variables to store parsed values
        //For example
        // uint32_t now_us, mss, rtt_us;
        // uint64_t bytes_acked;

        // NEED UPDATE: Parse the CSV line
        // if (sscanf(line, "%u,%lu,%u,%u", &now_us, &bytes_acked, &mss, &rtt_us) != 4) {
        //     fprintf(stderr, "Invalid line format at line %d: %s", line_number, line);
        //     continue;
        // }

        // NEED UPDATE: Set parsed values to the mock structure
        // tp->tcp_mstamp = now_us;
        // tp->bytes_acked = bytes_acked;
        // tp->mss_cache = mss;

        // NEED UPDATE: Call the function or the relevant function for the running protocol
        // Example: search_update(sk_ptr, rtt_us);

        // NEED UPDATE:Print debug information
        // Example:
        // printf("Line %d:\\n", line_number);
        // printf("  now_us: %u\\n", now_us);
        // printf("  bytes_acked: %lu\\n", bytes_acked);
        // printf("  mss: %u\\n", mss);
        // printf("  rtt_us: %u\\n", rtt_us);
        // printf("  Current bin index: %d\\n", ca->search.curr_idx);
        // printf("  Bin values:\\n");
        // for (int i = 0; i < SEARCH_TOTAL_BINS; i++) {
        //     printf("    Bin[%d]: %u\\n", i, ca->search.bin[i]);
        // }
        // printf("\\n");
    }

    // Clean up
    free(sk_ptr->bictcp);
    fclose(file);

    printf("Finished processing.\\n");
    return 0;
}
""")

            # Provide a comment for user to add desired function
            outfile.write("\n// Add function call for the desired protocol, e.g., search_update(sk_ptr, rtt_us);\n")

        print(f"Generated: {test_file_path}")

    except Exception as e:
        print(f"Error generating test file: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python generate_module.py <input_file> <keyword>")
        sys.exit(1)

    input_file = sys.argv[1]
    keyword = sys.argv[2]
    # output_dir = sys.argv[3]

    # Generate module, defs, and tcp.h files
    generate_files(input_file, keyword)

    # Generate the test file
    # generate_test_file(input_file, keyword)
