"""Tahap 8a: volume otomatis dari model BIM LOD 300 dan AHSP pekerjaan utama.

Keluaran: `08 RAB/8a Volume dan AHSP.xlsx` + `.md`. Keputusan K8-1..K8-7 di `08 RAB/00 Rencana Tahap 8.md`.
Data simulasi. Jalankan: .venv\\Scripts\\python.exe skrip\\tahap8_volume.py
"""
import collections
import functools
import math
import pathlib
import re
import sys

import ifcopenshell
import ifcopenshell.util.element as ue

AKAR = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AKAR / "skrip"))
IFC_STR = AKAR / "model" / "RSTB-STR-T7-LOD300.ifc"
IFC_ARS = AKAR / "model" / "RSTB-ARS-T7-LOD300.ifc"
KELUAR = AKAR / "08 RAB" / "8a Volume dan AHSP.xlsx"
STATUS = "disetujui Defsa 23 Nov 2026"
LABEL = "Data simulasi studi kasus. Harga [Asumsi: Jambi 2026], belum survei harga (SE 47/2026 Lampiran I)."
TOL = {"T-119a": 1.0, "T-119b": 5.0, "T-120": 75.0}   # %, ditetapkan sebelum membandingkan (rencana Tahap 8)
BTL = 0.12              # biaya umum + keuntungan, Permen PUPR 8/2023 Ps. 11 ayat (3) hal. 9: 10-15 % (K8-5)
T_PELAT, B_KOLOM, MASUK_CAP = 0.20, 0.75, 0.15   # m [Asumsi K8-2]

# Rasio tulangan kg/m³ (K8-3): Tahap 3.6 tahap3_struktur.BESI dan tahap3_biaya.BESI_KG [Asumsi]; sloof/tangga/pit [Asumsi]
BESI = {"Kolom": 200.0, "Balok": 180.0, "Pelat lantai": 100.0, "Dinding geser inti": 140.0, "Pile cap": 100.0,
        "Pelat lantai 1": 110.0, "Sloof dan balok pondasi": 150.0, "Tangga": 100.0, "Pit lift": 120.0}
MASSA = {"D13": 1.04, "D25": 3.85}   # kg/m, SNI 2052:2017 (D13 dipakai sejak 5.5)

# Data pembanding tahap lalu (VERIFIKASI.md)
T84 = {"Kolom": 677.8, "Balok": 860.6, "Pelat lantai": 2543.3, "Dinding geser inti": 1009.8, "Tangga": 141.6}
T107 = {"tiang": 6176.2, "n_tiang": 319, "cap": 2146.1}
CAP_E_LEBAR = 4.6 * 2.813 * 2.0      # m³, perlebaran Cap E 7.3 (x 37,1-41,7, y 29,4-32,2, h 2,0)


def _qto(e):
    q = {}
    for k, v in ue.get_psets(e, qtos_only=True).items():
        q.update({a: b for a, b in v.items() if a != "id"})
    return q


@functools.lru_cache(None)
def baca(path):
    m = ifcopenshell.open(str(path))
    out = []
    for e in m.by_type("IfcElement"):
        if e.is_a() in ("IfcOpeningElement", "IfcVirtualElement"):
            continue
        c = ue.get_container(e)
        out.append({"kelas": e.is_a(), "tipe": e.ObjectType or e.Name or "", "lantai": c.Name if c else "-", "q": _qto(e)})
    return out


def kelompok_str(kelas, tipe):
    if kelas == "IfcPile":
        return "Tiang bor Ø800"
    if kelas == "IfcFooting":
        return "Pile cap"
    if kelas == "IfcBeam":
        return "Sloof dan balok pondasi" if tipe[:2] in ("SL", "BP") else "Balok"
    if kelas == "IfcColumn":
        return "Kolom baja HEB 200" if tipe.startswith("HEB") else "Kolom"
    if kelas == "IfcSlab":
        if tipe.startswith("PL-250"):
            return "Pelat lantai 1"
        return {"PIT": "Pit lift", "TG-": "Tangga"}.get(tipe[:3], "Pelat lantai")
    if kelas == "IfcWall":
        return "Dinding geser inti" if tipe.startswith("DG") else "Pit lift"
    return None   # IfcDoor STR (pintu lift, dihitung di ARS), IfcReinforcingBar (contoh 7.5)


def _bh(tipe):
    a, b = re.search(r"(\d+)x(\d+)", tipe).groups()
    return int(a) / 1000, int(b) / 1000


def _fc(tipe):
    m = re.search(r"fc(\d+)", tipe)
    return int(m.group(1)) if m else None


def besi_tiang(L):
    """kg per tiang, susunan 6.7: 16 D25 sampai -17,76 (ujung -27,60) + stek 0,9 m ke cap; spiral D13 40 (6 m atas) / 80."""
    l_tul = L - (27.60 - 17.76) + 0.9                       # [Asumsi stek 36 db]
    keliling = math.pi * (0.800 - 2 * 0.075 - 0.013)        # selimut 75 mm [Asumsi]
    spiral = keliling * MASSA["D13"] * (6.0 / 0.040 + (l_tul - 6.0) / 0.080)
    return 16 * MASSA["D25"] * l_tul + spiral


def volume_struktur():
    g = collections.defaultdict(lambda: collections.Counter())
    soffit_balok = 0.0
    for r in baca(IFC_STR):
        k = kelompok_str(r["kelas"], r["tipe"])
        if not k:
            continue
        q, t = r["q"], r["tipe"]
        x = g[k]
        x["n"] += 1
        vg = q.get("GrossVolume", 0.0)
        x["kotor"] += q.get("NetVolume", vg)            # Qto bersih lubang (setara geometri T-84)
        fc = _fc(t)
        if k == "Tiang bor Ø800":
            L = q["Length"] / 1000
            vn = vg - q["CrossSectionArea"] * MASUK_CAP
            x["panjang"] += L
            x["besi"] += besi_tiang(L)
        elif k == "Balok":
            b, h = _bh(t)
            Ln = q["Length"] / 1000 - B_KOLOM
            vn = b * (h - T_PELAT) * Ln
            x["bek_h"] += (b + 2 * (h - T_PELAT)) * Ln
            soffit_balok += b * Ln
        elif k == "Kolom":
            b, _ = _bh(t)
            H = q["Length"] / 1000
            vn = vg - b * b * T_PELAT
            x["bek_v"] += 4 * b * (H - T_PELAT)
        elif k == "Kolom baja HEB 200":
            vn = 0.0
            x["baja"] += vg * 7850
        elif k == "Sloof dan balok pondasi":
            b, h = _bh(t)
            vn = vg                                        # [Asumsi: tumpang sloof di cap tidak dikurangi]
            x["bek_v"] += 2 * h * q["Length"] / 1000
        elif k == "Pile cap":
            L, W, H = q["Length"] / 1000, q["Width"] / 1000, q["Height"] / 1000
            vn = q.get("NetVolume", vg)
            x["bek_v"] += 2 * (L + W) * H
            x["galian"] += (L + 2) * (W + 2) * (H + 0.1)    # ruang kerja 1,0 m tiap sisi (6.8) + lantai kerja 0,1
            x["lantai_kerja"] += (L + 0.2) * (W + 0.2) * 0.1
        elif k in ("Dinding geser inti",) or (k == "Pit lift" and r["kelas"] == "IfcWall"):
            vn = q.get("NetVolume", vg)
            x["bek_v"] += 2 * q.get("NetSideArea", 0.0)
        else:                                               # pelat, pelat LT1, pit (pelat), tangga
            vn = q.get("NetVolume", vg)
            x["bek_h"] += q.get("NetArea", 0.0) if k != "Pelat lantai 1" else 0.0   # pelat LT1 di atas tanah/lantai kerja
        x["bersih"] += vn
        if fc:
            x[f"fc{fc}"] += vn
        if k in BESI:
            x["besi"] += vn * BESI[k]
    g["Pelat lantai"]["bek_h"] -= soffit_balok             # dasar balok sudah di bekisting balok
    return {k: dict(v) for k, v in g.items()}


# ------------------------------------------------------------------ arsitektur
ARS_PETA = {   # tipe/prefiks -> (kode, uraian, satuan, besaran Qto)
    "DP-Bata150": ("A7a", "Dinding bata ringan 150 mm", "m²", "NetSideArea"),
    "DP-Bata100": ("A7b", "Dinding bata ringan 100 mm", "m²", "NetSideArea"),
    "FS-Kaca": ("A9", "Fasad kaca (curtain wall unitized)", "m²", "NetSideArea"),
    "FS-Panel": ("A10", "Fasad panel komposit aluminium + rangka", "m²", "NetSideArea"),
    "DL-LapisInti50": ("R-DL", "Lapis dinding inti 50 mm (finishing)", "m²", "NetSideArea"),
    "PL-Gypsum": ("R-PF", "Plafon gipsum 12 mm + rangka hollow", "m²", "NetArea"),
    "LT-PARKIR": ("R-LE", "Lantai epoksi (parkir, servis, utilitas)", "m²", "NetArea"),
    "LT-SERVIS": ("R-LE", "Lantai epoksi (parkir, servis, utilitas)", "m²", "NetArea"),
    "LT-UTIL": ("R-LE", "Lantai epoksi (parkir, servis, utilitas)", "m²", "NetArea"),
    "LT-RAWAT": ("R-LV", "Lantai vinil homogen RS (rawat, intensif, OK, klinik)", "m²", "NetArea"),
    "LT-INTENSIF": ("R-LV", "Lantai vinil homogen RS (rawat, intensif, OK, klinik)", "m²", "NetArea"),
    "LT-OK": ("R-LV", "Lantai vinil homogen RS (rawat, intensif, OK, klinik)", "m²", "NetArea"),
    "LT-KLINIK": ("R-LV", "Lantai vinil homogen RS (rawat, intensif, OK, klinik)", "m²", "NetArea"),
    "LT-": ("R-LG", "Lantai granit/homogeneous tile 60 × 60", "m²", "NetArea"),
    "Single Door": ("R-P1", "Pintu tunggal 900 × 2100 + kusen + kunci", "bh", None),
    "Double Door": ("R-P2", "Pintu ganda 1200-1500 × 2100 + kusen + kunci", "bh", None),
    "PL-1400": ("R-P3", "Pintu lift 1400 × 2400 (bagian paket lift)", "bh", None),
    "Railing": ("R-RL", "Railing 1000 mm", "bh", None),
    "TP-Aspal": ("R-AS", "Perkerasan aspal jalan dan parkir luar", "m²", "NetArea"),
    "TP-Paving": ("R-PV", "Paving blok", "m²", "NetArea"),
    "TP-Beton": ("R-PB", "Perkerasan beton", "m²", "NetArea"),
    "TP-Rumput": ("R-RT", "Lansekap rumput dan tanah humus", "m²", "NetArea"),
    "TP-TamanAtap": ("R-TA", "Taman atap (kedap air + media tanam)", "m²", "NetArea"),
    "TP-Kanopi": ("R-KN", "Kanopi drop-off", "m²", "NetArea"),
    "TP-DekHelipad": ("R-HP", "Dek helipad (tahap 2, struktur disiapkan)", "m²", "NetArea"),
    "TP-Overstek": ("R-OV", "Overstek fasad", "m²", "NetArea"),
    "PG-Pagar150": ("R-PG", "Pagar keliling", "m²", "NetSideArea"),
    "PG-Tiang400": ("R-PG", "Pagar keliling", "m²", "NetSideArea"),
    "PG-Papan": ("R-NM", "Papan nama", "m²", "NetSideArea"),
    "BT-Bak200": ("R-BK", "Bak tanaman beton", "m³", "NetVolume"),
    "TK-Panel100": ("R-TK", "Dinding panel tangki air", "m²", "NetSideArea"),
}
ARS_TIDAK = ("RSTB ", "TP-Air", "TP-Lereng", "TP-Marka", "TP-AtapTangki")   # entourage, air sungai, lereng alami, marka, atap tangki (dicek 8b)


def _peta(tipe):
    for k in sorted(ARS_PETA, key=len, reverse=True):
        if tipe.startswith(k):
            return ARS_PETA[k]
    return None


def volume_arsitektur():
    v = collections.OrderedDict()
    tidak = collections.Counter()
    for r in baca(IFC_ARS):
        t = r["tipe"]
        if t.startswith(ARS_TIDAK):
            tidak[t.split(":")[0]] += 1
            continue
        p = _peta(t)
        if not p:
            tidak[t] += 1
            continue
        kode, ur, sat, qk = p
        x = v.setdefault(kode, {"uraian": ur, "satuan": sat, "volume": 0.0, "n": 0})
        x["volume"] += r["q"].get(qk, 0.0) if qk else 1
        x["n"] += 1
    bata = v["A7a"]["volume"] + v["A7b"]["volume"]
    v["A8"] = {"uraian": "Plesteran + acian dinding bata (2 sisi)", "satuan": "m²", "volume": 2 * bata, "n": 0}
    v["R-CT"] = {"uraian": "Cat dinding interior (2 sisi bata + lapis inti)", "satuan": "m²",
                 "volume": 2 * bata + v["R-DL"]["volume"], "n": 0}
    return v, tidak


# ------------------------------------------------------------------ harga dasar [Asumsi: Jambi 2026]
DASAR = {  # kode: (uraian, satuan, harga Rp)
    "L01": ("Pekerja", "OH", 130_000), "L02": ("Tukang", "OH", 160_000), "L03": ("Kepala tukang", "OH", 175_000),
    "L04": ("Mandor", "OH", 190_000), "L05": ("Operator alat berat", "OH", 210_000),
    "M01": ("Beton siap pakai fc' 35 MPa (slump 18 ± 2, tremie)", "m³", 1_420_000),
    "M02": ("Beton siap pakai fc' 35 MPa", "m³", 1_350_000), "M03": ("Beton siap pakai fc' 30 MPa", "m³", 1_260_000),
    "M04": ("Baja tulangan BjTS 420B", "kg", 13_500), "M05": ("Kawat bendrat", "kg", 25_000),
    "M06": ("Kayu kelas III (balok/papan)", "m³", 3_600_000), "M07": ("Multipleks 12 mm (122 × 244)", "lbr", 235_000),
    "M08": ("Paku 5-12 cm", "kg", 22_000), "M09": ("Minyak bekisting", "L", 15_000),
    "M10": ("Perancah besi (sewa per pakai, per m²)", "m²", 28_000), "M11": ("Bentonit", "kg", 6_500),
    "M12": ("Bata ringan (AAC)", "m³", 760_000), "M13": ("Perekat bata ringan (instan)", "kg", 2_900),
    "M14": ("Semen portland", "kg", 1_550), "M15": ("Pasir pasang", "m³", 310_000),
    "M16": ("Unit curtain wall kaca + rangka aluminium (pabrikasi)", "m²", 2_650_000),
    "M17": ("Sealant silikon struktural", "L", 120_000), "M18": ("Angkur + bracket fasad galvanis", "set", 85_000),
    "M19": ("Panel komposit aluminium 4 mm", "m²", 640_000), "M20": ("Rangka hollow galvanis 40 × 40", "kg", 28_000),
    "E01": ("Mesin bor tiang Ø ≤ 2,0 m + bahan bakar (E33)", "jam", 1_150_000),
    "E02": ("Crawler crane 50 t (bantu tulangan/tremie)", "jam", 680_000), "E03": ("Pompa beton", "jam", 520_000),
    "E04": ("Vibrator beton", "jam", 45_000), "E05": ("Dump truck 8 m³ (angkut tanah bor ≤ 5 km)", "m³", 85_000),
    "E06": ("Pompa air 4\" + bahan bakar (sewa)", "hari", 620_000), "E07": ("Gondola/alat angkat fasad", "jam", 250_000),
}


def koef_bor(p):
    """jam alat per m' tiang bor; SE 47/2026 Lampiran II hal. 187-188 (E33): Q1 = V p Fa 60 / Ts, contoh p 25,4 m Ts 225 menit.
    Pengeboran (90 menit) dan pengecoran (45 menit) diskalakan dengan p [Asumsi]."""
    ts = 5 + 10 + 5 + 20 + 90 * p / 25.4 + 15 + 15 + 45 * p / 25.4 + 20
    return 1 / (1 * p * 0.83 * 60 / ts)


def ahsp(p_tiang):
    """Kode: (uraian, satuan, [(kode dasar, koefisien)], catatan sumber). Koefisien [Asumsi: koefisien umum AHSP CK] (K8-6)."""
    kb = koef_bor(p_tiang)
    a_t = math.pi / 4 * 0.8 ** 2
    upah_beton = [("L01", 0.50), ("L02", 0.10), ("L03", 0.010), ("L04", 0.030)]
    bek = [("L01", 0.52), ("L02", 0.26), ("L03", 0.026), ("L04", 0.026), ("M08", 0.30), ("M09", 0.20)]
    return {
        "A1": ("Tiang bor Ø800 fc' 35 (bor, cor tremie, tanpa besi)", "m'",
               [("E01", kb), ("E02", kb), ("L05", kb / 8), ("L01", 0.15), ("L02", 0.05), ("L04", 0.015),
                ("M01", round(a_t * 1.10, 4)), ("M11", round(a_t * 40, 2)), ("E05", round(a_t * 1.2, 4))],
               f"Alat: SE 47/2026 Lamp. II hal. 187-188 (p {p_tiang:.1f} m, Fa 0,83, koef {kb:.4f} jam/m'); "
               "beton + overbreak 10 %, bentonit 40 kg/m³, tanah bor mengembang 1,2 [Asumsi]"),
        "A2": ("Beton siap pakai fc' 35 MPa dicor dengan pompa", "m³",
               [("M02", 1.02), ("E03", 0.05), ("E04", 0.10)] + upah_beton, "[Asumsi: koefisien umum AHSP CK beton siap pakai]"),
        "A3": ("Beton siap pakai fc' 30 MPa dicor dengan pompa", "m³",
               [("M03", 1.02), ("E03", 0.05), ("E04", 0.10)] + upah_beton, "[Asumsi: koefisien umum AHSP CK beton siap pakai]"),
        "A4": ("Pembesian BjTS 420B (potong, bengkok, pasang)", "kg",
               [("M04", 1.05), ("M05", 0.015), ("L01", 0.007), ("L02", 0.007), ("L03", 0.0007), ("L04", 0.0004)],
               "[Asumsi: koefisien umum AHSP CK pembesian 10 kg dibagi 10]"),
        "A5": ("Bekisting kolom, dinding, sisi cap/sloof (multipleks, pakai 3 kali)", "m²",
               [("M06", round(0.040 / 3, 4)), ("M07", round(0.35 / 3, 4))] + bek, "[Asumsi: koefisien umum AHSP CK, kayu/multipleks dibagi 3 pakai]"),
        "A6": ("Bekisting pelat dan balok + perancah (multipleks, pakai 3 kali)", "m²",
               [("M06", round(0.030 / 3, 4)), ("M07", round(0.35 / 3, 4)), ("M10", 1.0)] + bek, "[Asumsi: koefisien umum AHSP CK, perancah besi sewa]"),
        "A7a": ("Dinding bata ringan 150 mm", "m²",
                [("M12", 0.1575), ("M13", 5.0), ("L01", 0.30), ("L02", 0.10), ("L03", 0.010), ("L04", 0.015)], "[Asumsi: koefisien umum AHSP CK, susut bata 5 %]"),
        "A7b": ("Dinding bata ringan 100 mm", "m²",
                [("M12", 0.1050), ("M13", 3.5), ("L01", 0.30), ("L02", 0.10), ("L03", 0.010), ("L04", 0.015)], "[Asumsi: koefisien umum AHSP CK, susut bata 5 %]"),
        "A8": ("Plesteran 1:4 tebal 15 mm + acian (satu sisi)", "m²",
               [("M14", 9.49), ("M15", 0.024), ("L01", 0.50), ("L02", 0.25), ("L03", 0.025), ("L04", 0.025)], "[Asumsi: koefisien umum AHSP CK plester + acian]"),
        "A9": ("Fasad kaca curtain wall unitized (pasok + pasang)", "m²",
               [("M16", 1.0), ("M17", 0.40), ("M18", 1.0), ("E07", 0.08), ("L01", 0.25), ("L02", 0.25), ("L04", 0.025)], "[Asumsi: harga pabrikasi subkontraktor]"),
        "A10": ("Fasad panel komposit aluminium + rangka hollow", "m²",
                [("M19", 1.05), ("M20", 4.5), ("M17", 0.15), ("E07", 0.06), ("L01", 0.30), ("L02", 0.30), ("L04", 0.030)], "[Asumsi: koefisien pemasok]"),
        "A11": ("Dewatering sump terbuka (sewa pompa + operator)", "pompa-hari",
                [("E06", 1.0), ("L05", 1.0), ("L01", 0.5)], "Metode 6.8 (sump terbuka, parit keliling Cap E/pit) [Asumsi koefisien]"),
    }


def harga_satuan(kode, tabel):
    ur, sat, isi, _ = tabel[kode]
    d = sum(DASAR[k][2] * c for k, c in isi)
    return {"langsung": d, "btl": d * BTL, "hsp": d * (1 + BTL)}


RINGKAS = {  # kode: harga satuan termasuk BTL [Asumsi: Jambi 2026, harga satuan pasar ringkas]
    "R-GL": 95_000, "R-UR": 78_000, "R-LK": 1_050_000, "R-BJ": 34_000, "R-DL": 185_000, "R-PF": 195_000,
    "R-LE": 260_000, "R-LV": 480_000, "R-LG": 360_000, "R-P1": 4_200_000, "R-P2": 7_500_000, "R-P3": 0,
    "R-RL": 6_500_000, "R-AS": 265_000, "R-PV": 190_000, "R-PB": 210_000, "R-RT": 55_000, "R-TA": 720_000,
    "R-KN": 1_350_000, "R-HP": 2_600_000, "R-OV": 950_000, "R-PG": 480_000, "R-NM": 1_500_000, "R-BK": 2_900_000,
    "R-TK": 1_100_000, "R-CT": 42_000,
}


def daftar_pekerjaan():
    """Item volume × harga satuan untuk uji Pareto (T-120); RAB resmi di 8b."""
    s = volume_struktur()
    v_ars, _ = volume_arsitektur()
    tiang = s["Tiang bor Ø800"]
    tab = ahsp(tiang["panjang"] / tiang["n"])
    fc = collections.Counter()
    for k, x in s.items():
        if k != "Tiang bor Ø800":
            fc[35] += x.get("fc35", 0.0)
            fc[30] += x.get("fc30", 0.0)
    cap = s["Pile cap"]
    vg = cap["galian"]
    bek_v = sum(x.get("bek_v", 0.0) for x in s.values())
    bek_h = sum(x.get("bek_h", 0.0) for x in s.values())
    besi = sum(x.get("besi", 0.0) for x in s.values())
    pompa_hari = 3 * 150     # [Asumsi: 3 pompa × 150 hari kerja galian cap per zona (6.8)]
    item = [
        ("A1", "Tiang bor Ø800 fc' 35", "m'", tiang["panjang"]),
        ("A2", "Beton fc' 35 (cap, sloof, kolom, dinding, pelat LT1, pit)", "m³", fc[35]),
        ("A3", "Beton fc' 30 (balok, pelat, tangga)", "m³", fc[30]),
        ("A4", "Pembesian BjTS 420B (rasio kg/m³ + tiang 6.7)", "kg", besi),
        ("A5", "Bekisting vertikal", "m²", bek_v),
        ("A6", "Bekisting pelat dan balok + perancah", "m²", bek_h),
        ("A11", "Dewatering galian cap dan pit", "pompa-hari", pompa_hari),
    ]
    for k in ("A7a", "A7b", "A8", "A9", "A10"):
        item.append((k, v_ars[k]["uraian"], v_ars[k]["satuan"], v_ars[k]["volume"]))
    item +=[("R-GL", "Galian tanah cap (ruang kerja 1 m)", "m³", vg),
             ("R-LK", "Lantai kerja beton fc' 10 tebal 100 mm", "m³", cap["lantai_kerja"]),
             ("R-UR", "Urugan kembali dipadatkan", "m³", max(vg - cap["bersih"] - cap["lantai_kerja"], 0.0)),
             ("R-BJ", "Kolom baja HEB 200 (pasok + pasang)", "kg", s["Kolom baja HEB 200"]["baja"])]
    for k, x in v_ars.items():
        if k.startswith("R-"):
            item.append((k, x["uraian"], x["satuan"], x["volume"]))
    out = []
    for kode, ur, sat, vol in item:
        hsp = harga_satuan(kode, tab)["hsp"] if kode in tab else RINGKAS[kode]
        out.append({"kode": kode, "uraian": ur, "satuan": sat, "volume": vol, "hsp": hsp, "jumlah": vol * hsp,
                    "rinci": kode in tab})
    tot = sum(r["jumlah"] for r in out)
    for r in out:
        r["porsi"] = r["jumlah"] / tot * 100
    return out, tab


def cek_silang():
    s = volume_struktur()
    tiang = s["Tiang bor Ø800"]
    rerata = T107["tiang"] / T107["n_tiang"]
    a = [("Tiang bor (m³)", tiang["kotor"], T107["tiang"] + (tiang["n"] - T107["n_tiang"]) * rerata,
          f"T-107 6.176,2 + {tiang['n'] - T107['n_tiang']} tiang baru 7.3 × rerata {rerata:.2f}"),
         ("Pile cap (m³)", s["Pile cap"]["kotor"], T107["cap"] + CAP_E_LEBAR, "T-107 2.146,1 + perlebaran Cap E 7.3 (4,6 × 2,813 × 2,0)")]
    b = [(k + " (m³)", s[k]["kotor"], v, "T-84 (4.9)") for k, v in T84.items()]
    baris = []
    for kode, grup in (("T-119a", a), ("T-119b", b)):
        for n, x1, x2, ket in grup:
            d = (x1 / x2 - 1) * 100
            baris.append({"kode": kode, "besaran": n, "ifc": x1, "banding": x2, "selisih": d,
                          "lolos": abs(d) <= TOL[kode], "ket": ket})
    item, _ = daftar_pekerjaan()
    porsi = sum(r["porsi"] for r in item if r["rinci"])
    n_rinci = sum(r["rinci"] for r in item)
    return {"baris": baris, "pareto": {"porsi": porsi, "n_rinci": n_rinci, "n": len(item), "lolos": porsi >= TOL["T-120"]}}


# ------------------------------------------------------------------ keluaran
def idn(v, d=1):
    s = f"{v:,.{d}f}"
    return s.replace(",", "#").replace(".", ",").replace("#", ".")


def buat_excel(keluar=KELUAR):
    import openpyxl
    from format_dokumen import Lembar, set_font_bawaan
    s_vol = volume_struktur()
    v_ars, tidak = volume_arsitektur()
    item, tab = daftar_pekerjaan()
    cs = cek_silang()
    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)
    rp = "#,##0"
    # 1 Ringkasan
    s = Lembar(wb.create_sheet("Ringkasan"), 1, "Ringkasan volume dan AHSP Tahap 8a", [7, 50, 12, 16, 18, 20, 10])
    s.catatan(f"STATUS: {STATUS}. {LABEL}")
    s.catatan("Petunjuk: lembar 2-3 volume dari Qto IFC LOD 300 (STR 7.3, ARS 7.1); lembar 4 harga dasar (sel hijau dapat "
              "diubah); lembar 5 AHSP pekerjaan utama dengan rumus hidup; lembar 6 cek silang dan acuan. Harga satuan di "
              "bawah termasuk biaya umum + keuntungan 12 %. RAB resmi, SMKK, MEP, PPN di 8b. Hitung ulang: "
              ".venv\\Scripts\\python.exe skrip\\tahap8_volume.py")
    s.kosong()
    s.bagian("A", "Item pekerjaan dan uji Pareto (T-120)")
    tot = sum(r["jumlah"] for r in item)
    rows = [[i + 1, f"[{r['kode']}] {r['uraian']}", r["satuan"], round(r["volume"], 2), round(r["hsp"]), round(r["jumlah"]),
             round(r["porsi"], 2)] for i, r in enumerate(sorted(item, key=lambda r: -r["jumlah"]))]
    rows.append(["", "Jumlah biaya langsung + BTL bangunan dalam model 8a", "", "", "", round(tot), 100.0])
    s.tabel(["No", "Pekerjaan (kode AHSP / ringkas)", "Sat.", "Volume", "Harga satuan (Rp)", "Jumlah (Rp)", "Porsi (%)"],
            rows, rata=list("clcrrrr"), fmt=[None, None, None, "#,##0.00", rp, rp, "0.00"])
    p = cs["pareto"]
    s.catatan(f"T-120: {p['n_rinci']} dari {p['n']} item ({p['n_rinci'] / p['n'] * 100:.0f} %) ber-AHSP rinci mencakup "
              f"{idn(p['porsi'], 1)} % biaya (batas ≥ {TOL['T-120']:.0f} %): {'lolos' if p['lolos'] else 'gagal'}.")
    # 2 Volume struktur
    s = Lembar(wb.create_sheet("Volume Struktur"), 2, "Volume struktur dari IFC STR 7.3 (Qto BIMCraft)", [30, 8, 13, 13, 12, 12, 13, 13, 14])
    s.catatan("Qto = NetVolume (GrossVolume bila tidak ada), masih tumpang di joint; dipakai T-119. Bersih (RAB, K8-2): balok b(h − 0,20)(L − 0,75), kolom "
              "dikurangi b² × 0,20, tiang dikurangi masuk cap 0,15 m. Besi = rasio kg/m³ (K8-3) × bersih; tiang dari susunan 6.7.")
    rows = []
    for k, x in sorted(s_vol.items()):
        rows.append([k, x["n"], round(x.get("kotor", 0), 2), round(x.get("bersih", 0), 2), round(x.get("fc35", 0), 2),
                     round(x.get("fc30", 0), 2), round(x.get("bek_v", 0), 1), round(x.get("bek_h", 0), 1),
                     round(x.get("besi", 0) + x.get("baja", 0))])
    tot = [sum(r[i] for r in rows) for i in range(1, 9)]
    rows.append(["Jumlah"] + [round(t, 2) for t in tot])
    s.tabel(["Kelompok", "Jumlah unsur", "Beton Qto (m³)", "Beton bersih (m³)", "fc' 35 (m³)", "fc' 30 (m³)",
             "Bekisting vertikal (m²)", "Bekisting horizontal (m²)", "Besi/baja (kg)"], rows,
            rata=list("lrrrrrrrr"), fmt=[None, "0", "#,##0.00", "#,##0.00", "#,##0.00", "#,##0.00", "#,##0.0", "#,##0.0", rp])
    t = s_vol["Tiang bor Ø800"]
    s.catatan(f"Tiang: {t['n']} buah, panjang total {idn(t['panjang'], 1)} m' (rerata {idn(t['panjang'] / t['n'], 2)} m), "
              f"besi {idn(t['besi'] / t['bersih'], 1)} kg/m³. Galian cap {idn(s_vol['Pile cap']['galian'], 1)} m³, lantai kerja "
              f"{idn(s_vol['Pile cap']['lantai_kerja'], 1)} m³. Pintu lift di IFC STR (37) tidak dihitung (dihitung di ARS).")
    # 3 Volume arsitektur
    s = Lembar(wb.create_sheet("Volume Arsitektur"), 3, "Volume arsitektur dari IFC ARS 7.1 (Qto BIMCraft)", [10, 56, 10, 10, 16])
    s.tabel(["Kode", "Uraian", "Sat.", "Unsur", "Volume"],
            [[k, x["uraian"], x["satuan"], x["n"], round(x["volume"], 2)] for k, x in v_ars.items()],
            rata=list("cllrr"), fmt=[None, None, None, "0", "#,##0.00"])
    s.catatan("Tidak dihitung (K8-7): " + "; ".join(f"{k} {n}" for k, n in sorted(tidak.items())) + ". MEP di luar model: 8b.")
    # 4 Harga dasar
    s = Lembar(wb.create_sheet("Harga Dasar"), 4, "Harga dasar upah, bahan, alat [Asumsi: Jambi 2026]", [8, 60, 10, 18])
    s.tabel(["Kode", "Uraian", "Sat.", "Harga (Rp)"], [[k, u, sa, h] for k, (u, sa, h) in DASAR.items()],
            rata=list("clcr"), fmt=[None, None, None, rp], fill_kolom={3: "E2EFDA"})
    s.catatan("Harga belum survei (SE 47/2026 Lampiran I). Indeks IKK BPS 2025 Kota Jambi 95,03 dipakai di Tahap 3.8 sebagai pembanding.")
    # 5 AHSP (rumus hidup)
    s = Lembar(wb.create_sheet("AHSP"), 5, "Analisis harga satuan pekerjaan utama", [8, 58, 10, 12, 16, 18])
    s.catatan(f"Jumlah = koefisien × harga (rumus). D = Σ jumlah; E = biaya umum + keuntungan {BTL * 100:.0f} % × D "
              "(Permen PUPR 8/2023 Ps. 11 ayat (3) hal. 9); F = D + E.")
    for kode, (ur, sat, isi, cat) in tab.items():
        s.bagian(kode, f"{ur} (per {sat})")
        s.catatan(cat)
        r0 = s.baris + 1
        n = len(isi)
        K, H, J = s.kol(3), s.kol(4), s.kol(5)
        rows = [[k, DASAR[k][0], DASAR[k][1], c, DASAR[k][2], f"={K}{r0 + i}*{H}{r0 + i}"] for i, (k, c) in enumerate(isi)]
        rd = r0 + n
        rows += [["D", "Jumlah biaya langsung", "", "", "", f"=SUM({J}{r0}:{J}{rd - 1})"],
                 ["E", f"Biaya umum + keuntungan {BTL * 100:.0f} %", "", BTL, "", f"={K}{rd + 1}*{J}{rd}"],
                 ["F", "Harga satuan pekerjaan (D + E)", "", "", "", f"={J}{rd}+{J}{rd + 1}"]]
        s.tabel(["Kode", "Uraian", "Sat.", "Koefisien", "Harga (Rp)", "Jumlah (Rp)"], rows, rata=list("clcrrr"),
                fmt=[None, None, None, "0.0000", rp, rp], beku=False)
        s.kosong()
    # 6 Verifikasi dan acuan
    s = Lembar(wb.create_sheet("Verifikasi dan Acuan"), 6, "Cek silang volume dan acuan", [10, 30, 16, 16, 12, 10, 12, 46])
    s.tabel(["Kode", "Besaran", "IFC 7.3", "Pembanding", "Selisih (%)", "Batas (%)", "Hasil", "Keterangan"],
            [[b["kode"], b["besaran"], round(b["ifc"], 1), round(b["banding"], 1), round(b["selisih"], 2), TOL[b["kode"]],
              "lolos" if b["lolos"] else "gagal", b["ket"]] for b in cs["baris"]],
            rata=list("clrrrrcl"), fmt=[None, None, "#,##0.0", "#,##0.0", "0.00", "0", None, None])
    s.kosong()
    s.bagian("B", "Acuan")
    s.tabel(["No", "Acuan", "Dipakai untuk", "", "", "", "", "Status"], [
        [1, "Permen PUPR 8/2023 Ps. 11 ayat (3) hal. 9", "BTL 10-15 % (dipakai 12 %)", "", "", "", "", "acuan/publik"],
        [2, "SE Dirjen Binkon 47/2026 Lamp. II hal. 187-188", "produktivitas mesin bor E33", "", "", "", "", "acuan/publik"],
        [3, "Lampiran AHSP Cipta Karya (Permen PUPR 8/2023)", "koefisien bahan/upah", "", "", "", "", "pindaian, tidak terbaca: [Asumsi]"],
        [4, "SNI 2052:2017", "massa D13 1,04, D25 3,85 kg/m", "", "", "", "", "acuan/privat"],
        [5, "Survei harga SE 47/2026 Lamp. I", "harga dasar", "", "", "", "", "belum dilakukan: [Asumsi Jambi 2026]"],
    ], rata=list("clllllll"), beku=False)
    keluar.parent.mkdir(parents=True, exist_ok=True)
    wb.save(keluar)
    return keluar


def tulis_md(keluar=KELUAR.with_suffix(".md")):
    s_vol = volume_struktur()
    v_ars, tidak = volume_arsitektur()
    item, tab = daftar_pekerjaan()
    cs = cek_silang()
    tot = sum(r["jumlah"] for r in item)
    L = [f"# 8a Volume dan AHSP", "", f"Status: {STATUS}. {LABEL}", "",
         "Skrip `skrip/tahap8_volume.py`, Excel `08 RAB/8a Volume dan AHSP.xlsx` (6 lembar). Keputusan K8-1..K8-7: "
         "`08 RAB/00 Rencana Tahap 8.md`.", "", "## 1. Volume struktur (IFC STR 7.3)", "",
         "| Kelompok | Unsur | Beton Qto (m³) | Beton bersih (m³) | Bekisting (m²) | Besi/baja (kg) |", "|---|---:|---:|---:|---:|---:|"]
    for k, x in sorted(s_vol.items()):
        L.append(f"| {k} | {x['n']} | {idn(x.get('kotor', 0))} | {idn(x.get('bersih', 0))} | "
                 f"{idn(x.get('bek_v', 0) + x.get('bek_h', 0))} | {idn(x.get('besi', 0) + x.get('baja', 0), 0)} |")
    vb = sum(x.get("bersih", 0) for x in s_vol.values())
    bs = sum(x.get("besi", 0) for x in s_vol.values())
    L += ["", f"Beton bersih {idn(vb)} m³, besi {idn(bs / 1000)} t (rata-rata {idn(bs / vb)} kg/m³).", "",
          "## 2. Volume arsitektur (IFC ARS 7.1)", "", "| Kode | Uraian | Sat. | Volume |", "|---|---|---|---:|"]
    L += [f"| {k} | {x['uraian']} | {x['satuan']} | {idn(x['volume'])} |" for k, x in v_ars.items()]
    L += ["", "Tidak dihitung: " + "; ".join(f"{k} {n}" for k, n in sorted(tidak.items())) + ".", "",
          "## 3. AHSP pekerjaan utama", "", "| Kode | Pekerjaan | Sat. | Biaya langsung (Rp) | HSP + BTL 12 % (Rp) |", "|---|---|---|---:|---:|"]
    for k, (ur, sat, _, _) in tab.items():
        h = harga_satuan(k, tab)
        L.append(f"| {k} | {ur} | {sat} | {idn(h['langsung'], 0)} | {idn(h['hsp'], 0)} |")
    L += ["", f"## 4. Item pekerjaan dan Pareto (T-120)", "", "| Kode | Pekerjaan | Volume | Jumlah (Rp juta) | Porsi (%) |",
          "|---|---|---:|---:|---:|"]
    for r in sorted(item, key=lambda r: -r["jumlah"])[:15]:
        L.append(f"| {r['kode']} | {r['uraian']} | {idn(r['volume'])} {r['satuan']} | {idn(r['jumlah'] / 1e6)} | {idn(r['porsi'], 2)} |")
    p = cs["pareto"]
    L += ["", f"Total {len(item)} item: Rp {idn(tot / 1e9, 2)} miliar (biaya langsung + BTL, tanpa MEP, SMKK, PPN). "
          f"{p['n_rinci']} item AHSP rinci = {idn(p['porsi'], 1)} % biaya (batas ≥ {TOL['T-120']:.0f} %): "
          f"{'lolos' if p['lolos'] else 'gagal'}.", "", "## 5. Cek silang (T-119)", "",
          "| Kode | Besaran | IFC 7.3 | Pembanding | Selisih | Batas | Hasil |", "|---|---|---:|---:|---:|---:|---|"]
    for b in cs["baris"]:
        L.append(f"| {b['kode']} | {b['besaran']} | {idn(b['ifc'])} | {idn(b['banding'])} | {idn(b['selisih'], 2)} % | "
                 f"{TOL[b['kode']]:.0f} % | {'lolos' if b['lolos'] else 'gagal'} |")
    L += ["", "## 6. Catatan", "",
          "- Koefisien AHSP berlabel [Asumsi]: lampiran AHSP Permen PUPR 8/2023 di `acuan/` berupa pindaian (K8-6).",
          "- Harga dasar [Asumsi: Jambi 2026]; survei harga belum dilakukan.",
          "- T-119 memakai Qto NetVolume (lubang shaft dikurangi) karena T-84 dihitung dari geometri IFC yang juga mengurangi "
          "lubang. Perbandingan pertama dengan GrossVolume gagal untuk pelat (+6,7 %) dan dinding inti (+8,1 %); selisih yang "
          "tersisa (kolom +4,0 %, pelat +3,1 %, dinding +4,2 %, balok -2,4 %) sejalan dengan perubahan Tahap 5 (tangki, kolom "
          "800, pelat 350) dan 7.3 (K-01 6 balok dihapus, LB-1, rel chiller).",
          "- Besi tiang 6.7 (16 D25 + spiral D13 40/80) ±142 kg/m³ dan 31 % biaya 8a: periksa susunan spiral pada VE 8b.",
          "- Biaya 8a Rp 113 miliar tanpa MEP; pagu owner 12.000 m² × Rp 14 juta = Rp 168 miliar (TOR, `tahap3_biaya.PAGU_*`). "
          "Dengan MEP RS (±30-40 % [Asumsi]) total berisiko melewati pagu: dibahas di VE 8b.",
          "- Langkah berikutnya: 8b RAB (volume × HSP), SMKK, MEP, PPN, value engineering.", ""]
    keluar.write_text("\n".join(L), encoding="utf-8")
    return keluar


if __name__ == "__main__":
    print(buat_excel())
    print(tulis_md())
    for b in cek_silang()["baris"]:
        print(b["kode"], b["besaran"], round(b["ifc"], 1), round(b["banding"], 1), f"{b['selisih']:.2f} %", b["lolos"])
    print(cek_silang()["pareto"])
