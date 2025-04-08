import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.ticker import MaxNLocator

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("viridis")
plt.rcParams['figure.figsize'] = [12, 8]
plt.rcParams['figure.dpi'] = 300

# Create directory for plots
os.makedirs('plots/raid_frequency/bombing_scores', exist_ok=True)

# Load USAAF data
print("Loading USAAF-only data...")
df = pd.read_csv('processed_data/usaaf/usaaf_raids_full.csv')

# Clean up year data
print("Cleaning year and date data...")
df['YEAR'] = df['YEAR'].fillna(0).astype(float)
df['Year'] = (1940 + df['YEAR']).astype(int)
# Handle any outlier years
df.loc[df['Year'] < 1941, 'Year'] = 1941
df.loc[df['Year'] > 1946, 'Year'] = 1945

# Clean up month data
df['MONTH'] = df['MONTH'].fillna(1).astype(float).astype(int)
df['Month'] = df['MONTH'].clip(1, 12)  # Ensure valid month values

# Clean up day data
def clean_day(day_value):
    if pd.isna(day_value):
        return 1
    day_str = str(day_value)
    if '-' in day_str:
        day_str = day_str.split('-')[0]
    try:
        return int(float(day_str))
    except (ValueError, TypeError):
        return 1

df['DAY'] = df['DAY'].apply(clean_day)
df['Day'] = df['DAY'].clip(1, 31)  # Ensure valid day values

# Create a clean location field
df['Location'] = df['target_location'].str.strip().str.upper()

# Create date fields
df['Date'] = pd.to_datetime(
    df['Year'].astype(str) + '-' + 
    df['Month'].astype(str).str.zfill(2) + '-' + 
    df['Day'].astype(str).str.zfill(2),
    errors='coerce'
)

# Create quarter-year field manually
df['Year_Quarter'] = df['Year'].astype(str) + '-Q' + ((df['Month']-1)//3 + 1).astype(str)
# Create quarter field - use string representation instead of PeriodIndex
df['Quarter'] = df['Year'].astype(str) + 'Q' + ((df['Month']-1)//3 + 1).astype(str)

print("Analyzing bombing scores in relation to raid frequency and tonnage...")

# 1. Create a scatter plot using area bombing scores instead of average tons per raid
print("Creating bombing score visualizations...")

# Get all locations with at least 3 raids
location_counts = df['Location'].value_counts()
locations_with_sufficient_data = location_counts[location_counts >= 3].index.tolist()

# Calculate metrics by location
location_data = pd.DataFrame({'Location': locations_with_sufficient_data})
location_data['Raid_Count'] = location_data['Location'].map(df.groupby('Location').size())
location_data['Total_Tonnage'] = location_data['Location'].map(df.groupby('Location')['TOTAL_TONS'].sum())
location_data['Avg_Area_Bombing_Score'] = location_data['Location'].map(df.groupby('Location')['AREA_BOMBING_SCORE_NORMALIZED'].mean())
location_data = location_data.fillna(0)

# Create scatter plot with area bombing score as color metric
plt.figure(figsize=(16, 10))
scatter = plt.scatter(
    location_data['Raid_Count'],
    location_data['Total_Tonnage'],
    alpha=0.7,
    c=location_data['Avg_Area_Bombing_Score'],
    cmap='inferno',
    s=50,
    vmin=0,
    vmax=10  # Area bombing score is 0-10
)

plt.colorbar(scatter, label='Average Area Bombing Score')
plt.title('Raid Frequency vs Total Tonnage by Location (colored by Area Bombing Score)', fontsize=18)
plt.xlabel('Number of Raids', fontsize=14)
plt.ylabel('Total Tonnage', fontsize=14)
plt.grid(True, alpha=0.3)

# Label top points
top_points = location_data.nlargest(15, 'Total_Tonnage')
for i, row in top_points.iterrows():
    plt.annotate(
        f"{row['Location']} ({row['Avg_Area_Bombing_Score']:.1f})",
        (row['Raid_Count'], row['Total_Tonnage']),
        xytext=(5, 5),
        textcoords='offset points',
        fontsize=8,
        bbox=dict(boxstyle='round,pad=0.3', fc='white', alpha=0.7)
    )

plt.tight_layout()
plt.savefig('plots/raid_frequency/bombing_scores/raid_count_vs_tonnage_by_bombing_score.png', dpi=300)
plt.close()

# 2. Create a heatmap of average area bombing scores by location and year
# Get top locations by raid count
top_50_locations = location_counts.nlargest(50).index.tolist()

# Create pivot tables for area bombing scores
yearly_bombing_scores = df[df['Location'].isin(top_50_locations)].pivot_table(
    index='Year',
    columns='Location',
    values='AREA_BOMBING_SCORE_NORMALIZED',
    aggfunc='mean',
    fill_value=np.nan
)

# Filter to war years
yearly_bombing_scores = yearly_bombing_scores.loc[yearly_bombing_scores.index.isin(range(1942, 1946))]

# Sort locations by average bombing score
avg_bombing_scores = df[df['Location'].isin(top_50_locations)].groupby('Location')['AREA_BOMBING_SCORE_NORMALIZED'].mean()
top_locations_by_score = avg_bombing_scores.sort_values(ascending=False).index.tolist()

# Only keep locations with enough data
valid_columns = [col for col in yearly_bombing_scores.columns if yearly_bombing_scores[col].count() >= 2]
yearly_bombing_scores = yearly_bombing_scores[valid_columns]

# Sort columns by average bombing score
ordered_columns = [col for col in top_locations_by_score if col in valid_columns]
yearly_bombing_scores = yearly_bombing_scores[ordered_columns]

# Create heatmap
plt.figure(figsize=(16, 20))
sns.heatmap(
    yearly_bombing_scores.T,
    cmap='RdYlBu_r',  # Red for high area bombing, blue for precision bombing
    annot=True,
    fmt='.1f',
    linewidths=0.5,
    cbar_kws={'label': 'Area Bombing Score (0-10)'},
    vmin=0,
    vmax=10
)
plt.title('Yearly Area Bombing Scores by Location (USAAF)', fontsize=18)
plt.xlabel('Year', fontsize=14)
plt.ylabel('Location', fontsize=14)
plt.tight_layout()
plt.savefig('plots/raid_frequency/bombing_scores/yearly_bombing_scores_heatmap.png', dpi=300)
plt.close()

# 3. Create a combined metric of tonnage-weighted area bombing scores by location
# Calculate tonnage-weighted area bombing scores
location_data['Tonnage_Weighted_Score'] = location_data['Location'].map(
    df.groupby('Location').apply(
        lambda x: np.average(x['AREA_BOMBING_SCORE_NORMALIZED'], weights=x['TOTAL_TONS'], axis=0)
        if len(x) > 0 and x['TOTAL_TONS'].sum() > 0 else 0
    )
)
location_data = location_data.fillna(0)

# Create a bar chart of top locations by tonnage-weighted area bombing score
top_locations_by_weighted_score = location_data.nlargest(20, 'Tonnage_Weighted_Score')

fig, ax = plt.subplots(figsize=(16, 10))
bars = ax.bar(
    range(len(top_locations_by_weighted_score)),
    top_locations_by_weighted_score['Tonnage_Weighted_Score'],
    color=plt.cm.RdYlBu_r(top_locations_by_weighted_score['Tonnage_Weighted_Score'] / 10)
)

ax.set_title('Top 20 Locations by Tonnage-Weighted Area Bombing Score (USAAF)', fontsize=18)
ax.set_xlabel('Location', fontsize=14)
ax.set_ylabel('Tonnage-Weighted Area Bombing Score', fontsize=14)
ax.set_xticks(range(len(top_locations_by_weighted_score)))
ax.set_xticklabels(top_locations_by_weighted_score['Location'], rotation=45, ha='right')
ax.set_ylim(0, 10)

# Fix colorbar issue using explicit axes
sm = plt.cm.ScalarMappable(cmap='RdYlBu_r', norm=plt.Normalize(0, 10))
sm.set_array([])  # You need to provide an empty array 
fig.colorbar(sm, ax=ax, label='Area Bombing Score (0-10)')

ax.grid(True, alpha=0.3, axis='y')

# Add raid count and tonnage annotations
for i, row in enumerate(top_locations_by_weighted_score.iterrows()):
    row = row[1]  # Get the data from the tuple
    ax.annotate(
        f"{row['Raid_Count']} raids\n{row['Total_Tonnage']:.0f} tons",
        (i, row['Tonnage_Weighted_Score'] + 0.1),
        ha='center',
        va='bottom',
        fontsize=8
    )

plt.tight_layout()
plt.savefig('plots/raid_frequency/bombing_scores/top_locations_by_tonnage_weighted_score.png', dpi=300)
plt.close()

# 4. Create seasonal trend analysis of area bombing scores
# Group by month and calculate average area bombing score
monthly_bombing_scores = df.groupby('Month')['AREA_BOMBING_SCORE_NORMALIZED'].mean()
monthly_raid_counts = df.groupby('Month').size()

# Create dual axis plot
fig, ax1 = plt.subplots(figsize=(14, 8))

# Plot bombing scores
ax1.plot(monthly_bombing_scores.index, monthly_bombing_scores.values, 'ro-', linewidth=2, markersize=8)
ax1.set_xlabel('Month of Year', fontsize=14)
ax1.set_ylabel('Average Area Bombing Score', color='red', fontsize=14)
ax1.tick_params(axis='y', labelcolor='red')
ax1.set_ylim(0, 10)
ax1.set_xticks(range(1, 13))
ax1.set_xticklabels(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])

# Plot raid counts on secondary axis
ax2 = ax1.twinx()
ax2.plot(monthly_raid_counts.index, monthly_raid_counts.values, 'bo-', linewidth=2, markersize=8)
ax2.set_ylabel('Number of Raids', color='blue', fontsize=14)
ax2.tick_params(axis='y', labelcolor='blue')

plt.title('Seasonal Trends in Area Bombing Scores vs. Raid Frequency (USAAF)', fontsize=18)
plt.grid(True, alpha=0.3)

# Add legend
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(['Area Bombing Score', 'Number of Raids'], loc='upper right', fontsize=12)

plt.tight_layout()
plt.savefig('plots/raid_frequency/bombing_scores/seasonal_bombing_score_trends.png', dpi=300)
plt.close()

# 5. Create evolution of bombing approach over time (quarterly)
# Group by quarter and calculate metrics
quarterly_metrics = df.groupby('Quarter').agg({
    'AREA_BOMBING_SCORE_NORMALIZED': 'mean',
    'TOTAL_TONS': 'sum',
    'raid_id': 'count'
}).reset_index()

# Filter to war period
quarterly_metrics = quarterly_metrics[quarterly_metrics['Quarter'].str.startswith(('1942', '1943', '1944', '1945'))]
quarterly_metrics = quarterly_metrics.sort_values('Quarter')

# Add bombing intensity (tons per raid)
quarterly_metrics['Tons_Per_Raid'] = quarterly_metrics['TOTAL_TONS'] / quarterly_metrics['raid_id']

# Create bubble chart where:
# x-axis: time (quarters)
# y-axis: area bombing score
# bubble size: total tonnage
# color: raid count
plt.figure(figsize=(16, 10))
scatter = plt.scatter(
    range(len(quarterly_metrics)),
    quarterly_metrics['AREA_BOMBING_SCORE_NORMALIZED'],
    s=quarterly_metrics['Tons_Per_Raid'] * 10,  # Scale for visibility
    c=quarterly_metrics['raid_id'],
    cmap='viridis',
    alpha=0.7
)

plt.colorbar(scatter, label='Number of Raids')
plt.title('Evolution of Bombing Approach by Quarter (USAAF)', fontsize=18)
plt.xlabel('Quarter', fontsize=14)
plt.ylabel('Area Bombing Score', fontsize=14)
plt.xticks(range(len(quarterly_metrics)), quarterly_metrics['Quarter'], rotation=45, ha='right')
plt.ylim(0, 10)
plt.grid(True, alpha=0.3)

# Add annotations for significant points
for i, row in enumerate(quarterly_metrics.itertuples()):
    if row.raid_id > 100 or row.AREA_BOMBING_SCORE_NORMALIZED > 7 or row.AREA_BOMBING_SCORE_NORMALIZED < 3:
        plt.annotate(
            f"{row.Quarter}\n{row.raid_id} raids\n{row.Tons_Per_Raid:.1f} tons/raid",
            (i, row.AREA_BOMBING_SCORE_NORMALIZED),
            xytext=(0, 10),
            textcoords='offset points',
            ha='center',
            fontsize=8,
            bbox=dict(boxstyle='round,pad=0.3', fc='white', alpha=0.7)
        )

plt.tight_layout()
plt.savefig('plots/raid_frequency/bombing_scores/quarterly_bombing_approach_evolution.png', dpi=300)
plt.close()

# 6. Create a calendar heatmap of area bombing scores
# Calculate monthly averages
df['YearMonth'] = df['Year'].astype(str) + '-' + df['Month'].astype(str).str.zfill(2)
monthly_avg_scores = df.groupby('YearMonth')['AREA_BOMBING_SCORE_NORMALIZED'].mean()

# Filter to war period
monthly_avg_scores = monthly_avg_scores[monthly_avg_scores.index.str.startswith(('1942-', '1943-', '1944-', '1945-'))]

# Convert to a structured format for heatmap
months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']
years = ['1942', '1943', '1944', '1945']

# Create matrix for the heatmap
score_matrix = np.zeros((len(years), len(months)))

for i, year in enumerate(years):
    for j, month in enumerate(months):
        yearmonth = f"{year}-{month}"
        if yearmonth in monthly_avg_scores.index:
            score_matrix[i, j] = monthly_avg_scores[yearmonth]

# Create area bombing score calendar heatmap
plt.figure(figsize=(15, 8))
ax = sns.heatmap(
    score_matrix,
    annot=True,
    fmt='.1f',
    cmap='RdYlBu_r',  # Red for high area bombing, blue for precision
    linewidths=0.5,
    xticklabels=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
    yticklabels=years,
    cbar_kws={'label': 'Area Bombing Score (0-10)'},
    vmin=0,
    vmax=10
)
plt.title('Monthly Area Bombing Score Calendar (USAAF)', fontsize=18)
plt.tight_layout()
plt.savefig('plots/raid_frequency/bombing_scores/monthly_bombing_score_calendar.png', dpi=300)
plt.close()

# 7. Create a scatter plot of bombing intensity vs area bombing score by location
plt.figure(figsize=(14, 10))

# Plot scatter with size representing raid count
scatter = plt.scatter(
    location_data['Total_Tonnage'] / location_data['Raid_Count'],  # Bombing intensity (tons per raid)
    location_data['Avg_Area_Bombing_Score'],
    s=location_data['Raid_Count'] * 3,  # Scale size by raid count
    alpha=0.7,
    c=location_data['Total_Tonnage'],
    cmap='viridis'
)

plt.colorbar(scatter, label='Total Tonnage')
plt.title('Relationship Between Bombing Intensity and Area Bombing Score by Location', fontsize=18)
plt.xlabel('Average Tons per Raid', fontsize=14)
plt.ylabel('Area Bombing Score', fontsize=14)
plt.grid(True, alpha=0.3)
plt.ylim(0, 10)
plt.xlim(0, max(location_data['Total_Tonnage'] / location_data['Raid_Count']) * 1.1)

# Add trend line
x = location_data['Total_Tonnage'] / location_data['Raid_Count']
y = location_data['Avg_Area_Bombing_Score']
z = np.polyfit(x[~np.isnan(x) & ~np.isnan(y)], y[~np.isnan(x) & ~np.isnan(y)], 1)
p = np.poly1d(z)
plt.plot(
    np.linspace(0, plt.xlim()[1], 100),
    p(np.linspace(0, plt.xlim()[1], 100)),
    "r--",
    label=f"Trend: y={z[0]:.4f}x+{z[1]:.2f}"
)
plt.legend(fontsize=12)

# Label top points in various categories
# Top by bombing intensity
top_by_intensity = location_data.nlargest(5, 'Total_Tonnage')
for i, row in top_by_intensity.iterrows():
    plt.annotate(
        row['Location'],
        (row['Total_Tonnage'] / row['Raid_Count'], row['Avg_Area_Bombing_Score']),
        xytext=(5, 5),
        textcoords='offset points',
        fontsize=8,
        bbox=dict(boxstyle='round,pad=0.3', fc='white', alpha=0.7)
    )

# Top by area bombing score
top_by_score = location_data.nlargest(5, 'Avg_Area_Bombing_Score')
for i, row in top_by_score.iterrows():
    plt.annotate(
        row['Location'],
        (row['Total_Tonnage'] / row['Raid_Count'], row['Avg_Area_Bombing_Score']),
        xytext=(5, 5),
        textcoords='offset points',
        fontsize=8,
        bbox=dict(boxstyle='round,pad=0.3', fc='white', alpha=0.7)
    )

plt.tight_layout()
plt.savefig('plots/raid_frequency/bombing_scores/bombing_intensity_vs_area_score.png', dpi=300)
plt.close()

# 8. Create 3D scatter plot with Raid Count, Tonnage, and Area Bombing Score
try:
    from mpl_toolkits.mplot3d import Axes3D
    
    fig = plt.figure(figsize=(14, 12))
    ax = fig.add_subplot(111, projection='3d')
    
    scatter = ax.scatter(
        location_data['Raid_Count'], 
        location_data['Total_Tonnage'],
        location_data['Avg_Area_Bombing_Score'],
        s=50,
        c=location_data['Avg_Area_Bombing_Score'],
        cmap='inferno',
        alpha=0.7
    )
    
    ax.set_xlabel('Number of Raids', fontsize=14)
    ax.set_ylabel('Total Tonnage', fontsize=14)
    ax.set_zlabel('Area Bombing Score', fontsize=14)
    ax.set_zlim(0, 10)
    
    plt.colorbar(scatter, label='Area Bombing Score')
    plt.title('3D Relationship: Raids, Tonnage and Area Bombing Score by Location', fontsize=18)
    
    # Label select points
    for i, row in top_points.iloc[:7].iterrows():
        ax.text(
            row['Raid_Count'], 
            row['Total_Tonnage'],
            row['Avg_Area_Bombing_Score'],
            row['Location'],
            fontsize=8
        )
    
    plt.tight_layout()
    plt.savefig('plots/raid_frequency/bombing_scores/3d_raids_tonnage_area_score.png', dpi=300)
    plt.close()
except ImportError:
    print("3D plotting requires mpl_toolkits.mplot3d, skipping 3D visualization.")

# 9. Create heatmap of area bombing scores by target category
# Group by target category and calculate mean area bombing score
if 'CATEGORY' in df.columns:
    category_scores = df.groupby('CATEGORY').agg({
        'AREA_BOMBING_SCORE_NORMALIZED': 'mean',
        'raid_id': 'count',
        'TOTAL_TONS': 'sum'
    }).reset_index()
    
    # Filter to categories with sufficient data
    category_scores = category_scores[category_scores['raid_id'] >= 5]
    
    # Sort by area bombing score
    category_scores = category_scores.sort_values('AREA_BOMBING_SCORE_NORMALIZED', ascending=False)
    
    # Create category vs time heatmap
    # Pivot table for categories by year
    category_year_scores = df.pivot_table(
        index='CATEGORY',
        columns='Year',
        values='AREA_BOMBING_SCORE_NORMALIZED',
        aggfunc='mean'
    )
    
    # Filter to categories with sufficient data
    category_year_scores = category_year_scores.loc[category_scores['CATEGORY']]
    category_year_scores = category_year_scores[category_year_scores.columns.intersection([1942, 1943, 1944, 1945])]
    
    # Create heatmap
    plt.figure(figsize=(12, 14))
    sns.heatmap(
        category_year_scores,
        cmap='RdYlBu_r',
        annot=True,
        fmt='.1f',
        linewidths=0.5,
        cbar_kws={'label': 'Area Bombing Score (0-10)'},
        vmin=0,
        vmax=10
    )
    plt.title('Area Bombing Scores by Target Category and Year (USAAF)', fontsize=18)
    plt.xlabel('Year', fontsize=14)
    plt.ylabel('Target Category', fontsize=14)
    plt.tight_layout()
    plt.savefig('plots/raid_frequency/bombing_scores/category_year_bombing_scores.png', dpi=300)
    plt.close()
    
    # Create bar chart of category bombing scores
    fig, ax = plt.subplots(figsize=(16, 10))
    bars = ax.bar(
        range(len(category_scores)),
        category_scores['AREA_BOMBING_SCORE_NORMALIZED'],
        color=plt.cm.RdYlBu_r(category_scores['AREA_BOMBING_SCORE_NORMALIZED'] / 10)
    )
    
    ax.set_title('Average Area Bombing Score by Target Category (USAAF)', fontsize=18)
    ax.set_xlabel('Target Category', fontsize=14)
    ax.set_ylabel('Area Bombing Score', fontsize=14)
    ax.set_xticks(range(len(category_scores)))
    ax.set_xticklabels(category_scores['CATEGORY'], rotation=45, ha='right')
    ax.set_ylim(0, 10)

    # Fix colorbar issue using explicit axes
    sm = plt.cm.ScalarMappable(cmap='RdYlBu_r', norm=plt.Normalize(0, 10))
    sm.set_array([])  # You need to provide an empty array
    fig.colorbar(sm, ax=ax, label='Area Bombing Score (0-10)')

    ax.grid(True, alpha=0.3, axis='y')
    
    # Add raid count and tonnage annotations
    for i, row in enumerate(category_scores.iterrows()):
        row = row[1]  # Get the data from the tuple
        ax.annotate(
            f"{row['raid_id']} raids\n{row['TOTAL_TONS']:.0f} tons",
            (i, row['AREA_BOMBING_SCORE_NORMALIZED'] + 0.1),
            ha='center',
            va='bottom',
            fontsize=8
        )
    
    plt.tight_layout()
    plt.savefig('plots/raid_frequency/bombing_scores/category_bombing_scores.png', dpi=300)
    plt.close()

print("Area bombing score visualizations complete. Results saved to plots/raid_frequency/bombing_scores/ directory.") 