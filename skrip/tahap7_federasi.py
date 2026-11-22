"""Tahap 7 langkah 7.2: federasi IFC ARS + STR + alat/ruang MEP, clash, dan validasi IFC (IDS sederhana).

DATA SIMULASI untuk studi kasus portofolio. Disusun AI (22 Nov 2026), status draf, disetujui atas delegasi Defsa
22 Nov 2026. Masukan: `model/RSTB-ARS-T7-LOD300.ifc` (7.1), `model/RSTB-STR-T7-LOD300.ifc` (7.3, basis 6.9), Data Beban MEP Rinci
(Tahap 4, alat M-01/M-02/M-04, R-03, R-06). Keluaran: `model/RSTB-FED-T7.ifc`, `07 DED dan RKS/7.2 Koordinasi dan
Clash.xlsx` + `.md`.

Federasi: unsur STR disalin ke berkas ARS (konteks geometri dan storey disatukan, tulangan IfcReinforcingBar tidak
ikut: tetap di model STR, supaya berkas federasi ringan untuk clash dan render). Clash: ifcopenshell.geom.tree
(clash_intersection_many), ditambah cek aturan (jarak MRI, P4/KDB) dengan shapely.
"""
from __future__ import annotations

import json
import multiprocessing
import pickle
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import ifcopenshell
import ifcopenshell.api as api
import ifcopenshell.geom as geom
import ifcopenshell.util.element as ue
import ifcopenshell.util.placement as upl
import numpy as np
from shapely.geometry import MultiPoint, Point, box
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).parent))

AKAR = Path(__file__).resolve().parents[1]
ARS = AKAR / "model" / "RSTB-ARS-T7-LOD300.ifc"
STR = AKAR / "model" / "RSTB-STR-T7-LOD300.ifc"      # 7.3 (basis 6.9: K-01, rel chiller, LB-1, pit L-7)
STR6 = AKAR / "model" / "RSTB-STR-T6-LOD300.ifc"     # pembanding kolom "awal" (sebelum 7.3)
FED = AKAR / "model" / "RSTB-FED-T7.ifc"
KELUAR = AKAR / "07 DED dan RKS"
XLSX = KELUAR / "7.2 Koordinasi dan Clash.xlsx"
MD = KELUAR / "7.2 Koordinasi dan Clash.md"
CACHE = AKAR / "cache" / "tahap7_federasi"
STATUS = "draf, disetujui atas delegasi Defsa 22 Nov 2026"
LABEL = "DATA SIMULASI untuk studi kasus portofolio, tidak untuk konstruksi."
SUMBER_MEP = "[04 Struktur Atas/Data Owner/Data Beban MEP Rinci.xlsx]"

ISOCENTER = (80.5, 57.0)          # Syarat MRI butir 1 (Data Beban MEP Rinci, lembar Syarat MRI)
JARAK_LOGAM = 12.0                # Syarat MRI butir 2: benda logam bergerak besar ≥ 12,0 m dari isocenter
PANEL_MRI = (76.0, 51.0, 84.0, 59.0)   # pelat panel 9-10/D-E dipisah sambungan isolasi (5.2/5.3)
TOL_CLASH = 0.002                 # m; penetrasi ≤ 2 mm dianggap menempel (bukan clash)

# alat MEP: (kode, kelas IFC, uraian, storey, x0, y0, x1, y1, tinggi m, alas di atas lantai m, catatan)
# M-01: 4 unit 11,0 × 2,3 m, jarak antarunit 1,2 m (Daftar Alat no. 1); 7.3: pindah ke y ≥ 63, diputar (11 m arah y)
ALAT = [(f"M-01-{i + 1}", "IfcChiller", "Chiller berpendingin udara 350 TR", "LT3",
         68.4 + 3.5 * i, 63.5, 70.7 + 3.5 * i, 74.5, 2.5, 0.3,
         "115,8 kN operasi; kipas 14,5 Hz; [Asumsi tinggi 2,5 m; alas 0,3 m di atas pelat: lapis atap 150 + rel/pegas]") for i in range(4)] + [
    # M-02 tangki tidak ditambah: sudah ada di model ARS sebagai tangki opsi B (TK-Panel100, x 60-68, y 67-75, 5.x)
    ("M-04", "IfcPump", "Pompa sirkulasi air dingin primer (4 unit, kotak kelompok; 7.3: pindah)", "LT3", 60.0, 62.0, 68.0, 66.0,
     1.0, 0.3, "bantalan inersia + pegas di atas lapis atap 150; [Asumsi tinggi 1,0 m]"),
    ("R-03", "IfcMedicalDevice", "MRI 1,5 T: magnet", "LT1", 79.4, 55.8, 81.6, 58.2, 2.3, 0.05,
     "48,1 kN; isocenter (80,5; 57,0); [Asumsi tinggi 2,3 m]"),
    ("R-06", "IfcCompressor", "MRI: kompresor kriogenik di atas pegas δ ≥ 25 mm", "LT1", 74.5, 60.7, 75.5, 61.3, 1.2, 0.15,
     "3,9 kN; getaran 50 Hz; pegas δ ≥ 25 mm dan dudukan sendiri (5.2); [Asumsi tinggi 1,2 m]"),
]


# ------------------------------------------------------------------ federasi
def _salin_rel(fa, rel, peta):
    """Salin relasi STR ke berkas federasi; daftar Related* disaring ke unsur yang ikut, Relating* non-produk disalin."""
    data = {}
    for k, v in rel.get_info(recursive=False, include_identifier=False).items():
        if k == "type":
            continue
        if isinstance(v, tuple) and v and isinstance(v[0], ifcopenshell.entity_instance):
            v = [peta[x.id()] for x in v if x.id() in peta]
            if not v:
                return None
        elif isinstance(v, ifcopenshell.entity_instance):
            if v.is_a("IfcProduct"):
                if v.id() not in peta:
                    if not v.is_a("IfcOpeningElement"):
                        return None
                    peta[v.id()] = fa.add(v)
                v = peta[v.id()]
            else:
                v = fa.add(v)
        data[k] = v
    try:   # BIMCraft memberi GlobalId relasi yang sama di dua model: beri GlobalId baru bila sudah dipakai
        fa.by_guid(data["GlobalId"])
        data["GlobalId"] = ifcopenshell.guid.new()
    except RuntimeError:
        pass
    return fa.create_entity(rel.is_a(), **data)


def _satukan_konteks(fa, asli):
    """Konteks geometri hasil salinan STR diganti konteks ARS yang sama (ContextType/Identifier/TargetView)."""
    def kunci(c):
        return (c.ContextType, getattr(c, "ContextIdentifier", None), getattr(c, "TargetView", None))
    induk = [c for c in asli if not c.is_a("IfcGeometricRepresentationSubContext")]
    peta = {kunci(c): c for c in asli}
    baru = [c for c in fa.by_type("IfcGeometricRepresentationContext") if c.id() not in {a.id() for a in asli}]
    for c in sorted(baru, key=lambda c: not c.is_a("IfcGeometricRepresentationSubContext")):
        ganti = peta.get(kunci(c)) or (induk[0] if not c.is_a("IfcGeometricRepresentationSubContext")
                                         else peta.get(("Model", "Body", "MODEL_VIEW")) or induk[0])
        for inv in fa.get_inverse(c):
            ue.replace_attribute(inv, c, ganti)
        fa.remove(c)
    return len(baru)


def _kotak(fa, ctx, dx, dy, h):
    prof = fa.createIfcRectangleProfileDef("AREA", None, fa.createIfcAxis2Placement2D(
        fa.createIfcCartesianPoint((dx / 2, dy / 2)), None), dx, dy)
    solid = fa.createIfcExtrudedAreaSolid(prof, fa.createIfcAxis2Placement3D(fa.createIfcCartesianPoint((0.0, 0.0, 0.0)),
                                                                              None, None),
                                          fa.createIfcDirection((0.0, 0.0, 1.0)), h)
    return fa.createIfcProductDefinitionShape(None, None, [fa.createIfcShapeRepresentation(ctx, "Body", "SweptSolid",
                                                                                          [solid])])


def _letak(fa, storey, x, y, dz):
    return fa.createIfcLocalPlacement(storey.ObjectPlacement, fa.createIfcAxis2Placement3D(
        fa.createIfcCartesianPoint((x, y, dz)), None, None))


def _pset(fa, el, props):
    ps = api.run("pset.add_pset", fa, product=el, name="Pset_RSTB_Umum")
    api.run("pset.edit_pset", fa, pset=ps, properties=props)


def bounds_unsur(f, el, s=None):
    s = s or geom.settings()
    s.set("use-world-coords", True)
    v = np.array(geom.create_shape(s, el).geometry.verts).reshape(-1, 3)
    return v.min(0), v.max(0)


def federasi(ars=ARS, str_=STR, keluar=FED):
    t0 = time.time()
    fa, fs = ifcopenshell.open(str(ars)), ifcopenshell.open(str(str_))
    asli_ctx = list(fa.by_type("IfcGeometricRepresentationContext"))
    st_a = {s.Name: s for s in fa.by_type("IfcBuildingStorey")}
    # placement storey harus sama (T-110), supaya placement relatif unsur STR bisa ditempel ke storey ARS
    for s in fs.by_type("IfcBuildingStorey"):
        ma, ms = upl.get_local_placement(st_a[s.Name].ObjectPlacement), upl.get_local_placement(s.ObjectPlacement)
        assert np.allclose(ma, ms, atol=1.0), f"placement storey {s.Name} ARS ≠ STR"
    peta, jumlah, wadah = {}, Counter(), defaultdict(list)
    for el in fs.by_type("IfcElement"):
        # tulangan tetap di model STR; pintu STR tidak ikut karena kembar dengan pintu ARS 0,10-0,15 m (cek A-06)
        if el.is_a("IfcReinforcingBar") or el.is_a("IfcFeatureElement") or el.is_a("IfcDoor"):
            continue
        baru = fa.add(el)
        peta[el.id()] = baru
        jumlah[el.is_a()] += 1
        st = ue.get_container(el)
        if st is not None and st.is_a("IfcBuildingStorey"):
            # hanya placement yang relatif ke storey STR yang ditempel ke storey ARS (pintu relatif ke dindingnya)
            if el.ObjectPlacement and el.ObjectPlacement.PlacementRelTo == st.ObjectPlacement:
                baru.ObjectPlacement.PlacementRelTo = st_a[st.Name].ObjectPlacement
            wadah[st.Name].append(baru)
    for kelas in ("IfcRelVoidsElement", "IfcRelFillsElement", "IfcRelDefinesByProperties", "IfcRelDefinesByType",
                  "IfcRelAssociatesMaterial"):
        for rel in fs.by_type(kelas):
            _salin_rel(fa, rel, peta)
    oh = fa.by_type("IfcOwnerHistory")
    for nama, els in wadah.items():
        fa.createIfcRelContainedInSpatialStructure(ifcopenshell.guid.new(), oh[0] if oh else None,
                                                   "Unsur STR", None, els, st_a[nama])
    n_ctx = _satukan_konteks(fa, asli_ctx)
    body = next(c for c in fa.by_type("IfcGeometricRepresentationSubContext") if c.ContextIdentifier == "Body")
    # alat MEP (kotak) dan ruang shaft dari lubang STR
    for kode, kelas, uraian, lt, x0, y0, x1, y1, h, dz, cat in ALAT:
        el = api.run("root.create_entity", fa, ifc_class=kelas, name=kode)
        el.Description, el.ObjectType = uraian, "ALAT MEP"
        el.ObjectPlacement = _letak(fa, st_a[lt], x0 * 1000, y0 * 1000, dz * 1000)
        el.Representation = _kotak(fa, body, (x1 - x0) * 1000, (y1 - y0) * 1000, h * 1000)
        api.run("spatial.assign_container", fa, products=[el], relating_structure=st_a[lt])
        _pset(fa, el, {"Sumber": f"7.2 federasi {SUMBER_MEP}", "Catatan": cat})
        jumlah["alat MEP"] += 1
    elev = sorted((s.Elevation, s.Name) for s in fa.by_type("IfcBuildingStorey"))
    s = geom.settings()
    s.set("use-world-coords", True)
    for o in fs.by_type("IfcOpeningElement"):
        if not (o.Name or "").startswith("Shaft"):
            continue
        host = o.VoidsElements[0].RelatingBuildingElement
        lt = ue.get_container(host).Name
        lo, hi = bounds_unsur(fs, o, s)
        z = st_a[lt].Elevation
        z_atas = next((e for e, n in elev if e > z + 1), z + 4200)
        sp = api.run("root.create_entity", fa, ifc_class="IfcSpace", name=f"SH-{lt}-{jumlah['ruang shaft'] + 1:02d}")
        sp.LongName, sp.ObjectType = "Shaft MEP / lift (lubang pelat STR)", "SHAFT"
        sp.ObjectPlacement = _letak(fa, st_a[lt], lo[0] * 1000, lo[1] * 1000, 0.0)
        sp.Representation = _kotak(fa, body, (hi[0] - lo[0]) * 1000, (hi[1] - lo[1]) * 1000, z_atas - z)
        api.run("aggregate.assign_object", fa, products=[sp], relating_object=st_a[lt])
        _pset(fa, sp, {"Sumber": f"7.2 dari {o.Name} {o.GlobalId} pada {host.Name} {lt}"})
        jumlah["ruang shaft"] += 1
    proj = fa.by_type("IfcProject")[0]
    proj.Name = "RSTB federasi ARS 7.1 + STR 7.3 + MEP (7.2)"
    fa.write(str(keluar))
    return {"jumlah": dict(jumlah), "konteks_digabung": n_ctx, "detik": round(time.time() - t0, 1),
            "ukuran_mb": round(keluar.stat().st_size / 1e6, 1)}


# ------------------------------------------------------------------ geometri dan clash
def asal(el):
    """'STR' bila unsur salinan model STR (relasi wadah 'Unsur STR 6.9'), 'MEP' untuk alat, selain itu 'ARS'."""
    if (el.ObjectType or "") == "ALAT MEP":
        return "MEP"
    r = el.ContainedInStructure
    return "STR" if r and r[0].Name == "Unsur STR" else "ARS"


def geometri(f, path=FED):
    """Jejak 2D (union segitiga mesh terproyeksi, m) dan rentang z tiap unsur, di-cache menurut ukuran + waktu berkas."""
    import shapely
    st = Path(path).stat()
    cache = CACHE / f"geom_{Path(path).stem}_{st.st_size}_{int(st.st_mtime)}.pkl"
    if cache.exists():
        return pickle.loads(cache.read_bytes())
    els = [e for e in f.by_type("IfcElement") if not e.is_a("IfcVirtualElement") and not e.is_a("IfcFeatureElement")]
    els += [o for o in f.by_type("IfcOpeningElement") if (o.Name or "").startswith("Shaft")]
    s = geom.settings()
    s.set("use-world-coords", True)
    s.set("disable-opening-subtractions", False)
    it = geom.iterator(s, f, multiprocessing.cpu_count(), include=els)
    hasil = {}
    if it.initialize():
        while True:
            sh = it.get()
            v = np.array(sh.geometry.verts).reshape(-1, 3)
            t = np.array(sh.geometry.faces).reshape(-1, 3)
            if len(t):
                tri = v[t][:, :, :2]
                ar = 0.5 * np.abs((tri[:, 1, 0] - tri[:, 0, 0]) * (tri[:, 2, 1] - tri[:, 0, 1])
                                  - (tri[:, 2, 0] - tri[:, 0, 0]) * (tri[:, 1, 1] - tri[:, 0, 1]))
                tri = tri[ar > 1e-6]
                ring = np.concatenate([tri, tri[:, :1]], axis=1)
                jejak = shapely.union_all(shapely.polygons(ring)).buffer(0)
                hasil[sh.guid] = (shapely.to_wkb(jejak), float(v[:, 2].min()), float(v[:, 2].max()))
            if not it.next():
                break
    CACHE.mkdir(parents=True, exist_ok=True)
    cache.write_bytes(pickle.dumps(hasil))
    return hasil


def kelompok(el):
    n = el.Name or ""
    return f"{el.is_a()}:{n.split('-')[0] if '-' in n else n[:10]}"


def potong(ga, gb):
    """Penetrasi 2,5D: min(tumpang z, lebar terkecil irisan jejak). 0 bila hanya menempel."""
    ja, za0, za1 = ga
    jb, zb0, zb1 = gb
    zov = min(za1, zb1) - max(za0, zb0)
    if zov <= TOL_CLASH:
        return 0.0, None
    ir = ja.intersection(jb)
    if ir.is_empty or ir.area < 1e-6:
        return 0.0, None
    r = ir.minimum_rotated_rectangle
    x, y = r.exterior.coords.xy
    sisi = sorted(((x[i + 1] - x[i]) ** 2 + (y[i + 1] - y[i]) ** 2) ** 0.5 for i in range(4))
    return min(zov, sisi[0]), ir


def clash_mentah(f, g):
    """Semua pasangan berpotongan (penetrasi > TOL_CLASH) antara kelompok yang dikoordinasikan (metode 2,5D)."""
    import shapely
    from shapely.strtree import STRtree
    geo = {k: (shapely.from_wkb(w), z0, z1) for k, (w, z0, z1) in g.items()}
    semua = [e for e in f.by_type("IfcElement") if e.GlobalId in geo and not e.is_a("IfcFeatureElement")]
    stru = [e for e in semua if asal(e) == "STR"]
    ars = [e for e in semua if asal(e) == "ARS"]
    mep = [e for e in semua if asal(e) == "MEP"]
    shaft = [o for o in f.by_type("IfcOpeningElement") if o.GlobalId in geo]
    pit = [e for e in stru if (e.Name or "").startswith("PIT")]
    cap = [e for e in stru if e.is_a("IfcFooting")]
    hasil = []
    pintu_s = [e for e in stru if e.is_a("IfcDoor")]
    pintu_a = [e for e in ars if e.is_a("IfcDoor")]
    for nama, a, b in (("STR vs ARS", stru, ars), ("MEP vs STR+ARS", mep, stru + ars), ("Shaft vs ARS", shaft, ars),
                       ("Shaft vs STR", shaft, [e for e in stru if not e.is_a("IfcSlab")]), ("Pit vs cap", pit, cap),
                       ("MEP vs MEP", mep, mep), ("Pintu STR vs ARS", pintu_s, pintu_a)):
        pb = STRtree([geo[e.GlobalId][0] for e in b])
        for ea in a:
            gaa = geo[ea.GlobalId]
            for j in pb.query(gaa[0]):
                eb = b[int(j)]
                if eb == ea or (nama == "MEP vs MEP" and eb.id() < ea.id()):
                    continue
                d, ir = potong(gaa, geo[eb.GlobalId])
                if d > TOL_CLASH:
                    c = ir.representative_point()
                    hasil.append({"set": nama, "a": ea.GlobalId, "b": eb.GlobalId, "ka": kelompok(ea), "kb": kelompok(eb),
                                  "na": ea.Name, "nb": eb.Name, "d": round(d, 3), "luas": round(ir.area, 3),
                                  "p": [round(c.x, 2), round(c.y, 2), round(max(gaa[1], geo[eb.GlobalId][1]), 2)]})
    return hasil, geo


def ringkas(clash):
    g = defaultdict(lambda: [0, 0.0])
    for c in clash:
        k = (c["set"], c["ka"], c["kb"])
        g[k][0] += 1
        g[k][1] = max(g[k][1], c["d"])
    return sorted(((*k, n, round(d, 3)) for k, (n, d) in g.items()), key=lambda r: -r[3])


def jalankan_clash(fed=FED):
    f = ifcopenshell.open(str(fed))
    t0 = time.time()
    g = geometri(f, fed)
    t1 = time.time()
    c, geo = clash_mentah(f, g)
    return f, geo, c, {"geometri_s": round(t1 - t0, 1), "clash_s": round(time.time() - t1, 1), "unsur": len(g)}




# ------------------------------------------------------------------ klasifikasi clash
# kode: (uraian, kritis, status, tindakan, pemilik, penetrasi maks yang diterima m atau None)
KELOMPOK = {
    "K-01": ("Balok BL-350x600 as 6 (x 52) bentang B-C melintas di ruang luncur lift L-1..4 (lubang inti lift LT2-LT6)",
             True, "diperbaiki",
             "7.3: 6 balok as 6 di dalam inti lift dihapus dari model STR 7.3; model OpenSees 4.3 tanpa balok berubah "
             "≤ 0,22 % (T, simpangan, porsi geser inti), hasil Tahap 4-6 tetap (7.3 Cek Struktur Tambahan)",
             "AI struktur (7.3), disetujui atas delegasi Defsa 22 Nov 2026", None),
    "K-02": ("Kolom KL-750 6/B dan 6/C menonjol 0,20 m dari muka dalam dinding inti lift", False, "diterima",
             "Ruang bebas arah y 7,25 m ≥ 2 × 3,1 + 0,2 = 6,4 m (Data Lift: 2 × 2 shaft @ 2,6 × 3,1 m); tonjolan "
             "digambar di GA denah inti (7.4) dan diperiksa pemasok lift untuk braket rel", "Arsitek (7.4), pemasok lift", 0.20),
    "K-03": ("Lapis lantai, plafon, partisi, dan lapis atap ARS menutup atau memotong shaft dan lubang lift STR", True,
             "diperbaiki",
             "tahap7_arsitektur.py: shaft STR (tahap4_bim.SHAFT) jadi rintangan tata letak dengan selubung bata 100, ruang "
             "shaft dan ruang luncur lift tanpa lapis lantai (R-VOID), lubang shaft di lapis atap menara, podium, dan "
             "taman atap; model 7.1 dibangun ulang", "AI arsitektur (7.2)", None),
    "K-04": ("Pit lift (PIT-400/450) di dalam Cap E gabungan", False, "diterima",
             "Pit dicor menyatu dengan Cap E (keputusan 6.7 dan 6.9: pit berdiri di Cap E); tulangan pit di gambar "
             "pondasi 6.10; pit L-5..7 tetap temuan terbuka Ringkasan Tahap 6", "AI struktur (6.10/7.5)", None),
    "K-05": ("Alat MEP menembus lapis lantai/atap atau digandakan (tangki M-02)", True, "diperbaiki",
             "Tangki M-02 tidak ditambah (sudah ada di ARS sebagai tangki opsi B); alas M-01/M-04 dinaikkan 0,3 m di atas "
             "pelat (lapis atap 150 + rel/pegas), magnet MRI di atas lapis lantai 50", "AI MEP koordinasi (7.2)", None),
    "K-04b": ("Pit lift sebagian di luar telapak Cap E (pit L-5..6 dan L-7 menggantung di tanah)", False, "diterima",
              "7.3: L-7 ditutup perlebaran Cap E x 37,1-41,7 y 29,4-32,2 + 2 tiang Ø800 (STR 7.3); L-5..6 menjorok 0,39 m "
              "sebagai kantilever pelat dasar pit (Mu 4,0 ≤ φMn min 91 kNm/m), tidak diperlebar", "AI struktur (7.3), "
              "disetujui atas delegasi Defsa 22 Nov 2026", None),
    "K-07": ("Partisi bata ringan dan lapis inti ARS menempel atau masuk muka kolom/dinding inti STR", False, "diterima",
             "BIMCraft tidak memotong dinding pada unsur model lain; di lapangan partisi berhenti di muka struktur "
             "(detail sambungan partisi-kolom GA 7.4); penetrasi ≤ 150 mm = tebal partisi", "Arsitek (7.4)", 0.15),
    "K-08": ("Lapis lantai 50 mm dan plafon gypsum 12 mm tidak dipotong di kolom dan tangga STR", False, "diterima",
             "Volume tumpang kecil; QTO Tahap 8 mengurangi luas tembus kolom dari luas finishing", "QS (Tahap 8)", 0.05),
    "K-09": ("Cap tepi (PC-4000x1600) menembus lapis rumput 100 di tepi podium", False, "diterima",
             "Puncak cap tepi = muka halaman +12,05 (6.3); tepi bangunan diberi paving/plester di atas cap, rumput mulai di "
             "luar tepi cap (detail tapak GA 7.4)", "Arsitek (7.4)", 0.16),
    "K-10": ("Kolom, dinding inti, dan tiang dek helipad HEB 200 menembus lapis atap 150 / taman atap", False, "diterima",
             "Tembusan diberi detail kedap (flashing) di GA 7.4 dan RKS pekerjaan kedap 7.7", "Arsitek (7.4), RKS (7.7)", 0.16),
    "K-11": ("Pintu ARS di bukaan dinding inti STR (pintu lift/tangga) dan satu pintu 900 masuk 81 mm ke kolom", False,
             "diterima", "Pintu lift dan tangga di muka lapis inti sesuai bukaan STR; pintu 900 di sisi kolom 6/B LT1 "
             "digeser 100 mm saat GA 7.4", "Arsitek (7.4)", 0.10),
    "K-12": ("Railing void LT2 menembus kolom tepi void", False, "diterima",
             "Railing terputus di muka kolom (detail GA 7.4)", "Arsitek (7.4)", 0.40),
    "K-99": ("Lain-lain (belum terklasifikasi)", True, "ditanyakan", "Periksa satu per satu", "AI koordinasi", None),
}


def golong(c):
    ka, kb, s = c["ka"], c["kb"], c["set"]
    if s == "Shaft vs STR":
        return "K-01" if kb.startswith("IfcBeam") else "K-02"
    if s == "Shaft vs ARS":
        return "K-03"
    if s == "Pit vs cap":
        return "K-04"
    if s.startswith("MEP"):
        return "K-05"
    if kb.startswith(("IfcWall:DP", "IfcWall:DL")):
        return "K-07"
    if kb.startswith(("IfcSlab:LT", "IfcCovering")):
        return "K-08"
    if kb.startswith("IfcSlab:TP"):
        return "K-09" if ka.startswith("IfcFooting") else "K-10"
    if kb.startswith("IfcDoor"):
        return "K-11"
    if kb.startswith("IfcRailing"):
        return "K-12"
    return "K-99"


def pit_di_luar_cap(f, geo):
    """Pit (PIT-) yang jejaknya sebagian di luar union telapak pile cap: luas di luar (m²) per pit."""
    cap = unary_union([geo[e.GlobalId][0] for e in f.by_type("IfcFooting") if e.GlobalId in geo])
    out = []
    for e in f.by_type("IfcElement"):
        if (e.Name or "").startswith("PIT") and e.GlobalId in geo:
            j = geo[e.GlobalId][0]
            c = j.centroid
            out.append({"na": e.Name, "luas": j.area, "luar": j.difference(cap).area, "p": (c.x, c.y)})
    return out


def baris_pit(pit, n_awal=None):
    luar = [p for p in pit if p["luar"] > 0.01]
    if not luar:
        return None
    ur, kritis, st, tind, pem, _ = KELOMPOK["K-04b"]
    return {"kode": "K-04b", "uraian": ur, "kritis": kritis, "awal": len(luar) if n_awal is None else n_awal, "akhir": len(luar), "d_maks": 0.0,
            "status": st, "tindakan": tind, "pemilik": pem,
            "contoh": "; ".join(f"{p['na']} @ ({p['p'][0]:.1f}; {p['p'][1]:.1f}): {p['luar']:.2f} dari {p['luas']:.2f} m² "
                                f"di luar cap".replace(".", ",") for p in luar)}


def daftar_clash(akhir, awal):
    """Baris per kelompok: jumlah awal (ARS sekarang + STR 6.9, sebelum 7.3) dan akhir (STR 7.3), penetrasi maks, status."""
    ha, hw = defaultdict(list), defaultdict(list)
    for c in akhir:
        ha[golong(c)].append(c)
    for c in awal:
        hw[golong(c)].append(c)
    baris = []
    for k, (ur, kritis, st, tind, pemilik, batas) in KELOMPOK.items():
        n0, n1 = len(hw[k]), len(ha[k])
        if n0 == 0 and n1 == 0:
            continue
        dmaks = max((c["d"] for c in ha[k]), default=0.0)
        if st == "diterima" and batas is not None and dmaks > batas + 1e-6:
            st = "ditanyakan"   # penetrasi di atas batas yang diterima
        if st == "diperbaiki" and n1 > 0:
            st = "ditanyakan"
        baris.append({"kode": k, "uraian": ur, "kritis": kritis, "awal": n0, "akhir": n1, "d_maks": dmaks,
                      "status": st, "tindakan": tind, "pemilik": pemilik,
                      "contoh": "; ".join(f"{c['na']} × {c['nb']} @ ({c['p'][0]:.1f}; {c['p'][1]:.1f}; {c['p'][2]:.2f})"
                                          for c in (ha[k] or hw[k])[:2])})
    return baris


# ------------------------------------------------------------------ cek aturan (koordinasi tanpa tabrakan geometri)
def _jejak_ruang(f, kata):
    s = geom.settings()
    s.set("use-world-coords", True)
    out = []
    for sp in f.by_type("IfcSpace"):
        if kata in (sp.LongName or ""):
            v = np.array(geom.create_shape(s, sp).geometry.verts).reshape(-1, 3)
            out.append(MultiPoint([tuple(p[:2]) for p in v]).convex_hull)
    return out


def jarak_mri(f, geo):
    iso = Point(ISOCENTER)
    cand = [(e.Name, geo[e.GlobalId][0].distance(iso)) for e in f.by_type("IfcElement")
            if e.GlobalId in geo and (e.Name or "").startswith(("TP-Aspal", "TP-Beton", "RSTB Mobil", "RSTB Motor"))]
    cand += [("Drop-off ambulans", g.distance(iso)) for g in _jejak_ruang(f, "Drop-off")]
    return min(cand, key=lambda t: t[1])


def cek_aturan(f, geo, mri_awal=None):
    import tahap3_tapak as tp
    import tahap4_beban as tb
    import tahap4_bim as bim
    import tahap7_arsitektur as ta
    iso = Point(ISOCENTER)
    el = {e.GlobalId: e for e in f.by_type("IfcElement")}
    nm, dmin = jarak_mri(f, geo)
    awal = "; model 7.1 awal (7.2): 4,1 m (TP-Beton)"
    out = [{"kode": "A-01", "uraian": "Jarak isocenter MRI (80,5; 57,0) ke jalur kendaraan terdekat (aspal, ramp/pelataran "
            "IGD, drop-off, mobil, motor)", "nilai": dmin, "batas": "≥ 12,0 m (Syarat MRI butir 2)",
            "lolos": dmin >= JARAK_LOGAM - 1e-6, "kritis": True,
            "ket": f"terdekat: {nm}{awal}; lajur x 92,5-98,5 tepat 12,0 m (margin 0, keputusan 5.2 opsi 2)"}]
    lift = [box(cx - 4.175, cy - 4.175, cx + 4.175, cy + 4.175) for n, (cx, cy) in bim.PUSAT.items() if n.startswith("Inti")]
    lift.append(box(38.0, 30.0, 40.8, 33.4))   # L-7 (Data Beban MEP Rinci, lembar Lift)
    dl = min(g.distance(iso) for g in lift)
    out.append({"kode": "A-02", "uraian": "Jarak isocenter MRI ke lift dan bobot imbang", "nilai": dl,
                "batas": "≥ 8,0 m (Syarat MRI butir 3)", "lolos": dl >= 8.0, "kritis": True, "ket": "inti lift x 50-58 dan L-7"})
    r06 = next(e for e in el.values() if e.Name == "R-06")
    g6 = geo[r06.GlobalId][0]
    tump = g6.intersection(box(*PANEL_MRI)).area
    out.append({"kode": "A-03", "uraian": "R-06 kompresor kriogenik di atas pegas, di luar pelat panel MRI 9-10/D-E yang "
                "diisolasi", "nilai": tump, "batas": "tumpang 0 m²; pegas δ ≥ 25 mm, dudukan sendiri (5.2)",
                "lolos": tump < 1e-6, "kritis": False,
                "ket": f"jarak ke isocenter {idn(g6.distance(iso))} m; syarat pegas masuk RKS 7.7; gaya dinamis pabrikan "
                       "belum ada (5.2 butir 4)"})
    balok = [e for e in el.values() if e.is_a("IfcBeam") and asal(e) == "STR" and e.GlobalId in geo
             and abs(geo[e.GlobalId][2] - tb.LEVEL["LT3"]) < 0.05]
    sh7 = next(box(x0, y0, x1, y1) for k, x0, x1, y0, y1, *_ in bim.SHAFT if k == "SH-7")
    rinci, n_sh7 = [], 0
    for e in sorted((e for e in el.values() if (e.Name or "").startswith("M-01")), key=lambda e: e.Name):
        g = geo[e.GlobalId][0]
        bb = [b for b in balok if geo[b.GlobalId][0].intersects(g)]
        a7 = g.intersection(sh7).area
        n_sh7 += a7 > 0
        rinci.append(f"{e.Name}: {len(bb)} balok di bawah tapak" + (f", tepi unit di atas SH-7 {idn(a7, 2)} m²" if a7 else ""))
    out.append({"kode": "A-04", "uraian": "Chiller M-01 (4 unit) di atap podium: balok penumpu dan SH-7 (B-7)",
                "nilai": len(rinci), "batas": "rel dudukan di atas balok (≥ 2 per unit), tidak di atas lubang; letak y ≥ 63 "
                "dan pegas 25 mm (7.3, keputusan rencana 5)", "lolos": all(int(r.split(": ")[1].split()[0]) >= 2 for r in rinci)
                and n_sh7 == 0, "kritis": False,
                "ket": "; ".join(rinci) + ". 7.3: frekuensi lantai 4-6 Hz < 20,3 Hz, chiller dipindah ke y ≥ 63 (diputar) di "
                       "atas rel baru arah y, pegas δ 25 mm (RKS)"})
    p4 = box(*ta.P4_BAWAH)
    lajur = unary_union([box(*k) for k in ta.JALAN + [ta.RAMP_IGD, ta.APRON]])
    lain = unary_union([box(*k) for k in [ta.JALAN_LOBI, ta.KANOPI_LOBI, ta.DROPOFF, ta.APRON, ta.RAMP_IGD, ta.v4.PARKIR]
                        + ta.JALAN] + [tb.PODIUM, box(*ta.GU)])
    persil = box(*ta.v4.PERSIL)
    p4_ok = persil.contains(p4) and p4.intersection(lain).area < 1e-6
    out.append({"kode": "A-05", "uraian": "P4 76 motor (x 1-7, y 35-63,5): di dalam persil, tidak menumpang jalan/bangunan, "
                "terpisah dari lajur ambulans", "nilai": p4.distance(lajur), "batas": "di dalam persil, tumpang 0, jarak "
                "ke lajur > 0", "lolos": p4_ok and p4.distance(lajur) > 0, "kritis": False,
                "ket": f"luas {p4.area:.0f} m² (5.2: 192 m² hilang di timur); jarak ke lajur ambulans {idn(p4.distance(lajur))} m"})
    r = tp.ringkasan()
    tapak = unary_union([tb.PODIUM, box(*ta.GU), box(*ta.KANOPI_LOBI),
                         box(ta.DROPOFF[0], ta.DROPOFF[1], ta.APRON[2], ta.APRON[3]), box(*ta.RAMP_IGD)])
    out.append({"kode": "A-06", "uraian": "KDB: tapak bangunan + kanopi lobi dan IGD [Asumsi kanopi dihitung] vs KDB maks "
                "(lahan perencanaan PKKPR, 3.2)", "nilai": tapak.area, "batas": f"≤ {r['kdb_maks']:.0f} m²",
                "lolos": tapak.area <= r["kdb_maks"], "kritis": False,
                "ket": "P4 terbuka tanpa atap tidak dihitung KDB; batas owner 6.300 m²"})
    keras = unary_union([tapak, p4, box(*ta.v4.PARKIR), box(*ta.JALAN_LOBI)] + [box(*k) for k in ta.JALAN])
    hijau = tp.lahan_perencanaan().difference(keras)
    out.append({"kode": "A-07", "uraian": "KDH: ruang hijau di lahan perencanaan setelah P4 dipindah ke barat",
                "nilai": hijau.area, "batas": f"≥ {r['kdh_min']:.0f} m²", "lolos": hijau.area >= r["kdh_min"],
                "kritis": False, "ket": "lahan perencanaan dikurangi bangunan dan perkerasan (3.2)"})
    out.append({"kode": "A-08", "uraian": "Akses motor ke P4 dari gerbang utama", "nilai": None,
                "batas": "ada jalur ≥ 2,0 m [Asumsi]", "lolos": False, "kritis": False,
                "ket": "belum dimodelkan; jalur paving 2,0 m di sepanjang pagar utara ditambah di GA tapak 7.4 (pemilik: arsitek)"})
    return out


def cek_pintu_ganda(ars=ARS, str_=STR):
    """Pintu STR yang berjarak < 0,3 m dari pintu ARS di lantai yang sama (alasan pintu STR tidak ikut federasi)."""
    s = geom.settings()
    s.set("use-world-coords", True)

    def jejak(f):
        out = []
        for d in f.by_type("IfcDoor"):
            v = np.array(geom.create_shape(s, d).geometry.verts).reshape(-1, 3)
            out.append((MultiPoint([tuple(p[:2]) for p in v]).convex_hull, ue.get_container(d).Name))
        return out
    da, ds = jejak(ifcopenshell.open(str(ars))), jejak(ifcopenshell.open(str(str_)))
    kembar = sum(1 for g, lt in ds if min((g.distance(h) for h, l in da if l == lt), default=99) < 0.3)
    return {"pintu_str": len(ds), "kembar": kembar}


# ------------------------------------------------------------------ validasi IFC (IDS sederhana)
PSET_WAJIB = [  # (asal, kelas, pset wajib, butuh material)
    ("STR", "IfcBeam", ["Pset_BeamCommon", "Pset_RSTB_Umum"], True),
    ("STR", "IfcColumn", ["Pset_ColumnCommon", "Pset_RSTB_Umum"], True),
    ("STR", "IfcSlab", ["Pset_SlabCommon", "Pset_RSTB_Umum"], True),
    ("STR", "IfcWall", ["Pset_WallCommon", "Pset_RSTB_Umum"], True),
    ("STR", "IfcFooting", ["Pset_FootingCommon", "Pset_RSTB_Umum"], True),
    ("STR", "IfcPile", ["Pset_PileCommon", "Pset_RSTB_Umum"], True),
    ("ARS", "IfcWall", ["Pset_RSTB_Umum"], True),
    ("ARS", "IfcDoor", ["Pset_RSTB_Umum"], False),
    ("ARS", "IfcSlab", ["Pset_RSTB_Umum"], True),
    ("ARS", "IfcCovering", ["Pset_RSTB_Umum"], False),
    ("ARS", "IfcBuildingElementProxy", ["Pset_RSTB_Umum"], False),
    ("MEP", "IfcDistributionElement", ["Pset_RSTB_Umum"], False),
]
NAMA_POLA = {"STR": r"^([A-Z]{2,4}-[0-9A-Za-z]|HEB \d)", "MEP": r"^[MR]-\d\d",
             "ARS": r"^((DP|DL|FS|PG|TK|BT|LT|TP|PL)-|RSTB |Double Door|Single Door|Railing|Room Separator)"}


def validasi(f):
    import re
    cek = []

    def tambah(kode, butir, lolos, ket):
        cek.append({"kode": kode, "butir": butir, "lolos": bool(lolos), "ket": ket})
    tambah("V-01", "Skema IFC4", f.schema == "IFC4", f.schema)
    n = [len(f.by_type(k)) for k in ("IfcProject", "IfcSite", "IfcBuilding")]
    tambah("V-02", "Satu IfcProject, IfcSite, IfcBuilding (storey STR digabung ke storey ARS)", n == [1, 1, 1],
           "/".join(map(str, n)))
    st = sorted(((s.Name, s.Elevation) for s in f.by_type("IfcBuildingStorey")), key=lambda t: t[1])
    tambah("V-03", "8 storey unik B1-ATAP, elevasi BEP 3.1", len(st) == 8 and len({a for a, _ in st}) == 8,
           ", ".join(f"{a} {b / 1000:.2f}".replace(".", ",") for a, b in st))
    els = [e for e in f.by_type("IfcElement") if not e.is_a("IfcFeatureElement")]
    tanpa = [e for e in els if ue.get_container(e) is None]
    tambah("V-04", "Hierarki ruang: setiap unsur berada di storey", not tanpa, f"{len(tanpa)} tanpa storey dari {len(els)}")
    sp = f.by_type("IfcSpace")
    sp_x = [s for s in sp if not (s.Decomposes and s.Decomposes[0].RelatingObject.is_a("IfcBuildingStorey"))]
    sp_l = [s for s in sp if s.ObjectType != "SHAFT"
            and not ue.get_psets(s).get("Qto_SpaceBaseQuantities", {}).get("NetFloorArea")]
    tambah("V-05", "Ruang (IfcSpace) di storey, bernomor, ruang program punya NetFloorArea",
           not sp_x and not sp_l and all(s.Name for s in sp),
           f"{len(sp)} ruang ({sum(1 for s in sp if s.ObjectType == 'SHAFT')} shaft); di luar storey {len(sp_x)}; "
           f"tanpa luas {len(sp_l)}")
    for i, (a, kelas, psets, mat) in enumerate(PSET_WAJIB, 1):
        xs = [e for e in els if e.is_a(kelas) and asal(e) == a]
        if not xs:
            continue
        kurang = Counter()
        for e in xs:
            ps = ue.get_psets(e)
            kurang.update(p for p in psets if p not in ps)
            if mat and ue.get_material(e) is None:
                kurang["material"] += 1
        tambah(f"V-06.{i:02d}", f"Pset wajib {a} {kelas}: {', '.join(psets)}" + (" + material" if mat else ""),
               not kurang, f"{len(xs)} unsur; " + ("lengkap" if not kurang else
                                                   "; ".join(f"tanpa {k}: {v}" for k, v in kurang.items())))
    for a, pola in NAMA_POLA.items():
        xs = [e for e in els if asal(e) == a and not e.is_a("IfcVirtualElement")]   # garis pemisah ruang bukan unsur fisik
        salah = [e.Name for e in xs if not re.match(pola, e.Name or "")]
        tambah(f"V-07 {a}", f"Nama unsur {a} mengikuti pola {pola}", not salah,
               f"{len(xs) - len(salah)}/{len(xs)}" + (f"; contoh: {', '.join(sorted(set(map(str, salah)))[:4])}" if salah else ""))
    sp_s = [s.Name for s in sp if not re.match(r"^(GU-)?LT\d-(S?\d+)$|^SH-", s.Name or "")]
    tambah("V-07 ruang", "Nomor ruang LTn-nnn / LTn-Snn / GU-LTn-nnn / SH-", not sp_s, f"{len(sp) - len(sp_s)}/{len(sp)}")
    g = [e.GlobalId for e in f.by_type("IfcRoot")]
    tambah("V-08", "GlobalId unik", len(g) == len(set(g)), f"{len(g)} entitas")
    return cek


# ------------------------------------------------------------------ alur lengkap
def ars_awal():
    """IFC ARS 7.1 sebelum koreksi 7.2 (dari cabang main) untuk kolom 'awal' daftar clash."""
    p = CACHE / "ars_awal_7.1.ifc"
    if not p.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        isi = subprocess.run(["git", "show", "main:model/RSTB-ARS-T7-LOD300.ifc"], cwd=AKAR, capture_output=True,
                             check=True).stdout
        p.write_bytes(isi)
    return p


def hitung():
    fed = federasi()
    f, geo, c, w = jalankan_clash()
    p_awal = CACHE / "fed_awal_7.3.ifc"            # 7.2 (1.612 → 1.156 pasangan) tercatat di PROGRES; awal kini = sebelum 7.3
    if not p_awal.exists():
        federasi(str_=STR6, keluar=p_awal)
    fw, geo_w, cw, _ = jalankan_clash(p_awal)
    daftar = daftar_clash(c, cw)
    bp = baris_pit(pit_di_luar_cap(f, geo), sum(p["luar"] > 0.01 for p in pit_di_luar_cap(fw, geo_w)))
    if bp:
        daftar.insert(next(i for i, d in enumerate(daftar) if d["kode"] == "K-04") + 1, bp)
    aturan = cek_aturan(f, geo, jarak_mri(fw, geo_w))
    pintu = cek_pintu_ganda()
    val = validasi(f)
    blender = json.loads((CACHE / "uji_blender.json").read_text(encoding="utf-8")) if (CACHE / "uji_blender.json").exists() else None
    ifc = Counter(e.is_a() for e in f.by_type("IfcElement") if not e.is_a("IfcFeatureElement"))
    ifc["IfcSpace"] = len(f.by_type("IfcSpace"))
    kritis_buka = [d["kode"] for d in daftar if d["kritis"] and d["status"] != "diperbaiki" and d["akhir"] > 0] + \
                  [a["kode"] for a in aturan if a["kritis"] and not a["lolos"]]
    return {"fed": fed, "waktu": w, "daftar": daftar, "aturan": aturan, "pintu": pintu, "validasi": val,
            "blender": blender, "ifc": dict(ifc), "n_akhir": len(c), "n_awal": len(cw), "kritis_buka": kritis_buka,
            "contoh": c}


# ------------------------------------------------------------------ keluaran
def idn(v, d=1):
    if v is None:
        return "-"
    return f"{v:,.{d}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def _status_aturan(a):
    if a["lolos"]:
        return "lolos"
    return "ditanyakan" if a["kode"] in ("A-04", "A-08") else "gagal"


TINDAKAN_ATURAN = {
    "A-01": ("diperbaiki", "Jalan IGD dipindah ke lajur ambulans x 92,5-98,5 (5.2 opsi 2), ramp 9,6 m di lajur, drop-off "
             "digeser ke y 34,6-45,4 dan pelataran putar x 92-98,5 (tahap7_arsitektur.py)", "AI arsitektur (7.2)"),
    "A-02": ("lolos", "-", "-"),
    "A-03": ("diterima", "Syarat pegas δ ≥ 25 mm dan dudukan sendiri ditulis di RKS 7.7; minta gaya dinamis pabrikan",
             "MEP / pemasok MRI lewat owner"),
    "A-04": ("diperbaiki", "7.3: frekuensi lantai atap 4,1-5,6 Hz < 1,4 × 14,5 Hz, jadi chiller dipindah ke y ≥ 63 (unit diputar, "
             "x 68,4-81,2, y 63,5-74,5) di atas 7 rel baru arah y + balok induk x 76, pegas δ 25 mm; pompa M-04 ke x 60-68, "
             "y 62-66", "AI struktur (7.3)"),
    "A-05": ("lolos", "P4 di barat (keputusan rencana 4); tidak terpengaruh lajur ambulans timur", "-"),
    "A-06": ("lolos", "-", "-"),
    "A-07": ("lolos", "-", "-"),
    "A-08": ("ditanyakan", "Jalur paving motor 2,0 m dari gerbang utama ke P4 ditambah di GA tapak 7.4", "Arsitek (7.4)"),
}


def buat_excel(h):
    import openpyxl
    from format_dokumen import AI, Lembar, set_font_bawaan
    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)
    lb = Lembar(wb.create_sheet("Ringkasan"), 1, "Ringkasan koordinasi dan clash 7.2", [6, 70, 26, 40])
    lb.catatan(f"STATUS: {STATUS}. {LABEL}")
    lb.catatan("Petunjuk: lembar Daftar Clash = kelompok clash geometri (awal = ARS 7.2 + STR 6.9, akhir = STR 7.3; "
               "riwayat 7.2: 1.612 → 1.156 pasangan); Cek Aturan = koordinasi jarak/tata letak; Validasi IFC = IDS sederhana; Contoh Clash = 300 pasangan "
               "pertama. Sel hijau = isian/keputusan AI. Hitung ulang: .venv\\Scripts\\python.exe skrip\\tahap7_federasi.py")
    lb.kosong()
    lb.bagian("A", "Hasil utama")
    fed = h["fed"]["jumlah"]
    lb.tabel(["No", "Butir", "Nilai", "Keterangan"], [
        [1, "Unsur STR disalin ke federasi (tanpa tulangan dan pintu STR)",
         sum(v for k, v in fed.items() if k.startswith("Ifc")), ", ".join(f"{k} {v}" for k, v in fed.items() if k.startswith("Ifc"))],
        [2, "Alat MEP dan ruang shaft ditambah", f"{fed.get('alat MEP', 0)} / {fed.get('ruang shaft', 0)}",
         "M-01 ×4, M-04, R-03, R-06; IfcSpace SHAFT dari lubang pelat STR"],
        [3, "Pasangan clash geometri awal → akhir", f"{h['n_awal']} → {h['n_akhir']}", "metode 2,5D, penetrasi > 2 mm"],
        [4, "Kelompok clash kritis terbuka", len([k for k in h["kritis_buka"] if k.startswith("K")]),
         ", ".join(k for k in h["kritis_buka"] if k.startswith("K")) or "-"],
        [5, "Cek aturan kritis gagal", len([k for k in h["kritis_buka"] if k.startswith("A")]),
         ", ".join(k for k in h["kritis_buka"] if k.startswith("A")) or "-"],
        [6, "Validasi IFC lolos", f"{sum(v['lolos'] for v in h['validasi'])}/{len(h['validasi'])}", "lihat lembar Validasi IFC"],
        [7, "T-111 (0 clash kritis terbuka)", "lolos" if not h["kritis_buka"] else "belum lolos",
         "kritis terbuka diteruskan ke 7.3 dengan tindakan dan pemilik" if h["kritis_buka"] else "-"],
    ], rata=list("clcl"), beku=False)
    lb = Lembar(wb.create_sheet("Daftar Clash"), 2, "Daftar clash berstatus per kelompok", [7, 46, 8, 8, 8, 10, 12, 60, 24, 50])
    lb.catatan("Status: diperbaiki (akhir 0), diterima (penetrasi ≤ batas kelompok, alasan di kolom tindakan), ditanyakan "
               "(punya tindakan dan pemilik). Penetrasi = min(tumpang z, lebar terkecil irisan jejak 2D) dalam m.")
    lb.tabel(["Kode", "Uraian", "Kritis", "Awal", "Akhir", "Pen. maks (m)", "Status", "Tindakan", "Pemilik", "Contoh"],
             [[d["kode"], d["uraian"], "ya" if d["kritis"] else "tidak", d["awal"], d["akhir"], d["d_maks"], d["status"],
               d["tindakan"], d["pemilik"], d["contoh"]] for d in h["daftar"]],
             rata=list("clcccccllll"), fmt=[None, None, None, "0", "0", "0.000", None, None, None, None], fill_kolom={6: AI, 7: AI})
    lb = Lembar(wb.create_sheet("Cek Aturan"), 3, "Cek aturan koordinasi (MRI, R-06, chiller, P4, KDB)", [7, 50, 12, 30, 10, 12, 55, 22, 50])
    lb.catatan("Jarak dalam m, luas dalam m². Sumber batas: Data Beban MEP Rinci lembar Syarat MRI; 3.2 tapak (KDB/KDH PKKPR); 5.2.")
    lb.tabel(["Kode", "Cek", "Nilai", "Batas", "Kritis", "Status", "Tindakan", "Pemilik", "Keterangan"],
             [[a["kode"], a["uraian"], a["nilai"], a["batas"], "ya" if a["kritis"] else "tidak",
               TINDAKAN_ATURAN[a["kode"]][0] if a["lolos"] or a["kode"] != "A-01" else "gagal",
               TINDAKAN_ATURAN[a["kode"]][1], TINDAKAN_ATURAN[a["kode"]][2], a["ket"]] for a in h["aturan"]],
             rata=list("clclccll l".replace(" ", "")), fmt=[None, None, "#,##0.00", None, None, None, None, None, None],
             fill_kolom={5: AI, 6: AI})
    lb = Lembar(wb.create_sheet("Validasi IFC"), 4, "Validasi IFC federasi (IDS sederhana)", [10, 70, 10, 70])
    lb.catatan(f"Berkas {FED.name}. Aturan ditetapkan sebelum diperiksa: hierarki, Pset wajib per kelas dan asal, pola nama.")
    lb.tabel(["Kode", "Butir", "Hasil", "Keterangan"], [[v["kode"], v["butir"], "lolos" if v["lolos"] else "temuan", v["ket"]]
                                                       for v in h["validasi"]], rata=list("clcl"))
    lb = Lembar(wb.create_sheet("Contoh Clash"), 5, "Contoh pasangan clash akhir (300 pertama)", [7, 18, 30, 30, 10, 10, 26])
    lb.tabel(["Kode", "Set", "Unsur A", "Unsur B", "Pen. (m)", "Luas (m²)", "Titik x; y; z (m)"],
             [[golong(c), c["set"], c["na"], c["nb"], c["d"], c["luas"], "; ".join(idn(v, 2) for v in c["p"])]
              for c in h["contoh"][:300]], rata=list("cllllcl"), fmt=[None, None, None, None, "0.000", "0.000", None])
    lb = Lembar(wb.create_sheet("Acuan dan Keputusan"), 6, "Acuan dan keputusan 7.2", [8, 60, 70])
    lb.tabel(["No", "Butir", "Isi"], [[i + 1, a, b] for i, (a, b) in enumerate(KEPUTUSAN)], rata=list("cll"), fill_kolom={2: AI})
    KELUAR.mkdir(exist_ok=True)
    wb.save(XLSX)


KEPUTUSAN = [
    ("Isi federasi", "ARS 7.1 (dibangun ulang 7.2) + STR 6.9 tanpa IfcReinforcingBar (8.070 batang tetap di model STR) dan "
     "tanpa pintu STR (37 kembar dengan pintu ARS) + 7 alat MEP + 31 ruang shaft. Usulan AI, disetujui atas delegasi Defsa 22 Nov 2026."),
    ("Metode clash", "ifcopenshell 0.9 di .venv tidak menyediakan backend tree untuk clash_intersection_many; dipakai metode "
     "2,5D: jejak 2D (union segitiga mesh terproyeksi, shapely) × rentang z, kandidat dari STRtree, penetrasi > 2 mm. "
     "Batasan: unsur miring (ramp) dan cekung dalam arah z dibaca sebagai prisma, jadi hasil cenderung lebih banyak (aman)."),
    ("Jalur ambulans dan drop-off IGD", "Model 7.1 memakai jalan V4 x 84,6-92 (4,1 m dari isocenter); dikoreksi ke lajur 5.2 "
     "opsi 2 x 92,5-98,5 dan drop-off y 34,6-45,4. Disetujui atas delegasi Defsa 22 Nov 2026."),
    ("Shaft STR di model ARS", "Shaft tahap4_bim.SHAFT jadi rintangan tata letak, selubung bata 100, ruang R-VOID tanpa lapis "
     "lantai; ruang luncur lift juga R-VOID; lubang shaft di lapis atap. Disetujui atas delegasi Defsa 22 Nov 2026."),
    ("Balok di ruang luncur lift (K-01)", "Ditanyakan ke 7.3 (struktur), bukan diubah di 7.2. Ditutup di 7.3: 6 balok dihapus "
     "dari STR 7.3 (`tahap7_cek_struktur.py`), model OpenSees 4.3 berubah ≤ 0,22 %; federasi diulang dengan STR 7.3."),
    ("Rekap 3.4 luas massa", "tahap3_program.buat_excel: LT2 = 3.456 - 26 × 24 = 2.832 m², LT3 = 3.456 - 48 × 24 = 2.304 m²; "
     "3.4 Program Ruang Konsultan.xlsx dibuat ulang (temuan T-109c 7.1)."),
    ("Acuan", "Syarat MRI dan data alat: 04 Struktur Atas/Data Owner/Data Beban MEP Rinci.xlsx (data simulasi). KDB/KDH: "
     "3.2 (tahap3_tapak). Pedoman clash/IDS resmi (buildingSMART IDS 1.0) tidak ada di acuan/: aturan IDS ditulis sendiri."),
]


def tulis_md(h):
    o = ["# 7.2 Koordinasi dan Clash (federasi ARS + STR + MEP)", "",
         f"Status: **{STATUS}**. {LABEL}", "",
         "Skrip: `skrip/tahap7_federasi.py` (federasi, clash, cek aturan, validasi) dan `skrip/tahap7_uji_blender.py`. "
         f"Model: `model/{FED.name}` ({idn(h['fed']['ukuran_mb'])} MB). Excel: `07 DED dan RKS/{XLSX.name}`.", "",
         "## Ringkasan", ""]
    o += [f"- Federasi: ARS 7.1 (dibangun ulang) + {sum(v for k, v in h['fed']['jumlah'].items() if k.startswith('Ifc'))} unsur STR "
          f"7.3 + {h['fed']['jumlah'].get('alat MEP', 0)} alat MEP + {h['fed']['jumlah'].get('ruang shaft', 0)} ruang shaft; tulangan "
          "dan pintu STR tidak ikut (alasan di Keputusan).",
          f"- Clash geometri: {h['n_awal']} pasangan dengan STR 6.9 → {h['n_akhir']} dengan STR 7.3 (riwayat 7.2: 1.612 pada model "
          "7.1 awal → 1.156); sisanya kelompok diterima (menempel/finishing).",
          f"- **T-111: {'lolos' if not h['kritis_buka'] else 'belum lolos'}**; kritis terbuka: "
          f"{', '.join(h['kritis_buka']) or 'tidak ada'}.", ""]
    o += ["## Daftar clash (kelompok)", "", "| Kode | Uraian | Kritis | Awal | Akhir | Pen. maks (m) | Status | Tindakan | Pemilik |",
          "|---|---|---|---|---|---|---|---|---|"]
    o += [f"| {d['kode']} | {d['uraian']} | {'ya' if d['kritis'] else 'tidak'} | {d['awal']} | {d['akhir']} | {idn(d['d_maks'], 3)} | "
          f"{d['status']} | {d['tindakan']} | {d['pemilik']} |" for d in h["daftar"]]
    o += ["", "## Cek aturan koordinasi", "", "| Kode | Cek | Nilai | Batas | Status | Tindakan / keterangan |", "|---|---|---|---|---|---|"]
    for a in h["aturan"]:
        st, tind, pem = TINDAKAN_ATURAN[a["kode"]]
        st = st if a["lolos"] or a["kode"] != "A-01" else "gagal"
        o.append(f"| {a['kode']} | {a['uraian']} | {idn(a['nilai'], 2)} | {a['batas']} | {st} | {a['ket']}"
                 + (f". Tindakan: {tind} ({pem})" if tind != "-" else "") + " |")
    o += ["", "## Validasi IFC (IDS sederhana)", "", "| Kode | Butir | Hasil | Keterangan |", "|---|---|---|---|"]
    o += [f"| {v['kode']} | {v['butir']} | {'lolos' if v['lolos'] else 'temuan'} | {v['ket']} |" for v in h["validasi"]]
    o += ["", "Temuan validasi bukan clash: STR IfcWall tanpa Pset_WallCommon dan IfcPile memakai Pset_ColumnCommon "
          "(bawaan BIMCraft; diperbaiki saat model STR diperbarui di 7.3); lapis lantai ruang (IfcSlab LT-) dan plafon "
          "(IfcCovering) dibuat otomatis oleh ruang BIMCraft sehingga tanpa Pset_RSTB_Umum (sumbernya tercatat di Pset ruang).", ""]
    b = h.get("blender")
    o += ["## Uji alur Blender + Bonsai (pratinjau T-117, bukan render akhir)", ""]
    if b:
        ifc = h["ifc"]
        baris = []
        for k in sorted(set(ifc) | set(b["kelas_blender"])):
            if k in ("IfcOpeningElement",):
                continue
            baris.append(f"| {k} | {ifc.get(k, 0)} | {b['kelas_blender'].get(k, 0)} | {b['kelas_blender'].get(k, 0) - ifc.get(k, 0)} |")
        o += [f"- Perintah: `alat\\blender\\blender.exe -b --python skrip\\tahap7_uji_blender.py -- model\\{FED.name}`; impor "
              f"{idn(b['impor_s'])} s, render {b['mesin']} 1600 × 1000 px {idn(b['render_s'])} s. Hasil: "
              "`07 DED dan RKS/Gambar/7.2 Uji Blender.png` (dilihat).",
              f"- Material objek mesh: {b['material']}; unsur tanpa mesh: {b['unsur_tanpa_mesh']}.", "",
              "| Kelas | ifcopenshell | Blender (Bonsai) | Selisih |", "|---|---|---|---|"] + baris + [""]
        o += CATATAN_BLENDER + [""]
    else:
        o += ["- Belum dijalankan.", ""]
    o += ["## Perbaikan di model ARS (dibangun ulang)", "",
          "- Shaft STR SH-1..SH-7 dan LB-2 jadi rintangan tata letak dengan selubung bata 100; ruang shaft dan ruang luncur "
          "lift memakai tipe ruang R-VOID (tanpa lapis lantai dan plafon); lubang shaft di lapis atap menara, atap podium, dan "
          "taman atap LT4. Ruang HCU LT2 diberi takik di SH-2.",
          "- Jalan IGD x 92,5-98,5 (lajur 5.2 opsi 2), ramp 9,6 m di lajur (y 45,4-55), pelataran putar x 92-98,5, drop-off "
          "x 84,6-92 y 34,6-45,4, gerbang jalan IGD x 92,5-98,5; pohon dan mobil di atas perkerasan baru dihapus.",
          "- T-109 dan T-110 diulang setelah bangun ulang: tetap lolos (lihat `7.1 Model Arsitektur.md`).",
          "- Catatan untuk 7.6 (MEP): ruang program \"Shaft MEP\" 3.4 (6 ruang × 32 m², satu per lantai) tetap ruang berlantai "
          "di ARS dan belum punya lubang pelat di STR; letaknya dicocokkan dengan SH-1..SH-7 saat koordinasi MEP dasar 7.6.", "",
          "## Koreksi Rekap 3.4", "",
          "Kolom \"Luas massa\" lembar Rekap Lantai berasal dari `tahap3_program.buat_excel` (luas podium penuh untuk LT1-LT3). "
          "Dikoreksi: LT2 2.832 m² (tanpa void 36-62 × 51-75, zonasi 3.4), LT3 2.304 m² (tanpa x 36-84 y 51-75, V1 Tahap 4), "
          "dan `03 Desain Konsep/3.4 Program Ruang Konsultan.xlsx` dibuat ulang; uji `test_tahap3_program.py` lolos.", "",
          "## Keputusan (disetujui atas delegasi Defsa 22 Nov 2026)", ""]
    o += [f"{i + 1}. **{a}**: {b_}" for i, (a, b_) in enumerate(KEPUTUSAN)]
    o += ["", "## Langkah berikutnya", "",
          "7.3 selesai (K-01, A-04, K-04b ditutup; `7.3 Cek Struktur Tambahan.md`). Berikutnya 7.4-7.6 DED; A-08 jalur motor P4 "
          "di GA tapak 7.4.", ""]
    MD.write_text("\n".join(o), encoding="utf-8")


CATATAN_BLENDER = [   # dari melihat `7.2 Uji Blender.png` (22 Nov 2026); masalah impor untuk 7.8
    "Pratinjau T-117: jumlah unsur per kelas di Blender (Bonsai) sama dengan ifcopenshell (selisih 0); Blender juga memuat "
    "tipe (IfcWallType dan sebagainya) yang tidak dihitung. Impor ±10 s, render Eevee ±27 s: jauh di bawah batas 10 menit.",
    "Catatan untuk 7.8: (1) tiang pancang dan cap tampak menggantung di bawah tapak karena tanah tidak dimodelkan: "
    "sembunyikan IfcPile/IfcFooting atau beri blok tanah; (2) ±53 % objek mesh tanpa material Blender (warna dari gaya IFC "
    "saja): perlu material PBR per tipe (panel putih, kaca biru, aspal, rumput, air); (3) langit belum memakai Sky Texture/HDRI "
    "dan cahaya datar, warna pucat; (4) ruang (IfcSpace) dan garis pemisah ruang harus disembunyikan dari render (sudah di "
    "skrip uji); (5) batas model x -10..150, y -40..90 m: tebing dan sungai ikut, kamera 7.8 perlu dibingkai ulang.",
]


if __name__ == "__main__":
    h = hitung()
    CACHE.mkdir(parents=True, exist_ok=True)
    (CACHE / "hasil.pkl").write_bytes(pickle.dumps(h))
    buat_excel(h)
    tulis_md(h)
    print(h["fed"], h["waktu"], h["n_awal"], h["n_akhir"], "kritis terbuka:", h["kritis_buka"])
    for d in h["daftar"]:
        print(d["kode"], d["awal"], d["akhir"], d["status"])
