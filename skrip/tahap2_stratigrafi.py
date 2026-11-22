"""Tahap 2 langkah 2.2: unit tanah, batas lapisan per titik, dan tebal lapisan organik.

Dipakai oleh tahap2_gambar_geoteknik.py (gambar A3) dan tahap2_lembar_stratigrafi.py (Excel).
Sumber: log bor BH-1 s.d. BH-8, CPTu-1 s.d. CPTu-8 (qt dari langkah 2.1), bor tangan HA-1 s.d. HA-10.
"""
from pathlib import Path

import numpy as np
import openpyxl

import tahap2_koreksi_data as kd

AKAR = Path(__file__).resolve().parents[1]
LAMA = AKAR / "01 Penyelidikan Tanah"
BARU = LAMA / "Penyelidikan Tambahan"

# kode: (nama, USCS, warna isi, pola arsir)
UNIT = {
    "U1": ("Urugan dan tanah penutup", "ML", "#d9c7a7", ""),
    "U2": ("Kerak lempung teguh", "CH", "#c99a6b", "-"),
    "U3": ("Gambut dan lempung organik", "Pt/OH", "#4a3b2f", "xxx"),
    "U4": ("Lempung lunak", "CH", "#9fb8a3", "-"),
    "U5": ("Pasir halus kelanauan, lepas-agak padat", "SP-SM", "#ecd98a", ".."),
    "U6": ("Lempung kaku-sangat kaku", "CH", "#7f9cb5", "-"),
    "U7": ("Pasir padat-sangat padat", "SP/SM", "#e2bf5b", "..."),
    "U8": ("Lempung keras", "CH", "#5f7891", "---"),
}
URUT = list(UNIT)


def unit_dari_teks(teks):
    """Golongkan uraian log ke unit (dan sub-unit pasir)."""
    t = teks.lower()
    if "urug" in t:
        return "U1", ""
    if "coklat kemerahan" in t:
        return "U2", ""
    if "organik" in t or "gambut" in t:
        return "U3", ""
    if "kebiruan" in t:
        return "U6", ""
    if "abu-abu terang" in t:
        return "U7", ""
    if t.startswith("pasir halus-sedang kelanauan"):
        return "U5", "b"
    if t.startswith("pasir"):
        return "U5", "a"
    if "keras" in t:
        return "U8", ""
    return "U4", ""


def _titik_sheet(path, sheet="Titik"):
    ws = openpyxl.load_workbook(path, data_only=True)[sheet]
    hasil = {}
    for r in ws.iter_rows(values_only=True):
        isi = [c for c in r if c is not None]
        if len(isi) >= 5 and isinstance(isi[0], str) and isinstance(isi[2] if isinstance(isi[1], str) else isi[1],
                                                                     (int, float)):
            if isinstance(isi[1], str):  # Titik, Jenis, x, y, elev, ...
                hasil[isi[0]] = dict(x=isi[2], y=isi[3], elev=isi[4], akhir=isi[5])
            else:  # Titik, x, y, elev, akhir, ...
                hasil[isi[0]] = dict(x=isi[1], y=isi[2], elev=isi[3], akhir=isi[4])
    return hasil


def _log_bor(path, bor):
    ws = openpyxl.load_workbook(path, data_only=True)["Log " + bor]
    lap = []
    for r in ws.iter_rows(values_only=True):
        isi = [c for c in r if c is not None]
        if len(isi) >= 3 and isinstance(isi[0], (int, float)) and isinstance(isi[1], (int, float)):
            teks = [x for x in isi if isinstance(x, str)][-1]
            u, sub = unit_dari_teks(teks)
            lap.append(dict(atas=float(isi[0]), bawah=float(isi[1]), unit=u, sub=sub, uraian=teks))
    if lap[0]["atas"] > 0:
        lap[0]["atas"] = 0.0  # log lama mulai 0,4-0,5 m: lapisan teratas dianggap dari muka tanah
    return lap


def _cptu_lapisan(data):
    """Batas lapisan dari qt dan Rf (kriteria sederhana, lihat CATATAN di Excel)."""
    z = np.array([d[0] for d in data])
    qt = np.array([d[1] + d[3] / 1000 * (1 - kd.A_KONUS) for d in data])
    rf = np.array([d[2] / (q * 1000) * 100 for d, q in zip(data, qt)])

    def rata_ke_bawah(i, tebal):
        j = np.searchsorted(z, z[i] + tebal)
        return qt[i:max(j, i + 1)].mean()

    lunak = int(np.argmax(qt < 0.3))
    org = np.where((z >= 0.9) & (z <= 5.5) & (rf > 5))[0]
    lap = [dict(atas=0.0, bawah=float(z[lunak]), unit="U2", sub="", uraian="Kerak (qt > 0,3 MPa)")]
    atas4 = float(z[lunak])
    if len(org) >= 4:
        a, b = float(z[org[0]]), float(z[org[-1]]) + 0.05
        lap[-1]["bawah"] = a
        lap.append(dict(atas=a, bawah=b, unit="U3", sub="", uraian="Rf > 5 %"))
        atas4 = b
    i5 = next(i for i in range(len(z)) if z[i] > 5 and rata_ke_bawah(i, 0.5) > 2)
    i6 = next(i for i in range(i5, len(z)) if z[i] > z[i5] + 3 and rata_ke_bawah(i, 1.0) < 2.5)
    lap.append(dict(atas=atas4, bawah=float(z[i5]), unit="U4", sub="", uraian="qt < 2 MPa"))
    i7 = next((i for i in range(i6, len(z)) if z[i] > 25 and rata_ke_bawah(i, 0.5) > 10), None)
    lap.append(dict(atas=float(z[i5]), bawah=float(z[i6]), unit="U5", sub="", uraian="qt > 2 MPa"))
    lap.append(dict(atas=float(z[i6]), bawah=float(z[i7]) if i7 else float(z[-1]), unit="U6", sub="",
                    uraian="qt < 2,5 MPa"))
    if i7:
        lap.append(dict(atas=float(z[i7]), bawah=float(z[-1]), unit="U7", sub="", uraian="qt > 10 MPa"))
    return lap, z, qt, rf


def _ha_lapisan():
    """Bor tangan: U1/U2 dari log (titik tengah tumpang tindih), U3 dari lembar Titik."""
    wb = openpyxl.load_workbook(BARU / "Pemetaan Gambut Bor Tangan.xlsx", data_only=True)
    titik = {}
    for r in wb["Titik"].iter_rows(values_only=True):
        isi = [c for c in r if c is not None]
        if isi and str(isi[0]).startswith("HA-") and isinstance(isi[1], (int, float)):
            dasar = isi[7] if len(isi) > 7 and isinstance(isi[7], (int, float)) else None
            titik[isi[0]] = dict(x=isi[1], y=isi[2], elev=isi[3], akhir=isi[4], org_atas=isi[6], org_dasar=dasar)
    log = {}
    for r in wb["Log Bor Tangan"].iter_rows(values_only=True):
        isi = [c for c in r if c is not None]
        if isi and str(isi[0]).startswith("HA-") and isinstance(isi[1], (int, float)):
            log.setdefault(isi[0], []).append((isi[1], isi[2], isi[3]))
    hasil = {}
    for n, t in titik.items():
        lg = log[n]
        b1 = (lg[0][1] + lg[1][0]) / 2  # batas urugan-kerak
        dasar = t["org_dasar"] if t["org_dasar"] is not None else t["akhir"]
        lap = [dict(atas=0.0, bawah=b1, unit="U1", sub="", uraian=lg[0][2]),
               dict(atas=b1, bawah=t["org_atas"], unit="U2", sub="", uraian=lg[1][2]),
               dict(atas=t["org_atas"], bawah=dasar, unit="U3", sub="", uraian="Gambut dan lempung organik")]
        if t["org_dasar"] is not None:
            lap.append(dict(atas=dasar, bawah=t["akhir"], unit="U4", sub="", uraian="Lempung lunak"))
        hasil[n] = dict(t, lapisan=lap, org_terbuka=t["org_dasar"] is None, log=lg)
    return hasil


def semua_titik():
    """Daftar titik: nama, jenis, x, y, elev, akhir, lapisan, (cptu: z, qt, rf)."""
    t_lama = _titik_sheet(LAMA / "Bor dan SPT.xlsx")
    t_baru = _titik_sheet(BARU / "Bor Tambahan dan SPT.xlsx")
    t_cptu = _titik_sheet(BARU / "CPTu.xlsx")
    hasil = []
    for bor in ["BH-1", "BH-2", "BH-3", "BH-4", "BH-5", "BH-6", "BH-7", "BH-8"]:
        lama = bor in t_lama
        info = (t_lama if lama else t_baru)[bor]
        lap = _log_bor((LAMA / "Bor dan SPT.xlsx") if lama else (BARU / "Bor Tambahan dan SPT.xlsx"), bor)
        hasil.append(dict(nama=bor, jenis="Bor", **info, lapisan=lap))
    cptu = kd.baca_cptu()
    for nama, data in cptu.items():
        lap, z, qt, rf = _cptu_lapisan(data)
        hasil.append(dict(nama=nama, jenis="CPTu", **t_cptu[nama], lapisan=lap, z=z, qt=qt, rf=rf))
    for nama, h in _ha_lapisan().items():
        hasil.append(dict(nama=nama, jenis="Bor tangan", x=h["x"], y=h["y"], elev=h["elev"], akhir=h["akhir"],
                          lapisan=h["lapisan"], org_terbuka=h["org_terbuka"], log=h["log"]))
    return hasil


def atas_unit(titik, unit):
    """Kedalaman atas unit di titik. None bila tidak tercapai; bila unit tidak ada tetapi unit di bawahnya
    tercapai, kembalikan atas unit berikutnya (tebal nol)."""
    for lp in titik["lapisan"]:
        if lp["unit"] == unit:
            return lp["atas"]
    k = URUT.index(unit)
    for lp in titik["lapisan"]:
        if URUT.index(lp["unit"]) > k:
            return lp["atas"]
    return None


def tebal_organik(titik):
    return sum(lp["bawah"] - lp["atas"] for lp in titik["lapisan"] if lp["unit"] == "U3")


def n60_per_unit():
    """{unit: [N60 ...]} dari uji SPT yang dipakai (langkah 2.1) dan lapisan log tiap bor."""
    er = {"BH-4": 86, "BH-5": 85, "BH-6": 81, "BH-7": 53, "BH-8": 53, "BH-1": 53, "BH-2": 53, "BH-3": 53}
    lap = {t["nama"]: t["lapisan"] for t in semua_titik() if t["jenis"] == "Bor"}
    hasil = {}
    for u in kd.baca_spt():
        if kd.status_spt(u)[0] != "Ya":
            continue
        zt = u["dari"] + 0.225
        for lp in lap[u["bor"]]:
            if lp["atas"] <= zt < lp["bawah"]:
                hasil.setdefault(lp["unit"], []).append(u["n"] * er[u["bor"]] / 60)
                break
    return hasil


if __name__ == "__main__":
    for t in semua_titik():
        print(t["nama"], t["jenis"], f"elev {t['elev']}", [(lp["unit"] + lp["sub"], round(lp["atas"], 2))
                                                            for lp in t["lapisan"]], f"org {tebal_organik(t):.2f}")
    for k, v in sorted(n60_per_unit().items()):
        print(k, len(v), f"{min(v):.1f}-{max(v):.1f} median {np.median(v):.1f}")
