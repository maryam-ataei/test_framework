import os
import shutil
import argparse

def copy_file_if_exists(src, dest):
    """Copy the file from src to dest if it exists."""
    if os.path.isfile(src):
        shutil.copy(src, dest)
        print(f"Copied: {src} to {dest}")
    else:
        print(f"Warning: {src} does not exist.")

def generate_test_files(keyword):
    """Generate the test files by extracting the necessary files."""
    try:
        # Define the directory paths
        support_dir = 'support'  # Directory containing the source files
        test_dir = 'test_dir'  # Directory where we want to copy the test files

        # Ensure the test directory exists
        os.makedirs(test_dir, exist_ok=True)

        # Define the paths for the necessary files
        cc_helper_file = os.path.join(support_dir, 'cc_helper_function.h')
        test_file_keyword = os.path.join(support_dir, f'test_{keyword}.c')
        test_file_base = os.path.join(support_dir, 'test_base.c')

        # Copy cc_helper_function.h to the test_dir
        copy_file_if_exists(cc_helper_file, os.path.join(test_dir, 'cc_helper_function.h'))

        # Check if the test file with the keyword exists
        if os.path.isfile(test_file_keyword):
            # If the test file with the keyword exists, copy it
            copy_file_if_exists(test_file_keyword, os.path.join(test_dir, f'test_{keyword}.c'))
        else:
            # If the test file with the keyword does not exist, copy test_base.c
            copy_file_if_exists(test_file_base, os.path.join(test_dir, 'test_base.c'))
            print(f"Note: The test file test_{keyword}.c was not found. Please generate it manually based on test_base.c.")

    except Exception as e:
        print(f"Error: {e}")
        
def main():
    """Main function to handle command-line argument for keyword."""
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Generate test files from the support folder.")
    
    parser.add_argument("-k", "--keyword", required=True, help="The keyword used for generating test file (e.g., 'SEARCH').")

    # Parse arguments
    args = parser.parse_args()

    # Generate the necessary test files
    generate_test_files(args.keyword)

if __name__ == "__main__":
    main()

