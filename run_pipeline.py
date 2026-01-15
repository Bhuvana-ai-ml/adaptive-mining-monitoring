from src.ingestion.load_mines import load_mine_polygons
from src.ingestion.sentinel_access import prepare_mine_aois

def main():
    print("Starting Phase 2 – AOI preparation")

    mines = load_mine_polygons("data/vectors/CILS_mines_polygon")
    aois = prepare_mine_aois(mines, buffer_m=500)

    print(f"Prepared AOIs for {len(aois)} mines")
    print(aois.head())

if __name__ == "__main__":
    main()
