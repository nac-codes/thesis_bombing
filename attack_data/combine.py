import os
import pandas as pd
import json
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', filename='combine.log', filemode='w')
logger = logging.getLogger(__name__)

def process_files(base_path):
    # Initialize lists to store data and tracking information
    all_data = []
    all_data_simplified = []
    empty_table_files = []
    previous_metadata = None
    
    # Walk through the directory structure
    for box_dir in sorted(os.listdir(base_path)):
        if not box_dir.startswith('BOX_'):
            continue
            
        box_path = os.path.join(base_path, box_dir)
        for book_dir in sorted(os.listdir(box_path)):
            if not book_dir.startswith('BOOK_'):
                continue
                
            book_path = os.path.join(box_path, book_dir)
            for img_dir in sorted(os.listdir(book_path)):
                if not img_dir.endswith('_output'):
                    continue
                    
                img_output_path = os.path.join(book_path, img_dir)
                
                # Skip if no_table.txt exists
                if os.path.exists(os.path.join(img_output_path, 'no_table.txt')):
                    logger.info(f"Skipping {img_output_path} - no table marker found")
                    continue
                
                # Process the files
                try:
                    complete_data, simplified_data = process_image_output(
                        img_output_path, 
                        box_dir, 
                        book_dir, 
                        previous_metadata,
                        empty_table_files
                    )
                    
                    if complete_data:
                        all_data.extend(complete_data)
                        all_data_simplified.extend(simplified_data)
                        # Update previous_metadata if we found valid metadata
                        if complete_data[0].get('target_location') != 'NA':
                            previous_metadata = {
                                'target_location': complete_data[0]['target_location'],
                                'target_name': complete_data[0]['target_name'],
                                'latitude': complete_data[0]['latitude'],
                                'longitude': complete_data[0]['longitude'],
                                'target_code': complete_data[0]['target_code']
                            }
                except Exception as e:
                    logger.error(f"Error processing {img_output_path}: {str(e)}")
                    continue

    # Create final DataFrames
    df_complete = pd.DataFrame(all_data)
    df_simplified = pd.DataFrame(all_data_simplified)
    
    # Log empty table files
    if empty_table_files:
        logger.warning("Files with tables but no values:")
        for file in empty_table_files:
            logger.warning(f"  {file}")
    
    return df_complete, df_simplified

def process_image_output(img_path, box_dir, book_dir, previous_metadata, empty_table_files):
    # Read metadata from extracted_data.json
    json_path = os.path.join(img_path, 'extracted_data.json')
    if not os.path.exists(json_path):
        logger.warning(f"No extracted_data.json found in {img_path}")
        return None, None
        
    with open(json_path, 'r') as f:
        extracted_data = json.load(f)
    
    # Get metadata
    metadata = extracted_data.get('metadata', {})
    current_metadata = {
        'target_location': metadata.get('Target Location', 'NA'),
        'target_name': metadata.get('Target Name', 'NA'),
        'latitude': metadata.get('Latitude', 'NA'),
        'longitude': metadata.get('Longitude', 'NA'),
        'target_code': metadata.get('Target Code', 'NA')
    }
    
    # Use previous metadata if current is all NA
    if all(v == 'NA' for v in current_metadata.values()) and previous_metadata:
        current_metadata = previous_metadata
    
    # Read CSV data
    csv_path = os.path.join(img_path, 'table_data_final.csv')
    if not os.path.exists(csv_path):
        logger.warning(f"No table_data_final.csv found in {img_path}")
        return None, None
        
    df = pd.read_csv(csv_path)
    
    # Skip if no valid rows
    if len(df) == 0 or (df['SUMMATION_ROW'] == True).all():
        empty_table_files.append(img_path)
        logger.warning(f"Skipping {img_path} - no valid rows")
        return None, None
    
    # Process each non-summation row
    complete_results = []
    simplified_results = []
    
    for index, row in df[df['SUMMATION_ROW'] == False].iterrows():
        # Process bomb data
        has_he_bombs = not pd.isna(row['HIGH EXPLOSIVE BOMBS NUMBER']) and row['HIGH EXPLOSIVE BOMBS NUMBER'] != 0 and row['HIGH EXPLOSIVE BOMBS NUMBER'] != ''
        has_incendiary_bombs = not pd.isna(row['INCENDIARY BOMBS NUMBER']) and row['INCENDIARY BOMBS NUMBER'] != 0 and row['INCENDIARY BOMBS NUMBER'] != ''
        has_fragmentation_bombs = not pd.isna(row['FRAGMENTATION BOMBS NUMBER']) and row['FRAGMENTATION BOMBS NUMBER'] != 0 and row['FRAGMENTATION BOMBS NUMBER'] != ''
        
        if not has_he_bombs and not has_incendiary_bombs and not has_fragmentation_bombs:
            continue

        # Complete dataset
        complete_result = {
            'box': box_dir,
            'book': book_dir,
            'image': os.path.basename(img_path),
            **current_metadata,
            **row.to_dict()  # Include all columns from the CSV
        }
        complete_results.append(complete_result)

        # Simplified dataset
        simplified_result = {
            'box': box_dir,
            'book': book_dir,
            'image': os.path.basename(img_path),
            'target_location': current_metadata['target_location'],
            'target_name': current_metadata['target_name'],
            'day': row['DAY'],
            'month': row['MONTH'],
            'year': row['YEAR'],
            'air_force': row['AIR FORCE'],
            'has_he_bombs': has_he_bombs,
            'has_incendiary_bombs': has_incendiary_bombs,
            'has_fragmentation_bombs': has_fragmentation_bombs
        }
        simplified_results.append(simplified_result)
    
    return complete_results, simplified_results

if __name__ == "__main__":
    base_path = "/Users/chim/Working/Thesis/Attack_Images/BOXES"
    df_complete, df_simplified = process_files(base_path)
    
    # Save complete dataset
    complete_output_path = "combined_attack_data_complete_test.csv"
    df_complete.to_csv(complete_output_path, index=False)
    logger.info(f"Complete data saved to {complete_output_path}")
    
    # Save simplified dataset
    simplified_output_path = "combined_attack_data_simplified_test.csv"
    df_simplified.to_csv(simplified_output_path, index=False)
    logger.info(f"Simplified data saved to {simplified_output_path}")