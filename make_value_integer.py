import pandas as pd

# Load the CSV file
data = pd.read_csv("data_sample_viasat.csv")

# Convert 'now_us' to integers
data["now_us"] = data["now_us"].astype(int)

# Save the modified CSV
data.to_csv("data_sample_viasat_fixed.csv", index=False)

