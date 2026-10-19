"""Write-once files for run logs and registry entries: an existing record is never replaced."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


class RecordExistsError(FileExistsError):
    """A write would replace an existing run record. Use a new run or study id."""


def write_once_text(path: Path, text: str) -> Path:
    """Create `path` with `text`; refuse (RecordExistsError) if it already exists.

    Written to a temp file, then hard-linked into place: the link is atomic and fails
    if `path` exists, so a crash never leaves a truncated record.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            os.fchmod(fh.fileno(), 0o644)  # mkstemp makes 0600; records are plain files
            fh.write(text)
        # Needs hard links (local disks); SMB/exFAT raise a plain OSError instead.
        os.link(tmp, path)
    except FileExistsError as exc:
        raise RecordExistsError(
            f"refusing to overwrite {path}: run records are write-once; use a new id"
        ) from exc
    finally:
        os.unlink(tmp)
    return path
