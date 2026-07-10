# Skill Packager

This project-owned tool builds a portable `.skill` ZIP without dropping bundled resources.

```bash
python3 tools/skill-packager/package_skill.py \
  agents/data-quality-crm-hygiene/revops-data-deduplication \
  dist \
  --list
```

The packager fails closed when `SKILL.md` is invalid, `references/` is empty, a symlink is present, or the finished archive does not exactly match the source files. Output is deterministic, so identical source produces identical archive bytes.

Run its dependency-free tests with:

```bash
python3 -m unittest discover -s tools/skill-packager/tests -v
```
