"""Exercise the installed skill scripts against the real smoke-test GLB.
Run inside Blender; upstream files remain unchanged.
"""
from __future__ import annotations
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import bpy

ROOT = Path(__file__).resolve().parents[2]
GAME = ROOT / "vendor/blender-game-skills/skills/blender-image-to-3d/scripts"
ROBUST = ROOT / "vendor/blender-claude-skill/blender/scripts/boilerplate.py"

def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def invoke(fn, args):
    try:
        fn(args)
        return 0
    except SystemExit as exc:
        return int(exc.code or 0)

def configure_cycles(scene):
    """Narrow CPU replacement for the upstream Workbench roundtrip renderer."""
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 12
    scene.cycles.use_denoising = False
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 4
    scene.world = bpy.data.worlds.new("QAWorld")
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (0.7, 0.7, 0.7, 1)
    bg.inputs["Strength"].default_value = 0.8
    mat = bpy.data.materials.new("QAClay")
    mat.use_nodes = True
    mat.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = (0.42, 0.42, 0.42, 1)
    scene.view_layers[0].material_override = mat
    lamp = bpy.data.lights.new("QA Sun", "SUN")
    lamp.energy = 2.0
    obj = bpy.data.objects.new("QA Sun", lamp)
    scene.collection.objects.link(obj)
    obj.rotation_euler = (0.45, -0.65, -0.35)

def main():
    a = argparse.ArgumentParser()
    a.add_argument("--output", default="artifacts")
    args = a.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    out = Path(args.output).resolve()
    qa = out / "qa"
    qa.mkdir(parents=True, exist_ok=True)
    glb = out / "model/cloud_test_crate.glb"
    if not glb.is_file():
        raise RuntimeError("Run the original Blender smoke test first")
    helpers = load_module(ROBUST, "lulu_robust_helpers")
    helpers.clean_scene()
    bpy.ops.import_scene.gltf(filepath=str(glb))
    bpy.context.view_layer.update()
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    if not meshes:
        raise RuntimeError("No imported meshes: empty validation is not a pass")
    lo, hi = helpers.scene_bounds()
    height = hi.z - lo.z
    if height <= 0:
        raise RuntimeError("Invalid bounds from installed helper")
    helpers.add_framing_camera()
    helpers.report_scene()
    low = bpy.data.collections.new("LOW")
    bpy.context.scene.collection.children.link(low)
    for ob in meshes:
        low.objects.link(ob)
    master = qa / "validation_input.blend"
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(master))
    validator = load_module(GAME / "validate.py", "lulu_mesh_validator")
    def validate(blend, report):
        options = validator.parse(["--blend", str(blend), "--collections", "LOW", "--out", str(report), "--budget-tris", "10000", "--require-uv"])
        code = invoke(validator.main, options)
        data = json.loads(report.read_text())
        if not any(o.get("type") == "MESH" for o in data.get("objects", [])):
            raise RuntimeError("The upstream validator checked no meshes")
        return code, data
    ok_code, good = validate(master, qa / "mesh_validation.json")
    if ok_code or good["summary"]["fail"]:
        raise RuntimeError("Valid smoke-test mesh failed skill validation")
    first = next(o for o in bpy.context.scene.objects if o.type == "MESH")
    first.scale.x = -abs(first.scale.x)
    negative = qa / "negative_scale_input.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(negative))
    bad_code, bad = validate(negative, qa / "expected_negative_scale.json")
    caught_negative = bad_code != 0 and any("negative scale" in msg for msg in bad["summary"]["fail"])
    if not caught_negative:
        raise RuntimeError("The mesh validator failed to reject intentional negative scale")
    source_path = GAME / "roundtrip.py"
    source = source_path.read_text(encoding="utf-8")
    old = 'scene.render.engine = "BLENDER_WORKBENCH"'
    if source.count(old) != 1:
        raise RuntimeError("Upstream roundtrip changed: review the CPU adapter")
    source = source.replace(old, "configure_cycles(scene)", 1)
    namespace = {"__name__": "lulu_roundtrip_cpu", "__file__": str(source_path), "configure_cycles": configure_cycles}
    exec(compile(source, str(source_path) + ":cpu-adapter", "exec"), namespace)
    rt_dir = qa / "roundtrip"
    rt_args = namespace["parse"](["--file", str(glb), "--out", str(rt_dir), "--res", "384", "--expect-height", str(height)])
    rt_code = invoke(namespace["main"], rt_args)
    rt = json.loads((rt_dir / "roundtrip.json").read_text())
    if rt_code or rt.get("errors") or not rt.get("meshes"):
        raise RuntimeError("CPU-adapted upstream roundtrip failed")
    if not (rt_dir / "roundtrip_clay_threequarter.png").is_file():
        raise RuntimeError("Missing actual CPU roundtrip preview")
    report = {"status": "passed", "blender_version": bpy.app.version_string,
              "installed_robust_helpers_exercised": ["clean_scene", "scene_bounds", "add_framing_camera", "report_scene"],
              "upstream_mesh_validation": "passed", "mesh_objects_checked": len(meshes),
              "mesh_warnings": good["summary"]["warn"], "negative_scale_rejected": caught_negative,
              "roundtrip_cpu_adapter": "passed", "roundtrip_mesh_objects": len(rt["meshes"]),
              "upstream_files_modified": False, "godot_runtime_tested": False,
              "not_tested": ["all upstream functions", "reference-image likeness", "rigging", "baking", "animation", "speedup benchmark"]}
    (out / "skills_qa.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("BLENDER_SKILLS_QA_PASSED", json.dumps(report), flush=True)

if __name__ == "__main__":
    main()
