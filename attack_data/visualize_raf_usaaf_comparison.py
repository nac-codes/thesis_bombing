import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from matplotlib.colors import LinearSegmentedColormap

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("viridis")
plt.rcParams['figure.figsize'] = [12, 8]
plt.rcParams['figure.dpi'] = 300

# Create directories for plots
for dir_name in ['attack_data/plots/comparison/years', 'attack_data/plots/comparison/categories', 
                'attack_data/plots/comparison/cities', 'attack_data/plots/comparison/general']:
    os.makedirs(dir_name, exist_ok=True)

# Load bombing classification data
print("Loading bombing classification data...")
raids_classification = pd.read_csv('attack_data/processed_data/raids_area_bombing_classification_with_category.csv')

# Load raids summary data with air force information
print("Loading raids summary data...")
raids_summary = pd.read_csv('attack_data/processed_data/raids_summary.csv')

# Create raid_id in both datasets (will be the index)
raids_classification['raid_id'] = raids_classification.index
raids_summary['raid_id'] = raids_summary.index

# Merge datasets
print("Merging datasets...")
df = pd.merge(
    raids_classification,
    raids_summary[['raid_id', 'AIR FORCE', 'DAY', 'MONTH', 'YEAR']],
    on='raid_id',
    how='inner'
)

# Create Air Force type
df['Air Force'] = df['AIR FORCE'].apply(lambda x: 'RAF' if x == 'R' else 'USAAF')

# Clean up year data - it should be 1940s
print("Cleaning year data...")
df['YEAR'] = df['YEAR'].fillna(0).astype(float)  # Handle missing values
df['Year'] = (1940 + df['YEAR']).astype(int)
# Handle any outlier years
df.loc[df['Year'] < 1941, 'Year'] = 1941
df.loc[df['Year'] > 1946, 'Year'] = 1945

# Create a clean location field
df['Location'] = df['target_location'].str.strip().str.upper()

# Add score category to data
print("Creating score categories...")
df['Score Category'] = pd.cut(df['AREA_BOMBING_SCORE_NORMALIZED'], 
                             bins=[0, 2, 4, 6, 8, 10],
                             labels=['Very Precise (0-2)', 'Precise (2-4)', 
                                    'Mixed (4-6)', 'Area (6-8)', 'Heavy Area (8-10)'])

# Set up a common color map for consistency
cmap = plt.cm.viridis
norm = plt.Normalize(0, 10)

# Identify top 10 cities
top_cities = df['Location'].value_counts().head(10).index.tolist()
print(f"Top 10 most raided cities: {', '.join(top_cities)}")

# Add historically significant cities if not already in top cities
significant_cities = ['BERLIN', 'HAMBURG', 'COLOGNE', 'DRESDEN', 'SCHWEINFURT']
for city in significant_cities:
    if city not in top_cities and city in df['Location'].values:
        top_cities.append(city)
        print(f"Added {city} to city analysis list")

# Create general comparison plots
print("Creating RAF vs USAAF comparison plots...")

# 1. Score distribution comparison
plt.figure(figsize=(14, 8))
sns.histplot(data=df, x='AREA_BOMBING_SCORE_NORMALIZED', hue='Air Force', 
            element='step', stat='density', common_norm=False, bins=20, kde=True)
plt.title('Area Bombing Score Distribution: USAAF vs RAF', fontsize=18)
plt.xlabel('Area Bombing Score (10 = Clear Area Bombing, 0 = Precise Bombing)', fontsize=14)
plt.ylabel('Density', fontsize=14)
plt.xlim(0, 10)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('attack_data/plots/comparison/general/usaaf_vs_raf_score_distribution.png', dpi=300)
plt.close()

# 2. Mean and median scores comparison
plt.figure(figsize=(12, 8))
force_stats = df.groupby('Air Force')['AREA_BOMBING_SCORE_NORMALIZED'].agg(['mean', 'median', 'std']).reset_index()

x = np.arange(len(force_stats))
width = 0.35

fig, ax = plt.subplots(figsize=(12, 8))
ax.bar(x - width/2, force_stats['mean'], width, label='Mean Score', color='steelblue')
ax.bar(x + width/2, force_stats['median'], width, label='Median Score', color='darkgreen')

# Add error bars for standard deviation
ax.errorbar(x - width/2, force_stats['mean'], yerr=force_stats['std'], fmt='none', color='black', capsize=5)

ax.set_title('Area Bombing Score Comparison: USAAF vs RAF', fontsize=18)
ax.set_ylabel('Score', fontsize=14)
ax.set_xticks(x)
ax.set_xticklabels(force_stats['Air Force'], fontsize=14)
ax.set_ylim(0, 10)
ax.legend(fontsize=12)
ax.grid(True, alpha=0.3, axis='y')

# Add value labels on bars
for i, v in enumerate(force_stats['mean']):
    ax.text(i - width/2, v + 0.1, f"{v:.2f}", ha='center', fontsize=12)
for i, v in enumerate(force_stats['median']):
    ax.text(i + width/2, v + 0.1, f"{v:.2f}", ha='center', fontsize=12)

plt.tight_layout()
plt.savefig('attack_data/plots/comparison/general/usaaf_vs_raf_score_stats.png', dpi=300)
plt.close()

# 3. Bombing categories comparison
plt.figure(figsize=(14, 8))
category_by_af = pd.crosstab(df['Air Force'], df['Score Category'])
category_by_af_pct = category_by_af.div(category_by_af.sum(axis=1), axis=0) * 100

# Plot side by side
category_by_af_pct.plot(kind='bar', figsize=(14, 8))
plt.title('Bombing Categories: USAAF vs RAF', fontsize=18)
plt.xlabel('Air Force', fontsize=14)
plt.ylabel('Percentage of Raids', fontsize=14)
plt.ylim(0, 100)
plt.grid(True, alpha=0.3, axis='y')
plt.legend(title='Bombing Category', title_fontsize=12, fontsize=10, loc='upper left', bbox_to_anchor=(1, 1))

# Add percentage text on bars
for i, af in enumerate(category_by_af_pct.index):
    cumulative_sum = 0
    for j, col in enumerate(category_by_af_pct.columns):
        # Only add text for segments that are at least 3% of the total
        if category_by_af_pct.loc[af, col] >= 3:
            plt.text(i, cumulative_sum + category_by_af_pct.loc[af, col]/2,
                    f"{category_by_af_pct.loc[af, col]:.1f}%", ha='center', va='center',
                    fontsize=10, fontweight='bold', color='white')
        cumulative_sum += category_by_af_pct.loc[af, col]

plt.tight_layout()
plt.savefig('attack_data/plots/comparison/general/usaaf_vs_raf_categories.png', dpi=300)
plt.close()

# 4. Evolution over time
plt.figure(figsize=(14, 8))
yearly_scores = df.groupby(['Year', 'Air Force'])['AREA_BOMBING_SCORE_NORMALIZED'].agg(['mean', 'median']).reset_index()
yearly_scores = yearly_scores[(yearly_scores['Year'] >= 1941) & (yearly_scores['Year'] <= 1945)]

# Plot evolution of both air forces
for af in yearly_scores['Air Force'].unique():
    af_data = yearly_scores[yearly_scores['Air Force'] == af]
    plt.plot(af_data['Year'], af_data['mean'], 'o-', linewidth=2, markersize=8, label=f'{af} Mean Score')
    plt.plot(af_data['Year'], af_data['median'], 's--', linewidth=2, markersize=8, label=f'{af} Median Score')

plt.title('Evolution of Area Bombing Scores Throughout the War', fontsize=18)
plt.xlabel('Year', fontsize=14)
plt.ylabel('Area Bombing Score', fontsize=14)
plt.xticks(sorted(yearly_scores['Year'].unique()), fontsize=12)
plt.ylim(0, 10)  # Consistent y-axis limit
plt.grid(True, alpha=0.3)
plt.legend(fontsize=12)
plt.tight_layout()
plt.savefig('attack_data/plots/comparison/years/yearly_evolution.png', dpi=300)
plt.close()

# 5. Stacked bar chart of bombing categories by year and air force
plt.figure(figsize=(16, 10))
year_af_cat = pd.crosstab([df['Year'], df['Air Force']], df['Score Category'])
year_af_cat = year_af_cat.loc[year_af_cat.index.get_level_values(0).astype(int).isin(range(1941, 1946))]
year_af_cat_pct = year_af_cat.div(year_af_cat.sum(axis=1), axis=0) * 100

# Reshape the data for plotting
year_af_cat_pct_reset = year_af_cat_pct.reset_index()
plot_data = pd.melt(year_af_cat_pct_reset, 
                    id_vars=['Year', 'Air Force'], 
                    value_vars=year_af_cat_pct.columns, 
                    var_name='Category', 
                    value_name='Percentage')

# Create a grouped bar chart
plt.figure(figsize=(18, 10))
g = sns.catplot(
    data=plot_data,
    kind="bar",
    x="Year", y="Percentage", hue="Category", col="Air Force",
    palette="viridis", height=6, aspect=1.5, legend=False
)

g.set_axis_labels("Year", "Percentage")
g.set_titles("{col_name}")
g.tight_layout()
g.fig.suptitle('Distribution of Bombing Categories by Year and Air Force', fontsize=18, y=1.02)
plt.legend(title='Bombing Category', bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
plt.savefig('attack_data/plots/comparison/years/category_by_year_air_force.png', dpi=300, bbox_inches='tight')
plt.close()

# 6. Incendiary percentage comparison
plt.figure(figsize=(14, 8))
df['INCENDIARY_PERCENT'] = df['INCENDIARY_PERCENT'].fillna(0)
sns.boxplot(x='Air Force', y='INCENDIARY_PERCENT', data=df)
plt.title('Comparison of Incendiary Bomb Usage: USAAF vs RAF', fontsize=18)
plt.xlabel('Air Force', fontsize=14)
plt.ylabel('Incendiary Percentage', fontsize=14)
plt.ylim(0, 100)  # Consistent y-axis limit
plt.grid(True, alpha=0.3, axis='y')

# Add mean value text
for i, af in enumerate(df['Air Force'].unique()):
    mean_val = df[df['Air Force'] == af]['INCENDIARY_PERCENT'].mean()
    plt.text(i, df[df['Air Force'] == af]['INCENDIARY_PERCENT'].median() + 5, 
             f"Mean: {mean_val:.1f}%", ha='center', fontsize=12)

plt.tight_layout()
plt.savefig('attack_data/plots/comparison/general/incendiary_comparison.png', dpi=300)
plt.close()

# City-specific visualizations
print("Creating city comparison plots...")

# 1. Bar chart of average bombing scores for top cities by air force
plt.figure(figsize=(16, 10))
city_scores = df[df['Location'].isin(top_cities)].groupby(['Location', 'Air Force'])['AREA_BOMBING_SCORE_NORMALIZED'].mean().reset_index()

# Pivot the data
city_scores_pivot = city_scores.pivot(index='Location', columns='Air Force', values='AREA_BOMBING_SCORE_NORMALIZED')
city_scores_pivot = city_scores_pivot.fillna(0)  # Fill NaNs with 0 for cities only targeted by one air force

# Sort by the maximum of RAF or USAAF scores
city_scores_pivot = city_scores_pivot.reindex(city_scores_pivot.max(axis=1).sort_values(ascending=False).index)

# Plot
city_scores_pivot.plot(kind='bar', figsize=(16, 10))
plt.title('Average Area Bombing Score by City and Air Force', fontsize=18)
plt.xlabel('City', fontsize=14)
plt.ylabel('Average Area Bombing Score', fontsize=14)
plt.xticks(rotation=45, ha='right', fontsize=12)
plt.grid(True, alpha=0.3, axis='y')
plt.ylim(0, 10)  # Consistent y-axis limit
plt.legend(fontsize=12)

# Add values above bars
for i, city in enumerate(city_scores_pivot.index):
    for j, af in enumerate(city_scores_pivot.columns):
        if city_scores_pivot.loc[city, af] > 0:  # Only add text if there's a value
            plt.text(i + (j-0.5)*0.4, city_scores_pivot.loc[city, af] + 0.2, 
                     f"{city_scores_pivot.loc[city, af]:.1f}", ha='center', fontsize=10, fontweight='bold')

plt.tight_layout()
plt.savefig('attack_data/plots/comparison/cities/city_comparison_by_air_force.png', dpi=300)
plt.close()

# 2. Stacked bar chart showing proportion of raid categories for top cities by air force
for af in df['Air Force'].unique():
    plt.figure(figsize=(14, 8))
    af_data = df[(df['Location'].isin(top_cities)) & (df['Air Force'] == af)]
    
    if len(af_data) > 0:
        city_categories = pd.crosstab(af_data['Location'], af_data['Score Category'])
        city_categories_pct = city_categories.div(city_categories.sum(axis=1), axis=0) * 100

        # Sort by proportion of area bombing (highest to lowest)
        area_proportion = city_categories_pct['Area (6-8)'] + city_categories_pct.get('Heavy Area (8-10)', pd.Series(0, index=city_categories_pct.index))
        sorted_cities = area_proportion.sort_values(ascending=False).index

        city_categories_pct = city_categories_pct.loc[sorted_cities]

        city_categories_pct.plot(kind='bar', stacked=True, colormap='viridis', figsize=(14, 8))
        plt.title(f'Distribution of Bombing Categories by City ({af})', fontsize=18)
        plt.xlabel('City', fontsize=14)
        plt.ylabel('Percentage of Raids', fontsize=14)
        plt.ylim(0, 100)  # Consistent y-axis limit for percentage plots
        plt.xticks(rotation=45, ha='right', fontsize=12)
        plt.legend(title='Bombing Category', title_fontsize=12, fontsize=10, loc='upper left', bbox_to_anchor=(1, 1))
        plt.grid(True, alpha=0.3, axis='y')

        # Add percentage text on bars
        for i, city in enumerate(city_categories_pct.index):
            cumulative_sum = 0
            for j, col in enumerate(city_categories_pct.columns):
                # Only add text for segments that are at least 5% of the total
                if city_categories_pct.loc[city, col] >= 5:
                    plt.text(i, cumulative_sum + city_categories_pct.loc[city, col]/2,
                            f"{city_categories_pct.loc[city, col]:.1f}%", ha='center', va='center',
                            fontsize=10, fontweight='bold', color='white')
                cumulative_sum += city_categories_pct.loc[city, col]

        plt.tight_layout()
        plt.savefig(f'attack_data/plots/comparison/cities/category_by_city_{af.lower()}.png', dpi=300)
    plt.close()

# 3. Tonnage comparison
plt.figure(figsize=(14, 8))
df['TOTAL_TONS'] = df['TOTAL_TONS'].clip(0, 500)  # Clip extreme values
sns.boxplot(x='Air Force', y='TOTAL_TONS', data=df)
plt.title('Comparison of Bombing Tonnage: USAAF vs RAF (clipped at 500 tons)', fontsize=18)
plt.xlabel('Air Force', fontsize=14)
plt.ylabel('Total Tons', fontsize=14)
plt.grid(True, alpha=0.3, axis='y')

# Add mean value text
for i, af in enumerate(df['Air Force'].unique()):
    mean_val = df[df['Air Force'] == af]['TOTAL_TONS'].mean()
    plt.text(i, df[df['Air Force'] == af]['TOTAL_TONS'].median() + 20, 
             f"Mean: {mean_val:.1f} tons", ha='center', fontsize=12)

plt.tight_layout()
plt.savefig('attack_data/plots/comparison/general/tonnage_comparison.png', dpi=300)
plt.close()

# 4. Target category comparison
plt.figure(figsize=(16, 10))
target_type_af = pd.crosstab(df['CATEGORY'], df['Air Force'])
target_type_af_pct = target_type_af.div(target_type_af.sum(axis=0), axis=1) * 100

# Sort by difference between RAF and USAAF
if 'RAF' in target_type_af_pct.columns and 'USAAF' in target_type_af_pct.columns:
    target_type_af_pct['Difference'] = target_type_af_pct['RAF'] - target_type_af_pct['USAAF']
    target_type_af_pct = target_type_af_pct.sort_values('Difference', ascending=False)
    target_type_af_pct = target_type_af_pct.drop(columns=['Difference'])

# Filter to show only top categories (to keep the chart readable)
top_n = 15
if len(target_type_af_pct) > top_n:
    target_type_af_pct = target_type_af_pct.iloc[:top_n]

target_type_af_pct.plot(kind='barh', figsize=(16, 10))
plt.title('Target Category Distribution by Air Force', fontsize=18)
plt.xlabel('Percentage of Raids', fontsize=14)
plt.ylabel('Target Category', fontsize=14)
plt.xlim(0, 100)  # Consistent x-axis limit for percentage plots
plt.grid(True, alpha=0.3, axis='x')
plt.legend(fontsize=12)

# Add percentage text on bars
for i, cat in enumerate(target_type_af_pct.index):
    for j, af in enumerate(target_type_af_pct.columns):
        if target_type_af_pct.loc[cat, af] >= 3:  # Only add text for segments that are at least 3%
            plt.text(target_type_af_pct.loc[cat, af] / 2, i + (j-0.5)*0.4,
                    f"{target_type_af_pct.loc[cat, af]:.1f}%", va='center', ha='center',
                    fontsize=10, fontweight='bold', color='white')

plt.tight_layout()
plt.savefig('attack_data/plots/comparison/general/target_category_comparison.png', dpi=300)
plt.close()

# 5. Scatter plot of Tonnage vs Incendiary Score colored by Air Force
plt.figure(figsize=(14, 8))
scatter = sns.scatterplot(
    data=df, 
    x='TOTAL_TONS', 
    y='INCENDIARY_PERCENT',
    hue='Air Force',
    style='Air Force',
    alpha=0.7, 
    s=40
)
plt.title('Tonnage vs Incendiary Percentage by Air Force', fontsize=18)
plt.xlabel('Total Tons (clipped at 500)', fontsize=14)
plt.ylabel('Incendiary Percentage', fontsize=14)
plt.xlim(0, 500)  # Enforce consistent x-axis limits
plt.ylim(0, 100)  # Enforce consistent y-axis limits
plt.grid(True, alpha=0.3)
plt.legend(fontsize=12)
plt.tight_layout()
plt.savefig('attack_data/plots/comparison/general/tonnage_vs_incendiary_by_af.png', dpi=300)
plt.close()

# 6. Hexbin plot for better visualization of density
plt.figure(figsize=(16, 12))
g = sns.FacetGrid(df, col="Air Force", height=6, aspect=1.2)
g.map(plt.hexbin, "TOTAL_TONS", "INCENDIARY_PERCENT", gridsize=20, cmap="viridis", extent=[0, 500, 0, 100])
g.set_axis_labels("Total Tons (clipped at 500)", "Incendiary Percentage")
g.set_titles("{col_name}")
g.add_legend()
plt.tight_layout()
plt.savefig('attack_data/plots/comparison/general/tonnage_vs_incendiary_hexbin.png', dpi=300)
plt.close()

print("All visualizations completed!") 