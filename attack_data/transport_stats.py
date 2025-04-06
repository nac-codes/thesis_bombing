import pandas as pd

# Load data
df = pd.read_csv('processed_data/usaaf/usaaf_raids_classification_with_category.csv')

# Add score categories
df['Score Category'] = pd.cut(df['AREA_BOMBING_SCORE_NORMALIZED'], 
                         bins=[0, 2, 4, 6, 8, 10],
                         labels=['Very Precise (0-2)', 'Precise (2-4)', 
                                'Mixed (4-6)', 'Area (6-8)', 'Heavy Area (8-10)'])

# Filter for transportation targets (check both upper and lower case)
transport_data = df[df['CATEGORY'].str.upper() == 'TRANSPORTATION']

print('=== TRANSPORTATION TARGET ANALYSIS ===')
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