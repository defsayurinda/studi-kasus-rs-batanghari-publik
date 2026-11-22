"""Langkah 4.9: model struktur BIMCraft LOD 300 (RSTB-STR-T4-LOD300) dari ukuran final desain 4.5-4.8, validasi IFC,
clash dasar dengan shaft MEP, dan 3 varian fasad (Defsa memilih).

Sumber ukuran (bukan angka ketik ulang):
  pelat  tahap4_pelat (PANEL 200 mm; TANGKI 250 mm), wilayah lantai tahap4_beban.tingkat("K2");
  balok  tahap4_balok.rancang()["ukuran_model"] (transfer tangki), balok anak tangki dan rel chiller (Balok Khusus 4.6);
  kolom  tahap4_beban.KOLOM_POD/MEN dan tahap4_kolom.UKURAN_KOLOM (transfer 950/800 LT1-LT3);
  inti   tahap4_dinding (T 350, DIM, PINTU, H_PINTU) dan tahap4_beban.INTI (puncak tiap inti);
  tangga tahap4_dinding.tangga(h) (pelat 250, lebar lengan, bordes);
  shaft  Data Owner/Data Beban MEP Rinci.xlsx lembar Shaft dan Lubang (koordinat di SHAFT di bawah).
Paket: `tahap 1` = konfigurasi K1 (podium + menara s.d. kolom/inti LT5 di bawah atap sementara), `menyusul` = sisa K2.
Fondasi tetap di model LOD 200 (Tahap 6). Disusun AI atas permintaan Defsa (20 Nov 2026).
"""
import math
from collections import defaultdict
from pathlib import Path

from shapely.geometry import Point, box
from shapely.ops import unary_union

import tahap4_beban as tb
import tahap4_dinding as td
import tahap4_kolom as kl
import tahap4_pelat as tp

AKAR = Path(__file__).resolve().parents[1]
BIMC = AKAR / "model" / "RSTB-STR-T4-LOD300.bimc"
IFC = BIMC.with_suffix(".ifc")
TEMPLAT = AKAR / "model" / "RSTB-TPL-Template.bimc"
GAMBAR = AKAR / "04 Struktur Atas" / "Gambar"
STATUS = "disetujui Defsa 20 Nov 2026 (SH-4 digeser, fasad V3, void LT3 dihapus)"
TOLERANSI_VOLUME = 0.05      # T-84, ditetapkan sebelum dihitung
URUT = tb.URUT
NAMA_Y = "ABCDEFG"
TEPI_PELAT = 0.175           # m, tepi pelat rata muka luar balok tepi 350 [Asumsi detail]
TAHAP1 = {"LT2", "LT3", "LT4", "LT5"}      # tingkat (ujung atas segmen) yang masuk K1
PUSAT = {**{f"Tangga x{x} y{y}": (x, y) for x in (22, 46, 70) for y in (39, 63)}, "Inti lif x50-58 y35-43": (54, 39)}
KOPEL_LIF = "dinding di atas pintu lif = balok kopel diagonal 4.8"

# Data Beban MEP Rinci, lembar Shaft dan Lubang (SH-4 digeser dari x 59,0-61,4 y 41,8-44,2 karena menabrak kolom 7/C, disetujui Defsa 20 Nov 2026): (kode, x0, x1, y0, y1, tingkat bawah, tingkat atas yang ditembus)
SHAFT = [("SH-1", 25.0, 27.0, 36.6, 37.8, "LT1", "ATAP"), ("SH-2", 41.0, 43.4, 44.6, 46.2, "LT1", "ATAP"),
         ("SH-3", 64.6, 66.2, 44.4, 45.6, "LT1", "ATAP"), ("SH-4", 60.6, 63.0, 43.6, 46.0, "LT2", "LT3"),
         ("SH-5", 29.0, 31.0, 60.6, 61.8, "LT1", "LT4"), ("SH-6", 82.1, 82.7, 54.7, 55.3, "LT1", "LT3"),
         ("SH-7", 72.6, 74.4, 52.2, 53.2, "LT2", "LT3"), ("LB-2", 58.0, 58.8, 69.0, 69.8, "LT2", "LT3")]
LB1 = (70.0, 76.0, 52.0, 56.0, 0.300)      # lantai turun CSSD di pelat LT2
# chiller 4 unit 11,0 × 2,3 m di y 52,9-65,7 (Daftar Alat M-01); 2 rel per unit, 0,6 m dari tepi [Asumsi tata letak;
# 0,4 m menyentuh SH-7 y 52,2-53,2 pada cek clash 4.9]
CHILLER_Y0 = [52.9 + i * 3.5 for i in range(4)]
REL_Y = [round(y0 + d, 2) for y0 in CHILLER_Y0 for d in (0.6, 1.7)]
REL = (0.30, 0.50)
ANAK_TANGKI = (0.50, 0.90)
# tumpuan dek helipad baja (4.6 dek_helipad): tiang A di balok tepi y 27/51, angkur B 8 m ke dalam, jarak 4 m
DEK_X = [36.0 + 4.0 * i for i in range(9)]
DEK_Y = [27.0, 35.0, 43.0, 51.0]
DEK_PROFIL, DEK_TINGGI = "HEB 200", 600     # [Asumsi; desain dek baja menyusul]
MUTU = {"kolom": "fc' 35 MPa; BjTS 420B", "dinding": "fc' 35 MPa; BjTS 420B", "balok": "fc' 30 MPa; BjTS 420B",
        "pelat": "fc' 30 MPa; BjTS 420B", "tangga": "fc' 30 MPa; BjTS 420B", "dek": "baja BJ 41 [Asumsi]"}


def mm(x, y):
    return [round(x * 1000), round(y * 1000)]


def lv_mm(lv):
    return round(tb.LEVEL[lv] * 1000)


def bawah(lv):
    return URUT[URUT.index(lv) - 1]


def paket(lv):
    return "tahap 1" if lv in TAHAP1 else "menyusul"


def puncak_inti(nama):
    return {n: p for n, _, p in tb.INTI}[nama]


def dalam_inti(nama):
    """Persegi muka dalam inti (m)."""
    cx, cy = PUSAT[nama]
    dx, dy = td.DIM["L" if nama.startswith("Inti") else "T"]
    return box(cx - dx / 2 + td.T / 2, cy - dy / 2 + td.T / 2, cx + dx / 2 - td.T / 2, cy + dy / 2 - td.T / 2)


# ------------------------------------------------------------------ daftar unsur (tanpa BIMCraft: dipakai uji juga)
def ukuran_balok():
    import tahap4_balok as tbk
    return dict(tbk.rancang()["ukuran_model"])


def unsur(uk_balok=None):
    """Semua unsur struktur dengan ukuran dan volume rencana (m³) dari dimensi desain."""
    uk_balok = ukuran_balok() if uk_balok is None else uk_balok
    out = []
    puncak_kolom = defaultdict(set)
    for t in tb.tingkat("K2"):
        lv = t["lv"]
        h = tb.LEVEL[lv] - tb.LEVEL[bawah(lv)]
        wil_b, uk0 = t["kolom_bawah"]
        for x, y in tb.titik_kolom(wil_b):
            b = kl.UKURAN_KOLOM.get((lv, x, y), uk0)
            puncak_kolom[lv].add((x, y))
            out.append({"k": "kolom", "lv": lv, "x": x, "y": y, "b": b, "vol": b * b * h, "paket": paket(lv)})
        wil = unary_union([g for g in (t.get("lantai"), t.get("atap")) if g is not None])
        for x, y in puncak_kolom[lv]:
            for dx, dy in ((8.0, 0.0), (0.0, 8.0)):
                x2, y2 = x + dx, y + dy
                if (x2, y2) in puncak_kolom[lv] and wil.buffer(0.01).contains(Point(x + dx / 2, y + dy / 2)):
                    b, hb = uk_balok.get((lv, x, y, x2, y2), (tb.BALOK_B, tb.BALOK_H))
                    out.append({"k": "balok", "lv": lv, "p": (x, y, x2, y2), "b": b, "h": hb, "vol": b * hb * 8.0,
                                "paket": paket(lv) if lv != "LT5" else "menyusul"})
    for y in [tp.BALOK_ANAK_Y] + REL_Y:
        b, hb = ANAK_TANGKI if y == tp.BALOK_ANAK_Y else REL
        out.append({"k": "balok", "lv": "LT3", "p": (60.0, y, 76.0, y), "b": b, "h": hb, "vol": b * hb * 16.0,
                    "paket": "tahap 1", "khusus": "balok anak tangki" if y == tp.BALOK_ANAK_Y else "rel chiller"})
    out += pelat()
    out += inti()
    out += tangga()
    for x in DEK_X:
        for y in DEK_Y:
            out.append({"k": "dek", "lv": "ATAP", "x": x, "y": y, "vol": 0.0, "paket": "menyusul"})
    return out


def _bukaan_tangga(lv):
    """Lubang tangga di pelat tingkat lv (inti masih menerus di atasnya)."""
    return [dalam_inti(n) for n, _, p in tb.INTI if n.startswith("Tangga") and tb.LEVEL[p] > tb.LEVEL[lv] + 1e-6]


def pelat():
    out = []
    tangki = box(tp.TANGKI["x"][0], tp.TANGKI["y"][0], tp.TANGKI["x"][1], tp.TANGKI["y"][1])
    lb1 = box(LB1[0], LB1[2], LB1[1], LB1[3])
    for t in tb.tingkat("K2"):
        lv = t["lv"]
        g = unary_union([x for x in (t.get("lantai"), t.get("atap")) if x is not None])
        if g.is_empty:
            continue
        g = g.buffer(TEPI_PELAT, join_style=2)
        lubang = [o for o in _bukaan_tangga(lv) if o.within(g)]
        if lv == "LT3":
            lubang.append(tangki)
            out.append({"k": "pelat", "lv": lv, "poli": tangki, "lubang": [], "t": tp.H_TANGKI, "offset": 0.0,
                        "nama": "PL-250-tangki", "vol": tangki.area * tp.H_TANGKI, "paket": "tahap 1"})
        if lv == "LT2":
            lubang.append(lb1)
            out.append({"k": "pelat", "lv": lv, "poli": lb1, "lubang": [], "t": tp.H, "offset": -LB1[4],
                        "nama": "PL-200-LB1", "vol": lb1.area * tp.H, "paket": "tahap 1"})
        # lif dilubangi perintah shaft; volume rencana dikurangi di sini
        lif = dalam_inti("Inti lif x50-58 y35-43") if lv != "ATAP" else None
        bersih = g.difference(unary_union(lubang + ([lif] if lif is not None else [])))
        out.append({"k": "pelat", "lv": lv, "poli": g, "lubang": lubang, "t": tp.H, "offset": 0.0, "nama": "PL-200",
                    "vol": bersih.area * tp.H, "paket": "tahap 1" if lv in ("LT2", "LT3", "LT4") else "menyusul"})
    return out


def inti():
    out = []
    for nama, _, puncak in tb.INTI:
        cx, cy = PUSAT[nama]
        tipe = "L" if nama.startswith("Inti") else "T"
        dx, dy = td.DIM[tipe]
        for lv in URUT[1:]:
            if tb.LEVEL[lv] > tb.LEVEL[puncak] + 1e-6:
                break
            h = tb.LEVEL[lv] - tb.LEVEL[bawah(lv)]
            pintu = sum(lb for _, lb in td.PINTU[tipe]) * td.H_PINTU
            out.append({"k": "dinding", "lv": lv, "nama": nama, "tipe": tipe, "c": (cx, cy), "d": (dx, dy),
                        "vol": (2 * (dx + dy) * h - pintu) * td.T, "paket": paket(lv)})
    return out


def tangga():
    out = []
    for nama, _, puncak in tb.INTI:
        if not nama.startswith("Tangga"):
            continue
        d = dalam_inti(nama)
        x0, y0, x1, y1 = d.bounds
        for lv in URUT[1:]:
            if tb.LEVEL[lv] > tb.LEVEL[puncak] + 1e-6:
                break
            h = tb.LEVEL[lv] - tb.LEVEL[bawah(lv)]
            s = td.tangga(h)
            ya, yb = y0 + s["bordes"], y0 + s["bordes"] + s["lf"]
            th = math.atan(h / 2 / s["lf"])
            komponen = [  # (poli, offset tail m, kemiringan derajat, panah)
                (box(x0, y0, x1, ya), 0.0, 0.0, None),
                (box(x0, yb, x1, y1), h / 2, 0.0, None),
                (box(x0, ya, x0 + s["lebar"], yb), 0.0, math.degrees(th), ((x0 + s["lebar"] / 2, ya), (x0 + s["lebar"] / 2, yb))),
                (box(x1 - s["lebar"], ya, x1, yb), h / 2, math.degrees(th), ((x1 - s["lebar"] / 2, yb), (x1 - s["lebar"] / 2, ya))),
            ]
            for poli, off, kem, panah in komponen:
                vol = poli.area * s["t"] / (math.cos(th) if kem else 1.0)
                out.append({"k": "tangga", "lv": bawah(lv), "poli": poli, "offset": off, "slope": kem, "arrow": panah,
                            "t": s["t"], "vol": vol, "paket": paket(lv), "nama": nama})
    return out


# ------------------------------------------------------------------ bangun di BIMCraft
def _poli_mm(g):
    return [mm(x, y) for x, y in list(g.exterior.coords)[:-1]]


def bangun(uk_balok=None, status=STATUS):
    from bimcraft import Sesi

    daftar = unsur(uk_balok)
    ids = defaultdict(list)     # (kelompok, paket, sumber) -> id

    def catat(kunci, r):
        if isinstance(r, dict):
            ids[kunci] += [i for i in (r.get("ids") or [r.get("id")]) if isinstance(i, int)]

    with Sesi(TEMPLAT) as b:
        b.cmd("project_info", {"status": "Struktur Atas - model struktur LOD 300 (langkah 4.9)"})
        for nama, ket in (("RSTB_Mutu", "Mutu beton dan tulangan atau baja"),
                          ("RSTB_Paket", "Paket pelaksanaan: tahap 1 (K1) atau menyusul")):
            kat = ["wall", "floor", "column", "structuralcolumn", "beam", "footing", "roof", "stair", "railing", "room",
                   "component"]
            b.cmd("parameter", {"name": nama, "kind": "text", "categories": kat, "sets": {k: "Pset_RSTB_Umum" for k in kat},
                                "description": ket})
        b.cmd("material", {"name": "Baja BJ 41", "color": "#5A6E82", "cut": "solid"})
        tipe = set()

        def tipe_kolom(bm):
            n = f"KL-{round(bm * 1000)}x{round(bm * 1000)}-fc35"
            if n not in tipe:
                b.cmd("type", {"category": "structuralcolumn", "name": n, "width": round(bm * 1000),
                               "depth": round(bm * 1000), "material": "Beton fc 35 S2"})
                tipe.add(n)
            return n

        def tipe_balok(bb, hb):
            n = f"BL-{round(bb * 1000)}x{round(hb * 1000)}-fc30"
            if n not in tipe:
                b.cmd("type", {"category": "beam", "name": n, "width": round(bb * 1000), "depth": round(hb * 1000),
                               "material": "Beton fc 30 S2"})
                tipe.add(n)
            return n

        def tipe_pelat(t, awal="PL"):
            n = f"{awal}-{round(t * 1000)}-fc30"
            if n not in tipe:
                b.cmd("type", {"category": "floor", "name": n, "layers": [
                    {"function": "structure", "material": "Beton fc 30 S2", "thickness": round(t * 1000)}]})
                tipe.add(n)
            return n

        dg = f"DG-{round(td.T * 1000)}-fc35"
        b.cmd("type", {"category": "wall", "name": dg, "layers": [
            {"function": "structure", "material": "Beton fc 35 S2", "thickness": round(td.T * 1000)}]})
        for k, pintu in td.PINTU.items():
            lb = pintu[0][1]
            b.cmd("type", {"category": "door", "name": f"PT-{k}-{round(lb * 1000)}x{round(td.H_PINTU * 1000)}",
                           "width": round(lb * 1000), "height": round(td.H_PINTU * 1000)})
        b.cmd("type", {"category": "structuralcolumn", "name": DEK_PROFIL, "profile": DEK_PROFIL, "material": "Baja BJ 41"})
        for i, x in enumerate(tb.GRID_X):
            b.cmd("grid", {"start": mm(x, tb.GRID_Y[0] - 6), "end": mm(x, tb.GRID_Y[-1] + 6), "name": str(i + 1)})
        for j, y in enumerate(tb.GRID_Y):
            b.cmd("grid", {"start": mm(tb.GRID_X[0] - 6, y), "end": mm(tb.GRID_X[-1] + 6, y), "name": NAMA_Y[j]})

        for u in daftar:
            k, lv = u["k"], u["lv"]
            if k == "kolom":
                tr = kl.UKURAN_KOLOM.get((lv, u["x"], u["y"]))
                sumber = "4.7 kolom transfer tangki (950/800 LT1-LT3)" if tr else "4.7 kolom SRPMK"
                catat((k, u["paket"], sumber), b.cmd("structural_column", {
                    "at": mm(u["x"], u["y"]), "type": tipe_kolom(u["b"]), "level": bawah(lv), "top_level": lv}))
            elif k == "balok":
                x1, y1, x2, y2 = u["p"]
                sumber = "4.6 " + u.get("khusus", "balok SRPMK" if (u["b"], u["h"]) == (tb.BALOK_B, tb.BALOK_H)
                                          else "balok transfer tangki")
                catat((k, u["paket"], sumber), b.cmd("beam", {"points": [mm(x1, y1), mm(x2, y2)],
                                                              "type": tipe_balok(u["b"], u["h"]), "level": lv}))
            elif k == "pelat":
                p = {"boundary": _poli_mm(u["poli"]), "level": lv, "type": tipe_pelat(u["t"]), "structural": True}
                if u["lubang"]:
                    p["openings"] = [_poli_mm(o) for o in u["lubang"]]
                if u["offset"]:
                    p["offset"] = round(u["offset"] * 1000)
                sumber = {"PL-250-tangki": "4.5 pelat 250 di bawah tangki", "PL-200-LB1": "4.5 lantai turun CSSD LB-1 (300)"
                          }.get(u["nama"], "4.5 pelat 200")
                catat((k, u["paket"], sumber), b.cmd("floor", p))
            elif k == "dinding":
                (cx, cy), (dx, dy) = u["c"], u["d"]
                r = b.cmd("wall", {"points": [mm(cx - dx / 2, cy - dy / 2), mm(cx + dx / 2, cy - dy / 2),
                                              mm(cx + dx / 2, cy + dy / 2), mm(cx - dx / 2, cy + dy / 2)],
                                   "closed": True, "type": dg, "level": bawah(lv), "top_level": lv})
                catat((k, u["paket"], "4.8 dinding inti 350" + ("; " + KOPEL_LIF if u["tipe"] == "L" else "")), r)
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
                catat((k, u["paket"], "4.8 tangga pelat 250 (bordes dan lengan)"), b.cmd("floor", p))
            elif k == "dek":
                catat((k, u["paket"], "4.6 tumpuan dek helipad baja (tiang A / angkur B) [Asumsi profil]"),
                      b.cmd("structural_column", {"at": mm(u["x"], u["y"]), "type": DEK_PROFIL, "level": "ATAP",
                                                  "height": DEK_TINGGI}))
        # shaft MEP dan ruang lif
        for kode, x0, x1, y0, y1, a, c in SHAFT:
            b.cmd("shaft", {"boundary": _poli_mm(box(x0, y0, x1, y1)), "level": a, "base_offset": 100,
                            "height": lv_mm(c) - lv_mm(a)})
        lif = dalam_inti("Inti lif x50-58 y35-43")
        b.cmd("shaft", {"boundary": _poli_mm(lif), "level": "LT1", "base_offset": 100,
                        "height": lv_mm("LT6") - lv_mm("LT1")})
        for (k, pk, sumber), daftar_id in ids.items():
            b.cmd("modify", {"ids": daftar_id, "params": {
                "RSTB_Tahap": "4", "RSTB_LOD": "300", "RSTB_Status": status, "RSTB_KelasPaparan": "-",
                "RSTB_Mutu": MUTU[k], "RSTB_Paket": pk, "RSTB_Sumber": f"[{k}] {sumber}"}})
        b.simpan(BIMC)
        b.simpan(IFC)
        GAMBAR.mkdir(parents=True, exist_ok=True)
        b.alat("render", {"view": "{3D}", "path": str(GAMBAR / "4.9 Model LOD 300 3D.png"), "width": 1600, "height": 1000})
    return {k: len(v) for k, v in ids.items()}


# ------------------------------------------------------------------ validasi IFC
def _kelompok(e):
    import ifcopenshell.util.element as ue
    s = str(ue.get_psets(e).get("Pset_RSTB_Umum", {}).get("RSTB_Sumber", ""))
    return s[1:s.index("]")] if s.startswith("[") else None


def validasi(path=IFC, uk_balok=None):
    """Cek hierarki, Pset, GlobalId (pola 3.9) dan volume IFC vs rencana per kelompok."""
    import tahap3_bim as t3
    import ifcopenshell
    import ifcopenshell.util.element as ue

    v = t3.validasi(path, wajib_lod=False)
    f = v["file"]
    struktur = [e for e in f.by_type("IfcElement") if _kelompok(e)]
    cek = list(v["cek"])
    tanpa = [e for e in struktur if str(ue.get_psets(e)["Pset_RSTB_Umum"].get("RSTB_LOD")) != "300"
             or not ue.get_psets(e)["Pset_RSTB_Umum"].get("RSTB_Paket")]
    cek.append({"butir": "Pset_RSTB_Umum RSTB_LOD 300 + RSTB_Paket + RSTB_Mutu", "lolos": not tanpa,
                "ket": f"{len(tanpa)} dari {len(struktur)} unsur struktur tidak lengkap"})
    vol = t3.volume_elemen(f)
    ifc = defaultdict(float)
    for e in struktur:
        ifc[_kelompok(e)] += vol.get(e.id(), (0.0, 0.0))[0]
    rencana = defaultdict(float)
    for u in unsur(uk_balok):
        rencana[u["k"]] += u["vol"]
    baris = [{"unsur": k, "ifc": ifc[k], "rencana": rencana[k], "selisih": ifc[k] / rencana[k] - 1}
             for k in ("kolom", "balok", "pelat", "dinding", "tangga") if rencana[k]]
    paket = defaultdict(float)
    for e in struktur:
        paket[str(ue.get_psets(e)["Pset_RSTB_Umum"].get("RSTB_Paket"))] += vol.get(e.id(), (0.0, 0.0))[0]
    return {"cek": cek, "lolos": all(c["lolos"] for c in cek), "volume": baris, "paket": dict(paket),
            "kelas": v["kelas"], "file": f}


def clash_shaft(f):
    """Unsur struktur (kotak batas geometri dunia) yang masuk ke prisma shaft MEP (tepi bersih > 10 mm)."""
    import ifcopenshell.geom
    import numpy as np

    s = ifcopenshell.geom.settings()
    s.set("use-world-coords", True)
    kotak = {}
    it = ifcopenshell.geom.iterator(s, f, include=[e for e in f.by_type("IfcElement") if _kelompok(e)])
    if it.initialize():
        while True:
            sh = it.get()
            v = np.array(sh.geometry.verts).reshape(-1, 3)
            kotak[sh.id] = (v.min(0), v.max(0))
            if not it.next():
                break
    hasil = []
    e_tol = 0.010
    for kode, x0, x1, y0, y1, a, c in SHAFT:
        z0, z1 = tb.LEVEL[a] + 0.1, tb.LEVEL[c] + 0.1
        for i, (mn, mx) in kotak.items():
            if (mn[0] < x1 - e_tol and mx[0] > x0 + e_tol and mn[1] < y1 - e_tol and mx[1] > y0 + e_tol
                    and mn[2] < z1 - e_tol and mx[2] > z0 + e_tol):
                e = f.by_id(i)
                if e.is_a("IfcSlab"):
                    continue  # pelat dilubangi shaft; kotak batas pelat selalu menutupi shaft
                c_ = e.ContainedInStructure[0].RelatingStructure.Name if e.ContainedInStructure else "-"
                hasil.append({"shaft": kode, "kelas": e.is_a(), "nama": e.Name, "lantai": c_,
                              "x": (round(float(mn[0]), 2), round(float(mx[0]), 2)),
                              "y": (round(float(mn[1]), 2), round(float(mx[1]), 2))})
    return hasil


# ------------------------------------------------------------------ fasad (arsitektur, 3 varian untuk dipilih Defsa)
FASAD_JARAK = 0.6     # m, bidang fasad di luar as grid tepi (muka kolom 750 di 0,375) [Asumsi]
VARIAN = {
    "V1": "Pita horizontal: spandrel ACP putih 1,1 m + kaca pita setinggi lantai (tenang, mudah dirawat)",
    "V2": "Sirip vertikal aluminium 150 × 600 @ 1,6 m di depan kaca (peneduh sore barat-timur, kesan tinggi)",
    "V3": "Kaca + overstek horizontal 0,9 m tiap lantai di utara-selatan, dinding terakota masif di barat-timur",
}


def _pita():
    """(poligon, tingkat bawah, tingkat atas) bidang fasad."""
    return [(tb.PODIUM, "LT1", "LT3"), (tb.LT3, "LT3", "LT4"), (tb.MENARA, "LT4", "ATAP")]


def _sisi(poli):
    """Sisi poligon searah jarum jam (muka luar di kiri arah gambar BIMCraft)."""
    g = poli.buffer(FASAD_JARAK, join_style=2)
    c = list(g.exterior.coords)
    if g.exterior.is_ccw:
        c = c[::-1]
    return list(zip(c[:-1], c[1:]))


def fasad(varian, sumber=BIMC):
    from bimcraft import Sesi
    keluar = AKAR / "model" / f"RSTB-ARS-T4-Fasad-{varian}.bimc"
    with Sesi(sumber) as b:
        for nama, warna, tr in (("Kaca fasad", "#7FA7BA", 55), ("ACP putih", "#F1F1EE", 0),
                                ("Aluminium sirip", "#8E979E", 0), ("Terakota", "#B4643C", 0)):
            b.cmd("material", {"name": nama, "color": warna, "transparency": tr})
        for nama, bahan, t in (("FS-Kaca", "Kaca fasad", 30), ("FS-ACP", "ACP putih", 50), ("FS-Terakota", "Terakota", 200)):
            b.cmd("type", {"category": "wall", "name": nama,
                           "layers": [{"function": "finish", "material": bahan, "thickness": t}]})
        b.cmd("type", {"category": "column", "name": "SR-150x600", "width": 150, "depth": 600, "material": "Aluminium sirip"})
        b.cmd("type", {"category": "floor", "name": "OV-100", "layers": [
            {"function": "finish", "material": "ACP putih", "thickness": 100}]})
        for poli, a, c in _pita():
            tingkat = URUT[URUT.index(a):URUT.index(c) + 1]
            for p0, p1 in _sisi(poli):
                barat_timur = abs(p0[0] - p1[0]) < 1e-6
                for lo, hi in zip(tingkat[:-1], tingkat[1:]):
                    h = lv_mm(hi) - lv_mm(lo)
                    pts = [mm(*p0), mm(*p1)]
                    if varian == "V1":
                        b.cmd("wall", {"points": pts, "type": "FS-ACP", "level": lo, "height": 1100})
                        b.cmd("wall", {"points": pts, "type": "FS-Kaca", "level": lo, "base_offset": 1100,
                                       "height": h - 1100})
                    else:
                        tipe = "FS-Terakota" if varian == "V3" and barat_timur else "FS-Kaca"
                        b.cmd("wall", {"points": pts, "type": tipe, "level": lo, "height": h})
                if varian == "V2":
                    pj = math.dist(p0, p1)
                    for i in range(1, int(pj / 1.6)):
                        s = i * 1.6 / pj
                        x, y = p0[0] + s * (p1[0] - p0[0]), p0[1] + s * (p1[1] - p0[1])
                        nx, ny = (p1[1] - p0[1]) / pj * -0.45, (p1[0] - p0[0]) / pj * 0.45   # 0,45 m keluar
                        b.cmd("column", {"at": mm(x - nx, y - ny), "type": "SR-150x600", "level": a, "top_level": c,
                                         "angle": 0 if barat_timur else 90})
            if varian == "V3":
                luar = poli.buffer(FASAD_JARAK + 0.9, join_style=2)
                dalam = poli.buffer(FASAD_JARAK, join_style=2)
                for lo in tingkat[:-1]:
                    b.cmd("floor", {"boundary": _poli_mm(luar), "openings": [_poli_mm(dalam)], "level": lo,
                                    "offset": 3000, "type": "OV-100"})
        b.cmd("project_info", {"status": f"Fasad {varian} (usulan 4.9): {VARIAN[varian]}"})
        b.simpan(keluar)
        b.alat("render", {"view": "{3D}", "path": str(GAMBAR / f"4.9 Fasad {varian}.png"), "width": 1600, "height": 1000,
                          "azimuth": -60, "elevation": 20})
    return keluar


if __name__ == "__main__":
    import sys
    if "--bangun" in sys.argv:
        print(bangun())
    r = validasi()
    for c in r["cek"]:
        print(("OK  " if c["lolos"] else "GAL ") + c["butir"], "|", c["ket"])
    for b in r["volume"]:
        print(f"{b['unsur']:8s} IFC {b['ifc']:9.1f}  rencana {b['rencana']:9.1f}  {b['selisih']:+.1%}")
    print("paket", {k: round(v, 1) for k, v in r["paket"].items()})
    for c in clash_shaft(r["file"]):
        print("clash", c)
