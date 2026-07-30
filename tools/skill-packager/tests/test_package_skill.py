from __future__ import annotations

import hashlib
import importlib.util
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "package_skill.py"
SPEC = importlib.util.spec_from_file_location("factory_package_skill", MODULE_PATH)
assert SPEC and SPEC.loader
package_skill = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = package_skill
SPEC.loader.exec_module(package_skill)


class PackageSkillTests(unittest.TestCase):
    def make_skill(self, root: Path, *, name: str = "test-skill", references: bool = True) -> Path:
        skill = root / "source-with-id-prefix"
        skill.mkdir()
        (skill / "SKILL.md").write_text(
            f'---\nname: {name}\ndescription: "Use when testing the factory packager."\n---\n\n# Test Skill\n',
            encoding="utf-8",
        )
        if references:
            (skill / "references").mkdir()
            (skill / "references" / "rules.md").write_text("# Rules\n", encoding="utf-8")
        (skill / "scripts").mkdir()
        helper = skill / "scripts" / "helper.py"
        helper.write_text("print('ok')\n", encoding="utf-8")
        helper.chmod(0o755)
        return skill

    def test_packages_all_resources_under_skill_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            skill = self.make_skill(root)
            archive, members = package_skill.package_skill(skill, root / "dist")

            self.assertEqual(
                members,
                [
                    "test-skill/SKILL.md",
                    "test-skill/references/rules.md",
                    "test-skill/scripts/helper.py",
                ],
            )
            with zipfile.ZipFile(archive) as bundle:
                self.assertEqual(bundle.testzip(), None)
                self.assertEqual(bundle.read("test-skill/references/rules.md"), b"# Rules\n")

    def test_archive_is_reproducible(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            skill = self.make_skill(root)
            first, _ = package_skill.package_skill(skill, root / "one")
            second, _ = package_skill.package_skill(skill, root / "two")
            self.assertEqual(hashlib.sha256(first.read_bytes()).hexdigest(), hashlib.sha256(second.read_bytes()).hexdigest())

    def test_ignores_hidden_and_macos_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            skill = self.make_skill(root)
            (skill / ".DS_Store").write_bytes(b"noise")
            (skill / "Icon\r").write_bytes(b"noise")
            (skill / ".hidden").mkdir()
            (skill / ".hidden" / "secret.txt").write_text("noise", encoding="utf-8")
            _, members = package_skill.package_skill(skill, root / "dist")
            self.assertFalse(any("DS_Store" in member or "Icon" in member or ".hidden" in member for member in members))

    def test_fails_without_references(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            skill = self.make_skill(root, references=False)
            with self.assertRaisesRegex(package_skill.PackagingError, "references/"):
                package_skill.package_skill(skill, root / "dist")

    def test_fails_for_invalid_skill_name(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            skill = self.make_skill(root, name="Bad Skill")
            with self.assertRaisesRegex(package_skill.PackagingError, "slug"):
                package_skill.package_skill(skill, root / "dist")

    def test_refuses_unapproved_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            skill = self.make_skill(root)
            package_skill.package_skill(skill, root / "dist")
            with self.assertRaisesRegex(package_skill.PackagingError, "--force"):
                package_skill.package_skill(skill, root / "dist")


if __name__ == "__main__":
    unittest.main()
