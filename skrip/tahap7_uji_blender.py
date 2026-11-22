r"""Tahap 7 langkah 7.2: uji alur Blender + Bonsai pada IFC federasi (pratinjau T-117, bukan render akhir 7.8).

Pakai (mode latar):  alat\blender\blender.exe -b --python skrip\tahap7_uji_blender.py -- model\RSTB-FED-T7.ifc
Keluaran: `07 DED dan RKS/Gambar/7.2 Uji Blender.png` dan `cache/tahap7_federasi/uji_blender.json` (jumlah unsur per
kelas di Blender, waktu impor dan render, material).
"""
import json
import sys
import time
from collections import Counter
from pathlib import Path

import bpy
from mathutils import Vector

AKAR = Path(__file__).resolve().parents[1]
arg = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
BERKAS = Path(arg[0]) if arg else AKAR / "model" / "RSTB-FED-T7.ifc"
if not BERKAS.is_absolute():
    BERKAS = AKAR / BERKAS
PNG = AKAR / "07 DED dan RKS" / "Gambar" / "7.2 Uji Blender.png"
JSON = AKAR / "cache" / "tahap7_federasi" / "uji_blender.json"

hasil = {"berkas": BERKAS.name}
t0 = time.time()
bpy.ops.bim.load_project(filepath=str(BERKAS))
hasil["impor_s"] = round(time.time() - t0, 1)

from bonsai.bim.ifc import IfcStore  # noqa: E402

f = IfcStore.get_file()
kelas, tanpa_mesh, mat = Counter(), 0, Counter()
for ob in bpy.data.objects:
    i = ob.BIMObjectProperties.ifc_definition_id if hasattr(ob, "BIMObjectProperties") else 0
    if not i:
        continue
    e = f.by_id(i)
    kelas[e.is_a()] += 1
    if ob.type == "MESH":
        mat["dengan material" if ob.material_slots and any(s.material for s in ob.material_slots) else "tanpa material"] += 1
        if e.is_a("IfcSpace") or e.is_a("IfcOpeningElement") or e.is_a("IfcVirtualElement"):
            ob.hide_render = True
    elif e.is_a("IfcElement"):
        tanpa_mesh += 1
hasil["kelas_blender"] = dict(kelas)
hasil["unsur_tanpa_mesh"] = tanpa_mesh
hasil["material"] = dict(mat)

# kamera tiga perempat dari timur laut (arah jalan masuk utara), batas dari objek mesh yang dirender
mesh = [o for o in bpy.data.objects if o.type == "MESH" and not o.hide_render]
pts = [o.matrix_world @ Vector(c) for o in mesh for c in o.bound_box]
lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
pusat, uk = (lo + hi) / 2, hi - lo
hasil["batas_m"] = [round(v, 1) for v in (*lo, *hi)]
sc = bpy.context.scene
cam = bpy.data.objects.new("Kamera Uji", bpy.data.cameras.new("Kamera Uji"))
sc.collection.objects.link(cam)
cam.location = pusat + Vector((0.75 * uk.x, 0.95 * uk.y, 0.55 * max(uk.x, uk.y)))
cam.rotation_euler = (pusat - cam.location).to_track_quat("-Z", "Y").to_euler()
cam.data.lens = 32
sc.camera = cam
sun = bpy.data.objects.new("Matahari", bpy.data.lights.new("Matahari", "SUN"))
sun.data.energy = 3.5
sun.rotation_euler = (0.8, 0.2, 2.3)
sc.collection.objects.link(sun)
if sc.world is None:
    sc.world = bpy.data.worlds.new("Langit")
sc.world.use_nodes = True
sc.world.node_tree.nodes["Background"].inputs[0].default_value = (0.62, 0.74, 0.9, 1)
sc.world.node_tree.nodes["Background"].inputs[1].default_value = 0.8
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1600, 1000, 100
mesin = None
for nama in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
    try:
        sc.render.engine = nama
        mesin = nama
        break
    except TypeError:
        continue
if mesin is None:
    sc.render.engine, mesin = "CYCLES", "CYCLES"
    sc.cycles.samples = 16
sc.render.filepath = str(PNG)
PNG.parent.mkdir(parents=True, exist_ok=True)
t1 = time.time()
try:
    bpy.ops.render.render(write_still=True)
except Exception as galat:  # Eevee tanpa GPU di mode latar: ulang dengan Cycles sampel rendah
    hasil["galat_eevee"] = str(galat)[:200]
    sc.render.engine, mesin = "CYCLES", "CYCLES"
    sc.cycles.samples = 16
    bpy.ops.render.render(write_still=True)
hasil["mesin"] = mesin
hasil["render_s"] = round(time.time() - t1, 1)
JSON.parent.mkdir(parents=True, exist_ok=True)
JSON.write_text(json.dumps(hasil, indent=1, ensure_ascii=False), encoding="utf-8")
print("UJI_BLENDER", json.dumps(hasil, ensure_ascii=False))
