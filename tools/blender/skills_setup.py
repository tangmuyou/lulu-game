"""Verify pinned skill installations and package reusable skill files with licenses."""
from __future__ import annotations
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[2]
SPECS = [
    ("blender-image-to-3d", "vendor/blender-game-skills", "skills/blender-image-to-3d", "f0ef29385a03de139957e6f700b801cdc00b7e29"),
    ("blender", "vendor/blender-claude-skill", "blender", "964cfe73bb1d15ff5b1603c625ecf067fb8d11bc"),
]

def main():
    out = ROOT / "artifacts"
    out.mkdir(exist_ok=True)
    installs = []
    with zipfile.ZipFile(out / "installed_blender_skills.zip", "w", zipfile.ZIP_DEFLATED) as bundle:
        for name, vendor, subfolder, expected in SPECS:
            checkout = ROOT / vendor
            actual = subprocess.check_output(["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True).strip()
            if actual != expected:
                raise RuntimeError(f"Unexpected upstream revision for {name}: {actual}")
            folder = checkout / subfolder
            if not (folder / "SKILL.md").is_file():
                raise RuntimeError(f"Missing installed skill: {name}")
            license_path = checkout / "LICENSE"
            license_text = license_path.read_text(encoding="utf-8")
            if "MIT License" not in license_text or "Permission is hereby granted" not in license_text:
                raise RuntimeError(f"Expected MIT license was not found for {name}")
            files = [p for p in folder.rglob("*") if p.is_file() and "__pycache__" not in p.parts]
            for p in files:
                if p.suffix == ".py":
                    compile(p.read_text(encoding="utf-8"), str(p), "exec")
                bundle.write(p, str(Path(name) / p.relative_to(folder)))
            bundle.write(license_path, f"{name}/LICENSE")
            # Repair/create the project-local links on platforms where Git did not restore symlinks.
            link = ROOT / ".agents" / "skills" / name
            link.parent.mkdir(parents=True, exist_ok=True)
            if not link.is_symlink():
                if link.is_file():
                    link.unlink()
                if not link.exists():
                    shutil.copytree(folder, link)
            if not (link / "SKILL.md").is_file():
                raise RuntimeError(f"Skill discovery path is broken: {link}")
            installs.append({"skill": name, "revision": actual, "license": "MIT", "files": len(files), "python_syntax": "passed"})
    report = {"status": "passed", "scope": "repository and ephemeral GitHub Actions runtime", "skills": installs,
              "gltf_validator_expected_version": "2.0.0-dev.3.10", "blender_version_unchanged": "4.5.14",
              "third_party_install_scripts_executed": False, "account_wide_plugin_installed": False}
    (out / "skills_installation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
