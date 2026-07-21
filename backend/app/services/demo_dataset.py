from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path


class DemoDatasetError(RuntimeError):
    pass


@dataclass(frozen=True)
class DemoDatasetSummary:
    dataset_id: str
    chats: int
    projects: int
    proposals: int
    safe_proposals: int
    exceptions: int
    acceptance_cases: int
    source_files: int
    originals_immutable: bool


class DemoDatasetService:
    def __init__(self, canonical_dir: Path) -> None:
        self.canonical_dir = canonical_dir.resolve()

    def _read_json(self, filename: str) -> dict:
        path = (self.canonical_dir / filename).resolve()
        if path.parent != self.canonical_dir:
            raise DemoDatasetError("Dataset path escaped the canonical directory")
        if not path.exists():
            raise DemoDatasetError(f"Missing approved fixture: {filename}")
        return json.loads(path.read_text(encoding="utf-8"))

    def summary(self) -> DemoDatasetSummary:
        normalized = self._read_json("normalized_chats.json")
        projects = self._read_json("expected_projects.json")
        proposals = self._read_json("expected_proposals.json")

        matrix_path = self.canonical_dir.parent.parent / "tests" / "matrices" / "ot006_acceptance_matrix.csv"
        if not matrix_path.exists():
            raise DemoDatasetError("Missing O.T. 006 acceptance matrix")
        with matrix_path.open(encoding="utf-8", newline="") as handle:
            acceptance_cases = sum(1 for _ in csv.DictReader(handle))

        return DemoDatasetSummary(
            dataset_id=str(normalized["dataset_id"]),
            chats=len(normalized["chats"]),
            projects=len(projects["projects"]),
            proposals=len(proposals["proposal_items"]),
            safe_proposals=len(proposals["safe_proposal_ids"]),
            exceptions=len(proposals["exception_proposal_ids"]),
            acceptance_cases=acceptance_cases,
            source_files=len(normalized["import_batch"]["source_files"]),
            originals_immutable=bool(normalized["import_batch"]["originals_immutable"]),
        )
