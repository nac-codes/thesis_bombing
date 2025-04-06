import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Read the data
print("Reading data...")
df = pd.read_csv('processed_data/raids_summary.csv')

# Extract target type based on BOOK field
print("Analyzing target types...")
# If BOOK contains INDUSTRIAL, it's area bombing (value 1), otherwise precision bombing (value 0)
df['IS_AREA_BOMBING'] = df['BOOK'].str.contains('INDUSTRIAL', case=False, na=False)

# Calculate total tonnage statistics
print("Calculating tonnage statistics...")
tonnage_stats = df['TOTAL_TONS'].describe()
print('Tonnage Statistics:')
print(tonnage_stats)

# Calculate incendiary percentage
print("Calculating incendiary percentages...")
df['INCENDIARY_TONS_SAFE'] = df['TOTAL_INCENDIARY_TONS'].fillna(0)
df['TOTAL_TONS_SAFE'] = df['TOTAL_TONS'].fillna(0)
df.loc[df['TOTAL_TONS_SAFE'] > 0, 'INCENDIARY_PERCENT'] = df['INCENDIARY_TONS_SAFE'] / df['TOTAL_TONS_SAFE'] * 100
df['INCENDIARY_PERCENT'] = df['INCENDIARY_PERCENT'].fillna(0)
# Clean negative values (likely data errors)
df.loc[df['INCENDIARY_PERCENT'] < 0, 'INCENDIARY_PERCENT'] = 0
incendiary_stats = df['INCENDIARY_PERCENT'].describe(percentiles=[.75, .9, .95, .99])
print('\nIncendiary Percentage Statistics:')
print(incendiary_stats)

# Count area bombing vs precision bombing targets
area_bombing_count = df['IS_AREA_BOMBING'].sum()
precision_bombing_count = len(df) - area_bombing_count
print(f'\nArea bombing targets (INDUSTRIAL book): {area_bombing_count}')
print(f'Precision bombing targets (other books): {precision_bombing_count}')
print(f'Total targets: {len(df)}')

# Create scoring system
print("\nCreating scoring system...")

# 1. Target designation score (1 for area bombing/industrial, 0 for precision bombing/non-industrial)
df['TARGET_SCORE'] = df['IS_AREA_BOMBING'].astype(int)

# 2. Tonnage score - using percentile-based approach
print("Calculating tonnage percentiles...")
df['TONNAGE_PERCENTILE'] = df['TOTAL_TONS'].rank(pct=True)
df['TONNAGE_SCORE'] = df['TONNAGE_PERCENTILE'] * 10

# 3. Custom incendiary score that emphasizes higher percentages
print("Calculating custom incendiary score...")
# First identify key thresholds in the incendiary percentage distribution
print("Incendiary percentage thresholds:")
inc_75th = incendiary_stats['75%']
inc_90th = incendiary_stats['90%']
inc_95th = incendiary_stats['95%']
inc_99th = incendiary_stats['99%']
print(f"75th percentile: {inc_75th:.2f}%")
print(f"90th percentile: {inc_90th:.2f}%")
print(f"95th percentile: {inc_95th:.2f}%")
print(f"99th percentile: {inc_99th:.2f}%")

# Custom function to score incendiary percentage
# This gives 0% incendiaries a score of 0
# Uses a stepped approach to emphasize higher percentages
def score_incendiary(value):
    if value <= 0:
        return 0.0
    
    # For values > 0, use a stepped approach with emphasis on higher percentages
    elif value < inc_75th:  # Bottom 75% of non-zero values
        # Linear mapping from 0-3 for non-zero values below 75th percentile
        return 3.0 * (value / inc_75th) if inc_75th > 0 else 3.0
    
    elif value < inc_90th:  # 75-90th percentile
        # Linear mapping from 3-5
        return 3.0 + 2.0 * ((value - inc_75th) / (inc_90th - inc_75th)) if inc_90th > inc_75th else 5.0
    
    elif value < inc_95th:  # 90-95th percentile
        # Linear mapping from 5-7
        return 5.0 + 2.0 * ((value - inc_90th) / (inc_95th - inc_90th)) if inc_95th > inc_90th else 7.0
    
    elif value < inc_99th:  # 95-99th percentile
        # Linear mapping from 7-9
        return 7.0 + 2.0 * ((value - inc_95th) / (inc_99th - inc_95th)) if inc_99th > inc_95th else 9.0
    
    else:  # Top 1% (≥ 99th percentile)
        # If 99th percentile is already 100%, give it a max score
        if inc_99th >= 99.9:
            return 10.0
        # Otherwise, linear mapping from 9-10 for top 1%
        else:
            max_inc = 100.0
            return min(10.0, 9.0 + 1.0 * ((value - inc_99th) / (max_inc - inc_99th)))

# Apply the custom scoring function
df['INCENDIARY_SCORE'] = df['INCENDIARY_PERCENT'].apply(score_incendiary)

# Print distribution of incendiary scores
print("\nIncendiary Score Distribution:")
inc_score_stats = df['INCENDIARY_SCORE'].describe(percentiles=[.25, .5, .75, .9, .95, .99])
print(inc_score_stats)

# Print counts of incendiary score ranges to better understand distribution
print("\nIncendiary Score Ranges:")
inc_ranges = [0, 0.01, 1, 3, 5, 7, 9, 10]
for i in range(len(inc_ranges) - 1):
    count = ((df['INCENDIARY_SCORE'] >= inc_ranges[i]) & (df['INCENDIARY_SCORE'] < inc_ranges[i+1])).sum()
    pct = count / len(df) * 100
    print(f"{inc_ranges[i]}-{inc_ranges[i+1]}: {count} raids ({pct:.1f}%)")

# Combined area bombing score (weighted average)
# Higher score = more likely to be area bombing
print("\nCalculating final area bombing score...")
df['AREA_BOMBING_SCORE'] = (
    0.4 * df['TARGET_SCORE'] * 10 +  # Scale to 0-10 (40% weight)
    0.3 * df['TONNAGE_SCORE'] +      # 30% weight
    0.3 * df['INCENDIARY_SCORE']     # 30% weight
).round(1)

# Normalize scores to ensure we have a range from 0-10
min_score = df['AREA_BOMBING_SCORE'].min()
max_score = df['AREA_BOMBING_SCORE'].max()
print(f"Raw score range: {min_score} to {max_score}")

df['AREA_BOMBING_SCORE_NORMALIZED'] = ((df['AREA_BOMBING_SCORE'] - min_score) / (max_score - min_score) * 10).round(1)

# Print results
print("\nArea Bombing Score Statistics (Raw):")
print(df['AREA_BOMBING_SCORE'].describe())

print("\nArea Bombing Score Statistics (Normalized 0-10):")
print(df['AREA_BOMBING_SCORE_NORMALIZED'].describe())

# Save results
print("\nSaving results...")
output_columns = ['target_location', 'target_name', 'BOOK', 'TOTAL_TONS', 
                 'INCENDIARY_PERCENT', 'TARGET_SCORE', 'TONNAGE_SCORE', 
                 'INCENDIARY_SCORE', 'AREA_BOMBING_SCORE', 'AREA_BOMBING_SCORE_NORMALIZED']

output_df = df[output_columns]
output_df.to_csv('processed_data/raids_area_bombing_classification.csv', index=False)

print("Analysis complete. Results saved to 'processed_data/raids_area_bombing_classification.csv'") 