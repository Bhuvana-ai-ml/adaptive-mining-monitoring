import ee
from pathlib import Path

from src.ingestion.load_mines import load_mine_polygons
from src.ingestion.sentinel_access import prepare_mine_aois

# =========================
# CONFIG
# =========================
START_DATE = "2022-01-01"
END_DATE = "2022-12-31"
MAX_MINES = 5

OUT_DIR = Path("outputs/maps")
OUT_DIR.mkdir(parents=True, exist_ok=True)

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
    return image.addBands(
        image.normalizedDifference(["B8", "B4"]).rename("NDVI")
    )

# =========================
# MAIN
# =========================
def main():
    init_gee()

    mines = load_mine_polygons("data/vectors/CILS_mines_polygon")
    aois = prepare_mine_aois(mines).head(MAX_MINES)

    s2 = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterDate(START_DATE, END_DATE)
        .select(["B4", "B8"])
        .map(add_ndvi)
    )

    for _, row in aois.iterrows():
        mine_id = row["mine_id"]
        geom = ee.Geometry.Polygon(list(row.geometry.exterior.coords))

        mine_ic = s2.filterBounds(geom)

        early = (
            mine_ic
            .filterDate("2022-01-01", "2022-06-30")
            .select("NDVI")
            .median()
        )

        late = (
            mine_ic
            .filterDate("2022-07-01", "2022-12-31")
            .select("NDVI")
            .median()
        )

        ndvi_change = late.subtract(early).clip(geom)

        task = ee.batch.Export.image.toDrive(
            image=ndvi_change,
            description=f"{mine_id}_NDVI_CHANGE",
            folder="NDVI_CHANGE_MAPS",
            fileNamePrefix=f"{mine_id}_ndvi_change",
            region=geom,
            scale=10,
            crs="EPSG:4326",
            maxPixels=1e13
        )

        task.start()
        print(f"🗺️ Exporting NDVI change map for {mine_id}")

if __name__ == "__main__":
    main()
