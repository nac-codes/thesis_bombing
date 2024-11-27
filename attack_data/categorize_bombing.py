import pandas as pd
from datetime import timedelta
import logging

logging.basicConfig(level=logging.INFO)

def categorize_mission(row, df, time_window_hours=4):
    """
    Categorize a mission as either 'area' or 'precision' bombing based on:
    1. If the mission itself used incendiaries
    2. If any other mission at the same target within the time window used incendiaries
    """
    # get row index
    row_idx = row.name
    if row_idx % 100 == 0:
        logging.info(f"Processing row {row_idx} of {len(df)}")

    box = row['box']
    book = row['book']
    image = row['image']
    mission_time = pd.to_datetime(row['DATETIME'])
    
    # First check if this mission used incendiaries
    if row['INCENDIARY BOMBS NUMBER'] > 0:
        return 'area'
    
    # Check other missions at the same target within the time window
    time_window_start = mission_time - timedelta(hours=time_window_hours)
    time_window_end = mission_time + timedelta(hours=time_window_hours)
    
    # Filter missions at same target within time window
    related_missions = df[
        (df['box'] == box) &
        (df['book'] == book) &
        (df['image'] == image) &
        (pd.to_datetime(df['DATETIME']) >= time_window_start) &
        (pd.to_datetime(df['DATETIME']) <= time_window_end)
    ]
    
    # If any related mission used incendiaries, categorize as area bombing
    if (related_missions['INCENDIARY BOMBS NUMBER'] > 0).any():
        return 'area'
    
    # If we get here, it's precision bombing
    return 'precision'

def main():
    # Read the cleaned data
    logging.info("Reading cleaned data...")
    df = pd.read_csv('combined_attack_data_cleaned.csv')
    
    # Ensure datetime column is properly formatted
    df['DATETIME'] = pd.to_datetime(df['DATETIME'])
    
    # Add bombing type categorization
    logging.info("Categorizing bombing missions...")
    df['bombing_type'] = df.apply(lambda row: categorize_mission(row, df), axis=1)
    
    # Save the dataframe with the bombing type
    df.to_csv('combined_attack_data_bombing_type.csv', index=False)

    # Create summary statistics
    logging.info("Generating summary statistics...")
    
    # By bombing type
    type_summary = df['bombing_type'].value_counts()
    print("\nBombing Type Summary:")
    print(type_summary)
    
    # By year
    df['year'] = df['DATETIME'].dt.year
    year_type_summary = pd.crosstab(df['year'], df['bombing_type'])
    print("\nBombing Type by Year:")
    print(year_type_summary)

if __name__ == "__main__":
    main()