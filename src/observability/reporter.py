"""Generate HTML and JSON data quality reports."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

REPORTS_DIR = Path(__file__).parent.parent.parent / "reports"


def _html_row(key: str, value: Any, ok: bool | None = None) -> str:
    color = ""
    if ok is True:
        color = "background:#d4edda"
    elif ok is False:
        color = "background:#f8d7da"
    return f"<tr style='{color}'><td><b>{key}</b></td><td>{value}</td></tr>"


def generate_html_report(results: list[dict], title: str = "Data Quality Report") -> str:
    now = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    rows = ""
    for r in results:
        passed = r.get("passed")
        label = "PASS" if passed else "FAIL"
        name = f"{r.get('table', '')} / {r.get('column', r.get('check', ''))}"
        rows += _html_row(name, label, ok=passed)

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>{title}</title>
<style>body{{font-family:sans-serif;margin:2rem}}
table{{border-collapse:collapse;width:100%}}
td{{padding:8px 12px;border:1px solid #dee2e6}}
h1{{color:#343a40}}</style>
</head>
<body>
<h1>{title}</h1>
<p>Generated: {now}</p>
<table>{rows}</table>
</body>
</html>"""


def save_report(results: list[dict], name: str, fmt: str = "both") -> dict[str, Path]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
    saved = {}

    if fmt in ("json", "both"):
        json_path = REPORTS_DIR / f"{name}_{ts}.json"
        json_path.write_text(json.dumps(results, indent=2, default=str))
        saved["json"] = json_path
        logger.info("JSON report saved: %s", json_path)

    if fmt in ("html", "both"):
        html_path = REPORTS_DIR / f"{name}_{ts}.html"
        html_path.write_text(generate_html_report(results, title=name))
        saved["html"] = html_path
        logger.info("HTML report saved: %s", html_path)

    return saved
