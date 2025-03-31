# APPENDIX 1: Methodology for Attack Data

The following outlines the comprehensive methodology employed to create and analyze a digital database of strategic bombing missions during World War II. The process involved the collection of primary source data, optical character recognition (OCR) processing, data cleaning and validation, and the generation of analytical reports. Each step is detailed below, with references to the specific scripts used in the data processing pipeline.

## Data Collection

The foundational data for this thesis was derived from 8,134 photographs of original United States Strategic Bombing Survey (USSBS) computer printouts. These documents, housed at the National Archives in College Park, Maryland, contain detailed raid-level data of bombing missions "FROM THE FIRST ATTACK TO 'V-E' DAY." The photographs captured the following information per raid:

- Target identification (location, name, coordinates, and code)
- Mission details (date, time, air force, and squadron)
- Operational parameters (number of aircraft, altitude, sighting method, visibility, target priority)
- Detailed bomb loads (numbers, sizes, and tonnages of high explosive, incendiary, and fragmentation munitions)

An example of these computer printouts is shown in Figure 2.1.

![USSBS Computer Printout Example](./attack_data/IMG_0387.JPG)
*Figure 2.1: Example of USSBS computer printout showing detailed raid data.*

The photographs were systematically organized into directories based on boxes, books, and images to maintain a coherent data structure for subsequent processing.

## Optical Character Recognition (OCR)

To convert the photographed tables into machine-readable text, we employed OCR techniques using Azure's Form Recognizer service. The service was chosen for its capability to handle complex table structures and handwritten components.

### Processing with Azure Form Recognizer

The script [`send_to_azure.py`](attack_data/send_to_azure.py) was developed to automate the submission of images to the Azure service.

```python
# Excerpt from send_to_azure.py

document_analysis_client = DocumentAnalysisClient(
    endpoint=endpoint, credential=AzureKeyCredential(key)
)

def analyze_document(image_path):
    ...
    poller = document_analysis_client.begin_analyze_document(
        "prebuilt-layout", document=image_file
    )
    result = poller.result()
    ...
```

This script navigated through the directory of images, sent each image to Azure for processing, and stored the resulting JSON outputs containing the extracted data.

## Data Processing Pipeline

The data processing involved several stages to transform the raw OCR outputs into a clean, structured dataset suitable for analysis. The main steps included:

1. Extracting and organizing metadata and table data from the OCR outputs.
2. Correcting OCR errors and filling missing values using deterministic methods and language models.
3. Validating and cleaning the data to ensure consistency and accuracy.
4. Combining individual tables into a consolidated dataset.
5. Identifying and handling outliers and summation rows.
6. Generating analytical reports and visualizations.

### Extracting and Organizing Data

The initial processing of Azure's OCR output was handled by [`process_ocr.py`](attack_data/process_ocr.py). This script was responsible for two critical tasks: extracting metadata about the target and identifying the correct data table from the OCR output.

Azure Form Recognizer returns a structured JSON object containing detected tables, text blocks, and their spatial relationships on the page. While this provides a good foundation, the script needed to handle several complexities:

1. **Table Identification**: The script searched for tables containing exactly 23 columns matching our expected format:
```python
# Excerpt from process_ocr.py
expected_column_names = [
    "DATE OF ATTACK DAY", "MO", "YR", "TIME OF ATTACK", "AIR FORCE", 
    "GROUP OR SQUADRON NUMBER", "NUMBER OF AIRCRAFT BOMBING", 
    "ALTITUDE OF RELEASE IN HUND. FT.", "SIGHTING", "VISIBILITY OF TARGET", 
    "TARGET PRIORITY", "HIGH EXPLOSIVE BOMBS NUMBER", "SIZE", "TONS",
    "FUZING NOSE", "TAIL", "INCENDIARY BOMBS NUMBER", "SIZE", "TONS",
    "FRAGMENTATION BOMBS NUMBER", "SIZE", "TONS", "TOTAL TONS"
]
```

The script used fuzzy string matching to identify the correct table and column alignment, as OCR sometimes misread column headers:

```python
def find_table_with_23_columns(ocr_data, expected_names):
    best_match_score = 0
    best_match_table = None
    
    for table in ocr_data.get("tables", []):
        # Calculate fuzzy match scores between expected and found columns
        avg_score = calculate_column_match_score(table, expected_names)
        if avg_score > best_match_score:
            best_match_score = avg_score
            best_match_table = table
```

2. **Metadata Extraction**: Each page contained critical target information (location, name, coordinates, and target code) that needed to be extracted. The script used GPT-4o to help parse this information accurately:

```python
def extract_target_info(ocr_data, jpg_file):
    # Construct prompt for GPT-4 with the page content
    prompt = f"""Extract the following target information from this text:
    - Target Location
    - Target Name
    - Latitude
    - Longitude
    - Target Code
    
    Text: {page_text}
    """
    
    # Use GPT to extract structured information
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
```

3. **Data Organization**: The extracted data was organized into a structured format with two main components:
   - Metadata dictionary containing target information
   - Table data containing the actual bombing mission details

The script saved this information in two formats:
- A JSON file (`extracted_data.json`) containing both metadata and table data
- A CSV file (`table_data.csv`) containing just the table data for easier processing

```python
def save_csv(data, filename):
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(data.keys())
        writer.writerows(zip(*data.values()))

def save_json(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
```

This initial processing stage was critical for ensuring data quality and consistency. The script included extensive logging to track any issues or anomalies in the extraction process, allowing for manual review when necessary. The output files were organized in a directory structure that maintained the relationship between original images and extracted data:

```
original_image.JPG
original_image_output/
    ├── extracted_data.json
    └── table_data.csv
```

This structured approach to data extraction provided a solid foundation for subsequent processing steps, ensuring that both the tabular data and contextual metadata were accurately preserved.

### Validating and Correcting Data Fields

After initial extraction, each table underwent a rigorous validation and correction process using [`process_table.py`](attack_data/process_table.py). This script implemented a sophisticated field-by-field validation system with specific rules for each column type.

1. **Field-Specific Validation Rules**: Each column had its own validation function with precise expectations:

```python
def check_AIR_FORCE(value, is_required, is_RAF):
    # Expected: 8, 9, 12, 15 for US Air Forces, or R for Royal Air Force
    if pd.isna(value):
        if is_required:
            if is_RAF:
                return False, "AIR FORCE is required. Could be 8, 9, 12, 15, or R. Potentially is R."
            else:
                return False, "AIR FORCE is required. Should be 8, 9, 12, or 15. Potentially is 8."
    # Additional validation logic...

def check_DAY(value, is_required):
    # Expected: Single day (1-31) or a range (e.g., 15-16)
    if pd.isna(value):
        return not is_required, "DAY is required. Should be a number between 1 and 31 or a range (e.g., 15-16)."
    # Additional validation logic...
```

2. **Contextual Error Correction**: When errors were detected, the script used GPT-4o-mini with highly specific prompts that included:
   - The expected format and valid values for the field
   - Values from surrounding rows in the same column for context
   - Related values from the same row (e.g., bomb numbers and tonnage)
   - Historical patterns from similar entries

For example, when correcting Air Force designations, the prompt would look like this:

```python
prompt = f"""Correct the Air Force designation.
Current value: {value}
Valid options: 8, 9, 12, 15 (US Air Forces) or R (Royal Air Force)
Previous 3 rows in column: {previous_values}
Next 3 rows in column: {next_values}
Target location: {target_location}
Date of attack: {attack_date}

Please select the most likely correct value from the valid options."""
```

3. **Mathematical Validation**: For bomb-related data, the script implemented cross-field validation to ensure internal consistency:

```python
def check_TONNAGE(row):
    # Validate that individual tonnages sum to total
    he_tons = row['HIGH EXPLOSIVE BOMBS TONS']
    inc_tons = row['INCENDIARY BOMBS TONS']
    frag_tons = row['FRAGMENTATION BOMBS TONS']
    total_tons = row['TOTAL TONS']
    
    calculated_total = sum([he_tons, inc_tons, frag_tons])
    if abs(calculated_total - total_tons) > 0.1:
        return False, f"Total tons ({total_tons}) does not match sum of individual tonnages ({calculated_total})"
    return True, None
```

4. **Iterative Correction Process**: The script processed each row multiple times if necessary:
   - First pass: Basic validation and correction of individual fields
   - Second pass: Cross-field validation (e.g., tonnage calculations)
   - Final pass: Overall consistency check

This meticulous approach to data validation and correction significantly reduced errors while maintaining the integrity of the historical data. By providing GPT-4o-mini with specific constraints and contextual information, we minimized the risk of hallucinated values and ensured corrections were historically plausible.

The script maintained detailed logs of all corrections, allowing for manual review of significant changes:

```python
logging.info(f"Row {row_idx + 1}: Corrected Value for '{col}': {corrected_value}")
```

This combination of deterministic validation rules and context-aware AI assistance proved highly effective in cleaning the OCR output while preserving the historical accuracy of the data.

### Deterministic Validation and Correction

A critical aspect of data validation involved the mathematical relationships between bomb quantities, sizes, and tonnages. The script [`post_process_2.py`](attack_data/post_process_2.py) implemented a sophisticated system to validate and correct these interrelated values using known bomb specifications from the period.

#### Bomb Weight Mappings

First, we established a comprehensive mapping of bomb size codes to their actual weights in pounds:

```python
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
```

This was derived from the index of the USSBS computer printouts:

![USSBS Computer Printout Index](attack_data/IMG_0089.JPG)

#### Validation Process

For each row in the dataset, the script performed a three-way validation between:
- Number of bombs
- Bomb size (which mapped to weight in pounds)
- Total tonnage

The process worked as follows:

1. **Calculate Expected Values**: For each combination of two known values, calculate the expected third value:
```python
def get_expected_values(row, bomb_type):
    tonnage = row[f'{bomb_type} BOMBS TONS']
    number = row[f'{bomb_type} BOMBS NUMBER']
    size_code = row[f'{bomb_type} BOMBS SIZE']
    
    # If we have tonnage and number, calculate expected size
    if not pd.isna(tonnage) and not pd.isna(number):
        expected_size = size_code
        expected_tonnage = tonnage
        expected_number = number
    # If we have tonnage but no number, calculate expected number
    elif not pd.isna(tonnage) and pd.isna(number):
        expected_size = size_code
        expected_tonnage = tonnage
        expected_number = (tonnage * 2000) / weight  # Convert tons to pounds
    # If we have number but no tonnage, calculate expected tonnage
    elif pd.isna(tonnage) and not pd.isna(number):
        expected_size = size_code
        expected_tonnage = (number * weight) / 2000  # Convert pounds to tons
        expected_number = number
```

2. **Fuzzy Matching**: Compare each calculated combination against the original OCR values to find the best match:
```python
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
```

This approach sometimes produced mathematically correct but historically implausible values (such as fractional numbers of bombs). However, by using fuzzy string matching to compare the calculated values against the original OCR output, the script typically selected the most historically accurate combination. For example:

- Original OCR: `{number: 24, size: 3, tons: 6.0}`
- Calculated options:
  1. `{number: 24, size: 3, tons: 6.0}` - Score: 300
  2. `{number: 24.5, size: 3, tons: 5.9}` - Score: 250
  3. `{number: 23.8, size: 3, tons: 6.1}` - Score: 240

The first option would be selected as it best matches the original OCR values while maintaining mathematical consistency.

The script logged all corrections for manual review:
```python
logging.debug(f"Original values: {original_values}")
logging.debug(f"Calculated options: {expected_values_list}")
logging.debug(f"Selected best match: {best_match}")
```

This deterministic approach to validation proved particularly effective for correcting GPT-4o-mini hallucinations, as it leveraged both mathematical relationships and historical accuracy through fuzzy matching against the original values.

### Combining Data into a Consolidated Dataset

After processing individual tables, the script [`combine.py`](attack_data/combine.py) aggregated the data into a single comprehensive CSV file.

It outputted two CSV files:
- [`combined_attack_data_complete_checked.csv`](attack_data/combined_attack_data_complete_checked.csv): A detailed dataset which includes all the original data fields, including tonnage.
- [`combined_attack_data.csv`](attack_data/combined_attack_data.csv): A simplified dataset which includes only the most important fields for analysis. Reduced tonnage data to being binary (0 or 1) for high explosive, incendiary, and fragmentation bombs.

This script handled file system traversal, read individual CSV files, and concatenated them while preserving relevant metadata.

### Final Manual Review and Outlier Detection

The final step in data cleaning involved manual verification of statistical outliers using [`check_attacka_data.py`](attack_data/check_attacka_data.py). This was particularly important for handling summation rows—entries that represented mission totals rather than individual sorties—which occasionally escaped automated detection.

The script facilitated this review process in several ways:

1. **Statistical Detection**: For each bomb type (high explosive, incendiary, and fragmentation), the script identified statistical outliers:
```python
def find_outliers(data, column):
    mean = np.mean(data[column])
    std = np.std(data[column])
    outliers = data[data[column] > mean + 2*std]
    return outliers.sort_values(by=column, ascending=False)
```

2. **Contextual Review**: For each outlier, the script displayed:
   - The full table from the original image
   - Target information and date
   - Surrounding entries for context
   - The original photograph for verification

3. **Interactive Correction**: Users could:
   - Mark entries as summation rows (removing them from the dataset)
   - Correct erroneous values
   - Verify legitimate high-tonnage missions

The script generated distribution plots for each bomb type, helping identify unusual patterns:

```python
plot_distribution(
    data,
    f'Distribution of {bomb_type}',
    'reports/tons/',
    f'tonnage_distribution_{bomb_type.lower().replace(" ", "_")}.png'
)
```

This final manual review was particularly effective at catching aggregated entries that had slipped through automated detection, ensuring the final dataset limited the amount of double-counting.

The processed and validated dataset may be found at: [`combined_attack_data_complete_checked.csv`](attack_data/combined_attack_data_complete_checked.csv)

### Categorizing Area vs. Precision Bombing

A critical methodological challenge was determining whether each mission should be categorized as "area" or "precision" bombing. Initially, we considered using a simple ratio of incendiary to high explosive/fragmentary bombs as the determining factor. However, this approach proved inadequate as it failed to capture the sophisticated tactics employed in area bombing campaigns.

Historical evidence shows that the most devastating area raids deliberately combined both high explosive and incendiary bombs. As described in contemporary accounts, high explosive bombs would first demolish roofs and windows, creating optimal conditions for incendiary bombs to penetrate buildings and initiate urban firestorms. These tactical combinations turned targeted structures into "giant cauldrons" that became epicenters of devastating urban fires (See: [Hansen, *Fury*](./corpora_cited/hansen_fury/chunks/hansen_fury_0078.txt), [Davis, *Spaatz*](./corpora_cited/davis_spaatz/chunks/davis_spaatz_0810.txt)).

Given this historical context, we developed a more nuanced categorization algorithm that considers both temporal and spatial relationships between raids. The algorithm, implemented in [`categorize_bombing.py`](attack_data/categorize_bombing.py), uses the following logic:

1. Any mission that deployed incendiary bombs is automatically categorized as "area" bombing
2. For missions using only high explosive bombs, the algorithm:
   - Examines all other missions targeting the same location
   - Uses a 4-hour time window before and after the mission
   - If any related mission within this window used incendiaries, categorizes the mission as "area" bombing
   - Only if no related missions used incendiaries is the mission categorized as "precision" bombing

```python
def categorize_mission(row, df, time_window_hours=4):
    # First check if this mission used incendiaries
    if row['INCENDIARY BOMBS NUMBER'] > 0:
        return 'area'
    
    # Check other missions at same target within time window
    time_window_start = mission_time - timedelta(hours=time_window_hours)
    time_window_end = mission_time + timedelta(hours=time_window_hours)
    
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
    
    return 'precision'
```

This generous approach to identifying area bombing does have limitations. For instance, some oil refinery raids that used small quantities of incendiary bombs—presumably to ignite petroleum products as part of precise targeting—are categorized as "area" bombing despite potentially being more accurately described as precision attacks. However, these edge cases represent a relatively small portion of the overall dataset, and the categorization still provides a valuable analytical framework for understanding strategic bombing patterns.

