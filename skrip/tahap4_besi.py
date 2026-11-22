"""Langkah 4.10: model pembesian BIMCraft (LOD 350) dari model LOD 300 (4.9) dan hasil desain 4.5-4.8.

Arahan Defsa (20 Nov 2026): BIMCraft punya pembesian, jadi dipakai; gambar potongan dan penampang memperlihatkan besi.
Model LOD 300 yang sudah disetujui tidak diubah: besi ditambahkan ke salinan `model/RSTB-STR-T4-LOD350.bimc`.
Perintah BIMCraft:
  reinforce  balok (atas menerus = baris pertama tumpuan, bawah baris pertama, sengkang rapat 2h di ujung, tulangan
             samping), kolom (batang per sisi, sengkang rapat lo, ikat silang), pelat (mesh bawah/atas), tangga
             (pelat miring: tulangan mengikuti kemiringan);
  rebar      baris kedua tulangan (tumpuan atas sepanjang L/3 dari muka, bawah menerus) yang tidak dibuat reinforce.
Penyederhanaan model (gambar dan tabel tetap memakai angka desain): kaki sengkang dalam balok tidak dimodelkan; ikat
silang kolom di semua batang tengah; pelat lantai hanya mesh bawah tipikal P1 (BIMCraft membatasi 1.000 batang per
perintah; tulangan atas tumpuan dan panel lain lihat 4.5 Desain Pelat.xlsx, gambar pelat Tahap 7); pelat tangki S2 dan
tangga bermesh atas-bawah; dinding inti tidak dibesi di model (detail GS-15). Mutu baja ditulis BjTS 420B / BjTS 280.
DATA SIMULASI. Disusun AI atas permintaan Defsa (20 Nov 2026); disetujui Defsa 20 Nov 2026.
Jalankan: .venv\\Scripts\\python.exe skrip\\tahap4_besi.py
"""
from __future__ import annotations

import functools
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import tahap4_beban as tb  # noqa: E402
import tahap4_bim as bim  # noqa: E402

AKAR = Path(__file__).resolve().parents[1]
BIMC = AKAR / "model" / "RSTB-STR-T4-LOD350.bimc"
SEL_BALOK, SEL_PELAT = 40, 20          # mm, SNI 2847 Tabel 20.6.1.3.1 (4.6-4.8)
MUTU, MUTU_SENGKANG = "BjTS 420B", "BjTS 420B"
PELAT_TIPIKAL = {"bawah": (10, 175), "atas": (10, 150)}   # P1 bentang ujung/dalam terbesar (4.5) [penyederhanaan]
PELAT_ATAP = {"bawah": (13, 200), "atas": (10, 150)}      # atap helipad bawah D13-200 dua arah (4.5)


@functools.lru_cache(maxsize=1)
def desain():
    import tahap4_balok as bk
    import tahap4_dinding as td
    import tahap4_fasad as fs
    import tahap4_kolom as kl
    import tahap4_pelat as tp
    rb = bk.ringkasan()
    tepi = {x["kelompok"]: x for x in fs.cek_balok_tepi()}
    return {"balok": {x["kelompok"]: x for x in rb["kelompok"]}, "tangki": rb["tangki"], "chiller": rb["chiller"],
            "kolom": {x["kelompok"]: x for x in kl.rancang()["kelompok"]}, "tepi": tepi,
            "tangga": {h: td.tangga(h) for h in (4.2, 4.5)}, "pelat_tangki": tp.desain_tangki()}


def kelompok_balok(lv, p):
    """Kelompok desain balok dari level dan sumbu (mm); balok khusus LT3 atap V1 dikenali dari y."""
    import tahap4_gambar_ded as gd
    import tahap4_pelat as tp
    x1, y1, x2, y2 = (round(v / 1000, 3) for v in p)
    if lv == "LT3" and abs(y1 - y2) < 1e-6 and min(x1, x2) >= 60 - 1e-6 and max(x1, x2) <= 76 + 1e-6 and \
            abs(x2 - x1) > 8.5:
        return "anak tangki" if abs(y1 - tp.BALOK_ANAK_Y) < 0.01 else "rel chiller"
    return gd.kelompok_balok({"lv": lv, "p": (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))})


def param_balok(x, s_sendi=None, s_lap=None):
    """Parameter reinforce satu kelompok balok + baris kedua (dibuat dengan rebar)."""
    a, b_ = x["atas"], x["bawah"]
    n1a = a.get("n1", a["n"]) if a.get("lapis", 1) > 1 else a["n"]
    n1b = b_.get("n1", b_["n"]) if b_.get("lapis", 1) > 1 else b_["n"]
    s1 = round((s_sendi or x["s_sendi"]) * 1000)
    s2 = round((s_lap or x["s_lap"]) * 1000)
    prm = {"cover": SEL_BALOK, "grade": MUTU, "grade_stirrup": MUTU_SENGKANG,
           "top": {"count": n1a, "diameter": a["db"]}, "bottom": {"count": n1b, "diameter": b_["db"]},
           "stirrup": {"diameter": x["ds"], "spacing": s2, "ends": {"length": round(2 * x["h"] * 1000), "spacing": s1}}}
    if x["samping"]:
        prm["skin"] = {"diameter": 13, "spacing": round((x["h"] * 1000 - 2 * SEL_BALOK) / (x["samping"] + 1))}
    return prm, (a["n"] - n1a, a["db"]), (b_["n"] - n1b, b_["db"])


def _baris_kedua(b, host, axis, lv_z, h, bw, ds, n, db, atas, sepertiga):
    """Batang baris kedua (bersih 25 mm di bawah/atas baris pertama) di sepanjang sumbu balok (mm)."""
    if n <= 0:
        return 0
    (xa, ya, _), (xb, yb, _) = axis
    import math
    L = math.hypot(xb - xa, yb - ya)
    ux, uy = (xb - xa) / L, (yb - ya) / L
    nx, ny = -uy, ux
    c = SEL_BALOK + ds + db / 2
    z = -(c + db + 25) if atas else -(h - c - db - 25)
    lebar = bw - 2 * c
    jumlah = 0
    potong = [(0.0, L / 3), (L - L / 3, L)] if sepertiga else [(0.0, L)]
    for t0, t1 in potong:   # dari muka ke muka sumbu, dipotong selimut di kedua ujung
        p0 = (xa + ux * (t0 + SEL_BALOK), ya + uy * (t0 + SEL_BALOK))
        p1 = (xa + ux * (t1 - SEL_BALOK), ya + uy * (t1 - SEL_BALOK))
        o0 = -lebar / 2
        step = lebar / (n - 1) if n > 1 else 0.0
        if n == 1:
            o0 = 0.0
        r = b.cmd("rebar", {"points": [[p0[0] + nx * o0, p0[1] + ny * o0, z], [p1[0] + nx * o0, p1[1] + ny * o0, z]],
                            "diameter": db, "host": host, "grade": MUTU, "layer": "baris 2", "count": n,
                            "step": [nx * step, ny * step, 0.0]})
        jumlah += len(r.get("ids", []))
    return jumlah


def bangun(sumber=None):
    """Salin model LOD 300, tambahkan besi semua balok, kolom, pelat, dan tangga, simpan LOD 350. Kembalikan ringkasan."""
    from bimcraft import GalatBIM, Sesi
    import tahap4_kolom as kl
    d = desain()
    shutil.copy(sumber or bim.BIMC, BIMC)
    hasil = {"balok": 0, "kolom": 0, "pelat": 0, "tangga": 0, "baris2": 0, "berat_kg": 0.0, "catatan": [], "tanpa_besi": []}
    with Sesi(BIMC) as b:
        lev = {e["guid"]: e["name"] for e in b.alat("query_elements", {"category": "level", "limit": 50})["elements"]}
        lev.update({e["id"]: e["name"] for e in b.alat("query_elements", {"category": "level", "limit": 50})["elements"]})

        def tambah(r, kunci):
            hasil[kunci] += r.get("count", 0)
            hasil["berat_kg"] += r.get("weight_kg", 0.0)
            hasil["catatan"] += r.get("notes", [])

        # balok: dikelompokkan per kelompok desain lalu reinforce sekaligus (hosts)
        kel = {}
        for e in b.alat("query_elements", {"category": "beam", "limit": 2000})["elements"]:
            lv = lev[e["level"]]
            ax = e["axis"]
            kel.setdefault(kelompok_balok(lv, (ax[0][0], ax[0][1], ax[1][0], ax[1][1])), []).append(e)
        for nama, es in kel.items():
            x = d["tangki"] if nama == "anak tangki" else d["chiller"] if nama == "rel chiller" else d["balok"][nama]
            t = d["tepi"].get(nama)
            s1, s2 = t["s_baru"] if t and t["berubah"] else (None, None)
            prm, atas2, bawah2 = param_balok(x, s1, s2)
            ids = [e["id"] for e in es]
            for i in range(0, len(ids), 40):   # batas 20.000 batang per perintah
                tambah(b.cmd("reinforce", {"hosts": ids[i:i + 40], **prm}), "balok")
            for e in es:
                for (n, db), atas in ((atas2, True), (bawah2, False)):
                    hasil["baris2"] += _baris_kedua(b, e["id"], e["axis"], 0, x["h"] * 1000, x["b"] * 1000, x["ds"],
                                                    n, db, atas, sepertiga=atas)
        # kolom
        kel = {}
        for e in b.alat("query_elements", {"category": "structuralcolumn", "limit": 2000})["elements"]:
            if e.get("top_level") is None or e["width"] < 300:   # tumpuan dek helipad baja (HEB), bukan kolom beton
                continue
            atas_lv = lev[e["top_level"]]
            x, y = round(e["at"][0] / 1000, 3), round(e["at"][1] / 1000, 3)
            kel.setdefault(kl.kelompok_kolom(atas_lv, x, y, e["width"] / 1000), []).append(e["id"])
        for nama, ids in kel.items():
            x = d["kolom"][nama]
            g = x["geser"]
            prm = {"cover": SEL_BALOK, "grade": MUTU, "grade_stirrup": MUTU_SENGKANG,
                   "bars": {"diameter": x["db"], "x": x["m"], "y": x["m"]},
                   "stirrup": {"diameter": 13, "spacing": int(g["s_luar"]),
                               "ends": {"length": int(g["lo"]), "spacing": int(g["s_lo"])}},
                   "ties": {"diameter": 13}}
            for i in range(0, len(ids), 20):   # batas 20.000 batang per perintah
                tambah(b.cmd("reinforce", {"hosts": ids[i:i + 20], **prm}), "kolom")
        # pelat dan tangga
        pt = d["pelat_tangki"]
        for e in b.alat("query_elements", {"category": "floor", "limit": 2000})["elements"]:
            sumber_ = str(e.get("params", {}).get("RSTB_Sumber", ""))
            if "tangga" in sumber_:
                s = d["tangga"][4.5]
                prm = {"cover": SEL_PELAT, "grade": MUTU,
                       "bottom": {"x": {"diameter": 10, "spacing": 175}, "y": {"diameter": s["db"], "spacing": s["s_pos"]}},
                       "top": {"x": {"diameter": 10, "spacing": 175}, "y": {"diameter": s["db"], "spacing": s["s_neg"]}}}
                kunci = "tangga"
            elif "[pelat]" in sumber_ or "pelat" in sumber_:
                tebal = e.get("thickness") or 200
                if tebal >= 249:
                    prm = {"bottom": {"x": {"diameter": pt["positif"]["db"], "spacing": pt["positif"]["s"]},
                                      "y": {"diameter": pt["positif"]["db"], "spacing": pt["positif"]["s"]}},
                           "top": {"x": {"diameter": pt["negatif"]["db"], "spacing": pt["negatif"]["s"]},
                                   "y": {"diameter": pt["negatif"]["db"], "spacing": pt["negatif"]["s"]}}}
                else:
                    m = PELAT_ATAP if lev.get(e["level"]) == "ATAP" else PELAT_TIPIKAL
                    prm = {k: {"x": {"diameter": m[n][0], "spacing": m[n][1]}, "y": {"diameter": m[n][0], "spacing": m[n][1]}}
                           for k, n in (("bottom", "bawah"), ("top", "atas"))}
                if tebal < 249:   # batas 1.000 batang per perintah: pelat lantai hanya mesh bawah di model
                    prm.pop("top")
                prm.update({"cover": SEL_PELAT, "grade": MUTU})
                kunci = "pelat"
            else:
                continue
            try:
                tambah(b.cmd("reinforce", {"host": e["id"], **prm}), kunci)
            except GalatBIM as g:   # pelat lantai besar: > 1.000 batang per perintah BIMCraft
                if "1000 bars" not in str(g):
                    raise
                hasil["tanpa_besi"].append(f"{lev.get(e['level'])} pelat {e['id']}")
        b.cmd("project_info", {"status": "LOD 350 pembesian dari desain 4.5-4.8 (4.10, disetujui Defsa 20 Nov 2026)"})
        b.simpan(BIMC)
    hasil["MB"] = BIMC.stat().st_size / 1e6
    return hasil


if __name__ == "__main__":
    r = bangun()
    print({k: (round(v, 1) if isinstance(v, float) else v) for k, v in r.items() if k != "catatan"})
    print(sorted(set(r["catatan"]))[:20])
