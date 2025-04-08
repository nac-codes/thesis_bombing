import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.ticker import MaxNLocator
from scipy.cluster.hierarchy import linkage, dendrogram, fcluster

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("viridis")
plt.rcParams['figure.figsize'] = [12, 8]
plt.rcParams['figure.dpi'] = 300

# Create directory for plots
os.makedirs('plots/raid_frequency', exist_ok=True)
os.makedirs('plots/raid_frequency/comprehensive', exist_ok=True)

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

print("Analyzing raid frequency by location and quarter...")

# Identify top locations by raid count
top_locations = df['Location'].value_counts().head(10).index.tolist()
print(f"Top 10 most raided locations: {', '.join(top_locations)}")

# Create pivot table of raid counts by location and quarter
raid_counts = df[df['Location'].isin(top_locations)].pivot_table(
    index='Quarter',
    columns='Location',
    values='raid_id',
    aggfunc='count',
    fill_value=0
)

# Sort by quarter
raid_counts = raid_counts.sort_index()

# Filter to war period (1942-1945)
raid_counts = raid_counts[raid_counts.index.astype(str).str.startswith(('1942', '1943', '1944', '1945'))]

# Plot raid frequency over time for top locations
plt.figure(figsize=(16, 10))
for location in top_locations:
    if location in raid_counts.columns:
        plt.plot(
            range(len(raid_counts)), 
            raid_counts[location], 
            'o-', 
            linewidth=2, 
            label=location
        )

plt.title('Number of USAAF Raids by Location Per Quarter', fontsize=18)
plt.xlabel('Quarter', fontsize=14)
plt.ylabel('Number of Raids', fontsize=14)
plt.xticks(range(len(raid_counts)), raid_counts.index.astype(str), rotation=45, ha='right')
plt.grid(True, alpha=0.3)
plt.legend(title='Location', fontsize=12, title_fontsize=14)
plt.tight_layout()
plt.savefig('plots/raid_frequency/raids_by_location_per_quarter.png', dpi=300)
plt.close()

# Create a stacked area chart of raid frequency
plt.figure(figsize=(16, 10))
raid_counts_cumsum = raid_counts.cumsum(axis=1)

# Plot stacked area chart
colors = plt.cm.viridis(np.linspace(0, 1, len(top_locations)))
for i, location in enumerate(reversed(raid_counts.columns)):
    if i == 0:
        plt.fill_between(
            range(len(raid_counts)), 
            0, 
            raid_counts_cumsum[location], 
            label=location, 
            color=colors[len(top_locations)-i-1]
        )
    else:
        prev_location = raid_counts.columns[len(raid_counts.columns)-i]
        plt.fill_between(
            range(len(raid_counts)), 
            raid_counts_cumsum[prev_location], 
            raid_counts_cumsum[location], 
            label=location, 
            color=colors[len(top_locations)-i-1]
        )

plt.title('Stacked Area Chart of USAAF Raids by Location Per Quarter', fontsize=18)
plt.xlabel('Quarter', fontsize=14)
plt.ylabel('Number of Raids', fontsize=14)
plt.xticks(range(len(raid_counts)), raid_counts.index.astype(str), rotation=45, ha='right')
plt.grid(True, alpha=0.3)
plt.legend(title='Location', fontsize=12, title_fontsize=14, loc='upper left')
plt.tight_layout()
plt.savefig('plots/raid_frequency/stacked_area_raids_by_location.png', dpi=300)
plt.close()

# Create a heatmap of raid frequency
plt.figure(figsize=(16, 10))
sns.heatmap(
    raid_counts.T, 
    cmap='viridis', 
    annot=True, 
    fmt='g', 
    linewidths=0.5,
    cbar_kws={'label': 'Number of Raids'}
)
plt.title('Heatmap of USAAF Raids by Location and Quarter', fontsize=18)
plt.xlabel('Quarter', fontsize=14)
plt.ylabel('Location', fontsize=14)
plt.tight_layout()
plt.savefig('plots/raid_frequency/heatmap_raids_by_location_quarter.png', dpi=300)
plt.close()

# Create a grouped bar chart for quarterly comparison
# For each year, create a chart comparing quarters
for year in range(1942, 1946):
    year_data = df[df['Year'] == year]
    
    # Skip if no data for this year
    if len(year_data) == 0:
        continue
        
    quarter_location_counts = year_data.pivot_table(
        index='Location',
        columns='Year_Quarter',
        values='raid_id',
        aggfunc='count',
        fill_value=0
    )
    
    # Filter to relevant quarters for this year
    year_quarters = [f"{year}-Q{q}" for q in range(1, 5)]
    relevant_quarters = [q for q in year_quarters if q in quarter_location_counts.columns]
    
    if len(relevant_quarters) == 0:
        continue
        
    quarter_location_counts = quarter_location_counts[relevant_quarters]
    
    # Sort by total raids in year
    quarter_location_counts['Total'] = quarter_location_counts.sum(axis=1)
    quarter_location_counts = quarter_location_counts.sort_values('Total', ascending=False).drop('Total', axis=1)
    
    # Take top 10 locations
    quarter_location_counts = quarter_location_counts.head(10)
    
    # Plot
    plt.figure(figsize=(16, 10))
    quarter_location_counts.plot(kind='bar', figsize=(16, 10))
    plt.title(f'USAAF Raids by Location per Quarter in {year}', fontsize=18)
    plt.xlabel('Location', fontsize=14)
    plt.ylabel('Number of Raids', fontsize=14)
    plt.xticks(rotation=45, ha='right')
    plt.grid(True, alpha=0.3, axis='y')
    plt.legend(title='Quarter', fontsize=12, title_fontsize=14)
    plt.tight_layout()
    plt.savefig(f'plots/raid_frequency/raids_by_location_quarters_{year}.png', dpi=300)
    plt.close()

# Create a line chart showing the total raid count per quarter
quarterly_totals = df.groupby('Quarter').size()
quarterly_totals = quarterly_totals[quarterly_totals.index.astype(str).str.startswith(('1942', '1943', '1944', '1945'))]
quarterly_totals = quarterly_totals.sort_index()

plt.figure(figsize=(16, 8))
quarterly_totals.plot(kind='line', marker='o', linewidth=2, markersize=8)
plt.title('Total USAAF Raids Per Quarter', fontsize=18)
plt.xlabel('Quarter', fontsize=14)
plt.ylabel('Number of Raids', fontsize=14)
plt.grid(True, alpha=0.3)
plt.xticks(rotation=45, ha='right')
plt.gca().yaxis.set_major_locator(MaxNLocator(integer=True))  # Ensure integer y-axis labels
plt.tight_layout()
plt.savefig('plots/raid_frequency/total_raids_per_quarter.png', dpi=300)
plt.close()

# Create bubble chart showing raid frequency, tonnage, and area bombing score
# For each quarter and top location
quarterly_location_data = df[df['Location'].isin(top_locations)].groupby(['Quarter', 'Location']).agg({
    'raid_id': 'count',
    'TOTAL_TONS': 'sum',
    'AREA_BOMBING_SCORE_NORMALIZED': 'mean'
}).reset_index()

# Rename columns for clarity
quarterly_location_data.columns = ['Quarter', 'Location', 'Raid_Count', 'Total_Tonnage', 'Area_Bombing_Score']

# Plot bubble chart for each location
for location in top_locations:
    location_data = quarterly_location_data[quarterly_location_data['Location'] == location]
    
    # Skip if not enough data points
    if len(location_data) < 3:
        continue
    
    location_data = location_data.sort_values('Quarter')
    
    plt.figure(figsize=(14, 8))
    scatter = plt.scatter(
        range(len(location_data)),
        location_data['Raid_Count'],
        s=location_data['Total_Tonnage']/10,  # Adjust size for visibility
        c=location_data['Area_Bombing_Score'],
        cmap='viridis',
        alpha=0.7
    )
    
    plt.colorbar(scatter, label='Area Bombing Score')
    
    plt.title(f'Raid Frequency, Tonnage, and Bombing Score for {location}', fontsize=16)
    plt.xlabel('Quarter', fontsize=14)
    plt.ylabel('Number of Raids', fontsize=14)
    plt.xticks(range(len(location_data)), location_data['Quarter'].astype(str), rotation=45, ha='right')
    plt.grid(True, alpha=0.3)
    
    # Add annotations for significant points
    for i, row in enumerate(location_data.itertuples()):
        if row.Raid_Count >= 5 or row.Total_Tonnage >= 500:
            plt.annotate(
                f"{row.Raid_Count} raids\n{row.Total_Tonnage:.0f} tons",
                (i, row.Raid_Count),
                xytext=(10, 10),
                textcoords='offset points',
                fontsize=9,
                bbox=dict(boxstyle='round,pad=0.3', fc='white', alpha=0.7)
            )
    
    plt.tight_layout()
    plt.savefig(f'plots/raid_frequency/bubble_chart_{location.lower().replace(" ", "_")}.png', dpi=300)
    plt.close()

# ------- NEW COMPREHENSIVE ANALYSIS FOR ALL LOCATIONS -------
print("\nGenerating comprehensive visualizations for ALL locations...")

# 1. Get all locations with sufficient data (at least 3 raids)
location_counts = df['Location'].value_counts()
locations_with_sufficient_data = location_counts[location_counts >= 3].index.tolist()
print(f"Analyzing {len(locations_with_sufficient_data)} locations with at least 3 raids")

# 2. Create pivot tables for all these locations
# For raid frequency
all_locations_raid_counts = df[df['Location'].isin(locations_with_sufficient_data)].pivot_table(
    index='Quarter',
    columns='Location',
    values='raid_id',
    aggfunc='count',
    fill_value=0
)

# For tonnage
all_locations_tonnage = df[df['Location'].isin(locations_with_sufficient_data)].pivot_table(
    index='Quarter',
    columns='Location',
    values='TOTAL_TONS',
    aggfunc='sum',
    fill_value=0
)

# Filter to war period (1942-1945)
all_locations_raid_counts = all_locations_raid_counts[all_locations_raid_counts.index.astype(str).str.startswith(('1942', '1943', '1944', '1945'))]
all_locations_tonnage = all_locations_tonnage[all_locations_tonnage.index.astype(str).str.startswith(('1942', '1943', '1944', '1945'))]

# 3. Create clusters of locations based on raid patterns
print("Clustering locations based on raid patterns...")

# Prepare data for clustering - transpose to get locations as rows
raid_pattern_data = all_locations_raid_counts.T
# Fill NAs (if any)
raid_pattern_data = raid_pattern_data.fillna(0)

# Only include locations that have raids in at least 3 quarters
min_quarters_with_raids = 3
locations_to_cluster = raid_pattern_data[raid_pattern_data.sum(axis=1) >= 3].index.tolist()
raid_pattern_data_filtered = raid_pattern_data.loc[locations_to_cluster]

# Perform hierarchical clustering
if len(raid_pattern_data_filtered) > 1:  # Only cluster if we have enough data
    Z = linkage(raid_pattern_data_filtered, method='ward')
    
    # Cut the dendrogram to get clusters (adjust max_d for appropriate number of clusters)
    max_d = 5  # You can adjust this threshold
    clusters = fcluster(Z, max_d, criterion='distance')
    
    # Add cluster information to the data
    raid_pattern_data_filtered['cluster'] = clusters
    
    # Plot dendrogram to visualize the clusters
    plt.figure(figsize=(16, 10))
    plt.title('Hierarchical Clustering of Locations by Raid Patterns', fontsize=18)
    dendrogram(
        Z,
        labels=raid_pattern_data_filtered.index,
        orientation='right',
        leaf_font_size=8,
    )
    plt.tight_layout()
    plt.savefig('plots/raid_frequency/comprehensive/location_clustering_dendrogram.png', dpi=300)
    plt.close()
    
    # Get number of clusters
    num_clusters = len(set(clusters))
    print(f"Identified {num_clusters} clusters of locations with similar raid patterns")
else:
    print("Not enough data for clustering")
    num_clusters = 1
    raid_pattern_data_filtered['cluster'] = 1

# 4. Create a comprehensive heatmap showing raid frequency for all locations
# First aggregate by year to make it more manageable
print("Creating comprehensive heatmaps...")

# Aggregate raid counts by year instead of quarter to make the heatmap more readable
yearly_raid_counts = df.pivot_table(
    index='Year',
    columns='Location',
    values='raid_id',
    aggfunc='count',
    fill_value=0
)

# Filter to war years
yearly_raid_counts = yearly_raid_counts.loc[yearly_raid_counts.index.isin(range(1942, 1946))]

# Get top 50 locations by total raids
top_50_by_raids = yearly_raid_counts.sum().sort_values(ascending=False).head(50).index.tolist()

# Create the heatmap for top 50
plt.figure(figsize=(16, 20))
sns.heatmap(
    yearly_raid_counts[top_50_by_raids].T,
    cmap='viridis',
    annot=True,
    fmt='g',
    linewidths=0.5,
    cbar_kws={'label': 'Number of Raids'}
)
plt.title('Yearly Raid Frequency - Top 50 Locations (USAAF)', fontsize=18)
plt.xlabel('Year', fontsize=14)
plt.ylabel('Location', fontsize=14)
plt.tight_layout()
plt.savefig('plots/raid_frequency/comprehensive/top50_locations_yearly_heatmap.png', dpi=300)
plt.close()

# 5. Create a heatmap with tonnage information
# Aggregate tonnage by year
yearly_tonnage = df.pivot_table(
    index='Year',
    columns='Location',
    values='TOTAL_TONS',
    aggfunc='sum',
    fill_value=0
)

# Filter to war years
yearly_tonnage = yearly_tonnage.loc[yearly_tonnage.index.isin(range(1942, 1946))]

# Get top 50 locations by total tonnage
top_50_by_tonnage = yearly_tonnage.sum().sort_values(ascending=False).head(50).index.tolist()

# Create the heatmap for top 50 by tonnage
plt.figure(figsize=(16, 20))
sns.heatmap(
    yearly_tonnage[top_50_by_tonnage].T,
    cmap='magma',
    annot=True,
    fmt='.0f',
    linewidths=0.5,
    cbar_kws={'label': 'Total Tons'}
)
plt.title('Yearly Bombing Tonnage - Top 50 Locations (USAAF)', fontsize=18)
plt.xlabel('Year', fontsize=14)
plt.ylabel('Location', fontsize=14)
plt.tight_layout()
plt.savefig('plots/raid_frequency/comprehensive/top50_tonnage_yearly_heatmap.png', dpi=300)
plt.close()

# 6. Combined metric: Create a metric that combines raid frequency and tonnage
# Calculate average tons per raid for each location and year
print("Creating combined metrics...")

# Calculate tons per raid
yearly_tons_per_raid = yearly_tonnage / yearly_raid_counts
yearly_tons_per_raid = yearly_tons_per_raid.fillna(0)

# Get top 50 locations by average tons per raid
top_50_by_intensity = yearly_tons_per_raid.mean().sort_values(ascending=False).head(50).index.tolist()

# Create the heatmap for top 50 by bombing intensity
plt.figure(figsize=(16, 20))
sns.heatmap(
    yearly_tons_per_raid[top_50_by_intensity].T,
    cmap='inferno',
    annot=True,
    fmt='.1f',
    linewidths=0.5,
    cbar_kws={'label': 'Average Tons per Raid'}
)
plt.title('Yearly Bombing Intensity (Tons per Raid) - Top 50 Locations (USAAF)', fontsize=18)
plt.xlabel('Year', fontsize=14)
plt.ylabel('Location', fontsize=14)
plt.tight_layout()
plt.savefig('plots/raid_frequency/comprehensive/top50_intensity_yearly_heatmap.png', dpi=300)
plt.close()

# 7. Create quarterly aggregate visualizations
print("Creating quarterly visualizations of all locations...")

# Define quarters in order
all_quarters = sorted([q for q in all_locations_raid_counts.index if q.startswith(('1942', '1943', '1944', '1945'))])

# Sum across all locations by quarter for raid frequency and tonnage
quarterly_all_locations_raids = all_locations_raid_counts.sum(axis=1)
quarterly_all_locations_tonnage = all_locations_tonnage.sum(axis=1)

# Create a dual-axis chart showing both metrics
fig, ax1 = plt.subplots(figsize=(16, 8))

ax1.plot(range(len(all_quarters)), quarterly_all_locations_raids, 'bo-', linewidth=2, markersize=8, label='Number of Raids')
ax1.set_xlabel('Quarter', fontsize=14)
ax1.set_ylabel('Number of Raids', color='blue', fontsize=14)
ax1.tick_params(axis='y', labelcolor='blue')
ax1.set_xticks(range(len(all_quarters)))
ax1.set_xticklabels(all_quarters, rotation=45, ha='right')

ax2 = ax1.twinx()
ax2.plot(range(len(all_quarters)), quarterly_all_locations_tonnage, 'ro-', linewidth=2, markersize=8, label='Total Tonnage')
ax2.set_ylabel('Total Tonnage', color='red', fontsize=14)
ax2.tick_params(axis='y', labelcolor='red')

plt.title('Quarterly USAAF Raid Frequency and Tonnage (All Locations)', fontsize=18)
plt.grid(True, alpha=0.3)

# Add two legends
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=12)

plt.tight_layout()
plt.savefig('plots/raid_frequency/comprehensive/quarterly_all_locations_raids_and_tonnage.png', dpi=300)
plt.close()

# 8. Create a visualization showing raid frequency distribution by location
print("Creating raid distribution visualizations...")

# Get all locations with at least 1 raid
all_raided_locations = df['Location'].value_counts()

# Create a histogram of raid counts
plt.figure(figsize=(14, 8))
plt.hist(all_raided_locations.values, bins=50, alpha=0.7, color='darkblue')
plt.title('Distribution of Raid Counts by Location (USAAF)', fontsize=18)
plt.xlabel('Number of Raids', fontsize=14)
plt.ylabel('Number of Locations', fontsize=14)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('plots/raid_frequency/comprehensive/raid_count_distribution.png', dpi=300)
plt.close()

# Create a log-scale version for better visualization
plt.figure(figsize=(14, 8))
plt.hist(all_raided_locations.values, bins=50, alpha=0.7, color='darkblue', log=True)
plt.title('Distribution of Raid Counts by Location (Log Scale, USAAF)', fontsize=18)
plt.xlabel('Number of Raids', fontsize=14)
plt.ylabel('Number of Locations (Log Scale)', fontsize=14)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('plots/raid_frequency/comprehensive/raid_count_distribution_log.png', dpi=300)
plt.close()

# 9. Tonnage distribution by location
# Get total tonnage by location
location_tonnage = df.groupby('Location')['TOTAL_TONS'].sum().sort_values(ascending=False)

# Create a histogram of tonnage distribution
plt.figure(figsize=(14, 8))
plt.hist(location_tonnage.values, bins=50, alpha=0.7, color='darkred')
plt.title('Distribution of Total Bombing Tonnage by Location (USAAF)', fontsize=18)
plt.xlabel('Total Tons', fontsize=14)
plt.ylabel('Number of Locations', fontsize=14)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('plots/raid_frequency/comprehensive/tonnage_distribution.png', dpi=300)
plt.close()

# Log-scale version
plt.figure(figsize=(14, 8))
plt.hist(location_tonnage.values, bins=50, alpha=0.7, color='darkred', log=True)
plt.title('Distribution of Total Bombing Tonnage by Location (Log Scale, USAAF)', fontsize=18)
plt.xlabel('Total Tons', fontsize=14)
plt.ylabel('Number of Locations (Log Scale)', fontsize=14)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('plots/raid_frequency/comprehensive/tonnage_distribution_log.png', dpi=300)
plt.close()

# 10. Create a scatterplot of raid count vs. tonnage for all locations
plt.figure(figsize=(14, 10))

# Prepare data
location_data = pd.DataFrame({
    'Location': df['Location'].unique()
})

location_data['Raid_Count'] = location_data['Location'].map(df.groupby('Location').size())
location_data['Total_Tonnage'] = location_data['Location'].map(df.groupby('Location')['TOTAL_TONS'].sum())
location_data['Avg_Tonnage_Per_Raid'] = location_data['Total_Tonnage'] / location_data['Raid_Count']
location_data = location_data.fillna(0)

# Create scatter plot
plt.scatter(
    location_data['Raid_Count'],
    location_data['Total_Tonnage'],
    alpha=0.7,
    c=location_data['Avg_Tonnage_Per_Raid'],
    cmap='viridis',
    s=50
)

plt.colorbar(label='Average Tons per Raid')
plt.title('Relationship Between Raid Frequency and Total Tonnage by Location', fontsize=18)
plt.xlabel('Number of Raids', fontsize=14)
plt.ylabel('Total Tonnage', fontsize=14)
plt.grid(True, alpha=0.3)

# Label top points
top_points = location_data.nlargest(15, 'Total_Tonnage')
for i, row in top_points.iterrows():
    plt.annotate(
        row['Location'],
        (row['Raid_Count'], row['Total_Tonnage']),
        xytext=(5, 5),
        textcoords='offset points',
        fontsize=8,
        bbox=dict(boxstyle='round,pad=0.3', fc='white', alpha=0.7)
    )

plt.tight_layout()
plt.savefig('plots/raid_frequency/comprehensive/raid_count_vs_tonnage_scatter.png', dpi=300)
plt.close()

# 11. Create a treemap visualization of top 100 locations by total tonnage
try:
    import squarify
    
    # Get top 100 locations by tonnage
    top100_tonnage = location_tonnage.head(100)
    
    # Create treemap
    plt.figure(figsize=(20, 15))
    squarify.plot(
        sizes=top100_tonnage.values,
        label=[f"{loc} ({int(tons)} tons)" for loc, tons in zip(top100_tonnage.index, top100_tonnage.values)],
        alpha=0.8,
        color=plt.cm.viridis(np.linspace(0, 1, len(top100_tonnage))),
        pad=0.01,
        text_kwargs={'fontsize': 9}
    )
    
    plt.axis('off')
    plt.title('Treemap of Top 100 Locations by Total Bombing Tonnage (USAAF)', fontsize=20)
    plt.tight_layout()
    plt.savefig('plots/raid_frequency/comprehensive/top100_tonnage_treemap.png', dpi=300)
    plt.close()
except ImportError:
    print("Squarify package not found, skipping treemap visualization")

# 12. Create a heat calendar showing raids over time
print("Creating calendar heatmap of raids...")

# Create monthly aggregates
df['YearMonth'] = df['Year'].astype(str) + '-' + df['Month'].astype(str).str.zfill(2)
monthly_raids = df.groupby('YearMonth').size()
monthly_tonnage = df.groupby('YearMonth')['TOTAL_TONS'].sum()

# Filter to war period
monthly_raids = monthly_raids[monthly_raids.index.str.startswith(('1942-', '1943-', '1944-', '1945-'))]
monthly_tonnage = monthly_tonnage[monthly_tonnage.index.str.startswith(('1942-', '1943-', '1944-', '1945-'))]

# Convert to a structured format for heatmap
months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']
years = ['1942', '1943', '1944', '1945']

# Create matrices for the heatmap
raid_matrix = np.zeros((len(years), len(months)))
tonnage_matrix = np.zeros((len(years), len(months)))

for i, year in enumerate(years):
    for j, month in enumerate(months):
        yearmonth = f"{year}-{month}"
        if yearmonth in monthly_raids.index:
            raid_matrix[i, j] = monthly_raids[yearmonth]
        if yearmonth in monthly_tonnage.index:
            tonnage_matrix[i, j] = monthly_tonnage[yearmonth]

# Create raid frequency calendar heatmap
plt.figure(figsize=(15, 8))
ax = sns.heatmap(
    raid_matrix,
    annot=True,
    fmt='g',
    cmap='Blues',
    linewidths=0.5,
    xticklabels=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
    yticklabels=years,
    cbar_kws={'label': 'Number of Raids'}
)
plt.title('Monthly Raid Frequency Calendar (USAAF)', fontsize=18)
plt.tight_layout()
plt.savefig('plots/raid_frequency/comprehensive/monthly_raid_calendar.png', dpi=300)
plt.close()

# Create tonnage calendar heatmap
plt.figure(figsize=(15, 8))
ax = sns.heatmap(
    tonnage_matrix,
    annot=True,
    fmt='.0f',
    cmap='Reds',
    linewidths=0.5,
    xticklabels=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
    yticklabels=years,
    cbar_kws={'label': 'Total Tons'}
)
plt.title('Monthly Bombing Tonnage Calendar (USAAF)', fontsize=18)
plt.tight_layout()
plt.savefig('plots/raid_frequency/comprehensive/monthly_tonnage_calendar.png', dpi=300)
plt.close()

# Create average tonnage per raid calendar
avg_tonnage_matrix = np.divide(tonnage_matrix, raid_matrix, out=np.zeros_like(tonnage_matrix), where=raid_matrix!=0)

plt.figure(figsize=(15, 8))
ax = sns.heatmap(
    avg_tonnage_matrix,
    annot=True,
    fmt='.1f',
    cmap='YlOrBr',
    linewidths=0.5,
    xticklabels=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
    yticklabels=years,
    cbar_kws={'label': 'Average Tons per Raid'}
)
plt.title('Monthly Average Bombing Intensity Calendar (USAAF)', fontsize=18)
plt.tight_layout()
plt.savefig('plots/raid_frequency/comprehensive/monthly_avg_tonnage_calendar.png', dpi=300)
plt.close()

print("Comprehensive raid frequency and tonnage analysis complete. Results saved to plots/raid_frequency/comprehensive/ directory.") 