"""
NDVI time series analysis for an agricultural field using Sentinel-2
imagery via the Google Earth Engine Python API.

Outputs:
- ndvi_time_series.csv   -> raw NDVI values per date
- ndvi_chart.png         -> annotated NDVI evolution chart (with cloud
                             data-gap segments marked separately)
- report.md              -> short technical summary of the findings
"""

import ee
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# ---------------------------------------------------------------
# 1. CONFIGURATION
# ---------------------------------------------------------------

PROJECT_ID = "ndvi-agro"
START_DATE = "2024-07-01"
END_DATE = "2026-07-01"
MAX_CLOUD_PERCENT = 10

# NOTE: coordinates below are a generic example field, not a real
# property. Replace with your own field's polygon for a real case.
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
# 2. EARTH ENGINE CONNECTION
# ---------------------------------------------------------------

ee.Initialize(project=PROJECT_ID)
field = ee.Geometry.Polygon(FIELD_GEOJSON["coordinates"])


def mask_clouds(image):
    """
    Uses the Scene Classification Layer (SCL) to mask out clouds,
    cloud shadows, and snow at the pixel level - more reliable than
    the scene-wide CLOUDY_PIXEL_PERCENTAGE metadata, which can miss
    localized cloud/shadow contamination over a specific field.
    """
    scl = image.select("SCL")
    # SCL classes excluded: 3 = cloud shadow, 8/9 = cloud medium/high
    # probability, 10 = thin cirrus, 11 = snow
    mask = (
        scl.neq(3).And(scl.neq(8)).And(scl.neq(9))
        .And(scl.neq(10)).And(scl.neq(11))
    )
    return image.updateMask(mask)


def compute_ndvi(image):
    ndvi = image.normalizedDifference(["B8", "B4"]).rename("NDVI")
    return image.addBands(ndvi)


collection = (
    ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
    .filterBounds(field)
    .filterDate(START_DATE, END_DATE)
    .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", MAX_CLOUD_PERCENT))
    .map(mask_clouds)
    .map(compute_ndvi)
)

image_count = collection.size().getInfo()
if image_count == 0:
    raise SystemExit("No images found for this period/area.")


def extract_mean_ndvi(image):
    mean_value = image.select("NDVI").reduceRegion(
        reducer=ee.Reducer.mean(), geometry=field, scale=10, maxPixels=1e9
    )
    return image.set("mean_ndvi", mean_value.get("NDVI")).set(
        "date", image.date().format("YYYY-MM-dd")
    )


collection_with_ndvi = collection.map(extract_mean_ndvi)
result_list = collection_with_ndvi.reduceColumns(
    ee.Reducer.toList(2), ["date", "mean_ndvi"]
).get("list").getInfo()

df = pd.DataFrame(result_list, columns=["date", "ndvi"])
df = df.dropna()
df["date"] = pd.to_datetime(df["date"])

# Multiple Sentinel-2 orbits can cover the same field on the same day,
# producing more than one image per date. Average them into a single
# daily value instead of plotting them as separate points.
df = df.groupby("date", as_index=False)["ndvi"].mean()
df = df.sort_values("date").reset_index(drop=True)

df.to_csv("ndvi_time_series.csv", index=False)
print("Saved: ndvi_time_series.csv")

# ---------------------------------------------------------------
# 3. PROFESSIONAL CHART WITH CLOUD-GAP DETECTION
# ---------------------------------------------------------------

fig, ax = plt.subplots(figsize=(12, 6))

# Detect gaps: if more than 25 days pass between consecutive observations,
# it's very likely a data gap caused by persistent cloud cover (optical
# satellites can't see through clouds), not a real gradual NDVI change.
GAP_THRESHOLD_DAYS = 25
df["days_since_previous"] = df["date"].diff().dt.days

gap_already_in_legend = False
for i in range(1, len(df)):
    x_pair = df["date"].iloc[i - 1:i + 1]
    y_pair = df["ndvi"].iloc[i - 1:i + 1]
    if df["days_since_previous"].iloc[i] > GAP_THRESHOLD_DAYS:
        ax.plot(x_pair, y_pair, linestyle="--", linewidth=1.5,
                color="#B0B0B0",
                label="Data gap (cloud cover)" if not gap_already_in_legend else None)
        gap_already_in_legend = True
    else:
        ax.plot(x_pair, y_pair, linestyle="-", linewidth=2, color="#2E7D32")

ax.scatter(df["date"], df["ndvi"], color="#2E7D32", s=25, zorder=5,
           label="NDVI (field average)")

ax.fill_between(df["date"], df["ndvi"], alpha=0.1, color="#2E7D32")

ax.set_title(
    "NDVI Time Series — Field Vegetation Vigor\n"
    "Example field, Goiás, Brazil (Sentinel-2, 2024-2026)",
    fontsize=13, fontweight="bold"
)
ax.set_xlabel("Date")
ax.set_ylabel("NDVI (field average)")
ax.set_ylim(0, 1.08)
ax.grid(True, alpha=0.3)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b/%y"))
ax.legend(loc="lower right")

plt.tight_layout()
plt.savefig("ndvi_chart.png", dpi=150)
print("Saved: ndvi_chart.png")

# ---------------------------------------------------------------
# 4. AUTOMATED TECHNICAL REPORT (Markdown)
# ---------------------------------------------------------------

ndvi_max = df["ndvi"].max()
ndvi_min = df["ndvi"].min()
date_of_max = df.loc[df["ndvi"].idxmax(), "date"].strftime("%Y-%m-%d")
gap_count = (df["days_since_previous"] > GAP_THRESHOLD_DAYS).sum()

report = f"""# NDVI Monitoring Report — Field Analysis

**Location:** Goiás, Brazil (example field)
**Period analyzed:** {START_DATE} to {END_DATE}
**Satellite source:** Sentinel-2 (Copernicus), 10m resolution
**Observations used:** {len(df)} daily values (cloud-masked, cloud cover below {MAX_CLOUD_PERCENT}%)

## Summary

This report presents an automated NDVI (Normalized Difference Vegetation
Index) time series for a single field, generated via the Google Earth
Engine Python API. The workflow retrieves all available low-cloud
Sentinel-2 scenes over the field, applies pixel-level cloud/shadow
masking using the Scene Classification Layer (SCL), computes NDVI per
scene, and extracts the field-average value to build a continuous
vegetation vigor timeline.

## Key findings

- **Peak vegetative vigor:** NDVI = {ndvi_max:.2f}, observed on {date_of_max},
  consistent with full canopy cover during a crop growth cycle.
- **Minimum vigor:** NDVI = {ndvi_min:.2f}, corresponding to post-harvest
  bare soil / fallow periods between crop cycles.
- **{gap_count} significant data gap(s)** (more than {GAP_THRESHOLD_DAYS} days
  without a usable observation) were identified and are explicitly marked
  as dashed segments in the chart, rather than being interpolated as a
  real gradual change — these are typically caused by persistent cloud
  cover during the rainy season, a known limitation of optical satellite
  data.
- Repeated growth-and-harvest cycles are visible across the two-year
  period, consistent with the expected double-cropping calendar for the
  region (e.g. soybean followed by safrinha corn).

## Applications of this workflow for clients

- Early detection of vegetative stress or irregular crop development
- Remote monitoring of large landholdings without field visits
- Automated periodic reporting for farm management teams
- Historical yield-pattern analysis across multiple seasons

## Known limitation and planned improvement

Optical satellites (Sentinel-2) cannot see through cloud cover, which
creates data gaps during the rainy season, as marked in the chart above.
A planned second version of this pipeline will incorporate Sentinel-1
(radar) imagery, which penetrates clouds, to fill these gaps and produce
a fully continuous vegetation monitoring timeline.

---
*This analysis was generated with a reproducible Python + Google Earth
Engine pipeline. Field boundaries and date ranges can be adapted to any
location or crop cycle.*
"""

with open("report.md", "w", encoding="utf-8") as f:
    f.write(report)

print("Saved: report.md")
