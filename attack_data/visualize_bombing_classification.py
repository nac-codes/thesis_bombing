import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("viridis")

# Load the data
print("Loading data...")
df = pd.read_csv('processed_data/raids_area_bombing_classification.csv')

# Create directory for plots
if not os.path.exists('plots'):
    os.makedirs('plots')

# 1. Distribution of Normalized Area Bombing Scores
print("Creating distribution plot...")
plt.figure(figsize=(12, 6))
sns.histplot(df['AREA_BOMBING_SCORE_NORMALIZED'], bins=20, kde=True)
plt.title('Distribution of Area Bombing Scores', fontsize=16)
plt.xlabel('Area Bombing Score (10 = Clear Area Bombing, 0 = Precise Bombing)', fontsize=12)
plt.ylabel('Count', fontsize=12)
plt.axvline(df['AREA_BOMBING_SCORE_NORMALIZED'].median(), color='red', linestyle='--', 
           label=f'Median: {df["AREA_BOMBING_SCORE_NORMALIZED"].median():.1f}')
plt.legend()
plt.tight_layout()
plt.savefig('plots/area_bombing_score_distribution.png', dpi=300)

# 2. Scatter plot of Tonnage vs Incendiary Percentage, colored by Area Bombing Score
print("Creating scatter plot...")
plt.figure(figsize=(12, 8))
scatter = plt.scatter(df['TOTAL_TONS'].clip(0, 500), 
                     df['INCENDIARY_PERCENT'].clip(0, 100), 
                     c=df['AREA_BOMBING_SCORE_NORMALIZED'], 
                     alpha=0.6, 
                     cmap='viridis', 
                     s=30)
plt.colorbar(scatter, label='Area Bombing Score')
plt.title('Tonnage vs Incendiary Percentage', fontsize=16)
plt.xlabel('Total Tons (clipped at 500)', fontsize=12)
plt.ylabel('Incendiary Percentage', fontsize=12)
plt.tight_layout()
plt.savefig('plots/tonnage_vs_incendiary.png', dpi=300)

# 3. Box plot of Area Bombing Scores by Industrial vs Non-Industrial targets
print("Creating box plot...")
plt.figure(figsize=(10, 6))
df['Target Type'] = df['TARGET_SCORE'].map({1: 'Industrial/Area', 0: 'Non-Industrial/Precision'})
sns.boxplot(x='Target Type', y='AREA_BOMBING_SCORE_NORMALIZED', data=df)
plt.title('Area Bombing Scores by Target Type', fontsize=16)
plt.xlabel('Target Type', fontsize=12)
plt.ylabel('Area Bombing Score', fontsize=12)
plt.tight_layout()
plt.savefig('plots/area_bombing_by_target_type.png', dpi=300)

# 4. Create a table of sample raids with different area bombing scores
print("Creating table of example raids...")
score_ranges = [(8, 10), (6, 8), (4, 6), (2, 4), (0, 2)]
examples = []

for low, high in score_ranges:
    subset = df[(df['AREA_BOMBING_SCORE_NORMALIZED'] >= low) & 
               (df['AREA_BOMBING_SCORE_NORMALIZED'] < high)]
    if len(subset) > 0:
        # Sample multiple raids from each range to get representative examples
        examples.append(subset.sample(min(3, len(subset))))

example_df = pd.concat(examples)
example_df = example_df.sort_values('AREA_BOMBING_SCORE_NORMALIZED', ascending=False)

# Print example table
print("\nExample raids across the precision-to-area bombing continuum:")
print(example_df[['target_location', 'target_name', 'TARGET_SCORE', 'TONNAGE_SCORE', 
                 'INCENDIARY_SCORE', 'AREA_BOMBING_SCORE_NORMALIZED']].to_string())

# Save examples to CSV
example_df.to_csv('plots/example_raids.csv', index=False)

# 5. Heatmap of score components correlation
print("Creating correlation heatmap...")
correlation_data = df[['TARGET_SCORE', 'TONNAGE_SCORE', 'INCENDIARY_SCORE', 
                       'AREA_BOMBING_SCORE', 'AREA_BOMBING_SCORE_NORMALIZED']]
    
plt.figure(figsize=(10, 8))
sns.heatmap(correlation_data.corr(), annot=True, cmap='coolwarm', fmt='.2f')
plt.title('Correlation Between Scoring Components', fontsize=16)
plt.tight_layout()
plt.savefig('plots/correlation_heatmap.png', dpi=300)

# 6. Bar chart of distribution by score category
print("Creating bar chart of score categories...")
df['Score Category'] = pd.cut(df['AREA_BOMBING_SCORE_NORMALIZED'], 
                             bins=[0, 2, 4, 6, 8, 10],
                             labels=['Very Precise (0-2)', 'Precise (2-4)', 
                                    'Mixed (4-6)', 'Area (6-8)', 'Heavy Area (8-10)'])

category_counts = df['Score Category'].value_counts().sort_index()
plt.figure(figsize=(12, 6))
sns.barplot(x=category_counts.index, y=category_counts.values)
plt.title('Distribution of Raids by Bombing Type', fontsize=16)
plt.xlabel('Bombing Category', fontsize=12)
plt.ylabel('Number of Raids', fontsize=12)
plt.xticks(rotation=45)
for i, v in enumerate(category_counts.values):
    plt.text(i, v + 100, f"{v:,}", ha='center')
plt.tight_layout()
plt.savefig('plots/bombing_category_distribution.png', dpi=300)

# 7. 3D component visualization
print("Creating 3D component visualization...")
fig = plt.figure(figsize=(12, 10))
ax = fig.add_subplot(111, projection='3d')

# Sample a subset of data for clearer visualization
sample_size = min(5000, len(df))
df_sample = df.sample(sample_size)

# Create scatter plot
scatter = ax.scatter(
    df_sample['TARGET_SCORE'] * 10,  # Scale to 0-10
    df_sample['TONNAGE_SCORE'],
    df_sample['INCENDIARY_SCORE'],
    c=df_sample['AREA_BOMBING_SCORE_NORMALIZED'],
    cmap='viridis',
    s=30,
    alpha=0.6
)

# Add labels and colorbar
ax.set_xlabel('Target Type Score (0=Precision, 10=Area)', fontsize=12)
ax.set_ylabel('Tonnage Score', fontsize=12)
ax.set_zlabel('Incendiary Score', fontsize=12)
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.set_zlim(0, 10)
plt.colorbar(scatter, label='Area Bombing Score')
plt.title('3D Visualization of Bombing Score Components', fontsize=16)
plt.tight_layout()
plt.savefig('plots/3d_component_visualization.png', dpi=300)

print("\nVisualization complete. Plots saved to 'plots/' directory.") 