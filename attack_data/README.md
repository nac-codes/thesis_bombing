# USAAF Bombing Campaign Analysis Dashboard

A Streamlit app for visualizing and exploring the United States Army Air Forces (USAAF) bombing campaigns during World War II, with a focus on the evolution of precision vs. area bombing strategies.

## Features

- Interactive dashboard of pre-generated visualizations from USAAF bombing campaign data
- Filter and explore data by city, target category, and year
- Special analysis section for Schweinfurt raids
- Download options for raw data
- Comprehensive visualization of bombing patterns, tonnage, and bombing strategies

## Installation

1. Clone this repository:
   ```
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the Streamlit app:
   ```
   streamlit run app.py
   ```

## Data Structure

The dashboard uses pre-generated visualizations stored in the following directory structure:

```
plots/
└── usaaf/
    ├── general/         # Overall analysis visualizations
    ├── cities/          # City-specific visualizations
    │   └── schweinfurt/ # Special analysis for Schweinfurt
    ├── categories/      # Target category visualizations
    └── years/           # Yearly analysis visualizations
```

## Data Sources

The app uses two main data sources:

1. `combined_attack_data.csv` - Original combined bombing data
2. `processed_data/usaaf/usaaf_raids_full.csv` - Processed USAAF bombing raid data with area bombing classifications

## Data Quality Note

This data was derived from historical bombing records and has some limitations:
- Contains OCR errors from original documents
- May include misreadings of original records
- Could have processing/interpretation errors

Despite these limitations, the dataset provides a robust overall picture of USAAF bombing campaigns during World War II.

## Usage

The dashboard is organized into several sections:

1. **General Analysis**: Overview of bombing patterns, tonnage distribution, and temporal trends
2. **City Analysis**: Detailed analysis of specific cities with bombing metrics
3. **Category Analysis**: Analysis of bombing patterns by target category
4. **Year Analysis**: Yearly breakdown of bombing strategies
5. **Data Download**: Access to the raw datasets

## License

[Specify your license here]

## Acknowledgments

[Add any acknowledgments or credits here] 