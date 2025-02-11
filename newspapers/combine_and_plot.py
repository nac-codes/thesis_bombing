import os
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import argparse

# Define the standard bombing categories
STANDARD_CATEGORIES = [
    "Precision Bombing",
    "Area Bombing",
    "Industrial Bombing",
    "Counterforce Bombing",
    "Countervalue Bombing",
    "Nuclear Bombing"
]

def map_category(category_str: str):
    """
    Map a raw category string (from GPT analysis) to one of the standardized categories.
    """
    c = category_str.lower()
    if "precision" in c or "pinpoint" in c:
        return "Precision Bombing"
    elif "area" in c:
        return "Area Bombing"
    elif "industrial" in c:
        return "Industrial Bombing"
    elif "counterforce" in c:
        return "Counterforce Bombing"
    elif "countervalue" in c:
        return "Countervalue Bombing"
    elif "nuclear" in c:
        return "Nuclear Bombing"
    else:
        return None

def combine_json_to_csv(root_dir: str, output_csv: str):
    """
    Walk through the root directory and for each folder that has both info.txt.json and gpt_analysis.json,
    extract the date and the bombing category flags as binary values (1 if the category is mentioned, else 0).
    Save the combined data to a CSV.
    """
    # Check if the output CSV already exists
    if Path(output_csv).exists():
        print(f"Output CSV already exists: {output_csv}. Skipping combination.")
        # get the csv and return the dataframe
        df = pd.read_csv(output_csv)
        return df

    data_rows = []
    root_path = Path(root_dir)
    
    for current_dir, dirs, files in os.walk(root_path):
        current_dir_path = Path(current_dir)
        info_path = current_dir_path / "info.txt.json"
        analysis_path = current_dir_path / "gpt_analysis.json"
        
        if info_path.exists() and analysis_path.exists():
            try:
                with open(info_path, "r", encoding="utf-8") as f_info:
                    info_data = json.load(f_info)
                with open(analysis_path, "r", encoding="utf-8") as f_analysis:
                    analysis_data = json.load(f_analysis)
            except Exception as e:
                print(f"Error reading JSON files in {current_dir_path}: {str(e)}")
                continue

            # Extract date info from info.txt.json.
            try:
                d = info_data["date"]
                year = int(d.get("year"))
                month = int(d.get("month"))
                day = int(d.get("day"))
                date_obj = datetime(year, month, day)
            except Exception as e:
                print(f"Error parsing date in {info_path}: {str(e)}")
                continue

            # Process GPT analysis "Categories" list.
            raw_categories = analysis_data.get("Categories", [])
            mapped_categories = set()
            for cat in raw_categories:
                mapped = map_category(cat)
                if mapped:
                    mapped_categories.add(mapped)

            # Create binary columns for each standardized category.
            row = {"Date": date_obj.strftime("%Y-%m-%d")}
            for cat in STANDARD_CATEGORIES:
                row[cat] = 1 if cat in mapped_categories else 0

            data_rows.append(row)

    if data_rows:
        df = pd.DataFrame(data_rows)
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.sort_values("Date")
        df.to_csv(output_csv, index=False)
        print(f"Combined CSV saved to: {output_csv}")
        return df
    else:
        print("No valid data found for combining.")
        return None

def plot_market_share(df: pd.DataFrame, output_png: str, bin_size: int):
    """
    Group the records into bins of specified size and plot a market share line graph for each bombing category.
    For each bin, the proportion is the number of articles that mention that category divided by 
    the total number of articles in the bin.
    """
    # Ensure the "Date" column is datetime and set as index.
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date").set_index("Date")
    
    # Resample into specified bins.
    bin_total = df.resample(f"{bin_size}D").size()
    
    # Sum each categorical column within each bin.
    bin_counts = df.resample(f"{bin_size}D").sum()
    
    # Calculate proportion (%) for each category within each bin.
    proportions = bin_counts.divide(bin_total, axis=0) * 100
    proportions = proportions.fillna(0)

    # Restrict the date domain to before 1946
    proportions = proportions[proportions.index < datetime(1946, 1, 1)]

    # Prepare the plot.
    plt.figure(figsize=(12, 6))
    
    for cat in STANDARD_CATEGORIES:
        plt.plot(proportions.index, proportions[cat], marker="o", label=cat)
    
    plt.title(f"Market Share of Bombing Categories ({bin_size}-Day Bins)")
    plt.xlabel("Date")
    plt.ylabel("Percentage of Articles (%)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(output_png, dpi=300)
    plt.show()
    print(f"Market share graph saved to: {output_png}")

def main():
    # Set the root directory where the newspaper folders are located.
    root_dir = "/Users/chim/Working/Thesis/Readings/src/scrape_newspapers/newspaper_articles"
    output_csv = "combined_bombing_data.csv"
    
    # Set up command line argument parsing for bin size
    parser = argparse.ArgumentParser(description="Combine JSON data and plot market share.")
    parser.add_argument("--bin_size", type=int, default=100, help="Size of the bins in days for the market share plot.")
    args = parser.parse_args()
    
    output_png = f"bombing_market_share_{args.bin_size}d.png"

    print("Combining JSON data into CSV...")
    df = combine_json_to_csv(root_dir, output_csv)
    if df is not None and not df.empty:
        print("Plotting market share graph...")
        plot_market_share(df, output_png, args.bin_size)
    else:
        print("No data to plot.")

if __name__ == "__main__":
    main()