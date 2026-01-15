import ee
from src.ingestion.load_mines import load_mine_polygons
from src.ingestion.sentinel_access import prepare_mine_aois

# =========================
# CONFIG
# =========================
START_DATE = "2022-01-01"
END_DATE = "2022-12-31"
MAX_CLOUD = 20
MAX_MINES = 5

NDVI_DROP_THRESHOLD = -0.2
MIN_PERSISTENCE = 3   # pixel must be flagged ≥ 3 times

# =========================
# INIT GEE
# =========================
def init_gee():
    ee.Initialize(project="adaptive-mining-monitoring")
    print("✅ GEE initialized")

# =========================
# NDVI
# =========================
def add_ndvi(image):
    ndvi = image.normalizedDifference(["B8", "B4"]).rename("NDVI")
    return image.addBands(ndvi)

# =========================
# MAIN
# =========================
def main():
    init_gee()

    mines = load_mine_polygons("data/vectors/CILS_mines_polygon")
    aois = prepare_mine_aois(mines).head(MAX_MINES)

    print(f"Running Phase 4.2 for {len(aois)} mines")

    s2 = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterDate(START_DATE, END_DATE)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", MAX_CLOUD))
        .select(["B4", "B8"])
        .map(add_ndvi)
    )

    for _, row in aois.iterrows():
        mine_id = row["mine_id"]
        geom = ee.Geometry.Polygon(list(row.geometry.exterior.coords))

        mine_ic = s2.filterBounds(geom)

        # -------------------------
        # NDVI BASELINE
        # -------------------------
        baseline = mine_ic.select("NDVI").median().clip(geom)

        # -------------------------
        # ΔNDVI + Change Mask
        # -------------------------
        def add_change(image):
            dndvi = image.select("NDVI").subtract(baseline)
            mask = dndvi.lt(NDVI_DROP_THRESHOLD)
            return image.addBands(mask.rename("change_mask"))

        change_ic = mine_ic.map(add_change)

        # -------------------------
        # PERSISTENCE FILTER
        # -------------------------
        persistence = (
            change_ic
            .select("change_mask")
            .sum()
            .gte(MIN_PERSISTENCE)
            .rename("persistent_change")
        )

        print(f"✅ Phase 4.2 completed for {mine_id}")

    print("🎉 PHASE 4.2 COMPLETE")

if __name__ == "__main__":
    main()
