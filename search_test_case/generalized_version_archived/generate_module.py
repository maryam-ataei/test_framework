import sys
import re
import os

def extract_and_modify_search_content(input_file, keyword, output_file):
    try:
        with open(input_file, 'r') as infile:
            content = infile.read()

        # Find all content enclosed by // SEARCH_begin and // SEARCH_end
        pattern = rf"// {keyword}_begin(.*?)// {keyword}_end"
        matches = re.findall(pattern, content, re.DOTALL)

        if not matches:
            print(f"No content found for keyword: {keyword}")
            return

        # Replacement mappings for type changes
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
            r'__read_mostly': ''

        }

        # Apply replacements to the matched content
        modified_content = ""
        for match in matches:
            modified = match
            for pattern, replacement in replacements.items():
                modified = re.sub(pattern, replacement, modified)
            modified_content += modified.strip() + '\n\n'

        # Create output directory if not exists
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Write the modified content to the output file
        with open(output_file, 'w') as outfile:
            # Add includes at the start of the file
            outfile.write('#include "tcp.h"\n')
            outfile.write('#include <string.h>\n')
            outfile.write('#include "search_defs.h"\n\n')

            # Write the modified content
            outfile.write(modified_content)

        print(f"SEARCH-related content written and modified in {output_file}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python generate_search_module.py <input_file> <keyword> <output_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    keyword = sys.argv[2]
    output_file = sys.argv[3]

    extract_and_modify_search_content(input_file, keyword, output_file)

