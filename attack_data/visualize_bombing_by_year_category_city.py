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
for dir_name in ['plots/years', 'plots/categories', 'plots/cities']:
    os.makedirs(dir_name, exist_ok=True)

# Load and merge data
print("Loading data...")
raids_classification = pd.read_csv('processed_data/raids_area_bombing_classification_with_category.csv')
raids_summary = pd.read_csv('processed_data/raids_summary.csv')

# Create a unique identifier to merge datasets
raids_classification['raid_id'] = raids_classification.index
raids_summary['raid_id'] = raids_summary.index

# Merge datasets
print("Merging datasets...")
df = pd.merge(
    raids_classification, 
    raids_summary[['raid_id', 'DAY', 'MONTH', 'YEAR', 'AIR FORCE', 'TOTAL_AIRCRAFT']], 
    on='raid_id', 
    how='left'
)

# Clean up year data - it should be 1940s
print("Cleaning year data...")
df['YEAR'] = df['YEAR'].fillna(0).astype(float)  # Handle missing values
df['Year'] = (1940 + df['YEAR']).astype(int)
# Handle any outlier years
df.loc[df['Year'] < 1939, 'Year'] = 1940
df.loc[df['Year'] > 1946, 'Year'] = 1945

# Create a clean location field
df['Location'] = df['target_location'].str.strip().str.upper()

# Identify top 10 cities
top_cities = df['Location'].value_counts().head(10).index.tolist()
print(f"Top 10 most raided cities: {', '.join(top_cities)}")

# Set up a common color map for consistency
cmap = plt.cm.viridis
norm = plt.Normalize(0, 10)

# Create a custom function to generate standard set of plots
def generate_plots(data, group_name, save_dir):
    """Generate standard set of plots for a given dataset subset"""
    
    # 1. Distribution of Area Bombing Scores
    plt.figure(figsize=(12, 6))
    sns.histplot(data['AREA_BOMBING_SCORE_NORMALIZED'], bins=20, kde=True)
    plt.title(f'Distribution of Area Bombing Scores - {group_name}', fontsize=16)
    plt.xlabel('Area Bombing Score (10 = Clear Area Bombing, 0 = Precise Bombing)', fontsize=12)
    plt.ylabel('Count', fontsize=12)
    plt.axvline(data['AREA_BOMBING_SCORE_NORMALIZED'].median(), color='red', linestyle='--', 
               label=f'Median: {data["AREA_BOMBING_SCORE_NORMALIZED"].median():.1f}')
    plt.xlim(0, 10)  # Enforce consistent x-axis limits
    plt.legend()
    plt.tight_layout()
    plt.savefig(f'{save_dir}/score_distribution_{group_name.replace(" ", "_").lower()}.png', dpi=300)
    plt.close()
    
    # 2. Scatter plot of Tonnage vs Incendiary Score
    plt.figure(figsize=(12, 8))
    scatter = plt.scatter(
        data['TOTAL_TONS'].clip(0, 500), 
        data['INCENDIARY_PERCENT'].clip(0, 100), 
        c=data['AREA_BOMBING_SCORE_NORMALIZED'], 
        alpha=0.7, 
        cmap='viridis', 
        s=40,
        norm=norm
    )
    plt.colorbar(scatter, label='Area Bombing Score')
    plt.title(f'Tonnage vs Incendiary Percentage - {group_name}', fontsize=16)
    plt.xlabel('Total Tons (clipped at 500)', fontsize=12)
    plt.ylabel('Incendiary Percentage', fontsize=12)
    plt.xlim(0, 500)  # Enforce consistent x-axis limits
    plt.ylim(0, 100)  # Enforce consistent y-axis limits
    plt.tight_layout()
    plt.savefig(f'{save_dir}/tonnage_vs_incendiary_{group_name.replace(" ", "_").lower()}.png', dpi=300)
    plt.close()
    
    # 3. Box plot of scores by target type
    plt.figure(figsize=(10, 6))
    data.loc[:, 'Target Type'] = data['TARGET_SCORE'].map({1: 'Industrial/Area', 0: 'Non-Industrial/Precision'})
    sns.boxplot(x='Target Type', y='AREA_BOMBING_SCORE_NORMALIZED', data=data)
    plt.title(f'Area Bombing Scores by Target Type - {group_name}', fontsize=16)
    plt.xlabel('Target Type', fontsize=12)
    plt.ylabel('Area Bombing Score', fontsize=12)
    plt.ylim(0, 10)  # Enforce consistent y-axis limits
    plt.tight_layout()
    plt.savefig(f'{save_dir}/scores_by_target_type_{group_name.replace(" ", "_").lower()}.png', dpi=300)
    plt.close()
    
    # 4. Category distribution (pie chart)
    if len(data) > 20:  # Only create if enough data points
        plt.figure(figsize=(12, 10))
        cat_counts = data['Score Category'].value_counts().sort_index()
        colors = plt.cm.viridis(np.linspace(0, 1, len(cat_counts)))
        cat_counts.plot.pie(autopct='%1.1f%%', colors=colors, explode=[0.05]*len(cat_counts),
                           textprops={'fontsize': 12})
        plt.title(f'Distribution of Bombing Categories - {group_name}', fontsize=16)
        plt.ylabel('')  # Hide the ylabel
        plt.tight_layout()
        plt.savefig(f'{save_dir}/category_pie_{group_name.replace(" ", "_").lower()}.png', dpi=300)
        plt.close()
    
    # 5. Component scores (radar chart for groups with sufficient data)
    if len(data) >= 5:
        # Calculate average component scores
        avg_target = data['TARGET_SCORE'].mean() * 10
        avg_tonnage = data['TONNAGE_SCORE'].mean()
        avg_incendiary = data['INCENDIARY_SCORE'].mean()
        
        # Create radar chart
        categories = ['Target Type', 'Tonnage', 'Incendiary']
        values = [avg_target, avg_tonnage, avg_incendiary]
        
        # Create the radar chart
        angles = np.linspace(0, 2*np.pi, len(categories), endpoint=False).tolist()
        values += values[:1]  # Close the loop
        angles += angles[:1]  # Close the loop
        
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))
        ax.plot(angles, values, 'o-', linewidth=2, color='darkblue')
        ax.fill(angles, values, alpha=0.25, color='darkblue')
        ax.set_thetagrids(np.degrees(angles[:-1]), categories)
        ax.set_ylim(0, 10)  # Consistent range for component scores
        ax.set_title(f'Average Component Scores - {group_name}', fontsize=16, pad=20)
        ax.grid(True)
        
        # Add values at points
        for angle, value, category in zip(angles[:-1], values[:-1], categories):
            ax.text(angle, value + 0.5, f'{value:.1f}', 
                   horizontalalignment='center', verticalalignment='center')
        
        plt.tight_layout()
        plt.savefig(f'{save_dir}/component_radar_{group_name.replace(" ", "_").lower()}.png', dpi=300)
        plt.close()

# Add score category to data
print("Creating score categories...")
df['Score Category'] = pd.cut(df['AREA_BOMBING_SCORE_NORMALIZED'], 
                             bins=[0, 2, 4, 6, 8, 10],
                             labels=['Very Precise (0-2)', 'Precise (2-4)', 
                                    'Mixed (4-6)', 'Area (6-8)', 'Heavy Area (8-10)'])

print("Generating plots by year...")
# 1. Generate plots by year
years = sorted(df['Year'].unique())
for year in years:
    if pd.notna(year) and year >= 1940 and year <= 1945:
        year_data = df[df['Year'] == year]
        if len(year_data) > 0:
            print(f"  Processing year {year} ({len(year_data)} raids)")
            generate_plots(year_data, f"Year {year}", "plots/years")

# Year-specific visualizations
print("Creating year evolution plots...")
# 1. Evolution of bombing scores over years
plt.figure(figsize=(14, 8))
yearly_scores = df.groupby('Year')['AREA_BOMBING_SCORE_NORMALIZED'].agg(['mean', 'median', 'std']).reset_index()
yearly_scores = yearly_scores[(yearly_scores['Year'] >= 1940) & (yearly_scores['Year'] <= 1945)]

plt.errorbar(yearly_scores['Year'], yearly_scores['mean'], yerr=yearly_scores['std'], 
             fmt='o-', capsize=5, capthick=2, label='Mean Score ± Std Dev')
plt.plot(yearly_scores['Year'], yearly_scores['median'], 's--', color='red', label='Median Score')
plt.grid(True, alpha=0.3)
plt.title('Evolution of Area Bombing Scores Throughout the War', fontsize=18)
plt.xlabel('Year', fontsize=14)
plt.ylabel('Area Bombing Score', fontsize=14)
plt.xticks(yearly_scores['Year'], fontsize=12)
plt.ylim(0, 10)  # Consistent y-axis limit
plt.legend(fontsize=12)
plt.tight_layout()
plt.savefig('plots/years/yearly_evolution.png', dpi=300)
plt.close()

# 2. Stacked bar chart of bombing categories by year
plt.figure(figsize=(14, 8))
year_cat = pd.crosstab(df['Year'], df['Score Category'])
year_cat = year_cat.loc[year_cat.index.astype(float).astype(int).isin(range(1940, 1946))]
year_cat_pct = year_cat.div(year_cat.sum(axis=1), axis=0) * 100

year_cat_pct.plot(kind='bar', stacked=True, colormap='viridis')
plt.title('Distribution of Bombing Categories by Year', fontsize=18)
plt.xlabel('Year', fontsize=14)
plt.ylabel('Percentage of Raids', fontsize=14)
plt.xticks(rotation=0, fontsize=12)
plt.ylim(0, 100)  # Consistent y-axis limit for percentage plots
plt.legend(title='Bombing Category', title_fontsize=12, fontsize=10, loc='upper left', bbox_to_anchor=(1, 1))
plt.grid(True, alpha=0.3, axis='y')

# Add percentage text on bars
for i, year in enumerate(year_cat_pct.index):
    cumulative_sum = 0
    for j, col in enumerate(year_cat_pct.columns):
        # Only add text for segments that are at least 5% of the total
        if year_cat_pct.loc[year, col] >= 5:
            plt.text(i, cumulative_sum + year_cat_pct.loc[year, col]/2,
                    f"{year_cat_pct.loc[year, col]:.1f}%", ha='center', va='center',
                    fontsize=10, fontweight='bold', color='white')
        cumulative_sum += year_cat_pct.loc[year, col]

plt.tight_layout()
plt.savefig('plots/years/category_by_year.png', dpi=300)
plt.close()

print("Generating plots by category...")
# 2. Generate plots by category
for category in df['CATEGORY'].unique():
    if pd.notna(category):
        category_data = df[df['CATEGORY'] == category]
        if len(category_data) > 100:  # Only process categories with substantial data
            print(f"  Processing category {category} ({len(category_data)} raids)")
            generate_plots(category_data, f"Category {category}", "plots/categories")

# Category-specific visualizations
print("Creating category comparison plots...")
# 1. Box plot comparing categories
plt.figure(figsize=(16, 10))
# Sort categories by median score
cat_medians = df.groupby('CATEGORY')['AREA_BOMBING_SCORE_NORMALIZED'].median().sort_values(ascending=False)
top_categories = cat_medians.index[:12]  # Focus on top 12 categories for readability

cat_subset = df[df['CATEGORY'].isin(top_categories)]
ax = sns.boxplot(x='CATEGORY', y='AREA_BOMBING_SCORE_NORMALIZED', 
                order=cat_medians.index[:12],
                data=cat_subset, palette='viridis')
plt.title('Area Bombing Scores by Target Category', fontsize=18)
plt.xlabel('Target Category', fontsize=14)
plt.ylabel('Area Bombing Score', fontsize=14)
plt.ylim(0, 10)  # Consistent y-axis limit
plt.xticks(rotation=45, ha='right', fontsize=12)
plt.grid(True, alpha=0.3, axis='y')
plt.tight_layout()
plt.savefig('plots/categories/category_comparison.png', dpi=300)
plt.close()

# 2. Heatmap of category and year
plt.figure(figsize=(16, 10))
pivot_data = df.pivot_table(
    values='AREA_BOMBING_SCORE_NORMALIZED',
    index='CATEGORY',
    columns='Year',
    aggfunc='mean'
)
# Focus on years 1940-1945 and categories with sufficient data
pivot_filtered = pivot_data.loc[pivot_data.count(axis=1) >= 3, [y for y in range(1940, 1946) if y in pivot_data.columns]]
pivot_filtered = pivot_filtered.dropna(thresh=3)  # Drop rows with too many NaNs

# Set consistent color scale for heatmap
sns.heatmap(pivot_filtered, cmap='viridis', annot=True, fmt='.1f', linewidths=0.5, 
            cbar_kws={'label': 'Average Area Bombing Score'}, vmin=0, vmax=10)
plt.title('Average Area Bombing Score by Category and Year', fontsize=18)
plt.xlabel('Year', fontsize=14)
plt.ylabel('Target Category', fontsize=14)
plt.tight_layout()
plt.savefig('plots/categories/category_year_heatmap.png', dpi=300)
plt.close()

print("Generating plots by city...")
# 3. Generate plots for top 10 cities
for city in top_cities:
    city_data = df[df['Location'] == city]
    if len(city_data) > 0:
        print(f"  Processing city {city} ({len(city_data)} raids)")
        generate_plots(city_data, f"City {city}", "plots/cities")

# City-specific visualizations
print("Creating city comparison plots...")
# 1. Bar chart of average bombing scores for top cities
plt.figure(figsize=(14, 8))
city_scores = df[df['Location'].isin(top_cities)].groupby('Location')['AREA_BOMBING_SCORE_NORMALIZED'].mean().sort_values(ascending=False)

# Create a colormap based on the scores
colors = plt.cm.viridis(np.linspace(0, 1, len(city_scores)))

city_scores.plot(kind='bar', color=colors)
plt.title('Average Area Bombing Score by City', fontsize=18)
plt.xlabel('City', fontsize=14)
plt.ylabel('Average Area Bombing Score', fontsize=14)
plt.xticks(rotation=45, ha='right', fontsize=12)
plt.grid(True, alpha=0.3, axis='y')
plt.ylim(0, 10)  # Consistent y-axis limit

# Add values above bars
for i, v in enumerate(city_scores):
    plt.text(i, v + 0.2, f"{v:.1f}", ha='center', fontsize=12, fontweight='bold')

plt.tight_layout()
plt.savefig('plots/cities/city_comparison.png', dpi=300)
plt.close()

# 2. Evolution of bombing intensity for top 5 cities
plt.figure(figsize=(14, 8))
top5_cities = city_scores.index[:5]  # Top 5 most heavily bombed cities by score
city_year_counts = df[df['Location'].isin(top5_cities)].pivot_table(
    values='AREA_BOMBING_SCORE_NORMALIZED', 
    index='Year', 
    columns='Location', 
    aggfunc='mean'
)

# Filter to just 1940-1945
city_year_counts = city_year_counts.loc[city_year_counts.index.astype(int).isin(range(1940, 1946))]

for city in city_year_counts.columns:
    plt.plot(city_year_counts.index, city_year_counts[city], 'o-', linewidth=2, markersize=8, label=city)

plt.title('Evolution of Bombing Strategy for Top 5 Cities', fontsize=18)
plt.xlabel('Year', fontsize=14)
plt.ylabel('Average Area Bombing Score', fontsize=14)
plt.xticks(city_year_counts.index, fontsize=12)
plt.grid(True, alpha=0.3)
plt.ylim(0, 10)  # Consistent y-axis limit
plt.legend(fontsize=12)
plt.tight_layout()
plt.savefig('plots/cities/city_evolution.png', dpi=300)
plt.close()

# 3. Stacked bar chart showing proportion of raid categories for top cities
plt.figure(figsize=(14, 8))
city_categories = pd.crosstab(df[df['Location'].isin(top_cities)]['Location'], df[df['Location'].isin(top_cities)]['Score Category'])
city_categories_pct = city_categories.div(city_categories.sum(axis=1), axis=0) * 100

# Sort by proportion of area bombing (highest to lowest)
area_proportion = city_categories_pct['Area (6-8)'] + city_categories_pct['Heavy Area (8-10)']
sorted_cities = area_proportion.sort_values(ascending=False).index

city_categories_pct = city_categories_pct.loc[sorted_cities]

city_categories_pct.plot(kind='bar', stacked=True, colormap='viridis', figsize=(14, 8))
plt.title('Distribution of Bombing Categories by City', fontsize=18)
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
plt.savefig('plots/cities/category_by_city.png', dpi=300)
plt.close()

print("Visualization complete. Results saved to plots/years, plots/categories, and plots/cities directories.") 