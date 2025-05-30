"""
NDI Data Processing Pipeline

This script processes motion capture data from NDI (Northern Digital Inc.) optical tracking system.
Device: NDI Polaris Vega
Software: NDI Tool Tracker
Data Format: CSV
The workflow consists of the following steps:

1. Data Cleaning (clean_csv):
   - Removes first 42 columns of metadata
   - Keeps only numeric columns
   - Replaces invalid values with 0
   - Renames columns to x1,y1,z1,x2,y2,z2 format for markers

2. Marker Labelling (label_markers):
   - Tracks marker movements between frames
   - Filters out position glitches using maximum position change threshold
   - Ensures consistent marker labelling/tracking
   - Saves labelled data with consistent 2 markers (6 coordinates)

3. Data Interpolation (interpolate_data):
   - Resamples data from original frame rate to desired frame rate
   - Uses cubic interpolation to generate smooth trajectories
   - Handles any gaps in the data

The script automatically processes the latest CSV file from the raw data folder
and saves outputs in clean, labelled, and interpolated subfolders.

Dependencies:
- pandas: Data manipulation
- numpy: Numerical operations
- scipy: Interpolation functions
- os: File/directory operations
"""

import pandas as pd
import numpy as np
import os
from scipy import interpolate
from config import (
    NDI_MAX_POSITION_CHANGE as MAX_POSITION_CHANGE,
    NDI_ORIGINAL_FRAME_RATE as ORIGINAL_FRAME_RATE,
    NDI_DESIRED_FRAME_RATE as DESIRED_FRAME_RATE
)

def get_latest_csv_file(ndi_folder):
    """Get the latest CSV file in the specified folder."""
    csv_files = [f for f in os.listdir(ndi_folder) if f.endswith('.csv')]
    if not csv_files:
        print('No CSV files found in the specified folder.')
        return None
    latest_file = max([f"{ndi_folder}/{f}" for f in csv_files], key=os.path.getmtime)
    return latest_file

def clean_csv(file_path, output_path):
    """Clean and process the CSV file according to specified rules.
    First determines the maximum number of columns, then processes the data accordingly.
    Handles variable row lengths by filling empty spaces with NaN.
    """
    # First pass: determine maximum number of columns
    max_columns = 0
    with open(file_path, 'r') as file:
        for line in file:
            columns = len(line.strip().split(','))
            max_columns = max(max_columns, columns)
    
    # Read CSV with the determined number of columns
    df = pd.read_csv(file_path, 
                     header=None,
                     dtype=str,
                     on_bad_lines='skip',
                     names=range(max_columns),  # Pre-allocate all possible columns
                     na_values=[''],  # Treat empty fields as NaN
                     keep_default_na=True)  # Keep pandas' default NA values
    
    # Drop the first 42 columns
    df = df.iloc[:, 42:]
    
    # Function to check if a column contains only numeric values
    def is_numeric_column(col):
        try:
            pd.to_numeric(col, errors='raise')
            return True
        except ValueError:
            return False
    
    # Find columns that contain only numeric data
    data_rows = df.iloc[1:]  # Skip header row when checking for numeric values
    keep_cols = []
    for i in range(len(df.columns)):
        if is_numeric_column(data_rows.iloc[:, i]):
            keep_cols.append(i)
    
    # Keep only the numeric columns (including their headers)
    if keep_cols:  # Only proceed if we found numeric columns
        df = df.iloc[:, keep_cols]
    else:
        print("Warning: No numeric columns found after filtering")
    
    # Drop the header row as we'll create new column names
    df = df.iloc[1:]
    
    # Convert to float, replacing errors with NaN
    df = df.apply(pd.to_numeric, errors='coerce')
    
    # Replace -3.697314E28 and NaN with 0
    df = df.replace([-3.697314E28, np.nan], 0)
    
    # Generate new column names
    num_columns = len(df.columns)
    num_points = num_columns // 3  # Integer division to get complete sets of x,y,z
    if num_columns % 3 != 0:
        num_points += 1  # Add one more set if we have partial coordinates
    
    new_columns = []
    for i in range(1, num_points + 1):
        new_columns.extend([f'x{i}', f'y{i}', f'z{i}'])
    
    # Take exactly the number of columns we need
    new_columns = new_columns[:num_columns]
    df.columns = new_columns
    
    # Save the cleaned data
    df.to_csv(output_path, index=False)
    print(f"Cleaned!!")

# Rename the function and update its docstring
def label_markers(clean_file_path, max_position_change=MAX_POSITION_CHANGE):
    """Label marker positions by tracking their movement and filtering glitches.
    
    Args:
        clean_file_path: Path to the cleaned CSV file
        max_position_change: Maximum allowed position change in mm between consecutive frames
    """
    # Read the cleaned CSV file
    df = pd.read_csv(clean_file_path)
    
    # Ensure we have exactly 6 columns for 2 markers
    if len(df.columns) < 6:
        print(f"Warning: Not enough columns in cleaned data. Expected 6, got {len(df.columns)}")
        return
    
    # Initialize arrays to store previous valid positions for each marker
    prev_pos = {
        'marker1': (None, None, None),  # (x, y, z)
        'marker2': (None, None, None)
    }
    
    # Create a copy for labelled data
    labelled = df.copy()
    
    # Process each row
    for idx in range(1, len(labelled)):
        row = labelled.iloc[idx]
        
        # Group coordinates into markers as tuples
        markers = []
        for i in range(1, len(row.index) // 3 + 1):
            x = row[f'x{i}']
            y = row[f'y{i}']
            z = row[f'z{i}']
            # Only append marker if x, y, z are not all 0
            if not (x == 0 and y == 0 and z == 0):
                markers.append((x, y, z))
        
        # If this is the first valid data, initialize previous positions
        if idx == 1:
            if len(markers) !=2:
                print(f"Warning: Initial number of markers is {len(markers)} rather than 2!")
                return
            prev_pos['marker1'] = markers[0]
            prev_pos['marker2'] = markers[1]
            continue
        
        # Calculate distances from previous positions
        distances = []
        for marker in markers:
            for marker_id, prev_marker in prev_pos.items():
                if all(v is not None for v in prev_marker):
                    # Calculate Euclidean distance using numpy for better performance
                    marker_array = np.array(marker)
                    prev_marker_array = np.array(prev_marker)
                    dist = np.linalg.norm(marker_array - prev_marker_array)
                    if dist < max_position_change:
                        distances.append((marker, marker_id, dist))
        
        if len(distances) != 2:
            raise RuntimeError(f"Marker lost track at frame {idx}! Program terminated.")
        
        # Update positions based on closest matches within threshold
        used_marker_ids = set()
        
        # Since we have exactly 2 valid matches, assign them directly
        # First marker (closest match)
        curr_pos, marker_id, _ = distances[0]
        if marker_id == 'marker1':
            labelled.at[idx, 'x1'] = curr_pos[0]
            labelled.at[idx, 'y1'] = curr_pos[1]
            labelled.at[idx, 'z1'] = curr_pos[2]
            labelled.at[idx, 'x2'] = distances[1][0][0]  # Second marker position
            labelled.at[idx, 'y2'] = distances[1][0][1]
            labelled.at[idx, 'z2'] = distances[1][0][2]
        else:
            labelled.at[idx, 'x2'] = curr_pos[0]
            labelled.at[idx, 'y2'] = curr_pos[1]
            labelled.at[idx, 'z2'] = curr_pos[2]
            labelled.at[idx, 'x1'] = distances[1][0][0]  # Second marker position
            labelled.at[idx, 'y1'] = distances[1][0][1]
            labelled.at[idx, 'z1'] = distances[1][0][2]
        
        # Update previous positions
        prev_pos['marker1'] = labelled.iloc[idx][['x1', 'y1', 'z1']].values
        prev_pos['marker2'] = labelled.iloc[idx][['x2', 'y2', 'z2']].values
    
    # Keep only first 6 columns (2 markers x 3 coordinates)
    labelled = labelled.iloc[:, :6]

    # Save labelled data to the labelled folder
    labelled_folder = os.path.join(os.path.dirname(os.path.dirname(clean_file_path)), 'labelled')
    if not os.path.exists(labelled_folder):
        os.makedirs(labelled_folder)
    
    base_name, ext = os.path.splitext(os.path.basename(clean_file_path))
    base_name = base_name.replace('_clean', '_labelled')
    labelled_file = f"{labelled_folder}/{base_name}{ext}"
    labelled.to_csv(labelled_file, index=False)
    print(f"Labelled!!")

def interpolate_data(file_path, output_path):
    """Interpolate the marker data to match the desired frame rate.
    
    Args:
        file_path: Path to the input CSV file
        output_path: Path to save the interpolated data
    """
    # Read the labelled data
    df = pd.read_csv(file_path)
    
    # Calculate time points for original and desired data
    original_time = np.arange(len(df)) / ORIGINAL_FRAME_RATE
    desired_time = np.arange(0, original_time[-1], 1/DESIRED_FRAME_RATE)
    
    # Create interpolated data frame
    interpolated_data = {}
    
    # Interpolate each column
    for column in df.columns:
        # Create interpolation function
        f = interpolate.interp1d(original_time, df[column], kind='cubic', bounds_error=False, fill_value='extrapolate')
        # Generate interpolated values
        interpolated_data[column] = f(desired_time)
    
    # Create new dataframe with interpolated data
    interpolated_df = pd.DataFrame(interpolated_data)
    
    # Save interpolated data
    interpolated_folder = os.path.join(os.path.dirname(os.path.dirname(file_path)), 'interpolated')
    if not os.path.exists(interpolated_folder):
        os.makedirs(interpolated_folder)
    
    interpolated_df.to_csv(output_path, index=False)
    print(f"Interpolated!!")

# Update the main function
def main():
    """Main function to process the latest CSV file."""
    raw_folder = 'experiments/NDI/raw'
    clean_folder = 'experiments/NDI/clean'
    labelled_folder = 'experiments/NDI/labelled'
    interpolated_folder = 'experiments/NDI/interpolated'

    # Ensure the output directories exist
    for folder in [clean_folder, labelled_folder, interpolated_folder]:
        if not os.path.exists(folder):
            os.makedirs(folder)

    # Get the CSV file to process
    try:
        from config import CSV_FILE
        if not os.path.isfile(CSV_FILE):
            raise FileNotFoundError(f"Specified CSV_FILE '{CSV_FILE}' does not exist or is not a valid file")
        file_path = CSV_FILE
        print(f"Processing specified file: {file_path}")
    except ImportError:
        # If CSV_FILE is not defined in config, get the latest file
        file_path = get_latest_csv_file(raw_folder)
        print(f"Processing latest file: {file_path}")

    if file_path:
        try:
            # Process base name for all output files
            base_name, ext = os.path.splitext(os.path.basename(file_path))
            
            # Define output paths using forward slashes
            clean_output = f"{clean_folder}/{base_name}_clean{ext}"
            labelled_output = f"{labelled_folder}/{base_name}_labelled{ext}"
            interpolated_output = f"{interpolated_folder}/{base_name}_interpolated{ext}"

            # Process the data through each stage
            clean_csv(file_path, clean_output)
            label_markers(clean_output)
            interpolate_data(labelled_output, interpolated_output)
            
        except Exception as e:
            print(f'Error processing file: {str(e)}')


if __name__ == "__main__":
    main()