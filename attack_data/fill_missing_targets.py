import csv
import os

input_file = 'combined_attack_data_checked.csv'
output_file = 'combined_attack_data_filled.csv'

# Initialize variables to store previous non-empty target values
prev_target_location = ""
prev_target_name = ""

# Read input file and write to output file
with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8', newline='') as outfile:
    reader = csv.reader(infile)
    writer = csv.writer(outfile)
    
    # Process each row
    for i, row in enumerate(reader):
        # Save header row
        if i == 0:
            writer.writerow(row)
            continue
        
        # Check if target_location (index 3) is empty
        if row[3].strip() == "":
            # If the current row has target_name but not target_location
            if row[4].strip() != "":
                # Update previous target_name
                prev_target_name = row[4]
                # Use previous target_location
                row[3] = prev_target_location
            else:
                # Both fields are empty
                row[3] = prev_target_location
                row[4] = prev_target_name
        # Check if target_name (index 4) is empty but target_location is not
        elif row[4].strip() == "":
            # Update previous target_location
            prev_target_location = row[3]
            # Use previous target_name
            row[4] = prev_target_name
        else:
            # Both fields have values, update previous values
            prev_target_location = row[3]
            prev_target_name = row[4]
        
        # Write the updated row
        writer.writerow(row)

print(f"Processing complete. Output saved to {output_file}") 