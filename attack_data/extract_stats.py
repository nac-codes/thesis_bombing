import pandas as pd
import numpy as np

# Load USAAF data - using same path as in visualize_usaaf_bombing.py
print('Loading USAAF bombing data...')
try:
    df = pd.read_csv('processed_data/usaaf/usaaf_raids_classification_with_category.csv')
    
    # Clean up year data similar to visualize_usaaf_bombing.py
    print('Cleaning year data...')
    df['YEAR'] = df['YEAR'].fillna(0).astype(float)
    df['Year'] = (1940 + df['YEAR']).astype(int)
    df.loc[df['Year'] < 1939, 'Year'] = 1940
    df.loc[df['Year'] > 1946, 'Year'] = 1945
    
    # Add the score category field as in visualize_usaaf_bombing.py
    df['Score Category'] = pd.cut(df['AREA_BOMBING_SCORE_NORMALIZED'], 
                             bins=[0, 2, 4, 6, 8, 10],
                             labels=['Very Precise (0-2)', 'Precise (2-4)', 
                                    'Mixed (4-6)', 'Area (6-8)', 'Heavy Area (8-10)'])
                                    
    # Create clean location field
    df['Location'] = df['target_location'].str.strip().str.upper()
    
    print('\n=== OVERALL STATISTICS ===')
    print(f'Total USAAF raids analyzed: {len(df)}')
    print(f'Mean area bombing score: {df["AREA_BOMBING_SCORE_NORMALIZED"].mean():.2f}')
    print(f'Median area bombing score: {df["AREA_BOMBING_SCORE_NORMALIZED"].median():.2f}')
    print(f'Standard deviation: {df["AREA_BOMBING_SCORE_NORMALIZED"].std():.2f}')
    
    # Category distribution
    print('\n=== CATEGORY DISTRIBUTION ===')
    cat_dist = df['Score Category'].value_counts(normalize=True) * 100
    for cat, pct in cat_dist.sort_index().items():
        print(f'{cat}: {pct:.1f}%')
    
    # Group 'Very Precise' and 'Precise' together
    precise_total = cat_dist['Very Precise (0-2)'] + cat_dist['Precise (2-4)']
    print(f'Total "Very Precise" or "Precise": {precise_total:.1f}%')
    
    # Group 'Area' and 'Heavy Area' together
    area_total = cat_dist['Area (6-8)'] + cat_dist['Heavy Area (8-10)']
    print(f'Total "Area" or "Heavy Area": {area_total:.1f}%')
    
    print('\n=== YEARLY STATISTICS ===')
    yearly_stats = df.groupby('Year')['AREA_BOMBING_SCORE_NORMALIZED'].agg(['mean', 'median', 'std', 'count'])
    for year, row in yearly_stats.iterrows():
        if year >= 1940 and year <= 1945 and row['count'] > 10:
            print(f'Year {year}: Mean={row["mean"]:.2f}, Median={row["median"]:.2f}, StdDev={row["std"]:.2f}, Count={row["count"]}')
    
    print('\n=== YEARLY CATEGORY DISTRIBUTION ===')
    for year in range(1942, 1946):
        if year in df['Year'].values:
            year_data = df[df['Year'] == year]
            year_cats = year_data['Score Category'].value_counts(normalize=True) * 100
            print(f'\nYear {year} (n={len(year_data)}):')
            for cat in ['Very Precise (0-2)', 'Precise (2-4)', 'Mixed (4-6)', 'Area (6-8)', 'Heavy Area (8-10)']:
                if cat in year_cats:
                    print(f'  {cat}: {year_cats[cat]:.1f}%')
                else:
                    print(f'  {cat}: 0.0%')
    
    print('\n=== TARGET CATEGORY ANALYSIS ===')
    cat_scores = df.groupby('CATEGORY')['AREA_BOMBING_SCORE_NORMALIZED'].agg(['mean', 'median', 'count'])
    cat_scores = cat_scores.sort_values('mean', ascending=False)
    for cat, row in cat_scores.iterrows():
        if row['count'] >= 20:  # Only show categories with sufficient data
            print(f'{cat}: Mean={row["mean"]:.2f}, Median={row["median"]:.2f}, Count={row["count"]}')
    
    print('\n=== BERLIN ANALYSIS ===')
    berlin_data = df[df['Location'] == 'BERLIN']
    print(f'Number of Berlin raids: {len(berlin_data)}')
    print(f'Mean area bombing score: {berlin_data["AREA_BOMBING_SCORE_NORMALIZED"].mean():.2f}')
    print(f'Median area bombing score: {berlin_data["AREA_BOMBING_SCORE_NORMALIZED"].median():.2f}')
    print(f'Average incendiary percentage: {berlin_data["INCENDIARY_PERCENT"].mean():.1f}%')
    
    berlin_cats = berlin_data['Score Category'].value_counts(normalize=True) * 100
    for cat, pct in berlin_cats.sort_index().items():
        print(f'{cat}: {pct:.1f}%')
    
    precise_berlin = berlin_cats.get('Very Precise (0-2)', 0) + berlin_cats.get('Precise (2-4)', 0)
    mixed_berlin = berlin_cats.get('Mixed (4-6)', 0)
    area_berlin = berlin_cats.get('Area (6-8)', 0) + berlin_cats.get('Heavy Area (8-10)', 0)
    print(f'"Very Precise" or "Precise": {precise_berlin:.1f}%')
    print(f'"Mixed": {mixed_berlin:.1f}%')
    print(f'"Area" or "Heavy Area": {area_berlin:.1f}%')
    
    print('\n=== TRANSPORTATION TARGET ANALYSIS ===')
    transport_data = df[df['CATEGORY'] == 'transportation']
    if len(transport_data) > 0:
        print(f'Number of transportation raids: {len(transport_data)}')
        print(f'Mean area bombing score: {transport_data["AREA_BOMBING_SCORE_NORMALIZED"].mean():.2f}')
        print(f'Median area bombing score: {transport_data["AREA_BOMBING_SCORE_NORMALIZED"].median():.2f}')
        print(f'Average incendiary percentage: {transport_data["INCENDIARY_PERCENT"].mean():.1f}%')
        
        transport_cats = transport_data['Score Category'].value_counts(normalize=True) * 100
        for cat, pct in transport_cats.sort_index().items():
            print(f'{cat}: {pct:.1f}%')
        
        precise_transport = transport_cats.get('Very Precise (0-2)', 0) + transport_cats.get('Precise (2-4)', 0)
        mixed_transport = transport_cats.get('Mixed (4-6)', 0)
        area_transport = transport_cats.get('Area (6-8)', 0) + transport_cats.get('Heavy Area (8-10)', 0)
        print(f'"Very Precise" or "Precise": {precise_transport:.1f}%')
        print(f'"Mixed": {mixed_transport:.1f}%')
        print(f'"Area" or "Heavy Area": {area_transport:.1f}%')
    
except Exception as e:
    print(f'Error: {e}') 