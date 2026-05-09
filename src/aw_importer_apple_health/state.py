from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from platformdirs import user_config_dir

APP_NAME = "aw-importer-apple-health"


def config_dir() -> Path:
    p = Path(user_config_dir(APP_NAME, appauthor=False))
    p.mkdir(parents=True, exist_ok=True)
    return p


def state_path() -> Path:
    return config_dir() / "state.json"


@dataclass
class ImportState:
    record_hashes: set[str] = field(default_factory=set)
    imported_files: dict[str, str] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path | None = None) -> "ImportState":
        path = path or state_path()
        if not path.exists():
            return cls()
        data = json.loads(path.read_text())
        return cls(record_hashes=set(data.get("record_hashes", [])), imported_files=dict(data.get("imported_files", {})))

    def save(self, path: Path | None = None) -> None:
        path = path or state_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"record_hashes": sorted(self.record_hashes), "imported_files": self.imported_files}, indent=2, sort_keys=True))
        os.chmod(tmp, 0o600)
        tmp.replace(path)
        os.chmod(path, 0o600)
