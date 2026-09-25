"""Registry persistence and loading for studies and runs (JH-63.2)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from alphaguard.ml.study_schema import ParentStudyRecord, RunRecord


def dump_run_record(record: RunRecord) -> dict[str, Any]:
    """Serialize a run. Null Phase B blocks are omitted so off-mode bytes match."""
    data = record.model_dump(mode="json")
    if record.walk_forward is None:
        data.pop("walk_forward", None)
    if record.economic is None:
        data.pop("economic", None)
    if record.schema_version is None:
        data.pop("schema_version", None)
    return data


class StudyRegistry:
    """Manages reading and writing run records under artifacts/runs/studies/<study_id>/."""

    def __init__(self, root_dir: Path | str = "artifacts/runs") -> None:
        self.root_dir = Path(root_dir)

    def study_dir(self, study_id: str) -> Path:
        return self.root_dir / "studies" / study_id

    def runs_dir(self, study_id: str) -> Path:
        return self.study_dir(study_id) / "runs"

    def bundles_dir(self, study_id: str) -> Path:
        return self.study_dir(study_id) / "bundles"

    def ensure_study_dirs(self, study_id: str) -> None:
        self.runs_dir(study_id).mkdir(parents=True, exist_ok=True)
        self.bundles_dir(study_id).mkdir(parents=True, exist_ok=True)

    def save_study(self, record: ParentStudyRecord) -> Path:
        self.ensure_study_dirs(record.study_id)
        out_path = self.study_dir(record.study_id) / "study.json"
        out_path.write_text(
            json.dumps(record.model_dump(), indent=2, default=str) + "\n",
            encoding="utf-8",
        )
        return out_path

    def load_study(self, study_id: str) -> ParentStudyRecord:
        path = self.study_dir(study_id) / "study.json"
        if not path.exists():
            raise FileNotFoundError(f"study.json not found: {path}")
        return ParentStudyRecord.model_validate_json(path.read_text(encoding="utf-8"))

    def save_run(self, record: RunRecord) -> Path:
        self.ensure_study_dirs(record.study_id)
        out_path = self.runs_dir(record.study_id) / f"{record.run_id}.json"
        out_path.write_text(
            json.dumps(dump_run_record(record), indent=2, default=str) + "\n",
            encoding="utf-8",
        )
        return out_path

    def load_run(self, study_id: str, run_id: str) -> RunRecord:
        path = self.runs_dir(study_id) / f"{run_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"run record not found: {path}")
        return RunRecord.model_validate_json(path.read_text(encoding="utf-8"))

    def list_runs(self, study_id: str) -> list[RunRecord]:
        r_dir = self.runs_dir(study_id)
        if not r_dir.exists():
            return []
        records: list[RunRecord] = []
        for file in sorted(r_dir.glob("*.json")):
            try:
                records.append(RunRecord.model_validate_json(file.read_text(encoding="utf-8")))
            except Exception:
                continue
        return records
