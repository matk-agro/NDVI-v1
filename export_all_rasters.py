"""
Exports a georeferenced NDVI raster (GeoTIFF) for EVERY date in the
time series, downloading them automatically into a local folder.
This lets you load the full temporal progression as layers in QGIS
(e.g. to build an animation or compare growth stages side by side).

Requirements:
- Run 'calculate_ndvi.py' first, so 'ndvi_time_series.csv' exists.

Output:
- ndvi_rasters/ndvi_2024-07-03.tif
- ndvi_rasters/ndvi_2024-07-13.tif
- ... one file per date in the CSV
"""

import os
import ee
import pandas as pd
import requests

# ---------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------

PROJECT_ID = "ndvi-agro"
OUTPUT_FOLDER = "ndvi_rasters"

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
# CONNECTION
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


# ---------------------------------------------------------------
# READ THE LIST OF DATES FROM THE TIME SERIES CSV
# ---------------------------------------------------------------

if not os.path.exists("ndvi_time_series.csv"):
    raise SystemExit(
        "ndvi_time_series.csv not found. Run calculate_ndvi.py first."
    )

df = pd.read_csv("ndvi_time_series.csv")
dates = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d").tolist()

os.makedirs(OUTPUT_FOLDER, exist_ok=True)
print(f"Exporting {len(dates)} rasters to '{OUTPUT_FOLDER}/' ...\n")

# ---------------------------------------------------------------
# LOOP THROUGH EACH DATE, EXPORT AND DOWNLOAD THE RASTER
# ---------------------------------------------------------------

for i, date in enumerate(dates, start=1):
    file_path = os.path.join(OUTPUT_FOLDER, f"ndvi_{date}.tif")

    if os.path.exists(file_path):
        print(f"[{i}/{len(dates)}] {date} -> already downloaded, skipping.")
        continue

    next_date = (pd.Timestamp(date) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")

    image = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(field)
        .filterDate(date, next_date)
        .map(mask_clouds)
        .map(compute_ndvi)
        .first()
    )

    try:
        ndvi_image = image.select("NDVI").clip(field)

        url = ndvi_image.getDownloadURL({
            "scale": 10,
            "region": field,
            "format": "GEO_TIFF",
        })

        response = requests.get(url, timeout=60)
        response.raise_for_status()

        with open(file_path, "wb") as f:
            f.write(response.content)

        print(f"[{i}/{len(dates)}] {date} -> saved: {file_path}")

    except Exception as error:
        print(f"[{i}/{len(dates)}] {date} -> FAILED ({error})")

print("\nDone. Load the .tif files in QGIS as a raster layer stack")
print("(Layer -> Add Layer -> Add Raster Layer -> select multiple files).")
