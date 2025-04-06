import pandas as pd
import numpy as np

# Load USAAF data
print('Loading USAAF bombing data...')
try:
    df = pd.read_csv('processed_data/usaaf/usaaf_raids_classification_with_category.csv')
    
    # Clean up year data
    print('Cleaning year data...')
    df['YEAR'] = df['YEAR'].fillna(0).astype(float)
    df['Year'] = (1940 + df['YEAR']).astype(int)
    df.loc[df['Year'] < 1939, 'Year'] = 1940
    df.loc[df['Year'] > 1946, 'Year'] = 1945
    
    # Add score category
    df['Score Category'] = pd.cut(df['AREA_BOMBING_SCORE_NORMALIZED'], 
                             bins=[0, 2, 4, 6, 8, 10],
                             labels=['Very Precise (0-2)', 'Precise (2-4)', 
                                    'Mixed (4-6)', 'Area (6-8)', 'Heavy Area (8-10)'])
                                    
    # Create clean location field
    df['Location'] = df['target_location'].str.strip().str.upper()
    
    print('\n=== TONNAGE STATISTICS ===')
    print(f'Total tonnage dropped: {df["TOTAL_TONS"].sum():,.2f} tons')
    
    # Add HE tonnage and incendiary tonnage calculations if missing
    if 'HE_TONS' not in df.columns:
        df['INCENDIARY_PERCENT'] = df['INCENDIARY_PERCENT'].fillna(0)
        df['HE_PERCENT'] = 100 - df['INCENDIARY_PERCENT']
        df['HE_TONS'] = df['TOTAL_TONS'] * df['HE_PERCENT'] / 100
        df['INCENDIARY_TONS'] = df['TOTAL_TONS'] * df['INCENDIARY_PERCENT'] / 100
    
    print(f'High explosive tonnage: {df["HE_TONS"].sum():,.2f} tons ({df["HE_TONS"].sum()/df["TOTAL_TONS"].sum()*100:.1f}%)')
    print(f'Incendiary tonnage: {df["INCENDIARY_TONS"].sum():,.2f} tons ({df["INCENDIARY_TONS"].sum()/df["TOTAL_TONS"].sum()*100:.1f}%)')
    print(f'Average tonnage per raid: {df["TOTAL_TONS"].mean():.2f} tons')
    print(f'Median tonnage per raid: {df["TOTAL_TONS"].median():.2f} tons')
    
    print('\n=== YEARLY TONNAGE STATISTICS ===')
    yearly_tonnage = df.groupby('Year').agg({
        'TOTAL_TONS': ['sum', 'mean'],
        'HE_TONS': 'sum',
        'INCENDIARY_TONS': 'sum',
        'raid_id': 'count'
    })
    yearly_tonnage.columns = ['Total_Tons', 'Avg_Tons_Per_Raid', 'HE_Tons', 'Incendiary_Tons', 'Raid_Count']
    yearly_tonnage['Incendiary_Pct'] = yearly_tonnage['Incendiary_Tons'] / yearly_tonnage['Total_Tons'] * 100
    
    for year, row in yearly_tonnage.iterrows():
        if year >= 1940 and year <= 1945 and row['Raid_Count'] > 10:
            print(f'Year {year}: Total={row["Total_Tons"]:,.2f} tons, Average={row["Avg_Tons_Per_Raid"]:.2f} tons/raid, Incendiary={row["Incendiary_Pct"]:.1f}%, Raids={row["Raid_Count"]}')
    
    print('\n=== TONNAGE BY TARGET CATEGORY ===')
    category_tonnage = df.groupby('CATEGORY').agg({
        'TOTAL_TONS': ['sum', 'mean', 'count'],
        'HE_TONS': 'sum',
        'INCENDIARY_TONS': 'sum'
    })
    category_tonnage.columns = ['Total_Tons', 'Avg_Tons', 'Raid_Count', 'HE_Tons', 'Incendiary_Tons']
    category_tonnage['Pct_Of_Total'] = category_tonnage['Total_Tons'] / category_tonnage['Total_Tons'].sum() * 100
    category_tonnage['Incendiary_Pct'] = category_tonnage['Incendiary_Tons'] / category_tonnage['Total_Tons'] * 100
    
    # Sort by total tonnage
    category_tonnage = category_tonnage.sort_values('Total_Tons', ascending=False)
    
    for cat, row in category_tonnage.iterrows():
        if row['Raid_Count'] >= 20:  # Only show categories with sufficient data
            print(f'{cat}: {row["Total_Tons"]:,.2f} tons ({row["Pct_Of_Total"]:.1f}% of total), Avg={row["Avg_Tons"]:.2f} tons/raid, Inc={row["Incendiary_Pct"]:.1f}%, Raids={row["Raid_Count"]}')
    
    print('\n=== TOP 10 CITIES BY TONNAGE ===')
    city_tonnage = df.groupby('Location').agg({
        'TOTAL_TONS': ['sum', 'mean', 'count'],
        'HE_TONS': 'sum',
        'INCENDIARY_TONS': 'sum',
        'AREA_BOMBING_SCORE_NORMALIZED': 'mean'
    })
    city_tonnage.columns = ['Total_Tons', 'Avg_Tons', 'Raid_Count', 'HE_Tons', 'Incendiary_Tons', 'Avg_Score']
    city_tonnage['Incendiary_Pct'] = city_tonnage['Incendiary_Tons'] / city_tonnage['Total_Tons'] * 100
    
    # Get top cities by tonnage
    top_cities_tonnage = city_tonnage.sort_values('Total_Tons', ascending=False).head(10)
    
    for city, row in top_cities_tonnage.iterrows():
        print(f'{city}: {row["Total_Tons"]:,.2f} tons, Avg Score={row["Avg_Score"]:.2f}, Inc={row["Incendiary_Pct"]:.1f}%, Raids={row["Raid_Count"]}')
    
    print('\n=== TOP 10 CITIES BY AREA BOMBING SCORE ===')
    # Get top cities by area bombing score (min 5 raids)
    top_cities_score = city_tonnage[city_tonnage['Raid_Count'] >= 5].sort_values('Avg_Score', ascending=False).head(10)
    
    for city, row in top_cities_score.iterrows():
        print(f'{city}: Score={row["Avg_Score"]:.2f}, {row["Total_Tons"]:,.2f} tons, Inc={row["Incendiary_Pct"]:.1f}%, Raids={row["Raid_Count"]}')
    
    print('\n=== QUARTERLY PROGRESSION STATISTICS ===')
    # Create quarterly data for trend analysis
    df['Quarter'] = pd.PeriodIndex(pd.to_datetime(df['Year'].astype(str) + 'Q' + ((df['MONTH'].fillna(1).astype(int) - 1) // 3 + 1).astype(str)), freq='Q')
    
    quarterly_stats = df.groupby('Quarter').agg({
        'AREA_BOMBING_SCORE_NORMALIZED': 'mean',
        'TOTAL_TONS': ['sum', 'mean'],
        'INCENDIARY_PERCENT': 'mean',
        'raid_id': 'count'
    })
    quarterly_stats.columns = ['Avg_Score', 'Total_Tons', 'Avg_Tons', 'Inc_Pct', 'Raids']
    
    # Only show quarters with significant data
    for quarter, row in quarterly_stats[quarterly_stats['Raids'] >= 20].iterrows():
        print(f'{quarter}: Score={row["Avg_Score"]:.2f}, Tons={row["Total_Tons"]:,.2f}, Raids={row["Raids"]}, Inc%={row["Inc_Pct"]:.1f}%')
    
    print('\n=== COMPONENT SCORE STATISTICS ===')
    print(f'Target Type (Industrial) Score - Mean: {df["TARGET_SCORE"].mean()*10:.2f}, Median: {df["TARGET_SCORE"].median()*10:.2f}')
    print(f'Incendiary Score - Mean: {df["INCENDIARY_SCORE"].mean():.2f}, Median: {df["INCENDIARY_SCORE"].median():.2f}')
    print(f'Tonnage Score - Mean: {df["TONNAGE_SCORE"].mean():.2f}, Median: {df["TONNAGE_SCORE"].median():.2f}')
    
    print('\n=== CORRELATIONS BETWEEN COMPONENTS ===')
    corr_matrix = df[['TARGET_SCORE', 'INCENDIARY_SCORE', 'TONNAGE_SCORE', 'AREA_BOMBING_SCORE_NORMALIZED']].corr()
    print(corr_matrix)
    
    print('\n=== STATISTICAL DISTRIBUTIONS ===')
    for score_type in ['AREA_BOMBING_SCORE_NORMALIZED', 'INCENDIARY_PERCENT', 'TOTAL_TONS']:
        data = df[score_type].dropna()
        percentiles = [10, 25, 50, 75, 90, 95, 99]
        values = np.percentile(data, percentiles)
        print(f'\n{score_type} Percentiles:')
        for p, v in zip(percentiles, values):
            print(f'{p}th percentile: {v:.2f}')
    
except Exception as e:
    print(f'Error: {e}') 