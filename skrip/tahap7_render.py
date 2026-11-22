r"""Tahap 7 langkah 7.8: render akhir fotorealistis dari IFC federasi (Blender + Bonsai, Cycles).

Pakai (mode latar, satu kamera per proses supaya tiap render dibatasi waktunya):
  alat\blender\blender.exe -b --python skrip\tahap7_render.py -- --kamera R-01 [--uji] [--blend] [--jangkar]
  --uji     resolusi 960 px, 24 sampel (render uji); tanpa --uji: 3.200 x 1.800 px
  --blend   simpan adegan ke render/RSTB-Render-T7.blend (tanpa render)
  --jangkar cetak titik acuan (logo, IGD, air, gedung) ke cache/tahap7_render/jangkar.json lalu keluar
Keluaran: `07 DED dan RKS/Render/R-0x.png`. Sumber geometri tetap IFC federasi 7.2 (`model/RSTB-FED-T7.ifc`);
material, langit, lampu, kamera, dan tanah sekitar tapak hanya ada di berkas Blender (IFC tidak diubah).
"""
import json
from collections import Counter
import math
import sys
import time
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tahap7_render_detail as detail  # noqa: E402
from mathutils import Vector

AKAR = Path(__file__).resolve().parents[1]
IFC = AKAR / "model" / "RSTB-FED-T7.ifc"
KELUAR = AKAR / "07 DED dan RKS" / "Render"
BLEND = AKAR / "render" / "RSTB-Render-T7.blend"
CACHE = AKAR / "cache" / "tahap7_render"
arg = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
UJI, SIMPAN, JANGKAR = "--uji" in arg, "--blend" in arg, "--jangkar" in arg
KAMERA = arg[arg.index("--kamera") + 1] if "--kamera" in arg else "R-01"
CPU = "--cpu" in arg
VIDEO = KAMERA.startswith("V-")  # shot video: --kamera V-01..V-06 [--uji: 640 px, tiap frame ke-6]
VIDEO_DIR = AKAR / "07 DED dan RKS" / "Video" / "frame"
BATAS_DETIK = 540  # shortcut: batas waktu Cycles per render (±10 menit termasuk impor), naikkan bila hasil berbintik

SEMBUNYI = ("IfcSpace", "IfcVirtualElement", "IfcOpeningElement", "IfcGrid", "IfcGridAxis", "IfcPile", "IfcFooting")
TANAH = 12.05  # muka halaman (3.3)

# nama material IFC (BIMCraft) -> (warna RGB linear, kekasaran, logam, emisi senja)
MAT = {
    "Panel putih": ((0.80, 0.80, 0.78), 0.35, 0.0, 0),
    "Panel abu": ((0.32, 0.33, 0.34), 0.45, 0.0, 0),
    "Panel abu tua": ((0.10, 0.10, 0.11), 0.45, 0.0, 0),
    "Kaca pita": ((0.02, 0.05, 0.09), 0.04, 0.0, 6.0),
    "Kaca biru": ((0.02, 0.08, 0.20), 0.04, 0.0, 2.5),
    "Rumput": ((0.07, 0.17, 0.03), 0.9, 0.0, 0),
    "Aspal": ((0.035, 0.035, 0.04), 0.85, 0.0, 0),
    "Paving": ((0.30, 0.27, 0.24), 0.8, 0.0, 0),
    "Beton ekspos": ((0.42, 0.41, 0.39), 0.75, 0.0, 0),
    "Tanah lereng": ((0.07, 0.08, 0.03), 0.95, 0.0, 0),
    "Air sungai": ((0.020, 0.022, 0.016), 0.16, 0.0, 0),
    "Daun": ((0.04, 0.12, 0.03), 0.7, 0.0, 0),
    "Batang": ((0.10, 0.06, 0.03), 0.9, 0.0, 0),
    "Logo biru": ((0.01, 0.10, 0.45), 0.3, 0.0, 3.0),
    "Huruf putih": ((0.9, 0.9, 0.9), 0.3, 0.0, 6.0),
    "Cahaya": ((1.0, 0.85, 0.6), 0.3, 0.0, 25.0),
    "Pagar": ((0.06, 0.06, 0.06), 0.4, 0.8, 0),
    "Tiang lampu": ((0.08, 0.08, 0.08), 0.4, 0.8, 0),
    "Kanopi": ((0.75, 0.75, 0.75), 0.3, 0.2, 0),
    "Aluminium dek": ((0.55, 0.56, 0.58), 0.35, 1.0, 0),
    "Marka putih": ((0.85, 0.85, 0.85), 0.6, 0.0, 0),
    "Marka kuning": ((0.85, 0.55, 0.02), 0.6, 0.0, 0),
    "Tanah taman": ((0.06, 0.13, 0.03), 0.9, 0.0, 0),
    "Mobil putih": ((0.80, 0.80, 0.80), 0.2, 0.3, 0),
    "Mobil hitam": ((0.02, 0.02, 0.02), 0.2, 0.3, 0),
    "Mobil merah": ((0.45, 0.02, 0.02), 0.2, 0.3, 0),
    "Mobil abu": ((0.25, 0.26, 0.27), 0.2, 0.3, 0),
    "Mobil hijau": ((0.03, 0.15, 0.10), 0.2, 0.3, 0),
}
BETON = ((0.45, 0.44, 0.42), 0.7, 0.0, 0)


def senja():
    return detail.lampu_buatan(KAMERA)


def mat_pbr(m, warna, kasar, logam, emisi):
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    b.inputs["Base Color"].default_value = (*warna, 1)
    b.inputs["Roughness"].default_value = kasar
    b.inputs["Metallic"].default_value = logam
    if m.name.startswith(("Kaca", "Air")):
        b.inputs["Coat Weight"].default_value = 1.0
        b.inputs["IOR"].default_value = 1.52
    if m.name.startswith("Mobil"):
        b.inputs["Coat Weight"].default_value = 1.0
    if m.name in ("Rumput", "Aspal", "Tanah lereng", "Paving", "Air sungai"):  # variasi agar tidak datar
        tx = nt.nodes.new("ShaderNodeTexNoise")
        tx.inputs["Scale"].default_value = 0.08 if m.name == "Air sungai" else 2.5
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.35 if m.name == "Air sungai" else 0.3
        nt.links.new(tx.outputs["Fac"], bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        sok = {s.name: s for s in mix.inputs if s.type == "RGBA"}  # Mix punya socket A/B float, vektor, dan warna
        sok["A"].default_value = (*[c * 0.7 for c in warna], 1)
        sok["B"].default_value = (*[min(1, c * 1.3) for c in warna], 1)
        nt.links.new(tx.outputs["Fac"], mix.inputs["Factor"])
        nt.links.new([s for s in mix.outputs if s.type == "RGBA"][0], b.inputs["Base Color"])
    if emisi and senja():
        b.inputs["Emission Color"].default_value = (1.0, 0.78, 0.5, 1) if m.name.startswith("Kaca") else (*warna, 1)
        b.inputs["Emission Strength"].default_value = emisi
    nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])


def muat_ifc():
    """Muat IFC lewat Bonsai, atau pakai .blend dasar (Colab, tanpa Bonsai): kelas IFC disimpan di properti objek."""
    if any("ifc" in ob for ob in bpy.data.objects):
        return {ob.name: ob["ifc"] for ob in bpy.data.objects if "ifc" in ob}
    bpy.ops.bim.load_project(filepath=str(IFC))
    from bonsai.bim.ifc import IfcStore
    f = IfcStore.get_file()
    kelas = {}
    for ob in bpy.data.objects:
        p = getattr(ob, "BIMObjectProperties", None)
        i = p.ifc_definition_id if p else 0
        if i:
            kelas[ob.name] = f.by_id(i).is_a()
            ob["ifc"] = kelas[ob.name]
    return kelas


def bbox(obs):
    pts = [ob.matrix_world @ Vector(c) for ob in obs for c in ob.bound_box]
    return Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)])


def siapkan_objek(kelas):
    tampil = []
    for ob in bpy.data.objects:
        if ob.type != "MESH":
            continue
        k = kelas.get(ob.name, "")
        lo, hi = bbox([ob])
        tebing = any(s.material and s.material.name.startswith(("Air sungai", "Tanah lereng")) for s in ob.material_slots)
        if k.startswith(SEMBUNYI) or k.endswith("Type") or (hi.z < TANAH - 0.2 and not tebing):
            ob.hide_render = ob.hide_viewport = True
            continue
        tampil.append(ob)
    beton = bpy.data.materials.new("Beton")
    mat_pbr(beton, *BETON)
    for m in list(bpy.data.materials):
        if m.name == "Beton":
            continue
        dasar = m.name.split(".")[0]
        if dasar in MAT:
            mat_pbr(m, *MAT[dasar])
        else:  # interior/pintu/lantai: warna gaya IFC, permukaan matte
            mat_pbr(m, tuple(m.diffuse_color[:3]), 0.6, 0.0, 0)
    lereng = bpy.data.materials.get("Tanah lereng")
    for ob in tampil:
        if lereng and "TP-Lereng" in ob.name:  # gaya permukaan IFC lereng tidak selalu bernama sama
            for s in ob.material_slots:
                s.material = lereng
        if not ob.material_slots or not any(s.material for s in ob.material_slots):
            ob.data.materials.clear()
            ob.data.materials.append(beton)
    return tampil


def cari(nama):
    return [ob for ob in bpy.data.objects if not ob.hide_render and any(
        s.material and s.material.name.split(".")[0] == nama for s in ob.material_slots)]


def jangkar(tampil):
    gedung = cari("Panel putih") + cari("Kaca biru") + cari("Panel abu")
    g0, g1 = bbox(gedung)
    air0, air1 = bbox(cari("Air sungai"))
    logo = [((lo + hi) / 2) for lo, hi in (bbox([o]) for o in cari("Logo biru"))]
    kan0, kan1 = bbox(cari("Kanopi"))
    lampu = [tuple((bbox([o])[1])) for o in cari("Cahaya")]
    tp0, tp1 = bbox(cari("Rumput"))
    heli0, heli1 = bbox(cari("Aluminium dek")) if cari("Aluminium dek") else (g1, g1)
    j = {"gedung": [list(g0), list(g1)], "air": [list(air0), list(air1)], "logo": [list(p) for p in logo],
         "kanopi": [list(kan0), list(kan1)], "lampu": lampu, "helipad": [list(heli0), list(heli1)], "tapak": [list(tp0), list(tp1)]}
    return j


def pohon_prosedural():
    """Ganti keluarga pohon BIMCraft (silinder bertumpuk) dengan pohon tajuk acak di titik yang sama (tampilan saja).

    Tiga templat tinggi 1 m dibuat sekali (batang + 6 tajuk ber-displace, digabung), lalu disalin berbagi mesh.
    """
    import random
    rnd = random.Random(3)
    daun = bpy.data.materials.get("Daun") or bpy.data.materials["Beton"]
    batang = bpy.data.materials.get("Batang") or bpy.data.materials["Beton"]
    tx = bpy.data.textures.new("tajuk", "VORONOI")
    tx.noise_scale = 0.12
    templat = []
    for n in range(3):
        bagian = []
        bpy.ops.mesh.primitive_cylinder_add(radius=0.025, depth=0.55, location=(0, 0, 0.27), vertices=8)
        bpy.context.object.data.materials.append(batang)
        bagian.append(bpy.context.object)
        for k in range(6):
            r = rnd.uniform(0.16, 0.24)
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=r, location=(
                rnd.uniform(-0.14, 0.14), rnd.uniform(-0.14, 0.14), rnd.uniform(0.55, 0.85)))
            s = bpy.context.object
            m = s.modifiers.new("acak", "DISPLACE")
            m.texture, m.strength = tx, r * 0.35
            bpy.ops.object.modifier_apply(modifier="acak")
            s.data.materials.append(daun)
            bpy.ops.object.shade_smooth()
            bagian.append(s)
        bpy.ops.object.select_all(action="DESELECT")
        for o in bagian:
            o.select_set(True)
        bpy.context.view_layer.objects.active = bagian[0]
        bpy.ops.object.join()
        tp = bpy.context.object
        tp.name = f"Pohon render templat {n}"
        tp.hide_render = tp.hide_viewport = True
        templat.append(tp)
    for ob in [o for o in bpy.data.objects if "Pohon" in o.name and "render" not in o.name and not o.hide_render]:
        lo, hi = bbox([ob])
        h = hi.z - lo.z
        ob.hide_render = ob.hide_viewport = True
        d = rnd.choice(templat).copy()
        d.name = f"Pohon render {ob.name}"
        d.hide_render = d.hide_viewport = False
        d.location = ((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z)
        d.scale = (h, h, h)
        d.rotation_euler.z = rnd.uniform(0, 6.28)
        bpy.context.collection.objects.link(d)


def tanah_sekitar(j):
    """Tanah dan sungai di luar tapak (konteks render, bukan model BIM)."""
    g0, g1 = Vector(j["gedung"][0]), Vector(j["gedung"][1])
    a0, a1 = Vector(j["air"][0]), Vector(j["air"][1])
    zair = a1.z
    tepi = a1.y  # sungai di sisi -y (render 7.1)

    def bidang(nama, x0, x1, y0, y1, z, mat):
        bpy.ops.mesh.primitive_plane_add(size=1, location=((x0 + x1) / 2, (y0 + y1) / 2, z))
        ob = bpy.context.object
        ob.name = nama
        ob.scale = (x1 - x0, y1 - y0, 1)
        ob.data.materials.append(bpy.data.materials.get(mat) or bpy.data.materials["Beton"])
        return ob
    lebar = 320.0  # [Asumsi: lebar Batanghari di Jambi ±300 m, konteks render]
    t0, t1 = Vector(j["tapak"][0]), Vector(j["tapak"][1])
    x0, x1, yu = min(t0.x, a0.x) - 0.5, max(t1.x, a1.x) + 0.5, t1.y + 0.5  # batas persil (tanpa celah)
    bidang("Konteks sungai", -10000, 10000, tepi - lebar, tepi + 0.5, zair - 0.02, "Air sungai")
    bidang("Konteks tanah utara", -10000, 10000, yu + 12, 10000, TANAH - 0.03, "Rumput")
    bidang("Konteks jalan", -10000, 10000, yu, yu + 12, TANAH - 0.01, "Aspal")  # [Asumsi: jalan kota di utara]
    bidang("Konteks tanah bawah tapak", -10000, 10000, t0.y, yu, TANAH - 0.06, "Rumput")  # menutup celah tepi persil
    # tebing menerus di bawah pelat lereng model (menutup celah antarpelat) dan di luar persil [konteks render]
    me = bpy.data.meshes.new("Konteks tebing")
    me.from_pydata([(-10000, t0.y + 0.5, TANAH - 0.25), (10000, t0.y + 0.5, TANAH - 0.25),
                    (10000, -22.0, zair - 0.3), (-10000, -22.0, zair - 0.3)], [], [(0, 1, 2, 3)])
    tb = bpy.data.objects.new("Konteks tebing", me)
    me.materials.append(bpy.data.materials.get("Tanah lereng") or bpy.data.materials["Rumput"])
    bpy.context.scene.collection.objects.link(tb)
    # lajur batu kali (riprap) di garis air, 3 m ke atas lereng
    me = bpy.data.meshes.new("Konteks batu kali")
    z1 = zair + 3.0 * (TANAH - zair) / (t0.y + 22.5)
    me.from_pydata([(-10000, -19.0, z1 - 0.2), (10000, -19.0, z1 - 0.2), (10000, -23.0, zair - 0.45), (-10000, -23.0, zair - 0.45)],
                   [], [(0, 1, 2, 3)])
    bk = bpy.data.objects.new("Konteks batu kali", me)
    bk_m = bpy.data.materials.get("Batu kali") or bpy.data.materials.new("Batu kali")
    me.materials.append(bk_m)
    bpy.context.scene.collection.objects.link(bk)
    bidang("Konteks seberang", -10000, 10000, -10000, tepi - lebar, zair + 2.0, "Rumput")


def langit_dan_matahari(j):
    sc = bpy.context.scene
    w = bpy.data.worlds.new("Langit") if not sc.world else sc.world
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    sky = nt.nodes.new("ShaderNodeTexSky")
    for jenis in ("MULTIPLE_SCATTERING", "SINGLE_SCATTERING", "NISHITA", "HOSEK_WILKIE"):
        try:
            sky.sky_type = jenis
            break
        except TypeError:
            continue
    elev = math.radians(3.5 if senja() else 42)
    azim = math.radians(255 if senja() else 135)  # senja: matahari barat; siang: tenggara-timur laut
    if hasattr(sky, "sun_elevation"):
        sky.sun_elevation, sky.sun_rotation = elev, azim
    bg.inputs["Strength"].default_value = 0.12 if senja() else 0.22
    nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    bpy.ops.object.light_add(type="SUN")
    sun = bpy.context.object
    sun.data.energy = 0.8 if senja() else 3.2
    sun.data.angle = math.radians(0.6)
    sun.data.color = (1.0, 0.72, 0.52) if senja() else (1.0, 0.96, 0.9)
    sun.rotation_euler = (math.pi / 2 - elev, 0, azim + math.pi / 2)
    if senja():
        for p in j["lampu"]:
            bpy.ops.object.light_add(type="POINT", location=(p[0], p[1], p[2] - 0.3))
            L = bpy.context.object
            L.data.energy, L.data.color, L.data.shadow_soft_size = 1500, (1.0, 0.75, 0.45), 0.3


def kamera(j):
    """Titik kamera dihitung dari jangkar model; lensa mm."""
    g0, g1 = Vector(j["gedung"][0]), Vector(j["gedung"][1])
    c = (g0 + g1) / 2
    h0, h1 = Vector(j["helipad"][0]), Vector(j["helipad"][1])
    hc = (h0 + h1) / 2
    mata = TANAH + 1.7
    tepi = j["air"][1][1]
    # koordinat dari jangkar 7.1: huruf nama di muka selatan menara (y 26, sisi sungai), lobi dan gerbang di utara
    # (x 50-58, y 76-90), IGD di timur (kanopi x 85-92, y 35-45; ramp x 92-98), parkir tenggara (x 97-129, y 30-42)
    d = {
        "R-01": ((118, -95, 15), (55, 36, TANAH + 12), 32),  # siang 3/4 dari atas sungai (nama terbaca)
        "R-02": ((-48, -32, 24), (58, 46, TANAH + 12), 28),                    # senja barat daya
        "R-03": ((c.x + 40, tepi - 170, 140), (c.x - 10, c.y, TANAH + 5), 30),   # mata burung dari sungai
        "R-04": ((66, 118, mata + 1.5), (54, 76, TANAH + 7), 24),                 # depan lobi dan gerbang utara
        "R-05": ((118, 30, mata + 0.5), (90, 40, TANAH + 4), 22),                 # IGD, kanopi, ramp
        "R-06": ((hc.x - 55, hc.y - 70, h1.z + 45), (hc.x, hc.y, h1.z), 35),     # helipad atap
        "R-07": ((c.x - 120, tepi - 140, 95), (c.x, c.y, TANAH + 10), 28),       # senja mata burung
        "R-08": ((c.x - 20, tepi - 300, j["air"][1][2] + 4), (c.x - 15, c.y, TANAH + 16), 60),  # dari seberang sungai
    }
    pos, sasaran, lensa = d[KAMERA]
    bpy.ops.object.camera_add(location=pos)
    cam = bpy.context.object
    arah = Vector(sasaran) - Vector(pos)
    cam.rotation_euler = arah.to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = lensa
    cam.data.clip_end = 20000
    bpy.context.scene.camera = cam
    return cam


def setel_render():
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    cy = sc.cycles
    try:
        pref = bpy.context.preferences.addons["cycles"].preferences
        for jenis in ("OPTIX", "CUDA"):
            try:
                pref.compute_device_type = jenis
                pref.get_devices()
                if any(dv.type == jenis for dv in pref.devices):
                    for dv in pref.devices:
                        dv.use = dv.type == jenis
                    cy.device = "GPU"
                    break
            except TypeError:
                continue
    except KeyError:
        pass
    if CPU:  # GPU laptop tidak bisa dipakai beban lama (22 Nov 2026): Cycles CPU, hasil identik
        cy.device = "CPU"
    cy.samples = 24 if UJI else 128
    cy.use_adaptive_sampling = True
    cy.adaptive_threshold = 0.02
    sc.render.threads_mode, sc.render.threads = "FIXED", 8  # laptop mati karena panas 22 Nov 2026: CPU tidak dipakai penuh
    cy.use_denoising = True
    cy.time_limit = BATAS_DETIK
    cy.max_bounces = 6
    sc.render.resolution_x, sc.render.resolution_y = (960, 540) if UJI else (3200, 1800)
    sc.render.resolution_percentage = 100
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast" if not senja() else "AgX - Base Contrast"
    sc.view_settings.exposure = {"siang": 0.0, "emas": 0.0, "biru": -0.8}[detail.suasana(KAMERA)]
    sc.render.image_settings.file_format = "PNG"


def main():
    t0 = time.time()
    kelas = muat_ifc()
    if "--dasar" in arg:  # simpan model IFC sebagai .blend dasar untuk render di Colab (tanpa Bonsai)
        bpy.ops.wm.save_as_mainfile(filepath=str(AKAR / "render" / "RSTB-Dasar-T7.blend"), compress=True)
        print("DASAR disimpan")
        return
    tampil = siapkan_objek(kelas)
    j = jangkar(tampil)
    CACHE.mkdir(parents=True, exist_ok=True)
    if JANGKAR:
        (CACHE / "jangkar.json").write_text(json.dumps(j, indent=1), encoding="utf-8")
        print("jangkar ditulis", CACHE / "jangkar.json")
        return
    print("WAKTU impor+material", round(time.time() - t0, 1))
    tanah_sekitar(j)
    if VIDEO:
        cam, n_frame = detail.video_kamera(KAMERA)
    else:
        cam = kamera(j)
        detail.dua_titik_hilang(cam, TANAH + 30)
    detail.material_scene(KAMERA)
    if detail.langit_hdri(KAMERA, cam) is None:  # aset belum diunduh: langit prosedural lama
        langit_dan_matahari(j)
    n_kend = detail.kendaraan()
    n_veg = detail.vegetasi(j, cam, KAMERA)
    detail.papan_nama(KAMERA)
    n_mul = detail.mullion()
    n_lampu = detail.lampu_senja(j, KAMERA)
    print("DETAIL kendaraan", n_kend, "vegetasi", n_veg, "kaca bermullion", n_mul, "lampu", n_lampu)
    setel_render()
    if "--pasca" in arg:
        detail.pasca_olah()
    if VIDEO:
        keluar = VIDEO_DIR / (KAMERA + (" uji" if UJI else ""))
        keluar.mkdir(parents=True, exist_ok=True)
        detail.setel_eevee(keluar)
        sc = bpy.context.scene
        if "--video-cycles" in arg:  # Eevee gagal tanpa layar: Cycles 1080p, sampel rendah + denoiser
            sc.render.engine = "CYCLES"
            sc.cycles.device, sc.cycles.samples, sc.cycles.use_denoising = "GPU", 48, True
        sc.view_settings.view_transform = "AgX"
        sc.view_settings.look = "AgX - Medium High Contrast"
        if UJI:
            sc.render.resolution_percentage, sc.frame_step = 33, 6
        print("WAKTU siap video", round(time.time() - t0, 1), "frame", n_frame, sc.render.engine)
        detail.video_per_frame(keluar, sc.frame_step)
        print("VIDEO SELESAI", KAMERA, round(time.time() - t0, 1))
        return
    if SIMPAN:
        BLEND.parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(BLEND), compress=True)
        print("blend disimpan", BLEND)
        return
    KELUAR.mkdir(parents=True, exist_ok=True)
    png = KELUAR / (f"uji {KAMERA}.png" if UJI else f"{KAMERA}.png")
    bpy.context.scene.render.filepath = str(png)
    print("WAKTU siap render", round(time.time() - t0, 1))
    if UJI or CPU or not sys.platform.startswith("win"):  # Colab: GPU sehat, render langsung
        bpy.ops.render.render(write_still=True)
    else:
        detail.render_berdenyut(png)
    catat = {"kamera": KAMERA, "uji": UJI, "detik": round(time.time() - t0, 1), "png": png.name,
             "objek_tampil": len(tampil), "perangkat": bpy.context.scene.cycles.device,
             "kelas_ifc": dict(Counter(kelas.values()))}  # T-117: dibandingkan dengan ifcopenshell di uji
    (CACHE / f"log {KAMERA}{' uji' if UJI else ''}.json").write_text(json.dumps(catat), encoding="utf-8")
    print("RENDER SELESAI", catat)


main()
