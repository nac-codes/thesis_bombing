import pandas as pd
import os
import re

def organize_by_location():
    print("Loading data...")
    df = pd.read_csv('combined_attack_data_corrected.csv')
    
    # Create locations directory if it doesn't exist
    locations_dir = 'locations'
    os.makedirs(locations_dir, exist_ok=True)
    
    # Process each unique location
    locations = df['target_location'].unique()
    print(f"Found {len(locations)} unique target locations")
    
    for location in locations:
        if pd.isna(location):
            continue
            
        # Process location name (fix capitalization)
        clean_location = location.strip()
        # Title case the location (make first letter of each word capital)
        clean_location = ' '.join(word.capitalize() for word in clean_location.split())
        
        # Create safe filename
        safe_filename = re.sub(r'[^\w\s-]', '', clean_location).strip().replace(' ', '_')
        output_file = os.path.join(locations_dir, f"{safe_filename}.csv")
        
        # Get all data for this location
        location_data = df[df['target_location'] == location].copy()
        
        # Sort by date and time
        location_data = location_data.sort_values(by=['YEAR', 'MONTH', 'DAY', 'TIME OF ATTACK'])
        
        # Save to CSV
        location_data.to_csv(output_file, index=False)
        print(f"Saved data for {clean_location} to {output_file}")
    
    print("Location data organization complete!")

if __name__ == "__main__":
    organize_by_location() 