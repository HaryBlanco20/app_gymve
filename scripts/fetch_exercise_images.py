#!/usr/bin/env python3
"""Descarga las ilustraciones Everkinetic (CC BY-SA 4.0) usadas por el catálogo.

Las imágenes se guardan sin modificar en app/static/exercises/everkinetic/.
Atribución y licencia: docs/creditos-imagenes.md.
"""

import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.exercise_catalog import EXERCISES

EVERKINETIC_COMMIT = "446bb9a3d0c3beb6b84f7c9d77dfc8af707a2ab6"
BASE_URL = f"https://raw.githubusercontent.com/everkinetic/data/{EVERKINETIC_COMMIT}/dist/png"
DEST = ROOT / "app" / "static" / "exercises" / "everkinetic"


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    ids = sorted({ex["ek_id"] for ex in EXERCISES if ex["ek_id"]})
    for ek_id in ids:
        for phase in ("relaxation", "tension"):
            name = f"{ek_id}-{phase}.png"
            target = DEST / name
            if target.exists():
                continue
            with urllib.request.urlopen(f"{BASE_URL}/{name}", timeout=30) as resp:
                target.write_bytes(resp.read())
            print(f"Descargado {name}")
    print(f"{len(ids)} ejercicios con ilustración en {DEST.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
