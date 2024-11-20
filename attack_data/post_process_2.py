import os
import pandas as pd
import numpy as np
from fuzzywuzzy import fuzz
import logging

# Configure logging
logging.basicConfig(
    filename='/Users/chim/Working/Thesis/Attack_Images/OCR/PRODUCTION/running/final_processing_log.txt',
    level=logging.DEBUG,
    format='%(asctime)s - [PID %(process)d] - %(levelname)s - %(message)s',
    filemode='w'
)

BASE_DIR = '/Users/chim/Working/Thesis/Attack_Images/BOXES'

bomb_weight_mapping = {
    "HIGH EXPLOSIVE": {
        1: [100], 2: [250, 300], 3: [500, 600], 4: [1000, 1100], 5: [2000],
        6: [4000], 7: [500], 8: [1000], 9: [1000], 10: [1600],
        11: [325, 350], 12: [1000], 13: [1660], 14: [2000]
    },
    "INCENDIARY": {
        1: [2], 2: [4], 3: [6], 4: [10], 5: [100], 6: [500],
        7: [14 * 6], 8: [38 * 6], 9: [60 * 6], 10: [34 * 4],
        11: [110 * 4], 12: [128 * 4], 13: [100]
    },
    "FRAGMENTATION": {
        1: [4], 2: [20], 3: [23], 4: [90], 5: [260],
        6: [3 * 23], 7: [6 * 20], 8: [20 * 20, 24 * 20], 9: [6 * 90],
        10: [24 * 4], 11: [90 * 4]
    }
}

def get_expected_values(row, bomb_type):
    logging.debug(f"Getting expected values for bomb type: {bomb_type}")
    tonnage = row[f'{bomb_type} BOMBS TONS']
    number = row[f'{bomb_type} BOMBS NUMBER']
    size_code = row[f'{bomb_type} BOMBS SIZE']
    
    logging.debug(f"Current row values - Tonnage: {tonnage}, Number: {number}, Size Code: {size_code}")

    if pd.isna(size_code) or size_code == 0:
        logging.warning(f"Invalid size code: {size_code}. Returning None.")
        return None

    try:
        size_code = int(size_code)
        weights = bomb_weight_mapping[bomb_type].get(size_code, [])
    except ValueError:
        logging.warning(f"Invalid size code for bomb type {bomb_type}: {size_code}")
        return None

    if not weights:
        logging.warning(f"No weights found for bomb type: {bomb_type}, size code: {size_code}")
        return None

    expected_values = []
    for weight in weights:
        if not pd.isna(tonnage) and not pd.isna(number):
            expected_size = size_code
            expected_tonnage = tonnage
            expected_number = number
        elif not pd.isna(tonnage) and pd.isna(number):
            expected_size = size_code
            expected_tonnage = tonnage
            expected_number = (tonnage * 2000) / weight
        elif pd.isna(tonnage) and not pd.isna(number):
            expected_size = size_code
            expected_tonnage = (number * weight) / 2000
            expected_number = number
        else:
            continue

        expected_values.append({
            'tonnage': expected_tonnage,
            'size': expected_size,
            'number': expected_number
        })
        logging.debug(f"Calculated expected values: {expected_values[-1]}")

    return expected_values

def calculate_similarity(original, expected):
    if pd.isna(original) or pd.isna(expected):
        return 0
    return fuzz.ratio(str(original), str(expected))

def find_best_match(original_values, expected_values_list):
    best_match = None
    best_score = -1

    for expected_values in expected_values_list:
        score = sum([
            calculate_similarity(original_values['tonnage'], expected_values['tonnage']),
            calculate_similarity(original_values['size'], expected_values['size']),
            calculate_similarity(original_values['number'], expected_values['number'])
        ])

        if score > best_score:
            best_score = score
            best_match = expected_values

    return best_match

def process_row(row):
    for bomb_type in ['HIGH EXPLOSIVE', 'INCENDIARY', 'FRAGMENTATION']:
        original_values = {
            'tonnage': row[f'{bomb_type} BOMBS TONS'],
            'size': row[f'{bomb_type} BOMBS SIZE'],
            'number': row[f'{bomb_type} BOMBS NUMBER']
        }

        expected_values_list = get_expected_values(row, bomb_type)
        if expected_values_list:
            best_match = find_best_match(original_values, expected_values_list)
            if best_match:
                row[f'{bomb_type} BOMBS TONS'] = best_match['tonnage']
                row[f'{bomb_type} BOMBS SIZE'] = best_match['size']
                row[f'{bomb_type} BOMBS NUMBER'] = best_match['number']

    return row

def process_csv(input_csv, output_csv):
    df = pd.read_csv(input_csv)
    df = df.apply(process_row, axis=1)
    df.to_csv(output_csv, index=False)
    logging.info(f"Processed {input_csv} and saved results to {output_csv}")

def main():
    for root, dirs, files in os.walk(BASE_DIR):
        for file in files:
            if file.endswith('table_data_updated.csv'):
                input_csv = os.path.join(root, file)
                output_csv = os.path.join(root, 'table_data_final.csv')
                process_csv(input_csv, output_csv)

if __name__ == "__main__":
    main()

