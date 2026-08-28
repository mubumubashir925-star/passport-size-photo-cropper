"""
Passport Image Cropper for Mobile-Captured Images
Removes borders, table backgrounds, and white space from passport photos
Captured via mobile phone

Requirements: PIL/Pillow, NumPy, SciPy, scikit-image (all available on your system)

Usage:
    python passport_cropper.py <input_folder> <output_folder>
    
Or run without arguments for interactive mode (will prompt for paths)
"""

import os
import sys
import numpy as np
from PIL import Image
from skimage.filters import threshold_otsu, sobel
from skimage.morphology import binary_closing, binary_opening, disk
from skimage.measure import label, regionprops
from scipy import ndimage
from pathlib import Path

# Python 2/3 compatibility
try:
    input = raw_input
except NameError:
    pass


def crop_passport_photo(input_path, output_path, remove_white_bg=True, detect_edges=True):
    """
    Main function to crop passport photo from mobile-captured image
    Removes borders, table background, and white space
    
    Args:
        input_path: Path to input image
        output_path: Path to save cropped image
        remove_white_bg: Whether to remove white borders
        detect_edges: Whether to auto-detect document edges
    """
    # Load image
    img = Image.open(input_path).convert('RGB')
    img_array = np.array(img)
    
    if detect_edges:
        # Step 1: Convert to grayscale for edge detection
        gray = np.mean(img_array, axis=2)
        
        # Step 2: Detect edges using Sobel operator
        edges = sobel(gray)
        
        # Step 3: Apply threshold to get binary edge map
        threshold = threshold_otsu(edges)
        binary_edges = edges > (threshold * 0.5)  # Lower threshold for better detection
        
        # Step 4: Morphological operations to connect edges
        selem = disk(5)  # Larger structuring element
        closed = binary_closing(binary_edges, selem)
        opened = binary_opening(closed, disk(3))
        
        # Step 5: Find contours/regions
        labeled = label(opened)
        regions = regionprops(labeled)
        
        # Find the largest rectangular region (likely the document/photo)
        largest_region = None
        max_area = 0
        
        for region in regions:
            area = region.area
            # Look for significant regions but not the entire image
            if area > max_area and area > 1000 and area < img_array.shape[0] * img_array.shape[1] * 0.95:
                max_area = area
                largest_region = region
        
        # If we found a region, use its bounding box
        if largest_region is not None:
            bbox = largest_region.bbox
            y_min, x_min, y_max, x_max = bbox
            
            # Refine edges by checking gradient magnitude
            x_min, x_max, y_min, y_max = refine_edges(img_array, x_min, y_min, x_max, y_max)
            
            # Crop to detected region
            cropped = img_array[y_min:y_max, x_min:x_max]
        else:
            # Fallback: try direct white border removal
            cropped = remove_white_borders(img_array, threshold=245)
            # If that didn't help much, use entire image
            if cropped.size == img_array.size:
                cropped = img_array
    else:
        cropped = img_array
    
    # Step 6: Remove white borders and background (always apply this)
    if remove_white_bg:
        cropped = remove_white_borders(cropped, threshold=240)
    
    # Step 7: Convert back to PIL Image and save
    result_img = Image.fromarray(cropped)
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Save with high quality
    result_img.save(output_path, 'JPEG', quality=95, dpi=(300, 300))
    return True


def refine_edges(img_array, x_min, y_min, x_max, y_max, margin=5):
    """
    Refine the detected edges by analyzing pixel intensity gradients
    """
    height, width = img_array.shape[:2]
    
    # Expand search area slightly
    x_min = max(0, x_min - margin)
    y_min = max(0, y_min - margin)
    x_max = min(width, x_max + margin)
    y_max = min(height, y_max + margin)
    
    # Analyze edges to find actual document boundaries
    # Check top edge
    for y in range(y_min, min(y_min + 50, y_max)):
        row = img_array[y, x_min:x_max]
        if np.std(row) > 20:  # Found content
            y_min = y
            break
    
    # Check bottom edge
    for y in range(max(y_min, y_max - 50), y_max, -1):
        row = img_array[y, x_min:x_max]
        if np.std(row) > 20:  # Found content
            y_max = y
            break
    
    # Check left edge
    for x in range(x_min, min(x_min + 50, x_max)):
        col = img_array[y_min:y_max, x]
        if np.std(col) > 20:  # Found content
            x_min = x
            break
    
    # Check right edge
    for x in range(max(x_min, x_max - 50), x_max, -1):
        col = img_array[y_min:y_max, x]
        if np.std(col) > 20:  # Found content
            x_max = x
            break
    
    return x_min, x_max, y_min, y_max


def remove_white_borders(img_array, threshold=240):
    """
    Remove white borders from the image by finding content boundaries
    Works with both light-on-dark and dark-on-light scenarios
    """
    if len(img_array.shape) == 3:
        # Convert to grayscale for border detection
        gray = np.mean(img_array, axis=2)
    else:
        gray = img_array
    
    height, width = gray.shape
    
    # Calculate statistics to determine background type
    mean_val = np.mean(gray)
    std_val = np.std(gray)
    
    # Check if background is likely white (high values) or dark (low values)
    edge_pixels = np.concatenate([
        gray[0, :], gray[-1, :], 
        gray[:, 0], gray[:, -1]
    ])
    edge_mean = np.mean(edge_pixels)
    
    # Determine if we have a contrasting background
    # If edges are significantly different from center, crop them
    if edge_mean > threshold:
        # White/light background - find where content starts
        # Top
        top = 0
        for y in range(height):
            if np.any(gray[y, :] < threshold):
                top = y
                break
        
        # Bottom
        bottom = height
        for y in range(height - 1, -1, -1):
            if np.any(gray[y, :] < threshold):
                bottom = y + 1
                break
        
        # Left
        left = 0
        for x in range(width):
            if np.any(gray[:, x] < threshold):
                left = x
                break
        
        # Right
        right = width
        for x in range(width - 1, -1, -1):
            if np.any(gray[:, x] < threshold):
                right = x + 1
                break
    elif edge_mean < (threshold - 50):
        # Dark background - find where lighter content starts
        # Top
        top = 0
        for y in range(height):
            if np.any(gray[y, :] > (edge_mean + 30)):
                top = y
                break
        
        # Bottom
        bottom = height
        for y in range(height - 1, -1, -1):
            if np.any(gray[y, :] > (edge_mean + 30)):
                bottom = y + 1
                break
        
        # Left
        left = 0
        for x in range(width):
            if np.any(gray[:, x] > (edge_mean + 30)):
                left = x
                break
        
        # Right
        right = width
        for x in range(width - 1, -1, -1):
            if np.any(gray[:, x] > (edge_mean + 30)):
                right = x + 1
                break
    else:
        # Mixed or unclear background - use standard deviation method
        # Find rows/cols with significant variation (indicating content)
        row_std = np.std(gray, axis=1)
        col_std = np.std(gray, axis=0)
        
        # Find first and last rows/cols with significant variation
        threshold_std = std_val * 0.3
        
        top = 0
        for y in range(height):
            if row_std[y] > threshold_std:
                top = max(0, y - 5)
                break
        
        bottom = height
        for y in range(height - 1, -1, -1):
            if row_std[y] > threshold_std:
                bottom = min(height, y + 6)
                break
        
        left = 0
        for x in range(width):
            if col_std[x] > threshold_std:
                left = max(0, x - 5)
                break
        
        right = width
        for x in range(width - 1, -1, -1):
            if col_std[x] > threshold_std:
                right = min(width, x + 6)
                break
    
    # Crop to content
    cropped = img_array[top:bottom, left:right]
    
    # Ensure minimum size (at least 100x100)
    if cropped.shape[0] < 100 or cropped.shape[1] < 100:
        return img_array
    
    return cropped


def process_folder(input_folder, output_folder, remove_white_bg=True, detect_edges=True):
    """
    Process all images in a folder
    """
    # Get image files
    image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')
    image_files = [f for f in os.listdir(input_folder) 
                  if f.lower().endswith(image_extensions)]
    
    if not image_files:
        print("No images found in input folder!")
        return False
    
    total = len(image_files)
    success_count = 0
    
    print("Found {} images to process...".format(total))
    
    for idx, filename in enumerate(image_files):
        input_file = os.path.join(input_folder, filename)
        output_file = os.path.join(output_folder, filename)
        
        try:
            print("[{}/{}] Processing: {}...".format(idx+1, total, filename), end=" ")
            crop_passport_photo(input_file, output_file, remove_white_bg, detect_edges)
            success_count += 1
            print("Done!")
        except Exception as e:
            print("Error: {}".format(str(e)))
    
    print("\nCompleted! Successfully processed: {}/{} images".format(success_count, total))
    return True


def main():
    print("=" * 60)
    print("Passport Photo Cropper - Mobile Capture Edition")
    print("=" * 60)
    print()
    print("This tool removes borders, table backgrounds, and white space")
    print("from passport photos captured via mobile phone.")
    print()
    
    # Check command line arguments
    if len(sys.argv) >= 3:
        input_folder = sys.argv[1]
        output_folder = sys.argv[2]
    else:
        # Interactive mode
        print("Please enter the paths:")
        input_folder = input("Input folder (containing images): ").strip()
        output_folder = input("Output folder (for cropped images): ").strip()
    
    # Validate input folder
    if not os.path.isdir(input_folder):
        print("Error: Input folder '{}' does not exist!".format(input_folder))
        sys.exit(1)
    
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print("Created output folder: {}".format(output_folder))
    
    # Process images
    print()
    process_folder(input_folder, output_folder)
    print()
    print("Press Enter to exit...")
    input()


if __name__ == "__main__":
    main()
