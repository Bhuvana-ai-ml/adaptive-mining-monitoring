import geopandas as gpd
from shapely.geometry import box
from pathlib import Path
import pandas as pd


def build_mine_aoi(mine_geom, source_crs, buffer_m=500):
    """
    Build AOI by buffering in a projected CRS (meters),
    then return bounding box in EPSG:4326.
    """

    # Create temporary GeoDataFrame
    gdf = gpd.GeoDataFrame(
        geometry=[mine_geom],
        crs=source_crs
    )

    # Reproject to a metric CRS (Web Mercator)
    gdf_proj = gdf.to_crs(epsg=3857)

    # Buffer in meters
    buffered = gdf_proj.buffer(buffer_m)

    # Back to lat/lon
    buffered_latlon = buffered.to_crs(epsg=4326)

    minx, miny, maxx, maxy = buffered_latlon.total_bounds
    return box(minx, miny, maxx, maxy)


def prepare_mine_aois(mines_gdf, buffer_m=500):
    aois = []

    for _, mine in mines_gdf.iterrows():
        aoi_geom = build_mine_aoi(
            mine.geometry,
            source_crs=mines_gdf.crs,
            buffer_m=buffer_m
        )

        aois.append({
            "mine_id": mine["mine_id"],
            "geometry": aoi_geom
        })

    return gpd.GeoDataFrame(aois, crs="EPSG:4326")


def build_time_series_metadata(mine_id, dates, cloud_covers):
    """
    Create metadata table for Sentinel-2 acquisitions.
    """
    return pd.DataFrame({
        "mine_id": mine_id,
        "date": dates,
        "cloud_cover": cloud_covers
    })
