import pandas as pd
from pathlib import Path

# =========================
# FINAL METRICS (FROM PIPELINE)
# =========================
data = [
    {"mine_id": "MINE_0000", "area_ha": 173.23, "severity": -0.032, "risk": "MODERATE", "impact": 5.54},
    {"mine_id": "MINE_0001", "area_ha": 119.44, "severity": -0.048, "risk": "MODERATE", "impact": 5.73},
    {"mine_id": "MINE_0002", "area_ha": 409.12, "severity": -0.009, "risk": "MODERATE", "impact": 3.68},
    {"mine_id": "MINE_0003", "area_ha": 66.47,  "severity": -0.005, "risk": "MODERATE", "impact": 0.33},
    {"mine_id": "MINE_0004", "area_ha": 119.55, "severity": -0.007, "risk": "MODERATE", "impact": 0.84},
]

# =========================
# EXPORT
# =========================
def main():
    out_dir = Path("outputs")
    out_dir.mkdir(exist_ok=True)

    df = pd.DataFrame(data)
    df = df.sort_values("impact", ascending=False)

    out_path = out_dir / "final_mine_assessment.csv"
    df.to_csv(out_path, index=False)

    print(f"✅ Final table saved → {out_path}")

if __name__ == "__main__":
    main()
