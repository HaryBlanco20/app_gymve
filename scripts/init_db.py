#!/usr/bin/env python3
"""Crea las tablas en PostgreSQL (idempotente)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.db import engine
from app.schema_upgrade import upgrade_schema


def main() -> None:
    upgrade_schema(engine)
    print(
        "Tablas creadas o actualizadas (usuarios, ejercicios, máquinas, rutinas, "
        "compartidos, registros)."
    )


if __name__ == "__main__":
    main()
