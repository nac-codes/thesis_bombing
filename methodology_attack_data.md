# APPENDIX 1: Methodology for USAAF Strategic Bombing Data

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

### Post-Processing and Data Correction

After initial extraction and organization, the data required extensive cleaning and correction to address OCR errors, inconsistencies, and missing values. This stage of the pipeline involved several key scripts:

1. **`process_table.py`**: Validated and corrected individual table data, applying field-specific validation rules and using GPT-4o-mini for contextual error correction.

2. **`post_process_2.py`**: Implemented deterministic validation based on mathematical relationships between bomb quantities, sizes, and tonnages using known bomb specifications from the period.

3. **`combine.py`**: Aggregated all processed tables into a single comprehensive dataset while preserving relevant metadata.

4. **`check_attacka_data.py`**: Performed statistical anomaly detection and facilitated manual review of outliers.

5. **`fill_missing_targets.py`**: Addressed missing target information by carrying forward values from previous records where appropriate:

```python
# Excerpt from fill_missing_targets.py
# Check if target_location (index 3) is empty
if row[3].strip() == "":
    # If the current row has target_name but not target_location
    if row[4].strip() != "":
        # Update previous target_name
        prev_target_name = row[4]
        # Use previous target_location
        row[3] = prev_target_location
    else:
        # Both fields are empty
        row[3] = prev_target_location
        row[4] = prev_target_name
```

6. **`fix_missing_years.py`**: Corrected missing or invalid year values to ensure temporal consistency:

```python
# Excerpt from fix_missing_years.py
# Check if YEAR field (index 10) is empty
if len(row) > 10 and (row[10].strip() == "" or row[10].strip() == "."):
    row[10] = "0"
```

These data cleaning steps produced increasingly refined datasets:
- `combined_attack_data_checked.csv`: Initial consolidated dataset with validation checks
- `combined_attack_data_filled.csv`: Dataset with missing target information filled
- `combined_attack_data_corrected.csv`: Final cleaned dataset with corrected years and other values

### Location-Based Organization

To facilitate geospatial analysis, the script `organize_by_location.py` created separate CSV files for each unique target location:

```python
# Excerpt from organize_by_location.py
# Process each unique location
locations = df['target_location'].unique()

for location in locations:
    # Clean and process location name
    clean_location = ' '.join(word.capitalize() for word in location.strip().split())
    
    # Create safe filename
    safe_filename = re.sub(r'[^\w\s-]', '', clean_location).strip().replace(' ', '_')
    output_file = os.path.join(locations_dir, f"{safe_filename}.csv")
    
    # Get all data for this location
    location_data = df[df['target_location'] == location].copy()
    
    # Sort by date and time
    location_data = location_data.sort_values(by=['YEAR', 'MONTH', 'DAY', 'TIME OF ATTACK'])
    
    # Save to CSV
    location_data.to_csv(output_file, index=False)
```

This organization allowed for efficient city-level analysis and visualization of bombing patterns throughout the war.

## Data Analysis and Categorization

The cleaned dataset was then subjected to more sophisticated analyses to identify patterns and assess the nature of bombing operations. This phase involved several key analytical steps:

### Raid Identification and Aggregation

The script `process_raids.py` identified and aggregated related bombing missions into coherent raids:

```python
# Excerpt from process_raids.py
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
```

This process allowed for the calculation of aggregate raid statistics, including total aircraft, average altitude, and tonnage by bomb type:

```python
# Excerpt from process_raids.py
def aggregate_raid_data(raid_rows):
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
```

### Advanced Bombing Classification

A significant methodological innovation was the development of a nuanced classification system for bombing missions. Initially, we considered using a simple binary "area" vs. "precision" categorization, but historical evidence indicated that bombing tactics existed on a spectrum.

The original approach in `categorize_bombing.py` used a basic rule-based system:

```python
# Excerpt from categorize_bombing.py
def categorize_mission(row, df, time_window_hours=4):
    # First check if this mission used incendiaries
    if row['INCENDIARY BOMBS NUMBER'] > 0:
        return 'area'
    
    # Check other missions at the same target within the time window
    time_window_start = mission_time - timedelta(hours=time_window_hours)
    time_window_end = mission_time + timedelta(hours=time_window_hours)
    
    # If any related mission used incendiaries, categorize as area bombing
    if (related_missions['INCENDIARY BOMBS NUMBER'] > 0).any():
        return 'area'
    
    # If we get here, it's precision bombing
    return 'precision'
```

This was later refined in `visualize_usaaf_bombing.py` to implement a three-dimensional scoring algorithm that considered:

1. **Target designation**: Whether the target was categorized as an industrial/city area attack
2. **Incendiary proportion**: The percentage of incendiary munitions relative to total tonnage
3. **Total tonnage**: Whether excessive tonnage was employed compared to operational norms

```python
# Excerpt from visualize_usaaf_bombing.py
# Create target type score
df['TARGET_SCORE'] = (df['CATEGORY'].str.lower().str.contains('industrial')).astype(int)

# Create incendiary score (0-10 scale)
df['INCENDIARY_PERCENT'] = (df['TOTAL_INCENDIARY_TONS'] / df['TOTAL_TONS'] * 100).fillna(0)
df['INCENDIARY_SCORE'] = np.clip(df['INCENDIARY_PERCENT'] / 10, 0, 10)

# Create tonnage score (0-10 scale)
tonnage_threshold = df['TOTAL_TONS'].quantile(0.95)  # 95th percentile
df['TONNAGE_SCORE'] = np.clip(df['TOTAL_TONS'] / tonnage_threshold * 10, 0, 10)

# Create combined area bombing score (weighted average)
df['AREA_BOMBING_SCORE'] = (
    (0.3 * df['TARGET_SCORE'] * 10) +  # Target type (0 or 3)
    (0.5 * df['INCENDIARY_SCORE']) +   # Incendiary percentage (0-5)
    (0.2 * df['TONNAGE_SCORE'])        # Tonnage score (0-2)
)

# Normalize score to 0-10 scale
df['AREA_BOMBING_SCORE_NORMALIZED'] = df['AREA_BOMBING_SCORE']
```

This approach allowed missions to be classified on a continuous scale from 0 (precise bombing) to 10 (heavy area bombing). The scores were then bucketed into five categories:

```python
# Add score category to data
df['Score Category'] = pd.cut(df['AREA_BOMBING_SCORE_NORMALIZED'], 
                             bins=[0, 2, 4, 6, 8, 10],
                             labels=['Very Precise (0-2)', 'Precise (2-4)', 
                                    'Mixed (4-6)', 'Area (6-8)', 'Heavy Area (8-10)'])
```

This multidimensional approach provided a more nuanced and historically accurate representation of bombing character beyond the binary classification often employed in historical narratives.

## Data Visualization and Dashboard Development

The final stage of the methodology involved creating comprehensive visualizations and an interactive dashboard to explore the data.

### Visualization Scripts

Several specialized scripts were developed to generate visualizations focused on different aspects of the bombing campaign:

1. **`visualize_bombing_classification.py`**: Generated plots comparing area and precision bombing patterns.

2. **`visualize_bombing_by_year_category_city.py`**: Created visualizations breaking down bombing patterns by year, target category, and city.

3. **`visualize_usaaf_bombing.py`**: The primary visualization script that implemented the area bombing scoring algorithm and generated a comprehensive set of plots organized by:
   - Year
   - Target category
   - City
   - General trends

This script generated a wide range of visualization types:
- Histograms of area bombing scores
- Scatter plots of tonnage vs. incendiary percentage
- Box plots of scores by target type
- Pie charts of bombing category distributions
- Radar charts of component scores
- Time series of bombing evolution

### Interactive Dashboard

To make the data accessible to researchers and the public, the script `app.py` implemented a Streamlit-based web application:

```python
# Excerpt from app.py
# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Select a section:",
    ["General Analysis", "City Analysis", "Category Analysis", "Year Analysis", "Data Download"]
)

# Load data for filters
df = load_data()
cities = sorted(df["target_location"].unique())
categories = sorted(df["CATEGORY"].unique())
years = sorted([y for y in range(1940, 1946)])
```

The dashboard provides several key features:
- Interactive filtering by city, target category, and year
- Detailed visualizations for each filter context
- Data table views with search capabilities
- Summary statistics for filtered data subsets
- Data download options for further analysis

This dashboard is publicly accessible at https://strategic-bombing-data.streamlit.app/, enabling researchers to independently verify findings and conduct their own analyses.

## Conclusion

The methodology described here represents a comprehensive approach to digitizing, processing, and analyzing historical bombing records. By combining advanced OCR technology, rigorous data cleaning, sophisticated classification algorithms, and interactive visualization tools, we have created a robust framework for understanding the patterns and evolution of strategic bombing campaigns during World War II.

The resulting dataset and analytical tools provide an unprecedented level of detail and accessibility to this historical data, allowing for more nuanced and data-driven assessments of bombing doctrine and practice. This approach moves beyond selective examples and theoretical frameworks to provide a comprehensive empirical foundation for historical analysis.

