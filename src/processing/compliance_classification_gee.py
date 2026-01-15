import ee
from src.ingestion.load_mines import load_mine_polygons
from src.ingestion.sentinel_access import prepare_mine_aois

# =========================
# CONFIG
# =========================
MAX_MINES = 5

AREA_HIGH = 100     # hectares
AREA_MED = 25

SEVERITY_HIGH = -0.15
SEVERITY_MED = -0.05

# =========================
# INIT GEE
# =========================
def init_gee():
    ee.Initialize(project="adaptive-mining-monitoring")
    print("✅ GEE initialized")

# =========================
# RISK CLASSIFIER
# =========================
def classify_risk(area, severity):
    if area > AREA_HIGH and severity < SEVERITY_HIGH:
        return "HIGH"
    elif area > AREA_MED or severity < SEVERITY_MED:
        return "MODERATE"
    else:
        return "LOW"

# =========================
# MAIN
# =========================
def main():
    init_gee()

    mines = load_mine_polygons("data/vectors/CILS_mines_polygon")
    aois = prepare_mine_aois(mines).head(MAX_MINES)

    print(f"Running Phase 5.1 for {len(aois)} mines")

    # ⬇️ Paste results from Phase 4.3 here (for now)
    phase4_results = {
        "MINE_0000": (173.23, -0.032),
        "MINE_0001": (119.44, -0.048),
        "MINE_0002": (409.12, -0.009),
        "MINE_0003": (66.47, -0.005),
        "MINE_0004": (119.55, -0.007),
    }

    for mine_id, (area, severity) in phase4_results.items():
        risk = classify_risk(area, severity)
        print(f"🚦 {mine_id} | Risk Level: {risk}")

    print("🎉 PHASE 5.1 COMPLETE")

if __name__ == "__main__":
    main()
