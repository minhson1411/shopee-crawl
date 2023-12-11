import os
import pandas as pd
import glob
directory_path = "20231209_231744"
# Get a list of all items (files and folders) in the directory
all_items = os.listdir(directory_path)

# Filter out only the folders
folder_names = [item for item in all_items if os.path.isdir(os.path.join(directory_path, item))]
for folder in folder_names:


    # Specify the directory where your CSV files are located
    csv_files = glob.glob(f"{directory_path}/{folder}/*.csv")

    # Initialize an empty DataFrame to store the merged data
    merged_data = pd.DataFrame()

    # Loop through each CSV file and append its data to the merged_data DataFrame
    for csv_file in csv_files:
        df = pd.read_csv(csv_file)
        merged_data = merged_data.append(df, ignore_index=True)
    try:
        os.mkdir(f"transform/{directory_path}")  
    except:
        pass
        
    # Write the merged data to a new CSV file
    merged_data.to_csv(f"transform/{directory_path}/{folder}.csv", index=False)
    df = pd.read_csv(f"transform/{directory_path}/{folder}.csv")
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
    df.to_csv(f"transform/{directory_path}/{folder}.csv", index=False)
    print(df)