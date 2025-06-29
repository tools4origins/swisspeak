import sys
import os
from PIL import Image

def read_ascii_matrix(filepath):
    """
    Reads an ASCII file containing a matrix of points with a header.

    The header is expected to contain 'ncols', 'nrows', and 'NODATA_value'
    on the first three lines, in any order. The data rows follow.

    Args:
        filepath (str): The path to the input ASCII file.

    Returns:
        tuple: A tuple containing:
            - int: Number of columns (ncols).
            - int: Number of rows (nrows).
            - float: NODATA_value.
            - list: A 2D list representing the matrix data.
    """
    ncols = 0
    nrows = 0
    nodata_value = -9999.0  # Default NODATA_value, will be overwritten by file content
    matrix_data = []
    
    try:
        with open(filepath, 'r') as f:
            header_lines = []
            # Read header lines (assuming first 3 lines are header)
            for _ in range(6):
                line = f.readline().strip()
                if not line: # Handle case of empty file or too few header lines
                    raise ValueError("Input file has an incomplete header.")
                header_lines.append(line)

            # Parse header information
            for line in header_lines:
                parts = line.split()
                if len(parts) < 2:
                    raise ValueError(f"Malformed header line: '{line}'")
                
                key = parts[0]
                value = parts[1]

                if key == "ncols":
                    ncols = int(value)
                elif key == "nrows":
                    nrows = int(value)
                elif key == "NODATA_value":
                    nodata_value = float(value)
                elif key in ('xllcorner', 'yllcorner', 'cellsize'):
                    pass
                else:
                    print(f"Warning: Unrecognized header key '{key}' in line: {line}")

            # Read matrix data
            for line in f:
                # Split the line by space, convert to float, and append to matrix_data
                row_values = [float(x) for x in line.strip().split()]
                matrix_data.append(row_values)

    except FileNotFoundError:
        print(f"Error: Input file not found at '{filepath}'. Please check the path.")
        exit(1) # Exit the script on critical error
    except ValueError as ve:
        print(f"Error parsing file content: {ve}. Please ensure the file format is correct.")
        exit(1)
    except Exception as e:
        print(f"An unexpected error occurred while reading the file: {e}")
        exit(1)

    # Basic validation of matrix dimensions against header
    if not (ncols > 0 and nrows > 0 and len(matrix_data) == nrows and all(len(row) == ncols for row in matrix_data)):
        print("Error: Matrix dimensions from header do not match actual data or data is malformed.")
        print(f"Header: ncols={ncols}, nrows={nrows}")
        print(f"Actual data rows: {len(matrix_data)}, expected {nrows}")
        if matrix_data:
            print(f"Length of first data row: {len(matrix_data[0])}, expected {ncols}")
        exit(1)

    return ncols, nrows, nodata_value, matrix_data


def find_min_max(matrix_data, nodata_value):
    """
    Finds the minimum and maximum values in the matrix, ignoring NODATA_value.

    Args:
        matrix_data (list): The 2D list representing the matrix.
        nodata_value (float): The value to ignore.

    Returns:
        tuple: A tuple containing (min_value, max_value).
               Returns (None, None) if no valid data points are found.
    """
    min_val = float('inf')
    max_val = float('-inf')
    found_valid_data = False

    for row in matrix_data:
        for value in row:
            if value != nodata_value:
                min_val = min(min_val, abs(value))
                max_val = max(max_val, abs(value))
                found_valid_data = True
    
    if not found_valid_data:
        return None, None # No valid data points found
    
    #min_val, max_val = 1150, 1250
    return min_val, max_val

def map_value_to_color(value, min_val, max_val, nodata_value):
    """
    Maps a numerical value to an RGB color on a green-to-red gradient.
    NODATA_value is mapped to black.

    Args:
        value (float): The numerical value from the matrix.
        min_val (float): The global minimum value in the matrix.
        max_val (float): The global maximum value in the matrix.
        nodata_value (float): The value representing no data.

    Returns:
        tuple: An RGB tuple (R, G, B) where each component is 0-255.
    """
    if value == nodata_value:
        return (255, 255, 255)  # Black for NODATA_value

    if max_val == min_val:
        # If all valid values are the same, map to green
        return (0, 255, 0)
    
    # Normalize the value to a 0-1 range
    if abs(value) <= min_val:
        normalized_value = 0
    elif abs(value) >= max_val:
        normalized_value = 1
    else:
        normalized_value = (abs(value) - min_val) / (max_val - min_val)
        gap = 0.35
        normalized_value = gap + normalized_value * (1-gap)
    
    if value >= 0:
        # Map to green (0, 255, 0) to red (255, 0, 0) gradient
        red = int((1 - normalized_value) * 255)
        blue = 0
        green = 0 #int(normalized_value * 255)
    else:
        # Map to dark (0, 0, 0) to blue (0, 0, 255) gradient
        red = 0
        green = int(normalized_value * 255)
        blue = 0
    
    if not (0<=red<=255) or not (0<=green<=255) or not (0<=blue<=255):
        print(f"warning: for {value}: {red=},{green=},{blue=}")

    # Ensure color components are within valid 0-255 range
    red = max(0, min(255, red))
    green = max(0, min(255, green))
    blue = max(0, min(255, blue))
    
    return (red, green, blue)

def create_bitmap_from_matrix(matrix_data, ncols, nrows, nodata_value, output_filepath):
    """
    Converts a numerical matrix into a bitmap image.
    Values are mapped to a green-to-red gradient, with NODATA_value as black.

    Args:
        matrix_data (list): The 2D list representing the matrix.
        ncols (int): Number of columns in the matrix.
        nrows (int): Number of rows in the matrix.
        nodata_value (float): The value representing no data.
        output_filepath (str): The path to save the output image file (e.g., 'output.png').
    """
    # Find the min and max values in the matrix (excluding NODATA)
    min_val, max_val = find_min_max(matrix_data, nodata_value)
    print(f'{min_val=}, {max_val=}')

    if min_val is None:
        print("Warning: No valid data found in the matrix to create a gradient. Creating a black image.")
        # Create a blank black image if no valid data
        img = Image.new('RGB', (ncols, nrows), color = 'black')
        img.save(output_filepath)
        return

    # Create a new RGB image with the dimensions of the matrix
    img = Image.new('RGB', (ncols, nrows))
    pixels = img.load() # Get a pixel access object

    # Iterate through each cell in the matrix and set the corresponding pixel color
    for r in range(nrows):
        for c in range(ncols):
            value = matrix_data[r][c]
            # if value > 2400:
            #     print(f'{r=}, {c=}, {value=}') 
            color = map_value_to_color(value, min_val, max_val, nodata_value)
            pixels[c, r] = color # PIL uses (x, y) where x is column, y is row

    try:
        img.save(output_filepath)
        print(f"Bitmap image successfully created and saved to '{output_filepath}'")
    except Exception as e:
        print(f"Error saving the image to '{output_filepath}': {e}")
        exit(1)

# Main execution block
if __name__ == "__main__":
    # Define input and output filenames
    input_filename = sys.argv[1]
    output_image_filename = input_filename.removesuffix('.asc') + '.png'

    # --- Step 1: Read the input matrix from the file ---
    print(f"\nReading matrix from '{input_filename}'...")
    original_ncols, original_nrows, nodata_val, original_matrix = read_ascii_matrix(input_filename)
    print(f"Original matrix dimensions: {original_nrows} rows x {original_ncols} columns")

    # --- Step 2: Convert the matrix to a bitmap image ---
    print(f"\nConverting matrix to bitmap image '{output_image_filename}'...")
    create_bitmap_from_matrix(original_matrix, original_ncols, original_nrows, nodata_val, output_image_filename)
