import pandas as pd
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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

def load_and_prepare_data(file_path):
    logging.info("Loading data...")
    df = pd.read_csv(file_path, low_memory=False)

    # Ensure datetime column is properly formatted
    df['DATETIME'] = pd.to_datetime(df['DATETIME'])
    
    # Extract month and year
    df['month_year'] = df['DATETIME'].dt.strftime('%Y-%m')
    df['month'] = df['DATETIME'].dt.month
    df['year'] = df['DATETIME'].dt.year
    
    # Create RAF indicator
    df['is_RAF'] = df['AIR FORCE'].astype(str).str.contains('R', na=False)
    df['force_name'] = df['is_RAF'].map({True: 'RAF', False: 'USAAF'})

    # Extract book category
    df['book_category'] = df['book'].apply(extract_book_category)

    # Update mission category - combine area bombing types
    df['mission_category'] = df['bombing_type']

    logging.info(f"Data loaded with {len(df)} records.")
    return df

def create_bombing_volume_summary(df, output_dir):
    """
    Create CSV files summarizing the total volume of bombs by bombing type
    and the percentage each type represents of the total.
    """
    logging.info("Calculating bombing volume summary...")
    
    # Create overall summary
    bombing_summary = df.groupby('mission_category')['TOTAL TONS'].sum().reset_index()
    total_tonnage = bombing_summary['TOTAL TONS'].sum()
    bombing_summary['percentage'] = (bombing_summary['TOTAL TONS'] / total_tonnage) * 100
    
    # Add a row for the total
    total_row = pd.DataFrame({
        'mission_category': ['Total'],
        'TOTAL TONS': [total_tonnage],
        'percentage': [100.0]
    })
    
    # Combine with the summary
    bombing_summary = pd.concat([bombing_summary, total_row], ignore_index=True)
    
    # Format the values
    bombing_summary['TOTAL TONS'] = bombing_summary['TOTAL TONS'].round(2)
    bombing_summary['percentage'] = bombing_summary['percentage'].round(2)
    
    # Save overall summary to CSV
    output_file = output_dir / 'bombing_volume_summary.csv'
    bombing_summary.to_csv(output_file, index=False)
    logging.info(f"Overall bombing volume summary saved to {output_file}")
    
    # Create breakdown by air force
    force_summary = df.groupby(['force_name', 'mission_category'])['TOTAL TONS'].sum().reset_index()
    
    # Calculate percentages within each air force
    for force in ['RAF', 'USAAF']:
        force_data = force_summary[force_summary['force_name'] == force]
        force_total = force_data['TOTAL TONS'].sum()
        
        force_summary.loc[force_summary['force_name'] == force, 'percentage_within_force'] = (
            force_summary.loc[force_summary['force_name'] == force, 'TOTAL TONS'] / force_total * 100
        )
    
    # Calculate percentage of overall total
    force_summary['percentage_of_total'] = force_summary['TOTAL TONS'] / total_tonnage * 100
    
    # Add totals for each air force
    for force in ['RAF', 'USAAF']:
        force_data = force_summary[force_summary['force_name'] == force]
        force_total = force_data['TOTAL TONS'].sum()
        
        total_row = pd.DataFrame({
            'force_name': [force],
            'mission_category': ['Total'],
            'TOTAL TONS': [force_total],
            'percentage_within_force': [100.0],
            'percentage_of_total': [force_total / total_tonnage * 100]
        })
        
        force_summary = pd.concat([force_summary, total_row], ignore_index=True)
    
    # Format values
    force_summary['TOTAL TONS'] = force_summary['TOTAL TONS'].round(2)
    force_summary['percentage_within_force'] = force_summary['percentage_within_force'].round(2)
    force_summary['percentage_of_total'] = force_summary['percentage_of_total'].round(2)
    
    # Save to CSV
    force_output_file = output_dir / 'bombing_volume_by_force.csv'
    force_summary.to_csv(force_output_file, index=False)
    logging.info(f"Bombing volume by air force summary saved to {force_output_file}")

def create_monthly_bombing_summary(df, output_dir):
    """
    Create a CSV file with a month-by-month breakdown of bombing volumes.
    """
    logging.info("Creating monthly bombing summary...")
    
    # Group by month, year and mission_category
    monthly_summary = df.groupby(['year', 'month', 'mission_category'])['TOTAL TONS'].sum().reset_index()
    
    # Create a month-year string for display
    monthly_summary['month_year'] = monthly_summary['year'].astype(str) + '-' + monthly_summary['month'].astype(str).str.zfill(2)
    
    # Create a pivot table with months as rows and mission types as columns
    monthly_pivot = monthly_summary.pivot_table(
        index=['year', 'month', 'month_year'], 
        columns='mission_category', 
        values='TOTAL TONS',
        aggfunc='sum'
    ).fillna(0)
    
    # Add a total column
    monthly_pivot['Total'] = monthly_pivot.sum(axis=1)
    
    # Calculate percentages - properly for each row
    for col in monthly_pivot.columns:
        if col != 'Total':
            monthly_pivot[f'{col}_pct'] = (monthly_pivot[col] / monthly_pivot['Total']) * 100
    
    # Reset index to make year, month, and month_year columns
    monthly_pivot = monthly_pivot.reset_index()
    
    # Sort by year and month to ensure chronological order
    monthly_pivot = monthly_pivot.sort_values(['year', 'month'])
    
    # Round numeric columns
    for col in monthly_pivot.columns:
        if col not in ['year', 'month', 'month_year']:
            monthly_pivot[col] = monthly_pivot[col].round(2)
    
    # Create yearly totals
    yearly_totals = []
    for year in monthly_pivot['year'].unique():
        year_data = monthly_pivot[monthly_pivot['year'] == year]
        year_totals = {
            'year': year,
            'month': 0,  # Use 0 to make it sort first in each year
            'month_year': f"{year}-Total"
        }
        
        # Calculate totals for each column
        for col in monthly_pivot.columns:
            if col not in ['year', 'month', 'month_year']:
                if col.endswith('_pct'):
                    # Skip percentage columns - we'll recalculate them
                    continue
                else:
                    # For tonnage columns, sum
                    year_totals[col] = year_data[col].sum()
        
        # Calculate percentages for yearly totals directly from tonnage
        for col in monthly_pivot.columns:
            if col not in ['year', 'month', 'month_year', 'Total'] and not col.endswith('_pct'):
                col_pct = f"{col}_pct"
                year_totals[col_pct] = (year_totals[col] / year_totals['Total']) * 100 if year_totals['Total'] > 0 else 0
        
        yearly_totals.append(year_totals)
    
    # Add yearly totals to the dataframe
    yearly_df = pd.DataFrame(yearly_totals)
    monthly_pivot = pd.concat([monthly_pivot, yearly_df], ignore_index=True)
    
    # Sort again to ensure yearly totals appear in the right place
    monthly_pivot = monthly_pivot.sort_values(['year', 'month'])
    
    # Round values for yearly totals
    for col in monthly_pivot.columns:
        if col not in ['year', 'month', 'month_year']:
            monthly_pivot[col] = monthly_pivot[col].round(2)
    
    # Verify that area_pct + precision_pct = 100 for each row
    monthly_pivot['sum_pct'] = monthly_pivot['area_pct'] + monthly_pivot['precision_pct']
    # Handle any small floating point errors
    monthly_pivot.loc[abs(monthly_pivot['sum_pct'] - 100) < 0.1, 'sum_pct'] = 100
    
    # Drop the verification column
    monthly_pivot = monthly_pivot.drop(columns=['sum_pct'])
    
    # Save to CSV
    monthly_output_file = output_dir / 'monthly_bombing_summary.csv'
    monthly_pivot.to_csv(monthly_output_file, index=False)
    logging.info(f"Monthly bombing summary saved to {monthly_output_file}")
    
    # Create a monthly breakdown by air force
    monthly_force_summary = df.groupby(['year', 'month', 'force_name', 'mission_category'])['TOTAL TONS'].sum().reset_index()
    monthly_force_summary['month_year'] = monthly_force_summary['year'].astype(str) + '-' + monthly_force_summary['month'].astype(str).str.zfill(2)
    
    # Sort for readability
    monthly_force_summary = monthly_force_summary.sort_values(['year', 'month', 'force_name', 'mission_category'])
    
    # Calculate percentages
    total_monthly_tonnage = monthly_force_summary.groupby(['year', 'month'])['TOTAL TONS'].sum().reset_index()
    total_monthly_tonnage.rename(columns={'TOTAL TONS': 'monthly_total'}, inplace=True)
    
    # Merge to add monthly total column
    monthly_force_summary = pd.merge(
        monthly_force_summary, 
        total_monthly_tonnage, 
        on=['year', 'month']
    )
    
    # Calculate percentage of monthly total
    monthly_force_summary['pct_of_monthly_total'] = (monthly_force_summary['TOTAL TONS'] / monthly_force_summary['monthly_total']) * 100
    
    # Create totals by force for each month
    force_monthly_totals = []
    for year in monthly_force_summary['year'].unique():
        for month in monthly_force_summary[monthly_force_summary['year'] == year]['month'].unique():
            month_data = monthly_force_summary[(monthly_force_summary['year'] == year) & 
                                             (monthly_force_summary['month'] == month)]
            
            # Process each force
            for force in ['RAF', 'USAAF']:
                force_data = month_data[month_data['force_name'] == force]
                if force_data.empty:
                    continue
                    
                force_total = force_data['TOTAL TONS'].sum()
                monthly_total = month_data['monthly_total'].iloc[0] if not month_data.empty else 0
                
                force_monthly_totals.append({
                    'year': year,
                    'month': month,
                    'month_year': f"{year}-{str(month).zfill(2)}",
                    'force_name': force,
                    'mission_category': 'Total',
                    'TOTAL TONS': force_total,
                    'monthly_total': monthly_total,
                    'pct_of_monthly_total': (force_total / monthly_total) * 100 if monthly_total > 0 else 0
                })
    
    # Add monthly force totals
    force_monthly_df = pd.DataFrame(force_monthly_totals)
    
    # Format values
    force_monthly_df['TOTAL TONS'] = force_monthly_df['TOTAL TONS'].round(2)
    force_monthly_df['pct_of_monthly_total'] = force_monthly_df['pct_of_monthly_total'].round(2)
    
    # Combine with the main dataframe
    monthly_force_summary = pd.concat([monthly_force_summary, force_monthly_df], ignore_index=True)
    
    # Sort again for readability
    monthly_force_summary = monthly_force_summary.sort_values(['year', 'month', 'force_name', 'mission_category'])
    
    # Save detailed monthly breakdown by force
    monthly_force_output_file = output_dir / 'monthly_bombing_by_force.csv'
    monthly_force_summary.to_csv(monthly_force_output_file, index=False)
    logging.info(f"Monthly bombing by air force saved to {monthly_force_output_file}")

def main():
    # Load data
    df = load_and_prepare_data('attack_data/combined_attack_data_bombing_type.csv')
    
    # Create output directory if it doesn't exist
    output_dir = Path('reports_summary')
    output_dir.mkdir(exist_ok=True, parents=True)
    
    # Generate the bombing volume summary
    create_bombing_volume_summary(df, output_dir)
    
    # Generate the monthly bombing summary
    create_monthly_bombing_summary(df, output_dir)
    
    logging.info("All bombing volume summaries have been created successfully.")

if __name__ == "__main__":
    main() 