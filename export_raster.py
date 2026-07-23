"""
Exports a georeferenced NDVI raster (GeoTIFF) for a single date over
a given field, so spatial variability within the field can be
inspected in QGIS (not just the field-average value from the time
series script).

Usage:
1. Run 'calculate_ndvi.py' first and check 'ndvi_time_series.csv'
   to pick a date of interest (e.g. the peak-vigor date).
2. Set TARGET_DATE below to that date.
3. Run this script -> it prints a download URL.
4. Open the URL in your browser to download 'ndvi_raster.tif'.
5. In QGIS: Layer -> Add Layer -> Add Raster Layer -> select the file.
"""

import ee
import pandas as pd

# ---------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------

PROJECT_ID = "ndvi-agro"

# Date you want to export as a raster (pick from ndvi_time_series.csv
# after running calculate_ndvi.py)
TARGET_DATE = "2025-12-27"

FIELD_GEOJSON = {
    "type": "Polygon",
    "coordinates": [[
        [-51.9175746, -18.1807401],
        [-51.9020517, -18.189363],
        [-51.8930603, -18.1852531],
        [-51.8705818, -18.161478],
        [-51.8769436, -18.1559972],
        [-51.8752471, -18.1524507],
        [-51.8840689, -18.1524507],
        [-51.886444, -18.1520477],
        [-51.898998, -18.1457605],
        [-51.9051054, -18.1456799],
        [-51.9051902, -18.1500326],
        [-51.9147754, -18.174454],
        [-51.9175746, -18.1807401],
    ]]
}

# ---------------------------------------------------------------
# CONNECTION AND EXPORT
# ---------------------------------------------------------------

ee.Initialize(project=PROJECT_ID)
field = ee.Geometry.Polygon(FIELD_GEOJSON["coordinates"])


def mask_clouds(image):
    """
    Uses the Scene Classification Layer (SCL) to mask out clouds,
    cloud shadows, and snow at the pixel level.
    """
    scl = image.select("SCL")
    mask = (
        scl.neq(3).And(scl.neq(8)).And(scl.neq(9))
        .And(scl.neq(10)).And(scl.neq(11))
    )
    return image.updateMask(mask)


def compute_ndvi(image):
    ndvi = image.normalizedDifference(["B8", "B4"]).rename("NDVI")
    return image.addBands(ndvi)


next_date = (pd.Timestamp(TARGET_DATE) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")

image = (
    ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
    .filterBounds(field)
    .filterDate(TARGET_DATE, next_date)
    .map(mask_clouds)
    .map(compute_ndvi)
    .first()
)

if image is None:
    raise SystemExit(f"No image found for {TARGET_DATE}. Check the date exists in your time series CSV.")

ndvi_image = image.select("NDVI").clip(field)

download_url = ndvi_image.getDownloadURL({
    "scale": 10,
    "region": field,
    "format": "GEO_TIFF",
})

print(f"NDVI raster for {TARGET_DATE}")
print("Download URL:")
print(download_url)
print(
    "\nOpen this URL in your browser to download 'ndvi_raster.tif'.\n"
    "Then in QGIS: Layer -> Add Layer -> Add Raster Layer -> select the file."
)
