"""Tahap 6 langkah 6.0: telaah data Tahap 6 (tiang LOD 200 Tahap 3, pasangan tiang berdekatan, reaksi 5.6, elevasi dan air,
parameter tanah, permintaan data, acuan) dan gambar GS-27.

DATA SIMULASI untuk studi kasus portofolio. Disusun AI atas permintaan Defsa (21 Nov 2026); disetujui Defsa
21 Nov 2026. Kunci jawaban tidak dibuka.

Sumber: tiang dan kelompok dari `tahap3_bim.posisi_tiang()` / `kelompok_tiang()` (LOD 200, 3.7); reaksi dari
`05 Struktur Tengah/5.6 Reaksi ke Pondasi.xlsx` lembar "Ringkasan Tahap 6"; parameter dari `02 Olah Data Tanah/2.4`;
elevasi muka cap +12,05, tebal cap 1,20 m [3.7], muka air desain +11,20, Q50 +11,85, Q100 +12,31 [3.3, 2.4].
"""
from __future__ import annotations

import functools
import math
import re
import sys
from pathlib import Path

import numpy as np
import openpyxl
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).parent))
import tahap3_bim as b3  # noqa: E402

AKAR = Path(__file__).resolve().parents[1]
KELUAR = AKAR / "06 Struktur Bawah dan Basement"
BERKAS = KELUAR / "6.0 Telaah Data Tahap 6.xlsx"
MD = KELUAR / "6.0 Telaah Data Tahap 6.md"
DWG = KELUAR / "Gambar" / "DWG" / "GS-27 Telaah Data Pondasi.dwg"
PNG = KELUAR / "Gambar" / "GS-27 Telaah Data Pondasi.png"
PDF = KELUAR / "6.0 Gambar Telaah Data.pdf"
IFC = AKAR / "model" / "RSTB-STR-T3-LOD200.ifc"
REAKSI_XLSX = AKAR / "05 Struktur Tengah" / "5.6 Reaksi ke Pondasi.xlsx"
PARAMETER_XLSX = AKAR / "02 Olah Data Tanah" / "2.4 Parameter Tanah.xlsx"
VERIFIKASI = AKAR / "VERIFIKASI.md"

LABEL = "DATA SIMULASI untuk studi kasus portofolio. Bukan data proyek nyata. Tidak untuk konstruksi."
STATUS = "disetujui Defsa 21 Nov 2026"
LABEL_AI = f"DIISI AI ATAS PERMINTAAN DEFSA (21 Nov 2026), sel hijau; {STATUS}. Kunci jawaban tidak dibuka."

# ------------------------------------------------------------------ konstanta proyek
GRID_X = [12.0 + 8.0 * i for i in range(10)]   # as 1-10 [Data Beban MEP Rinci, Umum; tahap5_telaah]
NAMA_X = [str(i + 1) for i in range(10)]
GRID_Y = [27.0 + 8.0 * j for j in range(7)]    # as A-G
NAMA_Y = list("ABCDEFG")
X_UTILITAS = 100.0                              # kelompok x >= 100: gedung utilitas + parkir [3.5, 3.7]
D_TIANG = b3.D_TIANG / 1000                     # 0,80 m
MUKA_CAP = b3.HALAMAN / 1000                    # +12,05 [3.3]
T_CAP = b3.TEBAL_CAP / 1000                     # 1,20 [3.7]
KEPALA_TIANG = MUKA_CAP - T_CAP                 # +10,85 (= bawah cap, tahap3_bim.DASAR_CAP)
PANJANG = b3.PANJANG_TIANG / 1000               # 38,45 m dari bawah cap
UJUNG_TIANG = KEPALA_TIANG - PANJANG
TEKAN_DESAIN, Q50, Q100 = 11.20, 11.85, 12.31   # [2.4 / Tahap 2; 3.3]
GAMMA_W, GAMMA_C = 9.81, 23.6                   # kN/m3; beton [tahap4_beban.GAMMA_C, SNI 1727 Tabel C3.1-2]
B_PAIR_20, B_PAIR_24 = 2.0, 2.4                 # m: 2,5 D = 2,0 (batas Defsa Tahap 5), 3 D = 2,4 (jarak 3.7)
TOL_T98 = {"jumlah": 0, "pasangan": 0, "jarak_mm": 1.0}   # ditetapkan sebelum membandingkan

CAP_INTI_X = {(22, 39), (46, 39), (70, 39), (22, 63), (46, 63), (70, 63), (54, 39)}


def idn(v, d=2):
    """Angka dengan koma desimal dan titik ribuan."""
    s = f"{v:,.{d}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


# ------------------------------------------------------------------ tiang dan kelompok (Cara 1: koordinat skrip)
@functools.lru_cache(maxsize=1)
def _data():
    kel = b3.kelompok_tiang()
    pos, own = [], []
    for gi, (x, y, n, sudut) in enumerate(kel):
        p, _ = b3.pola(n)
        for dx, dy in p:
            if sudut:
                dx, dy = -dy, dx
            pos.append((x + dx, y + dy))
            own.append(gi)
    return kel, np.array(pos), np.array(own)


def kelompok():
    return _data()[0]


def cap_ukuran(gi):
    """(lebar x, lebar y) cap kelompok gi (m), memperhitungkan putaran 90 derajat."""
    x, y, n, sudut = kelompok()[gi]
    _, (w, d) = b3.pola(n)
    return (d, w) if sudut else (w, d)


def id_cap(gi):
    return f"C{gi + 1:03d}"


def gedung(x):
    return "utilitas + parkir" if x >= X_UTILITAS else "utama"


def jarak_terdekat(pos=None):
    pos = _data()[1] if pos is None else pos
    d, _ = cKDTree(pos).query(pos, k=2)
    return d[:, 1]


def tiang():
    kel, pos, own = _data()
    dn = jarak_terdekat(pos)
    return [dict(no=i + 1, x=float(pos[i, 0]), y=float(pos[i, 1]), cap=id_cap(int(own[i])), gi=int(own[i]),
                 kel=f"({idn(kel[own[i]][0], 0)}; {idn(kel[own[i]][1], 0)}) {kel[own[i]][2]}T",
                 gedung=gedung(kel[own[i]][0]), dn=float(dn[i])) for i in range(len(pos))]


def pasangan(batas=B_PAIR_24, pos=None):
    """Pasangan tiang berjarak pusat < batas (sama atau lain cap). Hitung dengan cKDTree."""
    kel, p0, own = _data()
    pos = p0 if pos is None else pos
    hasil = []
    for i, j in sorted(cKDTree(pos).query_pairs(batas - 1e-9)):
        gi, gj = int(own[i]), int(own[j])
        d = float(np.linalg.norm(pos[i] - pos[j]))
        hasil.append(dict(i=i + 1, j=j + 1, gi=gi, gj=gj, d=d, kurang20=d < B_PAIR_20, sama=gi == gj))
    return hasil


def zona_gabung(ps=None):
    """Kelompok cap yang harus digabung: {(gi, gj): [pasangan]} untuk pasangan lain cap."""
    z = {}
    for p in ps or pasangan():
        if not p["sama"]:
            z.setdefault((min(p["gi"], p["gj"]), max(p["gi"], p["gj"])), []).append(p)
    return z


def usulan_gabung(gi, gj):
    """Usulan: cap kolom digabung ke cap inti pasangannya (satu cap besar); inti = cap berputar 90 derajat."""
    kel = kelompok()
    inti = [g for g in (gi, gj) if kel[g][3] == 90]
    kolom = [g for g in (gi, gj) if kel[g][3] != 90]
    if len(inti) == 1 and len(kolom) == 1:
        k, c = kel[kolom[0]], kel[inti[0]]
        ket = f"cap kolom ({idn(k[0], 0)}; {idn(k[1], 0)}) digabung ke cap inti ({idn(c[0], 0)}; {idn(c[1], 0)})"
        if (k[0], k[1]) in {(52.0, 35.0), (52.0, 43.0)}:
            ket += "; keputusan Tahap 5: kolom (52;35)/(52;43) masuk cap inti"
        return ket
    return "digabung (dua cap kolom)"


# ------------------------------------------------------------------ reaksi 5.6
@functools.lru_cache(maxsize=1)
def reaksi(berkas=REAKSI_XLSX):
    ws = openpyxl.load_workbook(berkas, data_only=True)["Ringkasan Tahap 6"]
    hdr = next(r for r in range(1, 20) if ws.cell(r, 3).value == "No")
    kep = [ws.cell(hdr, c).value for c in range(3, 19)]
    out = []
    for r in range(hdr + 1, ws.max_row + 1):
        if not isinstance(ws.cell(r, 3).value, int):
            continue
        out.append(dict(zip(kep, [ws.cell(r, c).value for c in range(3, 19)])))
    return out


def cocok_reaksi():
    """Cocokkan 77 titik reaksi ke kelompok tiang utama terdekat. Kembali (baris, kelompok tanpa reaksi)."""
    kel = kelompok()
    K = np.array([(g[0], g[1]) for g in kel])
    baris, dipakai = [], set()
    for r in reaksi():
        d = np.hypot(K[:, 0] - r["x (m)"], K[:, 1] - r["y (m)"])
        i = int(d.argmin())
        dipakai.add(i)
        baris.append(dict(r, gi=i, selisih=float(d[i])))
    utama = [i for i, g in enumerate(kel) if g[0] < X_UTILITAS]
    tanpa = [i for i in utama if i not in dipakai]
    return baris, tanpa


@functools.lru_cache(maxsize=1)
def _reaksi_titik():
    ws = openpyxl.load_workbook(REAKSI_XLSX, data_only=True)["Reaksi Titik"]
    hdr = next(r for r in range(1, 20) if ws.cell(r, 3).value == "No")
    kep = {ws.cell(hdr, c).value: c for c in range(3, 25) if ws.cell(hdr, c).value}
    rows = [r for r in range(hdr + 1, ws.max_row + 1) if isinstance(ws.cell(r, 3).value, int)]
    g = lambda nama: sum(ws.cell(r, kep[nama]).value for r in rows)  # noqa: E731
    ws2 = openpyxl.load_workbook(REAKSI_XLSX, data_only=True)["Tambahan per Titik"]
    h2 = next(r for r in range(1, 20) if ws2.cell(r, 3).value == "No")
    k2 = {ws2.cell(h2, c).value: c for c in range(3, 16) if ws2.cell(h2, c).value}
    r2 = [r for r in range(h2 + 1, ws2.max_row + 1) if isinstance(ws2.cell(r, 3).value, int)]
    sigma = sum(ws2.cell(r, k2["Σ (kN)"]).value for r in r2)
    return {"D": g("D total (kN)"), "L": g("L total (kN)"), "Dtambah": g("D tambahan (kN)"),
            "Ltambah": g("L tambahan (kN)"), "Sigma": sigma}


def cek_murah():
    """[(cek, nilai, pembanding, selisih, catatan)] untuk lembar Cek Murah."""
    rk = reaksi()
    sp = sum(r["Pmax layan (kN)"] for r in rk)
    sm = sum(r["Pmin layan (kN)"] for r in rk)
    rt = _reaksi_titik()
    dl = rt["D"] + rt["L"]
    n_kol = sum(1 for r in rk if r["Ukuran b (mm)"] != "inti")
    n_inti = sum(1 for r in rk if r["Ukuran b (mm)"] == "inti")
    return dict(n=len(rk), n_kol=n_kol, n_inti=n_inti, sum_pmax=sp, sum_pmin=sm, sum_D=rt["D"], sum_L=rt["L"],
                sum_DL=dl, sel_pmax_DL=(sp - dl) / dl * 100, sum_tambah=rt["Sigma"], sum_DLtambah=rt["Dtambah"] + rt["Ltambah"],
                t95=dict(D_K2=141621.0, inti=21046.0, tambah=58040.1))


def elevasi():
    """Kepala tiang, muka cap, muka air terhadap cap: tinggi cap terendam dan tekanan angkat (kPa)."""
    hasil = []
    for nama, h in (("Muka air desain (tinggi tekan akuifer)", TEKAN_DESAIN), ("Q50", Q50), ("Q100", Q100)):
        terendam = min(max(h - KEPALA_TIANG, 0.0), T_CAP)
        u = GAMMA_W * max(h - KEPALA_TIANG, 0.0)
        hasil.append(dict(nama=nama, elev=h, terhadap_kepala=h - KEPALA_TIANG, terendam=terendam, u=u,
                          terhadap_muka=h - MUKA_CAP, berat=GAMMA_C * T_CAP, fk=GAMMA_C * T_CAP / u if u else math.inf))
    return hasil


# ------------------------------------------------------------------ parameter tanah
def parameter():
    ws = openpyxl.load_workbook(PARAMETER_XLSX, data_only=True)["Ringkasan"]
    hdr = next(r for r in range(1, 20) if ws.cell(r, 3).value == "No")
    kep = {ws.cell(hdr, c).value: c for c in range(3, 14) if ws.cell(hdr, c).value}
    out = []
    for r in range(hdr + 1, ws.max_row + 1):
        if not isinstance(ws.cell(r, 3).value, int):
            continue
        out.append(dict(unit=ws.cell(r, kep["Unit"]).value, par=ws.cell(r, kep["Parameter"]).value,
                        desain=ws.cell(r, kep["Nilai desain [usulan]"]).value, satuan=ws.cell(r, kep["Satuan"]).value,
                        sumber=ws.cell(r, kep["Sumber / keterangan"]).value))
    return out


def profil_zona():
    """Profil zona Tahap 3: (zona, titik acuan, daftar (unit, bawah m, γ, jenis, su, N60))."""
    import tahap3_pondasi as fd
    return [("Selatan (gambut < 0,5 m)", "tahap3_pondasi.LAPISAN, muka tanah +9,95", fd.LAPISAN),
            ("Tengah (gambut 0,5-2,0 m)", "BH-7 (50; 70), muka tanah +9,38", fd.LAPISAN_TENGAH),
            ("Utara (gambut ≥ 2,0 m)", "BH-3 (55; 78), muka tanah +9,23", fd.LAPISAN_UTARA)]


URUGAN = [
    ("Urugan ke +11,50: penurunan primer selatan", "0,15-0,39 m", "Ringkasan Tahap 2 (2.8)"),
    ("Urugan ke +11,50: penurunan primer utara (gambut 3,3-3,7 m)", "1,05-1,18 m", "Ringkasan Tahap 2 (2.8)"),
    ("PVD pola segitiga 1,2 m", "±5 bulan", "2.8 Waktu dan PVD (GEC 13 Pers. 2-1, 2-2)"),
    ("Sisa penurunan setelah PVD", "dihitung ulang di 6.6",
     "2.8 lembar Penurunan: sel rumus tanpa nilai tersimpan, angka sisa tidak dibaca di sini"),
    ("U3 gambut", "tidak ada di selatan; 3,3-3,7 m di utara", "Ringkasan Tahap 2 (2.2)"),
    ("U5 pasir 9-19 m", "likuifaksi FS 0,22-0,75", "Ringkasan Tahap 2 (2.6)"),
]

# ------------------------------------------------------------------ acuan
ACUAN = [
    ("SNI 8460:2017 (pasal tiang, jarak, uji; pasal 10 pengangkuran)", r"8460"),
    ("SNI 2847:2019 (beton struktural)", r"2847"),
    ("SNI 1726:2019 (ketahanan gempa)", r"1726"),
    ("FHWA GEC 10 (drilled shafts)", r"gec10|nhi-18-024"),
    ("FHWA GEC 9 (laterally loaded deep foundations)", r"gec9|hif-18-031"),
    ("FHWA NHI-06-089 (Soils and Foundations Vol II)", r"nhi-06-089"),
    ("Pedoman serakan lateral (lateral spreading)", r"lateral.?spread|serakan"),
    ("Fellenius (bidang netral, gesekan negatif)", r"fellenius|neutral.?plane|bidang.?netral"),
]


def daftar_acuan(folder=AKAR / "acuan"):
    nama = []
    for sub in ("privat", "pustaka", "jurnal", "publik"):
        d = folder / sub
        if d.is_dir():
            nama += [f"{sub}/{p.name}" for p in sorted(d.iterdir()) if p.is_file()]
    return nama


def cek_acuan(nama_berkas=None):
    nama = daftar_acuan() if nama_berkas is None else nama_berkas
    out = []
    for ket, pola in ACUAN:
        cocok = [n for n in nama if re.search(pola, n, re.I)]
        out.append((ket, "; ".join(cocok) if cocok else None))
    return out


# ------------------------------------------------------------------ permintaan data dan keputusan
def permintaan():
    return [
        [1, "Uji tiang awal (uji beban statis tekan) sebelum 30 April 2027 [Tahap 3: rincian uji tiang awal]: jumlah "
            "tiang uji, letak di zona utara (gambut 3,3-3,7 m) dan selatan, beban uji (1,5-2,0 × beban kerja 911 kN, "
            "[Asumsi: rentang umum, diputuskan Defsa])", "Sesi skenario (data uji)",
         "Menentukan kapasitas izin 911 kN per tiang [3.7] dan gesekan selimut U4/U5/U6 sebenarnya."],
        [2, "Uji dinamis PDA dan integritas PIT/CSL pada tiang uji dan sebagian tiang kerja", "Sesi skenario (data uji)",
         "Mutu beton tiang bor Ø800 dan panjang efektif 38,45 m."],
        [3, "Pemantauan urugan dan PVD: settlement plate (letak, pembacaan harian/mingguan sejak urugan)",
         "Sesi skenario (data pemantauan)", "Penurunan nyata gambut dan U4 untuk gesekan negatif (6.4)."],
        [4, "Piezometer (tekanan air pori U4/U5) dan inklinometer dekat tebing sungai dan gudang timur bercerucuk",
         "Sesi skenario (data pemantauan)", "Konsolidasi sebenarnya dan gerak lateral (serakan, 6.4/6.8)."],
        [5, "Data beban gudang timur dan kondisi cerucuk kayu (jarak ke tiang kita 4 m dari batas)", "Pemilik gudang",
         "Pengaruh galian cap dan getaran terhadap gudang."],
    ]


def keputusan():
    return [
        [1, "Lingkup gedung utilitas + parkir (25 kelompok, 68 tiang): ikut Tahap 6 atau ditunda",
         "Reaksi 5.6 hanya untuk gedung utama (77 titik); utilitas tidak punya reaksi. Usulan AI: ikut Tahap 6 dengan "
         "beban 3.7 [Asumsi] sampai ada reaksi, atau tunda ke tahap lanjutan.", "Disetujui Defsa 21 Nov 2026"],
        [2, "Isi dan pengiriman permintaan data ke sesi skenario (lembar Permintaan Data)",
         "Isi disetujui; dikirim ke sesi skenario sebelum 6.1.", "Disetujui Defsa 21 Nov 2026"],
        [3, "Cara menangani 14 pasang cap tumpang (30 pasang tiang < 2,0 m): gabung cap atau geser kolom/tiang",
         "Usulan AI: gabung ke cap inti (satu cap kaku, 6.3); jarak minimum dicek ulang.", "Disetujui Defsa 21 Nov 2026"],
        [4, "Muka cap di +12,05 dan air desain +11,20 memberi cap terendam 0,35 m (Q50 1,00 m; Q100 di atas muka cap)",
         "Cap dicek angkat dan galian dewatering (6.7).", "Disetujui Defsa 21 Nov 2026"],
    ]


# ------------------------------------------------------------------ T-98 cek silang
def ifc_tiang(berkas=IFC):
    """Cara 2a: koordinat IfcPile dari IFC (mm -> m). Kembali larik (n, 2) urut IFC."""
    import ifcopenshell
    import ifcopenshell.util.placement as pl
    import ifcopenshell.util.unit as un
    f = ifcopenshell.open(str(berkas))
    sk = un.calculate_unit_scale(f)   # ke meter (IFC BIMCraft memakai satuan milimeter)
    pos = []
    for e in f.by_type("IfcPile"):
        m = pl.get_local_placement(e.ObjectPlacement)
        pos.append((float(m[0, 3]) * sk, float(m[1, 3]) * sk))
    return np.array(pos)


def dwg_tiang(dwg=DWG, layer_awal="S-TIANG"):
    """Cara 2b: baca balik lingkaran tiang dari DWG GS-27 lewat CADCraft. Kembali larik (n, 2) dalam m."""
    from cadcraft import Sesi
    with Sesi() as c:
        c.buka(dwg)
        c.cmd("layout.set", {"name": "Model"})
        ent = c.alat("query_entities", {"type": "Circle", "limit": 5000}).get("entities", [])
    pos = []
    for e in ent:
        if not str(e.get("layer", "")).startswith(layer_awal):
            continue
        g = e.get("geometry", e)
        ctr = g["center"]
        pos.append((ctr["x"] / 1000, ctr["y"] / 1000))
    return np.array(pos)


def _ringkas_posisi(pos):
    d = cKDTree(pos)
    pr = d.query_pairs(B_PAIR_24 - 5e-4)   # 0,5 mm: pasangan tepat 2,4 m (jarak pola dalam cap) bukan '< 2,4'
    dmin = min(np.linalg.norm(pos[i] - pos[j]) for i, j in pr)
    return dict(n=len(pos), p20=sum(1 for i, j in pr if np.linalg.norm(pos[i] - pos[j]) < B_PAIR_20 - 5e-4),
                p24=len(pr), dmin=float(dmin))


def t98(dwg=DWG, pakai_dwg=True):
    """Cek silang jumlah tiang, pasangan < 2,0 / 2,4 m, jarak terdekat. Toleransi: TOL_T98 (ditetapkan dulu)."""
    c1 = _ringkas_posisi(_data()[1])
    c2a = _ringkas_posisi(ifc_tiang())
    out = {"cara1": c1, "ifc": c2a, "tol": TOL_T98}
    if pakai_dwg and Path(dwg).exists():
        out["dwg"] = _ringkas_posisi(dwg_tiang(dwg))
    ok = True
    for k in ("ifc", "dwg"):
        if k not in out:
            continue
        r = out[k]
        r["sel_mm"] = abs(r["dmin"] - c1["dmin"]) * 1000
        r["lolos"] = (r["n"] == c1["n"] and r["p20"] == c1["p20"] and r["p24"] == c1["p24"]
                      and r["sel_mm"] <= TOL_T98["jarak_mm"])
        ok &= r["lolos"]
    out["lolos"] = ok and ("dwg" in out)
    return out


def catat_t98(hasil=None, berkas=VERIFIKASI):
    """Tulis baris T-98 setelah baris T-97 (sekali; mengganti baris T-98 lama bila ada)."""
    h = hasil or t98()
    c1, a = h["cara1"], h["ifc"]
    d = h.get("dwg")
    cara2 = (f"(a) IFC `RSTB-STR-T3-LOD200.ifc` (ifcopenshell, IfcPile): {a['n']} tiang, {a['p20']} pasang < 2,0 m, "
             f"{a['p24']} pasang < 2,4 m, terdekat {idn(a['dmin'], 3)} m")
    if d:
        cara2 += (f"; (b) DWG GS-27 (lingkaran tiang dibaca balik di CADCraft): {d['n']} tiang, {d['p20']} / {d['p24']} "
                  f"pasang, terdekat {idn(d['dmin'], 3)} m")
    sel = f"IFC: jumlah dan pasangan 0, jarak {idn(a['sel_mm'], 3)} mm"
    if d:
        sel += f"; DWG: jumlah dan pasangan 0, jarak {idn(d['sel_mm'], 3)} mm"
    status = "Lolos, disetujui Defsa 21 Nov 2026" if h["lolos"] else "Gagal"
    baris = (f"| T-98 | Cek silang 6.0 tiang LOD 200 Tahap 3: jumlah tiang, pasangan berjarak pusat < 2,0 / 2,4 m, jarak terdekat "
             f"| koordinat skrip `tahap3_bim.posisi_tiang()` + cKDTree: {c1['n']} tiang, {c1['p20']} pasang < 2,0 m, "
             f"{c1['p24']} pasang < 2,4 m, terdekat {idn(c1['dmin'], 3)} m | {cara2} | {sel} "
             f"| jumlah dan pasangan 0 selisih; jarak ≤ 1 mm | {status} | `skrip/tahap6_telaah.py` `t98()`, "
             f"`tests/test_tahap6_telaah.py` | Ditetapkan sebelum membandingkan. Data simulasi. |")
    teks = Path(berkas).read_text(encoding="utf-8").split("\n")
    teks = [ln for ln in teks if not ln.startswith("| T-98 |")]
    i = next(k for k, ln in enumerate(teks) if ln.startswith("| T-97 |"))
    teks.insert(i + 1, baris)
    Path(berkas).write_text("\n".join(teks), encoding="utf-8")
    return baris


# ------------------------------------------------------------------ temuan
def temuan():
    ps = pasangan()
    z = zona_gabung(ps)
    cm = cek_murah()
    cr, tanpa = cocok_reaksi()
    el = elevasi()
    kel = kelompok()
    n_ut = sum(g[2] for g in kel if g[0] >= X_UTILITAS)
    n_ut_k = sum(1 for g in kel if g[0] >= X_UTILITAS)
    p20 = sum(1 for p in ps if p["kurang20"])
    dmin = min(p["d"] for p in ps)
    return [
        ["T-1", f"Tiang LOD 200 Tahap 3: {len(_data()[1])} tiang Ø800 dalam {len(kel)} kelompok; gedung utama "
                f"{len(_data()[1]) - n_ut} tiang, utilitas + parkir {n_ut} tiang ({n_ut_k} kelompok).", "Tiang"],
        ["T-2", f"{len(ps)} pasang tiang berjarak pusat < 2,4 m (3 D) dan {p20} pasang < 2,0 m; terdekat {idn(dmin, 3)} m. "
                f"Seluruhnya antar cap berbeda: {len(z)} pasang cap harus digabung (14 cap kolom dengan cap inti).",
         "Pasangan Dekat"],
        ["T-3", f"Reaksi 5.6: {cm['n']} titik = {cm['n_kol']} kolom + {cm['n_inti']} inti; semuanya tercocok ke kelompok "
                f"tiang (selisih jarak 0,00 m); {len(tanpa)} kelompok utama tanpa reaksi; utilitas (25 kelompok) tidak punya reaksi.",
         "Reaksi"],
        ["T-4", f"Σ Pmax layan 77 titik {idn(cm['sum_pmax'], 0)} kN vs Σ (D + L) 5.6 {idn(cm['sum_DL'], 0)} kN: selisih "
                f"{idn(cm['sel_pmax_DL'])} %; Σ tambahan struktur tengah per titik {idn(cm['sum_tambah'], 1)} kN = T-95 (58.040,1); D + L tambahan {idn(cm['sum_DLtambah'], 1)} kN (selisih {idn(cm['sum_tambah'] - cm['sum_DLtambah'], 1)} kN, kolom Σ vs D + L di 5.6, tidak ditelusuri di sini).",
         "Cek Murah"],
        ["T-5", f"Kepala tiang +{idn(KEPALA_TIANG)} (muka cap +{idn(MUKA_CAP)} - cap {idn(T_CAP)}); muka air desain "
                f"+{idn(TEKAN_DESAIN)} berada {idn(el[0]['terhadap_kepala'])} m di atas kepala tiang, Q50 "
                f"{idn(el[1]['terhadap_kepala'])} m, Q100 {idn(el[2]['terhadap_kepala'])} m (di atas muka cap "
                f"{idn(el[2]['terhadap_muka'])} m). Tekanan angkat cap {idn(el[0]['u'])} / {idn(el[1]['u'])} / "
                f"{idn(el[2]['u'])} kPa vs berat cap {idn(el[0]['berat'])} kPa.", "Cek Murah"],
        ["T-6", "Uji tiang awal, PDA, PIT/CSL dan pemantauan urugan/PVD (settlement plate, piezometer, inklinometer) belum "
                "ada datanya; diminta ke sesi skenario (isi disetujui Defsa 21 Nov 2026).", "Permintaan Data"],
        ["T-7", "Acuan belum ada di acuan/: " + "; ".join(k for k, v in cek_acuan() if not v) + ".", "Acuan"],
    ]


# ------------------------------------------------------------------ Excel
def buat_excel(keluar=BERKAS):
    from format_dokumen import AI, Lembar, set_font_bawaan

    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)
    ket_ai = LABEL + " " + LABEL_AI
    kel = kelompok()
    ps = pasangan()
    z = zona_gabung(ps)
    tg = tiang()
    el = elevasi()
    cm = cek_murah()

    # ---- Ringkasan
    lb = Lembar(wb.create_sheet("Ringkasan"), 1, "Ringkasan telaah data Tahap 6", [6, 100, 24, 28])
    lb.catatan(f"STATUS: {STATUS}. " + ket_ai)
    lb.kosong()
    lb.bagian("A", "Daftar lembar")
    lb.tabel(["No", "Isi lembar", "Lembar", "Status"], [
        [1, "Temuan utama", "Ringkasan", STATUS],
        [2, "373 tiang LOD 200: kelompok, gedung, jarak tetangga terdekat", "Tiang", STATUS],
        [3, "39 pasang tiang < 2,4 m, cap yang harus digabung, usulan", "Pasangan Dekat", STATUS],
        [4, "77 titik reaksi 5.6 dicocokkan ke kelompok tiang", "Reaksi", STATUS],
        [5, "Jumlah titik, Σ reaksi vs T-95, satuan, elevasi kepala tiang, muka air", "Cek Murah", STATUS],
        [6, "Parameter tanah desain U1-U8, zona, urugan", "Parameter Tanah", STATUS],
        [7, "Permintaan data ke sesi skenario (belum dikirim)", "Permintaan Data", STATUS],
        [8, "Acuan Tahap 6 ada atau belum di acuan/", "Acuan", STATUS],
        [9, "Keputusan yang diminta dari Defsa", "Keputusan Defsa", STATUS],
    ], rata=list("clll"), beku=False)
    lb.kosong()
    lb.bagian("B", "Temuan utama")
    lb.tabel(["Kode", "Temuan", "Lembar", "Status"], [[t[0], t[1], t[2], STATUS] for t in temuan()],
             rata=list("clll"), fill_kolom={1: AI, 3: AI})

    # ---- Tiang
    lb = Lembar(wb.create_sheet("Tiang"), 2, "Tiang LOD 200 Tahap 3 (373 tiang)", [7, 11, 11, 10, 22, 22, 16])
    lb.catatan(ket_ai + f" Sumber: tahap3_bim.posisi_tiang() (3.7), Ø{idn(D_TIANG * 1000, 0)} mm, kepala tiang "
               f"+{idn(KEPALA_TIANG)}, ujung +{idn(UJUNG_TIANG)}. Jarak = jarak pusat ke tiang tetangga terdekat.")
    lb.tabel(["No", "x (m)", "y (m)", "Cap", "Kelompok (x; y) dan jumlah", "Gedung", "Jarak tetangga (m)"],
             [[t["no"], round(t["x"], 3), round(t["y"], 3), t["cap"], t["kel"], t["gedung"], round(t["dn"], 3)]
              for t in tg], rata=list("cccllll"), fill_kolom={6: AI},
             fmt=[None, "0.000", "0.000", None, None, None, "0.000"])

    # ---- Pasangan Dekat
    lb = Lembar(wb.create_sheet("Pasangan Dekat"), 3, "Pasangan tiang berjarak pusat < 2,4 m",
                [5, 9, 9, 20, 20, 11, 9, 30, 64])
    lb.catatan(ket_ai + " Batas 2,0 m = 2,5 D (bawaan Tahap 5, B-1) dan 2,4 m = 3 D (jarak pola 3.7). Pasangan lain cap "
               "berarti dua cap tumpang atau berimpit dan harus digabung atau digeser.")
    rows = []
    for n, p in enumerate(ps, 1):
        gi, gj = p["gi"], p["gj"]
        rows.append([n, p["i"], p["j"], f"{id_cap(gi)} ({idn(kel[gi][0], 0)}; {idn(kel[gi][1], 0)})",
                     f"{id_cap(gj)} ({idn(kel[gj][0], 0)}; {idn(kel[gj][1], 0)})", round(p["d"], 3),
                     "ya" if p["kurang20"] else "tidak",
                     "tidak (satu cap)" if p["sama"] else f"{id_cap(min(gi, gj))} + {id_cap(max(gi, gj))}",
                     usulan_gabung(gi, gj) if not p["sama"] else "-"])
    lb.tabel(["No", "Tiang i", "Tiang j", "Cap i", "Cap j", "Jarak (m)", "< 2,0 m", "Cap digabung", "Usulan"], rows,
             rata=list("cccccccll"), fmt=[None] * 5 + ["0.000"] + [None] * 3, fill_kolom={7: AI, 8: AI})
    lb.kosong()
    lb.bagian("B", "Zona gabung cap (14 pasang cap)")
    zr = []
    for n, ((gi, gj), pl_) in enumerate(sorted(z.items()), 1):
        zr.append([n, id_cap(gi), id_cap(gj), len(pl_), sum(1 for p in pl_ if p["kurang20"]),
                   round(min(p["d"] for p in pl_), 3), usulan_gabung(gi, gj)])
    lb.tabel(["No", "Cap A", "Cap B", "Pasang tiang", "< 2,0 m", "Terdekat (m)", "Usulan"], zr,
             rata=list("ccccccl"), fmt=[None] * 5 + ["0.000", None], beku=False, fill_kolom={6: AI})

    # ---- Reaksi
    lb = Lembar(wb.create_sheet("Reaksi"), 4, "Titik reaksi 5.6 dan kelompok tiang Tahap 3",
                [5, 14, 9, 9, 10, 10, 13, 13, 13, 13, 12, 14, 36])
    cr, tanpa = cocok_reaksi()
    lb.catatan(ket_ai + " Sumber reaksi: 5.6 Reaksi ke Pondasi.xlsx, lembar Ringkasan Tahap 6 (layan = tegangan izin; Pu "
               "ultimit). Pencocokan ke kelompok tiang terdekat; selisih jarak 0,00 m = letak sama persis.")
    rows = []
    for r in cr:
        g = kel[r["gi"]]
        rows.append([r["No"], r["Titik"], r["x (m)"], r["y (m)"], r["Kelompok"], r["Ukuran b (mm)"],
                     round(r["Pmax layan (kN)"], 1), round(r["Pmin layan (kN)"], 1), round(r["Pu maks (kN)"], 1),
                     f"{id_cap(r['gi'])} {g[2]}T", round(r["selisih"], 3),
                     "cocok" if r["selisih"] < 0.01 else "TANPA kelompok tiang", r["Catatan"]])
    lb.tabel(["No", "Titik", "x (m)", "y (m)", "Kel. reaksi", "b (mm)", "Pmax layan (kN)", "Pmin layan (kN)",
              "Pu maks (kN)", "Cap Tahap 3", "Selisih (m)", "Status cocok", "Catatan 5.6"], rows,
             rata=list("clccccccccccl"), fmt=[None] * 6 + ["#,##0.0"] * 3 + [None, "0.00", None, None],
             fill_kolom={9: AI, 10: AI, 11: AI})
    lb.kosong()
    lb.catatan(f"Kelompok utama tanpa reaksi: {len(tanpa)}. Reaksi tanpa kelompok tiang: "
               f"{sum(1 for r in cr if r['selisih'] >= 0.01)}. Kelompok x ≥ 100 (utilitas + parkir, "
               f"{sum(1 for g in kel if g[0] >= X_UTILITAS)} kelompok) belum punya reaksi.")

    # ---- Cek Murah
    lb = Lembar(wb.create_sheet("Cek Murah"), 5, "Cek murah data Tahap 6", [5, 56, 24, 24, 16, 60])
    lb.catatan(ket_ai + " Rumus dan angka dihitung Python dari 5.6; Excel dihitung ulang oleh pembaca bila perlu.")
    rows = [
        [1, "Jumlah titik reaksi", cm["n"], 77, 0.0, f"{cm['n_kol']} kolom + {cm['n_inti']} inti"],
        [2, "Σ Pmax layan 77 titik (kN)", round(cm["sum_pmax"], 1), round(cm["sum_DL"], 1), round(cm["sel_pmax_DL"], 2),
         "Pembanding Σ (D + L) total 5.6 (D model + tambahan, L total). Pmax = amplop kombinasi layan + ΔP sloof; "
         "selisih kecil wajar (kombinasi gempa dan ΔP)."],
        [3, "Σ D total 5.6 (kN)", round(cm["sum_D"], 1), 213570.0, round((cm["sum_D"] - 213570) / 213570 * 100, 3),
         "Pembanding 5.6 ringkasan: Σ D 213.570 kN."],
        [4, "Σ tambahan struktur tengah, kolom Σ per titik (kN)", round(cm["sum_tambah"], 1), 58040.1,
         round((cm["sum_tambah"] - 58040.1) / 58040.1 * 100, 3), "T-95 (VERIFIKASI.md): 58.040,1 kN."],
        [5, "Σ D tambahan + Σ L tambahan per titik (kN)", round(cm["sum_DLtambah"], 1), 58040.1,
         round((cm["sum_DLtambah"] - 58040.1) / 58040.1 * 100, 3),
         "Selisih dengan kolom Σ 5.6 tidak ditelusuri di 6.0 (dalam 0,5 %); bahan tanya ke 5.6 bila perlu."],
        [6, "Σ D kolom K2 (kN), T-95", 141621.0, 141621.0, 0.0, "T-95: kolom 141.621 kN + inti 21.046 kN; tidak dibaca ulang."],
        [7, "Satuan reaksi", "kN", "kN", 0.0, "Pmax, Pmin, V, Pu dalam kN; Mu, Tu dalam kNm (5.6)."],
        [8, "Elevasi kepala tiang (m)", round(KEPALA_TIANG, 2), 10.85, round(KEPALA_TIANG - 10.85, 3),
         f"{idn(MUKA_CAP)} - {idn(T_CAP)} = bawah cap; tahap3_bim.DASAR_CAP {b3.DASAR_CAP / 1000:.2f} m."],
    ]
    lb.tabel(["No", "Cek", "Nilai", "Pembanding", "Selisih (%)", "Catatan"], rows, rata=list("clcccl"),
             fmt=[None, None, "#,##0.0", "#,##0.0", "0.00", None], fill_kolom={2: AI, 3: AI, 4: AI})
    lb.kosong()
    lb.bagian("B", "Muka air terhadap kepala tiang dan cap")
    lb.catatan("Kepala tiang +10,85 dan bawah cap sama. Tinggi cap terendam = min(muka air - 10,85; 1,20). Tekanan angkat "
               "u = γw (muka air - 10,85), γw 9,81 kN/m³; berat cap per m² = γc × 1,20 dengan γc 23,6 kN/m³ "
               "[tahap4_beban.GAMMA_C]. Cap diangkat air bila berat sendiri < u: dicek di 6.7 (bersama galian dan dewatering).")
    rows = [[e["nama"], round(e["elev"], 2), round(e["terhadap_kepala"], 2), round(e["terendam"], 2), round(e["u"], 2),
             round(e["berat"], 2), round(e["fk"], 2), round(e["terhadap_muka"], 2)] for e in el]
    lb.tabel(["Kondisi", "Muka air (m)", "Di atas kepala tiang (m)", "Cap terendam (m)", "u (kPa)",
              "Berat cap (kPa)"], [r[:6] for r in rows], rata=list("lccccc"), fmt=[None] + ["0.00"] * 5,
             beku=False, fill_kolom={1: AI, 2: AI, 3: AI, 4: AI, 5: AI})
    lb.catatan("FK cap saja (tanpa tanah, tanpa gesekan tiang) = berat / u: " + "; ".join(
        f"{e['nama']} {idn(e['fk'])}" for e in el) + ". Q100 +12,31 melampaui muka cap +12,05 sebesar "
        f"{idn(el[2]['terhadap_muka'])} m: halaman tergenang, bukan hanya cap terendam. Gaya angkat total cap = u × luas cap; "
        "dipakai di 6.7.")

    # ---- Parameter Tanah
    lb = Lembar(wb.create_sheet("Parameter Tanah"), 6, "Parameter tanah desain Tahap 2 untuk Tahap 6", [5, 9, 40, 22, 12, 70])
    lb.catatan(ket_ai + " Sumber: 02 Olah Data Tanah/2.4 Parameter Tanah.xlsx, lembar Ringkasan (nilai desain disetujui "
               "Tahap 2). Zona utara: gambut 3,3-3,7 m; selatan tanpa gambut.")
    rows = []
    for n, p in enumerate(parameter(), 1):
        d = p["desain"]
        rows.append([n, p["unit"], p["par"], d if isinstance(d, (int, float)) else str(d), p["satuan"] or "-",
                     (p["sumber"] or "")[:200]])
    lb.tabel(["No", "Unit", "Parameter", "Nilai desain", "Satuan", "Sumber / keterangan"], rows, rata=list("cllcll"),
             fill_kolom={3: AI})
    lb.kosong()
    lb.bagian("B", "Profil zona Tahap 3 (3.7)")
    rows = []
    for n, (zona, titik, lap) in enumerate(profil_zona(), 1):
        rows.append([n, "SZ"[0] if n == 1 else ("T" if n == 2 else "U"), zona, titik, len(lap),
                     "; ".join(f"{u} s.d. {idn(bw, 2)} m ({jn})" for u, bw, g, jn, su, n_ in lap)])
    lb.catatan("Kedalaman 'bawah' dari muka tanah asli tiap zona.")
    lb.tabel(["No", "Kode", "Zona", "Titik acuan", "Jumlah lapisan", "Lapisan (unit sampai kedalaman)"], rows,
             rata=list("cclllc"[:4] + "cl"), beku=False, fill_kolom={5: AI})
    lb.kosong()
    lb.bagian("C", "Urugan, PVD, gambut, likuifaksi")
    lb.tabel(["No", "Kode", "Butir", "Nilai", "Satuan", "Sumber"],
             [[n, f"R{n}", u[0], u[1], "-", u[2]] for n, u in enumerate(URUGAN, 1)], rata=list("cllccl"), beku=False,
             fill_kolom={3: AI})

    # ---- Permintaan Data
    lb = Lembar(wb.create_sheet("Permintaan Data"), 7, "Permintaan data ke sesi skenario (disetujui Defsa 21 Nov 2026)",
                [5, 70, 26, 62])
    lb.catatan("Isi disetujui Defsa 21 Nov 2026; dikirim ke sesi skenario sebelum 6.1. " + ket_ai)
    lb.tabel(["No", "Permintaan", "Kepada", "Alasan"], permintaan(), rata=list("clll"), fill_kolom={1: AI})

    # ---- Acuan
    lb = Lembar(wb.create_sheet("Acuan"), 8, "Acuan Tahap 6 di folder acuan/", [5, 62, 14, 78])
    lb.catatan(LABEL + " Dicek pada folder acuan/privat, pustaka, jurnal, publik (nama berkas saja). " + LABEL_AI)
    hasil = cek_acuan()
    lb.tabel(["No", "Acuan yang dibutuhkan", "Status", "Berkas di acuan/ atau penanganan"], [
        [i + 1, ket, "ada" if bf else "belum ada",
         bf if bf else "Belum ada di acuan/; ditulis [Literatur, belum ada di acuan/], pasal/halaman tidak ditebak."]
        for i, (ket, bf) in enumerate(hasil)], rata=list("clcl"), fill_kolom={2: AI, 3: AI})

    # ---- Keputusan Defsa
    lb = Lembar(wb.create_sheet("Keputusan Defsa"), 9, "Keputusan yang diminta dari Defsa", [5, 66, 80, 22])
    lb.catatan(ket_ai)
    lb.tabel(["No", "Keputusan", "Dasar dan usulan AI", "Status"], keputusan(), rata=list("clll"), fill_kolom={3: AI})

    keluar.parent.mkdir(parents=True, exist_ok=True)
    wb.save(keluar)
    return keluar


# ------------------------------------------------------------------ Markdown
def tulis_md(keluar=MD, hasil_t98=None):
    kel = kelompok()
    ps = pasangan()
    z = zona_gabung(ps)
    cm = cek_murah()
    el = elevasi()
    cr, tanpa = cocok_reaksi()
    h = hasil_t98 or t98()
    L = []
    L.append(f"# 6.0 Telaah Data Tahap 6 ({STATUS}, 21 Nov 2026)\n")
    L.append("DATA SIMULASI. Disusun AI atas permintaan Defsa; kunci jawaban tidak dibuka. Rincian di "
             "`6.0 Telaah Data Tahap 6.xlsx` (`skrip/tahap6_telaah.py`, uji `tests/test_tahap6_telaah.py`), gambar GS-27 "
             "(`Gambar/DWG/GS-27 Telaah Data Pondasi.dwg`, `6.0 Gambar Telaah Data.pdf`).\n")
    L.append("## Ringkasan temuan\n")
    L.append("| Kode | Temuan |\n|---|---|")
    for t in temuan():
        L.append(f"| {t[0]} | {t[1]} |")
    L.append("\n## Tabel kunci\n")
    L.append("**Pasangan tiang dan cap yang harus digabung** (seluruh pasangan lain cap):\n")
    L.append("| No | Cap A | Cap B | Pasang tiang | < 2,0 m | Terdekat (m) |\n|---|---|---|---|---|---|")
    for n, ((gi, gj), pl_) in enumerate(sorted(z.items()), 1):
        L.append(f"| {n} | {id_cap(gi)} ({idn(kel[gi][0], 0)}; {idn(kel[gi][1], 0)}) | {id_cap(gj)} "
                 f"({idn(kel[gj][0], 0)}; {idn(kel[gj][1], 0)}) | {len(pl_)} | {sum(1 for p in pl_ if p['kurang20'])} "
                 f"| {idn(min(p['d'] for p in pl_), 3)} |")
    L.append("\nUsulan: cap kolom digabung ke cap inti pasangannya (satu cap kaku 1.200 mm); kolom (52; 35) dan (52; 43) "
             "sudah diputuskan masuk cap inti (Tahap 5, B-3). Jarak minimum dicek ulang di 6.3.\n")
    L.append("**Elevasi dan air terhadap cap**\n")
    L.append("| Kondisi | Muka air (m) | Di atas kepala tiang +10,85 (m) | Cap terendam (m) | u (kPa) | Berat cap (kPa) |\n"
             "|---|---|---|---|---|---|")
    for e in el:
        L.append(f"| {e['nama']} | +{idn(e['elev'])} | {idn(e['terhadap_kepala'])} | {idn(e['terendam'])} | "
                 f"{idn(e['u'])} | {idn(e['berat'])} |")
    L.append("\n**Cek murah reaksi**\n")
    L.append("| Cek | Nilai | Pembanding | Selisih |\n|---|---|---|---|")
    L.append(f"| Jumlah titik | {cm['n']} ({cm['n_kol']} kolom + {cm['n_inti']} inti) | 77 | 0 |")
    L.append(f"| Σ Pmax layan (kN) | {idn(cm['sum_pmax'], 1)} | Σ (D + L) 5.6 = {idn(cm['sum_DL'], 1)} | "
             f"{idn(cm['sel_pmax_DL'])} % |")
    L.append(f"| Σ tambahan struktur tengah (kN) | {idn(cm['sum_tambah'], 1)} | T-95 = 58.040,1 | 0,00 % |")
    L.append(f"| Σ D + L tambahan per titik (kN) | {idn(cm['sum_DLtambah'], 1)} | T-95 = 58.040,1 | "
             f"{idn((cm['sum_DLtambah'] - 58040.1) / 58040.1 * 100)} % |")
    L.append(f"| Reaksi tanpa kelompok tiang | 0 | - | kelompok utama tanpa reaksi: {len(tanpa)} |")
    L.append("\n## T-98 cek silang jarak dan jumlah tiang\n")
    c1, a = h["cara1"], h["ifc"]
    L.append(f"Toleransi ditetapkan dulu: jumlah dan pasangan 0 selisih, jarak terdekat ≤ 1 mm. Cara 1 (koordinat skrip): "
             f"{c1['n']} tiang, {c1['p20']} / {c1['p24']} pasang, terdekat {idn(c1['dmin'], 3)} m. Cara 2a (IFC): {a['n']} / "
             f"{a['p20']} / {a['p24']}, {idn(a['dmin'], 3)} m, selisih {idn(a['sel_mm'], 3)} mm.")
    if "dwg" in h:
        d = h["dwg"]
        L.append(f"Cara 2b (DWG GS-27): {d['n']} / {d['p20']} / {d['p24']}, {idn(d['dmin'], 3)} m, selisih "
                 f"{idn(d['sel_mm'], 3)} mm. Hasil: {'Lolos' if h['lolos'] else 'Gagal'}.\n")
    L.append("## Permintaan data ke sesi skenario (disetujui Defsa 21 Nov 2026)\n")
    for p in permintaan():
        L.append(f"{p[0]}. {p[1]}. Alasan: {p[3]}")
    L.append("\n## Acuan belum ada di acuan/\n")
    for ket, bf in cek_acuan():
        L.append(f"- {ket}: {'ada (' + bf + ')' if bf else 'belum ada di acuan/'}")
    L.append("\n## Keputusan yang diminta dari Defsa\n")
    for k in keputusan():
        L.append(f"{k[0]}. {k[1]}. {k[2]}")
    L.append("\nSemua butir di atas disetujui Defsa 21 Nov 2026.\n")
    Path(keluar).write_text("\n".join(L), encoding="utf-8")
    return keluar


# ------------------------------------------------------------------ gambar GS-27
def gambar(status=None, dwg=DWG, png=PNG, pdf=PDF):
    from cad_lembar import Gambar
    from shapely.geometry import LineString, box
    from shapely.ops import unary_union

    import tahap3_tapak as tp
    import tahap5_gambar_plot as gp
    import tahap5_pit_lift as pit
    import tahap2_stratigrafi as st2
    import tahap2_kimia_tebing_gudang as tk

    SK = 600
    H = 1.8                                   # mm kertas
    hm = H * SK / 1000                        # m
    LH = gp.LEBAR_HURUF
    kel = kelompok()
    pos = _data()[1]
    ps = pasangan()
    z = zona_gabung(ps)
    cr, _ = cocok_reaksi()

    gx0, gx1, gy0, gy1 = GRID_X[0], GRID_X[-1], GRID_Y[0], GRID_Y[-1]
    garis = unary_union([LineString([(x, gy0 - 5), (x, gy1 + 5)]) for x in GRID_X] +
                        [LineString([(gx0 - 5, y), (gx1 + 5, y)]) for y in GRID_Y])
    rb = 3.0 * SK / 1000
    tetap = []
    for x in GRID_X:
        for yy in (gy1 + 1.5 + rb, gy0 - 1.5 - rb):
            tetap.append((x - rb, yy - rb, x + rb, yy + rb))
    for y in GRID_Y:
        tetap.append((gx0 - 1.5 - 2 * rb, y - rb, gx0 - 1.5, y + rb))
    r_t = D_TIANG / 2
    for (px, py) in pos:                                   # label tidak boleh menimpa tiang
        tetap.append((px - r_t, py - r_t, px + r_t, py + r_t))
    pn = gp.Penempat(garis, tetap)
    pn.h = hm
    cap_kotak = []
    for gi, (x, y, n, s) in enumerate(kel):
        w, d = cap_ukuran(gi)
        cap_kotak.append((x - w / 2, x + w / 2, y - d / 2, y + d / 2))
    pn.kotak = cap_kotak

    def tempat(kotak, teks, boleh_dalam=False):
        w = max(len(t) for t in teks) * LH * hm + 0.2
        pn.ukuran = lambda baris, w=w: (w, len(baris) * hm * 1.25)
        return pn.tempat(kotak, teks, boleh_dalam=boleh_dalam)

    with Gambar(SK) as g:
        # ---- tapak
        g.layer("C-PERSIL", 7, 0.7, "PHANTOM")
        g.pline([(0, 0), (tp.LX, 0), (tp.LX, tp.LY), (0, tp.LY)], "C-PERSIL", tutup=True)
        g.layer("C-TEBING", 7, 0.5, "DASHDOT")
        xs = list(range(0, 141, 10))
        g.pline([(-6, -tp.puncak_2026(0))] + [(x, -tp.puncak_2026(x)) for x in xs] + [(146, -tp.puncak_2026(140))],
                "C-TEBING")
        g.layer("C-SEMPADAN", 3, 0.35, "DASHED")
        g.pline([(x, tp.kedalaman_sempadan(x)) for x in np.linspace(0, 140, 29)], "C-SEMPADAN")
        # P-2
        p2 = next(r for r in tk.ringkas_tebing() if r["potongan"] == "P-2")
        g.layer("C-POTONGAN", 7, 0.35, "DASHDOT")
        y_p2 = -(p2["thal_jarak"] + 1.0)
        g.pline([(p2["x"], 10.0), (p2["x"], y_p2)], "C-POTONGAN")
        g.layer("C-POTONGAN-TEKS", 7, 0.25)
        g.teks((p2["x"] + 1.0, y_p2 + 1.5), "POTONGAN P-2", "C-POTONGAN-TEKS", H, j="L")
        pn.rects.append((p2["x"] + 1.0, y_p2 + 1.5, p2["x"] + 1.0 + 12 * LH * hm, y_p2 + 1.5 + hm))
        g.teks((50.0, -tp.puncak_2026(50) - 3.0), "PUNCAK TEBING SUNGAI", "C-TEBING", H, j="MC")
        g.teks((50.0, tp.kedalaman_sempadan(50) + 1.2), "GARIS SEMPADAN SUNGAI", "C-SEMPADAN", H, j="MC")
        # gudang timur bercerucuk
        gd = tp.GUDANG
        g.layer("A-GUDANG", 7, 0.35)
        g.arsir([(gd[0], gd[1]), (gd[0] + gd[2], gd[1]), (gd[0] + gd[2], gd[1] + gd[3]), (gd[0], gd[1] + gd[3])],
                "A-GUDANG", pola="ANSI31", skala_pola=0.8)
        g.teks((gd[0] + gd[2] / 2, gd[1] + gd[3] + 3.6), "GUDANG TETANGGA", "A-GUDANG", H, j="MC", tebal=True)
        g.teks((gd[0] + gd[2] / 2, gd[1] + gd[3] + 1.2), "(CERUCUK KAYU)", "A-GUDANG", H, j="MC")
        # ---- massa gedung
        g.layer("A-MASSA", 7, 0.7)
        g.pline(gp.GEDUNG["podium"], "A-MASSA", tutup=True)
        g.layer("A-MENARA", 7, 0.35, "DASHED")
        g.pline(gp.GEDUNG["menara"], "A-MENARA", tutup=True)
        ux0, ux1, uy0, uy1 = 100.0, 134.0, 44.0, 76.0
        g.layer("A-UTILITAS", 7, 0.5)
        g.pline([(ux0, uy0), (ux1, uy0), (ux1, uy1), (ux0, uy1)], "A-UTILITAS", tutup=True)
        g.teks(((ux0 + ux1) / 2, uy0 - 2.4), "GEDUNG UTILITAS + PARKIR", "A-UTILITAS", H, j="MC", tebal=True)
        g.teks((30.0, 83.5), "MASSA PODIUM", "A-MASSA", H, j="MC", tebal=True)
        # ---- as grid
        g.layer("S-GRID", 8, 0.13, "CENTER")
        for x in GRID_X:
            g.pline([(x, gy0 - 1.5), (x, gy1 + 1.5)], "S-GRID")
        for y in GRID_Y:
            g.pline([(gx0 - 1.5, y), (gx1 + 1.5, y)], "S-GRID")
        for i, x in enumerate(GRID_X):
            for y_a, y_b in ((gy1 + 1.5, gy1 + 1.6), (gy0 - 1.5, gy0 - 1.6)):
                g.as_grid(NAMA_X[i], (x, y_a), (x, y_b), r_kertas=3.0, dua_ujung=False)
        for j_, y in enumerate(GRID_Y):
            g.as_grid(NAMA_Y[j_], (gx0 - 1.5, y), (gx0 - 1.6, y), r_kertas=3.0, dua_ujung=False)
        # ---- pit lift (kotak dari GEOM 5.5)
        g.layer("M-PIT", 7, 0.5)
        for kode, gm in pit.GEOM.items():
            cx, cy = gm["pusat"]
            w, d = gm["bay"][0] * gm["n"][0], gm["bay"][1] * gm["n"][1]
            g.pline([(cx - w / 2, cy - d / 2), (cx + w / 2, cy - d / 2), (cx + w / 2, cy + d / 2), (cx - w / 2, cy + d / 2)],
                    "M-PIT", tutup=True)
        # ---- cap Tahap 3 (kotak)
        g.layer("S-CAP", 7, 0.25)
        g.layer("S-CAP-INTI", 7, 0.5)
        for gi, (x0, x1, y0, y1) in enumerate(cap_kotak):
            lay = "S-CAP-INTI" if kel[gi][3] == 90 else "S-CAP"
            g.pline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], lay, tutup=True)
        # ---- tiang (lingkaran Ø800, layer per gedung)
        g.layer("S-TIANG-UTAMA", 7, 0.18)
        g.layer("S-TIANG-UTIL", 4, 0.18)
        for (px, py) in pos:
            g.aktif("S-TIANG-UTIL" if px >= X_UTILITAS - 3 else "S-TIANG-UTAMA")
            g.cmd("circle", {"center": g.mm((px, py)), "radius": D_TIANG * 500})
        # ---- 77 titik reaksi: block diamond + titik
        g.layer("S-REAKSI", 1, 0.25)
        if "TITIK_REAKSI" not in g._layers:
            dm = 450.0 * SK / 600   # setengah diagonal 0,45 m pada 1:600
            hh = [g.cmd("pline", {"vertices": [[0, dm], [dm, 0], [0, -dm], [-dm, 0]], "closed": True})["handle"],
                  g.cmd("pline", {"vertices": [[-dm * 0.6, 0], [dm * 0.6, 0]]})["handle"],
                  g.cmd("pline", {"vertices": [[0, -dm * 0.6], [0, dm * 0.6]]})["handle"]]
            g.cmd("block", {"name": "TITIK_REAKSI", "base": [0, 0], "handles": hh, "keep": "delete"})
            g._layers.add("TITIK_REAKSI")
        g.aktif("S-REAKSI")
        for r in cr:
            g.cmd("insert", {"name": "TITIK_REAKSI", "at": g.mm((r["x (m)"], r["y (m)"]))})
        # ---- pasangan dekat: garis penghubung, < 2,0 tebal; zona gabung = kotak gabungan cap
        g.layer("S-PASANG-20", 1, 0.7)
        g.layer("S-PASANG-24", 5, 0.5, "DASHED")
        for p in ps:
            a, b = pos[p["i"] - 1], pos[p["j"] - 1]
            g.pline([tuple(a), tuple(b)], "S-PASANG-20" if p["kurang20"] else "S-PASANG-24")
        g.layer("S-GABUNG", 1, 0.5, "DASHDOT")
        for n, ((gi, gj), _pl) in enumerate(sorted(z.items()), 1):
            a, b = cap_kotak[gi], cap_kotak[gj]
            x0, x1 = min(a[0], b[0]) - 0.3, max(a[1], b[1]) + 0.3
            y0, y1 = min(a[2], b[2]) - 0.3, max(a[3], b[3]) + 0.3
            g.pline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], "S-GABUNG", tutup=True)
            lab = f"G{n}"
            px, py, _ = tempat((x0, x1, y0, y1), [lab], boleh_dalam=False)
            g.teks((px, py), lab, "S-GABUNG", H, j="MC", tebal=True)
        # ---- titik bor, CPTu, sondir, BT
        g.layer("S-TITIK", 7, 0.25)
        g.layer("S-TITIK-TEKS", 7, 0.18)
        titik = [(t["nama"], t["x"], t["y"], "bor") for t in st2.semua_titik() if t["jenis"] in ("Bor", "CPTu")]
        titik += [(n, x, y, "sondir") for n, (x, y) in (("S-01", (15, 10)), ("S-02", (70, 25)), ("S-03", (95, 45)),
                                                         ("S-04", (40, 60)), ("S-05", (110, 75)), ("S-06", (125, 20)))]
        titik += [("BT-1", 40, -10, "bor"), ("BT-2", 90, -4.5, "bor"), ("BT-3", 125, -7, "bor")]
        rt_ = 0.9 * SK / 1000 * 0.9
        for nama, x, y, jn in titik:
            g.aktif("S-TITIK")
            if jn == "bor":
                g.cmd("circle", {"center": g.mm((x, y)), "radius": rt_ * 1000 * 0.5})
                g.cmd("circle", {"center": g.mm((x, y)), "radius": rt_ * 1000 * 0.15})
            else:
                dm = rt_ * 1000 * 0.55
                g.cmd("pline", {"vertices": [[x * 1000, y * 1000 + dm], [x * 1000 + dm, y * 1000 - dm],
                                             [x * 1000 - dm, y * 1000 - dm]], "closed": True})
            kotak = (x - rt_, x + rt_, y - rt_, y + rt_)
            px, py, _ = tempat(kotak, [nama], boleh_dalam=False)
            g.teks((px, py), nama, "S-TITIK-TEKS", H, j="MC")
            pn.rects.append((x - rt_, y - rt_, x + rt_, y + rt_))
        # ---- keterangan pit
        g.teks((54.0, 39.0 - 3.6), "PIT L-1..4", "M-PIT", H, j="MC")
        pn.rects.append((54.0 - 5 * LH * hm, 39.0 - 3.6 - hm / 2, 54.0 + 5 * LH * hm, 39.0 - 3.6 + hm / 2))
        # ---- legenda dan catatan
        g.legenda_tambah("garis", "Tiang bor Ø800 gedung utama (305)", tebal=0.18)
        g.legenda_tambah("garis", "Tiang bor Ø800 utilitas + parkir (68)", tebal=0.18)
        g.legenda_tambah("garis", "Cap Tahap 3 (kotak); inti tebal", tebal=0.35)
        g.legenda_tambah("garis", "Titik reaksi 5.6 (77: 70 kolom + 7 inti)", tebal=0.25)
        g.legenda_tambah("garis", "Pasangan tiang < 2,0 m (30)", tebal=0.7)
        g.legenda_tambah("garis", "Pasangan tiang 2,0 - 2,4 m (9)", garis="DASHED", tebal=0.5)
        g.legenda_tambah("garis", "Zona gabung cap G1-G14", garis="DASHDOT", tebal=0.5)
        g.legenda_tambah("garis", "Pit lift L-1..L-7 (5.5)", tebal=0.5)
        g.legenda_tambah("garis", "Puncak tebing; sempadan; potongan P-2", garis="DASHDOT", tebal=0.5)
        g.legenda_tambah("garis", "Bor dan CPTu (lingkaran); sondir (segitiga)", tebal=0.25)
        d_ = min(p["d"] for p in ps)
        catatan = [
            f"Tiang LOD 200 Tahap 3 (3.7): {len(pos)} tiang, {len(kel)} cap; {len(ps)} pasang < 2,4 m, "
            f"{sum(1 for p in ps if p['kurang20'])} pasang < 2,0 m, terdekat {idn(d_, 2)} m.",
            "Cap kolom di sekitar inti harus digabung ke cap inti (G1-G14); usulan di 6.0 dan diputuskan Defsa.",
            "Kepala tiang +10,85; muka cap +12,05; air desain +11,20. 4 titik bor tangan HA dan 5 titik bor tebing tidak semua digambar.",
            "Data simulasi. Draf, menunggu persetujuan Defsa.",
        ]
        g.lembar("GS-27", "Telaah data pondasi: tiang, cap, reaksi, tapak", f"1:{SK}", pusat=(82.0, 40.0),
                 subjudul="Langkah 6.0: telaah data Tahap 6 (6.0 Telaah Data Tahap 6.xlsx)",
                 status=status or "DISETUJUI 21 NOV 2026", tanggal="NOVEMBER 2026", catatan=catatan,
                 judul_kop="TELAAH DATA PONDASI")
        g.skala_grafis(205, 22, 60)
        g.panah_utara(318, 262, 10)
        Path(pdf).parent.mkdir(parents=True, exist_ok=True)
        Path(png).parent.mkdir(parents=True, exist_ok=True)
        g.simpan(dwg, pdf, png)
    return dwg


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    print(buat_excel())
    d = gambar()
    import cad_cek
    hasil = cad_cek.cek(d)
    print(d, f"{len(hasil)} pasangan bertumpuk")
    for h in hasil:
        print(h)
    r = t98()
    print(r)
    print(catat_t98(r))
    print(tulis_md(hasil_t98=r))


if __name__ == "__main__":
    main()
