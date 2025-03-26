# #!/bin/bash

# output_file="files_with_passed_bin.txt"

# > "$output_file"

# # Loop through 100 output files
# for i in {1..100}; do
#     filename="output/output$i.txt"
    
#     # Check if the file exists
#     if [[ -f "$filename" ]]; then
#         # Search for "passed_bin" in the file
#         if grep -q "passed_bin" "$filename"; then
#             echo "$filename" >> "$output_file"
#         fi
#     fi
# done

# echo "Processing complete. Check $output_file for results."

#!/bin/bash

# Output file to store results
output_file="files_with_passed_bin_and_loss_0.txt"

# Clear the output file if it exists
> "$output_file"

# Loop through 100 output files
for i in {1..100}; do
    filename="output/output$i.txt"
    
    # Check if the file exists
    if [[ -f "$filename" ]]; then
        # Use awk to find "passed_bin" followed by "loss happen: 0"
        found_passed_bin=0
        found_loss_happen=0

        while IFS= read -r line; do
            if [[ "$line" == *"passed_bin"* ]]; then
                found_passed_bin=1  # Mark that "passed_bin" was found
            elif [[ "$line" == *"loss happen: 0"* && $found_passed_bin -eq 1 ]]; then
                found_loss_happen=1  # Mark that "loss happen: 0" appears after "passed_bin"
                echo "$filename" >> "$output_file"  # Save the filename
                break  # No need to check further, move to the next file
            fi
        done < "$filename"
    fi
done

echo "Processing complete. Check $output_file for results."
