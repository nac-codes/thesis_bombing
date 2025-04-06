import csv
import os

input_file = 'combined_attack_data_filled.csv'
output_file = 'combined_attack_data_corrected.csv'

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
        
        # Check if YEAR field (index 10) is empty
        if len(row) > 10 and (row[10].strip() == "" or row[10].strip() == "."):
            row[10] = "0"
        
        # Write the updated row
        writer.writerow(row)

print(f"Processing complete. Output saved to {output_file}") 