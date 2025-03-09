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


############################################# TCP.H ###################################################################
def generate_tcp_h(module_file, module_defs_file):
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

        cwd = os.getcwd()
        dir_path = os.path.join(cwd, 'test_dir')
        os.makedirs(dir_path, exist_ok=True)
        output_tcp_h=os.path.join(dir_path,"tcp.h")

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
            #include "cc_helper_function.h"
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

        print(f"Generated: tcp.h")

    except Exception as e:
        print(f"Error generating tcp.h: {e}")

############################################# MODULE.C &  MODULE_DEFS.H ###################################################
def generate_files(input_file, keyword):
    """
    Generate the module, defs, and tcp.h files from the input file.
    :param input_file: The source file to process.
    :param keyword: The keyword identifying the protocol.
    """
    try:

        cwd = os.getcwd()
        dir_path = os.path.join(cwd, 'test_dir')
        os.makedirs(dir_path, exist_ok=True)

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
            module_file = os.path.join(dir_path, f"{keyword}_module.c")

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
                    #include "cc_helper_function.h"
        
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
            defs_file = os.path.join(dir_path, f"{keyword}_defs.h")

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
                    #include "cc_helper_function.h"

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

############################################# MAKEFILE ###################################################################
def generate_makefile(keyword):
    """
    Generates a Makefile automatically based on the detected C source files.
    """
    try:
        cwd = os.getcwd()
        dir_path = os.path.join(cwd, 'test_dir')
        os.makedirs(dir_path, exist_ok=True)
        output_file=os.path.join(dir_path,"Makefile")

        executable_name=f"test_{keyword}"

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
SRC = {keyword}_module.c test_{keyword}.c

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

        print(f"Generated: Makefile")

    except Exception as e:
        print(f"Error generating Makefile: {e}")


############################################# MAIN ###################################################################
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python generate_module.py <input_file> <keyword>")
        sys.exit(1)

    input_file = sys.argv[1]
    keyword = sys.argv[2]

    # Generate module, defs, and tcp.h files
    generate_files(input_file, keyword)

    # Run the function to generate the Makefile
    generate_makefile(keyword)
