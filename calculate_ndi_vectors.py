import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import os

# Uncomment the following line and set the file name if you want to use a specific CSV file
# specific_file_path = 'experiments/NDI/vector_000.csv'

# Get the latest CSV file in the experiments/NDI folder
ndi_folder = 'experiments/NDI'
csv_files = [f for f in os.listdir(ndi_folder) if f.endswith('.csv')]
if not csv_files:
    print('No CSV files found in the experiments/NDI folder.')
else:
    # Use specific file if provided
    if 'specific_file_path' in locals() and specific_file_path:
        file_path = specific_file_path
    else:
        latest_file = max([os.path.join(ndi_folder, f) for f in csv_files], key=os.path.getmtime)
        file_path = latest_file
    try:
        data = pd.read_csv(file_path)
        # Get all column names
        columns = data.columns.tolist()

        # Assume the first three columns are for Point 1 and the next three are for Point 2
        point1_columns = columns[:3]
        point2_columns = columns[3:6]

        point1 = data[point1_columns].values
        point2 = data[point2_columns].values

        # Calculate the vector between two points
        vectors = point2 - point1

        # Normalize the vectors to have a length of 1
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        normalized_vectors = vectors / norms

        # Extract x, y, z coordinates from point1 and normalized_vectors
        x1, y1, z1 = point1[:, 0], point1[:, 1], point1[:, 2]
        x_vec, y_vec, z_vec = normalized_vectors[:, 0], normalized_vectors[:, 1], normalized_vectors[:, 2]

        # Create a 3D plot
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')

        # Plot the trajectory of Point 1
        ax.plot(x1, y1, z1, label='Trajectory of Point 1', color='blue')

        # Plot the vectors every 30 steps for better visibility
        scale_factor = 50  # Adjust this value to increase vector size
        for i in range(0, len(x1), 30):
            ax.quiver(x1[i], y1[i], z1[i], x_vec[i], y_vec[i], z_vec[i], color='red', length=scale_factor, normalize=True)

        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        ax.set_title('Normalized Vectors between Two Points')
        ax.legend()

        plt.show()
    except FileNotFoundError:
        print(f'The file {file_path} was not found.')