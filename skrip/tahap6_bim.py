"""Langkah 6.9: model BIMCraft LOD 300 pondasi (RSTB-STR-T6-LOD300) = model 5.7 + tiang bor Ø800 dan pile cap hasil Tahap 6.

DATA SIMULASI untuk studi kasus portofolio. Disusun AI atas permintaan Defsa (22 Nov 2026); disetujui atas delegasi Defsa 22 Nov 2026 (usulan AI: Cap E pelat h 2.000 mm, berat cap masuk 6.3).
Sumber (bukan angka ketik ulang):
  tata letak  tahap6_tata_letak.rancang("a") (62 cap, 230 tiang gedung utama; cache disk); utilitas 68 tiang dari Tahap 3 (tidak berubah);
  tebal cap   keputusan 6.7: cap kolom 2/3/4 tiang = 1.000/800/950 mm, cap inti 1.200, Cap E 1.800 (pelat, 6.7); muka cap +12,05;
  tiang       Ø800, fc' 35, 16 D25 + spiral D13 40/80, ujung -27,60, kepala = dasar cap + 0,15 m (tiang masuk cap 150 mm);
  Cap E       tulangan bawah D32 dari pelat 6.7 (tahap6_cap_pelat, Wood-Armer): As per meter x dan y, 2 lapis.
Jalankan: .venv\\Scripts\\python.exe skrip\\tahap6_bim.py [--bangun]
"""
from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree
from shapely.geometry import Point, box

sys.path.insert(0, str(Path(__file__).parent))
import tahap3_bim as t3  # noqa: E402
import tahap4_bim as t4  # noqa: E402
import tahap5_bim as t5  # noqa: E402
import tahap6_tata_letak as tl  # noqa: E402
import tahap6_struktur as ts6  # noqa: E402

AKAR = t4.AKAR
BIMC = AKAR / "model" / "RSTB-STR-T6-LOD300.bimc"
IFC = BIMC.with_suffix(".ifc")
KELUAR = AKAR / "06 Struktur Bawah dan Basement"
GAMBAR = KELUAR / "Gambar"
MD = KELUAR / "6.9 Model BIM Pondasi.md"
PNG = GAMBAR / "6.9 Model Pondasi 3D.png"
VERIFIKASI = AKAR / "VERIFIKASI.md"
CACHE = AKAR / "cache" / "tahap6_bim_besi.json"
STATUS = "disetujui atas delegasi Defsa 22 Nov 2026"
LABEL = "DATA SIMULASI untuk studi kasus portofolio. Bukan data proyek nyata. Tidak untuk konstruksi."
LT1 = 12.85
MUKA_CAP = 12.05
UJUNG = -27.60
MASUK = 0.15                      # m, tiang masuk cap
D = 0.80
AG = math.pi * D ** 2 / 4
TEBAL_N = tl.H_KOLOM                         # cap kolom per jumlah tiang (6.7, sama dengan berat cap 6.3)
TEBAL_INTI, TEBAL_E, TEBAL_GU = tl.H_INTI, ts6.H_E / 1e3, 1.200      # Cap E = pelat 6.7 (H_E)
TEPI = t3.TEPI_CAP                # 0,80 m
JARAK_MIN = 2.4
E_TOL = 0.010
SAMBUNG = 0.10                    # m, sloof masuk muka cap (SL-1 h 0,9 vs muka sloof +12,05) = sambungan, bukan clash
TOL = {"jumlah": 0, "volume": 0.01, "jarak": 0.001}    # T-107, ditetapkan sebelum dihitung: selisih jumlah 0, volume <= 1 %, jarak >= 2,4 m - 1 mm
BESI_TIANG = {"n": 16, "db": 25, "spiral": 13, "s_rapat": 40, "s_luar": 80, "cover": 75, "L_rapat": 2000}
BESI_E = {"db": 32, "lebar_x": 18.4, "lebar_y": 16.0}     # As dan jarak dihitung dari 6.7 (besi_e())
S_MIN = 65                         # mm, jarak minimum D32 satu lapis (jarak bersih 33 mm)


def idn(v, d=1):
    return f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ------------------------------------------------------------------ daftar unsur (tanpa BIMCraft)
def caps():
    """Semua cap: dict(id, jenis, h, pos, bbox, n, zona)."""
    ck, ci = tl.rancang("a")
    out = []
    for c in ck + ci:
        pos = [tuple(map(float, p)) for p in c["pos"]]
        xs, ys = [p[0] for p in pos], [p[1] for p in pos]
        n = len(pos)
        h = TEBAL_E if c["id"] == "Cap E" else TEBAL_INTI if c["jenis"] == "inti" else tl.tebal_cap(n)
        out.append(dict(id=c["id"], jenis=c["jenis"], n=n, h=h, pos=pos, tambah=c["tambah"], gedung="utama",
                        bbox=(min(xs) - TEPI, min(ys) - TEPI, max(xs) + TEPI, max(ys) + TEPI)))
    gu = [(x, y, n) for x, y, n, _ in t3.kelompok_tiang() if x >= t3.GU_X_MIN]
    for i, (x, y, n) in enumerate(gu):
        p, (w, d) = t3.pola(n)
        pos = [(x + a, y + b) for a, b in p]
        out.append(dict(id=f"GU-{i + 1}", jenis="utilitas", n=n, h=TEBAL_GU, pos=pos, tambah=0.0, gedung="utilitas",
                        bbox=(x - w / 2, y - d / 2, x + w / 2, y + d / 2)))
    return out


def tiang(daftar_cap=None):
    """Semua tiang: dict(x, y, cap, jenis, z0, z1, L)."""
    out = []
    for c in daftar_cap or caps():
        dasar = MUKA_CAP - c["h"]
        for x, y in c["pos"]:
            z1 = dasar + MASUK
            out.append(dict(x=x, y=y, cap=c["id"], jenis=c["jenis"], z0=UJUNG, z1=z1, L=z1 - UJUNG, gedung=c["gedung"]))
    return out


def rencana(daftar_cap=None):
    cs = daftar_cap or caps()
    ts = tiang(cs)
    return dict(n_tiang=len(ts), n_cap=len(cs), v_tiang=sum(AG * t["L"] for t in ts),
                v_cap=sum((c["bbox"][2] - c["bbox"][0]) * (c["bbox"][3] - c["bbox"][1]) * c["h"] for c in cs),
                n_utama=sum(1 for t in ts if t["gedung"] == "utama"), n_util=sum(1 for t in ts if t["gedung"] == "utilitas"))


def besi_e():
    """Kebutuhan tulangan bawah Cap E (pelat 6.7, Wood-Armer) dan jumlah lapis D32; model hanya satu lapis berjarak S_MIN."""
    import tahap6_cap_pelat as cp
    ce = next(c for c in caps() if c["id"] == "Cap E")
    pel = cp.semua(next(c for c in tl.rancang("a")[1] if c["kode"] == "E"), scan=False)["hasil"][ts6.H_E]
    a32 = math.pi * 16 ** 2
    w = ce["bbox"]
    ly, lx = (w[3] - w[1]), (w[2] - w[0])      # As x tersebar di lebar y; As y di lebar x
    out = {}
    for k, lb in (("x", ly), ("y", lx)):
        As = pel["lentur"][("bawah", k)]["As_maks"] * lb          # mm2/m maksimum x lebar (batas atas; per lajur lebih kecil)
        n = math.ceil(As / a32)
        per = int((lb * 1000 - 150) / S_MIN) + 1
        out[k] = dict(As=As, n=n, per_lapis=per, lapis=math.ceil(n / per), s_maks=(lb * 1000 - 150) / (n - 1), lebar=lb)
    out["rasio"] = dict(geser=pel["rasio"]["geser"], pons_tiang=pel["rasio"]["pons_tiang"], pons=pel["rasio"]["pons_inti"], stm=pel["rasio"]["stm"])
    return out


def _mm(x, y):
    return [round(x * 1000), round(y * 1000)]


# ------------------------------------------------------------------ bangun
def bangun():
    from bimcraft import Sesi, ke_v011

    cs = caps()
    ts = tiang(cs)
    ids = defaultdict(list)
    kunci_inti = {c["id"] for c in cs if c["jenis"] == "inti"}
    inti_ids, cap_ids = [], {}
    pe = next(c for c in cs if c["id"] == "Cap E")["pos"]
    xs, ys = [p[0] for p in pe], [p[1] for p in pe]
    sudut_e = {(x, y) for x in (min(xs), max(xs)) for y in (min(ys), max(ys))}   # tulangan 3D 4 tiang contoh: seluruh tiang cap inti (92 tiang sebelum penggabungan) = IFC 224 MB

    def idr(r):
        return [i for i in (r.get("ids") or [r.get("id")]) if isinstance(i, int)]

    with Sesi(t5.BIMC) as b:
        b.cmd("project_info", {"status": "Struktur Bawah - model LOD 300 pondasi (langkah 6.9), basis 5.7"})
        b.cmd("type", {"category": "structuralcolumn", "name": "TB-800-fc35", "width": 800, "depth": 800, "round": True, "material": "Beton fc 35 S2"})
        tipe = set()
        for c in cs:
            w, d = round((c["bbox"][2] - c["bbox"][0]) * 1000), round((c["bbox"][3] - c["bbox"][1]) * 1000)
            n = f"PC-{w}x{d}-h{round(c['h'] * 1000)}-fc35"
            if n not in tipe:
                b.cmd("type", {"category": "footing", "name": n, "width": w, "depth": d, "material": "Beton fc 35 S2"})
                tipe.add(n)
            cx, cy = (c["bbox"][0] + c["bbox"][2]) / 2, (c["bbox"][1] + c["bbox"][3]) / 2
            r = b.cmd("footing", {"at": _mm(cx, cy), "type": n, "thickness": round(c["h"] * 1000), "offset": round((MUKA_CAP - LT1) * 1000), "level": "LT1"})
            cap_ids[c["id"]] = idr(r)
            ids[("cap", c["jenis"])] += idr(r)
        for t in ts:
            r = b.cmd("structural_column", {"at": _mm(t["x"], t["y"]), "type": "TB-800-fc35", "level": "LT1",
                                            "base_offset": round((t["z0"] - LT1) * 1000), "height": round(t["L"] * 1000)})
            ids[("tiang", t["jenis"])] += idr(r)
            if t["cap"] == "Cap E" and (t["x"], t["y"]) in sudut_e:
                inti_ids += idr(r)
        ket = {("cap", "kolom"): "[cap] pile cap kolom 6.7 (tebal 1.000/800/950 mm untuk 2/3/4 tiang); fc' 35 MPa; tulangan bawah D32 dua lapis silang (6.7)",
               ("cap", "inti"): "[cap] pile cap inti 6.3/6.7, tebal 1.200 mm; fc' 35 MPa; Cap E lihat catatan tulangan",
               ("cap", "utilitas"): "[cap] pile cap gedung utilitas (Tahap 3, tidak diubah), tebal 1.200 mm",
               ("tiang", "kolom"): "[tiang] tiang bor Ø800 6.7, fc' 35, 16 D25 + spiral D13 40/80 sampai -17,76 (tulangan dipotong); ujung -27,60; kelas IFC IfcPile",
               ("tiang", "inti"): "[tiang] tiang bor Ø800 cap inti 6.7, tulangan penuh 16 D25 + spiral D13 40/80 (spiral rapat sampai -14,91); ujung -27,60; kelas IFC IfcPile",
               ("tiang", "utilitas"): "[tiang] tiang bor Ø800 gedung utilitas (Tahap 3 [Asumsi]); ujung -27,60; kelas IFC IfcPile"}
        for (k, jenis), idl in ids.items():
            b.cmd("modify", {"ids": idl, "params": {"RSTB_Tahap": "6", "RSTB_LOD": "300", "RSTB_Status": STATUS, "RSTB_KelasPaparan": "S2",
                                                    "RSTB_Mutu": "fc' 35 MPa; BjTS 420B", "RSTB_Paket": "tahap 1", "RSTB_Sumber": ket[(k, jenis)]}})
        besi = {}
        ok, gagal, cnt, kg, cat = 0, [], 0, 0.0, set()
        for h in inti_ids:
            try:
                r = b.cmd("reinforce", {"hosts": [h], "cover": BESI_TIANG["cover"], "grade": "BjTS 420B", "grade_stirrup": "BjTS 420B",
                                        "bars": {"diameter": BESI_TIANG["db"], "count": BESI_TIANG["n"]},
                                        "stirrup": {"diameter": BESI_TIANG["spiral"], "spacing": BESI_TIANG["s_luar"],
                                                    "ends": {"length": BESI_TIANG["L_rapat"], "spacing": BESI_TIANG["s_rapat"]}}})
                ok += 1
                cnt += r.get("count") or 0
                kg += r.get("weight_kg") or 0.0
                cat |= set(map(str, r.get("notes", [])))
            except Exception as e:                  # tulangan 3D tidak boleh menggagalkan model
                gagal.append(str(e)[-300:])
        besi["tiang_inti"] = {"hosts": ok, "count": cnt, "berat_kg": kg, "catatan": sorted(cat), "gagal": len(gagal), "galat": gagal[0] if gagal else ""}
        try:
            ce = next(c for c in cs if c["id"] == "Cap E")
            r = b.cmd("reinforce", {"hosts": cap_ids["Cap E"], "cover": 75, "grade": "BjTS 420B",
                                    "mesh": {"x": {"diameter": BESI_E["db"], "spacing": S_MIN}, "y": {"diameter": BESI_E["db"], "spacing": S_MIN}}})
            besi["cap_e"] = {"count": r.get("count"), "berat_kg": r.get("weight_kg"), "catatan": r.get("notes", [])}
        except Exception as e:
            besi["cap_e"] = {"galat": str(e)[:300]}
        b.simpan(BIMC)
        b.simpan(IFC)
        GAMBAR.mkdir(parents=True, exist_ok=True)
        try:
            b.cmd("camera", {"eye": [52000, -45000, -6000], "target": [45000, 40000, 2000], "lens": 22, "name": "Pondasi"})
            b.alat("render", {"view": "Pondasi", "path": str(PNG), "width": 1800, "height": 1100})
        except Exception as e:
            besi["render"] = str(e)[:200]
    ifc_pasca(IFC)
    ke_v011(IFC)
    return {"ids": {f"{k}-{j}": len(v) for (k, j), v in ids.items()}, "besi": besi}


def ifc_pasca(path=IFC):
    """BIMCraft belum punya kategori tiang: IfcColumn tipe TB-800 menjadi IfcPile BORED; IfcFooting menjadi PILE_CAP."""
    import ifcopenshell
    import ifcopenshell.api

    n = t3.ubah_kelas_tiang(path)
    f = ifcopenshell.open(str(path))
    for e in f.by_type("IfcFooting") + f.by_type("IfcFootingType"):
        e.PredefinedType = "PILE_CAP"
    f.write(str(path))
    return n


# ------------------------------------------------------------------ validasi IFC
def pusat_ifc(f):
    """Posisi (x, y, z) m dari penempatan IfcPile dan IfcFooting."""
    import ifcopenshell.util.placement as up
    out = {}
    for kelas in ("IfcPile", "IfcFooting"):
        out[kelas] = np.array([up.get_local_placement(e.ObjectPlacement)[:3, 3] for e in f.by_type(kelas)]) / 1000.0
    return out


def validasi(path=IFC):
    import ifcopenshell.util.element as ue

    t3m = t3
    v = t3m.validasi(path, wajib_lod=False)
    f = v["file"]
    cek = list(v["cek"])
    baru = [e for e in f.by_type("IfcElement") if t4._kelompok(e) in ("tiang", "cap")]
    tanpa = [e for e in baru if str(ue.get_psets(e)["Pset_RSTB_Umum"].get("RSTB_LOD")) != "300" or not ue.get_psets(e)["Pset_RSTB_Umum"].get("RSTB_Paket")]
    cek.append({"butir": "Pset_RSTB_Umum RSTB_LOD 300 + RSTB_Paket + RSTB_Mutu (tiang dan cap)", "lolos": not tanpa,
                "ket": f"{len(tanpa)} dari {len(baru)} unsur tidak lengkap"})
    rc = rencana()
    pus = pusat_ifc(f)
    n_p, n_c = len(f.by_type("IfcPile")), len(f.by_type("IfcFooting"))
    vol = t3m.volume_elemen(f)
    v_p = sum(vol.get(e.id(), (0.0, 0.0))[0] for e in f.by_type("IfcPile"))
    v_c = sum(vol.get(e.id(), (0.0, 0.0))[0] for e in f.by_type("IfcFooting"))
    pt = pus["IfcPile"][:, :2]
    d, _ = cKDTree(pt).query(pt, k=2)
    jarak = float(d[:, 1].min()) if len(pt) > 1 else float("nan")
    kelas = sum(1 for e in f.by_type("IfcPile") if e.PredefinedType == "BORED")
    cap_pc = sum(1 for e in f.by_type("IfcFooting") if e.PredefinedType == "PILE_CAP")
    cek.append({"butir": "Semua IfcPile BORED dan IfcFooting PILE_CAP", "lolos": kelas == n_p and cap_pc == n_c, "ket": f"{kelas}/{n_p} BORED; {cap_pc}/{n_c} PILE_CAP"})
    return dict(cek=cek, file=f, n_tiang=n_p, n_cap=n_c, v_tiang=v_p, v_cap=v_c, jarak_min=jarak, rencana=rc,
                d_n_tiang=n_p - rc["n_tiang"], d_n_cap=n_c - rc["n_cap"], d_v_tiang=v_p / rc["v_tiang"] - 1, d_v_cap=v_c / rc["v_cap"] - 1,
                lolos=all(c["lolos"] for c in cek), kelas=v["kelas"])


# ------------------------------------------------------------------ clash
def clash(cs=None):
    cs = cs or caps()
    ts = tiang(cs)
    daftar5 = t5.unsur()
    lain = [x for x in t5._bentuk(daftar5)]               # sloof, pit, stek: (nama, kel, poli, z0, z1)
    hasil = {k: [] for k in ("tiang_tiang", "tiang_cap_lain", "cap_cap", "cap_sloof", "cap_pit", "cap_stek", "tiang_lain")}
    hasil["sambungan"] = []
    pg = [Point(t["x"], t["y"]).buffer(D / 2, 32) for t in ts]
    pt = np.array([(t["x"], t["y"]) for t in ts])
    tree = cKDTree(pt)
    for i, j in tree.query_pairs(D - E_TOL):
        hasil["tiang_tiang"].append(f"{ts[i]['cap']} x {ts[j]['cap']}: jarak {np.hypot(*(pt[i] - pt[j])):.3f} m")
    cg = [box(*c["bbox"]) for c in cs]
    cz = [(MUKA_CAP - c["h"], MUKA_CAP) for c in cs]
    for i, t in enumerate(ts):
        for k, c in enumerate(cs):
            if t["cap"] == c["id"] or min(t["z1"], cz[k][1]) - max(t["z0"], cz[k][0]) <= E_TOL:
                continue
            if pg[i].buffer(-E_TOL).intersects(cg[k]):
                hasil["tiang_cap_lain"].append(f"tiang {t['cap']} ({t['x']:.2f};{t['y']:.2f}) x {c['id']}")
    for i in range(len(cs)):
        for j in range(i + 1, len(cs)):
            if cg[i].buffer(-E_TOL).intersects(cg[j].buffer(-E_TOL)):
                hasil["cap_cap"].append(f"{cs[i]['id']} x {cs[j]['id']}: {cg[i].intersection(cg[j]).area:.3f} m2")
    for nama, kel, g, z0, z1 in lain:
        for k, c in enumerate(cs):
            dz = min(z1, cz[k][1]) - max(z0, cz[k][0])
            if dz <= E_TOL:
                continue
            ov = g.buffer(-E_TOL).intersection(cg[k].buffer(-E_TOL)).area
            if ov <= 0:
                continue
            baris = f"{nama} x {c['id']}: {ov:.3f} m2 x {dz:.2f} m = {ov * dz:.3f} m3"
            if kel == "sloof" and dz <= SAMBUNG + E_TOL:
                hasil["sambungan"].append(baris)
            else:
                hasil["cap_" + kel].append(baris)
        for i, t in enumerate(ts):
            if min(z1, t["z1"]) - max(z0, t["z0"]) > E_TOL and g.buffer(-E_TOL).intersects(pg[i]):
                hasil["tiang_lain"].append(f"{nama} x tiang {t['cap']}")
    e = next(c for c in cs if c["id"] == "Cap E")
    ex0, ey0, ex1, ey1 = e["bbox"]
    luar = {}
    for n, kel, g, *_ in lain:
        if kel == "pit" and n.endswith("pelat"):
            x0, y0, x1, y1 = g.bounds
            luar[n.split()[1]] = dict(timur=round(x1 - ex1, 3), barat=round(ex0 - x0, 3), utara=round(y1 - ey1, 3), selatan=round(ey0 - y0, 3))
    hasil["pit_luar_e"] = {k: {a: b for a, b in v.items() if b > 1e-6} for k, v in luar.items()}
    return hasil


# ------------------------------------------------------------------ T-107
def catat_t107(v, cl, berkas=VERIFIKASI):
    rc = v["rencana"]
    lolos = (v["d_n_tiang"] == TOL["jumlah"] and v["d_n_cap"] == TOL["jumlah"] and abs(v["d_v_tiang"]) <= TOL["volume"]
             and abs(v["d_v_cap"]) <= TOL["volume"] and v["jarak_min"] >= JARAK_MIN - TOL["jarak"])
    baris = ("| T-107 | Cek silang 6.9 model BIM pondasi LOD 300 (IFC vs rencana 6.3/6.7): jumlah tiang dan pile cap, volume beton, jarak pusat tiang | "
             f"(a) jumlah IFC vs rencana: tiang {v['n_tiang']} vs {rc['n_tiang']} (selisih {v['d_n_tiang']}), cap {v['n_cap']} vs {rc['n_cap']} (selisih {v['d_n_cap']}); "
             f"(b) volume IFC vs rencana (π/4·0,8²·L dan Σ luas·tebal cap): tiang {idn(v['v_tiang'])} vs {idn(rc['v_tiang'])} m³ ({idn(v['d_v_tiang'] * 100, 3)} %), "
             f"cap {idn(v['v_cap'])} vs {idn(rc['v_cap'])} m³ ({idn(v['d_v_cap'] * 100, 3)} %); (c) jarak pusat tiang terkecil dari IFC {idn(v['jarak_min'], 3)} m | "
             "(a) selisih 0; (b) ≤ 1 %; (c) ≥ 2,4 m (tol. 1 mm) | "
             f"{'Lolos' if lolos else 'GAGAL'}, {STATUS} | `skrip/tahap6_bim.py`, `tests/test_tahap6_bim.py` | "
             "Ditetapkan sebelum membandingkan. Data simulasi. Rencana lama T-106 (volume IFC vs rencana) yang bergeser ke T-107; tiang masuk cap 0,15 m dihitung penuh di kedua sisi. "
             f"Temuan clash: cap vs pit {len(cl['cap_pit'])} pasang, cap vs sloof {len(cl['cap_sloof'])}, tiang vs tiang {len(cl['tiang_tiang'])}. |")
    teks = Path(berkas).read_text(encoding="utf-8").split("\n")
    teks = [ln for ln in teks if not ln.startswith("| T-107 |")]
    i = next(k for k, ln in enumerate(teks) if ln.startswith("| T-106 |"))
    teks.insert(i + 1, baris)
    Path(berkas).write_text("\n".join(teks), encoding="utf-8")
    return lolos


# ------------------------------------------------------------------ md
def tulis_md(v, rb, cl, lolos107):
    cs = caps()
    rc = v["rencana"]
    jenis = defaultdict(lambda: [0, 0])
    for c in cs:
        jenis[(c["jenis"], c["h"], c["n"] if c["jenis"] == "kolom" else 0)][0] += 1
        jenis[(c["jenis"], c["h"], c["n"] if c["jenis"] == "kolom" else 0)][1] += c["n"]
    be = rb["besi"]
    pe_ = cl["pit_luar_e"]
    o = ["# 6.9 Model BIM Pondasi LOD 300", "", f"STATUS: **{STATUS}**. {LABEL}", "",
         "Disusun AI 22 Nov 2026 (`skrip/tahap6_bim.py`, uji `tests/test_tahap6_bim.py`). Model: `model/RSTB-STR-T6-LOD300.bimc` dan `.ifc`; untuk jendela BIMCraft 0.11.0 "
         "pakai `model/RSTB-STR-T6-LOD300-v0.11.bimc`. Render: `Gambar/6.9 Model Pondasi 3D.png`.", "",
         "## Isi model", "",
         "Basis model 5.7 (`RSTB-STR-T5-LOD300`), ditambah semua tiang bor Ø800 dan pile cap hasil Tahap 6. Model utuh: struktur atas, sloof, pit, tangki opsi B, tiang, cap dalam satu berkas.", "",
         "| Kelompok | Cap | Tebal (mm) | Tiang |", "|---|---|---|---|"]
    for (j, h, n), (nc, nt) in sorted(jenis.items(), key=lambda a: (a[0][0], a[0][1], a[0][2])):
        o.append(f"| cap {j}{f' {n} tiang' if n else ''} | {nc} | {idn(h * 1000, 0)} | {nt} |")
    o += [f"| **jumlah** | **{rc['n_cap']}** | | **{rc['n_tiang']}** ({rc['n_utama']} gedung utama + {rc['n_util']} utilitas) |", "",
          f"- Tiang: Ø800 fc' 35, ujung {idn(UJUNG, 2)}, kepala = dasar cap + 0,15 m (masuk cap 150 mm), muka cap +{idn(MUKA_CAP, 2)}; panjang {idn(MUKA_CAP - TEBAL_E + MASUK - UJUNG, 2)} (Cap E), 38,60-38,80 (cap lain, bergantung tebal cap).",
          f"- Cap: kotak dari sumbu tiang terluar + 0,80 m (Tahap 3); 4,0 × 1,6 (2 tiang), 4,0 × 3,68 (3 tiang), 4,0 × 4,0 m (4 tiang). Cap E pelat h {idn(ts6.H_E, 0)} mm: dasar +{idn(MUKA_CAP - TEBAL_E, 2)}, kepala tiang +{idn(MUKA_CAP - TEBAL_E + MASUK, 2)}.",
          "- Gedung utilitas (68 tiang, 25 cap Tahap 3) tidak berubah dari Tahap 3 dan tidak punya struktur atas di model 5.7; dimodelkan hanya tiang dan cap (tebal 1.200).",
          "- IFC: tiang `IfcPile` BORED (BIMCraft belum punya kategori tiang; kolom bulat dengan tipe `TB-800-fc35` diubah ke `IfcPile` setelah ekspor lewat `ifcopenshell.api root.reassign_class`, pola 3.9); cap `IfcFooting` dengan PredefinedType PILE_CAP.",
          "- Pset_RSTB_Umum: LOD 300, status disetujui atas delegasi Defsa 22 Nov 2026, mutu fc' 35, kelas paparan S2, `RSTB_Sumber` diawali `[tiang]` atau `[cap]` memuat tulangan dan sumber.", "",
          "## Penulangan di model", ""]
    ti = be.get("tiang_inti", {})
    o.append("- Tiang contoh (4 tiang sudut Cap E; seluruh tiang cap inti penuh (92 tiang pada rancangan sebelum penggabungan) membuat IFC 224 MB dan BIMCraft 4,6 GB, tidak sanggup): " + (f"16 D25 + spiral D13-80 mm (zona rapat D13-40 mm hanya {BESI_TIANG['L_rapat']} mm di kepala dan ujung, "
             f"disederhanakan dari rencana 6.7 yang rapat sampai -14,91; alat `reinforce` hanya menerima zona rapat simetris), "
             f"{ti['hosts']} tiang berhasil, {idn(ti['count'], 0)} objek besi, {idn(ti['berat_kg'], 0)} kg" if ti.get("count") else f"tidak sanggup: {ti.get('galat') or ti}") + ".")
    ce = be.get("cap_e", {})
    be_e = besi_e()
    ex, ey = be_e["x"], be_e["y"]
    o.append(f"- Cap E gabungan (pelat h {idn(ts6.H_E, 0)}): jaring bawah D{BESI_E['db']} satu lapis jarak {S_MIN} mm kedua arah (jarak bersih {S_MIN - 32} mm). Kebutuhan 6.7 (pelat, As maksimum per meter × lebar; per lajur lebih kecil): "
             f"As x {idn(ex['As'], 0)} mm² = {ex['n']} batang di lebar {idn(ex['lebar'], 1)} m (jarak maksimum {idn(ex['s_maks'], 0)} mm, {ex['lapis']} lapis), "
             f"As y {idn(ey['As'], 0)} mm² = {ey['n']} batang di lebar {idn(ey['lebar'], 1)} m (jarak maksimum {idn(ey['s_maks'], 0)} mm, {ey['lapis']} lapis); "
             f"model hanya lapis pertama " + (f"({idn(ce['count'], 0)} batang, {idn(ce['berat_kg'], 0)} kg)." if ce.get("count") else f"(tidak sanggup: {ce.get('galat') or ce})."))
    o.append("- Tiang cap inti lainnya, tiang cap kolom (dipotong di -17,76 menurut 6.7) dan tulangan cap kolom: hanya properti teks di Pset (tidak dimodelkan 3D).")
    for kk in ("tiang_inti", "cap_e"):
        if be.get(kk, {}).get("catatan"):
            o.append(f"- Catatan BIMCraft {kk}: " + "; ".join(map(str, be[kk]["catatan"]))[:400])
    o += ["", "## Hasil cek (IFC)", "", "Validasi IFC (hierarki, Pset, GlobalId, kelas):", ""]
    o += [f"- {'Lolos' if c['lolos'] else 'GAGAL'}: {c['butir']} ({c['ket']})" for c in v["cek"]]
    o += ["", "T-107 (toleransi ditetapkan sebelum hitung: jumlah selisih 0; volume ≤ 1 %; jarak pusat ≥ 2,4 m):", "",
          "| Besaran | IFC | Rencana | Selisih |", "|---|---|---|---|",
          f"| jumlah tiang | {v['n_tiang']} | {rc['n_tiang']} | {v['d_n_tiang']} |",
          f"| jumlah cap | {v['n_cap']} | {rc['n_cap']} | {v['d_n_cap']} |",
          f"| volume tiang (m³) | {idn(v['v_tiang'])} | {idn(rc['v_tiang'])} | {idn(v['d_v_tiang'] * 100, 3)} % |",
          f"| volume cap (m³) | {idn(v['v_cap'])} | {idn(rc['v_cap'])} | {idn(v['d_v_cap'] * 100, 3)} % |",
          f"| jarak pusat tiang terkecil (m) | {idn(v['jarak_min'], 3)} | ≥ 2,4 | |", "",
          f"Hasil T-107: **{'Lolos' if lolos107 else 'GAGAL'}** (dicatat di `VERIFIKASI.md`). Rencana volume tiang = Σ π/4·0,8²·L dengan L dari ujung -27,60 ke kepala (termasuk 0,15 m masuk cap); "
          "rencana cap = Σ luas kotak × tebal; tumpang tiang-cap 0,15 m dihitung di kedua sisi (tidak dikurangkan).", "",
          "## Hasil clash (bidang denah dan tinggi, tumpang > 10 mm)", "", "| Cek | Hasil |", "|---|---|"]
    nama = {"tiang_tiang": "tiang vs tiang (tumpang badan)", "tiang_cap_lain": "tiang vs cap yang bukan pemiliknya", "cap_cap": "cap vs cap",
            "cap_sloof": "cap vs sloof (tumpang > 0,10 m)", "cap_pit": "cap vs pit lift", "cap_stek": "cap vs stek kolom dan dinding inti",
            "tiang_lain": "tiang vs sloof, pit, stek"}
    for k, nm in nama.items():
        o.append(f"| {nm} | {'tidak ada clash' if not cl[k] else str(len(cl[k])) + ' pasang: ' + '; '.join(cl[k][:4])} |")
    o += ["", f"Sambungan yang wajar dan tidak dihitung clash: sloof masuk muka cap ≤ 0,10 m ({len(cl['sambungan'])} pasang, SL-1 400 × 900 vs muka sloof +12,05) dan stek kolom/dinding "
          "yang berdiri di muka cap +12,05 (jarak 0).", "",
          "## Temuan", ""]
    n = 1
    cE = next(c for c in cs if c["id"] == "Cap E")
    rE = besi_e()["rasio"]
    ce_t = next(c for c in tl.rancang("a")[1] if c["kode"] == "E")
    sb, un = ce_t["sebelum"], ce_t["union"]
    o.append(f"{n}. **Cap C digabung ke Cap E** (keputusan Defsa 22 Nov 2026, 6.3 dan 6.7 direvisi): Cap E gabungan {ce_t['r']['n']} tiang, {idn(ce_t['ukuran'][0], 1)} × {idn(ce_t['ukuran'][1], 1)} m, "
             f"Pu maks {idn(ce_t['r']['Pu_maks'], 0)} kN (sebelum: Cap E {idn(sb['Cap E']['Pu_maks'], 0)}, Cap C {idn(sb['Cap C']['Pu_maks'], 0)}). "
             + (f"Gabungan polos {un['n']} tiang gagal tekan gempa (Pu maks {idn(un['Pu_maks'], 0)} kN > batas), sehingga tata letak dicari ulang: tiang gedung utama 244 menjadi 230 (total 312 menjadi 298). " if un else "")
             + f"Clash cap vs cap dan tiang vs cap lain: {len(cl['cap_cap'])} dan {len(cl['tiang_cap_lain'])} (sebelum penggabungan 1 dan 14).")
    n += 1
    o.append(f"{n}. **Cap E gabungan didesain sebagai pelat di atas tiang (keputusan Defsa 22 Nov 2026), h {idn(ts6.H_E, 0)} mm**: rasio geser satu arah {idn(rE['geser'], 3)}, pons tiang {idn(rE['pons_tiang'], 3)}, "
             f"pons inti {idn(rE['pons'], 3)}, STM lokal {idn(rE['stm'], 3)} (6.7 bagian 4; h 1.500 gagal geser 1,3).")
    n += 1
    if cl["cap_pit"]:
        o.append(f"{n}. **Pit lift berdiri di dalam beton Cap E** (dasar pit +10,80 di atas dasar cap +{idn(MUKA_CAP - TEBAL_E, 2)}, muka cap +12,05): L-1..4, L-5..6, dan L-7 menumpang Cap E ({len([x for x in cl['cap_pit'] if 'Cap E' in x])} pasang unsur), "
                 "ditambah tumpang kecil dengan cap kolom di dekatnya. Model tidak melubangi cap dan pit tidak diubah (arahan 6.9). Pelaksanaan: cap dilubangi (dasar pit tetap +10,80) atau pit dicor menyatu dengan cap; keputusan Defsa.")
        n += 1
    jor = [f"{k}: " + ", ".join(f"{a} {idn(b, 2)} m" for a, b in v.items()) for k, v in pe_.items() if v]
    bb = cE["bbox"]
    o.append(f"{n}. **Pit terhadap tepi Cap E** (tepi x {idn(bb[0], 1)}-{idn(bb[2], 1)}, y {idn(bb[1], 1)}-{idn(bb[3], 1)}): "
             + ("menjorok keluar: " + "; ".join(jor) + ". Bagian yang menjorok (dasar pit +10,80) tidak ditumpu cap; perlu ditumpu sloof/pelat LT1 atau cap diperlebar; pit dan Cap E tidak diubah di model ini."
                if jor else "semua pit L-1..4, L-5..6, L-7 berada di dalam telapak Cap E."))
    n += 1
    o.append(f"{n}. **Dampak ke 6.5, 6.6, 6.8**: sudah dihitung ulang pada rancangan 62 cap / 230 tiang gedung utama dan Cap E pelat h {idn(ts6.H_E, 0)} mm (lihat 6.5, 6.6, 6.8); model ini mengikuti tebal itu.")
    n += 1
    o.append(f"{n}. Tinggi kepala tiang mengikuti tebal cap (+11,20 untuk cap 1.000, +11,40 untuk cap 800, +11,25 untuk cap 950, +11,05 untuk cap 1.200, +{idn(MUKA_CAP - TEBAL_E + MASUK, 2)} Cap E); panjang tiang berbeda 38,30-38,80 m dengan ujung tetap -27,60.")
    n += 1
    o.append(f"{n}. Jarak pusat tiang terkecil di IFC {idn(v['jarak_min'], 3)} m (syarat ≥ 2,4 m 6.3); model 3.9 punya 30 pasang < 2,0 m, sudah diselesaikan di 6.3 dan model ini.")
    o += ["", "## Penyederhanaan model [Asumsi]", "",
          "- Spiral rapat D13-40 mm hanya 2.000 mm di kepala dan ujung (alat `reinforce` menerima zona rapat simetris); rencana 6.7 rapat sampai -14,91.",
          "- Cap E satu lapis jaring D32 (6.7: dua lapis silang); tulangan atas, tulangan samping, dan tulangan geser cap tidak dimodelkan.",
          "- Tiang cap kolom tanpa tulangan 3D (tulangan di properti teks); utilitas tanpa tulangan.", "",
          "## Keputusan Defsa", "", "Disetujui atas delegasi Defsa 22 Nov 2026 (usulan AI): Cap E gabungan 54 tiang 30,4 × 13,6 m, pelat h 2.000 mm tanpa tulangan pons; berat cap masuk 6.3. Temuan pit-Cap E (pit menumpang Cap E) tetap sebagai catatan pelaksanaan.", "",
          "## Langkah berikutnya", "", "6.10 gambar pondasi (denah tiang dan cap, potongan Cap E) dari model ini; render akhir Tahap 7.", ""]
    MD.write_text("\n".join(o), encoding="utf-8")
    return MD


def jalankan(bangun_dulu=False):
    if bangun_dulu:
        rb = bangun()
        CACHE.parent.mkdir(exist_ok=True)
        CACHE.write_text(json.dumps(rb, default=str), encoding="utf-8")
    else:
        rb = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {"ids": {}, "besi": {}}
    v = validasi()
    cl = clash()
    l107 = catat_t107(v, cl)
    tulis_md(v, rb, cl, l107)
    return v, cl, rb, l107


if __name__ == "__main__":
    v, cl, rb, l107 = jalankan("--bangun" in sys.argv)
    for c in v["cek"]:
        print(("OK  " if c["lolos"] else "GAL ") + c["butir"], "|", c["ket"])
    print({k: v[k] for k in ("n_tiang", "n_cap", "v_tiang", "v_cap", "jarak_min", "d_v_tiang", "d_v_cap")}, v["rencana"])
    print({k: len(x) if isinstance(x, list) else x for k, x in cl.items()}, "T-107", l107)
    print(rb)
