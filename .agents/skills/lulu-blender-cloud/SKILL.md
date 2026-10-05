---
name: lulu-blender-cloud
description: Build and check Lulu game assets with the repository's pinned headless Blender skills, CPU previews, mesh validation, and Khronos GLB validation.
---

# Lulu cloud Blender

This is a repository-level workflow, not a ChatGPT account-wide plugin or a remote Blender desktop.

## Installed references

- Reliable scripting: `vendor/blender-claude-skill/blender/SKILL.md`.
- Reference-to-asset production: `vendor/blender-game-skills/skills/blender-image-to-3d/SKILL.md`.
- Install/check report: `artifacts/skills_installation.json`.

Git submodules pin the exact reviewed upstream commits. Initialize with `git submodule update --init` on a newly cloned checkout; GitHub Actions does this automatically. Read only the relevant references. Do not execute arbitrary snippets or change the pinned versions without review.

## Production workflow

1. Record the asset brief: silhouette, dimensions, component list, target engine, required texture maps, triangle budget, and inferred details. Do not invent reference evidence.
2. Block out large forms, render, and compare proportions before adding detail.
3. Prefer explicit data/BMesh operations; use correctly scoped operators when necessary. Probe version-sensitive APIs in Blender 4.5.14.
4. Use reusable geometry/material helpers. Export portable Principled/image-based materials. Bake Blender-only procedural effects when required.
5. Export GLB, reimport it, and render real previews. Use CPU Cycles on this Linux runner, not the upstream Workbench-only roundtrip path.
6. Use the upstream mesh validator on named, nonempty collections. The project adapter rejects an empty mesh selection rather than treating it as a pass.
7. Run `gltf_check.cjs` with Khronos glTF-Validator. Fail on errors; preserve and explain warnings. Do not hide warnings by changing severity.
8. Inspect PNGs for empty alpha and examine visuals. Technical success does not prove likeness, aesthetic quality or Godot runtime compatibility.

## Installed smoke/compatibility checks

`tools/blender/skills_qa.py` exercises the reliable-scripting helpers, the upstream mesh validator and a narrowly adapted CPU version of the upstream roundtrip script. It includes an expected negative-scale failure. `tools/blender/gltf_check.cjs` validates the real GLB and checks that corrupt GLB bytes are rejected.

This smoke test does not certify every upstream script, rigging, baking, animation, reference-image accuracy or performance gains. Retain all reports and report that limitation.

## Outputs and boundaries

Keep `.blend`, `.glb`, PNG textures, four GLB-derived previews, logs and JSON validation reports. No empty asset folders. Do not use generated illustration images as evidence of Blender geometry. No paid services, API credentials or private source images should enter this public CI workflow.
