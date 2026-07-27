from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from orchestrator.privacy import PrivacyBoundaryError, create_owner_only_file, create_real_data_directory

pytestmark = pytest.mark.skipif(os.name != "posix", reason="POSIX permission proof; ACL equivalent required elsewhere")


def test_real_data_directory_and_file_are_owner_only_and_outside_repo(tmp_path: Path) -> None:
    repository = tmp_path / "checkout"
    repository.mkdir()
    import_directory = tmp_path / "imports"
    import_directory.mkdir()
    state = create_real_data_directory(
        tmp_path / "private-state",
        repository_root=repository,
        import_directory=import_directory,
    )
    private_file = create_owner_only_file(state / "state.sqlite")
    assert stat.S_IMODE(state.stat().st_mode) == 0o700
    assert stat.S_IMODE(private_file.stat().st_mode) == 0o600
    assert not state.is_relative_to(repository)
    assert not state.is_relative_to(import_directory)


def test_real_data_directory_inside_repo_fails_closed(tmp_path: Path) -> None:
    repository = tmp_path / "checkout"
    repository.mkdir()
    with pytest.raises(PrivacyBoundaryError, match="outside the repository"):
        create_real_data_directory(repository / ".orchestrator", repository_root=repository)
