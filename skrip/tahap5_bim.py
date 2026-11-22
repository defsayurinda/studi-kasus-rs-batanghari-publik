"""Langkah 5.7: model struktur BIMCraft LOD 300 struktur tengah (RSTB-STR-T5-LOD300) = model 4.9 + pelat LT1, sloof, pit lift,
stek ke pile cap, dan tangki opsi B (kolom 800, pelat 350, balok opsi B, besi kolom tangki).

DATA SIMULASI untuk studi kasus portofolio. Disusun AI atas permintaan Defsa (21 Nov 2026); disetujui Defsa 21 Nov 2026.
Sumber ukuran (bukan angka ketik ulang):
  dasar    tahap4_bim.unsur (4.9), unsur tangki opsi A diganti opsi B;
  pelat LT1  tahap5_pelat_lt1 (H 250, fc' 35, SH_LT1), tapak podium = pelat LT2 4.9;
  sloof    tahap5_penerusan.segmen_sloof + UKURAN_SLOOF (5.4/5.6); SL-1 as 6 di dalam inti lift dihapus (keputusan 5.6);
  pit      tahap5_pit_lift (GEOM, TW, ATAS, data_lift) dan tahap5_penerusan.T_PIT, BALOK_PG (5.5/5.6);
  tangki   tahap5_tangki.TANGKI_B/KOLOM, tahap5_kolom_tangki (B_ELEMEN, SEG; besi 5.6a), ukuran balok opsi B tabel 5.1;
  stek     tahap5_penerusan.HALAMAN (12,05).
Jalankan: .venv\\Scripts\\python.exe skrip\\tahap5_bim.py [--bangun]
"""
from __future__ import annotations

import subprocess
import sys
from collections import defaultdict
from pathlib import Path

from shapely.geometry import LineString, box
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).parent))
import tahap4_beban as tb  # noqa: E402
import tahap4_bim as t4  # noqa: E402
import tahap4_dinding as td  # noqa: E402
import tahap5_kolom_tangki as kt  # noqa: E402
import tahap5_pelat_lt1 as pl  # noqa: E402
import tahap5_penerusan as pe  # noqa: E402
import tahap5_pit_lift as pit  # noqa: E402
import tahap5_tangki as tn  # noqa: E402

AKAR = t4.AKAR
BIMC = AKAR / "model" / "RSTB-STR-T5-LOD300.bimc"
IFC = BIMC.with_suffix(".ifc")
KELUAR = AKAR / "05 Struktur Tengah"
GAMBAR = KELUAR / "Gambar"
MD = KELUAR / "5.7 Model BIMCraft.md"
STATUS = "disetujui Defsa 21 Nov 2026"
KEPUTUSAN = ("21 Nov 2026: model 5.7 disetujui dan di-merge, termasuk balok penggantung L-7 digeser 0,5 m ke muka luar dinding pit. "
             "Temuan untuk Tahap 6: di model fondasi LOD 200 Tahap 3 (`RSTB-STR-T3-LOD200`) ada 30 pasang tiang Ø800 berjarak pusat < 2,0 m "
             "(terdekat 0,83 m) di sekitar inti tangga/lift, karena cap inti dan cap kolom pradimensi diletakkan terpisah. "
             "Tahap 6 menggabungkan cap inti dengan cap kolom di dekatnya (sejalan keputusan 5.6) dan memeriksa jarak minimum tiang "
             "terhadap acuan; model 5.7 tidak memuat tiang.")
LABEL = "DATA SIMULASI untuk studi kasus portofolio. Bukan data proyek nyata. Tidak untuk konstruksi."
TOLERANSI_VOLUME = 0.05       # T-97, ditetapkan sebelum dihitung
E_TOL = 0.010                 # m, tumpang di bawah ini tidak dihitung clash
LT1 = tb.LEVEL["LT1"]
L = 8.0
KELOMPOK = ("kolom", "balok", "pelat", "sloof", "pit", "stek", "dinding", "tangga")
MUTU = {**t4.MUTU, "sloof": "fc' 35 MPa; BjTS 420B", "pit": "fc' 35 MPa; BjTS 420B", "stek": "fc' 35 MPa; BjTS 420B"}

# ukuran balok opsi B (tabel 5.1; kunci = tahap5_kolom_tangki.B_ELEMEN, None = kembali standar 4.6)
UKURAN_B = {"x 60": (0.40, 0.70), "x 68": (0.45, 0.80), "x 76 (standar)": None, "y 67 (x 60-68)": (0.40, 0.70),
            "y 67 (x 68-76, standar)": None, "y 75 (x 60-68)": (0.40, 0.70)}
# ukuran 4.6 yang dipakai 4.9 untuk balok di LT3 bay tangki (tahap4_balok.rancang()["ukuran_model"], 4.6 disetujui); rancang() ±80 s
UK_46 = {("LT3", 60.0, 67.0, 68.0, 67.0): (0.4, 0.7), ("LT3", 60.0, 67.0, 60.0, 75.0): (0.45, 0.8),
         ("LT3", 68.0, 67.0, 76.0, 67.0): (0.4, 0.7), ("LT3", 68.0, 67.0, 68.0, 75.0): (0.6, 1.2),
         ("LT3", 76.0, 67.0, 76.0, 75.0): (0.45, 0.8)}
UK_B = {("LT3", *p0, *p1): UKURAN_B[n] for n, (p, _) in kt.B_ELEMEN.items() if UKURAN_B[n] for p0, p1 in [p]}
KOLOM_B = set(map(tuple, tn.KOLOM))
B_TANGKI = box(tn.TANGKI_B["x"][0], tn.TANGKI_B["y"][0], tn.TANGKI_B["x"][1], tn.TANGKI_B["y"][1])
A_TANGKI = box(t4.tp.TANGKI["x"][0], t4.tp.TANGKI["y"][0], t4.tp.TANGKI["x"][1], t4.tp.TANGKI["y"][1])
T_TANGKI_B = 0.35             # tebal pelat tangki opsi B (5.1)
B_KOLOM_B = 0.80              # kolom tangki seragam (5.6a)
# besi kolom tangki (5.6a): (jumlah batang per sisi m, diameter, s_lo, s_luar); 20 D22 = 4(6-1), 32 D29 = 4(9-1)
BESI_TANGKI = {"LT2": {"n": 20, "m": 6, "db": 22, "s_lo": 125, "s_luar": 125, "lo": 800},
               "LT3": {"n": 32, "m": 9, "db": 29, "s_lo": 150, "s_luar": 150, "lo": 800}}
PIT_OFF = 0.30                # m, balok penggantung L-7 digeser ke muka luar dinding pit [Asumsi 5.7]


def _paket(lv):
    return t4.paket(lv)


# ------------------------------------------------------------------ daftar unsur (tanpa BIMCraft)
def unsur():
    out = []
    for u in t4.unsur(UK_B):
        if u.get("khusus") == "balok anak tangki":
            continue                                     # opsi B tanpa balok anak (5.1)
        if u["k"] == "pelat" and u["nama"] == "PL-250-tangki":
            continue                                     # diganti pelat 350 opsi B
        if u["k"] == "pelat" and u["lv"] == "LT3" and u["nama"] == "PL-200":
            lub = [o for o in u["lubang"] if not o.equals(A_TANGKI)] + [B_TANGKI]
            lif = t4.dalam_inti("Inti lif x50-58 y35-43")
            u = {**u, "lubang": lub, "vol": u["poli"].difference(unary_union(lub + [lif])).area * u["t"], "tahap": "5"}
        if u["k"] == "kolom" and u["lv"] in kt.SEG and (u["x"], u["y"]) in KOLOM_B:
            h = u["vol"] / u["b"] ** 2
            u = {**u, "b": B_KOLOM_B, "vol": B_KOLOM_B ** 2 * h, "tangki": True, "tahap": "5"}
        if u["k"] == "balok" and u["lv"] == "LT3" and u["p"] in {k[1:] for k in UK_B}:
            u = {**u, "opsiB": True, "tahap": "5"}
        out.append(u)
    out.append({"k": "pelat", "lv": "LT3", "poli": B_TANGKI, "lubang": [], "t": T_TANGKI_B, "offset": 0.0, "nama": "PL-350-tangki",
                "vol": B_TANGKI.area * T_TANGKI_B, "paket": "tahap 1", "tahap": "5"})
    out += _pelat_lt1() + _sloof() + _pit() + _stek()
    return out


def kolom_lt1():
    # kolom tangki opsi B 800 seragam (5.6a), bukan ukuran opsi A 950/800 dari 4.9
    return {(u["x"], u["y"]): B_KOLOM_B if (u["x"], u["y"]) in KOLOM_B else u["b"]
            for u in t4.unsur(UK_B) if u["k"] == "kolom" and u["lv"] == "LT2"}


def pelat_lt1_lubang(g):
    """Lubang pelat LT1: shaft SH yang tembus LT1, inti tangga di dalam tapak, pit lift (tepi dalam a × b)."""
    sh = [box(x0, y0, x1, y1) for kode, x0, x1, y0, y1, a, c in t4.SHAFT if kode in pl.SH_LT1 and a == "LT1"]
    tg = [o for o in (t4.dalam_inti(n) for n, _, _ in tb.INTI if n.startswith("Tangga")) if o.within(g)]
    lift = []
    for p in pit.data_lift().values():
        cx, cy = p["pusat"]
        lift.append(box(cx - p["a"] / 2, cy - p["b"] / 2, cx + p["a"] / 2, cy + p["b"] / 2))
    lub = sh + tg + lift
    for i, a in enumerate(lub):
        for b in lub[i + 1:]:
            assert a.intersection(b).area < 1e-9, "lubang pelat LT1 saling tumpang"
    return lub


def _pelat_lt1():
    g = [u for u in t4.unsur(UK_B) if u["k"] == "pelat" and u["lv"] == "LT2" and u["nama"] == "PL-200"][0]["poli"]
    lub = pelat_lt1_lubang(g)
    return [{"k": "pelat", "lv": "LT1", "poli": g, "lubang": lub, "t": pl.H, "offset": 0.0, "nama": "PL-250-LT1", "mutu": "fc' 35 MPa; BjTS 420B",
             "fc": 35, "vol": g.difference(unary_union(lub)).area * pl.H, "paket": "tahap 1", "tahap": "5", "lt1": True,
             "sumber": "5.3 pelat LT1 250 fc' 35 (zona baja tahan karat MRI x 79,5-81,5 / y 56-58 dalam pelat yang sama, tanpa lubang)"}]


def sloof_segmen():
    """Segmen sloof 5.4/5.6 tanpa yang berada di dalam kotak inti (keputusan 5.6) ditambah dua balok penggantung L-7."""
    ada = set(kolom_lt1())
    dalam = {(s["a"], s["b"]) for s in pe.sloof_di_inti(ada) if s["di_dalam"]}
    seg = [(a, b, t) for a, b, t in pe.segmen_sloof(ada) if (a, b) not in dalam]
    return seg, dalam


def _sloof():
    out = []
    seg, _ = sloof_segmen()
    for (x, y), (x2, y2), tipe in seg:
        b, h = pe.UKURAN_SLOOF[tipe]
        out.append({"k": "sloof", "lv": "LT1", "p": (x, y, x2, y2), "b": b, "h": h, "tipe": tipe, "vol": b * h * L, "paket": "tahap 1",
                    "tahap": "5", "sumber": f"5.4 sloof {tipe}, muka atas = muka atas pelat LT1"})
    p = pit.data_lift()["L-7"]
    cx, cy = p["pusat"]
    for s in (-1, 1):
        yc = cy + s * (p["b"] / 2 + pit.TW + pe.BALOK_PG[0] / 2)
        out.append({"k": "sloof", "lv": "LT1", "p": (36.0, yc, 44.0, yc), "b": pe.BALOK_PG[0], "h": pe.BALOK_PG[1], "tipe": "BP-L7",
                    "vol": pe.BALOK_PG[0] * pe.BALOK_PG[1] * L, "paket": "tahap 1", "tahap": "5",
                    "sumber": "5.5 balok penggantung pit L-7 (digeser ke muka luar dinding pit, 5.6 memakai tepi shaft) [Asumsi]"})
    return out


def pit_geom(kode, p):
    cx, cy = p["pusat"]
    luar = box(cx - p["a"] / 2 - pit.TW, cy - p["b"] / 2 - pit.TW, cx + p["a"] / 2 + pit.TW, cy + p["b"] / 2 + pit.TW)
    dalam = box(cx - p["a"] / 2, cy - p["b"] / 2, cx + p["a"] / 2, cy + p["b"] / 2)
    return luar, dalam


def _pit():
    out = []
    for kode, p in pit.data_lift().items():
        luar, dalam = pit_geom(kode, p)
        t = pe.T_PIT[kode]
        z0, z1 = p["dasar"], pit.ATAS
        out.append({"k": "pit", "lv": "LT1", "jenis": "pelat", "kode": kode, "poli": luar, "t": t, "offset": z0 - LT1, "z": (z0 - t, z0),
                    "vol": luar.area * t, "paket": "tahap 1", "tahap": "5", "sumber": f"5.5 pelat dasar pit {kode} t {t:.2f} m"})
        out.append({"k": "pit", "lv": "LT1", "jenis": "dinding", "kode": kode, "poli": luar, "dalam": dalam, "c": p["pusat"], "z": (z0, z1),
                    "vol": (luar.area - dalam.area) * (z1 - z0), "paket": "tahap 1", "tahap": "5",
                    "sumber": f"5.5 dinding pit {kode} tebal {pit.TW:.2f} m sampai sisi bawah pelat LT1 (+{pit.ATAS:.2f})"})
    return out


def _stek():
    out = []
    h = LT1 - pe.HALAMAN
    for (x, y), b in kolom_lt1().items():
        out.append({"k": "stek", "lv": "LT1", "jenis": "kolom", "x": x, "y": y, "b": b, "h": h, "vol": b * b * h, "paket": "tahap 1", "tahap": "5",
                    "sumber": f"5.6 stek kolom ke pile cap, muka atas cap +{pe.HALAMAN:.2f}"})
    for u in t4.unsur(UK_B):
        if u["k"] == "dinding" and u["lv"] == "LT2":
            (dx, dy) = u["d"]
            out.append({"k": "stek", "lv": "LT1", "jenis": "dinding", "c": u["c"], "d": u["d"], "h": h, "tipe": u["tipe"],
                        "vol": 2 * (dx + dy) * h * td.T, "paket": "tahap 1", "tahap": "5",
                        "sumber": f"5.6 stek dinding inti ke pile cap inti, muka atas cap +{pe.HALAMAN:.2f}"})
    return out


# ------------------------------------------------------------------ bangun di BIMCraft
mm, _poli_mm, lv_mm, bawah = t4.mm, t4._poli_mm, t4.lv_mm, t4.bawah


def bangun():
    from bimcraft import Sesi

    daftar = unsur()
    ids = defaultdict(list)
    tk_ids = defaultdict(list)

    def catat(kunci, r):
        if isinstance(r, dict):
            ids[kunci] += [i for i in (r.get("ids") or [r.get("id")]) if isinstance(i, int)]
        return r

    with Sesi(t4.TEMPLAT) as b:
        b.cmd("project_info", {"status": "Struktur Tengah - model struktur LOD 300 (langkah 5.7)"})
        for nama, ket in (("RSTB_Mutu", "Mutu beton dan tulangan atau baja"), ("RSTB_Paket", "Paket pelaksanaan: tahap 1 (K1) atau menyusul")):
            kat = ["wall", "floor", "column", "structuralcolumn", "beam", "footing", "roof", "stair", "railing", "room", "component"]
            b.cmd("parameter", {"name": nama, "kind": "text", "categories": kat, "sets": {k: "Pset_RSTB_Umum" for k in kat}, "description": ket})
        b.cmd("material", {"name": "Baja BJ 41", "color": "#5A6E82", "cut": "solid"})
        tipe = set()

        def tipe_kolom(bm):
            n = f"KL-{round(bm * 1000)}x{round(bm * 1000)}-fc35"
            if n not in tipe:
                b.cmd("type", {"category": "structuralcolumn", "name": n, "width": round(bm * 1000), "depth": round(bm * 1000),
                               "material": "Beton fc 35 S2"})
                tipe.add(n)
            return n

        def tipe_balok(bb, hb, fc=30, awal="BL"):
            n = f"{awal}-{round(bb * 1000)}x{round(hb * 1000)}-fc{fc}"
            if n not in tipe:
                b.cmd("type", {"category": "beam", "name": n, "width": round(bb * 1000), "depth": round(hb * 1000),
                               "material": f"Beton fc {fc} S2"})
                tipe.add(n)
            return n

        def tipe_pelat(t, awal="PL", fc=30):
            n = f"{awal}-{round(t * 1000)}-fc{fc}"
            if n not in tipe:
                b.cmd("type", {"category": "floor", "name": n, "layers": [
                    {"function": "structure", "material": f"Beton fc {fc} S2", "thickness": round(t * 1000)}]})
                tipe.add(n)
            return n

        def tipe_dinding(t, awal):
            n = f"{awal}-{round(t * 1000)}-fc35"
            if n not in tipe:
                b.cmd("type", {"category": "wall", "name": n, "layers": [
                    {"function": "structure", "material": "Beton fc 35 S2", "thickness": round(t * 1000)}]})
                tipe.add(n)
            return n

        dg = tipe_dinding(td.T, "DG")
        for k, pintu in td.PINTU.items():
            lb = pintu[0][1]
            b.cmd("type", {"category": "door", "name": f"PT-{k}-{round(lb * 1000)}x{round(td.H_PINTU * 1000)}",
                           "width": round(lb * 1000), "height": round(td.H_PINTU * 1000)})
        b.cmd("type", {"category": "structuralcolumn", "name": t4.DEK_PROFIL, "profile": t4.DEK_PROFIL, "material": "Baja BJ 41"})
        for i, x in enumerate(tb.GRID_X):
            b.cmd("grid", {"start": mm(x, tb.GRID_Y[0] - 6), "end": mm(x, tb.GRID_Y[-1] + 6), "name": str(i + 1)})
        for j, y in enumerate(tb.GRID_Y):
            b.cmd("grid", {"start": mm(tb.GRID_X[0] - 6, y), "end": mm(tb.GRID_X[-1] + 6, y), "name": t4.NAMA_Y[j]})

        for u in daftar:
            k, lv = u["k"], u["lv"]
            tahap = u.get("tahap", "4")
            if k == "kolom":
                tr = u.get("tangki")
                sumber = "5.6a kolom tangki opsi B 800 seragam (LT1-LT3)" if tr else "4.7 kolom SRPMK"
                r = b.cmd("structural_column", {"at": mm(u["x"], u["y"]), "type": tipe_kolom(u["b"]), "level": bawah(lv), "top_level": lv})
                catat((k, u["paket"], sumber, tahap, "kolom"), r)
                if tr:
                    tk_ids[lv] += [i for i in (r.get("ids") or [r.get("id")]) if isinstance(i, int)]
            elif k == "balok":
                x1, y1, x2, y2 = u["p"]
                if u.get("opsiB"):
                    sumber = "5.1 balok opsi B tangki"
                else:
                    sumber = "4.6 " + u.get("khusus", "balok SRPMK" if (u["b"], u["h"]) == (tb.BALOK_B, tb.BALOK_H) else "balok transfer tangki")
                catat((k, u["paket"], sumber, tahap, "balok"), b.cmd("beam", {"points": [mm(x1, y1), mm(x2, y2)], "type": tipe_balok(u["b"], u["h"]),
                                                                               "level": lv}))
            elif k == "pelat":
                fc = u.get("fc", 30)
                p = {"boundary": _poli_mm(u["poli"]), "level": lv, "type": tipe_pelat(u["t"], fc=fc), "structural": True}
                if u["lubang"]:
                    p["openings"] = [_poli_mm(o) for o in u["lubang"]]
                if u["offset"]:
                    p["offset"] = round(u["offset"] * 1000)
                sumber = u.get("sumber") or {"PL-350-tangki": "5.1 pelat tangki opsi B 350", "PL-200-LB1": "4.5 lantai turun CSSD LB-1 (300)"
                                             }.get(u["nama"], "4.5 pelat 200")
                catat((k, u["paket"], sumber, tahap, "pelat" if not u.get("lt1") else "pelat LT1"), b.cmd("floor", p))
            elif k == "dinding":
                (cx, cy), (dx, dy) = u["c"], u["d"]
                r = b.cmd("wall", {"points": [mm(cx - dx / 2, cy - dy / 2), mm(cx + dx / 2, cy - dy / 2), mm(cx + dx / 2, cy + dy / 2),
                                              mm(cx - dx / 2, cy + dy / 2)], "closed": True, "type": dg, "level": bawah(lv), "top_level": lv})
                catat((k, u["paket"], "4.8 dinding inti 350" + ("; " + t4.KOPEL_LIF if u["tipe"] == "L" else ""), tahap, "dinding"), r)
                for xp, lb in td.PINTU[u["tipe"]]:
                    b.cmd("door", {"at": mm(cx + xp, cy - dy / 2), "level": bawah(lv),
                                   "type": f"PT-{u['tipe']}-{round(lb * 1000)}x{round(td.H_PINTU * 1000)}"})
            elif k == "tangga":
                p = {"boundary": _poli_mm(u["poli"]), "level": lv, "type": tipe_pelat(u["t"], "TG"), "structural": True}
                if u["offset"]:
                    p["offset"] = round(u["offset"] * 1000)
                if u["slope"]:
                    p["slope"] = round(u["slope"], 3)
                    p["arrow"] = [mm(*u["arrow"][0]), mm(*u["arrow"][1])]
                catat((k, u["paket"], "4.8 tangga pelat 250 (bordes dan lengan)", tahap, "tangga"), b.cmd("floor", p))
            elif k == "dek":
                catat((k, u["paket"], "4.6 tumpuan dek helipad baja (tiang A / angkur B) [Asumsi profil]", tahap, "dek"),
                      b.cmd("structural_column", {"at": mm(u["x"], u["y"]), "type": t4.DEK_PROFIL, "level": "ATAP", "height": t4.DEK_TINGGI}))
            elif k == "sloof":
                x1, y1, x2, y2 = u["p"]
                catat((k, u["paket"], u["sumber"], tahap, "sloof"), b.cmd("beam", {
                    "points": [mm(x1, y1), mm(x2, y2)], "type": tipe_balok(u["b"], u["h"], 35, "SL" if u["tipe"] != "BP-L7" else "BP"), "level": "LT1"}))
            elif k == "pit":
                if u["jenis"] == "pelat":
                    r = b.cmd("floor", {"boundary": _poli_mm(u["poli"]), "level": "LT1", "type": tipe_pelat(u["t"], "PIT", 35),
                                        "structural": True, "offset": round(u["offset"] * 1000)})
                else:
                    cx, cy = u["c"]
                    a_, b_ = u["dalam"].bounds[2] - u["dalam"].bounds[0], u["dalam"].bounds[3] - u["dalam"].bounds[1]
                    xa, xb, ya, yb = cx - (a_ + pit.TW) / 2, cx + (a_ + pit.TW) / 2, cy - (b_ + pit.TW) / 2, cy + (b_ + pit.TW) / 2
                    r = b.cmd("wall", {"points": [mm(xa, ya), mm(xb, ya), mm(xb, yb), mm(xa, yb)], "closed": True, "type": tipe_dinding(pit.TW, "DP"),
                                       "level": "LT1", "base_offset": round((u["z"][0] - LT1) * 1000), "height": round((u["z"][1] - u["z"][0]) * 1000)})
                catat((k, u["paket"], u["sumber"], tahap, "pit"), r)
            elif k == "stek":
                if u["jenis"] == "kolom":
                    catat((k, u["paket"], u["sumber"], tahap, "stek"), b.cmd("structural_column", {
                        "at": mm(u["x"], u["y"]), "type": tipe_kolom(u["b"]), "level": "LT1", "base_offset": -round(u["h"] * 1000),
                        "height": round(u["h"] * 1000)}))
                else:
                    (cx, cy), (dx, dy) = u["c"], u["d"]
                    catat((k, u["paket"], u["sumber"], tahap, "stek"), b.cmd("wall", {
                        "points": [mm(cx - dx / 2, cy - dy / 2), mm(cx + dx / 2, cy - dy / 2), mm(cx + dx / 2, cy + dy / 2), mm(cx - dx / 2, cy + dy / 2)],
                        "closed": True, "type": dg, "level": "LT1", "base_offset": -round(u["h"] * 1000), "height": round(u["h"] * 1000)}))
        # shaft MEP dan ruang lif (seperti 4.9)
        for kode, x0, x1, y0, y1, a, c in t4.SHAFT:
            b.cmd("shaft", {"boundary": _poli_mm(box(x0, y0, x1, y1)), "level": a, "base_offset": 100, "height": lv_mm(c) - lv_mm(a)})
        lif = t4.dalam_inti("Inti lif x50-58 y35-43")
        b.cmd("shaft", {"boundary": _poli_mm(lif), "level": "LT1", "base_offset": 100, "height": lv_mm("LT6") - lv_mm("LT1")})
        for (k, pk, sumber, tahap, mk), daftar_id in ids.items():
            b.cmd("modify", {"ids": daftar_id, "params": {
                "RSTB_Tahap": tahap, "RSTB_LOD": "300", "RSTB_Status": STATUS if tahap == "5" else t4.STATUS, "RSTB_KelasPaparan": "-",
                "RSTB_Mutu": "fc' 35 MPa; BjTS 420B" if mk in ("pelat LT1", "sloof", "pit", "stek") else MUTU[k],
                "RSTB_Paket": pk, "RSTB_Sumber": f"[{k}] {sumber}"}})
        # besi enam kolom tangki (5.6a)
        besi = {}
        for lv, prm in BESI_TANGKI.items():
            r = b.cmd("reinforce", {"hosts": tk_ids[lv], "cover": 40, "grade": "BjTS 420B", "grade_stirrup": "BjTS 420B",
                                    "bars": {"diameter": prm["db"], "x": prm["m"], "y": prm["m"]},
                                    "stirrup": {"diameter": 13, "spacing": prm["s_luar"], "ends": {"length": prm["lo"], "spacing": prm["s_lo"]}},
                                    "ties": {"diameter": 13}})
            besi[lv] = {"hosts": len(tk_ids[lv]), "count": r.get("count"), "berat_kg": r.get("weight_kg"), "catatan": r.get("notes", [])}
        b.simpan(BIMC)
        b.simpan(IFC)
        GAMBAR.mkdir(parents=True, exist_ok=True)
        b.alat("render", {"view": "{3D}", "path": str(GAMBAR / "5.7 Model LOD 300 3D.png"), "width": 1600, "height": 1000})
        try:
            b.cmd("camera", {"eye": [76000, 100000, 19500], "target": [66000, 71000, 17500], "lens": 24, "name": "Zona Tangki"})
            b.alat("render", {"view": "Zona Tangki", "path": str(GAMBAR / "5.7 Zona Tangki dan LT1 dekat.png"), "width": 1600, "height": 1000})
        except Exception as e:      # render pendukung tidak boleh menggagalkan model
            besi["render_dekat"] = str(e)[:200]
    return {"ids": {k: len(v) for k, v in ids.items()}, "besi": besi}


# ------------------------------------------------------------------ validasi IFC
def validasi(path=IFC):
    """Cek hierarki, Pset, GlobalId (pola 3.9) dan volume IFC vs rencana per kelompok (T-97)."""
    import tahap3_bim as t3
    import ifcopenshell.util.element as ue

    v = t3.validasi(path, wajib_lod=False)
    f = v["file"]
    struktur = [e for e in f.by_type("IfcElement") if t4._kelompok(e)]
    cek = list(v["cek"])
    tanpa = [e for e in struktur if str(ue.get_psets(e)["Pset_RSTB_Umum"].get("RSTB_LOD")) != "300"
             or not ue.get_psets(e)["Pset_RSTB_Umum"].get("RSTB_Paket")]
    cek.append({"butir": "Pset_RSTB_Umum RSTB_LOD 300 + RSTB_Paket + RSTB_Mutu", "lolos": not tanpa,
                "ket": f"{len(tanpa)} dari {len(struktur)} unsur struktur tidak lengkap"})
    vol = t3.volume_elemen(f)
    ifc, jml = defaultdict(float), defaultdict(int)
    for e in struktur:
        kel = t4._kelompok(e)
        ifc[kel] += vol.get(e.id(), (0.0, 0.0))[0]
        jml[kel] += 1
    rencana = defaultdict(float)
    for u in unsur():
        rencana[u["k"]] += u["vol"]
    baris = [{"unsur": k, "n": jml[k], "ifc": ifc[k], "rencana": rencana[k], "selisih": ifc[k] / rencana[k] - 1} for k in KELOMPOK if rencana[k]]
    return {"cek": cek, "lolos": all(c["lolos"] for c in cek), "volume": baris, "kelas": v["kelas"], "file": f}


# ------------------------------------------------------------------ clash
def _bentuk(daftar):
    """[(nama, kelompok, poligon denah, z0, z1)] untuk sloof, pit, stek, pelat LT1."""
    out = []
    for u in daftar:
        if u["k"] == "sloof":
            x1, y1, x2, y2 = u["p"]
            out.append((f"{u['tipe']} ({x1:g};{y1:g})-({x2:g};{y2:g})", "sloof", LineString([(x1, y1), (x2, y2)]).buffer(u["b"] / 2, cap_style=2),
                        LT1 - u["h"], LT1))
        elif u["k"] == "pit":
            g = u["poli"] if u["jenis"] == "pelat" else u["poli"].difference(u["dalam"])
            out.append((f"pit {u['kode']} {u['jenis']}", "pit", g, u["z"][0] if "z" in u else 0, u["z"][1] if "z" in u else 0))
        elif u["k"] == "stek":
            if u["jenis"] == "kolom":
                g = box(u["x"] - u["b"] / 2, u["y"] - u["b"] / 2, u["x"] + u["b"] / 2, u["y"] + u["b"] / 2)
                nama = f"stek kolom ({u['x']:g};{u['y']:g})"
            else:
                (cx, cy), (dx, dy) = u["c"], u["d"]
                g = box(cx - dx / 2 - td.T / 2, cy - dy / 2 - td.T / 2, cx + dx / 2 + td.T / 2, cy + dy / 2 + td.T / 2).difference(
                    box(cx - dx / 2 + td.T / 2, cy - dy / 2 + td.T / 2, cx + dx / 2 - td.T / 2, cy + dy / 2 - td.T / 2))
                nama = f"stek dinding {u['tipe']} ({cx:g};{cy:g})"
            out.append((nama, "stek", g, LT1 - u["h"], LT1))
    return out


def clash(daftar=None, f=None):
    """Clash dasar: pit vs sloof/stek, shaft vs pelat LT1, zona MRI, kolom/pelat/balok tangki ganda, shaft MEP vs struktur (IFC)."""
    daftar = unsur() if daftar is None else daftar
    b = _bentuk(daftar)
    hasil = {"pit_sloof": [], "pit_stek": [], "shaft_lt1": [], "mri": [], "tangki": [], "shaft_ifc": []}
    pits = [x for x in b if x[1] == "pit"]
    for pn, _, pg, pz0, pz1 in pits:
        for sn, kel, sg, sz0, sz1 in b:
            if kel == "pit" or min(pz1, sz1) - max(pz0, sz0) <= E_TOL:
                continue
            ov = pg.buffer(-E_TOL).intersection(sg.buffer(-E_TOL)).area
            if ov > 0:
                hasil["pit_sloof" if kel == "sloof" else "pit_stek"].append(f"{pn} x {sn}: {ov:.3f} m2")
    lt1 = [u for u in daftar if u["k"] == "pelat" and u.get("lt1")][0]
    for kode, x0, x1, y0, y1, a, c in t4.SHAFT:
        if tb.LEVEL[a] <= LT1 + 1e-6 and not box(x0, y0, x1, y1).within(unary_union(lt1["lubang"]).buffer(1e-6)):
            hasil["shaft_lt1"].append(f"{kode} tembus LT1 tetapi tanpa lubang pelat LT1")
    sh_lt1 = [kode for kode, *_, a, c in t4.SHAFT if a == "LT1"]
    hasil["shaft_lt1_dicek"] = sh_lt1
    zona = box(pl.ZONA_TK[0], pl.ZONA_TK[2], pl.ZONA_TK[1], pl.ZONA_TK[3])
    for sn, kel, sg, *_ in b:
        if sg.buffer(-E_TOL).intersects(zona):
            hasil["mri"].append(f"zona MRI x {sn}")
    for kode, x0, x1, y0, y1, a, c in t4.SHAFT:
        if box(x0, y0, x1, y1).intersects(zona):
            hasil["mri"].append(f"zona MRI x {kode}")
    if any(o.intersects(zona) for o in lt1["lubang"]):
        hasil["mri"].append("zona MRI x lubang pelat LT1")
    kol = [(u["lv"], u["x"], u["y"], u["b"]) for u in daftar if u["k"] == "kolom" and u.get("tangki")]
    if len(kol) != 12 or len({k[:3] for k in kol}) != 12 or any(k[3] != B_KOLOM_B for k in kol):
        hasil["tangki"].append(f"kolom tangki {len(kol)} (harus 12 segmen unik, semua {B_KOLOM_B})")
    if [u for u in daftar if u["k"] in ("kolom", "stek") and u.get("b") == 0.95]:
        hasil["tangki"].append("masih ada kolom 950")
    tk = [u for u in daftar if u["k"] == "pelat" and u["lv"] == "LT3" and "tangki" in u["nama"]]
    if len(tk) != 1 or tk[0]["t"] != T_TANGKI_B:
        hasil["tangki"].append("pelat tangki harus tepat satu, tebal 350")
    for u in daftar:
        if u["k"] == "pelat" and u["lv"] == "LT3" and u["nama"] == "PL-200":
            if u["poli"].difference(unary_union(u["lubang"])).intersection(B_TANGKI).area > 1e-6:
                hasil["tangki"].append("PL-200 LT3 menumpang pelat tangki 350")
    if [u for u in daftar if u["k"] == "balok" and u.get("khusus") == "balok anak tangki"]:
        hasil["tangki"].append("balok anak tangki opsi A masih ada")
    if f is not None:
        hasil["shaft_ifc"] = [f"{c['shaft']} x {c['kelas']} {c['nama']} ({c['lantai']})" for c in t4.clash_shaft(f)]
    return hasil


# ------------------------------------------------------------------ md
def idn(v, d=1):
    return f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def info_cli():
    from bimcraft import CLI
    import json
    r = subprocess.run([str(CLI), "info", str(BIMC)], capture_output=True, text=True, encoding="utf-8")
    d = json.loads(r.stdout)
    return ([f"nama: {d['name']}; satuan: {d['units']}; peringatan: {len(d['warnings'])}",
             "level: " + ", ".join(f"{x['name']} {x['elevation'] / 1000:.2f}" for x in d["levels"])]
            + [f"{k}: {v}" for k, v in d["counts"].items()])


def tulis_md(v, ringkas_bangun, cl, info):
    daftar = unsur()
    kel = defaultdict(int)
    for u in daftar:
        kel[u["k"]] += 1
    seg, dalam = sloof_segmen()
    n_sl = sum(1 for u in daftar if u["k"] == "sloof" and u["tipe"] != "BP-L7")
    pt = {k: (idn(pe.T_PIT[k], 2)) for k in pe.T_PIT}
    o = ["# 5.7 Model BIMCraft LOD 300 Struktur Tengah", "",
         f"Status: **{STATUS}**. {LABEL}", "",
         "Disusun AI 21 Nov 2026 (`skrip/tahap5_bim.py`, uji `tests/test_tahap5_bim.py`). Model: `model/RSTB-STR-T5-LOD300.bimc` dan `.ifc`; "
         "untuk jendela BIMCraft 0.11.0 pakai `model/RSTB-STR-T5-LOD300-v0.11.bimc` (impor dari IFC).", "",
         "## Tujuan", "",
         "Menggabungkan hasil Tahap 5 ke model struktur 4.9: pelat LT1, sloof, pit lift, stek ke pile cap, dan tangki opsi B, sebagai model LOD 300 yang utuh, "
         "terlihat 3D, dan bisa diedit manual. Pile cap dan tiang tetap di model LOD 200 Tahap 3 (diperbarui Tahap 6).", "",
         "## Sumber per kelompok", "",
         "| Kelompok | Isi | Sumber |", "|---|---|---|",
         "| kolom, balok, dinding, tangga | semua unsur model 4.9, kecuali unsur tangki opsi A | `tahap4_bim.unsur` (4.5-4.8) |",
         f"| kolom tangki | enam kolom (x 60/68/76, y 67/75), segmen LT1-LT2 dan LT2-LT3, **{idn(B_KOLOM_B * 1000, 0)} × {idn(B_KOLOM_B * 1000, 0)}** seragam; tanpa kolom 950 | 5.6a (`tahap5_tangki.KOLOM`) |",
         f"| pelat tangki | **{idn(T_TANGKI_B * 1000, 0)} mm** di LT3 bay x 60-68 / y 67-75 (pelat 250 opsi A dan balok anak y 71 tidak dipakai; PL-200 LT3 berlubang di bay ini) | 5.1 |",
         "| balok bay tangki LT3 | x 68 450 × 800; x 60, y 67 dan y 75 (x 60-68) 400 × 700; x 76 dan y 67 (x 68-76) kembali standar 350 × 600 | tabel 5.1, `tahap5_kolom_tangki.B_ELEMEN` |",
         f"| pelat LT1 | +{idn(LT1, 2)}, tebal {idn(pl.H * 1000, 0)} mm, fc' 35, seluruh tapak podium; lubang: shaft SH-1, SH-2, SH-3, SH-5, SH-6, enam inti tangga, tiga pit lift (a × b); zona baja tahan karat MRI x 79,5-81,5 / y 56-58 ditandai di Pset (tanpa lubang) | 5.3 (`tahap5_pelat_lt1`) |",
         f"| sloof | {n_sl} segmen (SL-1 400 × 900, SL-2 dan SL-3 400 × 800), muka atas = muka atas pelat LT1, fc' 35; **SL-1 as 6 di dalam inti lift tidak ada** (keputusan 5.6: {len(dalam)} segmen dihapus) | 5.4, 5.6 (`segmen_sloof`) |",
         f"| pit lift | pelat dasar L-1..4 {pt['L-1..4']} m, L-5..6 {pt['L-5..6']} m, L-7 {pt['L-7']} m; dinding tebal {idn(pit.TW, 2)} m dari dasar pit sampai +{idn(pit.ATAS, 2)}; "
         f"L-7 digantung dua balok penggantung {idn(pe.BALOK_PG[0] * 1000, 0)} × {idn(pe.BALOK_PG[1] * 1000, 0)} ke sloof x 36 dan x 44 | 5.5 (`tahap5_pit_lift`, `T_PIT`, `BALOK_PG`) |",
         f"| stek | kolom LT1 dan dinding inti diperpanjang ke bawah sampai muka atas pile cap +{idn(pe.HALAMAN, 2)} (kolom pedestal dan dinding stek 0,80 m) | 5.6 (`HALAMAN`) |",
         "", "## Daftar unsur dan volume", "",
         f"Toleransi volume IFC terhadap rencana **{TOLERANSI_VOLUME:.0%}** (T-97, ditetapkan sebelum dihitung).", "",
         "| Kelompok | Jumlah (IFC) | Volume IFC (m³) | Rencana (m³) | Selisih |", "|---|---|---|---|---|"]
    o += [f"| {b['unsur']} | {b['n']} | {idn(b['ifc'])} | {idn(b['rencana'])} | {idn(b['selisih'] * 100, 2)} % |" for b in v["volume"]]
    o += ["", "Validasi IFC (hierarki, Pset, GlobalId):", ""]
    o += [f"- {'Lolos' if c['lolos'] else 'GAGAL'}: {c['butir']} ({c['ket']})" for c in v["cek"]]
    o += ["", "## Penulangan enam kolom tangki (5.6a)", "",
          "| Segmen | Jumlah kolom | Batang | Susunan model | Sengkang | Mutu |", "|---|---|---|---|---|---|"]
    for lv, pr in BESI_TANGKI.items():
        seg_n = "LT1-LT2" if lv == "LT2" else "LT2-LT3"
        o.append(f"| {seg_n} | {ringkas_bangun['besi'][lv]['hosts']} | {pr['n']} D{pr['db']} | {pr['m']} batang per sisi (4 × {pr['m'] - 1} = {pr['n']}) | "
                 f"D13-{pr['s_lo']} di lo {pr['lo']} mm, D13-{pr['s_luar']} di luar lo; ikat silang D13 | BjTS 420B |")
    bs = ringkas_bangun["besi"]
    if all(bs[lv].get("berat_kg") for lv in BESI_TANGKI):
        o += ["", "Model: " + "; ".join(f"segmen {lv}: {idn(bs[lv]['count'], 0)} batang, {idn(bs[lv]['berat_kg'], 0)} kg" for lv in BESI_TANGKI) + " (keluaran `reinforce`)."]
    o += ["", "Susunan 20 D22 dan 32 D29 persis sama dengan 5.6a (tidak perlu pembagian per sisi terdekat). Berat besi dan catatan BIMCraft ada di berkas model.", "",
          "## Hasil clash dasar", "",
          "| Cek | Hasil |", "|---|---|"]
    nama = {"pit_sloof": "pit lift vs sloof dan balok penggantung (tumpang bidang denah dan tinggi > 10 mm)",
            "pit_stek": "pit lift vs stek kolom dan dinding inti",
            "shaft_lt1": f"shaft MEP yang tembus LT1 ({', '.join(cl['shaft_lt1_dicek'])}) punya lubang di pelat LT1",
            "mri": "zona baja tahan karat MRI vs sloof, shaft, lubang pelat",
            "tangki": "kolom 800, pelat 350, balok opsi B tidak ganda (kolom 950, pelat 250, balok anak y 71 tidak ada)",
            "shaft_ifc": "shaft MEP vs unsur struktur (kotak batas IFC, `tahap4_bim.clash_shaft`)"}
    for kk, nm in nama.items():
        o.append(f"| {nm} | {'tidak ada clash' if not cl[kk] else '; '.join(cl[kk][:6])} |")
    o += ["", "Sambungan yang wajar dan tidak dihitung clash: balok penggantung L-7 menempel muka luar dinding pit (jarak 0), sloof as C (y 43) menempel pit L-5..6 (jarak 0,1 m), "
              "dan sloof-kolom-stek di titik kolom (unsur beton monolit; model memakai sumbu ke sumbu seperti 4.9).", "",
          "## Ringkasan `bimcraft-cli info`", "", "```"] + info[:40] + ["```", "",
          "## Penyederhanaan model [Asumsi]", "",
          "- Pelat LT1 satu pelat berlubang; zona MRI hanya ditandai di Pset `RSTB_Sumber` (baja tahan karat belum dimodelkan terpisah).",
          "- Pit L-1..4 satu pit 5,2 × 6,2 m (empat shaft lift menjadi satu bak); lift L-5..6 dan L-7 tidak dimodelkan di atas LT1 (hanya pit dan lubang pelat LT1).",
          f"- Balok penggantung L-7 digeser {idn(pit.TW + pe.BALOK_PG[0] / 2, 2)} m keluar dari tepi shaft ke muka luar dinding pit supaya tidak menumpang dinding (5.6 menghitung beban di tepi shaft; selisih 0,5 m tidak mengubah sloof penerima karena beban dibagi ke sloof x 36 dan x 44).",
          "- Stek kolom dan dinding inti berupa segmen beton polos dari +12,05 ke +12,85; tulangan stek mengikuti 5.6 dan tidak dimodelkan; besi hanya enam kolom tangki.",
          "- Momen balok opsi B memakai ukuran tabel 5.1 (balok dan pelat tangki 350); analisis ulang model 3D tidak dilakukan (catatan 5.6a).",
          "- Pile cap, tiang, dan zona MRI baja tahan karat di model LOD 200 Tahap 3 / Tahap 6; lift L-5..6 dan L-7 di atas LT1 mengikuti arsitektur.",
          "", "## Keputusan Defsa", "", KEPUTUSAN, "",
          "## Langkah berikutnya", "",
          "5.8 gambar CADCraft (denah pelat LT1, sloof, pit, tangki opsi B) dari model ini; render akhir di Tahap 7.", ""]
    MD.write_text("\n".join(o), encoding="utf-8")
    return MD


def jalankan(bangun_dulu=False):
    from bimcraft import ke_v011
    ringkas = bangun() if bangun_dulu else None
    if ringkas is None:
        ringkas = {"besi": {lv: {"hosts": 6} for lv in BESI_TANGKI}}
    v = validasi()
    cl = clash(f=v["file"])
    info = info_cli()
    ke_v011(IFC)
    tulis_md(v, ringkas, cl, info)
    return v, cl, ringkas


if __name__ == "__main__":
    v, cl, rb = jalankan("--bangun" in sys.argv)
    for c in v["cek"]:
        print(("OK  " if c["lolos"] else "GAL ") + c["butir"], "|", c["ket"])
    for b in v["volume"]:
        print(f"{b['unsur']:8s} n {b['n']:4d} IFC {b['ifc']:9.1f}  rencana {b['rencana']:9.1f}  {b['selisih']:+.2%}")
    print("clash", {k: x for k, x in cl.items() if x})
    print(rb)
