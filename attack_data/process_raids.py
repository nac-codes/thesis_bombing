import pandas as pd
import os

# Load the data
df = pd.read_csv('combined_attack_data_corrected.csv')
print("Available columns:", df.columns.tolist())

# Function to identify raids
def identify_raids(df):
    raids = []
    current_raid = []
    
    # Sort by location, target, date and time for proper sequencing
    sorted_df = df.sort_values(by=['target_location', 'target_name', 'YEAR', 'MONTH', 'DAY', 'TIME OF ATTACK'])
    
    for idx, row in sorted_df.iterrows():
        if not current_raid:
            current_raid.append(row)
            continue
            
        prev_row = current_raid[-1]
        
        # Check if this row belongs to the same raid (same location, target, and date)
        same_location = prev_row['target_location'] == row['target_location']
        same_target = prev_row['target_name'] == row['target_name']
        same_day = prev_row['DAY'] == row['DAY']
        same_month = prev_row['MONTH'] == row['MONTH']
        same_year = prev_row['YEAR'] == row['YEAR']
        
        if same_location and same_target and same_day and same_month and same_year:
            current_raid.append(row)
        else:
            raids.append(current_raid)
            current_raid = [row]
    
    # Add the last raid
    if current_raid:
        raids.append(current_raid)
    
    return raids

# Function to aggregate raid data
def aggregate_raid_data(raid_rows):
    first_row = raid_rows[0]
    
    # Get unique books for this raid
    books = set(row['book'] for row in raid_rows if pd.notna(row['book']))
    book_info = list(books)[0] if len(books) == 1 else list(books)
    
    result = {
        'target_location': first_row['target_location'],
        'target_name': first_row['target_name'],
        'BOOK': book_info,  # Add book information
        'latitude': first_row['latitude'],
        'longitude': first_row['longitude'],
        'target_code': first_row['target_code'],
        'DAY': first_row['DAY'],
        'MONTH': first_row['MONTH'],
        'YEAR': first_row['YEAR'],
        'TIME OF ATTACK': first_row['TIME OF ATTACK'],  # Using first attack time as reference
        'AIR FORCE': first_row['AIR FORCE'],
        # Sum of aircraft
        'TOTAL_AIRCRAFT': sum(row['NUMBER OF AIRCRAFT BOMBING'] for row in raid_rows if pd.notna(row['NUMBER OF AIRCRAFT BOMBING'])),
        # Average altitude
        'AVG_ALTITUDE': sum(row['ALTITUDE OF RELEASE IN HUND. FT.'] for row in raid_rows if pd.notna(row['ALTITUDE OF RELEASE IN HUND. FT.'])) / 
                        sum(1 for row in raid_rows if pd.notna(row['ALTITUDE OF RELEASE IN HUND. FT.'])) if any(pd.notna(row['ALTITUDE OF RELEASE IN HUND. FT.']) for row in raid_rows) else None,
        # Sum of high explosive bombs
        'TOTAL_HE_BOMBS': sum(row['HIGH EXPLOSIVE BOMBS NUMBER'] for row in raid_rows if pd.notna(row['HIGH EXPLOSIVE BOMBS NUMBER'])),
        'TOTAL_HE_TONS': sum(row['HIGH EXPLOSIVE BOMBS TONS'] for row in raid_rows if pd.notna(row['HIGH EXPLOSIVE BOMBS TONS'])),
        # Sum of incendiary bombs
        'TOTAL_INCENDIARY_BOMBS': sum(row['INCENDIARY BOMBS NUMBER'] for row in raid_rows if pd.notna(row['INCENDIARY BOMBS NUMBER'])),
        'TOTAL_INCENDIARY_TONS': sum(row['INCENDIARY BOMBS TONS'] for row in raid_rows if pd.notna(row['INCENDIARY BOMBS TONS'])),
        # Sum of fragmentation bombs
        'TOTAL_FRAG_BOMBS': sum(row['FRAGMENTATION BOMBS NUMBER'] for row in raid_rows if pd.notna(row['FRAGMENTATION BOMBS NUMBER'])),
        'TOTAL_FRAG_TONS': sum(row['FRAGMENTATION BOMBS TONS'] for row in raid_rows if pd.notna(row['FRAGMENTATION BOMBS TONS'])),
        # Total tonnage
        'TOTAL_TONS': sum(row['TOTAL TONS'] for row in raid_rows if pd.notna(row['TOTAL TONS'])),
        # Count of attacks in the raid
        'NUM_ATTACKS': len(raid_rows)
    }
    return result

# Main process
def process_raids():
    print("Loading and processing data...")
    raids = identify_raids(df)
    
    # Process each raid
    raid_summaries = [aggregate_raid_data(raid) for raid in raids]
    
    # Create a DataFrame from the raid summaries
    raids_df = pd.DataFrame(raid_summaries)
    
    # Create output directory if it doesn't exist
    os.makedirs('processed_data', exist_ok=True)
    
    # Save to CSV
    output_file = 'processed_data/raids_summary.csv'
    raids_df.to_csv(output_file, index=False)
    print(f"Raid summaries saved to {output_file}")
    print(f"Total raids identified: {len(raids_df)}")

if __name__ == "__main__":
    process_raids() 