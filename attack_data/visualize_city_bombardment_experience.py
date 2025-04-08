import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.ticker import MaxNLocator
from matplotlib.gridspec import GridSpec
from matplotlib.patches import Patch

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("viridis")
plt.rcParams['figure.figsize'] = [12, 8]
plt.rcParams['figure.dpi'] = 300

# Create directory for plots
os.makedirs('plots/city_bombardment', exist_ok=True)

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

print("Analyzing city bombardment experience...")

# Filter to focus on significant locations (at least 5 raids total)
location_counts = df['Location'].value_counts()
significant_locations = location_counts[location_counts >= 5].index.tolist()
print(f"Found {len(significant_locations)} locations with at least 5 raids")

# Sort quarters chronologically
all_quarters = sorted([q for q in df['Quarter'].unique() if q.startswith(('1942', '1943', '1944', '1945'))])

# Create a DataFrame to store bombardment metrics for each location and quarter
bombardment_data = []

for location in significant_locations:
    location_df = df[df['Location'] == location]
    
    for quarter in all_quarters:
        quarter_df = location_df[location_df['Quarter'] == quarter]
        
        if len(quarter_df) > 0:
            # Calculate bombardment metrics
            raid_count = len(quarter_df)
            total_tonnage = quarter_df['TOTAL_TONS'].sum()
            avg_tonnage_per_raid = total_tonnage / raid_count if raid_count > 0 else 0
            avg_area_bombing_score = quarter_df['AREA_BOMBING_SCORE_NORMALIZED'].mean()
            
            bombardment_data.append({
                'Location': location,
                'Quarter': quarter,
                'Raid_Count': raid_count,
                'Total_Tonnage': total_tonnage,
                'Avg_Tonnage_Per_Raid': avg_tonnage_per_raid,
                'Avg_Area_Bombing_Score': avg_area_bombing_score
            })
        else:
            # Add zero entry for quarters with no raids
            bombardment_data.append({
                'Location': location,
                'Quarter': quarter,
                'Raid_Count': 0,
                'Total_Tonnage': 0,
                'Avg_Tonnage_Per_Raid': 0,
                'Avg_Area_Bombing_Score': np.nan
            })

# Convert to DataFrame
bombardment_df = pd.DataFrame(bombardment_data)

# Calculate additional metrics
# 1. Bombardment continuity - consecutive quarters with raids
def calculate_continuity(group):
    """Calculate the number of consecutive quarters with raids"""
    continuity = 0
    max_continuity = 0
    current_streak = 0
    
    for has_raid in (group['Raid_Count'] > 0).astype(int).values:
        if has_raid:
            current_streak += 1
            max_continuity = max(max_continuity, current_streak)
        else:
            current_streak = 0
    
    return max_continuity

location_continuity = {}
for location in significant_locations:
    location_data = bombardment_df[bombardment_df['Location'] == location].sort_values('Quarter')
    location_continuity[location] = calculate_continuity(location_data)

# 2. Bombardment intensity - max raids per quarter
location_max_raids = {}
for location in significant_locations:
    location_data = bombardment_df[bombardment_df['Location'] == location]
    location_max_raids[location] = location_data['Raid_Count'].max()

# 3. Total bombardment - total tonnage across all quarters
location_total_tonnage = {}
for location in significant_locations:
    location_data = bombardment_df[bombardment_df['Location'] == location]
    location_total_tonnage[location] = location_data['Total_Tonnage'].sum()

# 4. Persistence - total quarters with raids
location_active_quarters = {}
for location in significant_locations:
    location_data = bombardment_df[bombardment_df['Location'] == location]
    location_active_quarters[location] = (location_data['Raid_Count'] > 0).sum()

# Find top locations by total bombardment
top_by_tonnage = sorted(location_total_tonnage.items(), key=lambda x: x[1], reverse=True)
top_locations = [loc for loc, _ in top_by_tonnage[:15]]  # Top 15 most bombed cities
print(f"Top 15 most bombed cities: {', '.join(top_locations)}")

# 1. Create bombardment experience heatmap for top cities
# Pivot data for raids per quarter
raid_pivot = bombardment_df[bombardment_df['Location'].isin(top_locations)].pivot_table(
    index='Location',
    columns='Quarter',
    values='Raid_Count',
    fill_value=0
)

# Sort by total raids
raid_pivot['Total'] = raid_pivot.sum(axis=1)
raid_pivot = raid_pivot.sort_values('Total', ascending=False).drop('Total', axis=1)

# Create heatmap
plt.figure(figsize=(16, 10))
sns.heatmap(
    raid_pivot,
    cmap='YlOrRd',
    annot=True,
    fmt='g',
    linewidths=0.5,
    cbar_kws={'label': 'Number of Raids'}
)
plt.title('Quarterly Bombardment Experience by Location (Number of Raids)', fontsize=18)
plt.xlabel('Quarter', fontsize=14)
plt.ylabel('Location', fontsize=14)
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig('plots/city_bombardment/quarterly_raid_heatmap.png', dpi=300)
plt.close()

# 2. Create a combined "bombardment intensity" heatmap (raids × average tonnage)
# Pivot data for tonnage per quarter
tonnage_pivot = bombardment_df[bombardment_df['Location'].isin(top_locations)].pivot_table(
    index='Location',
    columns='Quarter',
    values='Total_Tonnage',
    fill_value=0
)

# Create normalized bombardment intensity metric
# For each quarter and location: (raids / max_raids) * (tonnage / max_tonnage) * 10
# This creates a 0-10 scale similar to the area bombing score
intensity_pivot = raid_pivot.copy()
for quarter in all_quarters:
    if quarter in raid_pivot.columns:
        max_raids = raid_pivot[quarter].max() if raid_pivot[quarter].max() > 0 else 1
        max_tonnage = tonnage_pivot[quarter].max() if quarter in tonnage_pivot.columns and tonnage_pivot[quarter].max() > 0 else 1
        
        for location in intensity_pivot.index:
            raids = raid_pivot.loc[location, quarter] if location in raid_pivot.index else 0
            tonnage = tonnage_pivot.loc[location, quarter] if quarter in tonnage_pivot.columns and location in tonnage_pivot.index else 0
            
            normalized_raids = raids / max_raids
            normalized_tonnage = tonnage / max_tonnage
            
            # Calculate bombardment intensity (scale 0-10)
            intensity = np.sqrt(normalized_raids * normalized_tonnage) * 10
            intensity_pivot.loc[location, quarter] = intensity

# Create intensity heatmap
plt.figure(figsize=(16, 10))
sns.heatmap(
    intensity_pivot,
    cmap='YlOrRd',
    annot=True,
    fmt='.1f',
    linewidths=0.5,
    vmin=0,
    vmax=10,
    cbar_kws={'label': 'Bombardment Intensity (0-10)'}
)
plt.title('Quarterly Bombardment Intensity by Location (Scale 0-10)', fontsize=18)
plt.xlabel('Quarter', fontsize=14)
plt.ylabel('Location', fontsize=14)
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig('plots/city_bombardment/quarterly_intensity_heatmap.png', dpi=300)
plt.close()

# 3. Create a multi-panel "bombardment calendar" for individual cities
def create_bombardment_calendar(location, bombardment_df, all_quarters):
    """Create a multi-panel bombardment calendar for a single location"""
    location_data = bombardment_df[bombardment_df['Location'] == location].set_index('Quarter')
    
    # Extract data for this location including incendiary percentage
    location_raw_data = df[df['Location'] == location]
    
    # Calculate incendiary percentage by quarter
    inc_by_quarter = {}
    for quarter in all_quarters:
        quarter_data = location_raw_data[location_raw_data['Quarter'] == quarter]
        if len(quarter_data) > 0 and quarter_data['TOTAL_TONS'].sum() > 0:
            # Check if INCENDIARY_TONS exists, if not calculate it from INCENDIARY_PERCENT
            if 'INCENDIARY_TONS' not in quarter_data.columns:
                if 'INCENDIARY_PERCENT' in quarter_data.columns:
                    inc_tons = (quarter_data['INCENDIARY_PERCENT'] * quarter_data['TOTAL_TONS'] / 100).sum()
                else:
                    inc_tons = 0
            else:
                inc_tons = quarter_data['INCENDIARY_TONS'].sum()
            
            total_tons = quarter_data['TOTAL_TONS'].sum()
            inc_by_quarter[quarter] = (inc_tons / total_tons) * 100 if total_tons > 0 else 0
        else:
            inc_by_quarter[quarter] = 0
    
    # Create figure with 4 panels
    fig = plt.figure(figsize=(16, 12))
    gs = GridSpec(4, 1, height_ratios=[2, 1, 1, 1], hspace=0.3)
    
    # Prepare data arrays
    quarters = []
    raids = []
    tonnage = []
    tons_per_raid = []
    area_scores = []
    inc_percentages = []
    
    for quarter in all_quarters:
        quarters.append(quarter)
        if quarter in location_data.index:
            raids.append(location_data.loc[quarter, 'Raid_Count'])
            tonnage.append(location_data.loc[quarter, 'Total_Tonnage'])
            
            # Calculate tons per raid
            if location_data.loc[quarter, 'Raid_Count'] > 0:
                tons_per_raid.append(location_data.loc[quarter, 'Total_Tonnage'] / location_data.loc[quarter, 'Raid_Count'])
            else:
                tons_per_raid.append(0)
            
            # Get area bombing score
            if not np.isnan(location_data.loc[quarter, 'Avg_Area_Bombing_Score']):
                area_scores.append(location_data.loc[quarter, 'Avg_Area_Bombing_Score'])
            else:
                area_scores.append(np.nan)
                
            # Get incendiary percentage
            inc_percentages.append(inc_by_quarter.get(quarter, 0))
        else:
            raids.append(0)
            tonnage.append(0)
            tons_per_raid.append(0)
            area_scores.append(np.nan)
            inc_percentages.append(0)
    
    # Define shared x positions and quarters
    x_positions = np.arange(len(quarters))
    
    # Get quarters to label (every 2 quarters to avoid crowding)
    quarters_to_label = [q if i % 2 == 0 else "" for i, q in enumerate(quarters)]
    
    # Simplified color schemes
    main_color = '#1f77b4'  # Blue
    secondary_color = '#d62728'  # Red
    bar_colors = [main_color if r > 0 else '#cccccc' for r in raids]
    
    # Panel 1: Raid count and tonnage
    ax1 = fig.add_subplot(gs[0])
    
    # Create bar chart for raids with simplified colors
    bars1 = ax1.bar(x_positions, raids, color=bar_colors, alpha=0.8, label='Raid Count')
    ax1.set_ylabel('Number of Raids', fontsize=12)
    
    # Create line chart for tonnage on secondary y-axis
    ax1_twin = ax1.twinx()
    ax1_twin.plot(x_positions, tonnage, color=secondary_color, linewidth=2, label='Total Tonnage')
    ax1_twin.set_ylabel('Total Tonnage', color=secondary_color, fontsize=12)
    ax1_twin.tick_params(axis='y', labelcolor=secondary_color)
    
    # Set x-axis labels
    ax1.set_xticks(x_positions)
    ax1.set_xticklabels([])  # Hide x labels for top panel
    ax1.set_title(f'Bombardment Experience for {location} (1942-1945)', fontsize=20)
    
    # Add vertical grid lines to help align panels
    ax1.grid(True, axis='x', alpha=0.3, linestyle='--')
    ax1.grid(True, axis='y', alpha=0.2)
    
    # Add legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax1_twin.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=12)
    
    # Panel 2: Bombing intensity (tons per raid)
    ax2 = fig.add_subplot(gs[1])
    
    # Simplified color scheme for tons per raid
    intensity_colors = []
    for tpr in tons_per_raid:
        if tpr <= 0:
            intensity_colors.append('#cccccc')  # Gray for zero values
        elif tpr < 25:
            intensity_colors.append('#9ecae1')  # Light blue for low intensity
        elif tpr < 50:
            intensity_colors.append('#4292c6')  # Medium blue for medium intensity
        else:
            intensity_colors.append('#084594')  # Dark blue for high intensity
    
    # Create bar chart for tons per raid with simplified colors
    bars2 = ax2.bar(x_positions, tons_per_raid, color=intensity_colors, alpha=0.8)
    
    # Create legend for tons per raid
    handles = [
        Patch(facecolor='#9ecae1', label='< 25 tons'),
        Patch(facecolor='#4292c6', label='25-50 tons'),
        Patch(facecolor='#084594', label='> 50 tons')
    ]
    ax2.legend(handles=handles, loc='upper right', fontsize=10)
    
    ax2.set_ylabel('Tons Per Raid', fontsize=12)
    ax2.set_xticks(x_positions)
    ax2.set_xticklabels([])  # Hide x labels for middle panel
    ax2.grid(True, axis='x', alpha=0.3, linestyle='--')
    ax2.grid(True, axis='y', alpha=0.2)
    
    # Panel 3: Bombing approach (area bombing score)
    ax3 = fig.add_subplot(gs[2])
    
    # Simplified colors for area bombing
    area_colors = []
    for score in area_scores:
        if np.isnan(score):
            area_colors.append('#cccccc')  # Gray for NaN values
        elif score <= 3:
            area_colors.append('#4292c6')  # Blue for precision bombing
        elif score < 7:
            area_colors.append('#f7a35c')  # Orange for mixed bombing
        else:
            area_colors.append('#d62728')  # Red for area bombing
    
    # Create bar chart for area bombing score with simplified colors
    bars3 = ax3.bar(x_positions, area_scores, color=area_colors, alpha=0.8)
    
    # Create legend for area bombing
    handles = [
        Patch(facecolor='#4292c6', label='Precision (0-3)'),
        Patch(facecolor='#f7a35c', label='Mixed (4-6)'),
        Patch(facecolor='#d62728', label='Area (7-10)')
    ]
    ax3.legend(handles=handles, loc='upper right', fontsize=10)
    
    ax3.set_ylabel('Area Bombing Score', fontsize=12)
    ax3.set_ylim(0, 10)
    ax3.set_xticks(x_positions)
    ax3.set_xticklabels([])  # Hide x labels
    ax3.grid(True, axis='x', alpha=0.3, linestyle='--')
    ax3.grid(True, axis='y', alpha=0.2)
    
    # Panel 4: Incendiary percentage
    ax4 = fig.add_subplot(gs[3])
    
    # Simplified colors for incendiary percentage
    inc_colors = []
    for pct in inc_percentages:
        if pct <= 0:
            inc_colors.append('#cccccc')  # Gray for zero values
        elif pct < 25:
            inc_colors.append('#9ecae1')  # Light blue for low percentage
        elif pct < 50:
            inc_colors.append('#f7a35c')  # Orange for medium percentage
        else:
            inc_colors.append('#d62728')  # Red for high percentage
    
    # Create bar chart for incendiary percentage with simplified colors
    bars4 = ax4.bar(x_positions, inc_percentages, color=inc_colors, alpha=0.8)
    
    # Create legend for incendiary percentage
    handles = [
        Patch(facecolor='#9ecae1', label='< 25%'),
        Patch(facecolor='#f7a35c', label='25-50%'),
        Patch(facecolor='#d62728', label='> 50%')
    ]
    ax4.legend(handles=handles, loc='upper right', fontsize=10)
    
    ax4.set_ylabel('Incendiary %', fontsize=12)
    ax4.set_ylim(0, 100)
    ax4.set_xticks(x_positions)
    ax4.set_xticklabels(quarters, rotation=45, ha='right')
    ax4.grid(True, axis='x', alpha=0.3, linestyle='--')
    ax4.grid(True, axis='y', alpha=0.2)
    
    # Add horizontal grid lines to align panels visually
    x_min, x_max = ax1.get_xlim()
    for i in range(len(quarters)):
        if i % 2 == 0:  # Add vertical line for every other quarter
            ax1.axvline(x=i, color='gray', alpha=0.2, linestyle='-', zorder=0)
            ax2.axvline(x=i, color='gray', alpha=0.2, linestyle='-', zorder=0)
            ax3.axvline(x=i, color='gray', alpha=0.2, linestyle='-', zorder=0)
            ax4.axvline(x=i, color='gray', alpha=0.2, linestyle='-', zorder=0)
    
    # Ensure consistent x-axis limits across all panels
    for ax in [ax1, ax2, ax3, ax4]:
        ax.set_xlim(-0.5, len(quarters)-0.5)
    
    plt.tight_layout()
    plt.savefig(f'plots/city_bombardment/calendar_{location.lower().replace(" ", "_")}.png', dpi=300)
    plt.close()

# Create bombardment calendars for top 10 cities
print("Creating bombardment calendars for top cities...")
for location in top_locations[:10]:
    create_bombardment_calendar(location, bombardment_df, all_quarters)

# 4. Create a comprehensive "bombardment experience index"
# Combine continuity, intensity, and persistence into a single index
print("Creating bombardment experience index...")

# Calculate the index components for all significant locations
location_index_data = []
for location in significant_locations:
    max_raids_per_quarter = bombardment_df[bombardment_df['Location'] == location]['Raid_Count'].max()
    total_raids = bombardment_df[bombardment_df['Location'] == location]['Raid_Count'].sum()
    max_tons_per_quarter = bombardment_df[bombardment_df['Location'] == location]['Total_Tonnage'].max()
    total_tons = bombardment_df[bombardment_df['Location'] == location]['Total_Tonnage'].sum()
    avg_tons_per_raid = total_tons / total_raids if total_raids > 0 else 0
    continuity = location_continuity[location]
    persistence = location_active_quarters[location]
    
    # Calculate normalized metrics (0-10 scale)
    norm_max_raids = min(max_raids_per_quarter / 20 * 10, 10)  # 20+ raids in a quarter is max
    norm_total_raids = min(total_raids / 100 * 10, 10)  # 100+ total raids is max
    norm_max_tons = min(max_tons_per_quarter / 1000 * 10, 10)  # 1000+ tons in a quarter is max
    norm_total_tons = min(total_tons / 5000 * 10, 10)  # 5000+ total tons is max
    norm_tons_per_raid = min(avg_tons_per_raid / 50 * 10, 10)  # 50+ tons per raid is max
    norm_continuity = min(continuity / 5 * 10, 10)  # 5+ consecutive quarters is max
    norm_persistence = min(persistence / (len(all_quarters)/2) * 10, 10)  # Half or more quarters active is max
    
    # Calculate overall bombardment experience index (weighted average)
    bombardment_index = (
        norm_max_raids * 0.15 +
        norm_total_raids * 0.15 +
        norm_max_tons * 0.15 +
        norm_total_tons * 0.15 +
        norm_tons_per_raid * 0.15 +
        norm_continuity * 0.10 +
        norm_persistence * 0.15
    )
    
    location_index_data.append({
        'Location': location,
        'Total_Raids': total_raids,
        'Total_Tonnage': total_tons,
        'Max_Raids_Per_Quarter': max_raids_per_quarter,
        'Max_Tonnage_Per_Quarter': max_tons_per_quarter,
        'Avg_Tons_Per_Raid': avg_tons_per_raid,
        'Continuity': continuity,
        'Persistence': persistence,
        'Norm_Max_Raids': norm_max_raids,
        'Norm_Total_Raids': norm_total_raids,
        'Norm_Max_Tons': norm_max_tons,
        'Norm_Total_Tons': norm_total_tons,
        'Norm_Tons_Per_Raid': norm_tons_per_raid,
        'Norm_Continuity': norm_continuity,
        'Norm_Persistence': norm_persistence,
        'Bombardment_Index': bombardment_index
    })

index_df = pd.DataFrame(location_index_data)
index_df = index_df.sort_values('Bombardment_Index', ascending=False)

# Create visualization of bombardment experience index
top_index_cities = index_df.head(20)

# Create horizontal bar chart of bombardment index
plt.figure(figsize=(14, 12))
bars = plt.barh(
    range(len(top_index_cities)),
    top_index_cities['Bombardment_Index'],
    color=plt.cm.YlOrRd(top_index_cities['Bombardment_Index'] / 10),
    alpha=0.8
)

plt.yticks(range(len(top_index_cities)), top_index_cities['Location'])
plt.xlabel('Bombardment Experience Index (0-10)', fontsize=14)
plt.title('Top 20 Locations by Bombardment Experience Index', fontsize=18)
plt.grid(True, alpha=0.3, axis='x')
plt.xlim(0, 10)

# Add annotations for key metrics
for i, row in enumerate(top_index_cities.iterrows()):
    row = row[1]
    plt.annotate(
        f"{row['Total_Raids']} raids, {row['Total_Tonnage']:.0f} tons, {row['Persistence']} quarters",
        (row['Bombardment_Index'] + 0.1, i),
        va='center',
        fontsize=9
    )

plt.tight_layout()
plt.savefig('plots/city_bombardment/bombardment_experience_index.png', dpi=300)
plt.close()

# 5. Create a stacked area chart of quarter-by-quarter bombardment experience
# Get top 5 locations by bombardment index
top5_locations = index_df.head(5)['Location'].tolist()

# Create quarter-by-quarter tonnage visualization
quarter_tonnage_pivot = bombardment_df[bombardment_df['Location'].isin(top5_locations)].pivot_table(
    index='Quarter',
    columns='Location',
    values='Total_Tonnage',
    fill_value=0
)

plt.figure(figsize=(14, 8))
quarter_tonnage_pivot.plot.area(alpha=0.7, figsize=(14, 8), colormap='viridis')
plt.title('Quarterly Bombing Tonnage for Top 5 Cities', fontsize=18)
plt.xlabel('Quarter', fontsize=14)
plt.ylabel('Total Tonnage', fontsize=14)
plt.xticks(rotation=45, ha='right')
plt.grid(True, alpha=0.3)
plt.legend(title='Location', fontsize=12, title_fontsize=14)
plt.tight_layout()
plt.savefig('plots/city_bombardment/top5_quarterly_tonnage.png', dpi=300)
plt.close()

# 6. Create radar charts for comparing bombardment components across top cities
def create_radar_chart(city_data, title, filename):
    """Create a radar chart comparing bombardment components for cities"""
    # Categories for radar chart
    categories = ['Max Raids', 'Total Raids', 'Max Tonnage',
                 'Total Tonnage', 'Tons/Raid', 'Continuity', 'Persistence']
    
    # Number of categories and cities
    N = len(categories)
    num_cities = len(city_data)
    
    # Create angles for radar chart
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]  # Close the loop
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))
    
    # Colors for each city
    colors = plt.cm.viridis(np.linspace(0, 1, num_cities))
    
    # Plot data for each city
    for i, (city, row) in enumerate(city_data.iterrows()):
        values = [row['Norm_Max_Raids'], row['Norm_Total_Raids'], row['Norm_Max_Tons'],
                 row['Norm_Total_Tons'], row['Norm_Tons_Per_Raid'], row['Norm_Continuity'],
                 row['Norm_Persistence']]
        values += values[:1]  # Close the loop
        
        ax.plot(angles, values, 'o-', linewidth=2, label=city, color=colors[i])
        ax.fill(angles, values, alpha=0.1, color=colors[i])
    
    # Set category labels
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)
    
    # Set y-axis limits
    ax.set_ylim(0, 10)
    
    # Add legend
    plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1), fontsize=10)
    
    plt.title(title, fontsize=18, y=1.1)
    plt.tight_layout()
    plt.savefig(filename, dpi=300)
    plt.close()

# Create radar chart for top 5 cities
create_radar_chart(
    index_df.head(5).set_index('Location'),
    'Bombardment Components Comparison - Top 5 Cities',
    'plots/city_bombardment/top5_radar_chart.png'
)

# 7. Create a combined "bombardment streak" visualization
# This shows how many consecutive quarters each city was bombed
streak_data = []

for location in significant_locations:
    location_data = bombardment_df[bombardment_df['Location'] == location].sort_values('Quarter')
    current_streak = 0
    max_streak = 0
    streak_start = None
    max_streak_start = None
    
    # Find the longest streak and its start quarter
    for i, (_, row) in enumerate(location_data.iterrows()):
        if row['Raid_Count'] > 0:
            if current_streak == 0:
                streak_start = row['Quarter']
            current_streak += 1
            
            if current_streak > max_streak:
                max_streak = current_streak
                max_streak_start = streak_start
        else:
            current_streak = 0
            streak_start = None
    
    if max_streak >= 3:  # Only include locations with streaks of 3+ quarters
        streak_data.append({
            'Location': location,
            'Max_Streak': max_streak,
            'Streak_Start': max_streak_start,
            'Total_Raids': bombardment_df[bombardment_df['Location'] == location]['Raid_Count'].sum(),
            'Total_Tonnage': bombardment_df[bombardment_df['Location'] == location]['Total_Tonnage'].sum()
        })

streak_df = pd.DataFrame(streak_data)
streak_df = streak_df.sort_values(['Max_Streak', 'Total_Tonnage'], ascending=[False, False])

# Create horizontal bar chart showing streak duration
top_streak_cities = streak_df.head(15)

plt.figure(figsize=(14, 10))
bars = plt.barh(
    range(len(top_streak_cities)),
    top_streak_cities['Max_Streak'],
    color=plt.cm.Reds(top_streak_cities['Max_Streak'] / top_streak_cities['Max_Streak'].max()),
    alpha=0.8
)

plt.yticks(range(len(top_streak_cities)), top_streak_cities['Location'])
plt.xlabel('Consecutive Quarters Under Bombardment', fontsize=14)
plt.title('Cities with Longest Continuous Bombardment Periods', fontsize=18)
plt.grid(True, alpha=0.3, axis='x')

# Add annotations
for i, row in enumerate(top_streak_cities.iterrows()):
    row = row[1]
    plt.annotate(
        f"Starting {row['Streak_Start']} | {row['Total_Raids']} raids, {row['Total_Tonnage']:.0f} tons",
        (row['Max_Streak'] + 0.1, i),
        va='center',
        fontsize=9
    )

plt.tight_layout()
plt.savefig('plots/city_bombardment/longest_bombardment_streaks.png', dpi=300)
plt.close()

print("City bombardment experience analysis complete. Results saved to plots/city_bombardment/ directory.") 