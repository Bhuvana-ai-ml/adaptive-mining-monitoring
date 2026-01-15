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
NDVI_DROP_THRESHOLD = -0.2  # strong vegetation loss

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
# MAIN PIPELINE
# =========================
def main():
    init_gee()

    mines = load_mine_polygons("data/vectors/CILS_mines_polygon")
    aois = prepare_mine_aois(mines).head(MAX_MINES)

    print(f"Running Phase 4.1 for {len(aois)} mines")

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
        baseline_ndvi = (
            mine_ic
            .select("NDVI")
            .median()
            .clip(geom)
        )

        # -------------------------
        # DELTA NDVI
        # -------------------------
        def delta_ndvi(image):
            delta = image.select("NDVI").subtract(baseline_ndvi).rename("dNDVI")
            return image.addBands(delta)

        delta_ic = mine_ic.map(delta_ndvi)

        # -------------------------
        # CHANGE MASK
        # -------------------------
        def flag_change(image):
            change = image.select("dNDVI").lt(NDVI_DROP_THRESHOLD)
            return image.addBands(change.rename("change_mask"))

        delta_ic = delta_ic.map(flag_change)

        print(f"✅ Phase 4.1 completed for {mine_id}")

    print("🎉 PHASE 4.1 COMPLETE")

if __name__ == "__main__":
    main()
