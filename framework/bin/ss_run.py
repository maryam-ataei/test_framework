import os
import subprocess
import argparse

def run_test(executable, input_file, output_file):
    """Run the executable with input and redirect output to a file."""
    try:
        if not os.path.isfile(input_file):
            print(f"Error: {input_file} does not exist.")
            return

        # Run the executable with the input file and redirect the output
        with open(output_file, 'w') as out:
            subprocess.check_call([f"./{executable}", input_file], stdout=out)
        print(f"Test completed. Output written to {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error during test execution: {e}")

def process_input_files(input_folder, output_folder, keyword):
    """Process all .csv files in the input folder and generate output .txt files."""
    try:
        # Ensure the output directory exists
        os.makedirs(output_folder, exist_ok=True)

        # Check if the executable exists
        executable = f"test_dir/test_{keyword}"
        if not os.path.isfile(executable):
            print(f"Error: {executable} does not exist. Please compile the object file first.")
            return

        # Iterate through all files in the input folder
        for filename in os.listdir(input_folder):
            if filename.endswith(".csv"):
                input_file = os.path.join(input_folder, filename)
                output_file = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}.txt")

                # Run the test for each .csv file
                run_test(executable, input_file, output_file)

    except Exception as e:
        print(f"Error processing files: {e}")

def main():
    """Main function to handle command-line argument parsing."""
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Run tests for all .csv files in the input folder.")
    parser.add_argument("keyword", help="The keyword used for the test (e.g., 'SEARCH').")
    parser.add_argument("input_folder", help="The folder containing the input .csv files.")
    parser.add_argument("output_folder", help="The folder to save the output .txt files.")
    
    args = parser.parse_args()

    keyword = args.keyword
    input_folder = args.input_folder
    output_folder = args.output_folder

    # Process the input files and generate output files
    process_input_files(input_folder, output_folder, keyword)

if __name__ == "__main__":
    main()
