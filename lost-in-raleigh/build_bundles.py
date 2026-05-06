#!/usr/bin/env python3
"""
Bundle builder for Lost in Raleigh quest document bundles.

Creates a ZIP file per quest from selected city-guide chapters.
Each ZIP includes 5-8 thematic chapters; exactly one chapter per quest
contains the secret code embedded in natural-language prose.

Usage:
    python build_bundles.py

Output:
    bundles/raleigh/glenwood_getaway.zip   (~<5 MB)
    bundles/raleigh/museum_mile.zip        (~<5 MB)
    bundles/raleigh/warehouse_run.zip      (~<5 MB)

After building, upload the bundles/ directory to Azure Blob Storage
and update the document_bundle_url values in city_config.yaml.
"""
from __future__ import annotations

import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CITY_GUIDE = ROOT / "city-guide" / "raleigh"
BUNDLES_OUT = ROOT / "bundles" / "raleigh"

# ─── Quest bundle definitions ───────────────────────────────────────────────
# Each entry maps quest id -> list of chapter filenames to include.
# The chapter that contains the secret code is noted in the comment.

BUNDLES: dict[str, list[str]] = {
    "glenwood_getaway": [
        "01_welcome_to_raleigh.md",
        "02_downtown_and_moore_square.md",   # ← secret code GLENWOOD42 is here
        "03_glenwood_south.md",
        "05_cameron_village_and_midtown.md",
        "09_getting_around_goRaleigh_buses.md",
        "11_getting_around_biking_and_greenways.md",
        "13_food_and_drink.md",
    ],
    "museum_mile": [
        "01_welcome_to_raleigh.md",
        "06_warehouse_district.md",
        "13_food_and_drink.md",
        "14_arts_and_culture.md",            # ← secret code MUSEUMRUN88 is here
        "15_parks_and_outdoors.md",
        "17_history_of_raleigh.md",
        "20_nc_biotech_center_and_rtp.md",
    ],
    "warehouse_run": [
        "01_welcome_to_raleigh.md",
        "06_warehouse_district.md",          # ← secret code TOBACCO55 is here
        "07_boylan_heights.md",
        "09_getting_around_goRaleigh_buses.md",
        "12_getting_around_rideshare_and_parking.md",
        "16_research_triangle_and_innovation.md",
        "17_history_of_raleigh.md",
    ],
}

# ─── Build ───────────────────────────────────────────────────────────────────

def build_bundle(quest_id: str, chapters: list[str]) -> Path:
    BUNDLES_OUT.mkdir(parents=True, exist_ok=True)
    out_path = BUNDLES_OUT / f"{quest_id}.zip"
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for chapter in chapters:
            src = CITY_GUIDE / chapter
            if not src.exists():
                raise FileNotFoundError(f"Chapter not found: {src}")
            zf.write(src, arcname=chapter)
    size_mb = out_path.stat().st_size / (1024 * 1024)
    print(f"  {out_path.name}  {size_mb:.2f} MB")
    if size_mb > 5:
        raise ValueError(f"Bundle {quest_id} exceeds 5 MB limit: {size_mb:.2f} MB")
    return out_path


def main() -> None:
    print("Building quest document bundles...\n")
    for quest_id, chapters in BUNDLES.items():
        print(f"  Quest: {quest_id}")
        path = build_bundle(quest_id, chapters)
    print(f"\nAll bundles written to: {BUNDLES_OUT}")
    print(
        "\nNext steps:\n"
        "  1. Upload the bundles/ directory to an Azure Blob Storage container\n"
        "     (set the container to public read access).\n"
        "  2. Update document_bundle_url values in lost-in-raleigh/city_config.yaml\n"
        "     with the public blob URLs.\n"
        "  3. Restart the game server to pick up the new URLs.\n"
    )


if __name__ == "__main__":
    main()
