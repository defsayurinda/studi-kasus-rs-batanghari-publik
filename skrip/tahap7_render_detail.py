r"""Tahap 7 langkah 7.8 (revisi): detail render setara archviz, dipanggil dari `tahap7_render.py` di dalam Blender.

Isi (hanya di adegan Blender; IFC tidak diubah):
- langit HDRI Poly Haven (CC0, `skrip/aset_render.py`) diputar supaya matahari menyinari fasad yang dilihat kamera;
- tekstur PBR (aspal, rumput, paving, beton, tanah) dengan pemetaan dunia dan variasi makro anti-ulang;
- pohon/semak/rumput glTF menggantikan keluarga pohon BIMCraft (silinder bertumpuk);
- mobil dan motor berbentuk (loft penampang superelips, roda, kaca, lampu) menggantikan kotak;
- papan nama huruf asli (Segoe UI Bold) dan panel logo H menggantikan huruf piksel;
- mullion fasad dan kaca berinterior (jendela menyala saat senja);
- lampu senja (downlight kanopi, wall-washer fasad, lampu jalan) dan kamera dua titik hilang.
"""
import math
import random
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector

AKAR = Path(__file__).resolve().parents[1]
ASET = AKAR / "alat" / "aset-render"
FONT = next((f for f in (Path(r"C:\Windows\Fonts\segoeuib.ttf"), AKAR / "alat" / "aset-render" / "font" / "segoeuib.ttf",
                          Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf")) if f.exists()), Path("-"))

# suasana per kamera: (HDRI, kekuatan, sudut matahari relatif kamera [derajat, + = dari kanan], lampu buatan)
SUASANA = {
    "siang": ("kloofendal_48d_partly_cloudy_puresky", 1.0, False),
    "emas": ("lonely_road_afternoon_puresky", 1.0, False),  # sore: lampu belum menyala
    "biru": ("qwantani_dusk_2_puresky", 0.55, True),
}
KAMERA_SUASANA = {"R-01": "siang", "R-02": "emas", "R-03": "siang", "R-04": "biru", "R-05": "biru",
                  "R-06": "siang", "R-07": "emas", "R-08": "siang"}
SUDUT_MATAHARI = {"R-01": 55, "R-02": -75, "R-03": 50, "R-04": 70, "R-05": -70, "R-06": 60, "R-07": -45, "R-08": 40}


def suasana(kamera):
    return KAMERA_SUASANA.get(kamera, "siang")


def lampu_buatan(kamera):
    return SUASANA[suasana(kamera)][2]


# ------------------------------------------------------------------ material
def _nodes(m):
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])
    return nt, bsdf


def _gambar(nt, path, warna=True):
    n = nt.nodes.new("ShaderNodeTexImage")
    n.image = bpy.data.images.load(str(path), check_existing=True)
    if not warna:
        n.image.colorspace_settings.name = "Non-Color"
    n.projection = "BOX"
    n.projection_blend = 0.25
    return n


def tekstur_pbr(m, nama, skala, kali=(1, 1, 1), kasar_tambah=0.0, normal=0.6, hue=0.5, sat=1.0):
    """Material bertekstur Poly Haven, koordinat dunia (box), variasi warna makro supaya tidak tampak berulang."""
    d = ASET / "tekstur" / nama
    if not d.exists():
        return False
    nt, bsdf = _nodes(m)
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1 / skala,) * 3
    nt.links.new(geo.outputs["Position"], mp.inputs["Vector"])
    dif = _gambar(nt, d / f"{nama}_diff_2k.jpg")
    nt.links.new(mp.outputs[0], dif.inputs[0])
    hs = nt.nodes.new("ShaderNodeHueSaturation")
    hs.inputs["Hue"].default_value, hs.inputs["Saturation"].default_value = hue, sat
    nt.links.new(dif.outputs[0], hs.inputs["Color"])
    makro = nt.nodes.new("ShaderNodeTexNoise")
    makro.inputs["Scale"].default_value = 0.035
    makro.inputs["Detail"].default_value = 3
    nt.links.new(geo.outputs["Position"], makro.inputs["Vector"])
    rp = nt.nodes.new("ShaderNodeMapRange")
    rp.inputs["To Min"].default_value, rp.inputs["To Max"].default_value = 0.8, 1.15
    nt.links.new(makro.outputs["Fac"], rp.inputs["Value"])
    kal = nt.nodes.new("ShaderNodeMix")
    kal.data_type, kal.blend_type = "RGBA", "MULTIPLY"
    kal.inputs["Factor"].default_value = 1.0
    nt.links.new(hs.outputs[0], kal.inputs[6])
    tint = nt.nodes.new("ShaderNodeMix")
    tint.data_type, tint.blend_type = "RGBA", "MULTIPLY"
    tint.inputs["Factor"].default_value = 1.0
    nt.links.new(rp.outputs[0], tint.inputs[6])
    tint.inputs[7].default_value = (*kali, 1)
    nt.links.new(tint.outputs[2], kal.inputs[7])
    nt.links.new(kal.outputs[2], bsdf.inputs["Base Color"])
    r = d / f"{nama}_rough_2k.jpg"
    if r.exists():
        rg = _gambar(nt, r, False)
        nt.links.new(mp.outputs[0], rg.inputs[0])
        ad = nt.nodes.new("ShaderNodeMath")
        ad.operation = "ADD"
        ad.inputs[1].default_value = kasar_tambah
        nt.links.new(rg.outputs[0], ad.inputs[0])
        nt.links.new(ad.outputs[0], bsdf.inputs["Roughness"])
    n = d / f"{nama}_nor_gl_2k.jpg"
    if n.exists():
        ng = _gambar(nt, n, False)
        nt.links.new(mp.outputs[0], ng.inputs[0])
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nm.inputs["Strength"].default_value = normal
        nt.links.new(ng.outputs[0], nm.inputs["Color"])
        nt.links.new(nm.outputs[0], bsdf.inputs["Normal"])
    return True


def panel_bersambung(m, warna, kasar, lebar=1.2, tinggi=0.9):
    """Panel fasad (ACP/GRC) dengan nat tipis dan sedikit variasi per panel (dunia, sumbu x+y vs z)."""
    nt, bsdf = _nodes(m)
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Position"], sep.inputs[0])
    plus = nt.nodes.new("ShaderNodeMath")
    plus.operation = "ADD"
    nt.links.new(sep.outputs[0], plus.inputs[0])
    nt.links.new(sep.outputs[1], plus.inputs[1])
    com = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(plus.outputs[0], com.inputs[0])
    nt.links.new(sep.outputs[2], com.inputs[1])
    br = nt.nodes.new("ShaderNodeTexBrick")
    br.offset = 0.0
    br.inputs["Scale"].default_value = 1.0
    br.inputs["Brick Width"].default_value = lebar
    br.inputs["Row Height"].default_value = tinggi
    br.inputs["Mortar Size"].default_value = 0.008
    br.inputs["Mortar Smooth"].default_value = 0.3
    c = Vector(warna)
    br.inputs["Color1"].default_value = (*c * 1.0, 1)
    br.inputs["Color2"].default_value = (*c * 0.94, 1)
    br.inputs["Mortar"].default_value = (*c * 0.35, 1)
    nt.links.new(com.outputs[0], br.inputs["Vector"])
    nt.links.new(br.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = kasar
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.4
    bump.inputs["Distance"].default_value = 0.004
    nt.links.new(br.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs[0], bsdf.inputs["Normal"])


def kaca_berinterior(m, warna, menyala, ambang=0.45):
    """Kaca reflektif dengan interior palsu: sel jendela acak menyala hangat (senja) atau ruang gelap (siang)."""
    nt, bsdf = _nodes(m)
    bsdf.inputs["Base Color"].default_value = (*warna, 1)
    bsdf.inputs["Roughness"].default_value = 0.035
    bsdf.inputs["Metallic"].default_value = 0.65  # kaca reflektif low-e: memantulkan langit
    bsdf.inputs["IOR"].default_value = 1.52
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1 / 3.0, 1 / 3.0, 1 / 4.2)
    nt.links.new(geo.outputs["Position"], mp.inputs["Vector"])
    fl = nt.nodes.new("ShaderNodeVectorMath")
    fl.operation = "FLOOR"
    nt.links.new(mp.outputs[0], fl.inputs[0])
    wn = nt.nodes.new("ShaderNodeTexWhiteNoise")
    wn.noise_dimensions = "3D"
    nt.links.new(fl.outputs[0], wn.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[0].color = ambang, (0, 0, 0, 1)
    ramp.color_ramp.elements[1].position, ramp.color_ramp.elements[1].color = ambang + 0.05, (1.0, 0.62, 0.32, 1)
    el = ramp.color_ramp.elements.new(0.8)
    el.color = (1.0, 0.78, 0.55, 1)
    nt.links.new(wn.outputs["Value"], ramp.inputs[0])
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.35
    inv = nt.nodes.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    nt.links.new(lw.outputs["Facing"], inv.inputs[1])
    kuat = nt.nodes.new("ShaderNodeMath")
    kuat.operation = "MULTIPLY"
    kuat.inputs[1].default_value = 3.0 if menyala else 0.0
    nt.links.new(inv.outputs[0], kuat.inputs[0])
    sepz = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(mp.outputs[0], sepz.inputs[0])
    fr = nt.nodes.new("ShaderNodeMath")
    fr.operation = "FRACT"
    nt.links.new(sepz.outputs[2], fr.inputs[0])
    grad = nt.nodes.new("ShaderNodeMapRange")  # bawah jendela gelap, dekat plafon terang (lampu plafon)
    grad.inputs["From Min"].default_value, grad.inputs["From Max"].default_value = 0.25, 0.85
    grad.inputs["To Min"].default_value, grad.inputs["To Max"].default_value = 0.25, 1.0
    nt.links.new(fr.outputs[0], grad.inputs["Value"])
    acak = nt.nodes.new("ShaderNodeMapRange")
    acak.inputs["To Min"].default_value, acak.inputs["To Max"].default_value = 0.35, 1.0
    nt.links.new(wn.outputs["Value"], acak.inputs["Value"])
    k1 = nt.nodes.new("ShaderNodeMath")
    k1.operation = "MULTIPLY"
    nt.links.new(grad.outputs[0], k1.inputs[0])
    nt.links.new(acak.outputs[0], k1.inputs[1])
    k2 = nt.nodes.new("ShaderNodeMath")
    k2.operation = "MULTIPLY"
    nt.links.new(k1.outputs[0], k2.inputs[0])
    nt.links.new(kuat.outputs[0], k2.inputs[1])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Emission Color"])
    nt.links.new(k2.outputs[0], bsdf.inputs["Emission Strength"])


def pagar_jeruji(m):
    """Pagar BRC: jeruji tegak 25 mm tiap 150 mm + rel atas/bawah; selebihnya tembus pandang (dinding pejal di model)."""
    nt, bsdf = _nodes(m)
    bsdf.inputs["Base Color"].default_value = (0.03, 0.035, 0.035, 1)
    bsdf.inputs["Metallic"].default_value = 0.8
    bsdf.inputs["Roughness"].default_value = 0.4
    out = nt.nodes["Material Output"]
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Position"], sep.inputs[0])
    plus = nt.nodes.new("ShaderNodeMath")
    plus.operation = "ADD"
    nt.links.new(sep.outputs[0], plus.inputs[0])
    nt.links.new(sep.outputs[1], plus.inputs[1])
    jer = nt.nodes.new("ShaderNodeMath")
    jer.operation = "PINGPONG"
    jer.inputs[1].default_value = 0.075
    nt.links.new(plus.outputs[0], jer.inputs[0])
    bar = nt.nodes.new("ShaderNodeMath")
    bar.operation = "LESS_THAN"
    bar.inputs[1].default_value = 0.0125
    nt.links.new(jer.outputs[0], bar.inputs[0])
    relz = nt.nodes.new("ShaderNodeMath")
    relz.operation = "PINGPONG"
    relz.inputs[1].default_value = 1.0
    nt.links.new(sep.outputs[2], relz.inputs[0])
    rel = nt.nodes.new("ShaderNodeMath")
    rel.operation = "LESS_THAN"
    rel.inputs[1].default_value = 0.04
    nt.links.new(relz.outputs[0], rel.inputs[0])
    mx = nt.nodes.new("ShaderNodeMath")
    mx.operation = "MAXIMUM"
    nt.links.new(bar.outputs[0], mx.inputs[0])
    nt.links.new(rel.outputs[0], mx.inputs[1])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mx.outputs[0], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(bsdf.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])


def air_sungai(m):
    nt, bsdf = _nodes(m)
    bsdf.inputs["Base Color"].default_value = (0.045, 0.040, 0.026, 1)  # Batanghari keruh kecokelatan
    bsdf.inputs["Roughness"].default_value = 0.07
    bsdf.inputs["IOR"].default_value = 1.33
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (0.5, 2.5, 0.5)  # riak memanjang searah arus (x)
    nt.links.new(geo.outputs["Position"], mp.inputs["Vector"])
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 1.0
    nz.inputs["Detail"].default_value = 10
    nz.inputs["Roughness"].default_value = 0.6
    nt.links.new(mp.outputs[0], nz.inputs["Vector"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.35
    nt.links.new(nz.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs[0], bsdf.inputs["Normal"])


def material_scene(kamera):
    M = bpy.data.materials
    nyala = lampu_buatan(kamera)
    for nama, (tx, sk, kali, kt) in {
        "Aspal": ("asphalt_02", 5.0, (0.85, 0.85, 0.85), 0.0),
        "Rumput": ("leafy_grass", 3.0, (0.44, 0.5, 0.35), 0.1),
        "Tanah taman": ("leafy_grass", 3.0, (0.5, 0.56, 0.4), 0.1),
        "Batu kali": ("ganges_river_pebbles", 2.5, (0.45, 0.43, 0.38), 0.0),
        "Paving": ("pavement_02", 3.0, (1, 1, 1), 0.0),
        "Beton": ("concrete_wall_008", 4.0, (1, 1, 1), 0.0),
        "Beton ekspos": ("concrete_wall_008", 4.0, (1, 1, 1), 0.0),
        "Tanah lereng": ("leafy_grass", 2.0, (0.42, 0.47, 0.33), 0.15),  # tebing berumput (bukan tanah terbuka)
    }.items():
        for m in [m for m in M if m.name.split(".")[0] == nama]:
            if nama in ("Rumput", "Tanah taman", "Tanah lereng"):  # tekstur daun gugur digeser ke hijau rumput tropis
                tekstur_pbr(m, tx, sk, kali, kt, hue=0.63, sat=0.95)
            else:
                tekstur_pbr(m, tx, sk, kali, kt)
    for m in M:
        dasar = m.name.split(".")[0]
        if dasar == "Panel putih":
            panel_bersambung(m, (0.78, 0.78, 0.76), 0.32, 1.2, 0.9)
        elif dasar in ("Panel abu", "Panel abu tua"):
            panel_bersambung(m, (0.30, 0.31, 0.32) if dasar == "Panel abu" else (0.09, 0.09, 0.10), 0.42, 1.2, 0.6)
        elif dasar == "Kaca pita":
            kaca_berinterior(m, (0.20, 0.24, 0.28), nyala)
        elif dasar == "Kaca biru":
            kaca_berinterior(m, (0.14, 0.22, 0.34), nyala, 0.9)  # dinding tirai: sebagian kecil menyala
        elif dasar == "Pagar":
            pagar_jeruji(m)
        elif dasar == "Air sungai":
            air_sungai(m)
        elif dasar == "Cahaya":
            nt, b = _nodes(m)
            b.inputs["Base Color"].default_value = (1, 0.9, 0.75, 1)
            b.inputs["Emission Color"].default_value = (1.0, 0.78, 0.5, 1)
            b.inputs["Emission Strength"].default_value = 40.0 if nyala else 0.0


# ------------------------------------------------------------------ langit
def _arah_matahari_hdri(img):
    """(azimut, elevasi) radian piksel paling terang HDRI equirect."""
    import numpy as np
    img.reload()
    _ = img.pixels[0]  # paksa memuat piksel sebelum membaca ukuran
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    lum = px.reshape(h, w, 4)[:, :, :3].sum(axis=2)
    j, i = divmod(int(lum.argmax()), w)
    az = math.pi - 2 * math.pi * (i / w)  # Cycles: u = 0,5 - atan2(y, x)/(2 pi)  ->  azimut dunia
    el = (j / h) * math.pi - math.pi / 2
    return az, el


def langit_hdri(kamera, cam):
    nama, kuat, _ = SUASANA[suasana(kamera)]
    exr = ASET / "hdri" / f"{nama}_4k.exr"
    jpg = ASET / "hdri" / f"{nama}_latar.jpg"
    if not exr.exists():
        return None
    sc = bpy.context.scene
    w = sc.world or bpy.data.worlds.new("Langit")
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(str(exr), check_existing=True)
    nt.links.new(mp.outputs[0], env.inputs["Vector"])
    az, el = _arah_matahari_hdri(env.image)
    sun_dunia = az  # azimut matahari HDRI sebelum diputar
    f = cam.matrix_world.to_quaternion() @ Vector((0, 0, -1))
    az_kam = math.atan2(f.y, f.x)
    # matahari datang dari belakang-samping kamera: arah ke matahari = kebalikan arah pandang diputar
    target = az_kam + math.pi + math.radians(SUDUT_MATAHARI.get(kamera, 50))
    mp.inputs["Rotation"].default_value[2] = sun_dunia - target  # vektor diputar sebelum dibaca: arah dunia = hdri - rotasi
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = kuat
    nt.links.new(env.outputs["Color"], bg.inputs["Color"])
    akhir = bg
    if jpg.exists():  # latar resolusi tinggi hanya untuk sinar kamera
        lt = nt.nodes.new("ShaderNodeTexEnvironment")
        lt.image = bpy.data.images.load(str(jpg), check_existing=True)
        nt.links.new(mp.outputs[0], lt.inputs["Vector"])
        bg2 = nt.nodes.new("ShaderNodeBackground")
        bg2.inputs["Strength"].default_value = 0.9 if suasana(kamera) == "siang" else 0.7
        nt.links.new(lt.outputs["Color"], bg2.inputs["Color"])
        lp = nt.nodes.new("ShaderNodeLightPath")
        mx = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(lp.outputs["Is Camera Ray"], mx.inputs[0])
        nt.links.new(bg.outputs[0], mx.inputs[1])
        nt.links.new(bg2.outputs[0], mx.inputs[2])
        akhir = mx
    nt.links.new(akhir.outputs[0], out.inputs["Surface"])
    return math.degrees(el)


# ------------------------------------------------------------------ vegetasi
def _impor_gltf(nama):
    """Impor glTF Poly Haven; tiap varian mesh jadi koleksi sendiri berpangkal di (0, 0, 0). Kembali [(koleksi, tinggi)]."""
    d = ASET / "model" / nama
    g = next(d.glob("*.gltf"), None) if d.exists() else None
    if g is None:
        return []
    sebelum = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(g))
    baru = [o for o in bpy.data.objects if o not in sebelum]
    hasil = []
    for o in [o for o in baru if o.type == "MESH" and "LOD" not in o.name.replace("LOD0", "")]:
        mw = o.matrix_world.copy()
        o.parent = None
        o.matrix_world = mw
        pts = [mw @ Vector(c) for c in o.bound_box]
        lo = Vector([min(p[i] for p in pts) for i in range(3)])
        hi = Vector([max(p[i] for p in pts) for i in range(3)])
        o.location -= Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
        kol = bpy.data.collections.new(f"Aset {o.name}")
        bpy.context.scene.collection.children.link(kol)
        for c in list(o.users_collection):
            c.objects.unlink(o)
        kol.objects.link(o)
        bpy.context.view_layer.layer_collection.children[kol.name].exclude = True  # sumber instans
        hasil.append((kol, hi.z - lo.z))
    for o in baru:
        if o.type != "MESH" and o.name in bpy.data.objects:
            bpy.data.objects.remove(o)
    return hasil


ANTRE = []  # instans vegetasi ditunda sampai semua raycast selesai (menambah objek memicu evaluasi ulang adegan)


def _contoh(kol, tinggi_asal, pos, tinggi, rot):
    ANTRE.append((kol, tinggi_asal, tuple(pos), tinggi, rot))


def _buat_antrean():
    for kol, tinggi_asal, pos, tinggi, rot in ANTRE:
        _contoh_buat(kol, tinggi_asal, pos, tinggi, rot)
    ANTRE.clear()


def _contoh_buat(kol, tinggi_asal, pos, tinggi, rot):
    e = bpy.data.objects.new(f"Vegetasi {kol.name}", None)
    e.instance_type = "COLLECTION"
    e.instance_collection = kol
    e.location = pos
    s = tinggi / tinggi_asal
    e.scale = (s, s, s)
    e.rotation_euler.z = rot
    bpy.context.scene.collection.objects.link(e)
    return e


_DG = []


def _tanah_di(x, y, z0=200.0):
    """(z, nama material) permukaan teratas yang terlihat di (x, y); depsgraph disimpan (adegan tidak berubah saat raycast)."""
    if not _DG:
        _DG.append(bpy.context.evaluated_depsgraph_get())
    dg = _DG[0]
    ok, loc, _n, _i, ob, _m = bpy.context.scene.ray_cast(dg, Vector((x, y, z0)), Vector((0, 0, -1)))
    if not ok:
        return None, ""
    nama = ""
    if ob and ob.material_slots and ob.material_slots[0].material:
        nama = ob.material_slots[0].material.name.split(".")[0]
    return loc.z, nama


def vegetasi(j, cam, kamera):
    rnd = random.Random(11)
    pohon = _impor_gltf("jacaranda_tree") + _impor_gltf("tree_small_02")
    kecil = [k for k in _impor_gltf("searsia_lucida") if k[1] > 1.3]
    semak = _impor_gltf("shrub_02")
    rumput = _impor_gltf("grass_medium_01")
    if not pohon:
        return 0
    pohon.sort(key=lambda p: -p[1])  # jacaranda (tertinggi) dulu
    n = 0
    # 1) ganti pohon model (posisi dan tinggi dari IFC)
    for ob in [o for o in bpy.data.objects if "Pohon" in o.name and o.type == "MESH" and "render" not in o.name]:
        pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
        lo = Vector([min(p[i] for p in pts) for i in range(3)])
        hi = Vector([max(p[i] for p in pts) for i in range(3)])
        ob.hide_render = ob.hide_viewport = True
        kol, h0 = pohon[0] if rnd.random() < 0.7 else rnd.choice(pohon)
        _contoh(kol, h0, ((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z), (hi.z - lo.z) * rnd.uniform(1.3, 1.7),
                rnd.uniform(0, 6.28))
        n += 1
    for ob in [o for o in bpy.data.objects if o.name.startswith("Pohon render")]:
        ob.hide_render = ob.hide_viewport = True
    # 2) konteks: sabuk pohon seberang sungai, tepi jalan utara, sisi barat dan timur persil
    tepi, lebar = j["air"][1][1], 320.0
    zair = j["air"][1][2]
    t0, t1 = Vector(j["tapak"][0]), Vector(j["tapak"][1])
    for i in range(700):
        if i >= 420:  # lahan kosong barat/timur/utara: kelompok pohon (bukan baris)
            x, y = rnd.uniform(-300, 450), rnd.uniform(-2, 300)
            if t0.x - 4 < x < t1.x + 4 and t0.y - 4 < y < t1.y + 24:
                continue
            z, mat = _tanah_di(x, y)
            if z is None or mat not in ("Rumput", ""):
                continue
            kol, h0 = rnd.choice(pohon)
            _contoh(kol, h0, (x, y, z), rnd.uniform(7, 15), rnd.uniform(0, 6.28))
            n += 1
            continue
        if i < 260:
            x, y, z = rnd.uniform(-450, 650), tepi - lebar - rnd.uniform(4, 160), zair + 2.0
        elif i < 340:
            x, y, z = rnd.uniform(-250, 400), t1.y + rnd.uniform(14, 80), None
        else:
            x = rnd.choice((rnd.uniform(-120, t0.x - 6), rnd.uniform(t1.x + 6, 300)))
            y, z = rnd.uniform(t0.y, t1.y + 10), None
        if z is None:
            z, mat = _tanah_di(x, y)
            if z is None or mat not in ("Rumput", ""):
                continue
        kol, h0 = rnd.choice(pohon)
        _contoh(kol, h0, (x, y, z), rnd.uniform(8, 16), rnd.uniform(0, 6.28))
        n += 1
    # 3) semak tepi bangunan dan rumput rumpun dekat kamera (hanya di atas rumput)
    if semak:
        g0, g1 = Vector(j["gedung"][0]), Vector(j["gedung"][1])
        for i in range(500):
            x, y = rnd.uniform(g0.x - 6, g1.x + 6), rnd.uniform(g0.y - 6, g1.y + 6)
            z, mat = _tanah_di(x, y)
            if z is None or mat != "Rumput" or z > j["tapak"][1][2] + 0.5:
                continue
            kol, h0 = rnd.choice(semak + kecil)
            _contoh(kol, h0, (x, y, z), rnd.uniform(0.8, 1.6), rnd.uniform(0, 6.28))
            n += 1
    # semak di tebing sungai (memecah bidang lereng polos)
    for i in range(900 if semak else 0):
        x, y = rnd.uniform(-250, 350), rnd.uniform(-19.5, -1.0)
        z, mat = _tanah_di(x, y)
        if z is None or mat not in ("Tanah lereng", "Rumput"):
            continue
        kol, h0 = rnd.choice(semak + kecil)
        _contoh(kol, h0, (x, y, z - 0.1), rnd.uniform(0.7, 1.8), rnd.uniform(0, 6.28))
        n += 1
    if rumput and cam.location.z < j["tapak"][1][2] + 6:
        f = cam.matrix_world.to_quaternion() @ Vector((0, 0, -1))
        for i in range(2500):
            jarak, sudut = rnd.uniform(2, 40), rnd.uniform(-0.6, 0.6)
            a = math.atan2(f.y, f.x) + sudut
            x, y = cam.location.x + jarak * math.cos(a), cam.location.y + jarak * math.sin(a)
            z, mat = _tanah_di(x, y)
            if z is None or mat != "Rumput":
                continue
            kol, h0 = rnd.choice(rumput)
            _contoh(kol, h0, (x, y, z), h0 * rnd.uniform(1.0, 1.6), rnd.uniform(0, 6.28))
            n += 1
    _buat_antrean()
    _DG.clear()
    return n


# ------------------------------------------------------------------ kendaraan
def _mesh_mobil(bm, L, W):
    """Loft penampang superelips sepanjang mobil (x), dengan tumblehome; tinggi dalam m."""
    st = [(-0.50, 0.30, 0.62, 0.86), (-0.47, 0.24, 0.78, 0.97), (-0.32, 0.24, 0.90, 1.0), (-0.16, 0.24, 0.98, 1.0),
          (-0.02, 0.24, 1.42, 0.98), (0.20, 0.24, 1.44, 0.98), (0.33, 0.24, 1.10, 1.0), (0.46, 0.25, 1.02, 0.98),
          (0.50, 0.32, 0.86, 0.90)]
    n = 20
    cincin = []
    for fx, zb, zt, fw in st:
        x = fx * L
        hw = W / 2 * fw
        zc, hz = (zb + zt) / 2, (zt - zb) / 2
        ring = []
        for k in range(n):
            t = 2 * math.pi * k / n
            c, s = math.cos(t), math.sin(t)
            y = hw * math.copysign(abs(c) ** 0.35, c)
            z = zc + hz * math.copysign(abs(s) ** 0.45, s)
            y *= 1 - 0.18 * max(0.0, z - 0.95) / 0.5  # kabin menyempit ke atap
            ring.append(bm.verts.new((x, y, z)))
        cincin.append(ring)
    for a, b in zip(cincin, cincin[1:]):
        for k in range(n):
            bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]))
    bm.faces.new(list(reversed(cincin[0])))
    bm.faces.new(cincin[-1])


def _model_mobil(warna_mat):
    nama = f"Mobil render {warna_mat.name}"
    if nama in bpy.data.objects:
        return bpy.data.objects[nama]
    L, W = 4.5, 1.80
    me = bpy.data.meshes.new(nama)
    bm = bmesh.new()
    _mesh_mobil(bm, L, W)
    bm.to_mesh(me)
    bm.free()
    kaca = bpy.data.materials.get("Kaca mobil") or bpy.data.materials.new("Kaca mobil")
    if not kaca.use_nodes or "Principled BSDF" not in kaca.node_tree.nodes:
        nt, b = _nodes(kaca)
        b.inputs["Base Color"].default_value = (0.01, 0.012, 0.015, 1)
        b.inputs["Roughness"].default_value = 0.02
    me.materials.append(warna_mat)
    me.materials.append(kaca)
    for p in me.polygons:  # jendela: sisi kabin di atas garis pinggang, kecuali atap datar
        c = p.center
        if 0.97 < c.z < 1.40 and abs(p.normal.z) < 0.85:
            p.material_index = 1
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(nama, me)
    sub = ob.modifiers.new("halus", "SUBSURF")
    sub.levels = sub.render_levels = 1
    bpy.context.scene.collection.objects.link(ob)
    # roda
    ban = bpy.data.materials.get("Ban") or bpy.data.materials.new("Ban")
    nt, b = _nodes(ban)
    b.inputs["Base Color"].default_value = (0.015, 0.015, 0.015, 1)
    b.inputs["Roughness"].default_value = 0.8
    velg = bpy.data.materials.get("Velg") or bpy.data.materials.new("Velg")
    nt, b = _nodes(velg)
    b.inputs["Base Color"].default_value = (0.6, 0.6, 0.62, 1)
    b.inputs["Metallic"].default_value = 1.0
    b.inputs["Roughness"].default_value = 0.25
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * 0.30 * L, sy * (W / 2 - 0.13)
            bpy.ops.mesh.primitive_cylinder_add(radius=0.33, depth=0.22, vertices=24, location=(x, y, 0.33),
                                                rotation=(math.pi / 2, 0, 0))
            t = bpy.context.object
            t.data.materials.append(ban)
            t.parent = ob
            bpy.ops.mesh.primitive_cylinder_add(radius=0.21, depth=0.02, vertices=16, location=(x, y + sy * 0.11, 0.33),
                                                rotation=(math.pi / 2, 0, 0))
            v = bpy.context.object
            v.data.materials.append(velg)
            v.parent = ob
    ob.hide_render = ob.hide_viewport = True
    for c in ob.children:
        c.hide_render = c.hide_viewport = True
    return ob


def _salin_hirarki(src, loc, rotz):
    d = src.copy()
    d.hide_render = d.hide_viewport = False
    bpy.context.scene.collection.objects.link(d)
    for c in src.children:
        cc = c.copy()
        cc.parent = d
        cc.hide_render = cc.hide_viewport = False
        bpy.context.scene.collection.objects.link(cc)
    d.location = loc
    d.rotation_euler.z = rotz
    return d


def kendaraan():
    n = 0
    mobil = []
    for ob in [o for o in bpy.data.objects if o.type == "MESH" and "RSTB Mobil" in o.name and not o.hide_render]:
        cat = next((s.material for s in ob.material_slots if s.material and s.material.name.startswith("Mobil")), None)
        if not cat:
            continue
        nt = cat.node_tree.nodes.get("Principled BSDF") if cat.use_nodes else None
        if nt:
            nt.inputs["Coat Weight"].default_value = 1.0
            nt.inputs["Roughness"].default_value = 0.25
            nt.inputs["Metallic"].default_value = 0.4
        pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
        lo = Vector([min(p[i] for p in pts) for i in range(3)])
        hi = Vector([max(p[i] for p in pts) for i in range(3)])
        rot = 0.0 if (hi.x - lo.x) > (hi.y - lo.y) else math.pi / 2
        mobil.append((ob, cat, lo, hi, rot))
    for ob, *_ in mobil:  # sembunyikan dulu supaya raycast mengenai aspal, bukan mobil kotak
        ob.hide_render = ob.hide_viewport = True
    bpy.context.view_layer.update()
    _DG.clear()
    letak = [_tanah_di((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, hi.z + 0.5)[0] for _ob, _c, lo, hi, _r in mobil]
    _DG.clear()
    for (ob, cat, lo, hi, rot), z in zip(mobil, letak):
        _salin_hirarki(_model_mobil(cat), ((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, (z if z is not None else lo.z - 0.25)), rot)
        n += 1
    # motor: dua roda tipis + badan membulat (pengganti kotak)
    for ob in [o for o in bpy.data.objects if o.type == "MESH" and "RSTB Motor" in o.name and not o.hide_render]:
        pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
        lo = Vector([min(p[i] for p in pts) for i in range(3)])
        hi = Vector([max(p[i] for p in pts) for i in range(3)])
        ob.hide_render = ob.hide_viewport = True
        src = bpy.data.objects.get("Motor render") or _model_motor()
        rot = 0.0 if (hi.x - lo.x) > (hi.y - lo.y) else math.pi / 2
        _salin_hirarki(src, ((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z), rot)
        n += 1
    return n


def _model_motor():
    ban = bpy.data.materials.get("Ban")
    badan = bpy.data.materials.get("Motor bodi") or bpy.data.materials.get("Mobil hitam")
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=16, ring_count=8, location=(0, 0, 0.62))
    ob = bpy.context.object
    ob.name = "Motor render"
    ob.scale = (0.62, 0.17, 0.22)
    bpy.ops.object.shade_smooth()
    if badan:
        ob.data.materials.append(badan)
    for x in (-0.62, 0.62):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.25, minor_radius=0.05, location=(x, 0, 0.30),
                                         rotation=(math.pi / 2, 0, 0))
        r = bpy.context.object
        if ban:
            r.data.materials.append(ban)
        r.parent = ob
        r.matrix_parent_inverse = ob.matrix_world.inverted()
    ob.hide_render = ob.hide_viewport = True
    for c in ob.children:
        c.hide_render = c.hide_viewport = True
    return ob


# ------------------------------------------------------------------ papan nama dan fasad
def _teks(isi, ukuran, mat, tebal=0.08):
    cu = bpy.data.curves.new("teks", "FONT")
    cu.body = isi
    if FONT.exists():
        cu.font = bpy.data.fonts.load(str(FONT), check_existing=True)
    cu.size = ukuran
    cu.align_x, cu.align_y = "CENTER", "CENTER"
    cu.extrude = tebal
    ob = bpy.data.objects.new(f"Teks {isi[:12]}", cu)
    ob.data.materials.append(mat)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def papan_nama(kamera):
    nyala = lampu_buatan(kamera)
    biru = bpy.data.materials.new("Papan biru")
    nt, b = _nodes(biru)
    b.inputs["Base Color"].default_value = (0.0, 0.12, 0.55, 1)
    b.inputs["Roughness"].default_value = 0.3
    b.inputs["Emission Color"].default_value = (0.1, 0.35, 1.0, 1)
    b.inputs["Emission Strength"].default_value = 1.5 if nyala else 0.0
    putih = bpy.data.materials.new("Papan putih")
    nt, b = _nodes(putih)
    b.inputs["Base Color"].default_value = (0.95, 0.95, 0.95, 1)
    b.inputs["Emission Color"].default_value = (1, 1, 1, 1)
    b.inputs["Emission Strength"].default_value = 8.0 if nyala else 0.4
    huruf = [o for o in bpy.data.objects if o.type == "MESH" and "RSTB Huruf" in o.name]
    if huruf:
        pts = [o.matrix_world @ Vector(c) for o in huruf for c in o.bound_box]
        lo = Vector([min(p[i] for p in pts) for i in range(3)])
        hi = Vector([max(p[i] for p in pts) for i in range(3)])
        for o in huruf:
            o.hide_render = o.hide_viewport = True
        t = _teks("RUMAH SAKIT TEPIAN BATANGHARI", 1.0, biru, 0.06)
        t.rotation_euler = (math.pi / 2, 0, 0)  # berdiri di bidang xz, muka ke -y (sisi sungai)
        bpy.context.view_layer.update()
        s = min((hi.x - lo.x) / max(t.dimensions.x, 1e-6), 1.5 / max(t.dimensions.y * 0.75, 1e-6))
        t.scale = (s, s, s)
        t.location = ((lo.x + hi.x) / 2, lo.y - 0.02, (lo.z + hi.z) / 2)
    for o in [o for o in bpy.data.objects if o.type == "MESH" and "RSTB Logo H" in o.name]:
        pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
        lo = Vector([min(p[i] for p in pts) for i in range(3)])
        hi = Vector([max(p[i] for p in pts) for i in range(3)])
        o.hide_render = o.hide_viewport = True
        c = (lo + hi) / 2
        sisi = min(hi.z - lo.z, max(hi.x - lo.x, hi.y - lo.y))
        tipis_x = (hi.x - lo.x) < (hi.y - lo.y)
        bpy.ops.mesh.primitive_cube_add(size=1, location=c)
        p = bpy.context.object
        p.name = "Panel logo H"
        p.scale = (0.25, sisi, sisi) if tipis_x else (sisi, 0.25, sisi)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        bev = p.modifiers.new("tepi", "BEVEL")
        bev.width, bev.segments, bev.use_clamp_overlap = sisi * 0.12, 5, True
        p.data.materials.append(biru)
        for arah in (-1, 1):
            h = _teks("H", sisi * 1.05, putih, 0.04)
            if tipis_x:
                h.rotation_euler = (math.pi / 2, 0, math.pi / 2 * arah)
                h.location = (c.x + arah * 0.13, c.y, c.z)
            else:
                h.rotation_euler = (math.pi / 2, 0, 0 if arah < 0 else math.pi)
                h.location = (c.x, c.y + arah * 0.13, c.z)


def mullion():
    """Mullion aluminium gelap tiap 1,5 m dan transom atas-bawah pada setiap bidang kaca fasad."""
    al = bpy.data.materials.new("Aluminium mullion")
    nt, b = _nodes(al)
    b.inputs["Base Color"].default_value = (0.05, 0.055, 0.06, 1)
    b.inputs["Metallic"].default_value = 0.9
    b.inputs["Roughness"].default_value = 0.35
    bm = bmesh.new()
    n = 0

    def kotak(c, s):
        r = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=s, verts=r["verts"])
        bmesh.ops.translate(bm, vec=c, verts=r["verts"])

    for ob in bpy.data.objects:
        if ob.type != "MESH" or ob.hide_render:
            continue
        if not any(s.material and s.material.name.split(".")[0] in ("Kaca biru", "Kaca pita") for s in ob.material_slots):
            continue
        if any(k in ob.name for k in ("Mobil", "Motor")):
            continue
        pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
        lo = Vector([min(p[i] for p in pts) for i in range(3)])
        hi = Vector([max(p[i] for p in pts) for i in range(3)])
        dx, dy, dz = hi - lo
        if dz < 0.4 or max(dx, dy) < 0.8 or min(dx, dy) > 0.4:
            continue
        sumbu = 0 if dx > dy else 1
        pj = (dx, dy)[sumbu]
        m = max(1, round(pj / 1.5))
        c0 = (lo + hi) / 2
        for k in range(m + 1):
            t = lo[sumbu] + pj * k / m
            c = c0.copy()
            c[sumbu] = t
            s = Vector((0.07, 0.07, dz))
            s[1 - sumbu] = 0.16
            kotak(c, s)
        for zz in (lo.z + 0.03, hi.z - 0.03) + ((tuple(lo.z + 1.4 * i for i in range(1, int(dz / 1.4)))) if dz > 3 else ()):
            c = c0.copy()
            c.z = zz
            s = Vector((pj, pj, 0.06))
            s[1 - sumbu] = 0.14
            kotak(c, s)
        n += 1
    me = bpy.data.meshes.new("Mullion fasad")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(al)
    ob = bpy.data.objects.new("Mullion fasad", me)
    bpy.context.scene.collection.objects.link(ob)
    return n


# ------------------------------------------------------------------ lampu senja
def lampu_senja(j, kamera):
    if not lampu_buatan(kamera):
        return 0
    n = 0

    def titik(loc, w, warna=(1.0, 0.72, 0.45), r=0.15):
        nonlocal n
        L = bpy.data.lights.new("Lampu", "POINT")
        L.energy, L.color, L.shadow_soft_size = w, warna, r
        o = bpy.data.objects.new("Lampu", L)
        o.location = loc
        bpy.context.scene.collection.objects.link(o)
        n += 1

    def sorot(loc, arah, w, sudut=0.5):
        nonlocal n
        L = bpy.data.lights.new("Sorot", "SPOT")
        L.energy, L.color, L.spot_size, L.spot_blend, L.shadow_soft_size = w, (1.0, 0.74, 0.48), sudut, 0.6, 0.05
        o = bpy.data.objects.new("Sorot", L)
        o.location = loc
        o.rotation_euler = Vector(arah).to_track_quat("-Z", "Y").to_euler()
        bpy.context.scene.collection.objects.link(o)
        n += 1

    for p in j["lampu"]:
        titik((p[0], p[1], p[2] - 0.35), 900)
    # downlight di bawah kanopi (IGD, lobi) tiap 2,5 m
    for ob in [o for o in bpy.data.objects if o.type == "MESH" and not o.hide_render and
               any(s.material and s.material.name.split(".")[0] == "Kanopi" for s in o.material_slots)]:
        pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
        lo = Vector([min(p[i] for p in pts) for i in range(3)])
        hi = Vector([max(p[i] for p in pts) for i in range(3)])
        nx, ny = max(1, int((hi.x - lo.x) / 2.5)), max(1, int((hi.y - lo.y) / 2.5))
        for a in range(nx):
            for b in range(ny):
                sorot((lo.x + (a + 0.5) * (hi.x - lo.x) / nx, lo.y + (b + 0.5) * (hi.y - lo.y) / ny, lo.z - 0.1),
                      (0, 0, -1), 250, 1.4)
    # wall-washer di kaki fasad tiap kolom grid (sisi selatan dan utara menara, timur podium)
    g0, g1 = Vector(j["gedung"][0]), Vector(j["gedung"][1])
    z = j["tapak"][1][2] + 0.1
    for x in [12.0 + 8.0 * i for i in range(16)]:
        for y, dy in ((g0.y - 0.6, 1), (g1.y + 0.6, -1)):
            zz, mat = _tanah_di(x, y, z + 2.5)
            if zz is not None and zz < z + 1.0:
                sorot((x, y, zz + 0.15), (0, dy * 0.18, 1), 2500, 0.35)
    return n


# ------------------------------------------------------------------ kamera dan pasca-olah
def dua_titik_hilang(cam, batas_tinggi):
    """Kamera setinggi mata: pitch nol, framing dengan geser lensa supaya garis tegak tetap tegak."""
    bpy.context.view_layer.update()
    if cam.location.z > batas_tinggi:
        return False
    f = cam.rotation_euler.to_quaternion() @ Vector((0, 0, -1))
    pitch = math.asin(max(-1.0, min(1.0, f.z)))
    yaw = math.atan2(f.y, f.x)
    cam.rotation_euler = (math.pi / 2, 0, yaw - math.pi / 2)
    cam.data.sensor_fit = "HORIZONTAL"
    cam.data.shift_y = cam.data.lens * math.tan(pitch) / cam.data.sensor_width
    bpy.context.view_layer.update()
    return True


def pasca_olah():
    sc = bpy.context.scene
    try:
        ng = bpy.data.node_groups.new("Pasca", "CompositorNodeTree")
        rl = ng.nodes.new("CompositorNodeRLayers")
        gl = ng.nodes.new("CompositorNodeGlare")
        for k, v in (("glare_type", "BLOOM"), ("quality", "HIGH")):
            if hasattr(gl, k):
                setattr(gl, k, v)
        for nama, v in (("Threshold", 1.2), ("Strength", 0.25), ("Size", 0.6)):
            if nama in gl.inputs:
                gl.inputs[nama].default_value = v
        ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
        go = ng.nodes.new("NodeGroupOutput")
        ng.links.new(rl.outputs["Image"], gl.inputs["Image"])
        ng.links.new(gl.outputs["Image"], go.inputs[0])
        sc.compositing_node_group = ng
        sc.render.use_compositing = True
        return True
    except Exception as e:  # shortcut: tanpa bloom bila API kompositor berbeda; render tetap jalan
        print("PASCA-OLAH dilewati:", e)
        return False


# ------------------------------------------------------------------ video sinematik
# shot: (suasana, sudut matahari, detik, [(posisi awal, sasaran awal), (posisi akhir, sasaran akhir)], lensa)
SHOT = {
    "V-01": ("siang", 50, 7, [((52, -170, 26), (52, 30, 22)), ((52, -45, 42), (52, 39, 30))], 30),   # drone dari sungai
    "V-02": ("siang", 40, 6, [((-5, -24, 22), (30, 32, 25)), ((112, -24, 27), (78, 32, 25))], 26),  # geser sepanjang fasad
    "V-03": ("emas", -60, 6, [((18, 101, 13.8), (38, 76, 19)), ((78, 101, 13.8), (64, 76, 19))], 24),  # dolly jalan utara
    "V-04": ("biru", -70, 6, [((112, 78, 14.6), (88, 40, 15)), ((96, 54, 14.2), (88, 40, 15.6))], 22),  # menuju IGD
    "V-05": ("siang", 60, 6, [((52, -25, 48), (52, 39, 39.4)), ((52, 8, 78), (52, 39, 39.4))], 28),   # crane helipad
    "V-06": ("emas", -45, 7, [((-70, -110, 85), (72, 50, 18)), ((150, -120, 85), (72, 50, 18))], 30),  # orbit senja
}
for _k, _v in SHOT.items():
    KAMERA_SUASANA[_k], SUDUT_MATAHARI[_k] = _v[0], _v[1]


def video_kamera(shot, fps=24):
    """Kamera dan target beranimasi dengan ease-in/out (Bezier); kembali (kamera, jumlah frame)."""
    _s, _sud, detik, kunci, lensa = SHOT[shot]
    sc = bpy.context.scene
    n = int(detik * fps)
    sc.frame_start, sc.frame_end, sc.render.fps = 1, n, fps
    tgt = bpy.data.objects.new("Sasaran video", None)
    sc.collection.objects.link(tgt)
    cd = bpy.data.cameras.new("Kamera video")
    cd.lens, cd.clip_end = lensa, 20000
    cam = bpy.data.objects.new("Kamera video", cd)
    sc.collection.objects.link(cam)
    tr = cam.constraints.new("TRACK_TO")
    tr.target, tr.track_axis, tr.up_axis = tgt, "TRACK_NEGATIVE_Z", "UP_Y"
    for f, (pos, sas) in zip((1, n), kunci):
        cam.location, tgt.location = pos, sas
        cam.keyframe_insert("location", frame=f)
        tgt.keyframe_insert("location", frame=f)
    for ob in (cam, tgt):
        for fc in ob.animation_data.action.fcurves if hasattr(ob.animation_data.action, "fcurves") else []:
            for kp in fc.keyframe_points:
                kp.interpolation, kp.easing = "BEZIER", "AUTO"
    sc.camera = cam
    sc.frame_set(1)
    bpy.context.view_layer.update()
    # langit/vegetasi membaca arah kamera dari rotasi: salin hasil Track To pada frame 1
    cam.rotation_euler = cam.matrix_world.to_euler()
    return cam, n


def setel_eevee(keluar):
    sc = bpy.context.scene
    for mesin in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        try:
            sc.render.engine = mesin
            break
        except TypeError:
            continue
    ev = sc.eevee
    for k, v in (("taa_render_samples", 48), ("use_raytracing", True), ("use_shadows", True),
                 ("shadow_ray_count", 2), ("shadow_step_count", 8), ("use_gtao", True), ("fast_gi_method", "GLOBAL_ILLUMINATION")):
        if hasattr(ev, k):
            try:
                setattr(ev, k, v)
            except (TypeError, AttributeError):
                pass
    sc.render.use_motion_blur = True
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1920, 1080, 100
    sc.render.image_settings.file_format = "PNG"
    sc.render.filepath = str(keluar) + "/"


# ------------------------------------------------------------------ render berdenyut (GPU laptop panas, 22 Nov 2026)
def suhu_gpu():
    import subprocess
    try:
        r = subprocess.run([r"C:\Windows\System32\nvidia-smi.exe", "--query-gpu=temperature.gpu", "--format=csv,noheader"],
                           capture_output=True, text=True, timeout=10)
        return int(r.stdout.strip())
    except Exception:
        return None


def tunggu_dingin(batas=60, maks=300):
    import time
    t0 = time.time()
    while time.time() - t0 < maks:
        t = suhu_gpu()
        if t is None or t < batas:
            return
        time.sleep(3)


def render_berdenyut(png, tahap=10, detik=8):
    """Gambar diam dalam `tahap` semburan GPU <= `detik` s (seed berbeda, sudah didenoise), rata-rata float, lalu AgX ke PNG."""
    import numpy as np
    sc = bpy.context.scene
    cy = sc.cycles
    sc.render.use_persistent_data = True  # BVH tidak dibangun ulang tiap semburan
    cy.use_adaptive_sampling = False
    cy.samples, cy.time_limit = 100000, detik
    if hasattr(cy, "denoising_use_gpu"):
        cy.denoising_use_gpu = False  # denoiser di CPU: GPU sempat dingin
    sm = sc.render.image_settings
    sm.file_format, sm.color_depth = "OPEN_EXR", "32"
    tmp = Path(png).parent / "_denyut"
    tmp.mkdir(exist_ok=True)
    w, h = sc.render.resolution_x, sc.render.resolution_y
    jumlah = None
    for i in range(tahap):
        tunggu_dingin(60)
        cy.seed = 7919 * (i + 1)
        exr = tmp / f"tahap_{i:02d}.exr"
        sc.render.filepath = str(exr)
        bpy.ops.render.render(write_still=True)
        img = bpy.data.images.load(str(exr))
        px = np.empty(w * h * 4, dtype=np.float32)
        img.pixels.foreach_get(px)
        bpy.data.images.remove(img)
        jumlah = px if jumlah is None else jumlah + px
        print(f"DENYUT {i + 1}/{tahap} suhu {suhu_gpu()}", flush=True)
    hasil = bpy.data.images.new("Hasil berdenyut", w, h, alpha=True, float_buffer=True)
    hasil.pixels.foreach_set(jumlah / tahap)
    sm.file_format, sm.color_depth, sm.color_mode = "PNG", "8", "RGB"
    hasil.save_render(str(png), scene=sc)  # menerapkan AgX dan eksposur adegan
    for f in tmp.glob("*.exr"):
        f.unlink()


def video_per_frame(keluar, langkah=1):
    """Render animasi frame demi frame: tunggu bila GPU >= 75 °C; frame yang sudah ada dilewati (bisa dilanjutkan)."""
    sc = bpy.context.scene
    for f in range(sc.frame_start, sc.frame_end + 1, langkah):
        out = Path(keluar) / f"{f:04d}.png"
        if out.exists():
            continue
        t = suhu_gpu()
        if t is not None and t >= 75:
            tunggu_dingin(62)
        sc.frame_set(f)
        sc.render.filepath = str(out)
        bpy.ops.render.render(write_still=True)
