import geopandas as gpd
import pandas as pd
from pathlib import Path


def load_mine_polygons(vector_dir: str, target_crs: str = "EPSG:4326"):
    """
    Load mine polygon data, validate CRS, and assign unique mine IDs.
    """

    vector_dir = Path(vector_dir)

    # Load polygon data (supports SHP or GeoJSON)
    polygon_files = list(vector_dir.glob("*.shp")) + list(vector_dir.glob("*.geojson"))

    if not polygon_files:
        raise FileNotFoundError("No polygon files found in directory")

    gdf = gpd.read_file(polygon_files[0])

    # CRS validation
    if gdf.crs is None:
        raise ValueError("Mine polygon data has no CRS defined")

    if gdf.crs.to_string() != target_crs:
        gdf = gdf.to_crs(target_crs)

    # Assign unique mine IDs
    gdf = gdf.reset_index(drop=True)
    gdf["mine_id"] = ["MINE_{:04d}".format(i) for i in range(len(gdf))]

    # Basic geometry validation
    gdf = gdf[gdf.is_valid]

    return gdf


def create_mine_metadata(gdf: gpd.GeoDataFrame):
    """
    Create mine metadata table (non-geometry attributes).
    """

    metadata_cols = [col for col in gdf.columns if col != "geometry"]
    metadata = gdf[metadata_cols].copy()

    return metadata


if __name__ == "__main__":
    mines = load_mine_polygons(
        vector_dir="data/vectors/CILS_mines_polygon"
    )

    metadata = create_mine_metadata(mines)

    print("Total mines loaded:", len(mines))
    print(metadata.head())
