import sys
import os
from PIL import Image

def write_ascii_matrix(filepath, matrix_data, ncols, nrows, nodata_value):
    """
    Writes a matrix to an ASCII file with a standard header.

    Args:
        filepath (str): The path to the output ASCII file.
        matrix_data (list): The 2D list representing the matrix.
        ncols (int): Number of columns.
        nrows (int): Number of rows.
        nodata_value (int): NODATA_value (expected to be -9999 for this script).
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
            
            # Write matrix data row by row, formatted as integers
            for row in matrix_data:
                f.write(" ".join([f"{int(val)}" for val in row]) + "\n")
    except Exception as e:
        print(f"An error occurred while writing the file to '{filepath}': {e}")
        exit(1)

def convert_png_to_ascii_matrix(png_filepath, output_ascii_filepath, nodata_value=-9999):
    """
    Converts a PNG image to an ASCII matrix file.
    Transparent pixels (alpha=0) are mapped to nodata_value (-9999).
    Opaque pixels are mapped to 1.

    Args:
        png_filepath (str): Path to the input PNG file.
        output_ascii_filepath (str): Path to the output ASCII matrix file.
        nodata_value (int): The value to use for transparent pixels. Defaults to -9999.
    """
    try:
        img = Image.open(png_filepath)
        
        # Ensure the image has an alpha channel, convert if necessary
        if img.mode != 'RGBA':
            print(f"Warning: Image '{png_filepath}' does not have an alpha channel. "
                  "Assuming all pixels are opaque for conversion.")
            img = img.convert('RGBA') # Convert to RGBA to ensure alpha is present (will be 255 for all if no original alpha)

        ncols, nrows = img.size
        ascii_matrix = []

        # Iterate through pixels and build the matrix
        for r in range(nrows):
            row_data = []
            for c in range(ncols):
                # Get the pixel data (R, G, B, A)
                # img.getpixel((c, r)) returns a tuple, e.g., (255, 255, 255, 255) for white opaque
                # or (0, 0, 0, 0) for black transparent.
                pixel = img.getpixel((c, r))
                alpha = pixel[3] # Alpha channel is the 4th element (index 3)

                if alpha == 0: # Check for transparency
                    row_data.append(nodata_value)
                else:
                    row_data.append(1) # Opaque pixel
            ascii_matrix.append(row_data)

        # Write the generated matrix to the output ASCII file
        write_ascii_matrix(output_ascii_filepath, ascii_matrix, ncols, nrows, nodata_value)
        print(f"Successfully converted '{png_filepath}' to '{output_ascii_filepath}'.")

    except FileNotFoundError:
        print(f"Error: PNG file not found at '{png_filepath}'. Please check the path.")
        exit(1)
    except Exception as e:
        print(f"An unexpected error occurred during PNG conversion: {e}")
        exit(1)

# Main execution block
if __name__ == "__main__":
    input_png_filename = sys.argv[1]
    output_ascii_filename = input_png_filename.removesuffix('.png') + '.from_image.asc'
    default_nodata_value = -9999

    # --- Convert the dummy PNG to an ASCII matrix ---
    print(f"\nConverting '{input_png_filename}' to '{output_ascii_filename}'...")
    convert_png_to_ascii_matrix(input_png_filename, output_ascii_filename, default_nodata_value)

    # --- Optional: Print the content of the output ASCII file to the console ---
    print(f"\n--- Content of '{output_ascii_filename}' ---")
    try:
        with open(output_ascii_filename, 'r') as f:
            print(f.read())
    except Exception as e:
        print(f"Could not read output file for display: {e}")
    print("----------------------------------------")

    # --- Optional: Clean up the dummy input PNG file ---
    # Uncomment the following lines if you want to remove the input file after execution.
    # try:
    #     os.remove(input_png_filename)
    #     print(f"\nCleaned up dummy input PNG file: '{input_png_filename}'")
    # except OSError as e:
    #     print(f"Error removing dummy input PNG file '{input_png_filename}': {e}")