"""
Quick connectivity test for the Google Earth Engine Python API.
Confirms authentication and project configuration are working before
running the full analysis pipeline.
"""

import ee

# Replace with your own Earth Engine / Google Cloud project ID
PROJECT_ID = "ndvi-agro"

ee.Initialize(project=PROJECT_ID)

# Test: search for Sentinel-2 imagery over a sample point
test_point = ee.Geometry.Point([-54.6462, -20.4697])

collection = (
    ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
    .filterBounds(test_point)
    .filterDate("2026-01-01", "2026-06-01")
    .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
)

count = collection.size().getInfo()

print("Earth Engine connection OK.")
print(f"Sentinel-2 images found in the test area: {count}")
