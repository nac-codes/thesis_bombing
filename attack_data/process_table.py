import pandas as pd
import os
import sys
import re
import json
from openai import OpenAI
import logging
# from tqdm import tqdm

# Configure logging
log_file = '/Users/chim/Working/Thesis/Attack_Images/OCR/PRODUCTION/running/table_processing_log.txt'

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - [PID %(process)d] - %(levelname)s - %(message)s',
    filemode='a'
)

client = OpenAI()

def check_DAY(value, is_required):
    # Expected: Single day (1-31) or a range (e.g., 15-16)
    if pd.isna(value):
        return not is_required, "DAY is required. should be a number between 1 and 31 or a range (e.g., 15-16)." if is_required else (True, None)
    value = str(value).strip()
    if value.isdigit():
        day = int(float(value))
        if 1 <= day <= 31:
            return True, None
        else:
            return False, "DAY should be between 1 and 31."
    elif re.match(r'^\d{1,2}-\d{1,2}$', value):
        start_day, end_day = map(int, value.split('-'))
        if 1 <= start_day <= 31 and 1 <= end_day <= 31 and start_day <= end_day:
            return True, None
        else:
            return False, "DAY range should be between 1 and 31 and start <= end."
    else:
        return False, "Invalid DAY format. Expected single day (1-31) or a range (e.g., 15-16)."

def check_MONTH(value, is_required):
    # Expected: Number from 1 to 12
    if pd.isna(value):
        return not is_required, "MONTH is required. Should be a number between 1 and 12." if is_required else (True, None)
    try:
        month = int(float(value))
        if 1 <= month <= 12:
            return True, None
        else:
            return False, "MONTH should be between 1 and 12."
    except ValueError:
        return False, "MONTH should be an integer with a value between 1 and 12."

def check_YEAR(value, is_required):
    # Expected: Single digit (0-5) representing 1940-1945
    if pd.isna(value):
        return not is_required, "YEAR is required. Should be a single digit (0-5) representing 1940-1945." if is_required else (True, None)
    try:
        year = int(float(value))
        if 0 <= year <= 5:
            return True, None
        else:
            return False, "YEAR should be between 0 and 5."
    except ValueError:
        return False, "YEAR should be a single digit integer between 0 and 5."

def check_TIME_OF_ATTACK(value, is_required):
    # Expected: 24-hour time format (e.g., 1434)
    if pd.isna(value):
        return not is_required, "TIME OF ATTACK is required. Should be a 4 digit number representing the time in 24-hour format (e.g., 1434)." if is_required else (True, None)
    value = str(value).strip()
    if re.match(r'^\d{4}$', value):
        hour = int(value[:2])
        minute = int(value[2:])
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return True, None
        else:
            return False, "TIME OF ATTACK should be in 24-hour format HHMM."
    else:
        return False, "Invalid TIME OF ATTACK format. Expected HHMM."

def check_AIR_FORCE(value, *args):
    # Expected: 8, 9, 12, 15 for US Air Forces, or R for Royal Air Force
    is_required = args[0] if len(args) > 0 else True
    is_RAF = args[1] if len(args) > 1 else False
    if pd.isna(value):
        if is_required:
            if is_RAF:
                return False, "AIR FORCE is required. Could be 8, 9, 12, 15, or R. Potentially is R."
            else:
                return False, "AIR FORCE is required. Should be 8, 9, 12, or 15. Potentially is 8."
        else:
            return True, None
    valid_values = {'8', '9', '12', '15', 'R'}
    if str(value).strip() in valid_values:
        return True, None
    else:
        return False, "AIR FORCE code should be one of 8, 9, 12, 15, or R."

def check_GROUP_SQUADRON_NUMBER(value, is_required):
    # Expected: IDs like 305G, 305AG, 305BG, 305CG, 95G, 99G, etc.
    if pd.isna(value):
        return not is_required, "GROUP/SQUADRON NUMBER is required. Should be 2 to 4 numbers followed by an optional A, B, or C, and then G or S (e.g., 305CG, 99G, 305S)." if is_required else (True, None)
    value = str(value).strip()
    if re.match(r'^\d{2,4}([ABC]?[GS])$', value):
        return True, None
    else:
        return False, "GROUP/SQUADRON NUMBER should be 2 to 4 numbers followed by an optional A, B, or C, and then G or S (e.g., 305CG, 99G, 305S)."

def check_NUMBER_OF_AIRCRAFT_BOMBING(value, is_required):
    # Expected: Number from 1 to hundreds
    if pd.isna(value):    
        return not is_required, "NUMBER OF AIRCRAFT BOMBING is required. Should be a number between 1 and 999." if is_required else (True, None)
    try:
        num = int(float(value))
        if 1 <= num <= 999:
            return True, None
        else:
            return False, "NUMBER OF AIRCRAFT BOMBING should be between 1 and 999."
    except ValueError:
        return False, "NUMBER OF AIRCRAFT BOMBING should be an integer with a value between 1 and 999."

def check_ALTITUDE_OF_RELEASE(value, is_required):
    # expected a number between 50 and 600
    if pd.isna(value):
        return not is_required, "ALTITUDE OF RELEASE IN HUND. FT. is required. Should be a number between 50 and 600." if is_required else (True, None)
    try:
        num = int(float(value))
        if 50 <= num <= 600:
            return True, None
        else:
            return False, "ALTITUDE OF RELEASE IN HUND. FT. should be between 50 and 600."
    except ValueError:
        return False, "ALTITUDE OF RELEASE IN HUND. FT. should be an integer with a value between 50 and 600."

def check_SIGHTING(value, is_required):
    # expected a number between 1 and 13 or a letter R, L, D, S, or G
    if pd.isna(value):
        return not is_required, "SIGHTING is required. Should be a number between 1 and 13 or a letter R, L, D, S, or G." if is_required else (True, None)
    value = str(value).strip()
    if re.match(r'^\d+(\.\d+)?$', value):
        num = int(float(value))
        if 1 <= num <= 13:
            return True, None
        else:
            return False, "SIGHTING should be between 1 and 13."
    elif value in {'R', 'L', 'D', 'S', 'G'}:
        return True, None
    else:
        return False, "SIGHTING should be a number between 1 and 13 or a letter R, L, D, S, or G."

def check_VISIBILITY_OF_TARGET(value, is_required):
    # expected a letter, G, C, P, or N
    if pd.isna(value):
        return not is_required, "VISIBILITY OF TARGET is required. Should be a letter G, C, P, or N." if is_required else (True, None)
    value = str(value).strip()
    if value in {'G', 'C', 'P', 'N'}:
        return True, None
    else:
        return False, "VISIBILITY OF TARGET should be a letter G, C, P, or N."

def check_TARGET_PRIORITY(value, is_required):
    # expected a value between 1 and 4
    if pd.isna(value):
        return not is_required, "TARGET PRIORITY is required. Should be a number between 1 and 4." if is_required else (True, None)
    try:
        num = int(float(value))
        if 1 <= num <= 4:
            return True, None
        else:
            return False, "TARGET PRIORITY should be between 1 and 4."
    except ValueError:
        return False, "TARGET PRIORITY should be an integer with a value between 1 and 4."

def check_HIGH_EXPLOSIVE_BOMBS_NUMBER(value, is_required):
    if pd.isna(value):
        return not is_required, "HIGH EXPLOSIVE BOMBS NUMBER is required. Should be a number between 1 and 999." if is_required else (True, None)
    try:
        num = int(float(value))
        if 1 <= num <= 999:
            return True, None
        else:
            return False, "HIGH EXPLOSIVE BOMBS NUMBER should be between 1 and 999."
    except ValueError:
        return False, "HIGH EXPLOSIVE BOMBS NUMBER should be an integer with a value between 1 and 999."

def check_HIGH_EXPLOSIVE_BOMBS_SIZE(value, is_required):
    if pd.isna(value):
        return not is_required, "HIGH EXPLOSIVE BOMBS SIZE is required. Should be a number between 1 and 16, or 21 to 23, or 'C'." if is_required else (True, None)
    if value == 'C':
        return True, None
    try:
        num = int(float(value))
        if 1 <= num <= 16 or 21 <= num <= 23:
            return True, None
        else:
            return False, "HIGH EXPLOSIVE BOMBS SIZE should be between 1 and 16, or 21 to 23, or 'C'."
    except ValueError:
        return False, "HIGH EXPLOSIVE BOMBS SIZE should be a number between 1 and 16, or 21 to 23, or 'C'."

def check_HIGH_EXPLOSIVE_BOMBS_FUZING_NOSE(value, is_required):
    if pd.isna(value):
        return not is_required, "HIGH EXPLOSIVE BOMBS FUZING NOSE is required. Should be one of 1, 2, 3, 4, 5, 6, or 9." if is_required else (True, None)
    valid_values = {1, 2, 3, 4, 5, 6, 9}
    try:
        num = int(float(value))
        if num in valid_values:
            return True, None
        else:
            return False, "HIGH EXPLOSIVE BOMBS FUZING NOSE should be one of 1, 2, 3, 4, 5, 6, or 9."
    except ValueError:
        return False, "HIGH EXPLOSIVE BOMBS FUZING NOSE should be an integer: 1, 2, 3, 4, 5, 6, or 9."

def check_HIGH_EXPLOSIVE_BOMBS_FUZING_TAIL(value, is_required):
    if pd.isna(value):
        return not is_required, "HIGH EXPLOSIVE BOMBS FUZING TAIL is required. Should be one of 1-16, 91, or 92." if is_required else (True, None)
    valid_values = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 91, 92}
    try:
        num = int(float(value))
        if num in valid_values:
            return True, None
        else:
            return False, "HIGH EXPLOSIVE BOMBS FUZING TAIL should be one of 1-16, 91, or 92."
    except ValueError:
        return False, "HIGH EXPLOSIVE BOMBS FUZING TAIL should be an integer: 1-16, 91, or 92."

def check_INCENDIARY_BOMBS_NUMBER(value, is_required):
    if pd.isna(value):
        return not is_required, "INCENDIARY BOMBS NUMBER is required. Should be a number between 1 and 999." if is_required else (True, None)
    try:
        num = int(float(value))
        if 1 <= num <= 999:
            return True, None
        else:
            return False, "INCENDIARY BOMBS NUMBER should be between 1 and 999."
    except ValueError:
        return False, "INCENDIARY BOMBS NUMBER should be an integer with a value between 1 and 999."

def check_INCENDIARY_BOMBS_SIZE(value, is_required):
    if pd.isna(value):
        return not is_required, "INCENDIARY BOMBS SIZE is required. Should be a number between 1-13, 21-25, or 31-37." if is_required else (True, None)
    try:
        num = int(float(value))
        if 1 <= num <= 13 or 21 <= num <= 25 or 31 <= num <= 37:
            return True, None
        else:
            return False, "INCENDIARY BOMBS SIZE should be between 1-13, 21-25, or 31-37."
    except ValueError:
        return False, "INCENDIARY BOMBS SIZE should be a number between 1-13, 21-25, or 31-37."

def check_FRAGMENTATION_BOMBS_NUMBER(value, is_required):
    if pd.isna(value):
        return not is_required, "FRAGMENTATION BOMBS NUMBER is required. Should be a number between 1 and 999." if is_required else (True, None)
    try:
        num = int(float(value))
        if 1 <= num <= 999:
            return True, None
        else:
            return False, "FRAGMENTATION BOMBS NUMBER should be between 1 and 999."
    except ValueError:
        return False, "FRAGMENTATION BOMBS NUMBER should be an integer with a value between 1 and 999."

def check_FRAGMENTATION_BOMBS_SIZE(value, is_required):
    if pd.isna(value):
        return not is_required, "FRAGMENTATION BOMBS SIZE is required. Should be a number between 1-11 or 41." if is_required else (True, None)
    try:
        num = int(float(value))
        if 1 <= num <= 11 or num == 41:
            return True, None
        else:
            return False, "FRAGMENTATION BOMBS SIZE should be between 1-11 or 41."
    except ValueError:
        return False, "FRAGMENTATION BOMBS SIZE should be a number between 1-11 or 41."

def check_TONNAGE(row):
    logging.debug(f"Checking TONNAGE for row {row}")
    # Check if individual tonnages sum up to TOTAL TONS
    try:
        he_tons = int(float(row['HIGH EXPLOSIVE BOMBS TONS']))
        incendiary_tons = int(float(row['INCENDIARY BOMBS TONS']))
        frag_tons = int(float(row['FRAGMENTATION BOMBS TONS']))
        total_tons = int(float(row['TOTAL TONS']))
    except ValueError:
        return False, "Tonnage values should be numbers."

    # check if TOTAL TONS is na
    if pd.isna(total_tons):
        return False, "TOTAL TONS is required. Should be a number."
    
    # calculate the total but don't include nan values
    if pd.isna(he_tons):
        he_tons = 0
    if pd.isna(incendiary_tons):
        incendiary_tons = 0
    if pd.isna(frag_tons):
        frag_tons = 0        
    calculated_total = he_tons + incendiary_tons + frag_tons

    if calculated_total != total_tons or pd.isna(calculated_total):
        return False, "Individual tonnages do not sum up to TOTAL TONS."
    else:
        logging.debug(f"Row {row}: TONNAGE is valid.")
        return True, None


def get_context_values(df, col, row_idx, check_function, n=4):
    # Get all values in the column
    all_values = df[col].tolist()
    
    # Create a list of tuples with (index, value) for non-empty values, excluding rows that are summation rows
    non_empty_values = [(i, v) for i, v in enumerate(all_values) if pd.notna(v) and v != "" and not df.at[i, 'SUMMATION_ROW']]
    
    # Sort by distance from the current row
    sorted_values = sorted(non_empty_values, key=lambda x: abs(x[0] - row_idx))
    
    # Separate previous and subsequent values
    previous_values = []
    subsequent_values = []
    
    for i, v in sorted_values:
        if i < row_idx:
            # check if the value is valid based on the column and the check_ function
            valid, message = check_function(v, True)
            logging.debug(f"For value {v}, got validity of {valid}")
            if valid:
                previous_values.append((i - row_idx, v))  # Negative index indicates previous
        elif i > row_idx:
            valid, message = check_function(v, True)
            logging.debug(f"For value {v}, got validity of {valid}")
            if valid:
                subsequent_values.append((i - row_idx, v))  # Positive index indicates subsequent
        
        if len(previous_values) + len(subsequent_values) == n:
            break
    
    # Sort previous values in reverse order (closest to current row first)
    previous_values.sort(reverse=False)
    
    context = {
        "previous": previous_values,
        "subsequent": subsequent_values
    }
    
    return context

def check_summation_row(df, row_idx):
    current_row = df.iloc[row_idx]
    
    required_columns = ['NUMBER OF AIRCRAFT BOMBING', 'TOTAL TONS']
    tonnage_columns = ['HIGH EXPLOSIVE BOMBS TONS', 'INCENDIARY BOMBS TONS', 'FRAGMENTATION BOMBS TONS']
    
    # Check if required columns are filled
    if not all(pd.notna(current_row[col]) for col in required_columns):
        return False
    
    # Check if at least one tonnage column is filled
    if not any(pd.notna(current_row[col]) for col in tonnage_columns):
        return False
    
    # Count how many other columns (excluding required and tonnage) have values
    other_columns = [col for col in df.columns if col not in required_columns + tonnage_columns]
    other_filled_columns = sum(pd.notna(current_row[col]) for col in other_columns)
    
    # If 1 or fewer other columns have values, it's a summation row
    is_sum_row = other_filled_columns <= 1
    
    logging.debug(f"Row {row_idx + 1} determined to be a summation row: {is_sum_row}")
    return is_sum_row    


def send_to_ai(prompt, attributes, max_retries=3, model="gpt-4o-mini"):
    for attempt in range(max_retries):
        try:            
            # Append instructions for JSON format
            attributes_str = ", ".join([f'"{attr}"' for attr in attributes])
            full_prompt = f"{prompt}\n\nPlease return the corrected values for {attributes_str} in the following JSON format:\n```json\n{{\n"
            for attr in attributes:
                full_prompt += f'  "{attr}": "your_corrected_value_here",\n'
            full_prompt = full_prompt.rstrip(',\n') + "\n}\n```"
            full_prompt = full_prompt + "\n\nExplain your reasoning briefly for your answer and then return the corrected values in the same JSON format."
            
            logging.debug(f"Attempt {attempt + 1}: Sending prompt to AI:\n{full_prompt}")

            # Make the API call
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that corrects data entry errors in the US Strategic Bombing Survey."},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=0.5,
                top_p=0.5
            )
            
            # Extract the JSON part from the response
            full_response = response.choices[0].message.content.strip()
            logging.debug(f"Received full response from AI:\n{full_response}")

            # Use regex to find the JSON part
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', full_response)
            if json_match:
                json_str = json_match.group(1)
                logging.debug(f"Extracted JSON from response:\n{json_str}")
            else:
                logging.warning("No JSON found in the response. Retrying...")
                continue

            # Parse the JSON
            result = json.loads(json_str)
            
            # Check if all expected attributes are in the result
            if all(attr in result for attr in attributes):
                logging.debug(f"Successfully received all expected attributes: {result}")
                return result
            else:
                logging.warning(f"Attempt {attempt + 1}: JSON response does not contain all expected attributes. Retrying...")
        except json.JSONDecodeError:
            logging.error(f"Attempt {attempt + 1}: Failed to parse JSON. Retrying...")
        except Exception as e:
            logging.error(f"Attempt {attempt + 1}: An error occurred: {str(e)}. Retrying...")
    
    logging.error(f"Failed to get a valid response after {max_retries} attempts.")
    return None

def has_valid_value(row, columns):
    return any(pd.notna(row[col]) and row[col] != "" for col in columns)

def initial_table_cleanup(df):
    # Iterate through each column
    for col in df.columns:
        # Iterate through each row
        row_idx = 0
        while row_idx < len(df):
            cell_value = df.at[row_idx, col]
            
            # Check if the cell contains a newline character
            if isinstance(cell_value, str) and '\n' in cell_value:
                parts = cell_value.split('\n', 1)
                
                # Assign the first part to the current cell
                df.at[row_idx, col] = parts[0].strip()
                
                # Handle the second part
                if len(parts) > 1:
                    second_part = parts[1].strip()
                    if second_part:
                        # Start from the next row
                        next_row = row_idx + 1
                        value_to_insert = second_part
                        
                        while next_row < len(df):
                            # Store the current value of the next row
                            current_value = df.at[next_row, col]
                            
                            # Insert the new value
                            df.at[next_row, col] = value_to_insert
                            
                            # If the current value was empty, we're done
                            if pd.isna(current_value) or current_value == "":
                                break
                            
                            # Otherwise, prepare to insert the displaced value in the next iteration
                            value_to_insert = current_value
                            next_row += 1
                        
                        if next_row == len(df):
                            # We've reached the end of the table
                            logging.warning(f"Reached end of table while trying to split cell at row {row_idx}, column '{col}'. Some data may be lost.")
            
            row_idx += 1
    
    return df



def add_additional_context(prompt, row, prev_row, col):
    logging.debug(f"Adding additional context for column: {col}")
    if col == 'DAY':              
        prompt += f"Note also that the month and year for the current row are {row['MONTH']} and {row['YEAR']}.\n"
        logging.debug(f"Current row month and year: {row['MONTH']}, {row['YEAR']}")
        if prev_row is not None:
            prompt += f"\nNote also that the Day, Month, and Year for the previous row is {prev_row['DAY']}, {prev_row['MONTH']}, and {prev_row['YEAR']}.\n"
            logging.debug(f"Previous row day, month, and year: {prev_row['DAY']}, {prev_row['MONTH']}, {prev_row['YEAR']}")
    elif col == 'MONTH':
        prompt += f"Note also that the Day and Year for the current row are {row['DAY']} and {row['YEAR']}.\n"
        logging.debug(f"Current row day and year: {row['DAY']}, {row['YEAR']}")
        if prev_row is not None:
            prompt += f"\nNote also that the Day, Month, and Year for the previous row is {prev_row['DAY']}, {prev_row['MONTH']}, and {prev_row['YEAR']}.\n"
            logging.debug(f"Previous row day, month, and year: {prev_row['DAY']}, {prev_row['MONTH']}, {prev_row['YEAR']}")
    elif col == 'YEAR':
        prompt += f"Note also that the Day and Month for the current row are {row['DAY']} and {row['MONTH']}.\n"
        logging.debug(f"Current row day and month: {row['DAY']}, {row['MONTH']}")
        if prev_row is not None:
            prompt += f"\nNote also that the Day, Month, and Year for the previous row is {prev_row['DAY']}, {prev_row['MONTH']}, and {prev_row['YEAR']}.\n"
            logging.debug(f"Previous row day, month, and year: {prev_row['DAY']}, {prev_row['MONTH']}, {prev_row['YEAR']}")
    elif col == 'TIME OF ATTACK':
        # check if the date has changed from the previous row
        if prev_row is not None:
            if prev_row['DAY'] == row['DAY'] and prev_row['MONTH'] == row['MONTH'] and prev_row['YEAR'] == row['YEAR']:
                prompt += f"Note that the date has not changed from the previous row. meaning that the time of attack should be similar or the same as the previous rows.\n"
                logging.debug("Date has not changed from the previous row.")
            else:
                prompt += f"Note that the date has changed from the previous row. meaning that the time of attack might be different from the previous row and more like subsequent rows.\n"
                logging.debug("Date has changed from the previous row.")
    elif col == 'AIR FORCE':
        # check if the date has changed from the previous row
        if prev_row is not None:
            if prev_row['DAY'] == row['DAY'] and prev_row['MONTH'] == row['MONTH'] and prev_row['YEAR'] == row['YEAR']:
                prompt += f"Note that the date has not changed from the previous row. meaning that the air force should be the same as the previous row(s).\n"
                logging.debug("Date has not changed from the previous row.")
            elif prev_row['YEAR'] == row['YEAR']:
                prompt += f"Note that the year has not changed from the previous row. meaning that the air force might be the same as the previous row(s).\n"
                logging.debug("Year has not changed from the previous row.")
            else:
                prompt += f"Note that the date has changed from the previous row. meaning that the air force might be different from the previous row(s) and may be more like subsequent rows.\n"
                logging.debug("Date has changed from the previous row.")
    
    logging.debug(f"Final prompt: {prompt}")
    return prompt

def split_csv_cells(input_csv):
    number_of_gpt_requests_made = 0

    # Read the input CSV file
    df = pd.read_csv(input_csv)    

   # Replace ":unselected:" with "" in the entire DataFrame
    df = df.replace(":unselected:", "", regex=False)
    df = df.replace(":selected:", "", regex=False)
    logging.debug("Replaced all instances of ':unselected:' with ''")


    # logg the number of rows and columns
    logging.debug(f"Initial number of rows: {len(df)}")
    logging.debug(f"Initial number of columns: {len(df.columns)}")

    # Remove completely empty rows
    empty_rows = df.isna().all(axis=1) | (df == "").all(axis=1)
    df = df[~empty_rows].reset_index(drop=True)
    logging.debug(f"Removed {empty_rows.sum()} completely empty rows")

    # logg the number of rows and columns after removing completely empty rows
    logging.debug(f"Number of rows after removing completely empty rows: {len(df)}")
    logging.debug(f"Number of columns after removing completely empty rows: {len(df.columns)}")

    # # Remove rows that have only one or fewer non-NA values
    # non_empty_count = df.notna().sum(axis=1) & (df != "").sum(axis=1)
    # df = df[non_empty_count > 1].reset_index(drop=True)
    # logging.info(f"Removed {len(non_empty_count) - len(df)} rows with one or fewer non-empty values")

    # # logg the number of rows and columns after removing rows with one or fewer non-empty values
    # logging.debug(f"Number of rows after removing rows with one or fewer non-empty values: {len(df)}")
    # logging.debug(f"Number of columns after removing rows with one or fewer non-empty values: {len(df.columns)}")

    # add the column "summation row" boolean column
    
    df['SUMMATION_ROW'] = False

    logging.debug("Checking for summation rows")
    # first loop through each row and check if it's a summation row
    for row_idx in range(len(df)):
        if check_summation_row(df, row_idx):
            df.at[row_idx, 'SUMMATION_ROW'] = True
            logging.debug(f"Row {row_idx + 1} is a summation row.")

    # Do initial table cleanup
    df = initial_table_cleanup(df)

    df['GROUP/SQUADRON NUMBER'] = df['GROUP/SQUADRON NUMBER'].astype(str)
    df['AIR FORCE'] = df['AIR FORCE'].astype(str)

    # # save a version of the table just after the initial cleanup
    # df.to_csv('table_after_initial_cleanup.csv', index=False)

    # logg the number of rows and columns after the initial cleanup
    logging.debug(f"Number of rows after initial cleanup: {len(df)}")
    logging.debug(f"Number of columns after initial cleanup: {len(df.columns)}")

    # Define check functions for each column
    check_functions = {
        'DAY': check_DAY,
        'MONTH': check_MONTH,
        'YEAR': check_YEAR,
        'TIME OF ATTACK': check_TIME_OF_ATTACK,
        'AIR FORCE': check_AIR_FORCE,
        'GROUP/SQUADRON NUMBER': check_GROUP_SQUADRON_NUMBER,
        'NUMBER OF AIRCRAFT BOMBING': check_NUMBER_OF_AIRCRAFT_BOMBING,
        'ALTITUDE OF RELEASE IN HUND. FT.': check_ALTITUDE_OF_RELEASE,
        'SIGHTING': check_SIGHTING,
        'VISIBILITY OF TARGET': check_VISIBILITY_OF_TARGET,
        'TARGET PRIORITY': check_TARGET_PRIORITY,
        'HIGH EXPLOSIVE BOMBS NUMBER': check_HIGH_EXPLOSIVE_BOMBS_NUMBER,
        'HIGH EXPLOSIVE BOMBS SIZE': check_HIGH_EXPLOSIVE_BOMBS_SIZE,
        'HIGH EXPLOSIVE BOMBS FUZING NOSE': check_HIGH_EXPLOSIVE_BOMBS_FUZING_NOSE,
        'HIGH EXPLOSIVE BOMBS FUZING TAIL': check_HIGH_EXPLOSIVE_BOMBS_FUZING_TAIL,
        'INCENDIARY BOMBS NUMBER': check_INCENDIARY_BOMBS_NUMBER,
        'INCENDIARY BOMBS SIZE': check_INCENDIARY_BOMBS_SIZE,
        'FRAGMENTATION BOMBS NUMBER': check_FRAGMENTATION_BOMBS_NUMBER,
        'FRAGMENTATION BOMBS SIZE': check_FRAGMENTATION_BOMBS_SIZE,
    }

    # Iterate through each row
    logging.debug("Starting to process rows...")
    for row_idx in range(len(df)):
        # Get the current row and nearby rows for context
        current_row = df.iloc[row_idx]

        # Check if this is a summation row and perform necessary checks
        if current_row['SUMMATION_ROW']:
            logging.debug(f"Row {row_idx + 1} is a summation row.")
            continue

        # # check if this is an RAF entry or a US entry. For the RAF most of the values aren't filled in except for date, time, air force, aircraft bombing, sometimes altitude, and the bombs (not fuzing though)
        # col_count = 0
        # is_RAF = False
        # for col in df.columns:
        #     if col in ['GROUP/SQUADRON NUMBER', 'SIGHTING', 'VISIBILITY OF TARGET', 'TARGET PRIORITY', 'HIGH EXPLOSIVE BOMBS FUZING NOSE', 'HIGH EXPLOSIVE BOMBS FUZING TAIL', 'TIME OF ATTACK', 'ALTITUDE OF RELEASE IN HUND. FT.']:
        #         if not pd.isna(current_row[col]):
        #             col_count += 1
        # if col_count == 0:
        #     # Check if this row could be RAF
        #     is_potential_RAF = current_row['AIR FORCE'] not in ['8', '9', '12', '15']
            
        #     # If it's a potential RAF row, check the previous row if it exists
        #     if is_potential_RAF and row_idx > 0:
        #         prev_row = df.iloc[row_idx - 1]
                
        #         # Check if the date is the same as the previous row
        #         same_date = (current_row['DAY'] == prev_row['DAY'] and 
        #                      current_row['MONTH'] == prev_row['MONTH'] and 
        #                      current_row['YEAR'] == prev_row['YEAR'])
                
        #         # If the date is the same and the previous row is not RAF, consider this row as part of the same US Air Force mission
        #         if same_date and prev_row['AIR FORCE'] in ['8', '9', '12', '15']:
        #             is_RAF = False
        #         else:
        #             is_RAF = True
        #     else:
        #         is_RAF = is_potential_RAF
        
        # logging.debug(f"Row {row_idx + 1} appears to be a RAF entry: {is_RAF}")
        
        # Check each cell in the row
        for col, check_func in check_functions.items():
            value = current_row[col]
            is_required = False
            # Day, Month, Year, Time of Attack, Air Force, Number of Aircraft Bombing always required
            if col in ['DAY', 'MONTH', 'YEAR', 'AIR FORCE', 'NUMBER OF AIRCRAFT BOMBING']:
                is_required = True
            # else if it's not an RAF entry then Altitude of release, group squadron number, sighting, visibility of target, target priority all required            
            if col in ['TIME OF ATTACK', 'ALTITUDE OF RELEASE IN HUND. FT.', 'GROUP/SQUADRON NUMBER', 'SIGHTING', 'VISIBILITY OF TARGET', 'TARGET PRIORITY']:
                is_required = True
                # if not is_RAF:
                #     is_required = True 
                # else: 
                #     is_required = False
            # if there is any value in the columns related to high explosive bombs ... then they are all required except fuzing nose/tail.. if not raf then fuzing nose tail are required
            he_cols = ['HIGH EXPLOSIVE BOMBS NUMBER', 'HIGH EXPLOSIVE BOMBS SIZE','HIGH EXPLOSIVE BOMBS TONS', 'HIGH EXPLOSIVE BOMBS FUZING NOSE', 'HIGH EXPLOSIVE BOMBS FUZING TAIL']            
            if col in he_cols:
                if has_valid_value(current_row, he_cols):
                    is_required = True
                    # if not is_RAF:                
                    #     is_required = True
                    # else:
                    #     if col in ['HIGH EXPLOSIVE BOMBS FUZING NOSE', 'HIGH EXPLOSIVE BOMBS FUZING TAIL']:
                    #         is_required = False
                    #     else:
                    #         is_required = True
                else:
                    is_required = False
            # if there is any value in the columns related to incendiary bombs ... then they are all required except fuzing nose/tail.. if not raf then fuzing nose tail are required
            incendiary_cols = ['INCENDIARY BOMBS NUMBER', 'INCENDIARY BOMBS SIZE', 'INCENDIARY BOMBS TONS']
            if col in incendiary_cols:
                if has_valid_value(current_row, incendiary_cols):
                    is_required = True
                else:
                    is_required = False
            # if there is any value in the columns related to fragmentation bombs ... then they are all required except fuzing nose/tail.. if not raf then fuzing nose tail are required
            frag_cols = ['FRAGMENTATION BOMBS NUMBER', 'FRAGMENTATION BOMBS SIZE', 'FRAGMENTATION BOMBS TONS']
            if col in frag_cols:
                if has_valid_value(current_row, frag_cols):
                    is_required = True
                else:
                    is_required = False

            
            if col == "AIR FORCE":
                is_valid, error_msg = check_func(value, is_required)
                if is_valid and row_idx > 0:
                    prev_row = df.iloc[row_idx - 1]
                    if (current_row['DAY'] == prev_row['DAY'] and 
                        current_row['MONTH'] == prev_row['MONTH'] and 
                        current_row['YEAR'] == prev_row['YEAR'] and 
                        current_row['AIR FORCE'] != prev_row['AIR FORCE']):
                        is_valid = False
                        error_msg = "Air Force value has changed while the date remains the same. This is unusual and should be verified."
                        # logging.warning(f"Row {row_idx + 1}: {error_msg}")
            else:
                is_valid, error_msg = check_func(value, is_required)
            if not is_valid:
                # Get context for this column
                context_values = get_context_values(df, col, row_idx, check_func, n=5)
                prompt = (
                    f"Value Error in column '{col}' at row {row_idx + 1}:\n"
                    f"Current Value: {value}\n"
                    f"Error: {error_msg}\n"
                    f"Context Values:\n"
                    f"  Previous values (relative row index, value):\n"
                )

                for rel_idx, prev_value in context_values["previous"]:
                    prompt += f"    {rel_idx}: {prev_value}\n"
                
                prompt += " --- Current Row is Here! --- \n"

                prompt += f"  Subsequent values (relative row index, value):\n"

                for rel_idx, next_value in context_values["subsequent"]:
                    prompt += f"    {rel_idx}: {next_value}\n"

                # function to add additional context to the prompt based on the column
                if row_idx > 0:
                    prompt = add_additional_context(prompt, current_row, df.iloc[row_idx - 1], col)
                else:
                    prompt = add_additional_context(prompt, current_row, None, col)

                prompt += f"Please suggest the correct value for the current row."    
                logging.debug(f"Row {row_idx + 1}: {prompt}")
                corrected_values = send_to_ai(prompt, [col])
                number_of_gpt_requests_made += 1
                if corrected_values is not None and col in corrected_values:
                    corrected_value = corrected_values[col]
                    try:
                        # Try to convert the value to the appropriate type
                        if pd.api.types.is_numeric_dtype(df[col]) and col not in ['GROUP/SQUADRON NUMBER', 'AIR FORCE']:
                            corrected_value = int(float(corrected_value))
                        elif pd.api.types.is_datetime64_any_dtype(df[col]):
                            corrected_value = pd.to_datetime(corrected_value)
                        else:
                            # For non-numeric columns or special cases, keep as string
                            corrected_value = str(corrected_value).strip()
                        
                        df.at[row_idx, col] = corrected_value
                        # fix the value for the current row as well
                        current_row = df.iloc[row_idx]                 
                        
                        logging.info(f"Row {row_idx + 1}: Corrected Value for '{col}': {corrected_value}")
                    except ValueError as e:
                        logging.error(f"Row {row_idx + 1}: Error converting value for '{col}': {str(e)}")
                else:
                    logging.error(f"Row {row_idx + 1}: Error in column '{col}': Unable to get corrected value.")            
        
        # Check tonnage values
        is_tonnage_valid, tonnage_error = check_TONNAGE(current_row)
        if not is_tonnage_valid:
            # Prepare prompt with tonnage details
            tonnage_values = {}            
            if has_valid_value(current_row, he_cols):
                tonnage_values['HIGH EXPLOSIVE BOMBS TONS'] = current_row['HIGH EXPLOSIVE BOMBS TONS']
                        
            if has_valid_value(current_row, incendiary_cols):
                tonnage_values['INCENDIARY BOMBS TONS'] = current_row['INCENDIARY BOMBS TONS']
                        
            if has_valid_value(current_row, frag_cols):
                tonnage_values['FRAGMENTATION BOMBS TONS'] = current_row['FRAGMENTATION BOMBS TONS']
            
            # Always include TOTAL TONS
            tonnage_values['TOTAL TONS'] = current_row['TOTAL TONS']
            
            prompt = (
                f"Tonnage Error at row {row_idx + 1}:\n"
                f"Error: {tonnage_error}\n"
                f"Expected Rule: Individual tonnages should sum up to TOTAL TONS. Total Tons should be the sum of all TONS columns.\n"
                f"Tonnage Values: {tonnage_values}\n"
                f"Please correct the tonnage values."
            )
            logging.debug(f"Row {row_idx + 1}: {prompt}")
            corrected_values = send_to_ai(prompt, list(tonnage_values.keys()))
            number_of_gpt_requests_made += 1            
            if corrected_values:
                for col, value in corrected_values.items():
                    try:
                        int_value = int(float(value))
                        df.at[row_idx, col] = int_value
                        logging.debug(f"Updated value in column '{col}' at row {row_idx + 1} to: {int_value}")
                    except ValueError:
                        # If conversion fails, log an error and skip this value
                        logging.error(f"Error: Could not convert '{value}' to int for column '{col}' at row {row_idx + 1}")
                        continue
            else:
                logging.error(f"Row {row_idx + 1}: Error in Tonnage: Unable to get corrected values.")
        
    logging.info(f"Made {number_of_gpt_requests_made} gpt api requests")

    return df

    # TODO
    # Make the tonnage thing more mathematical, so after we do all this we should maybe make another script that does the following, for each row it takes the size converts it to pound per bomb, multiplies it by the numebr to get the expected tonnage... it does that for all variables so it finds the expected size, the expected number, and expected tonnage using the other variables. whichever one takes the least number of changes to make seemingly accurate. we go with those values
    # We also need to think about the next step of handling data from one page going over into the next one. 

    # For cleaning
        # first 1000 tables processed processed all rows, something wrong with the empty row removal. Need to clean this by finding rows with no tonnages other than total tons at the start and end.
    
# Example usage
if __name__ == "__main__":
    input_csv = sys.argv[1]
    logging.info(f"------------Processing {input_csv}------------")

    df = split_csv_cells(input_csv)

    # Save the updated DataFrame to a new CSV file
    output_csv = input_csv.replace(".csv", "_updated.csv")
    df.to_csv(output_csv, index=False)
    logging.info(f"----------- Updated DataFrame saved to {output_csv}")
