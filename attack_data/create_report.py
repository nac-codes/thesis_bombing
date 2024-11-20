import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Set style for high quality visualizations
plt.style.use('seaborn-v0_8-dark')
plt.rcParams['figure.dpi'] = 300
plt.rcParams['figure.figsize'] = [12, 8]
plt.rcParams['font.size'] = 12

# Create reports directory if it doesn't exist
reports_dir = Path('reports')
reports_dir.mkdir(exist_ok=True)

def load_and_prepare_data(file_path):
    # Read the data
    df = pd.read_csv(file_path)
    
    # Create RAF indicator
    df['is_RAF'] = df['air_force'].astype(str).str.contains('R', na=False)
    df['force_name'] = df['is_RAF'].map({True: 'RAF', False: 'USAAF'})
    
    # Create attack type indicators
    df['HE_only'] = df['has_he_bombs'] & ~df['has_incendiary_bombs']
    df['incendiary_attack'] = df['has_incendiary_bombs']
    
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
    df['year'] = df['year'].apply(clean_date_field)
    df['month'] = df['month'].apply(clean_date_field)
    df['day'] = df['day'].apply(clean_date_field)
    
    # Drop rows with invalid dates
    df = df.dropna(subset=['year', 'month'])
    logging.debug(f"Dropped rows with invalid dates. Remaining rows: {len(df)}")
    
    # Convert single digit years to full years
    df['year'] = df['year'].apply(lambda x: x + 1940 if x < 10 else x)
    
    # Ensure years and months are valid
    df = df[df['year'].between(1940, 1945)]
    df = df[df['month'].between(1, 12)]
    logging.debug(f"Filtered years and months. Remaining rows: {len(df)}")
    
    # Create date column
    df['date'] = pd.to_datetime({
        'year': df['year'],
        'month': df['month'],
        'day': 1
    })
    
    # Add book category
    df['book_category'] = df['book'].apply(extract_book_category)
    
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

def create_attack_type_comparison(df):
    # Extract book categories
    df['book_category'] = df['book'].apply(extract_book_category)
    
    # Create summary data with air force breakdown
    summary_data = df.groupby('book_category').agg({
        'HE_only': ['count', 'sum'],
        'incendiary_attack': 'sum',
        'force_name': lambda x: (x == 'RAF').sum()  # Count RAF missions
    }).reset_index()
    
    # Get RAF/USAAF specific stats
    raf_stats = df[df['force_name'] == 'RAF'].groupby('book_category').agg({
        'HE_only': 'sum',
        'incendiary_attack': 'sum'
    }).reset_index()
    raf_stats.columns = ['book_category', 'HE_only_RAF', 'incendiary_attack_RAF']
    
    usaaf_stats = df[df['force_name'] == 'USAAF'].groupby('book_category').agg({
        'HE_only': 'sum',
        'incendiary_attack': 'sum'
    }).reset_index()
    usaaf_stats.columns = ['book_category', 'HE_only_USAAF', 'incendiary_attack_USAAF']
    
    # Flatten and merge column names
    summary_data.columns = ['Category', 'Total_Missions', 'HE_Only', 'Incendiary', 'RAF_Missions']
    summary_data['USAAF_Missions'] = summary_data['Total_Missions'] - summary_data['RAF_Missions']
    
    # Merge in RAF/USAAF specific stats
    summary_data = summary_data.merge(
        raf_stats, left_on='Category', right_on='book_category', how='left'
    ).merge(
        usaaf_stats, left_on='Category', right_on='book_category', how='left'
    )
    
    # Drop duplicate columns and fill NAs
    summary_data = summary_data.drop(columns=['book_category_x', 'book_category_y']).fillna(0)
    
    # Sort by total missions
    summary_data = summary_data.sort_values('Total_Missions', ascending=True)
    
    # Create the visualization
    plt.figure(figsize=[15, 10])
    
    # Create the stacked bar chart
    x = range(len(summary_data))
    width = 0.2
    
    # Plot RAF mission types
    plt.barh([i-width for i in x], summary_data['HE_only_RAF'], width, 
            label='RAF - HE Only', color='lightblue')
    plt.barh([i-width for i in x], summary_data['incendiary_attack_RAF'], width,
            left=summary_data['HE_only_RAF'],
            label='RAF - Incendiary', color='blue')
    
    # Plot USAAF mission types
    plt.barh([i for i in x], summary_data['HE_only_USAAF'], width,
            label='USAAF - HE Only', color='lightcoral')
    plt.barh([i for i in x], summary_data['incendiary_attack_USAAF'], width,
            left=summary_data['HE_only_USAAF'],
            label='USAAF - Incendiary', color='red')
    
    # Plot total missions for reference
    plt.barh([i+width for i in x], summary_data['Total_Missions'], width,
            label='Total Missions', color='gray', alpha=0.3)
    
    # Customize the plot
    plt.yticks(x, summary_data['Category'], fontsize=10)
    plt.xlabel('Number of Missions', fontsize=12)
    plt.title('Attack Types by Air Force and Target Category', 
             pad=20, fontsize=14)
    
    # Add legend
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # Add grid
    plt.grid(True, alpha=0.3)
    
    # Adjust layout
    plt.tight_layout()
    
    # Save the plot
    plt.savefig(reports_dir / 'attack_types.png', bbox_inches='tight', dpi=300)
    plt.close()
    
    # Create and save a text summary
    summary_text = "Attack Types by Target Category Summary\n"
    summary_text += "=====================================\n\n"
    
    for _, row in summary_data.iterrows():
        summary_text += f"\nCategory: {row['Category']}\n"
        summary_text += f"  Total Missions: {row['Total_Missions']}\n"
        summary_text += "\n  RAF Statistics:\n"
        summary_text += f"    Missions: {row['RAF_Missions']} ({row['RAF_Missions']/row['Total_Missions']*100:.1f}%)\n"
        summary_text += f"    HE Only: {row['HE_only_RAF']} ({row['HE_only_RAF']/row['RAF_Missions']*100:.1f}% of RAF)\n"
        summary_text += f"    Incendiary: {row['incendiary_attack_RAF']} ({row['incendiary_attack_RAF']/row['RAF_Missions']*100:.1f}% of RAF)\n"
        summary_text += "\n  USAAF Statistics:\n"
        summary_text += f"    Missions: {row['USAAF_Missions']} ({row['USAAF_Missions']/row['Total_Missions']*100:.1f}%)\n"
        if row['USAAF_Missions'] > 0:  # Avoid division by zero
            summary_text += f"    HE Only: {row['HE_only_USAAF']} ({row['HE_only_USAAF']/row['USAAF_Missions']*100:.1f}% of USAAF)\n"
            summary_text += f"    Incendiary: {row['incendiary_attack_USAAF']} ({row['incendiary_attack_USAAF']/row['USAAF_Missions']*100:.1f}% of USAAF)\n"
        else:
            summary_text += "    No USAAF missions\n"
    
    with open(reports_dir / 'attack_types_summary.txt', 'w') as f:
        f.write(summary_text)

def clean_date_field(value):
    # logging.debug(f"Cleaning date field: {value}")
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
        # logging.debug(f"Cleaned date field: {str_val}")
        return int(str_val) if str_val else None
    except ValueError:
        logging.warning(f"Invalid date field: {str_val}")
        return None

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
            
            # Create date range
            date_range = pd.date_range(start='1941-01-01', end='1945-12-01', freq='MS')
            monthly_stats = []
            
            # Calculate 12-month moving average for each month
            for current_date in date_range:
                # Get window end dates
                window_end = current_date
                window_start = current_date - pd.DateOffset(months=11)
                
                # Get data in window
                window_data = category_data[
                    (category_data['date'] >= window_start) & 
                    (category_data['date'] <= window_end)
                ]
                
                if len(window_data) > 0:
                    # Calculate proportions
                    total_attacks = len(window_data)
                    he_only = window_data['HE_only'].sum() / total_attacks
                    incendiary = window_data['incendiary_attack'].sum() / total_attacks
                    
                    monthly_stats.append({
                        'date': current_date,
                        'force_name': force,
                        'category': category,
                        'HE_only': he_only,
                        'incendiary_attack': incendiary,
                        'total_attacks': total_attacks
                    })
            
            if monthly_stats:  # Only extend if we have data
                results.extend(monthly_stats)
    
    # Convert results to DataFrame and ensure we have data
    if not results:
        logging.warning("No data to plot in temporal analysis")
        return
        
    combined_stats = pd.DataFrame(results)
    logging.debug("Combined stats DataFrame created.")

    # First create the aggregate plot (all categories combined)
    fig, ax1 = plt.subplots(figsize=[15, 10])
    ax2 = ax1.twinx()
    
    # Plot for each force
    for force, color in zip(['RAF', 'USAAF'], ['#1f77b4', '#ff7f0e']):
        force_data = combined_stats[combined_stats['force_name'] == force].groupby('date').agg({
            'HE_only': 'mean',
            'incendiary_attack': 'mean',
            'total_attacks': 'sum'
        }).reset_index()
        
        if len(force_data) == 0:
            logging.warning(f"No data available for {force}. Skipping plot.")
            continue
            
        # Plot the lines on first y-axis (proportions)
        ax1.plot(force_data['date'], force_data['HE_only'], 
                color=color, linestyle='-', linewidth=2,
                label=f'{force} - HE Only (12-month avg)')
        ax1.plot(force_data['date'], force_data['incendiary_attack'], 
                color=color, linestyle='--', linewidth=2,
                label=f'{force} - Incendiary (12-month avg)')
        
        # Add markers showing number of attacks
        sizes = force_data['total_attacks'].map(lambda x: min(x/10, 200))
        ax1.scatter(force_data['date'], force_data['HE_only'],
                   s=sizes, color=color, alpha=0.3, marker='o')
        ax1.scatter(force_data['date'], force_data['incendiary_attack'],
                   s=sizes, color=color, alpha=0.3, marker='s')
        
        # Plot mission count trend on second y-axis
        ax2.plot(force_data['date'], force_data['total_attacks'],
                color=color, linestyle=':', linewidth=1.5,
                label=f'{force} - Mission Count')
    
    # Customize the first y-axis (proportions)
    ax1.set_xlabel('Date', fontsize=12)
    ax1.set_ylabel('Proportion of Attacks', fontsize=12)
    ax1.tick_params(axis='y', labelcolor='black')
    ax1.grid(True, alpha=0.3)
    
    # Customize the second y-axis (mission counts)
    ax2.set_ylabel('Number of Missions (12-month window)', fontsize=12)
    ax2.tick_params(axis='y', labelcolor='gray')
    
    # Title for aggregate plot
    plt.title('Overall Attack Types Over Time\n(12-month moving average, marker size indicates number of attacks)', 
             pad=20, fontsize=14)
    
    # Combine legends from both axes
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, 
              bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
    
    # Rotate x-axis labels
    plt.xticks(rotation=45)
    
    # Adjust layout to prevent label cutoff
    plt.tight_layout()
    
    # Save the aggregate plot
    plt.savefig(reports_dir / 'overall_temporal_analysis.png', bbox_inches='tight', dpi=300)
    plt.close()
    logging.debug("Overall temporal analysis plot saved")

    # Create separate plots for each category
    categories = combined_stats['category'].unique()
    for category in categories:
        # Create figure with two y-axes
        fig, ax1 = plt.subplots(figsize=[15, 10])
        ax2 = ax1.twinx()
        
        category_data = combined_stats[combined_stats['category'] == category]
        
        # Plot for each force
        for force, color in zip(['RAF', 'USAAF'], ['#1f77b4', '#ff7f0e']):
            force_data = category_data[category_data['force_name'] == force]
            
            if len(force_data) == 0:
                logging.warning(f"No data available for {force} in {category}. Skipping plot.")
                continue
                
            # Plot the lines on first y-axis (proportions)
            ax1.plot(force_data['date'], force_data['HE_only'], 
                    color=color, linestyle='-', linewidth=2,
                    label=f'{force} - HE Only (12-month avg)')
            ax1.plot(force_data['date'], force_data['incendiary_attack'], 
                    color=color, linestyle='--', linewidth=2,
                    label=f'{force} - Incendiary (12-month avg)')
            
            # Add markers showing number of attacks
            sizes = force_data['total_attacks'].map(lambda x: min(x/10, 200))
            ax1.scatter(force_data['date'], force_data['HE_only'],
                       s=sizes, color=color, alpha=0.3, marker='o')
            ax1.scatter(force_data['date'], force_data['incendiary_attack'],
                       s=sizes, color=color, alpha=0.3, marker='s')
            
            # Plot mission count trend on second y-axis
            ax2.plot(force_data['date'], force_data['total_attacks'],
                    color=color, linestyle=':', linewidth=1.5,
                    label=f'{force} - Mission Count')
        
        # Customize the first y-axis (proportions)
        ax1.set_xlabel('Date', fontsize=12)
        ax1.set_ylabel('Proportion of Attacks', fontsize=12)
        ax1.tick_params(axis='y', labelcolor='black')
        ax1.grid(True, alpha=0.3)
        
        # Customize the second y-axis (mission counts)
        ax2.set_ylabel('Number of Missions (100-day window)', fontsize=12)
        ax2.tick_params(axis='y', labelcolor='gray')
        
        # Title
        plt.title(f'Attack Types Over Time for {category}\n(12-month moving average, marker size indicates number of attacks)', 
                 pad=20, fontsize=14)
        
        # Combine legends from both axes
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, 
                  bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
        
        # Rotate x-axis labels
        plt.xticks(rotation=45)
        
        # Adjust layout to prevent label cutoff
        plt.tight_layout()
        
        # Save the plot
        plt.savefig(reports_dir / f'temporal_analysis_{category.lower().replace(" ", "_")}.png', 
                   bbox_inches='tight', dpi=300)
        plt.close()
        logging.debug(f"Temporal analysis plot saved for {category}")

def create_temporal_contribution_analysis(df):
    """Analyze how each category contributes to the overall HE vs Incendiary trend, split by air force"""
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
                # Calculate overall proportions
                total_missions = len(window_data)
                overall_he = window_data['HE_only'].sum() / total_missions
                overall_inc = window_data['incendiary_attack'].sum() / total_missions
                
                # Calculate category contributions
                category_stats = window_data.groupby('book_category').agg({
                    'HE_only': ['count', 'sum'],
                    'incendiary_attack': 'sum'
                })
                
                # Fix column names after aggregation
                category_stats.columns = ['missions', 'he_total', 'inc_total']
                category_stats = category_stats.reset_index()
                
                for _, row in category_stats.iterrows():
                    category_missions = row['missions']
                    category_weight = category_missions / total_missions
                    category_he = row['he_total'] / category_missions
                    category_inc = row['inc_total'] / category_missions
                    
                    results.append({
                        'date': current_date,
                        'category': row['book_category'],
                        'missions': category_missions,
                        'weight': category_weight,
                        'he_contribution': category_weight * category_he,
                        'inc_contribution': category_weight * category_inc,
                        'overall_he': overall_he,
                        'overall_inc': overall_inc
                    })
        
        # Convert to DataFrame
        contribution_stats = pd.DataFrame(results)
        
                # Create stacked area plots with dark theme
        plt.style.use('dark_background')
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=[15, 15])
        
        # Define patterns for the stackplot
        patterns = ['//', '\\\\', 'xx', '..', 'oo', '++', '**', '--', '||']
        
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
        ax1.set_title(f'{force_name} Contribution to HE-Only Attack Proportion by Category',
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
        ax2.set_title(f'{force_name} Contribution to Incendiary Attack Proportion by Category',
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
        plt.savefig(reports_dir / f'temporal_contribution_analysis_{force_name.lower()}.png', 
                    bbox_inches='tight', dpi=300,
                    facecolor='#1C1C1C')
        plt.close()
        
        # Save contribution statistics
        with open(reports_dir / f'contribution_analysis_{force_name.lower()}.txt', 'w') as f:
            f.write(f"{force_name} Category Contributions to Attack Type Proportions\n")
            f.write("=============================================\n\n")
            
            # Calculate average contributions
            avg_contributions = contribution_stats.groupby('category').agg({
                'weight': 'mean',
                'he_contribution': 'mean',
                'inc_contribution': 'mean'
            }).round(3)
            
            for category in avg_contributions.index:
                f.write(f"\nCategory: {category}\n")
                f.write(f"  Average Mission Weight: {avg_contributions.loc[category, 'weight']:.1%}\n")
                f.write(f"  HE Contribution: {avg_contributions.loc[category, 'he_contribution']:.1%}\n")
                f.write(f"  Incendiary Contribution: {avg_contributions.loc[category, 'inc_contribution']:.1%}\n")

def generate_statistics_report(df):
    # Overall statistics
    total_missions = len(df)
    raf_missions = df['is_RAF'].sum()
    usaaf_missions = (~df['is_RAF']).sum()
    
    # Attack type statistics
    he_only_total = df['HE_only'].sum()
    incendiary_total = df['incendiary_attack'].sum()
    
    # Target type statistics
    city_targets = df['is_city_target'].sum()
    industrial_areas = df['is_industrial_book'].sum()
    
    # Create report
    report = f"""
    Statistical Analysis Report
    =========================

    Overall Mission Statistics:
    -------------------------
    Total Missions: {total_missions}
    RAF Missions: {raf_missions} ({raf_missions/total_missions*100:.1f}%)
    USAAF Missions: {usaaf_missions} ({usaaf_missions/total_missions*100:.1f}%)

    Attack Type Statistics:
    ---------------------
    HE Only Attacks: {he_only_total} ({he_only_total/total_missions*100:.1f}%)
    Incendiary Attacks: {incendiary_total} ({incendiary_total/total_missions*100:.1f}%)

    Target Type Statistics:
    ---------------------
    City Targets: {city_targets} ({city_targets/total_missions*100:.1f}%)
    Industrial Areas: {industrial_areas} ({industrial_areas/total_missions*100:.1f}%)

    Breakdown by Air Force:
    ---------------------
    """
    
    # Add air force specific statistics
    for force in ['RAF', 'USAAF']:
        force_data = df[df['force_name'] == force]
        force_total = len(force_data)
        
        report += f"\n{force} Statistics:"
        report += f"\n    Total Missions: {force_total}"
        report += f"\n    HE Only: {force_data['HE_only'].sum()} ({force_data['HE_only'].sum()/force_total*100:.1f}%)"
        report += f"\n    Incendiary: {force_data['incendiary_attack'].sum()} ({force_data['incendiary_attack'].sum()/force_total*100:.1f}%)"
        report += f"\n    City Targets: {force_data['is_city_target'].sum()} ({force_data['is_city_target'].sum()/force_total*100:.1f}%)"
        report += f"\n    Industrial Areas: {force_data['is_industrial_book'].sum()} ({force_data['is_industrial_book'].sum()/force_total*100:.1f}%)"
    
    # Save report
    with open(reports_dir / 'statistics_report.txt', 'w') as f:
        f.write(report)
    
    return report

def main():
    # Load data
    df = load_and_prepare_data('combined_attack_data.csv')
    df = preprocess_data(df)
    
    # Create visualizations
    create_attack_type_comparison(df)    
    # create_temporal_analysis(df)
    create_temporal_contribution_analysis(df)
    # Generate and print statistics report
    report = generate_statistics_report(df)
    print(report)

if __name__ == "__main__":
    main()