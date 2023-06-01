import json
import pandas as pd
import numpy as np
import re
import os

def clean_file(filepath):
    # Read the text file
    with open(filepath) as f:
        input_text = f.read()

    # Define the regex pattern & Replace the regex pattern with an empty string
    regex = r'\r|\t|\n|\s|(pd numbers)|([0-9]{2}:[0-9]{2}:[0-9]{2})'
    pattern = re.compile(regex)
    modified_text = pattern.sub('', input_text)

    try:
        # Extract the JSON string from the text
        json_string = modified_text[modified_text.index("{"):modified_text.rindex("}")+1]

        # Load the JSON string as a dictionary
        data = json.loads(json_string)

        # Create a DataFrame from the dictionary
        df = pd.DataFrame.from_dict(data, orient="index").reset_index()
        df.columns = ["name", "value"]

        return df
    except (ValueError, json.JSONDecodeError) as e:
        # Print the error message along with the filename
        print(f"Error parsing JSON in file: {filepath}")
        print(f"Error message: {str(e)}")
        return None

def read_folder(folder_path):
    # Create a dictionary to store the dataframes
    df_dict = {}
    error_files = []

    # Loop through each file in the folder
    for filename in os.listdir(folder_path):
        if filename.endswith('_Num.txt'):
            # Get the key from the filename
            key = filename.split('_')[0]

            # Clean the file and create the dataframe
            filepath = os.path.join(folder_path, filename)
            df = clean_file(filepath)

            # Skip the file if it returns None from clean_file
            if df is None:
                error_files.append(filename)
                continue

            # Add the dataframe to the dictionary
            if key in df_dict:
                # If the key already exists in the dictionary, add a new column to the existing dataframe
                value_name = filename.split('_')[1].split('.')[0]
                df_dict[key][value_name] = df['value']
            else:
                # If the key does not exist in the dictionary, create a new dataframe
                df_dict[key] = df.rename(columns={'value': filename.split('_')[1].split('.')[0]})

    return df_dict, error_files

def process_dataframes(df_dict):
    # Create a new dictionary to store the processed dataframes
    processed_dict = {}

    # Loop through each key and dataframe in the input dictionary
    for key, df in df_dict.items():

        df = df.set_index('name')

        # Convert the numeric columns to numeric type
        numeric_columns = df.columns
        df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric, errors='coerce')
        # Calculate the statistics
        df["Amount of Columns"] = df[numeric_columns].count(axis=1)
        df['Max'] = df[numeric_columns].max(axis=1)
        df["Minimum Value (excluding 0)"] = df[df[numeric_columns] > 0].min(axis=1)
        df["Average"] = df[numeric_columns].mean(axis=1)
        df["Average (excluding 0)"] = df[df[numeric_columns] > 0].mean(axis=1)
        df["Standard Deviation"] = df[numeric_columns].std(axis=1)
        df["Median"] = df[numeric_columns].median(axis=1)

        # Apply formatting to remove scientific notation and keep 2 decimal places
        df = df.applymap(lambda x: '{:.2f}'.format(x))

        # Add the processed dataframe to the new dictionary
        processed_dict[key] = df
    return processed_dict


folder_path = r'C:\Users\tra1ein\SharePoint On-Premise\BT-ASA DataShare - Documents\006 Log-Files\PRAESENSA'
dict_all, error_files = read_folder(folder_path)
processed_dict = process_dataframes(dict_all)
output_path = r'C:\Users\tra1ein\Downloads\output.xlsx'


# Create a DataFrame to store the error files
error_df = pd.DataFrame({"Error files": error_files})

# Write each processed dataframe to an Excel sheet with the key as sheet name
with pd.ExcelWriter(output_path) as writer:
    for key, df in processed_dict.items():
        df.to_excel(writer, sheet_name=key, index=True)
    # Write the error DataFrame to a separate sheet
    error_df.to_excel(writer, sheet_name="Errors", index=False)

# Print the filenames that encountered errors
print("Error files:")
print(error_files)
