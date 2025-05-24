# APE: AMD Protocol Explorer Assets

This directory contains assets used by the APE application.

## Logo Files

### ape_logo.svg (Primary)

The app will first look for an SVG logo file named `ape_logo.svg`. SVG is preferred because:
- It scales perfectly to any size without quality loss
- It typically has a smaller file size
- It supports transparency

### ape_logo.jpg (Fallback)

If the SVG file is not found, the app will look for `ape_logo.jpg` as a fallback.

## Logo Priority

The application uses the following priority order for logos:
1. `ape_logo.svg` (preferred)
2. `ape_logo.jpg` (fallback)
3. Ape emoji (🦧) if no logo files are found

## Changing the Logo

If you want to use a different image file:

1. Save your logo image in this directory
2. Update the file paths in `app.py` to match your new filename

## Logo Requirements

For best results:

- Use a square or nearly square aspect ratio
- Include some transparent background space for better appearance
- For SVG: Ensure the file is properly optimized
- For JPG/PNG: Recommended dimensions of 400x400 pixels or larger

## Supported Formats

- SVG (preferred for scalability)
- PNG (good for transparency)
- JPG (acceptable, but lacks transparency)