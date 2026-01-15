import ee
from pathlib import Path
from datetime import datetime

from src.ingestion.load_mines import load_mine_polygons
from src.ingestion.sentinel_access import prepare_mine_aois

# =========================
# CONFIG
# =========================
START_DATE = "2022-01-01"
END_DATE = "2022-12-31"
MAX_CLOUD = 20
TARGET_SCALE = 10  # meters

# =========================
# INIT GEE
# =========================
def init_gee():
    ee.Initialize(project="adaptive-mining-monitoring")
    print("✅ GEE initialized")

# =========================
# CLOUD MASK
# =========================
def mask_clouds(image):
    scl = image.select("SCL")
    valid = (
        scl.eq(4)   # vegetation
        .Or(scl.eq(5))  # bare soil
        .Or(scl.eq(6))  # water
        .Or(scl.eq(7))  # unclassified
    )
    return image.updateMask(valid)

# =========================
# RESAMPLE TO 10m
# =========================
def resample_10m(image):
    return (
        image
        .resample("bilinear")
        .reproject(crs="EPSG:4326", scale=10)
    )

# =========================
# SEASON TAGGING
# =========================
def add_season(image):
    month = ee.Date(image.get("system:time_start")).get("month")
    season = ee.Algorithms.If(
        ee.Number(month).gte(5).And(ee.Number(month).lte(10)),
        "wet",
        "dry"
    )
    return image.set("season", season)

# =========================
# MAIN PIPELINE
# =========================
def main():
    init_gee()

    mines = load_mine_polygons("data/vectors/CILS_mines_polygon")
    aois = prepare_mine_aois(mines).head(5)

    print(f"Processing {len(aois)} mines")

    s2 = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterDate(START_DATE, END_DATE)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", MAX_CLOUD))
        .select(["B2", "B3", "B4", "B8", "B11", "B12", "SCL"])
        .map(mask_clouds)
        .map(resample_10m)
        .map(add_season)
    )

    for _, row in aois.iterrows():
        mine_id = row["mine_id"]
        geom = ee.Geometry.Polygon(list(row.geometry.exterior.coords))

        mine_ic = s2.filterBounds(geom)

        # -------------------------
        # SEASONAL BASELINES
        # -------------------------
        dry_baseline = (
            mine_ic
            .filter(ee.Filter.eq("season", "dry"))
            .median()
            .clip(geom)
        )

        wet_baseline = (
            mine_ic
            .filter(ee.Filter.eq("season", "wet"))
            .median()
            .clip(geom)
        )

        # -------------------------
        # NORMALIZATION
        # -------------------------
        def normalize(image):
            season = ee.String(image.get("season"))
            baseline = ee.Image(
        ee.Algorithms.If(
            season.compareTo("dry").eq(0),
            dry_baseline,
            wet_baseline
        )
    )
            return (
                image.subtract(baseline)
                .copyProperties(image, ["system:time_start", "season"])
            )

        normalized = mine_ic.map(normalize)

        # -------------------------
        # VALID PIXEL MASK
        # -------------------------
        valid_mask = (
            normalized
            .select("B8")
            .count()
            .gte(5)   # pixel must be valid in ≥5 timestamps
        )

        # -------------------------
        # STORE AS ASSET (OPTIONAL)
        # -------------------------
        print(f"✅ Phase 3 completed for {mine_id}")

    print("🎉 PHASE 3 FULLY COMPLETE")

if __name__ == "__main__":
    main()
