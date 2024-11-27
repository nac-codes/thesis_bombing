import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import logging
import numpy as np
from tqdm import tqdm

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Set style for high-quality visualizations
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.dpi'] = 300
plt.rcParams['figure.figsize'] = [12, 8]
plt.rcParams['font.size'] = 12

# Create reports directory if it doesn't exist
reports_dir = Path('reports_3/')
reports_dir.mkdir(exist_ok=True, parents=True)

def load_and_prepare_data(file_path):
    logging.info("Loading data...")
    df = pd.read_csv(file_path, low_memory=False)

    # Ensure datetime column is properly formatted
    df['DATETIME'] = pd.to_datetime(df['DATETIME'])
    df['date'] = df['DATETIME'].dt.date
    df['date'] = pd.to_datetime(df['date'])

    df['YEAR'] = df['DATETIME'].dt.year

    # Create RAF indicator
    df['is_RAF'] = df['AIR FORCE'].astype(str).str.contains('R', na=False)
    df['force_name'] = df['is_RAF'].map({True: 'RAF', False: 'USAAF'})

    # Extract book category
    df['book_category'] = df['book'].apply(extract_book_category)

    # Update mission category - combine area bombing types
    df['mission_category'] = df['bombing_type']

    logging.info(f"Data loaded with {len(df)} records.")

    return df

def extract_book_category(book_name):
    """Extract category from book name format."""
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
    logging.info("Creating attack type comparison charts...")

    plt.style.use('dark_background')

    output_dir = reports_dir / 'attack_type_comparison'
    output_dir.mkdir(exist_ok=True, parents=True)

    # Group by mission category and force name, summing tonnage
    summary_data = df.groupby(['mission_category', 'force_name']).agg({
        'TOTAL TONS': 'sum'
    }).reset_index()

    # Pivot the data to get force names as columns
    pivot_data = summary_data.pivot(index='mission_category', columns='force_name', values='TOTAL TONS').fillna(0)
    pivot_data = pivot_data.reset_index()

    # Sort mission categories
    pivot_data['mission_category'] = pd.Categorical(pivot_data['mission_category'],
                                                    categories=['precision', 'area'],
                                                    ordered=True)
    pivot_data = pivot_data.sort_values('mission_category')

    # Plot the data
    pivot_data.set_index('mission_category', inplace=True)
    ax = pivot_data.plot(kind='bar', stacked=True, figsize=(12, 8), color=['#1f77b4', '#ff7f0e'])

    plt.xlabel('Mission Category')
    plt.ylabel('Total Tonnage')
    plt.title('Attack Types by Air Force and Mission Category (Total Tonnage)', pad=20)
    plt.xticks(rotation=0)
    plt.legend(title='Air Force')
    plt.tight_layout()

    # Save the plot
    plt.savefig(output_dir / 'attack_types_by_mission_category.png', bbox_inches='tight', dpi=300)
    plt.close()

    logging.info("Attack type comparison charts created and saved.")

def create_trends_by_industry(df):
    logging.info("Creating trends by industry and bombing type...")

    output_dir = reports_dir / 'trends_by_industry'
    output_dir.mkdir(exist_ok=True, parents=True)

    # Set dark style
    plt.style.use('dark_background')

    # Define colors for mission categories - more muted/sophisticated palette
    colors = {
        'precision': '#5c7d9a',  # Muted blue-gray
        'area': '#a65d57'        # Muted burgundy
    }

    # Group by date, bombing type, industry, and force, summing tonnage
    df['month'] = df['date'].dt.to_period('M').dt.to_timestamp()
    group_cols = ['month', 'book_category', 'mission_category', 'force_name']
    summary = df.groupby(group_cols).agg({'TOTAL TONS': 'sum'}).reset_index()

    # Create time series plots for each industry and air force
    industries = summary['book_category'].unique()
    forces = ['RAF', 'USAAF']

    for industry in industries:
        # Create overall plot for this industry
        industry_data = summary[summary['book_category'] == industry]
        
        # Pivot the data for rolling average calculation
        pivot_data = industry_data.pivot_table(
            index='month',
            columns='mission_category',
            values='TOTAL TONS',
            aggfunc='sum'
        ).fillna(0)
        
        # Calculate 12-month moving average
        rolling_data = pivot_data.rolling(window=12, min_periods=1).mean()
        
        # Plot both raw data and moving average
        plt.figure(figsize=(14, 8))
        
        # Plot raw data with higher alpha and actual points
        for mission_type in industry_data['mission_category'].unique():
            mission_data = industry_data[industry_data['mission_category'] == mission_type]
            plt.plot(mission_data['month'], mission_data['TOTAL TONS'], 
                     alpha=0.7, color=colors[mission_type], linewidth=1, marker='o', markersize=4)
        
        # Plot moving averages
        for column in rolling_data.columns:
            plt.plot(rolling_data.index, rolling_data[column], 
                     label=f'{column} (12-month avg)', linewidth=3,
                     color=colors[column])
        
        plt.title(f'Total Tonnage over Time by Bombing Type - {industry} (All Forces)\n12-Month Moving Average', 
                 pad=20)
        plt.xlabel('Month')
        plt.ylabel('Total Tonnage')
        plt.legend(title='Mission Category')
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.2)
        plt.tight_layout()
        filename = f'trend_{industry.lower().replace(" ", "_")}_all.png'
        plt.savefig(output_dir / filename, bbox_inches='tight', dpi=300, facecolor='black', edgecolor='none')
        plt.close()

        # Create separate plots for each air force
        for force in forces:
            force_data = industry_data[industry_data['force_name'] == force]
            
            if len(force_data) > 0:  # Only create plot if there's data for this force
                # Pivot the data for rolling average calculation
                pivot_force = force_data.pivot_table(
                    index='month',
                    columns='mission_category',
                    values='TOTAL TONS',
                    aggfunc='sum'
                ).fillna(0)
                
                # Calculate 12-month moving average
                rolling_force = pivot_force.rolling(window=12, min_periods=1).mean()
                
                plt.figure(figsize=(14, 8))
                
                # Plot raw data with higher alpha and actual points
                for mission_type in force_data['mission_category'].unique():
                    mission_data = force_data[force_data['mission_category'] == mission_type]
                    plt.plot(mission_data['month'], mission_data['TOTAL TONS'], 
                             alpha=0.7, color=colors[mission_type], linewidth=1, marker='o', markersize=4)
                
                # Plot moving averages
                for column in rolling_force.columns:
                    plt.plot(rolling_force.index, rolling_force[column], 
                             label=f'{column} (12-month avg)', linewidth=3,
                             color=colors[column])
                
                plt.title(f'Total Tonnage over Time by Bombing Type - {industry} ({force})\n12-Month Moving Average', 
                         pad=20)
                plt.xlabel('Month')
                plt.ylabel('Total Tonnage')
                plt.legend(title='Mission Category')
                plt.xticks(rotation=45)
                plt.grid(True, alpha=0.2)
                plt.tight_layout()
                
                filename = f'trend_{industry.lower().replace(" ", "_")}_{force.lower()}.png'
                plt.savefig(output_dir / filename, bbox_inches='tight', dpi=300, facecolor='black', edgecolor='none')
                plt.close()

    logging.info("Trends by industry and bombing type created and saved.")

def create_industry_contribution_analysis(df):
    """Analyze bombing type proportions by industry for each air force"""
    logging.info("Starting industry contribution analysis...")
    
    output_dir = reports_dir / 'industry_contribution'
    output_dir.mkdir(exist_ok=True, parents=True)

    # Define consistent colors and patterns
    colors = {
        'precision': '#2ecc71',  # Green
        'area': '#e74c3c'        # Red
    }
    
    patterns = ['xx', '\\\\', '//', '..', 'oo', '++', '**', '--', '||', 'OO', 'XX', '\\O', '/O']
    
    # Create separate plots for each force
    for force_name in ['RAF', 'USAAF']:
        force_df = df[df['force_name'] == force_name].copy()
        
        # Create monthly stats for each category
        results = []
        date_range = pd.date_range(start='1942-01-01', end='1945-12-01', freq='MS')
        
        for current_date in date_range:
            window_end = current_date
            window_start = current_date - pd.DateOffset(months=11)
            
            # Get data in window
            window_data = force_df[
                (force_df['date'] >= window_start) & 
                (force_df['date'] <= window_end)
            ]
            
            if len(window_data) > 0:
                # Calculate overall tonnage
                total_tonnage = window_data['TOTAL TONS'].sum()
                
                # Calculate category contributions
                for category in window_data['book_category'].unique():
                    category_data = window_data[window_data['book_category'] == category]
                    category_tonnage = category_data['TOTAL TONS'].sum()
                    category_weight = category_tonnage / total_tonnage
                    
                    if category_tonnage > 0:
                        # Calculate proportions for each mission type
                        mission_tons = category_data.groupby('mission_category')['TOTAL TONS'].sum()
                        
                        results.append({
                            'date': current_date,
                            'category': category,
                            'precision_contrib': (mission_tons.get('precision', 0) / category_tonnage) * category_weight,
                            'area_contrib': (mission_tons.get('area', 0) / category_tonnage) * category_weight
                        })
        
        # Convert to DataFrame and create plots
        contribution_stats = pd.DataFrame(results)
        
        if contribution_stats.empty:
            logging.warning(f"No contribution data for {force_name}")
            continue

        plt.style.use('dark_background')
        
        # Create two-category plot (Precision vs Area)
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=[15, 15])
        
        # 1. Precision contributions
        precision_pivot = contribution_stats.pivot(
            index='date',
            columns='category',
            values='precision_contrib'
        ).fillna(0)
        
        ax1.stackplot(precision_pivot.index, precision_pivot.T,
                     labels=precision_pivot.columns, alpha=0.7,
                     hatch=patterns[:len(precision_pivot.columns)])
        ax1.set_title(f'{force_name} Industry Contributions to Precision Bombing',
                     pad=20, fontsize=14, color='white')
        
        # 2. Area contributions
        area_pivot = contribution_stats.pivot(
            index='date',
            columns='category',
            values='area_contrib'
        ).fillna(0)
        
        ax2.stackplot(area_pivot.index, area_pivot.T,
                     labels=area_pivot.columns, alpha=0.7,
                     hatch=patterns[:len(area_pivot.columns)])
        ax2.set_title(f'{force_name} Industry Contributions to Area Bombing',
                     pad=20, fontsize=14, color='white')
        
        # Customize both plots
        for ax in [ax1, ax2]:
            ax.set_xlabel('Date', color='white')
            ax.set_ylabel('Proportion Contribution', color='white')
            ax.tick_params(colors='white')
            ax.grid(True, alpha=0.3, color='gray')
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left',
                     facecolor='black', edgecolor='white')
            plt.setp(ax.get_xticklabels(), rotation=45)
            for spine in ax.spines.values():
                spine.set_color('white')
        
        # Set figure background color
        fig.patch.set_facecolor('#1C1C1C')
        for ax in [ax1, ax2]:
            ax.set_facecolor('#2F2F2F')
        
        plt.tight_layout()
        plt.savefig(output_dir / f'industry_contribution_{force_name.lower()}.png',
                    bbox_inches='tight', dpi=300, facecolor='#1C1C1C')
        plt.close()
        
        logging.info(f"Industry contribution analysis completed for {force_name}")

def create_summary_statistics(df):
    logging.info("Creating summary statistics...")

    output_dir = reports_dir / 'summary_statistics'
    output_dir.mkdir(exist_ok=True, parents=True)

    # Overall statistics
    total_tonnage = df['TOTAL TONS'].sum()
    precision_tonnage = df[df['mission_category'] == 'precision']['TOTAL TONS'].sum()
    area_tonnage = df[df['mission_category'] == 'area']['TOTAL TONS'].sum()

    report = f"""
Summary Statistics Report
=========================

Total Tonnage Dropped: {total_tonnage:.2f}

By Mission Category:
--------------------
Precision Bombing Tonnage: {precision_tonnage:.2f} ({precision_tonnage/total_tonnage*100:.1f}%)
Area Bombing Tonnage: {area_tonnage:.2f} ({area_tonnage/total_tonnage*100:.1f}%)

By Air Force:
-------------
"""

    # Statistics by air force
    for force in ['RAF', 'USAAF']:
        force_data = df[df['force_name'] == force]
        force_tonnage = force_data['TOTAL TONS'].sum()
        force_precision_tonnage = force_data[force_data['mission_category'] == 'precision']['TOTAL TONS'].sum()
        force_area_tonnage = force_data[force_data['mission_category'] == 'area']['TOTAL TONS'].sum()

        report += f"""
{force}:
  Total Tonnage: {force_tonnage:.2f} ({force_tonnage/total_tonnage*100:.1f}%)
  Precision Bombing Tonnage: {force_precision_tonnage:.2f} ({force_precision_tonnage/force_tonnage*100:.1f}%)
  Area Bombing Tonnage: {force_area_tonnage:.2f} ({force_area_tonnage/force_tonnage*100:.1f}%)
"""

    # Save the report
    with open(output_dir / 'summary_statistics.txt', 'w') as f:
        f.write(report)

    logging.info("Summary statistics report created and saved.")

def create_overall_trends(df):
    logging.info("Creating overall trends by bombing type...")

    output_dir = reports_dir / 'overall_trends'
    output_dir.mkdir(exist_ok=True, parents=True)

    # Group by month
    df['month'] = df['date'].dt.to_period('M').dt.to_timestamp()
    
    # Create monthly summaries with complete date range
    date_range = pd.date_range(start=df['month'].min(), end=df['month'].max(), freq='MS')
    
    # Create and reindex the data to ensure same length
    precision_data = df[df['mission_category'] == 'precision'].groupby('month')['TOTAL TONS'].sum()
    area_data = df[df['mission_category'] == 'area'].groupby('month')['TOTAL TONS'].sum()
    
    # Reindex both series to have the same date range, filling missing values with 0
    precision_data = precision_data.reindex(date_range, fill_value=0)
    area_data = area_data.reindex(date_range, fill_value=0)
        
    plt.style.use('dark_background')

    # Create figure
    plt.figure(figsize=(14, 8))
    
    # Create stacked area plot
    plt.stackplot(date_range, 
                 precision_data.values,
                 area_data.values,
                 labels=['Precision', 'Area'])

    plt.title('Total Tonnage Over Time by Bombing Type', pad=20)
    plt.xlabel('Month')
    plt.ylabel('Total Tonnage')
    plt.legend(title='Mission Category')
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Save the plot
    plt.savefig(output_dir / 'overall_trends_by_bombing_type.png', bbox_inches='tight', dpi=300)
    plt.close()

    logging.info("Overall trends by bombing type created and saved.")

def analyze_area_bombing_composition(df):
    """Analyze the composition of area bombing between HE and incendiary bombs by industry"""
    logging.info("Starting area bombing composition analysis...")
    
    output_dir = reports_dir / 'area_bombing_composition'
    output_dir.mkdir(exist_ok=True, parents=True)

    # Filter for area bombing only
    area_df = df[df['mission_category'] == 'area'].copy()
    
    # Create monthly stats for each category
    results = []
    date_range = pd.date_range(start='1942-01-01', end='1945-12-01', freq='MS')
    
    for current_date in date_range:
        window_end = current_date
        window_start = current_date - pd.DateOffset(months=11)
        
        # Get data in window
        window_data = area_df[
            (area_df['date'] >= window_start) & 
            (area_df['date'] <= window_end)
        ]
        
        if len(window_data) > 0:
            # Calculate overall tonnage for the window
            total_window_tonnage = window_data['TOTAL TONS'].sum()
            
            # Calculate category contributions
            for category in window_data['book_category'].unique():
                category_data = window_data[window_data['book_category'] == category]
                category_tonnage = category_data['TOTAL TONS'].sum()
                category_weight = category_tonnage / total_window_tonnage
                
                if category_tonnage > 0:
                    # Calculate proportions for HE and incendiary
                    he_tons = category_data['HIGH EXPLOSIVE BOMBS TONS'].sum()
                    inc_tons = category_data['INCENDIARY BOMBS TONS'].sum()
                    
                    # Calculate weighted contributions
                    results.append({
                        'date': current_date,
                        'category': category,
                        'he_contrib': (he_tons / category_tonnage) * category_weight,
                        'inc_contrib': (inc_tons / category_tonnage) * category_weight
                    })
    
    # Convert to DataFrame
    composition_stats = pd.DataFrame(results)
    
    if not composition_stats.empty:
        plt.style.use('dark_background')
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=[15, 15])
        
        # Define patterns for visual distinction
        patterns = ['xx', '\\\\', '//', '..', 'oo', '++', '**', '--', '||', 'OO', 'XX', '\\O', '/O']
        
        # 1. HE Bombs contributions
        he_pivot = composition_stats.pivot(
            index='date',
            columns='category',
            values='he_contrib'
        ).fillna(0)
        
        ax1.stackplot(he_pivot.index, he_pivot.T,
                     labels=he_pivot.columns, alpha=0.7,
                     hatch=patterns[:len(he_pivot.columns)])
        ax1.set_title('Industry Contributions to Area Bombing (High Explosive)',
                     pad=20, fontsize=14, color='white')
        
        # 2. Incendiary contributions
        inc_pivot = composition_stats.pivot(
            index='date',
            columns='category',
            values='inc_contrib'
        ).fillna(0)
        
        ax2.stackplot(inc_pivot.index, inc_pivot.T,
                     labels=inc_pivot.columns, alpha=0.7,
                     hatch=patterns[:len(inc_pivot.columns)])
        ax2.set_title('Industry Contributions to Area Bombing (Incendiary)',
                     pad=20, fontsize=14, color='white')
        
        # Customize both plots
        for ax in [ax1, ax2]:
            ax.set_xlabel('Date', color='white')
            ax.set_ylabel('Proportion Contribution', color='white')
            ax.tick_params(colors='white')
            ax.grid(True, alpha=0.3, color='gray')
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left',
                     facecolor='black', edgecolor='white')
            plt.setp(ax.get_xticklabels(), rotation=45)
            for spine in ax.spines.values():
                spine.set_color('white')
        
        # Set figure background color
        fig.patch.set_facecolor('#1C1C1C')
        for ax in [ax1, ax2]:
            ax.set_facecolor('#2F2F2F')
        
        plt.tight_layout()
        plt.savefig(output_dir / 'area_bombing_composition.png',
                    bbox_inches='tight', dpi=300, facecolor='#1C1C1C')
        plt.close()
        
        logging.info("Area bombing composition analysis completed")

def create_top_missions_report(df):
    """Create CSV reports for each industry showing top 100 missions by bombing type, separated by air force."""
    logging.info("Creating top missions reports by industry...")
    
    output_dir = reports_dir / 'top_missions'
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Group missions by combining Box, Book, Image and date (within same day)
    df['date'] = df['DATETIME'].dt.date
    df['mission_id'] = df['box'] + '_' + df['book'] + '_' + df['image'] + '_' + df['date'].astype(str)
    
    # Create RAF indicator
    df['is_RAF'] = df['AIR FORCE'].astype(str).str.contains('R', na=False)
    df['force_name'] = df['is_RAF'].map({True: 'RAF', False: 'USAAF'})
    
    # Process each industry
    for industry in df['book_category'].unique():
        industry_df = df[df['book_category'] == industry]
        
        # Process for each air force
        for force in ['RAF', 'USAAF']:
            force_df = industry_df[industry_df['force_name'] == force]
            
            # Area Bombing Section
            area_missions = force_df[force_df['mission_category'] == 'area'].groupby(['mission_id', 'date']).agg({
                'DATETIME': 'first',
                'target_name': 'first',
                'target_location': 'first',
                'HIGH EXPLOSIVE BOMBS TONS': 'sum',
                'INCENDIARY BOMBS TONS': 'sum',
                'TOTAL TONS': 'sum',
                'NUMBER OF AIRCRAFT BOMBING': 'sum'
            }).reset_index()
            
            if len(area_missions) > 0:
                area_missions['total_area_tons'] = (area_missions['HIGH EXPLOSIVE BOMBS TONS'] + 
                                                  area_missions['INCENDIARY BOMBS TONS'])
                area_missions['mission_type'] = 'area'
                area_missions['he_percentage'] = (area_missions['HIGH EXPLOSIVE BOMBS TONS'] / 
                                                area_missions['total_area_tons'] * 100)
                area_missions['inc_percentage'] = (area_missions['INCENDIARY BOMBS TONS'] / 
                                                 area_missions['total_area_tons'] * 100)
                
                # Sort and get top 100
                top_area = area_missions.nlargest(100, 'total_area_tons')
                
                # Save to CSV
                csv_path = output_dir / f'top_missions_{industry.lower().replace(" ", "_")}_{force.lower()}_area.csv'
                top_area.to_csv(csv_path, index=False, columns=[
                    'DATETIME', 'mission_id', 'target_name', 'target_location',
                    'NUMBER OF AIRCRAFT BOMBING', 'total_area_tons',
                    'HIGH EXPLOSIVE BOMBS TONS', 'he_percentage',
                    'INCENDIARY BOMBS TONS', 'inc_percentage'
                ])
            
            # Precision Bombing Section
            precision_missions = force_df[force_df['mission_category'] == 'precision'].groupby(['mission_id', 'date']).agg({
                'DATETIME': 'first',
                'target_name': 'first',
                'target_location': 'first',
                'TOTAL TONS': 'sum',
                'NUMBER OF AIRCRAFT BOMBING': 'sum'
            }).reset_index()
            
            if len(precision_missions) > 0:
                precision_missions['mission_type'] = 'precision'
                
                # Sort and get top 100
                top_precision = precision_missions.nlargest(100, 'TOTAL TONS')
                
                # Save to CSV
                csv_path = output_dir / f'top_missions_{industry.lower().replace(" ", "_")}_{force.lower()}_precision.csv'
                top_precision.to_csv(csv_path, index=False, columns=[
                    'DATETIME', 'mission_id', 'target_name', 'target_location',
                    'NUMBER OF AIRCRAFT BOMBING', 'TOTAL TONS'
                ])
    
    logging.info("Top missions CSV reports created for all industries")

def create_summary_statistics_detailed(df):
    """Create comprehensive statistics report for bombing operations."""
    logging.info("Creating summary statistics report...")
    
    output_dir = reports_dir / 'summary_statistics'
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Overall statistics
    total_tonnage = df['TOTAL TONS'].sum()
    
    # Create RAF indicator
    df['is_RAF'] = df['AIR FORCE'].astype(str).str.contains('R', na=False)
    df['force_name'] = df['is_RAF'].map({True: 'RAF', False: 'USAAF'})
    
    # Force statistics
    raf_tonnage = df[df['force_name'] == 'RAF']['TOTAL TONS'].sum()
    usaaf_tonnage = df[df['force_name'] == 'USAAF']['TOTAL TONS'].sum()
    
    # Mission type statistics
    area_tonnage = df[df['mission_category'] == 'area']['TOTAL TONS'].sum()
    precision_tonnage = df[df['mission_category'] == 'precision']['TOTAL TONS'].sum()
    
    report = f"""
Strategic Bombing Statistical Analysis
====================================

Overall Tonnage Statistics:
--------------------------
Total Tonnage Dropped: {total_tonnage:,.2f}
RAF Tonnage: {raf_tonnage:,.2f} ({raf_tonnage/total_tonnage*100:.1f}%)
USAAF Tonnage: {usaaf_tonnage:,.2f} ({usaaf_tonnage/total_tonnage*100:.1f}%)

Mission Type Statistics:
----------------------
Area Bombing Tonnage: {area_tonnage:,.2f} ({area_tonnage/total_tonnage*100:.1f}%)
Precision Bombing Tonnage: {precision_tonnage:,.2f} ({precision_tonnage/total_tonnage*100:.1f}%)

Breakdown by Air Force and Mission Type:
-------------------------------------"""

    # Process each force
    for force in ['RAF', 'USAAF']:
        force_data = df[df['force_name'] == force]
        force_tonnage = force_data['TOTAL TONS'].sum()
        
        # Get mission type data
        force_area_tonnage = force_data[force_data['mission_category'] == 'area']['TOTAL TONS'].sum()
        force_precision_tonnage = force_data[force_data['mission_category'] == 'precision']['TOTAL TONS'].sum()
        
        # Area bombing composition
        area_data = force_data[force_data['mission_category'] == 'area']
        area_he_tons = area_data['HIGH EXPLOSIVE BOMBS TONS'].sum()
        area_inc_tons = area_data['INCENDIARY BOMBS TONS'].sum()
        
        report += f"""

{force}:
  Total Tonnage: {force_tonnage:,.2f} ({force_tonnage/total_tonnage*100:.1f}%)
  Area Bombing: {force_area_tonnage:,.2f} ({force_area_tonnage/force_tonnage*100:.1f}%)
    - HE Bombs: {area_he_tons:,.2f} ({area_he_tons/force_area_tonnage*100:.1f}% of area)
    - Incendiary Bombs: {area_inc_tons:,.2f} ({area_inc_tons/force_area_tonnage*100:.1f}% of area)
  Precision Bombing: {force_precision_tonnage:,.2f} ({force_precision_tonnage/force_tonnage*100:.1f}%)"""

    # Add yearly statistics
    report += """

Yearly Statistics:
----------------"""

    yearly_stats = df.groupby(['YEAR', 'force_name', 'mission_category']).agg({
        'TOTAL TONS': 'sum',
        'HIGH EXPLOSIVE BOMBS TONS': 'sum',
        'INCENDIARY BOMBS TONS': 'sum'
    }).round(2)

    for year in sorted(df['YEAR'].unique()):
        year_data = df[df['YEAR'] == year]
        year_total = year_data['TOTAL TONS'].sum()
        
        report += f"\n\n{int(year)}:"
        report += f"\n  Total Tonnage: {year_total:,.2f}"
        
        for force in ['RAF', 'USAAF']:
            force_year_data = year_data[year_data['force_name'] == force]
            force_year_total = force_year_data['TOTAL TONS'].sum()
            
            if force_year_total > 0:
                report += f"\n  {force}: {force_year_total:,.2f} ({force_year_total/year_total*100:.1f}%)"
                
                # Area bombing details
                area_data = force_year_data[force_year_data['mission_category'] == 'area']
                area_total = area_data['TOTAL TONS'].sum()
                if area_total > 0:
                    he_tons = area_data['HIGH EXPLOSIVE BOMBS TONS'].sum()
                    inc_tons = area_data['INCENDIARY BOMBS TONS'].sum()
                    report += f"\n    Area: {area_total:,.2f} ({area_total/force_year_total*100:.1f}%)"
                    report += f"\n      - HE: {he_tons:,.2f} ({he_tons/area_total*100:.1f}%)"
                    report += f"\n      - Incendiary: {inc_tons:,.2f} ({inc_tons/area_total*100:.1f}%)"
                
                # Precision bombing details
                precision_total = force_year_data[force_year_data['mission_category'] == 'precision']['TOTAL TONS'].sum()
                if precision_total > 0:
                    report += f"\n    Precision: {precision_total:,.2f} ({precision_total/force_year_total*100:.1f}%)"

    # Save the report
    with open(output_dir / 'summary_statistics_detailed.txt', 'w') as f:
        f.write(report)
    
    logging.info("Summary statistics report created and saved.")

def main():
    # Load data
    df = load_and_prepare_data('combined_attack_data_bombing_type.csv')

    # Create charts and reports
    create_summary_statistics_detailed(df)
    # create_attack_type_comparison(df)
    # create_trends_by_industry(df)    
    # create_industry_contribution_analysis(df)
    # create_overall_trends(df)
    # create_summary_statistics(df)
    # analyze_area_bombing_composition(df)
    # create_top_missions_report(df)
    
    logging.info("All reports and charts have been created successfully.")

if __name__ == "__main__":
    main()
