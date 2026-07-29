from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from forge_works.dr.label_schema_validator.types import CatalogEntry, EstimandCatalog


def load_catalog_from_yaml(path: str | Path) -> EstimandCatalog:
    with Path(path).open(encoding="utf-8") as handle:
        raw: Any = yaml.safe_load(handle)
    if not isinstance(raw, dict) or "estimands" not in raw:
        raise ValueError(f"Invalid catalog file at {path}: missing 'estimands' key")
    entries: dict[str, CatalogEntry] = {}
    for item in raw["estimands"]:
        entry = CatalogEntry(
            estimand_id=item["estimand_id"],
            outcome_vocabulary=tuple(item.get("outcome_vocabulary", ())),
            version=item.get("version", ""),
            owner=item.get("owner", ""),
            superseded_by=item.get("superseded_by"),
            notes=item.get("notes", ""),
        )
        entries[entry.estimand_id] = entry
    return EstimandCatalog(entries=entries)
