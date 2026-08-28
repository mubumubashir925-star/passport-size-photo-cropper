# Passport Photo Cropper for Mobile-Captured Images

This tool removes borders, table backgrounds, and white space from passport photos captured via mobile phone.

## Features

- **Auto-detect document edges**: Uses edge detection to find the passport photo boundaries
- **Remove white borders**: Automatically crops out white space around the photo
- **Handle dark backgrounds**: Works with photos placed on dark tables/surfaces
- **Batch processing**: Process multiple images at once
- **No external dependencies beyond Python libraries**: Uses only PIL/Pillow, NumPy, SciPy, and scikit-image

## Requirements

The following Python libraries must be installed (all are commonly available):
- PIL/Pillow
- NumPy
- SciPy
- scikit-image

## Usage

### Command Line (Recommended for Windows 7)

```bash
python passport_cropper.py <input_folder> <output_folder>
```

Example:
```bash
python passport_cropper.py C:\passport_photos\input C:\passport_photos\output
```

### Interactive Mode

If you run without arguments, it will prompt for folder paths:

```bash
python passport_cropper.py
```

Then enter:
1. Input folder path (containing your mobile-captured passport photos)
2. Output folder path (where cropped images will be saved)

## How It Works

1. **Edge Detection**: Uses Sobel operator to detect edges in the image
2. **Morphological Operations**: Connects edge fragments to find document boundaries
3. **Content Detection**: Identifies the largest rectangular region (the passport photo)
4. **Border Removal**: Removes white or dark borders around the photo
5. **Smart Cropping**: Handles both light-on-dark and dark-on-light scenarios

## Example Scenarios

### Scenario 1: Passport photo on a table with visible table edges
- The tool detects the table edges and crops them out
- Only the passport photo area remains

### Scenario 2: Passport photo with white paper background
- White borders are automatically detected and removed
- Photo is cropped to content boundaries

### Scenario 3: Photo captured at an angle
- Edge detection finds the document boundaries
- Rectangular crop is applied

## Tips for Best Results

1. **Good lighting**: Ensure even lighting without harsh shadows
2. **Contrast**: Place the photo on a surface with contrasting color
3. **Straight capture**: Try to capture the photo as straight as possible
4. **High resolution**: Use higher resolution images for better edge detection

## Files

- `passport_cropper.py` - Main Python script
- `run_cropper.bat` - Windows batch file to run the cropper (modify paths as needed)

## Troubleshooting

**Issue**: No cropping happens
- Solution: Ensure there's sufficient contrast between the photo and background
- Try adjusting the threshold values in the code

**Issue**: Over-cropping (too much is removed)
- Solution: The minimum size protection should prevent this
- Check that the photo has clear boundaries

**Issue**: Under-cropping (borders remain)
- Solution: Increase the threshold value in `remove_white_borders()` function
- Try `threshold=230` instead of `threshold=240`

## License

Free to use and modify.
