from __future__ import annotations

import os
import stat
from pathlib import Path


class PrivacyBoundaryError(RuntimeError):
    pass


def _contains(parent: Path, child: Path) -> bool:
    try:
        child.relative_to(parent)
    except ValueError:
        return False
    return True


def create_real_data_directory(
    path: Path,
    *,
    repository_root: Path,
    import_directory: Path | None = None,
) -> Path:
    """Create/verify an owner-only authorized-data directory outside forbidden roots."""
    if os.name != "posix":
        raise PrivacyBoundaryError("owner-only ACL enforcement is not implemented for this platform")
    root = repository_root.resolve()
    expanded = path.expanduser()
    probe = expanded
    while not probe.exists() and probe != probe.parent:
        probe = probe.parent
    if any(part.is_symlink() for part in (probe, *probe.parents)):
        raise PrivacyBoundaryError("real-data path cannot traverse a symlink")
    candidate = expanded.resolve(strict=False)
    if _contains(root, candidate):
        raise PrivacyBoundaryError("authorized real-data state must be outside the repository")
    if import_directory is not None and _contains(import_directory.resolve(), candidate):
        raise PrivacyBoundaryError("authorized real-data state must be outside the import directory")
    if candidate.exists() and candidate.is_symlink():
        raise PrivacyBoundaryError("real-data directory cannot be a symlink")
    candidate.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(candidate, 0o700)
    mode = stat.S_IMODE(candidate.stat().st_mode)
    if mode != 0o700 or candidate.is_symlink():
        raise PrivacyBoundaryError(f"owner-only directory permission check failed: {mode:o}")
    return candidate


def create_owner_only_file(path: Path) -> Path:
    if os.name != "posix":
        raise PrivacyBoundaryError("owner-only ACL enforcement is not implemented for this platform")
    if path.parent.is_symlink() or stat.S_IMODE(path.parent.stat().st_mode) != 0o700:
        raise PrivacyBoundaryError("private file parent must be an owner-only non-symlink directory")
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        os.fchmod(descriptor, 0o600)
    finally:
        os.close(descriptor)
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode != 0o600 or path.is_symlink():
        raise PrivacyBoundaryError(f"owner-only file permission check failed: {mode:o}")
    return path
