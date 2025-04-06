import pandas as pd
import os

print("Filtering data for USAAF raids only...")

# Step 1: Load the classification data with categories
raids_classification = pd.read_csv('processed_data/raids_area_bombing_classification_with_category.csv')
raids_summary = pd.read_csv('processed_data/raids_summary.csv')

# Create unique identifiers for joining
raids_classification['raid_id'] = raids_classification.index
raids_summary['raid_id'] = raids_summary.index

# Step 2: Merge to get Air Force information
print("Merging datasets to get Air Force information...")
merged_data = pd.merge(
    raids_classification,
    raids_summary[['raid_id', 'AIR FORCE', 'DAY', 'MONTH', 'YEAR', 'TIME OF ATTACK', 'AVG_ALTITUDE', 'TOTAL_AIRCRAFT']],
    on='raid_id',
    how='left'
)

# Step 3: Filter for USAAF raids (anything except "R")
print("Filtering for USAAF raids...")
usaaf_data = merged_data[merged_data['AIR FORCE'] != 'R'].copy()

# Check counts before and after filtering
total_raids = len(merged_data)
usaaf_raids = len(usaaf_data)
raf_raids = total_raids - usaaf_raids

print(f"Total raids: {total_raids}")
print(f"USAAF raids: {usaaf_raids} ({usaaf_raids/total_raids*100:.1f}%)")
print(f"RAF raids (filtered out): {raf_raids} ({raf_raids/total_raids*100:.1f}%)")

# Create output directory if it doesn't exist
output_dir = 'processed_data/usaaf'
os.makedirs(output_dir, exist_ok=True)

# Step 4: Save filtered data
# Save full merged dataset with all columns
print("Saving filtered USAAF dataset...")
usaaf_data.to_csv(f'{output_dir}/usaaf_raids_full.csv', index=False)

# Save with same columns as original classification file for compatibility with existing scripts

usaaf_data.to_csv(f'{output_dir}/usaaf_raids_classification_with_category.csv', index=False)

print("USAAF filtering complete. Files saved to processed_data/usaaf directory.")

# Calculate and display some basic statistics for the filtered data
print("\nUSAAF Bombing Statistics:")
print(f"Average area bombing score: {usaaf_data['AREA_BOMBING_SCORE_NORMALIZED'].mean():.2f}")

# Category distribution
print("\nBombing Category Distribution (USAAF):")
usaaf_data['Score Category'] = pd.cut(usaaf_data['AREA_BOMBING_SCORE_NORMALIZED'], 
                             bins=[0, 2, 4, 6, 8, 10],
                             labels=['Very Precise (0-2)', 'Precise (2-4)', 
                                    'Mixed (4-6)', 'Area (6-8)', 'Heavy Area (8-10)'])

category_counts = usaaf_data['Score Category'].value_counts().sort_index()
for category, count in category_counts.items():
    percentage = count / len(usaaf_data) * 100
    print(f"{category}: {count} raids ({percentage:.1f}%)") 