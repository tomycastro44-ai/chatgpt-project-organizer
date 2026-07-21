from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4


SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


@dataclass(frozen=True)
class StoredOriginal:
    stored_name: str
    relative_path: str
    size_bytes: int
    sha256: str


class ImportStorage:
    def __init__(self, imports_dir: Path) -> None:
        self.imports_dir = imports_dir.resolve()
        self.imports_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        name = Path(filename).name.strip() or "source.bin"
        sanitized = SAFE_NAME_RE.sub("_", name)
        return sanitized[:180] or "source.bin"

    def store_original(self, batch_id: str, filename: str, content: bytes) -> StoredOriginal:
        batch_dir = (self.imports_dir / batch_id / "originals").resolve()
        if self.imports_dir not in batch_dir.parents:
            raise RuntimeError("Import storage path escaped its root")
        batch_dir.mkdir(parents=True, exist_ok=True)
        safe_name = self.sanitize_filename(filename)
        stored_name = f"{uuid4().hex}_{safe_name}"
        final_path = batch_dir / stored_name
        temporary_path = batch_dir / f".{stored_name}.tmp"
        temporary_path.write_bytes(content)
        os.replace(temporary_path, final_path)
        try:
            final_path.chmod(0o444)
        except OSError:
            pass
        digest = hashlib.sha256(content).hexdigest()
        return StoredOriginal(
            stored_name=stored_name,
            relative_path=str(final_path.relative_to(self.imports_dir.parent)).replace("\\", "/"),
            size_bytes=len(content),
            sha256=digest,
        )
