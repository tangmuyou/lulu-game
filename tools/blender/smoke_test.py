"""Build, export, reimport and render a small test crate with real Blender.

Run: blender --background --factory-startup --python-exit-code 1 \
    --python tools/blender/smoke_test.py -- --output artifacts
This is a pipeline smoke test, not a finished game asset.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

import bpy
from mathutils import Vector


def arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="artifacts")
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    return parser.parse_args(args)


def material(name, color, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Roughness"].default_value = 0.58
    shader.inputs["Metallic"].default_value = metallic
    return mat


def box(name, location, dimensions, mat, bevel=0.05):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    modifier = obj.modifiers.new("Rounded edges", "BEVEL")
    modifier.width = bevel
    modifier.segments = 3
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    return obj


def aim(obj, point):
    obj.rotation_euler = (Vector(point) - obj.location).to_track_quat("-Z", "Y").to_euler()


def area(name, position, energy, size):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = position
    aim(obj, (0, 0, 0.65))


def main():
    out = Path(arguments().output).resolve()
    for subdir in ("model", "textures", "preview", "logs"):
        (out / subdir).mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system = "METRIC"

    wood = material("Warm wood", (0.58, 0.30, 0.13))
    green = material("Green bands", (0.13, 0.35, 0.24))
    brass = material("Brass latch", (0.70, 0.44, 0.12), 0.45)
    size = 128
    image = bpy.data.images.new("wood_basecolor", width=size, height=size, alpha=True)
    pixels = []
    for y in range(size):
        for x in range(size):
            grain = 0.93 + 0.04 * math.sin(x * 0.32 + math.sin(y * 0.06))
            pixels.extend((0.65 * grain, 0.39 * grain, 0.19 * grain, 1.0))
    image.pixels.foreach_set(pixels)
    image.filepath_raw = str(out / "textures" / "wood_basecolor.png")
    image.file_format = "PNG"
    image.save()
    tex = wood.node_tree.nodes.new("ShaderNodeTexImage")
    tex.image = image
    wood.node_tree.links.new(tex.outputs["Color"], wood.node_tree.nodes.get("Principled BSDF").inputs["Base Color"])

    assets = [box("Crate body", (0, 0, 0.60), (1.60, 1.20, 1.20), wood, 0.085)]
    assets.append(box("Crate lid", (0, 0, 1.23), (1.70, 1.30, 0.19), wood, 0.06))
    for x in (-0.52, 0.52):
        for y in (-0.608, 0.608):
            assets.append(box("Vertical band", (x, y, 0.64), (0.15, 0.055, 1.25), green, 0.018))
        assets.append(box("Top band", (x, 0, 1.332), (0.15, 1.26, 0.035), green, 0.012))
    assets.append(box("Latch", (0, -0.667, 1.05), (0.21, 0.08, 0.28), brass, 0.025))
    bpy.ops.object.select_all(action="DESELECT")
    for obj in assets:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = assets[0]
    glb_path = out / "model" / "cloud_test_crate.glb"
    bpy.ops.export_scene.gltf(filepath=str(glb_path), export_format="GLB", use_selection=True, export_apply=True)
    data = glb_path.read_bytes()
    magic, version, declared_size = struct.unpack_from("<4sII", data, 0)
    if (magic, version, declared_size) != (b"glTF", 2, len(data)):
        raise RuntimeError("Invalid GLB header")
    json_size, chunk_type = struct.unpack_from("<II", data, 12)
    if chunk_type != 0x4E4F534A:
        raise RuntimeError("GLB JSON chunk missing")
    gltf = json.loads(data[20:20 + json_size].decode("utf-8"))
    if not gltf.get("meshes") or not gltf.get("images"):
        raise RuntimeError("GLB is missing meshes or embedded texture")
    if any("uri" in img for img in gltf["images"]):
        raise RuntimeError("GLB unexpectedly depends on an external texture")

    # Preview the reimported GLB, not a separate look-alike scene.
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(glb_path))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not meshes or not any(len(obj.data.vertices) for obj in meshes):
        raise RuntimeError("Blender could not reimport non-empty geometry")
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 16
    scene.cycles.use_denoising = False
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 4
    scene.render.resolution_x = 512
    scene.render.resolution_y = 512
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = True
    scene.world = bpy.data.worlds.new("World")
    scene.world.use_nodes = True
    scene.world.node_tree.nodes.get("Background").inputs["Color"].default_value = (0.55, 0.62, 0.72, 1)
    scene.world.node_tree.nodes.get("Background").inputs["Strength"].default_value = 0.65
    area("Key", (-3, -4, 6), 650, 4)
    area("Fill", (4, -1, 4), 400, 3)
    area("Rim", (0, 4, 5), 500, 3)
    cam_data = bpy.data.cameras.new("Preview camera")
    camera = bpy.data.objects.new("Preview camera", cam_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = 2.8
    views = {
        "front": (3, -5, 3.0),
        "right": (5, 3, 3.0),
        "back": (-3, 5, 3.0),
        "left": (-5, -3, 3.0),
    }
    for name, position in views.items():
        camera.location = position
        aim(camera, (0, 0, 0.64))
        scene.render.filepath = str(out / "preview" / f"{name}.png")
        bpy.ops.render.render(write_still=True)
        if not Path(scene.render.filepath).is_file():
            raise RuntimeError(f"Missing rendered preview: {name}")
    camera.location = views["front"]
    aim(camera, (0, 0, 0.64))
    scene.render.filepath = "//../preview/front.png"
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(out / "model" / "cloud_test_crate.blend"))
    report = {
        "status": "passed",
        "purpose": "Blender cloud pipeline smoke test; not a finished game asset",
        "blender_version": bpy.app.version_string,
        "render_engine": "Cycles CPU",
        "mesh_objects_after_glb_reimport": len(meshes),
        "glb_bytes": len(data),
        "glb_sha256": hashlib.sha256(data).hexdigest(),
        "embedded_images": len(gltf["images"]),
        "previews_rendered_from_reimported_glb": list(views),
        "godot_runtime_tested": False,
    }
    (out / "validation.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("BLENDER_CLOUD_SMOKE_TEST_PASSED", json.dumps(report), flush=True)


if __name__ == "__main__":
    main()
