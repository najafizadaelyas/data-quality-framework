"""Schema drift detection — compare live table schema against a saved baseline."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import text

from src.utils.db import get_connection
from src.utils.alerts import alert

logger = logging.getLogger(__name__)

BASELINES_DIR = Path(__file__).parent.parent.parent / "great_expectations" / "schema_baselines"


def get_live_schema(table: str, schema: str = "public", db_name: str | None = None) -> dict[str, str]:
    """Return column → data_type mapping for *table* from information_schema."""
    sql = text(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_schema = :schema AND table_name = :table "
        "ORDER BY ordinal_position"
    )
    with get_connection(db_name) as conn:
        rows = conn.execute(sql, {"schema": schema, "table": table}).fetchall()
    return {row[0]: row[1] for row in rows}


def save_baseline(table: str, schema_map: dict[str, str]) -> Path:
    """Persist a schema baseline to disk."""
    BASELINES_DIR.mkdir(parents=True, exist_ok=True)
    path = BASELINES_DIR / f"{table}.json"
    path.write_text(json.dumps(schema_map, indent=2))
    logger.info("Saved baseline for %s → %s", table, path)
    return path


def load_baseline(table: str) -> dict[str, str] | None:
    path = BASELINES_DIR / f"{table}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


class SchemaDriftResult:
    def __init__(self, table: str, added: list, removed: list, changed: list):
        self.table = table
        self.added = added
        self.removed = removed
        self.changed = changed

    @property
    def has_drift(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def summary(self) -> str:
        parts = []
        if self.added:
            parts.append(f"Added columns: {self.added}")
        if self.removed:
            parts.append(f"Removed columns: {self.removed}")
        if self.changed:
            parts.append(f"Type changes: {self.changed}")
        return f"[{self.table}] " + " | ".join(parts) if parts else f"[{self.table}] No drift"


def check_schema_drift(
    table: str,
    schema: str = "public",
    db_name: str | None = None,
    send_alerts: bool = True,
) -> SchemaDriftResult:
    """Compare live schema against saved baseline and return a drift result."""
    live = get_live_schema(table, schema, db_name)
    baseline = load_baseline(table)

    if not baseline:  # None or empty dict — treat as first run
        logger.warning("No baseline for %s — saving current schema as baseline.", table)
        save_baseline(table, live)
        return SchemaDriftResult(table, [], [], [])

    added = [c for c in live if c not in baseline]
    removed = [c for c in baseline if c not in live]
    changed = [
        {"column": c, "from": baseline[c], "to": live[c]}
        for c in live
        if c in baseline and baseline[c] != live[c]
    ]

    result = SchemaDriftResult(table, added, removed, changed)
    if result.has_drift:
        msg = f"Schema drift detected!\n{result.summary()}"
        logger.warning(msg)
        if send_alerts:
            alert(msg, subject=f"Schema Drift — {table}", level="warning")

    return result
