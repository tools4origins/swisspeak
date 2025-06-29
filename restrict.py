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
            
            # Write matrix data row by row, formatted to 3 decimal places for general use
            # If values are strictly integers (like 0, 1, -9999), can use int(val)
            for row in matrix_data:
                f.write(" ".join([f"{val:.3f}" for val in row]) + "\n")
    except Exception as e:
        print(f"An error occurred while writing the file to '{filepath}': {e}")
        exit(1)

def combine_matrices(matrix1_data, ncols1, nrows1, nodata_value1,
                     matrix2_data, ncols2, nrows2, nodata_value2):
    """
    Combines two matrices based on a condition:
    For each cell, takes the value from the first file if and only if the value
    is not NODATA_value in the second file. Otherwise, it outputs NODATA_value1.

    Args:
        matrix1_data (list): 2D list of data from the first matrix.
        ncols1 (int): Columns of first matrix.
        nrows1 (int): Rows of first matrix.
        nodata_value1 (float): NODATA_value of the first matrix.
        matrix2_data (list): 2D list of data from the second matrix.
        ncols2 (int): Columns of second matrix.
        nrows2 (int): Rows of second matrix.
        nodata_value2 (float): NODATA_value of the second matrix.

    Returns:
        tuple: A tuple containing:
            - list: The combined 2D matrix data.
            - int: Number of columns of the combined matrix.
            - int: Number of rows of the combined matrix.
            - float: NODATA_value for the combined matrix (from matrix1).
    """
    if not (ncols1 == ncols2 and nrows1 == nrows2):
        print(f"Error: Input matrices must have the same dimensions. "
              f"Matrix 1: {nrows1}x{ncols1}, Matrix 2: {nrows2}x{ncols2}")
        exit(1)

    combined_matrix = []
    
    for r in range(nrows1):
        row_data = []
        for c in range(ncols1):
            value_from_matrix2 = matrix2_data[r][c]
            
            # Condition: if value in second file is NOT NODATA_value
            if value_from_matrix2 != nodata_value2:
                row_data.append(matrix1_data[r][c])
            else:
                # If value in second file IS NODATA_value, output NODATA_value from first file
                row_data.append(nodata_value1)
        combined_matrix.append(row_data)

    return combined_matrix, ncols1, nrows1, nodata_value1

# Main execution block
if __name__ == "__main__":
    input_file1 = sys.argv[1]
    input_file2 = sys.argv[2]
    output_combined_file = sys.argv[3]

    
    # --- Step 1: Read the input matrices ---
    print(f"\nReading matrix from '{input_file1}'...")
    ncols1, nrows1, nodata_val1, matrix1 = read_ascii_matrix(input_file1)
    print(f"Matrix 1 dimensions: {nrows1} rows x {ncols1} columns, NODATA: {nodata_val1}")

    print(f"\nReading matrix from '{input_file2}'...")
    ncols2, nrows2, nodata_val2, matrix2 = read_ascii_matrix(input_file2)
    print(f"Matrix 2 dimensions: {nrows2} rows x {ncols2} columns, NODATA: {nodata_val2}")

    # --- Step 2: Combine the matrices ---
    print(f"\nCombining matrices based on the condition...")
    combined_mat, combined_ncols, combined_nrows, combined_nodata_val = combine_matrices(
        matrix1, ncols1, nrows1, nodata_val1,
        matrix2, ncols2, nrows2, nodata_val2
    )
    print(f"Combined matrix dimensions: {combined_nrows} rows x {combined_ncols} columns")

    # --- Step 3: Write the combined matrix to an output file ---
    print(f"\nWriting combined matrix to '{output_combined_file}'...")
    write_ascii_matrix(output_combined_file, combined_mat, combined_ncols, combined_nrows, combined_nodata_val)
    print(f"Combined matrix successfully written to '{output_combined_file}'")

    # --- Optional: Print the content of the output file to the console ---
    print(f"\n--- Content of '{output_combined_file}' ---")
    try:
        with open(output_combined_file, 'r') as f:
            print(f.read())
    except Exception as e:
        print(f"Could not read output file for display: {e}")
    print("----------------------------------------")
