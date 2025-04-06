import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import os

# Create directory for reports
if not os.path.exists('reports'):
    os.makedirs('reports')

# Load the data
print("Loading data...")
df = pd.read_csv('processed_data/raids_area_bombing_classification.csv')

# Open file for writing the report
with open('reports/bombing_classification_report.txt', 'w') as report:
    # Title and introduction
    report.write("=======================================================\n")
    report.write("     BOMBING RAID CLASSIFICATION DETAILED ANALYSIS     \n")
    report.write("=======================================================\n\n")
    
    report.write("This report provides a comprehensive analysis of bombing raids classified\n")
    report.write("on a precision-to-area bombing continuum (0-10 scale) based on target type,\n")
    report.write("tonnage, and incendiary usage.\n\n")
    
    # 1. Overall Statistics
    report.write("=======================================================\n")
    report.write("1. OVERALL STATISTICS\n")
    report.write("=======================================================\n\n")
    
    # Basic statistics
    report.write("Total raids analyzed: {:,}\n".format(len(df)))
    report.write("Area bombing targets (INDUSTRIAL book): {:,} ({:.1f}%)\n".format(
        df['TARGET_SCORE'].sum(), df['TARGET_SCORE'].sum()/len(df)*100))
    report.write("Precision bombing targets (other books): {:,} ({:.1f}%)\n\n".format(
        len(df) - df['TARGET_SCORE'].sum(), (len(df) - df['TARGET_SCORE'].sum())/len(df)*100))
    
    # Area bombing score distribution
    score_stats = df['AREA_BOMBING_SCORE_NORMALIZED'].describe()
    report.write("Area Bombing Score Distribution:\n")
    for stat in ['min', '25%', '50%', 'mean', '75%', 'max', 'std']:
        report.write("  - {}: {:.2f}\n".format(stat, score_stats[stat]))
    report.write("\n")
    
    # Score distribution by percentiles
    percentiles = [5, 10, 25, 50, 75, 90, 95, 99]
    perc_values = np.percentile(df['AREA_BOMBING_SCORE_NORMALIZED'], percentiles)
    report.write("Score distribution by percentiles:\n")
    for p, v in zip(percentiles, perc_values):
        report.write("  - {}th percentile: {:.2f}\n".format(p, v))
    report.write("\n")
    
    # 2. Score Categories
    report.write("=======================================================\n")
    report.write("2. BOMBING CATEGORIES\n")
    report.write("=======================================================\n\n")
    
    # Create bombing categories
    df['Score Category'] = pd.cut(df['AREA_BOMBING_SCORE_NORMALIZED'], 
                                 bins=[0, 2, 4, 6, 8, 10],
                                 labels=['Very Precise (0-2)', 'Precise (2-4)', 
                                        'Mixed (4-6)', 'Area (6-8)', 'Heavy Area (8-10)'])
    
    category_counts = df['Score Category'].value_counts().sort_index()
    category_percent = (category_counts / len(df) * 100).round(1)
    
    report.write("Distribution of raids by bombing category:\n")
    for category, count, percent in zip(category_counts.index, category_counts, category_percent):
        report.write("  - {}: {:,} raids ({:.1f}%)\n".format(category, count, percent))
    report.write("\n")
    
    # 3. Analysis by Target Type
    report.write("=======================================================\n")
    report.write("3. ANALYSIS BY TARGET TYPE\n")
    report.write("=======================================================\n\n")
    
    # Map target types
    df['Target Type'] = df['TARGET_SCORE'].map({1: 'Industrial/Area', 0: 'Non-Industrial/Precision'})
    
    # Calculate statistics by target type
    target_stats = df.groupby('Target Type')['AREA_BOMBING_SCORE_NORMALIZED'].describe()
    
    report.write("Area Bombing Score by Target Type:\n\n")
    for target_type in target_stats.index:
        report.write("{} Targets:\n".format(target_type))
        stats = target_stats.loc[target_type]
        for stat in ['count', 'min', '25%', '50%', 'mean', '75%', 'max', 'std']:
            if stat == 'count':
                report.write("  - {}: {:,}\n".format(stat, int(stats[stat])))
            else:
                report.write("  - {}: {:.2f}\n".format(stat, stats[stat]))
        report.write("\n")
    
    # Category breakdown by target type
    target_category = pd.crosstab(df['Target Type'], df['Score Category'], normalize='index') * 100
    
    report.write("Bombing Category Distribution by Target Type (%):\n\n")
    report.write(target_category.to_string(float_format='{:.1f}%'.format))
    report.write("\n\n")
    
    # 4. Component Analysis
    report.write("=======================================================\n")
    report.write("4. COMPONENT ANALYSIS\n")
    report.write("=======================================================\n\n")
    
    # Tonnage distribution
    tonnage_stats = df['TOTAL_TONS'].describe(percentiles=[.1, .25, .5, .75, .9, .95, .99])
    
    report.write("Tonnage Distribution:\n")
    for stat in ['min', '10%', '25%', '50%', 'mean', '75%', '90%', '95%', '99%', 'max', 'std']:
        if stat in tonnage_stats:
            report.write("  - {}: {:.2f} tons\n".format(stat, tonnage_stats[stat]))
    report.write("\n")
    
    # Incendiary percentage distribution
    incendiary_stats = df['INCENDIARY_PERCENT'].describe(percentiles=[.1, .25, .5, .75, .9, .95, .99])
    
    report.write("Incendiary Percentage Distribution:\n")
    for stat in ['min', '10%', '25%', '50%', 'mean', '75%', '90%', '95%', '99%', 'max', 'std']:
        if stat in incendiary_stats:
            report.write("  - {}: {:.2f}%\n".format(stat, incendiary_stats[stat]))
    report.write("\n")
    
    # Correlations
    corr = df[['TARGET_SCORE', 'TONNAGE_SCORE', 'INCENDIARY_SCORE', 
              'AREA_BOMBING_SCORE_NORMALIZED']].corr()
    
    report.write("Correlation Matrix:\n")
    report.write(corr.to_string(float_format='{:.3f}'.format))
    report.write("\n\n")
    
    # 5. Example Raids
    report.write("=======================================================\n")
    report.write("5. EXAMPLE RAIDS ACROSS THE CONTINUUM\n")
    report.write("=======================================================\n\n")
    
    # Sample raids from each category
    examples = []
    # Define the score ranges directly instead of using the categorical column
    score_ranges = [(8, 10), (6, 8), (4, 6), (2, 4), (0, 2)]
    for low, high in score_ranges:
        subset = df[(df['AREA_BOMBING_SCORE_NORMALIZED'] >= low) & 
                   (df['AREA_BOMBING_SCORE_NORMALIZED'] < high)]
        if len(subset) > 0:
            examples.append(subset.sample(min(3, len(subset))))
    
    example_df = pd.concat(examples)
    example_df = example_df.sort_values('AREA_BOMBING_SCORE_NORMALIZED', ascending=False)
    
    # Selected columns for examples
    example_cols = ['target_location', 'target_name', 'TARGET_SCORE', 
                   'TONNAGE_SCORE', 'INCENDIARY_SCORE', 'AREA_BOMBING_SCORE_NORMALIZED']
    
    report.write(example_df[example_cols].to_string(index=False))
    report.write("\n\n")
    
    # 6. Time Series Analysis (if date information is available)
    if all(col in df.columns for col in ['YEAR', 'MONTH']):
        report.write("=======================================================\n")
        report.write("6. TEMPORAL ANALYSIS\n")
        report.write("=======================================================\n\n")
        
        try:
            df['Date'] = pd.to_datetime(df['YEAR'].astype(str) + '-' + df['MONTH'].astype(str), format='%Y-%m')
            monthly_avg = df.groupby(df['Date'].dt.to_period('M'))['AREA_BOMBING_SCORE_NORMALIZED'].mean()
            
            report.write("Average Area Bombing Score by Month:\n")
            report.write(monthly_avg.to_string())
            report.write("\n\n")
        except:
            report.write("Date information is available but could not be processed correctly.\n\n")
    
    # Conclusion
    report.write("=======================================================\n")
    report.write("CONCLUSION\n")
    report.write("=======================================================\n\n")
    
    precision_percent = category_percent.loc['Very Precise (0-2)'] + category_percent.loc['Precise (2-4)']
    area_percent = category_percent.loc['Area (6-8)'] + category_percent.loc['Heavy Area (8-10)']
    
    report.write("This analysis reveals that approximately {:.1f}% of raids were predominantly\n".format(precision_percent))
    report.write("precision bombing in nature, while only about {:.1f}% fall clearly\n".format(area_percent))
    report.write("into the area bombing category. This supports the historical understanding\n")
    report.write("that while area bombing was a significant strategy, precision bombing\n")
    report.write("was more frequently attempted, though often with varying degrees of success.\n")

print("Report generated at 'reports/bombing_classification_report.txt'") 