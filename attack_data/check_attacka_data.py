import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from scipy import stats
import subprocess
import os
from tabulate import tabulate

def display_attack_data(image_rows, idx, bomb_type, row):
    # Select relevant columns
    display_columns = [
        'DAY', 'MONTH', 'YEAR', 'AIR FORCE', 
        'HIGH EXPLOSIVE BOMBS TONS', 'INCENDIARY BOMBS TONS', 
        'FRAGMENTATION BOMBS TONS', 'TOTAL TONS'
    ]
    
    # Prepare data for display
    display_data = image_rows[display_columns].copy()
    
    # Add marker column for outlier row
    display_data.insert(0, '', ['>>>' if i == idx else '' for i in display_data.index])
    
    # Format the table
    print("\nFull table for this image:")
    print(tabulate(
        display_data,
        headers=['', *display_columns],
        tablefmt='grid',
        floatfmt='.2f',
        showindex=True
    ))
    
    # Print context information
    print(f"\nOutlier Details:")
    print(f"Target: {row['target_location']} ({row['target_name']})")
    print(f"Date: {(row['DAY'])}/{(row['MONTH'])}/{(row['YEAR'])}")
    print(f"Outlier value ({bomb_type}): {row[bomb_type]:.2f}")


def plot_distribution(data, title, directory, filename):
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    save_path = os.path.join(directory, filename)
    
    plt.figure(figsize=(10, 6))
    
    # Create distribution plot
    sns.histplot(data, kde=True)
    
    # Calculate mean and std
    mean = np.mean(data)
    std = np.std(data)
    
    # Add vertical lines for mean and ±2 std
    plt.axvline(mean, color='r', linestyle='--', label='Mean')
    plt.axvline(mean + 2*std, color='g', linestyle='--', label='+2 STD')
    plt.axvline(mean - 2*std, color='g', linestyle='--', label='-2 STD')
    
    plt.title(title)
    plt.legend()
    plt.savefig(save_path)
    plt.close()

def find_outliers(data, column):
    mean = np.mean(data[column])
    std = np.std(data[column])
    outliers = data[data[column] > mean + 2*std].copy()
    return outliers.sort_values(by=column, ascending=False)

def open_image_in_preview(image_path):
    try:
        subprocess.run(['open', '-a', 'Preview', image_path])
    except Exception as e:
        print(f"Error opening image: {e}")

def close_preview():
    try:
        subprocess.run(['osascript', '-e', 'tell application "Preview" to quit'])
    except Exception as e:
        print(f"Error closing Preview: {e}")

def main():
    # Read the data

    # if checked data exists, load it
    if os.path.exists('/Users/chim/Working/Thesis/Attack_Images/OCR/PRODUCTION/combined_attack_data_checked.csv'):
        print('Loading checked data')
        df = pd.read_csv('/Users/chim/Working/Thesis/Attack_Images/OCR/PRODUCTION/combined_attack_data_checked.csv')
    else:
        print('Loading complete data')
        df = pd.read_csv('/Users/chim/Working/Thesis/Attack_Images/OCR/PRODUCTION/combined_attack_data_complete.csv')
    
    # Create distributions for each bomb type
    for bomb_type in ['HIGH EXPLOSIVE BOMBS TONS', 'INCENDIARY BOMBS TONS', 'FRAGMENTATION BOMBS TONS']:
        data = df[bomb_type].dropna()
        if len(data) > 0:
            plot_distribution(
                data,
                f'Distribution of {bomb_type}',
                '/Users/chim/Working/Thesis/Attack_Images/OCR/PRODUCTION/reports/tons/',
                f'tonnage_distribution_{bomb_type.lower().replace(" ", "_")}.png'
            )
    
    # Process outliers for each bomb type
    for bomb_type in ['HIGH EXPLOSIVE BOMBS TONS', 'INCENDIARY BOMBS TONS', 'FRAGMENTATION BOMBS TONS']:
        print(f"\nProcessing outliers for {bomb_type}")
        outliers = find_outliers(df, bomb_type)
        
        if len(outliers) == 0:
            print(f"No outliers found for {bomb_type}")
            continue
        
        print(f"\nStatistics for {bomb_type} outliers:")
        print(f"Number of outliers: {len(outliers)}")
        print(f"Mean of outliers: {outliers[bomb_type].mean():.2f}")
        print(f"Max value: {outliers[bomb_type].max():.2f}")
        
        # Process each outlier
        for idx, row in outliers.iterrows():
            # Get all rows for the same image
            image_rows = df[df['image'] == row['image']].copy()
            
            # Print the full table with row numbers
            display_attack_data(image_rows, idx, bomb_type, row)
            
            
            print(f"\nOutlier value: {row[bomb_type]}")
            print(f"Location: {row['target_location']}")
            print(f"Date: {row['DAY']}/{row['MONTH']}/{row['YEAR']}")
            
            # Construct image path
            image_path = os.path.join('/Users/chim/Working/Thesis/Attack_Images/BOXES',
                                    row['box'],
                                    row['book'],
                                    row['image'].replace('_output', '.JPG'))
            
            # Open image in Preview
            open_image_in_preview(image_path)    
            
            # Get user input
            user_input = input("Press Enter if value is correct, enter 'SUM' to mark as summation, or enter new value: ").strip()        

            # Close image
            close_preview()
            
            if user_input.upper() == 'SUM':
                # Remove the row                
                df = df.drop(idx)
                print(f"Removed row {idx}")
                df.to_csv('combined_attack_data_checked.csv', index=False)
            elif user_input.upper() == 'END':
                print('Moving to next bomb type')
                break
            elif user_input:
                try:
                    new_value = float(user_input)
                    df.loc[idx, bomb_type] = new_value
                    # Recalculate total tonnage
                    df.loc[idx, 'TOTAL TONS'] = df.loc[idx, ['HIGH EXPLOSIVE BOMBS TONS', 
                                                            'INCENDIARY BOMBS TONS', 
                                                            'FRAGMENTATION BOMBS TONS']].sum()
                    print(f"Updated value to {new_value}")
                    df.to_csv('combined_attack_data_checked.csv', index=False)
                except ValueError:
                    print("Invalid input - keeping original value")
    
    # Save updated dataframe
    df.to_csv('combined_attack_data_checked.csv', index=False)
    print("\nUpdated data saved to combined_attack_data_checked.csv")

if __name__ == "__main__":
    main()