import sys
import math
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
            
            # Write matrix data row by row, formatted as integers (0, 1, or -9999)
            for row in matrix_data:
                # Use a generator expression for efficient string joining
                f.write(" ".join([f"{int(val)}" for val in row]) + "\n")
    except Exception as e:
        print(f"An error occurred while writing the file to '{filepath}': {e}")
        exit(1)

def manhattan_distance(p1, p2):
    return abs(p2[0] - p1[0]) + abs(p2[1] - p1[1])

def euclidean_distance(p1, p2):
    """
    Calculates the Euclidean distance between two 2D points (row, col).

    Args:
        p1 (tuple): First point (row1, col1).
        p2 (tuple): Second point (row2, col2).

    Returns:
        float: The Euclidean distance.
    """
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)


def calculate_peak_dominance(matrix_data, ncols, nrows, nodata_value, peak_row, peak_col):
    """
    Calculates dominance for each cell relative to a specified peak using a
    "higher border cells" approach.

    A cell is considered dominated by this peak if there are no higher cells
    closer to the current cell than this peak using an euclidean distance.
    This is optimized by only checking against "border" cells of higher regions.

    Args:
        matrix_data (list): The original 2D list representing the matrix.
        ncols (int): Original number of columns.
        nrows (int): Original number of rows.
        nodata_value (float): The value to ignore.
        peak_row (int): The row index of the peak (0-indexed).
        peak_col (int): The column index of the peak (0-indexed).

    Returns:
        list: A 2D list representing the dominance matrix (1, 0, or -9999).
    """
    # Validate peak coordinates
    if not (0 <= peak_row < nrows and 0 <= peak_col < ncols):
        print(f"Error: Peak coordinates ({peak_row}, {peak_col}) are out of bounds "
              f"for matrix dimensions ({nrows} rows x {ncols} columns).")
        exit(1)

    output_matrix = [[nodata_value for _ in range(ncols)] for _ in range(nrows)]
    
    peak_value = matrix_data[peak_row][peak_col]

    # Handle case where the peak itself is NODATA_value
    if peak_value == nodata_value:
        print(f"Warning: The specified peak at ({peak_row}, {peak_col}) is a NODATA_value. "
              "No cells can be dominated by a NODATA peak. Output will be mostly 0s or -9999s.")
        for r in range(nrows):
            for c in range(ncols):
                if matrix_data[r][c] == nodata_value:
                    output_matrix[r][c] = nodata_value
                else:
                    output_matrix[r][c] = 0 # Valid data cells are not dominated by a NODATA peak
        return output_matrix

    # Define possible neighbor offsets (8 directions: horizontal, vertical, and diagonals)
    dr = [-1, -1, -1, 0, 0, 1, 1, 1]
    dc = [-1, 0, 1, -1, 1, -1, 0, 1]

    # --- Step 1: Identify all cells strictly higher than the peak value ---
    higher_border_cells = set()
    for r in range(nrows):
        print('Border:', r, '/', nrows)
        for c in range(ncols):
            if matrix_data[r][c] == nodata_value or matrix_data[r][c] <= peak_value:
                continue

            is_border = False
            for i in range(8):
                nr, nc = r + dr[i], c + dc[i]
                
                # Check if neighbor is out of bounds (considered a border)
                if not (0 <= nr < nrows and 0 <= nc < ncols):
                    is_border = True
                    break
                
                neighbor_value = matrix_data[nr][nc]
                
                # Check if neighbor is NODATA or not strictly higher than peak_value
                if neighbor_value == nodata_value or neighbor_value <= peak_value:
                    is_border = True
                    break
            
            if is_border:
                higher_border_cells.add((r, c))
    
    higher_border_cells = list(higher_border_cells)
    print(len(higher_border_cells), ' cells in border higher than ', peak_value)

    # --- Step 3: Calculate dominance for each cell ---
    for r in range(nrows):
        print('Dom:', r, '/', nrows)
        for c in range(ncols):
            row_value, is_dominated = adapt_value_based_on_dominance(matrix_data, r, c, nodata_value, peak_row, peak_col, higher_border_cells)
            output_matrix[r][c] = -row_value if is_dominated else row_value
            #output_matrix[r][c] = nodata_val if matrix_data[r][c] == nodata_val else 100 if (r, c) in higher_border_cells else nodata_val

    return output_matrix


def adapt_value_based_on_dominance(matrix_data, r, c, nodata_value, peak_row, peak_col, higher_border_cells):
    current_cell_value = matrix_data[r][c]

    # Case 1: NODATA_value cell
    if current_cell_value == nodata_value:
        return nodata_value, False

    # Case 2: The peak cell itself
    if r == peak_row and c == peak_col:
        return nodata_value, False

    # Case 3: Valid data cell (not the peak)
    dist_to_peak = euclidean_distance((r, c), (peak_row, peak_col))
    manhattan_sup = math.ceil(dist_to_peak)

    # If there are no higher border cells, then this cell is dominated
    if not higher_border_cells:
        return current_cell_value, False

    # Iterate through the higher border cells to check for violating conditions
    for br, bc in higher_border_cells:
        man_dist_to_border_cell = manhattan_distance((r, c), (br, bc))
        # print(f'{r=}, {c=} vs {br=}, {bc=}, {manhattan_sup}')
        if man_dist_to_border_cell > manhattan_sup:
            #print('skip')
            continue
        
        dist_to_border_cell = euclidean_distance((r, c), (br, bc))
        
        # If a higher border cell is found closer than the peak,
        # then the current cell is NOT dominated by the peak.
        if dist_to_border_cell < dist_to_peak:
            return current_cell_value, False

    return current_cell_value, True


# Main execution block
if __name__ == "__main__":
    # Define input and output filenames
    input_filename = sys.argv[1]
    output_dominance_filename = sys.argv[2]
    peak_row_id = int(sys.argv[4])
    peak_col_id = int(sys.argv[3])

    # --- Step 1: Read the input matrix from the file ---
    print(f"\nReading matrix from '{input_filename}'...")
    original_ncols, original_nrows, nodata_val, original_matrix = read_ascii_matrix(input_filename)
    print(f"Original matrix dimensions: {original_nrows} rows x {original_ncols} columns")
    print(f"Selected peak at (row={peak_row_id}, col={peak_col_id}) with value: {original_matrix[peak_row_id][peak_col_id]}")

    # --- Step 2: Calculate the dominance matrix ---
    print(f"\nCalculating dominance matrix relative to peak ({peak_row_id}, {peak_col_id})...")
    dominance_mat = calculate_peak_dominance(
        original_matrix, original_ncols, original_nrows, nodata_val, peak_row_id, peak_col_id
    )
    print("Dominance calculation complete.")

    # --- Step 3: Write the dominance matrix to an output file ---
    print(f"\nWriting dominance matrix to '{output_dominance_filename}'...")
    write_ascii_matrix(output_dominance_filename, dominance_mat, original_ncols, original_nrows, nodata_val)
    print(f"Dominance matrix successfully written to '{output_dominance_filename}'")

    # --- Optional: Print the content of the output file to the console ---
    print(f"\n--- Content of '{output_dominance_filename}' ---")
    try:
        with open(output_dominance_filename, 'r') as f:
            print(f.read())
    except Exception as e:
        print(f"Could not read output file for display: {e}")
    print("----------------------------------------")
