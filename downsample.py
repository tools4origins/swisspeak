import sys
import os

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
            for i, line in enumerate(f):
                print(i, '/', nrows)
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

def downsample_matrix(matrix_data, ncols, nrows, nodata_value, factor):
    """
    Downsamples a matrix by averaging values within blocks of 'factor' x 'factor' size.
    NODATA_value entries are ignored during the averaging calculation.

    Args:
        matrix_data (list): The original 2D list representing the matrix.
        ncols (int): Original number of columns.
        nrows (int): Original number of rows.
        nodata_value (float): The value to ignore during averaging.
        factor (int): The downsampling factor (e.g., 2 for 2x2 blocks).

    Returns:
        tuple: A tuple containing:
            - list: The downsampled 2D list.
            - int: New number of columns.
            - int: New number of rows.
    """
    if not isinstance(factor, int) or factor <= 0:
        print("Error: Downsampling factor must be a positive integer.")
        exit(1)

    # Calculate the dimensions of the new downsampled matrix
    # Integer division ensures whole blocks
    new_nrows = nrows // factor
    new_ncols = ncols // factor

    if new_nrows == 0 or new_ncols == 0:
        print(f"Error: Downsampling factor {factor} is too large. "
              f"Original dimensions ({nrows}x{ncols}) result in zero new rows/columns.")
        exit(1)

    # Initialize the downsampled matrix with NODATA_value
    downsampled_matrix = [[nodata_value for _ in range(new_ncols)] for _ in range(new_nrows)]

    # Iterate through each block in the original matrix to calculate its average
    for r in range(new_nrows):
        print(r, "/", new_nrows)
        for c in range(new_ncols):
            block_sum = 0.0
            valid_count = 0
            
            # Define the boundaries of the current block in the original matrix
            start_row = r * factor
            end_row = (r + 1) * factor
            start_col = c * factor
            end_col = (c + 1) * factor

            max_val = nodata_value

            # Iterate over the cells within the current block
            for i in range(start_row, end_row):
                for j in range(start_col, end_col):
                    # Ensure indices are within the bounds of the original matrix
                    # This handles cases where original dimensions might not be perfect multiples
                    # of the factor, though the problem implies they will be.
                    if i < nrows and j < ncols:
                        value = matrix_data[i][j]
                        # Only include valid values in the sum and count
                        if value != nodata_value:
                            block_sum += value
                            valid_count += 1
                            max_value = max(max_val, value)
            
            # Calculate the average for the block
            if valid_count > 0:
                downsampled_matrix[r][c] = max_value # block_sum / valid_count
            else:
                # If all values in the block were NODATA, the result for this cell is NODATA
                downsampled_matrix[r][c] = nodata_value
                
    return downsampled_matrix, new_ncols, new_nrows

def write_ascii_matrix(filepath, matrix_data, ncols, nrows, nodata_value):
    """
    Writes a matrix to an ASCII file with a standard header.

    Args:
        filepath (str): The path to the output ASCII file.
        matrix_data (list): The 2D list representing the matrix.
        ncols (int): Number of columns.
        nrows (int): Number of rows.
        nodata_value (float): NODATA_value.
    """
    try:
        with open(filepath, 'w') as f:
            # Write header information
            f.write(f"ncols        {ncols}\n")
            f.write(f"nrows        {nrows}\n")
            f.write(f"NODATA_value {nodata_value}\n")
            f.write(f"xllcorner N/A\n")
            f.write(f"yllcorner N/A\n")
            f.write(f"cellsize N/A\n")
            
            # Write matrix data row by row, formatted to 3 decimal places
            for row in matrix_data:
                # Use a generator expression for efficient string joining
                f.write(" ".join([f"{val:.3f}" for val in row]) + "\n")
    except Exception as e:
        print(f"An error occurred while writing the file to '{filepath}': {e}")
        exit(1)

# Main execution block
if __name__ == "__main__":
    # Define input and output filenames and the downsampling factor
    input_filename = sys.argv[1]
    output_filename = sys.argv[2]
    downsample_factor = sys.argv[2] if len(sys.argv) > 3 else 10

    # --- Step 1: Read the input matrix from the file ---
    print(f"\nReading matrix from '{input_filename}'...")
    original_ncols, original_nrows, nodata_val, original_matrix = read_ascii_matrix(input_filename)
    print(f"Original matrix dimensions: {original_nrows} rows x {original_ncols} columns")

    # --- Step 2: Downsample the matrix ---
    print(f"\nDownsampling matrix by a factor of {downsample_factor}...")
    downsampled_mat, new_ncols, new_nrows = downsample_matrix(
        original_matrix, original_ncols, original_nrows, nodata_val, downsample_factor
    )
    print(f"Downsampled matrix dimensions: {new_nrows} rows x {new_ncols} columns")

    # --- Step 3: Write the downsampled matrix to an output file ---
    print(f"\nWriting downsampled matrix to '{output_filename}'...")
    write_ascii_matrix(output_filename, downsampled_mat, new_ncols, new_nrows, nodata_val)
    print(f"Downsampled matrix successfully written to '{output_filename}'")

    # --- Optional: Print the content of the output file to the console ---
    print(f"\n--- Content of '{output_filename}' ---")
    try:
        with open(output_filename, 'r') as f:
            print(f.read())
    except Exception as e:
        print(f"Could not read output file for display: {e}")
    print("----------------------------------------")
