# NDVI Monitoring Report — Field Analysis

**Location:** Goiás, Brazil (example field)
**Period analyzed:** 2024-07-01 to 2026-07-01
**Satellite source:** Sentinel-2 (Copernicus), 10m resolution
**Observations used:** 71 daily values (cloud-masked, cloud cover below 10%)

## Summary

This report presents an automated NDVI (Normalized Difference Vegetation
Index) time series for a single field, generated via the Google Earth
Engine Python API. The workflow retrieves all available low-cloud
Sentinel-2 scenes over the field, applies pixel-level cloud/shadow
masking using the Scene Classification Layer (SCL), computes NDVI per
scene, and extracts the field-average value to build a continuous
vegetation vigor timeline.

## Key findings

- **Peak vegetative vigor:** NDVI = 0.91, observed on 2025-12-25,
  consistent with full canopy cover during a crop growth cycle.
- **Minimum vigor:** NDVI = 0.14, corresponding to post-harvest
  bare soil / fallow periods between crop cycles.
- **7 significant data gap(s)** (more than 25 days
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
