#!/usr/bin/env python3
"""Crea las tablas en PostgreSQL (idempotente)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Import models so metadata registers workout tables.
import app.models  # noqa: F401
from app.db import Base, engine
from app.models import User  # noqa: F401 — registra tablas en Base.metadata


def main() -> None:
    Base.metadata.create_all(bind=engine)
    print("Tablas creadas o ya existentes (usuarios, ejercicios, rutinas, compartidos).")


if __name__ == "__main__":
    main()
