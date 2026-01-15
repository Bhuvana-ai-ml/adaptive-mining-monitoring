print("SCRIPT STARTED")

import ee
import os
import requests
from pathlib import Path

from src.ingestion.load_mines import load_mine_polygons
from src.ingestion.sentinel_access import prepare_mine_aois

# =========================
# CONFIG
# =========================
PROJECT_ID = "adaptive-mining-monitoring"
START_DATE = "2022-01-01"
END_DATE = "2022-12-31"
MAX_CLOUD = 20

RAW_DATA_DIR = Path("data/raw/sentinel2")


# =========================
# INIT GEE
# =========================
def init_gee():
    try:
        ee.Initialize(project=PROJECT_ID)
        print(f"GEE initialized with project: {PROJECT_ID}")
    except Exception:
        ee.Authenticate()
        ee.Initialize(project=PROJECT_ID)
        print(f"GEE initialized with project: {PROJECT_ID}")


# =========================
# CLOUD MASK
# =========================
def mask_s2_clouds(image):
    scl = image.select("SCL")
    valid = (
        scl.eq(4)  # vegetation
        .Or(scl.eq(5))  # bare soil
        .Or(scl.eq(6))  # water
        .Or(scl.eq(7))  # unclassified
    )
    return image.updateMask(valid)


# =========================
# DOWNLOAD IMAGE (SAFE METHOD)
# =========================
import time
import requests

def download_image(image, geom, out_path, scale=10, max_retries=5):
    url = image.getDownloadURL({
        "scale": scale,
        "region": geom,
        "format": "GEO_TIFF"
    })

    for attempt in range(1, max_retries + 1):
        try:
            r = requests.get(url, stream=True, timeout=120)
            r.raise_for_status()

            with open(out_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            return  # ✅ success

        except Exception as e:
            print(f"⚠ Download failed (attempt {attempt}): {out_path.name}")
            if attempt == max_retries:
                print(f"❌ Skipping {out_path.name}")
                return
            time.sleep(5 * attempt)  # ⏳ backoff


# =========================
# MAIN PIPELINE
# =========================
def main():
    print("ENTERED main()")

    init_gee()
    print("GEE INITIALIZED")

    mines = load_mine_polygons("data/vectors/CILS_mines_polygon")
    print("Mines loaded:", len(mines))

    aois = prepare_mine_aois(mines)
    print("AOIs prepared:", len(aois))

    s2 = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterDate(START_DATE, END_DATE)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", MAX_CLOUD))
        .map(mask_s2_clouds)
    )

    for _, row in aois.head(5).iterrows():
        mine_id = row["mine_id"]

        # ✅ FIXED LINE
        geom = ee.Geometry.Polygon(list(row.geometry.exterior.coords))

        out_dir = RAW_DATA_DIR / mine_id
        out_dir.mkdir(parents=True, exist_ok=True)

        images = s2.filterBounds(geom).toList(100)
        count = images.size().getInfo()

        print(f"Downloading {count} images for {mine_id}")

        for i in range(count):
            img = ee.Image(images.get(i))
            date = ee.Date(img.get("system:time_start")).format("YYYY-MM-dd").getInfo()

            out_path = out_dir / f"{date}.tif"
            if out_path.exists():
                continue

            print(f"  Downloading {date}")
            clipped = img.clip(geom)
            download_image(clipped, geom, out_path)
            time.sleep(2)

if __name__ == "__main__":
    main()
