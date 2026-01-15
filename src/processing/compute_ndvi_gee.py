import ee
import time
from pathlib import Path

from src.ingestion.load_mines import load_mine_polygons
from src.ingestion.sentinel_access import prepare_mine_aois

# =========================
# CONFIG
# =========================
START_DATE = "2022-01-01"
END_DATE = "2022-12-31"
MAX_CLOUD = 20
MAX_MINES = 5   # ⬅ keep small for now

NDVI_DIR = Path("data/processed/ndvi")
NDVI_DIR.mkdir(parents=True, exist_ok=True)


# =========================
# INIT GEE
# =========================
def init_gee():
    ee.Initialize(project="adaptive-mining-monitoring")
    print("✅ GEE initialized")


# =========================
# CLOUD MASK
# =========================
def mask_s2(image):
    scl = image.select("SCL")
    mask = scl.eq(4).Or(scl.eq(5)).Or(scl.eq(6)).Or(scl.eq(7))
    return image.updateMask(mask)


# =========================
# NDVI COMPUTATION
# =========================
def add_ndvi(image):
    ndvi = image.normalizedDifference(["B8", "B4"]).rename("NDVI")
    return image.addBands(ndvi)


# =========================
# EXPORT NDVI
# =========================
def export_ndvi(image, geom, mine_id, date):
    out_dir = NDVI_DIR / mine_id
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / f"{date}_ndvi.tif"
    if out_path.exists():
        return

    task = ee.batch.Export.image.toDrive(
        image=image.select("NDVI"),
        description=f"{mine_id}_{date}",
        folder="NDVI_EXPORT",
        fileNamePrefix=f"{mine_id}_{date}",
        region=geom,
        scale=10,
        crs="EPSG:4326",
        maxPixels=1e13
    )

    task.start()
    print(f"⬆ Exporting NDVI: {mine_id} {date}")
    time.sleep(1)


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
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", MAX_CLOUD))
        .map(mask_s2)
        .map(add_ndvi)
    )

    for _, row in aois.iterrows():
        mine_id = row["mine_id"]
        geom = ee.Geometry.Polygon(list(row.geometry.exterior.coords))

        images = s2.filterBounds(geom).toList(50)
        count = images.size().getInfo()

        print(f"🔹 {mine_id}: {count} images")

        for i in range(count):
            img = ee.Image(images.get(i))
            date = ee.Date(img.get("system:time_start")).format("YYYY-MM-dd").getInfo()

            clipped = img.clip(geom)
            export_ndvi(clipped, geom, mine_id, date)


if __name__ == "__main__":
    main()
