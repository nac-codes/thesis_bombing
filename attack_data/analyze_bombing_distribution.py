import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from matplotlib.ticker import MaxNLocator
from matplotlib.gridspec import GridSpec

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("viridis")
plt.rcParams['figure.figsize'] = [12, 8]
plt.rcParams['figure.dpi'] = 300

# Create directory for plots
os.makedirs('plots/bombing_distribution', exist_ok=True)

# Load USAAF data
print("Loading USAAF data...")
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

# Create quarter-year field and quarter field
df['Year_Quarter'] = df['Year'].astype(str) + '-Q' + ((df['Month']-1)//3 + 1).astype(str)
df['Quarter'] = df['Year'].astype(str) + 'Q' + ((df['Month']-1)//3 + 1).astype(str)

print("Analyzing bombing distribution...")

# Sort quarters chronologically - MODIFIED: exclude Q3-Q4 1945
all_quarters = sorted([q for q in df['Quarter'].unique() 
                     if q.startswith(('1942', '1943', '1944')) 
                     or (q.startswith('1945') and not (q.endswith('Q3') or q.endswith('Q4')))])

#--------------------------------------------------------------
# 1. Number of Unique Locations Bombed Over Time (Cumulative)
#--------------------------------------------------------------
print("Analyzing unique locations bombed over time...")

# Create dataframe for tracking unique locations by quarter
locations_by_quarter = []

# Track all unique locations up to each quarter
all_locations_so_far = set()

for quarter in all_quarters:
    quarter_df = df[df['Quarter'] == quarter]
    quarter_locations = set(quarter_df['Location'].unique())
    
    # Add new locations to cumulative set
    all_locations_so_far.update(quarter_locations)
    
    locations_by_quarter.append({
        'Quarter': quarter,
        'New_Locations': len(quarter_locations - (all_locations_so_far - quarter_locations)),
        'Total_Locations': len(all_locations_so_far),
        'Active_Locations': len(quarter_locations)
    })

locations_trend = pd.DataFrame(locations_by_quarter)

# Create visualization for cumulative and new locations over time
plt.figure(figsize=(14, 8))
ax1 = plt.gca()

# Plot cumulative locations
ax1.plot(range(len(all_quarters)), locations_trend['Total_Locations'], 
         marker='o', markersize=8, linewidth=3, color='#1f77b4', 
         label='Cumulative Locations')

# Plot active locations per quarter
ax1.plot(range(len(all_quarters)), locations_trend['Active_Locations'], 
         marker='s', markersize=6, linewidth=2, color='#ff7f0e', 
         label='Active Locations')

# Create a twin y-axis for new locations
ax2 = ax1.twinx()
ax2.bar(range(len(all_quarters)), locations_trend['New_Locations'], 
        alpha=0.3, color='#2ca02c', label='New Locations')

# Set labels and legends
ax1.set_xlabel('Quarter', fontsize=14)
ax1.set_ylabel('Number of Locations', fontsize=14)
ax2.set_ylabel('New Locations', fontsize=14, color='#2ca02c')
ax2.tick_params(axis='y', labelcolor='#2ca02c')

# Set x-axis ticks and labels
ax1.set_xticks(range(len(all_quarters)))
ax1.set_xticklabels(all_quarters, rotation=45, ha='right')

# Add legends
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=12)

plt.title('Growth of Bombing Locations Over Time', fontsize=18)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('plots/bombing_distribution/locations_growth_over_time.png', dpi=300)
plt.close()

#--------------------------------------------------------------
# 2. Distribution Analysis - Concentration of Bombing
#--------------------------------------------------------------
print("Analyzing bombing concentration...")

# Calculate total tonnage by location
location_tonnage = df.groupby('Location')['TOTAL_TONS'].sum().reset_index()
location_tonnage = location_tonnage.sort_values('TOTAL_TONS', ascending=False)

# Calculate running percentage of total tonnage
total_tonnage = location_tonnage['TOTAL_TONS'].sum()
location_tonnage['Percentage'] = location_tonnage['TOTAL_TONS'] / total_tonnage * 100
location_tonnage['Cumulative_Percentage'] = location_tonnage['Percentage'].cumsum()

# Calculate metrics for concentration analysis
top10_percentage = location_tonnage.iloc[:10]['Percentage'].sum()
top25_percentage = location_tonnage.iloc[:25]['Percentage'].sum()
top50_percentage = location_tonnage.iloc[:50]['Percentage'].sum()

# Number of locations accounting for 50%, 75%, and 90% of bombing
locations_for_50percent = location_tonnage[location_tonnage['Cumulative_Percentage'] <= 50].shape[0]
locations_for_75percent = location_tonnage[location_tonnage['Cumulative_Percentage'] <= 75].shape[0]
locations_for_90percent = location_tonnage[location_tonnage['Cumulative_Percentage'] <= 90].shape[0]

# Create Lorenz curve visualization
plt.figure(figsize=(12, 8))

# Get percentiles of locations
x = np.array(range(len(location_tonnage))) / len(location_tonnage) * 100
y = location_tonnage['Cumulative_Percentage'].values

# Plot Lorenz curve
plt.plot(x, y, 'b-', linewidth=2, label='Actual Distribution')
plt.plot([0, 100], [0, 100], 'r--', linewidth=2, label='Perfect Equality')

# Fill area between curves
plt.fill_between(x, y, np.linspace(0, 100, len(y)), alpha=0.2, color='blue')



# Set labels and title
plt.xlabel('Percentage of Locations (Cumulative)', fontsize=14)
plt.ylabel('Percentage of Total Bombing Tonnage (Cumulative)', fontsize=14)
plt.title('Concentration of Bombing Campaign (Lorenz Curve)', fontsize=18)
plt.grid(True, alpha=0.3)
plt.legend(fontsize=12)
plt.tight_layout()
plt.savefig('plots/bombing_distribution/bombing_concentration_lorenz.png', dpi=300)
plt.close()

#--------------------------------------------------------------
# 3. Top Locations Bombing Share Over Time
#--------------------------------------------------------------
print("Analyzing top locations' share over time...")

# Get top 10 locations by total tonnage
top10_locations = location_tonnage.head(10)['Location'].tolist()

# Calculate tonnage by quarter for all locations
tonnage_by_quarter = df.groupby(['Quarter', 'Location'])['TOTAL_TONS'].sum().reset_index()

# Create a pivot table for analysis
tonnage_pivot = tonnage_by_quarter.pivot_table(
    index='Quarter', 
    columns='Location', 
    values='TOTAL_TONS',
    fill_value=0
)

# Calculate quarterly total tonnage
tonnage_pivot['Total'] = tonnage_pivot.sum(axis=1)

# Calculate quarterly percentage for top 10 locations
for location in top10_locations:
    if location in tonnage_pivot.columns:
        tonnage_pivot[f'{location}_pct'] = tonnage_pivot[location] / tonnage_pivot['Total'] * 100

# Calculate "Other Locations" percentage
top10_cols = [loc for loc in top10_locations if loc in tonnage_pivot.columns]
tonnage_pivot['Others'] = tonnage_pivot['Total'] - tonnage_pivot[top10_cols].sum(axis=1)
tonnage_pivot['Others_pct'] = tonnage_pivot['Others'] / tonnage_pivot['Total'] * 100

# Create a stacked area chart showing percentage share over time
plt.figure(figsize=(16, 10))

# Prepare data for stacked area chart
data_cols = [loc for loc in top10_locations if loc in tonnage_pivot.columns] + ['Others']
data = np.zeros((len(all_quarters), len(data_cols)))

for i, loc in enumerate(data_cols):
    for j, quarter in enumerate(all_quarters):
        if quarter in tonnage_pivot.index:
            if loc == 'Others':
                data[j, i] = tonnage_pivot.loc[quarter, 'Others_pct']
            else:
                data[j, i] = tonnage_pivot.loc[quarter, f'{loc}_pct'] if f'{loc}_pct' in tonnage_pivot.columns else 0

# Create colormap for visualization
colors = plt.cm.viridis(np.linspace(0, 1, len(data_cols)))

# Plot stacked area chart
plt.stackplot(range(len(all_quarters)), data.T, labels=data_cols, colors=colors, alpha=0.8)

# Set labels and title
plt.xlabel('Quarter', fontsize=14)
plt.ylabel('Percentage of Total Tonnage', fontsize=14)
plt.title('Share of Bombing Tonnage by Location Over Time', fontsize=18)

# Set x-axis ticks and labels
plt.xticks(range(len(all_quarters)), all_quarters, rotation=45, ha='right')
plt.yticks(range(0, 101, 10))

# Add grid
plt.grid(True, alpha=0.3)

# Add legend
plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=5, fontsize=10)

plt.tight_layout()
plt.savefig('plots/bombing_distribution/top_locations_share_over_time.png', dpi=300)
plt.close()
#--------------------------------------------------------------
# 4. Concentration Metrics Over Time
#--------------------------------------------------------------
print("Analyzing changes in bombing concentration over time...")

# Calculate share metrics for each quarter
concentration_by_quarter = []

for quarter in all_quarters:
    quarter_tonnage = tonnage_by_quarter[tonnage_by_quarter['Quarter'] == quarter]
    
    # Calculate concentration metrics
    quarter_locations = len(quarter_tonnage)
    quarter_total = quarter_tonnage['TOTAL_TONS'].sum()
    
    # Sort locations by tonnage
    quarter_tonnage = quarter_tonnage.sort_values('TOTAL_TONS', ascending=False)
    
    # Calculate top 1% and top 10% shares
    top_1pct_count = max(1, int(quarter_locations * 0.01))
    top_10pct_count = max(1, int(quarter_locations * 0.1))
    
    top_1pct_share = 0
    if quarter_locations > 0 and quarter_total > 0:
        top_1pct_share = quarter_tonnage.iloc[:top_1pct_count]['TOTAL_TONS'].sum() / quarter_total
    
    top_10pct_share = 0
    if quarter_locations > 0 and quarter_total > 0:
        top_10pct_share = quarter_tonnage.iloc[:top_10pct_count]['TOTAL_TONS'].sum() / quarter_total
    
    concentration_by_quarter.append({
        'Quarter': quarter,
        'Top1Pct_Share': top_1pct_share,
        'Top10Pct_Share': top_10pct_share,
        'Locations': quarter_locations
    })

concentration_df = pd.DataFrame(concentration_by_quarter)

# Create visualization of concentration metrics over time
plt.figure(figsize=(16, 10))
gs = GridSpec(3, 1, height_ratios=[2, 1, 1], hspace=0.3)

# Panel 1: Concentration metrics
ax1 = plt.subplot(gs[0])
ax1.plot(range(len(all_quarters)), concentration_df['Top1Pct_Share'], marker='o', linewidth=2, 
         label='Top 1% Locations Share', color='#1f77b4')
ax1.plot(range(len(all_quarters)), concentration_df['Top10Pct_Share'], marker='s', linewidth=2, 
         label='Top 10% Locations Share', color='#ff7f0e')

ax1.set_title('Bombing Concentration Metrics Over Time', fontsize=18)
ax1.set_ylabel('Share of Total Tonnage', fontsize=14)
ax1.set_ylim(0, 1)
ax1.grid(True, alpha=0.3)
ax1.legend(fontsize=12)
ax1.set_xticks(range(len(all_quarters)))
ax1.set_xticklabels([])  # Hide x labels for top panel

# Panel 2: Number of bombed locations per quarter
ax2 = plt.subplot(gs[1])
ax2.bar(range(len(all_quarters)), concentration_df['Locations'], color='#9467bd', alpha=0.7)
ax2.set_ylabel('Locations Bombed', fontsize=14)
ax2.grid(True, axis='y', alpha=0.3)
ax2.set_xticks(range(len(all_quarters)))
ax2.set_xticklabels([])  # Hide x labels for middle panel

# Panel 3: Total tonnage per quarter
ax3 = plt.subplot(gs[2])

# Fix for the length mismatch issue
quarterly_tonnage = []
for quarter in all_quarters:
    if quarter in tonnage_pivot.index:
        quarterly_tonnage.append(tonnage_pivot.loc[quarter, 'Total'])
    else:
        quarterly_tonnage.append(0)

ax3.bar(range(len(all_quarters)), quarterly_tonnage, color='#8c564b', alpha=0.7)
ax3.set_xlabel('Quarter', fontsize=14)
ax3.set_ylabel('Total Tonnage', fontsize=14)
ax3.grid(True, axis='y', alpha=0.3)
ax3.set_xticks(range(len(all_quarters)))
ax3.set_xticklabels(all_quarters, rotation=45, ha='right')

# Ensure consistent x-axis limits
for ax in [ax1, ax2, ax3]:
    ax.set_xlim(-0.5, len(all_quarters)-0.5)

plt.tight_layout()
plt.savefig('plots/bombing_distribution/concentration_metrics_over_time.png', dpi=300)
plt.close()

#--------------------------------------------------------------
# 5. Geographic Distribution - Top 20 Most Bombed Locations
#--------------------------------------------------------------
print("Creating visualization of top bombed locations...")

# Get top 20 most bombed locations
top20_locations = location_tonnage.head(20)

plt.figure(figsize=(14, 10))

# Create horizontal bar chart
bars = plt.barh(
    range(len(top20_locations)),
    top20_locations['TOTAL_TONS'],
    color=plt.cm.viridis(np.linspace(0, 0.8, len(top20_locations))),
    alpha=0.8
)

# Add percentage labels
for i, (_, row) in enumerate(top20_locations.iterrows()):
    plt.annotate(
        f"{row['Percentage']:.1f}%",
        (row['TOTAL_TONS'] + 100, i),
        va='center',
        fontsize=10
    )

# Set labels and title
plt.yticks(range(len(top20_locations)), top20_locations['Location'])
plt.xlabel('Total Bombing Tonnage', fontsize=14)
plt.title('Top 20 Most Bombed Locations', fontsize=18)
plt.grid(True, alpha=0.3, axis='x')
plt.tight_layout()
plt.savefig('plots/bombing_distribution/top20_bombed_locations.png', dpi=300)
plt.close()

print("Bombing distribution analysis complete. Results saved to plots/bombing_distribution/ directory.") 

#--------------------------------------------------------------
# 6. Generate Report with Bombing Concentration Tables
#--------------------------------------------------------------
print("\nGenerating bombing concentration report...")

# Ensure directory exists for reports
os.makedirs('reports', exist_ok=True)

# Create a report file
with open('reports/bombing_concentration_report.txt', 'w') as f:
    f.write("=================================================================\n")
    f.write("                 USAAF BOMBING CONCENTRATION REPORT               \n")
    f.write("=================================================================\n\n")
    
    # Overall concentration stats
    f.write("OVERALL BOMBING CONCENTRATION\n")
    f.write("-----------------------------------------------------------------\n")
    f.write(f"Total number of bombed locations: {len(location_tonnage)}\n")
    f.write(f"Total bombing tonnage: {total_tonnage:.1f} tons\n\n")
    
    f.write(f"Top 10 locations received {top10_percentage:.1f}% of all bombing\n")
    f.write(f"Top 25 locations received {top25_percentage:.1f}% of all bombing\n")
    f.write(f"Top 50 locations received {top50_percentage:.1f}% of all bombing\n\n")
    
    f.write(f"Number of locations accounting for 50% of bombing: {locations_for_50percent}\n")
    f.write(f"Number of locations accounting for 75% of bombing: {locations_for_75percent}\n")
    f.write(f"Number of locations accounting for 90% of bombing: {locations_for_90percent}\n\n")
    
    # Top 20 bombed locations table
    f.write("TOP 20 MOST BOMBED LOCATIONS\n")
    f.write("-----------------------------------------------------------------\n")
    f.write(f"{'Rank':<5}{'Location':<20}{'Tonnage':<12}{'% of Total':<12}\n")
    f.write("-----------------------------------------------------------------\n")
    
    for i, (_, row) in enumerate(top20_locations.iterrows()):
        f.write(f"{i+1:<5}{row['Location']:<20}{row['TOTAL_TONS']:<12.1f}{row['Percentage']:<12.1f}\n")
    
    f.write("\n\n")
    
    # Concentration over time table
    f.write("BOMBING CONCENTRATION OVER TIME\n")
    f.write("-----------------------------------------------------------------\n")
    f.write(f"{'Quarter':<10}{'Locations':<10}{'Top 1% Share':<15}{'Top 10% Share':<15}{'Total Tons':<12}\n")
    f.write("-----------------------------------------------------------------\n")
    
    for i, quarter in enumerate(all_quarters):
        locs = concentration_df.iloc[i]['Locations']
        top1 = concentration_df.iloc[i]['Top1Pct_Share'] * 100
        top10 = concentration_df.iloc[i]['Top10Pct_Share'] * 100
        tons = quarterly_tonnage[i]
        
        f.write(f"{quarter:<10}{locs:<10}{top1:<15.1f}{top10:<15.1f}{tons:<12.1f}\n")
    
    f.write("\n\n")
    
    # Summary analysis
    f.write("CONCENTRATION ANALYSIS SUMMARY\n")
    f.write("-----------------------------------------------------------------\n")
    
    # Calculate average and trend for concentration metrics
    avg_top1 = concentration_df['Top1Pct_Share'].mean() * 100
    avg_top10 = concentration_df['Top10Pct_Share'].mean() * 100
    
    # Simple trend analysis - compare first half to second half
    mid_point = len(concentration_df) // 2
    early_top1 = concentration_df.iloc[:mid_point]['Top1Pct_Share'].mean() * 100
    late_top1 = concentration_df.iloc[mid_point:]['Top1Pct_Share'].mean() * 100
    early_top10 = concentration_df.iloc[:mid_point]['Top10Pct_Share'].mean() * 100
    late_top10 = concentration_df.iloc[mid_point:]['Top10Pct_Share'].mean() * 100
    
    top1_trend = "increasing" if late_top1 > early_top1 else "decreasing"
    top10_trend = "increasing" if late_top10 > early_top10 else "decreasing"
    
    f.write(f"Average share of bombing for top 1% of locations: {avg_top1:.1f}%\n")
    f.write(f"Average share of bombing for top 10% of locations: {avg_top10:.1f}%\n\n")
    
    f.write(f"Concentration trend (top 1% share): {top1_trend}\n")
    f.write(f"  Early war average (top 1%): {early_top1:.1f}%\n")
    f.write(f"  Late war average (top 1%): {late_top1:.1f}%\n\n")
    
    f.write(f"Concentration trend (top 10% share): {top10_trend}\n")
    f.write(f"  Early war average (top 10%): {early_top10:.1f}%\n")
    f.write(f"  Late war average (top 10%): {late_top10:.1f}%\n")

print("Report generated: reports/bombing_concentration_report.txt")