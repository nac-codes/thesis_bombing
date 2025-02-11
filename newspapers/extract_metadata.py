import os
import json
import re
from datetime import datetime
from pathlib import Path

def parse_newspaper_info(text):
    # Regular expression to extract date, newspaper name, and archive
    pattern = r'(?:viewer: )?([A-Za-z]+ \d{2}, \d{4}),.*?- (.*?) at (.*?) -'
    match = re.search(pattern, text)
    
    if match:
        date_str, newspaper, archive = match.groups()
        
        # Parse the date
        try:
            date_obj = datetime.strptime(date_str, '%b %d, %Y')
            date_info = {
                'year': date_obj.year,
                'month': date_obj.month,
                'day': date_obj.day,
                'month_name': date_obj.strftime('%B')
            }
        except ValueError:
            date_info = None
            
        return {
            'date': date_info,
            'newspaper': newspaper.strip(),
            'archive': archive.strip(),
            'original_text': text.strip()
        }
    return None

def process_met_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        parsed_data = parse_newspaper_info(content)
        if parsed_data:
            # Create JSON file path (same name but .json extension)
            json_path = file_path.with_suffix('.json')
            
            # Save individual JSON file
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(parsed_data, indent=2, fp=f)
            
            print(f"Processed: {file_path}")
            return True
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")
        return False

def main():
    # Replace with your root directory path
    root_dir = '/Users/chim/Working/Thesis/Readings/src/scrape_newspapers/newspaper_articles'
    processed_count = 0
    
    # Walk through all directories
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.txt.met'):
                file_path = Path(root) / file
                if process_met_file(file_path):
                    processed_count += 1
    
    print(f"\nProcessed {processed_count} files successfully")

if __name__ == "__main__":
    main()