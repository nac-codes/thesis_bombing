import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import logging
import numpy as np

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Set style for high-quality visualizations
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.dpi'] = 300
plt.rcParams['figure.figsize'] = [12, 8]
plt.rcParams['font.size'] = 12

# Create reports directory if it doesn't exist
reports_dir = Path('reports/tons/')
reports_dir.mkdir(exist_ok=True)

def load_and_prepare_data(file_path):
    # Read the data
    df = pd.read_csv(file_path)
    
    # Create RAF indicator
    df['is_RAF'] = df['AIR FORCE'].astype(str).str.contains('R', na=False)
    df['force_name'] = df['is_RAF'].map({True: 'RAF', False: 'USAAF'})

    # Convert tonnage columns to numeric and fill NaNs with 0
    tonnage_columns = ['HIGH EXPLOSIVE BOMBS TONS', 'INCENDIARY BOMBS TONS', 'FRAGMENTATION BOMBS TONS', 'TOTAL TONS']
    for col in tonnage_columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Create attack type tonnage
    df['HE_tonnage'] = df['HIGH EXPLOSIVE BOMBS TONS']
    df['Incendiary_tonnage'] = df['INCENDIARY BOMBS TONS']
    df['Fragmentation_tonnage'] = df['FRAGMENTATION BOMBS TONS']

    # Create area target indicators
    df['is_city_target'] = (
        df['target_name'].str.contains('CITY', case=True, na=False) |
        df['target_name'].str.contains('CITY AREA', case=True, na=False)
    )
    df['is_industrial_book'] = df['book'].str.contains('INDUSTRIAL', case=True, na=False)
    
    return df

def preprocess_data(df):
    """Prepare data with cleaned dates and categories for all analyses"""
    logging.debug("Starting data preprocessing")
    
    # Create a copy to avoid warnings
    df = df.copy()
    
    # Clean date fields
    df['YEAR'] = df['YEAR'].apply(clean_date_field)
    df['MONTH'] = df['MONTH'].apply(clean_date_field)
    df['DAY'] = df['DAY'].apply(clean_date_field)
    
    # Drop rows with invalid dates
    df = df.dropna(subset=['YEAR', 'MONTH'])
    logging.debug(f"Dropped rows with invalid dates. Remaining rows: {len(df)}")
    
    # Convert single-digit years to full years
    df['YEAR'] = df['YEAR'].apply(lambda x: x + 1940 if x < 10 else x)
    
    # Ensure years and months are valid
    df = df[df['YEAR'].between(1940, 1945)]
    df = df[df['MONTH'].between(1, 12)]
    logging.debug(f"Filtered years and months. Remaining rows: {len(df)}")
    
    # Create date column
    df['date'] = pd.to_datetime({
        'year': df['YEAR'].astype(int),
        'month': df['MONTH'].astype(int),
        'day': 1
    })
    
    # Add book category
    df['book_category'] = df['book'].apply(extract_book_category)
    
    # Remove summation rows if any
    if 'SUMMATION_ROW' in df.columns:
        df = df[df['SUMMATION_ROW'] != True]
    
    logging.debug("Data preprocessing complete")
    return df

def extract_book_category(book_name):
    """Extract category from book name format BOOK_NUMBER_CATEGORY__PART_X"""
    # Split by underscore and get the category part
    parts = book_name.split('_')
    if len(parts) < 3:
        return 'Unknown'
    
    # Find where the category starts (after BOOK_NUMBER_)
    category_parts = []
    for part in parts[2:]:
        if part.startswith('PART'):
            break
        category_parts.append(part)
    
    # Join category parts back together
    category = ' '.join(category_parts)
    return category.replace('__', '')  # Remove any double underscores

def clean_date_field(value):
    """Clean date fields by taking first number if there are multiple"""
    if pd.isna(value):
        return value
    
    # Convert to string and handle any potential float formatting
    str_val = str(value).split('.')[0]
    
    # If there's a range (e.g., "18-19"), take the first number
    if '-' in str_val:
        str_val = str_val.split('-')[0]
    
    # Remove any non-numeric characters
    str_val = ''.join(c for c in str_val if c.isdigit())
    
    # Convert back to numeric, return NA if invalid
    try:
        return int(str_val) if str_val else None
    except ValueError:
        logging.warning(f"Invalid date field: {str_val}")
        return None

def create_attack_type_comparison(df):
    # Extract book categories
    df['book_category'] = df['book'].apply(extract_book_category)
    
    # Group by book category and force name, summing tonnage
    summary_data = df.groupby(['book_category', 'force_name']).agg({
        'HE_tonnage': 'sum',
        'Incendiary_tonnage': 'sum',
        'Fragmentation_tonnage': 'sum',
        'TOTAL TONS': 'sum'
    }).reset_index()
    
    # Pivot the data to get force names as columns
    pivot_data = summary_data.pivot(index='book_category', columns='force_name', values=['HE_tonnage', 'Incendiary_tonnage', 'Fragmentation_tonnage', 'TOTAL TONS'])
    pivot_data = pivot_data.fillna(0)
    
    # Flatten the MultiIndex columns
    pivot_data.columns = ['_'.join(col).strip() for col in pivot_data.columns.values]
    pivot_data = pivot_data.reset_index()
    
    # Sort by total tonnage
    pivot_data = pivot_data.sort_values('TOTAL TONS_RAF', ascending=True)
    
    # Create the visualization
    plt.figure(figsize=[15, 10])
    x = range(len(pivot_data))
    width = 0.35  # Width of the bars

    # Plot RAF tonnage
    plt.barh([i - width/2 for i in x], pivot_data['HE_tonnage_RAF'], width, label='RAF - HE', color='lightblue')
    plt.barh([i - width/2 for i in x], pivot_data['Incendiary_tonnage_RAF'], width, left=pivot_data['HE_tonnage_RAF'], label='RAF - Incendiary', color='blue')
    plt.barh([i - width/2 for i in x], pivot_data['Fragmentation_tonnage_RAF'], width, left=pivot_data['HE_tonnage_RAF'] + pivot_data['Incendiary_tonnage_RAF'], label='RAF - Fragmentation', color='navy')

    # Plot USAAF tonnage
    plt.barh([i + width/2 for i in x], pivot_data['HE_tonnage_USAAF'], width, label='USAAF - HE', color='lightcoral')
    plt.barh([i + width/2 for i in x], pivot_data['Incendiary_tonnage_USAAF'], width, left=pivot_data['HE_tonnage_USAAF'], label='USAAF - Incendiary', color='red')
    plt.barh([i + width/2 for i in x], pivot_data['Fragmentation_tonnage_USAAF'], width, left=pivot_data['HE_tonnage_USAAF'] + pivot_data['Incendiary_tonnage_USAAF'], label='USAAF - Fragmentation', color='darkred')

    # Customize the plot
    plt.yticks(x, pivot_data['book_category'], fontsize=10)
    plt.xlabel('Tonnage Dropped', fontsize=12)
    plt.title('Attack Types by Air Force and Target Category (Tonnage)', pad=20, fontsize=14)
    
    # Add legend
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # Add grid
    plt.grid(True, alpha=0.3)
    
    # Adjust layout
    plt.tight_layout()
    
    # Save the plot
    plt.savefig(reports_dir / 'attack_types_tonnage.png', bbox_inches='tight', dpi=300)
    plt.close()
    
    # Create and save a text summary
    summary_text = "Attack Types by Target Category Summary (Tonnage)\n"
    summary_text += "==========================================\n\n"
    
    for _, row in pivot_data.iterrows():
        total_tonnage_RAF = row['TOTAL TONS_RAF']
        total_tonnage_USAAF = row['TOTAL TONS_USAAF']
        total_tonnage = total_tonnage_RAF + total_tonnage_USAAF
        
        summary_text += f"\nCategory: {row['book_category']}\n"
        summary_text += f"  Total Tonnage: {total_tonnage:.2f}\n"
        summary_text += "\n  RAF Statistics:\n"
        summary_text += f"    Tonnage: {total_tonnage_RAF:.2f} ({total_tonnage_RAF/total_tonnage*100:.1f}% of Total)\n"
        summary_text += f"    HE Tonnage: {row['HE_tonnage_RAF']:.2f} ({row['HE_tonnage_RAF']/total_tonnage_RAF*100 if total_tonnage_RAF > 0 else 0:.1f}% of RAF)\n"
        summary_text += f"    Incendiary Tonnage: {row['Incendiary_tonnage_RAF']:.2f} ({row['Incendiary_tonnage_RAF']/total_tonnage_RAF*100 if total_tonnage_RAF > 0 else 0:.1f}% of RAF)\n"
        summary_text += f"    Fragmentation Tonnage: {row['Fragmentation_tonnage_RAF']:.2f} ({row['Fragmentation_tonnage_RAF']/total_tonnage_RAF*100 if total_tonnage_RAF > 0 else 0:.1f}% of RAF)\n"
        summary_text += "\n  USAAF Statistics:\n"
        summary_text += f"    Tonnage: {total_tonnage_USAAF:.2f} ({total_tonnage_USAAF/total_tonnage*100:.1f}% of Total)\n"
        if total_tonnage_USAAF > 0:
            summary_text += f"    HE Tonnage: {row['HE_tonnage_USAAF']:.2f} ({row['HE_tonnage_USAAF']/total_tonnage_USAAF*100:.1f}% of USAAF)\n"
            summary_text += f"    Incendiary Tonnage: {row['Incendiary_tonnage_USAAF']:.2f} ({row['Incendiary_tonnage_USAAF']/total_tonnage_USAAF*100:.1f}% of USAAF)\n"
            summary_text += f"    Fragmentation Tonnage: {row['Fragmentation_tonnage_USAAF']:.2f} ({row['Fragmentation_tonnage_USAAF']/total_tonnage_USAAF*100:.1f}% of USAAF)\n"
        else:
            summary_text += "    No USAAF tonnage\n"
    
    with open(reports_dir / 'attack_types_summary_tonnage.txt', 'w') as f:
        f.write(summary_text)

def create_temporal_analysis(df):
    logging.debug("Starting temporal analysis.")
    
    # Create results for each force and category combination
    results = []
    for force in ['RAF', 'USAAF']:
        force_data = df[df['force_name'] == force].copy()
        categories = force_data['book_category'].unique()
        
        for category in categories:
            category_data = force_data[force_data['book_category'] == category].copy()
            logging.debug(f"Processing data for {force}, {category}. Rows: {len(category_data)}")
            
            if len(category_data) == 0:
                continue
            
            # Resample data monthly, summing tonnage
            monthly_data = category_data.resample('MS', on='date').agg({
                'HE_tonnage': 'sum',
                'Incendiary_tonnage': 'sum',
                'Fragmentation_tonnage': 'sum',
                'TOTAL TONS': 'sum'
            }).reset_index()
            
            # Calculate 12-month moving average
            rolling_data = monthly_data.rolling(window=12, min_periods=1, on='date').mean()
            rolling_data['date'] = monthly_data['date']
            rolling_data['force_name'] = force
            rolling_data['category'] = category
            
            results.append(rolling_data)
    
    # Concatenate all rolling data
    if not results:
        logging.warning("No data to plot in temporal analysis")
        return
    combined_stats = pd.concat(results)
    logging.debug("Combined stats DataFrame created.")
    
    # Create the aggregate plot (all categories combined)
    fig, ax1 = plt.subplots(figsize=[15, 10])
    ax2 = ax1.twinx()
    
    # Plot for each force
    for force, color in zip(['RAF', 'USAAF'], ['#1f77b4', '#ff7f0e']):
        force_data = combined_stats[combined_stats['force_name'] == force]
        force_data = force_data.groupby('date').sum().reset_index()
        
        if len(force_data) == 0:
            logging.warning(f"No data available for {force}. Skipping plot.")
            continue
        
        # Plot the lines on first y-axis (proportions)
        total_tonnage = force_data['TOTAL TONS']
        he_proportion = force_data['HE_tonnage'] / total_tonnage
        inc_proportion = force_data['Incendiary_tonnage'] / total_tonnage
        
        ax1.plot(force_data['date'], he_proportion, 
                color=color, linestyle='-', linewidth=2,
                label=f'{force} - HE Proportion (12-month avg)')
        ax1.plot(force_data['date'], inc_proportion, 
                color=color, linestyle='--', linewidth=2,
                label=f'{force} - Incendiary Proportion (12-month avg)')
        
        # Plot total tonnage on second y-axis
        ax2.plot(force_data['date'], total_tonnage,
                color=color, linestyle=':', linewidth=1.5,
                label=f'{force} - Total Tonnage')
    
    # Customize the plot
    ax1.set_xlabel('Date', fontsize=12)
    ax1.set_ylabel('Proportion of Tonnage', fontsize=12)
    ax1.tick_params(axis='y')
    ax1.grid(True, alpha=0.3)
    
    ax2.set_ylabel('Total Tonnage (12-month average)', fontsize=12)
    ax2.tick_params(axis='y')
    
    plt.title('Overall Attack Tonnage Proportions Over Time\n(12-month moving average)', pad=20, fontsize=14)
    
    # Combine legends from both axes
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, bbox_to_anchor=(1.05, 1), loc='upper left')
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(reports_dir / 'overall_temporal_analysis_tonnage.png', bbox_inches='tight', dpi=300)
    plt.close()
    logging.debug("Overall temporal analysis plot saved")
    
    # Create separate plots for each category
    categories = combined_stats['category'].unique()
    for category in categories:
        fig, ax1 = plt.subplots(figsize=[15, 10])
        ax2 = ax1.twinx()
        
        category_data = combined_stats[combined_stats['category'] == category]
        
        # Plot for each force
        for force, color in zip(['RAF', 'USAAF'], ['#1f77b4', '#ff7f0e']):
            force_data = category_data[category_data['force_name'] == force]
            
            if len(force_data) == 0:
                logging.warning(f"No data available for {force} in {category}. Skipping plot.")
                continue
            
            total_tonnage = force_data['TOTAL TONS']
            he_proportion = force_data['HE_tonnage'] / total_tonnage
            inc_proportion = force_data['Incendiary_tonnage'] / total_tonnage
            
            ax1.plot(force_data['date'], he_proportion, 
                    color=color, linestyle='-', linewidth=2,
                    label=f'{force} - HE Proportion (12-month avg)')
            ax1.plot(force_data['date'], inc_proportion, 
                    color=color, linestyle='--', linewidth=2,
                    label=f'{force} - Incendiary Proportion (12-month avg)')
            
            # Plot total tonnage on second y-axis
            ax2.plot(force_data['date'], total_tonnage,
                    color=color, linestyle=':', linewidth=1.5,
                    label=f'{force} - Total Tonnage')
        
        # Customize the plot
        ax1.set_xlabel('Date', fontsize=12)
        ax1.set_ylabel('Proportion of Tonnage', fontsize=12)
        ax1.tick_params(axis='y')
        ax1.grid(True, alpha=0.3)
        
        ax2.set_ylabel('Total Tonnage (12-month average)', fontsize=12)
        ax2.tick_params(axis='y')
        
        plt.title(f'Attack Tonnage Proportions Over Time\nCategory: {category} (12-month moving average)', pad=20, fontsize=14)
        
        # Combine legends from both axes
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, bbox_to_anchor=(1.05, 1), loc='upper left')
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(reports_dir / f'temporal_analysis_tonnage_{category.lower().replace(" ", "_")}.png', bbox_inches='tight', dpi=300)
        plt.close()
        logging.debug(f"Temporal analysis plot saved for {category}")

def create_temporal_contribution_analysis(df):
    """Analyze how each category contributes to the overall HE vs Incendiary tonnage trend, split by air force"""
    logging.debug("Starting temporal contribution analysis")
    
    # Create separate plots for each force
    for force_name in ['RAF', 'USAAF']:
        force_df = df[df['force_name'] == force_name]
        
        # Create monthly stats for each category
        results = []
        date_range = pd.date_range(start='1941-01-01', end='1945-12-01', freq='MS')
        
        for current_date in date_range:
            window_end = current_date
            window_start = current_date - pd.DateOffset(months=11)
            
            # Get data in window
            window_data = force_df[
                (force_df['date'] >= window_start) & 
                (force_df['date'] <= window_end)
            ]
            
            if len(window_data) > 0:
                # Calculate overall tonnage proportions
                total_tonnage = window_data['TOTAL TONS'].sum()
                overall_he = window_data['HE_tonnage'].sum() / total_tonnage
                overall_inc = window_data['Incendiary_tonnage'].sum() / total_tonnage
                
                # Calculate category contributions
                category_stats = window_data.groupby('book_category').agg({
                    'HE_tonnage': 'sum',
                    'Incendiary_tonnage': 'sum',
                    'TOTAL TONS': 'sum'
                }).reset_index()
                
                for _, row in category_stats.iterrows():
                    category_tonnage = row['TOTAL TONS']
                    category_weight = category_tonnage / total_tonnage
                    category_he = row['HE_tonnage'] / category_tonnage if category_tonnage > 0 else 0
                    category_inc = row['Incendiary_tonnage'] / category_tonnage if category_tonnage > 0 else 0
                    
                    results.append({
                        'date': current_date,
                        'category': row['book_category'],
                        'total_tonnage': category_tonnage,
                        'weight': category_weight,
                        'he_contribution': category_weight * category_he,
                        'inc_contribution': category_weight * category_inc,
                        'overall_he': overall_he,
                        'overall_inc': overall_inc
                    })
        
        # Convert to DataFrame
        contribution_stats = pd.DataFrame(results)
        
        if contribution_stats.empty:
            logging.warning(f"No contribution data for {force_name}")
            continue

        # Create stacked area plots
        plt.style.use('dark_background')
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=[15, 15])

        # Define patterns for the stackplot - ensure variety
        patterns = ['xx', '\\\\', '//', '..', 'oo', '++', '**', '--', '||', 'OO', 'XX', '\\O', '/O']
        

        # Plot HE contributions
        he_pivot = contribution_stats.pivot(
            index='date', 
            columns='category', 
            values='he_contribution'
        ).fillna(0)

        # Create stackplot with patterns
        ax1.stackplot(he_pivot.index, he_pivot.T,
                     labels=he_pivot.columns, alpha=0.7,
                     hatch=patterns[:len(he_pivot.columns)])
        ax1.plot(contribution_stats.groupby('date')['overall_he'].first(),
                color='yellow', linestyle='--', label='Overall Proportion',
                linewidth=2)
        ax1.set_title(f'{force_name} Contribution to HE Tonnage Proportion by Category',
                     pad=20, fontsize=14, color='white')
        ax1.set_ylabel('Proportion Contribution', color='white')
        ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left',
                  facecolor='black', edgecolor='white')
        ax1.grid(True, alpha=0.3, color='gray')
        
        # Plot Incendiary contributions
        inc_pivot = contribution_stats.pivot(
            index='date', 
            columns='category', 
            values='inc_contribution'
        ).fillna(0)
        
        # Create stackplot with patterns
        ax2.stackplot(inc_pivot.index, inc_pivot.T,
                     labels=inc_pivot.columns, alpha=0.7,
                     hatch=patterns[:len(inc_pivot.columns)])
        ax2.plot(contribution_stats.groupby('date')['overall_inc'].first(),
                color='yellow', linestyle='--', label='Overall Proportion',
                linewidth=2)
        ax2.set_title(f'{force_name} Contribution to Incendiary Tonnage Proportion by Category',
                     pad=20, fontsize=14, color='white')
        ax2.set_ylabel('Proportion Contribution', color='white')
        ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left',
                  facecolor='black', edgecolor='white')
        ax2.grid(True, alpha=0.3, color='gray')
        
        # Customize both plots
        for ax in [ax1, ax2]:
            ax.set_xlabel('Date', color='white')
            ax.tick_params(colors='white')
            plt.setp(ax.get_xticklabels(), rotation=45)
            # Set spines color to white
            for spine in ax.spines.values():
                spine.set_color('white')
        
        # Set figure background color
        fig.patch.set_facecolor('#1C1C1C')
        for ax in [ax1, ax2]:
            ax.set_facecolor('#2F2F2F')
        
        plt.tight_layout()
        plt.savefig(reports_dir / f'temporal_contribution_analysis_tonnage_{force_name.lower()}.png', 
                    bbox_inches='tight', dpi=300,
                    facecolor='#1C1C1C')
        plt.close()
        logging.debug(f"Temporal contribution analysis plot saved for {force_name}")

        # Save contribution statistics
        with open(reports_dir / f'contribution_analysis_tonnage_{force_name.lower()}.txt', 'w') as f:
            f.write(f"{force_name} Category Contributions to Attack Tonnage Proportions\n")
            f.write("===========================================\n\n")
            
            # Calculate average contributions
            avg_contributions = contribution_stats.groupby('category').agg({
                'weight': 'mean',
                'he_contribution': 'mean',
                'inc_contribution': 'mean'
            }).round(3)
            
            for category in avg_contributions.index:
                f.write(f"\nCategory: {category}\n")
                f.write(f"  Average Tonnage Weight: {avg_contributions.loc[category, 'weight']:.1%}\n")
                f.write(f"  HE Contribution: {avg_contributions.loc[category, 'he_contribution']:.1%}\n")
                f.write(f"  Incendiary Contribution: {avg_contributions.loc[category, 'inc_contribution']:.1%}\n")

def generate_statistics_report(df):
    # Overall statistics
    total_tonnage = df['TOTAL TONS'].sum()
    raf_tonnage = df[df['force_name'] == 'RAF']['TOTAL TONS'].sum()
    usaaf_tonnage = df[df['force_name'] == 'USAAF']['TOTAL TONS'].sum()
    
    # Attack type statistics
    he_total = df['HE_tonnage'].sum()
    incendiary_total = df['Incendiary_tonnage'].sum()
    fragmentation_total = df['Fragmentation_tonnage'].sum()
    
    # Target type statistics
    city_targets_tonnage = df[df['is_city_target']]['TOTAL TONS'].sum()
    industrial_areas_tonnage = df[df['is_industrial_book']]['TOTAL TONS'].sum()
    
    # Create report
    report = f"""
Statistical Analysis Report (Tonnage)
=====================================

Overall Tonnage Statistics:
---------------------------
Total Tonnage Dropped: {total_tonnage:.2f}
RAF Tonnage: {raf_tonnage:.2f} ({raf_tonnage/total_tonnage*100:.1f}%)
USAAF Tonnage: {usaaf_tonnage:.2f} ({usaaf_tonnage/total_tonnage*100:.1f}%)

Attack Type Statistics:
-----------------------
HE Tonnage: {he_total:.2f} ({he_total/total_tonnage*100:.1f}%)
Incendiary Tonnage: {incendiary_total:.2f} ({incendiary_total/total_tonnage*100:.1f}%)
Fragmentation Tonnage: {fragmentation_total:.2f} ({fragmentation_total/total_tonnage*100:.1f}%)

Target Type Statistics:
-----------------------
City Targets Tonnage: {city_targets_tonnage:.2f} ({city_targets_tonnage/total_tonnage*100:.1f}%)
Industrial Areas Tonnage: {industrial_areas_tonnage:.2f} ({industrial_areas_tonnage/total_tonnage*100:.1f}%)

Breakdown by Air Force:
-----------------------
"""
    
    # Add air force specific statistics
    for force in ['RAF', 'USAAF']:
        force_data = df[df['force_name'] == force]
        force_total_tonnage = force_data['TOTAL TONS'].sum()
        
        he_tonnage = force_data['HE_tonnage'].sum()
        incendiary_tonnage = force_data['Incendiary_tonnage'].sum()
        fragmentation_tonnage = force_data['Fragmentation_tonnage'].sum()
        city_tonnage = force_data[force_data['is_city_target']]['TOTAL TONS'].sum()
        industrial_tonnage = force_data[force_data['is_industrial_book']]['TOTAL TONS'].sum()
        
        report += f"\n{force} Statistics:"
        report += f"\n    Total Tonnage: {force_total_tonnage:.2f}"
        report += f"\n    HE Tonnage: {he_tonnage:.2f} ({he_tonnage/force_total_tonnage*100 if force_total_tonnage > 0 else 0:.1f}%)"
        report += f"\n    Incendiary Tonnage: {incendiary_tonnage:.2f} ({incendiary_tonnage/force_total_tonnage*100 if force_total_tonnage > 0 else 0:.1f}%)"
        report += f"\n    Fragmentation Tonnage: {fragmentation_tonnage:.2f} ({fragmentation_tonnage/force_total_tonnage*100 if force_total_tonnage > 0 else 0:.1f}%)"
        report += f"\n    City Targets Tonnage: {city_tonnage:.2f} ({city_tonnage/force_total_tonnage*100 if force_total_tonnage > 0 else 0:.1f}%)"
        report += f"\n    Industrial Areas Tonnage: {industrial_tonnage:.2f} ({industrial_tonnage/force_total_tonnage*100 if force_total_tonnage > 0 else 0:.1f}%)"
    
    # Add yearly tonnage statistics
    report += "\nYearly Tonnage Statistics:\n"
    report += "-----------------------\n"
    
    # Get yearly totals
    yearly_totals = df.groupby('YEAR')['TOTAL TONS'].sum().sort_index()
    yearly_raf = df[df['force_name'] == 'RAF'].groupby('YEAR')['TOTAL TONS'].sum()
    yearly_usaaf = df[df['force_name'] == 'USAAF'].groupby('YEAR')['TOTAL TONS'].sum()
    
    for year in yearly_totals.index:
        total = yearly_totals[year]
        raf = yearly_raf.get(year, 0)
        usaaf = yearly_usaaf.get(year, 0)
        
        report += f"\n{int(year)}:\n"
        report += f"  Total: {int(total):,} tons\n"
        if raf > 0:
            report += f"  RAF: {int(raf):,} tons ({raf/total*100:.1f}%)\n"
        if usaaf > 0:
            report += f"  USAAF: {int(usaaf):,} tons ({usaaf/total*100:.1f}%)\n"
    
    report += "\nBreakdown by Air Force:\n"
    report += "-----------------------\n"

    # Add yearly breakdown by specific air forces
    report += "\n\nDetailed Air Force Breakdown by Year:\n"
    report += "================================\n"
    
    def clean_air_force(af):
        """Clean air force values to standardize format"""
        if pd.isna(af):
            return af
        af_str = str(af).strip().upper()
        if af_str == 'R':
            return 'R'
        try:
            # Convert to integer if it's a number (handles both '8' and '8.0')
            return str(int(float(af_str)))
        except ValueError:
            return af_str

    df = df.copy()
    df['AIR FORCE'] = df['AIR FORCE'].apply(clean_air_force)
    
    # Get unique air forces
    air_forces = df['AIR FORCE'].unique()
    
    # Calculate total tonnage for each air force
    af_total = df.groupby('AIR FORCE')['TOTAL TONS'].sum().sort_values(ascending=False)
    
    # First show overall totals
    report += "\nOverall Totals by Air Force:\n"
    report += "--------------------------\n"
    for af in af_total.index:
        tonnage = af_total[af]
        report += f"Air Force {af}: {tonnage:.2f} tons ({tonnage/total_tonnage*100:.1f}%)\n"
    
    # Then show yearly breakdown
    report += "\nYearly Breakdown by Air Force:\n"
    report += "--------------------------\n"
    
    yearly_af = df.pivot_table(
        values='TOTAL TONS',
        index='AIR FORCE',
        columns='YEAR',
        aggfunc='sum',
        fill_value=0
    ).round(2)
    
    # Add total column
    yearly_af['Total'] = yearly_af.sum(axis=1)
    
    # Sort by total tonnage
    yearly_af = yearly_af.sort_values('Total', ascending=False)
    
    # Format into report
    for af in yearly_af.index:
        report += f"\nAir Force {af}:\n"
        for year in sorted(yearly_af.columns[:-1]):  # Exclude 'Total' column
            tonnage = yearly_af.loc[af, year]
            if tonnage > 0:  # Only show years with activity
                report += f"  {int(year)}: {tonnage:.2f} tons"
                yearly_total = df[df['YEAR'] == year]['TOTAL TONS'].sum()
                if yearly_total > 0:
                    report += f" ({tonnage/yearly_total*100:.1f}% of {int(year)} total)\n"
                else:
                    report += "\n"
        report += f"  Total: {yearly_af.loc[af, 'Total']:.2f} tons\n"
    
    # Add breakdown of bomb types by air force
    report += "\nBomb Type Distribution by Air Force:\n"
    report += "--------------------------------\n"
    
    for af in yearly_af.index:
        af_data = df[df['AIR FORCE'] == af]
        af_total = af_data['TOTAL TONS'].sum()
        if af_total > 0:
            he_tons = af_data['HIGH EXPLOSIVE BOMBS TONS'].sum()
            inc_tons = af_data['INCENDIARY BOMBS TONS'].sum()
            frag_tons = af_data['FRAGMENTATION BOMBS TONS'].sum()
            
            report += f"\nAir Force {af}:\n"
            report += f"  HE: {he_tons:.2f} tons ({he_tons/af_total*100:.1f}%)\n"
            report += f"  Incendiary: {inc_tons:.2f} tons ({inc_tons/af_total*100:.1f}%)\n"
            report += f"  Fragmentation: {frag_tons:.2f} tons ({frag_tons/af_total*100:.1f}%)\n"
    
    # Save report
    with open(reports_dir / 'statistics_report_tonnage.txt', 'w') as f:
        f.write(report)
    
    return report

def main():
    # Load data
    df = load_and_prepare_data('/Users/chim/Working/Thesis/Attack_Images/OCR/PRODUCTION/combined_attack_data_checked.csv')
    df = preprocess_data(df)
    
    # Create visualizations
    create_attack_type_comparison(df)
    create_temporal_analysis(df)
    create_temporal_contribution_analysis(df)
    
    # Generate and print statistics report
    report = generate_statistics_report(df)
    print(report)

if __name__ == "__main__":
    main()
if __name__ == "__main__":
    main()