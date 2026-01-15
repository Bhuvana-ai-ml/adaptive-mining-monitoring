from operator import itemgetter

# =========================
# INPUT (FROM PHASE 4 & 5.1)
# =========================
mine_metrics = {
    "MINE_0000": {"area": 173.23, "severity": -0.032, "risk": "MODERATE"},
    "MINE_0001": {"area": 119.44, "severity": -0.048, "risk": "MODERATE"},
    "MINE_0002": {"area": 409.12, "severity": -0.009, "risk": "MODERATE"},
    "MINE_0003": {"area": 66.47,  "severity": -0.005, "risk": "MODERATE"},
    "MINE_0004": {"area": 119.55, "severity": -0.007, "risk": "MODERATE"},
}

# =========================
# ALERT LOGIC
# =========================
def alert_level(risk):
    if risk == "HIGH":
        return "🚨 IMMEDIATE INSPECTION"
    elif risk == "MODERATE":
        return "⚠ INCREASED MONITORING"
    else:
        return "✅ NO ACTION"

# =========================
# MAIN
# =========================
def main():
    print("🔔 PHASE 5.2 — ALERTS & RANKING\n")

    results = []

    for mine_id, m in mine_metrics.items():
        impact_score = m["area"] * abs(m["severity"])
        alert = alert_level(m["risk"])

        results.append({
            "mine": mine_id,
            "impact": impact_score,
            "risk": m["risk"],
            "alert": alert
        })

    # -------------------------
    # RANK MINES
    # -------------------------
    ranked = sorted(results, key=itemgetter("impact"), reverse=True)

    for i, r in enumerate(ranked, start=1):
        print(
            f"{i}. {r['mine']} | "
            f"Impact Score: {r['impact']:.2f} | "
            f"Risk: {r['risk']} | "
            f"Alert: {r['alert']}"
        )

    print("\n🎉 PHASE 5.2 COMPLETE")

if __name__ == "__main__":
    main()
