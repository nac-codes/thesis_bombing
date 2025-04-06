import pandas as pd
import re

# Read the CSV file
print("Reading CSV file...")
df = pd.read_csv('processed_data/raids_area_bombing_classification.csv')

# Extract category from BOOK column
print("Extracting categories...")
def extract_category(book_value):
    if not isinstance(book_value, str):
        return "UNKNOWN"
    
    # Extract text between BOOK_XX_ and __PART or end of string
    match = re.search(r'BOOK_\d+_([A-Z]+)(?:__PART_\d+)?', book_value)
    if match:
        return match.group(1)
    else:
        # Handle special cases
        if "MILITARYINDUSTRY" in book_value:
            return "MILITARYINDUSTRY"
        elif "OILREFINERIES" in book_value:
            return "OILREFINERIES"
        elif "EXPLOSIVES" in book_value:
            return "EXPLOSIVES"
        elif "NAVAL" in book_value:
            return "NAVAL"
        elif "RADIO" in book_value:
            return "RADIO"
        elif "TACTICAL" in book_value:
            return "TACTICAL"
        elif "SUPPLY" in book_value:
            return "SUPPLY"
        elif "UTILITIES" in book_value:
            return "UTILITIES"
        elif "MANUFACTURING" in book_value:
            return "MANUFACTURING"
        elif "AIRFIELDS" in book_value:
            return "AIRFIELDS"
        elif "TRANSPORTATION" in book_value:
            return "TRANSPORTATION"
        else:
            return "UNKNOWN"

# Apply the function to create the new column
df['CATEGORY'] = df['BOOK'].apply(extract_category)

# Save the updated CSV
print("Saving updated CSV...")
df.to_csv('processed_data/raids_area_bombing_classification_with_category.csv', index=False)

print("Done! New file saved as 'processed_data/raids_area_bombing_classification_with_category.csv'") 