import os
import pandas as pd
import glob
from datetime import datetime
import sys

# Check if the command line argument is provided
if len(sys.argv) < 2:
    print("Usage: python script.py <directory_suffix>")
    sys.exit(1)

# Get the directory suffix from the command line argument
directory_suffix = sys.argv[1]


# Get a list of all items (files and folders) in the directory
export_folder = 'export'
directory_path = os.path.join(export_folder, directory_suffix)
all_items = os.listdir(directory_path)

# Uncomment if you want to check performance transform

# Time before running transform
# start_time = datetime.now()
# print("start time: ",start_time)

# Filter out only the folders
folder_names = [item for item in all_items if os.path.isdir(os.path.join(directory_path, item))]
len_items = 0
for folder in folder_names:


    # Specify the directory where your CSV files are located
    csv_files = glob.glob(f"{directory_path}/{folder}/*.csv")

    # Initialize an empty DataFrame to store the merged data
    merged_data = pd.DataFrame()

    # Loop through each CSV file and append its data to the merged_data DataFrame
    for csv_file in csv_files:
        df = pd.read_csv(csv_file)
        merged_data = merged_data._append(df, ignore_index=True)
    try:
        os.mkdir(f"transform/{directory_suffix}")  
    except:
        pass
        
    # Write the merged data to a new CSV file
    merged_data.to_csv(f"transform/{directory_suffix}/{folder}.csv", index=False)
    df = pd.read_csv(f"transform/{directory_suffix}/{folder}.csv")
    df = df.drop_duplicates()
    df["product_rating"] = df["product_rating"] / 100.0
    df["product_rating"] = df["product_rating"].apply(lambda x: f"{x:.3f}").astype(float)
    df["product_price"] = df["product_price"].str.replace(".", "")
    df["history_sold"] = df["history_sold"].str.replace(",", ".").str.replace("k", "e3").str.replace("tr", "e6")
    df["history_sold"] = df["history_sold"].astype(float)
    def multiply_values(row):
        if "-" in row['product_price']:
            start, end = map(float, row['product_price'].split(" - "))
            result = f"{start * row['history_sold']} - {end * row['history_sold']}"
        else:
            result = float(row['product_price']) * row['history_sold']
        return result

    df["product_revenue"] = df.apply(multiply_values, axis=1)
    df = df.drop("history_sold", axis=1)
    df.to_csv(f"transform/{directory_suffix}/{folder}.csv", index=False)
    len_items += len(df)
    
# performance transform

# print("Total items transfom: ", len_items)
# # Time after running transform
# end_time = datetime.now()
# print("End time: ", end_time)

# # Calculate the time difference
# elapsed_time = end_time - start_time
# elapsed_minutes = elapsed_time.total_seconds() / 60

# # Evaluate the number of products transform per minute
# products_per_minute = len_items / elapsed_minutes
# print(f"Number of products transform per minute: {products_per_minute}")