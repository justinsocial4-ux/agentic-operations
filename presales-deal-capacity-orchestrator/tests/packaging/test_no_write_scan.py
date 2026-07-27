import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_non_test_source_has_no_mutation_surface() -> None:
    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts/no_write_scan.py")],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
