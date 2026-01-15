import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling


# -------------------------------
# 3.2 Cloud Masking (Sentinel-2 L2A)
# -------------------------------

VALID_SCL = [4, 5, 6, 7, 11]
# 4 vegetation, 5 bare soil, 6 water, 7 unclassified, 11 snow

def apply_cloud_mask(image, scl):
    """
    Mask clouds using Sentinel-2 Scene Classification Layer (SCL).
    """
    mask = np.isin(scl, VALID_SCL)
    return np.where(mask, image, np.nan), mask


# -------------------------------
# 3.3 Band Harmonization to 10 m
# -------------------------------

def resample_to_10m(src_array, src_transform, src_crs,
                    dst_shape, dst_transform):
    """
    Resample Sentinel-2 bands to 10 m resolution.
    """
    dst = np.empty(dst_shape, dtype=np.float32)

    reproject(
        source=src_array,
        destination=dst,
        src_transform=src_transform,
        src_crs=src_crs,
        dst_transform=dst_transform,
        dst_crs=src_crs,
        resampling=Resampling.bilinear
    )
    return dst


# -------------------------------
# 3.4 Radiometric Normalization
# -------------------------------

def temporal_normalization(stack):
    """
    Normalize band stack by temporal median.
    stack shape: (time, height, width)
    """
    median = np.nanmedian(stack, axis=0)
    return stack - median


# -------------------------------
# 3.5 Seasonal Baseline Computation
# -------------------------------

def compute_seasonal_baseline(dates, stack):
    """
    Compute seasonal baselines (monthly).
    """
    baseline = {}

    for month in range(1, 13):
        idx = [i for i, d in enumerate(dates) if d.month == month]
        if idx:
            baseline[month] = np.nanmedian(stack[idx], axis=0)

    return baseline


# -------------------------------
# 3.6 Valid Observation Mask
# -------------------------------

def build_valid_mask(mask_stack):
    """
    Combine cloud masks across time.
    """
    return np.all(mask_stack, axis=0)
