"""Langkah 4.10: rincian fasad V3 terpilih (keputusan Defsa 20 Nov 2026) untuk gambar DED struktur.

V3 = kaca + overstek 0,9 m tiap lantai di sisi utara-selatan, dinding terakota masif di sisi barat-timur. Isi:
  1. berat fasad V3 per sisi (bidang fasad 0,6 m di luar as, model 4.9) dibandingkan asumsi 4.2 (q seragam di keliling
     as untuk berat seismik dan beban balok tepi 4.6);
  2. beban angkur konsol overstek + kaca (U-S) dan konsol terakota (B-T) ke tepi pelat/balok tepi, kombinasi SNI 1726
     4.2.2 dan gaya komponen nonstruktural Pasal 9, dicek terhadap angkur cor 4 M16 hef 150 (sama dengan 4.8);
  3. torsi keseimbangan pada balok tepi (beban fasad eksentris) dibandingkan Tu desain 4.6.
DATA SIMULASI untuk studi kasus portofolio. Disusun AI atas permintaan Defsa (20 Nov 2026); disetujui
Defsa 20 Nov 2026. Kunci jawaban tidak dibuka.

Acuan (halaman cetak):
SNI 1727:2020 Tabel C3.1-1 hal. 278 (jendela kaca, kusen, dan sash 0,38 kPa); Tabel C3.1-2 hal. 281 (terra cotta
arsitektural, rongga tidak diisi 11,3 kN/m³); Tabel 4.3-1 hal. 27 (awning dan kanopi, semua konstruksi lainnya 0,96 kPa;
pekerja pemeliharaan 1,33 kN); Gambar 27.3-1 hal. 128-129 (Cp dinding datang 0,8, dinding samping -0,7, atap -0,9);
Tabel 26.13-1 (GCpi ±0,18); qh dari 4.2 `angin()` (V 30 m/s [Asumsi]).
SNI 1726:2019 Pasal 4.2.2 hal. 25-26 (kombinasi); 9.1.1 hal. 109 (Ip 1,5: fasad RS kategori IV memengaruhi operasi);
9.2.1 Pers. (85)-(87) hal. 111 (Fp, batas 0,3-1,6 SDS Ip Wp); 9.2.1.2 hal. 111 (vertikal ±0,2 SDS Wp); Tabel 25
hal. 116-117 (pengencang sambungan dinding eksterior ap 1,25, Rp 1,0); 9.2.2 Pers. (90)-(92) hal. 113 (Dpl = Ie Dp);
butir sambungan panel hal. 118 (Dpl >= 13 mm).
SNI 2847:2019 17.3.3 hal. 319 (φ 0,75 tarik baja, 0,65 geser baja, 0,70 beton kondisi B); 17.4.1.2 hal. 321 (Nsa);
17.4.2.2 hal. 323 (Nb = 10 √fc' hef^1,5); 17.2.3.4.4 hal. 309 (0,75 φNcbg untuk gaya gempa); 17.5.1.2 Pers. (b)
hal. 339 (Vsa = 0,6 Ase futa); 17.6.3 hal. 352 (interaksi <= 1,2).
"""
from __future__ import annotations

import math
import re
import sys
from pathlib import Path

from shapely.geometry import box

sys.path.insert(0, str(Path(__file__).parent))
import tahap4_beban as tb  # noqa: E402
import tahap4_bim as bim  # noqa: E402
import tahap4_dinding as td  # noqa: E402

AKAR = Path(__file__).resolve().parents[1]
KELUAR = AKAR / "04 Struktur Atas"
BERKAS = KELUAR / "4.10 Rincian Fasad V3.xlsx"
LABEL = tb.LABEL
STATUS = "disetujui Defsa 20 Nov 2026"
W_K2 = 159156.0   # kN, berat seismik K2 (4.2, T-69)
TU_TEPI = {"podium": 24.5, "menara": 21.5}   # kNm, Tu desain balok tepi 4.6 (B-P tepi LT3, B-M tepi LT4-LT6)

# (kode, uraian, nilai atau rumus, satuan, sumber). Rumus memakai kode sebelumnya; sama persis di Python dan Excel.
_A = td.ANGKUR
PARAM = [
    ("h", "Tinggi tingkat terbesar (LT1-LT3)", tb.LEVEL["LT2"] - tb.LEVEL["LT1"], "m", "4.2 LEVEL"),
    ("e_tepi", "Tepi pelat di luar as", bim.TEPI_PELAT, "m", "4.9 [Asumsi detail]"),
    ("d_fs", "Bidang fasad di luar as", bim.FASAD_JARAK, "m", "4.9 model fasad [Asumsi]"),
    ("L_ov", "Panjang overstek dari bidang kaca", 0.9, "m", "Keputusan Defsa 4.9 (V3)"),
    ("s_ov", "Jarak konsol kaca + overstek (modul kaca)", 1.6, "m", "[Asumsi: 5 modul per bentang 8 m]"),
    ("s_tk", "Jarak konsol terakota", 1.2, "m", "[Asumsi]"),
    ("q_kaca", "Kaca, kusen, dan sash", 0.38, "kPa", "SNI 1727 Tabel C3.1-1 hal. 278"),
    ("g_tk", "Terakota arsitektural, rongga tidak diisi", 11.3, "kN/m³", "SNI 1727 Tabel C3.1-2 hal. 281"),
    ("tb_tk", "Tebal blok terakota", 0.20, "m", "4.9 model (FS-Terakota 200)"),
    ("q_ov", "Overstek: rangka baja hollow + ACP 4 mm atas-bawah", 0.40, "kPa", "[Asumsi: katalog pemasok, dicek Tahap 7]"),
    ("lr_ov", "Beban hidup awning dan kanopi", 0.96, "kPa", "SNI 1727 Tabel 4.3-1 hal. 27"),
    ("P_pm", "Pekerja pemeliharaan di ujung overstek", 1.33, "kN", "SNI 1727 Tabel 4.3-1 hal. 27"),
    ("qh", "Tekanan velositas di puncak menara", round(tb.angin()["qh"], 4), "kPa", "4.2 angin() (V 30 m/s [Asumsi])"),
    ("G", "Faktor efek tiupan", 0.85, "-", "SNI 1727 Pasal 26.11.1"),
    ("cp_b", "Cp permukaan bawah overstek (= dinding datang)", 0.8, "-", "Gambar 27.3-1 [Asumsi pendekatan overhang]"),
    ("cp_a", "Cp permukaan atas overstek (atap)", 0.9, "-", "Gambar 27.3-1 hal. 129 (nilai mutlak)"),
    ("cp_s", "Cp dinding samping (hisap)", 0.7, "-", "Gambar 27.3-1 hal. 128 (nilai mutlak)"),
    ("gcpi", "GCpi tertutup", 0.18, "-", "SNI 1727 Tabel 26.13-1"),
    ("SDS", "Percepatan spektral desain", tb.SDS, "g", "4.1 opsi (a)"),
    ("Ip", "Faktor keutamaan komponen", 1.5, "-", "SNI 1726 9.1.1 butir 3 hal. 109"),
    ("ap", "Faktor amplifikasi pengencang", 1.25, "-", "SNI 1726 Tabel 25 hal. 117"),
    ("Rp", "Faktor modifikasi respons pengencang", 1.0, "-", "SNI 1726 Tabel 25 hal. 117"),
    ("zh", "z/h (konservatif: tingkat atas)", 1.0, "-", "SNI 1726 9.2.1 hal. 111"),
    ("r_sim", "Rasio simpangan maks terhadap izin (tepi + torsi)", 0.46, "-", "4.3 (46 % dari 0,010 hsx)"),
    ("n_a", "Jumlah angkur per konsol", _A["n"], "buah", "4.8 ANGKUR (cor di tempat)"),
    ("Ase", "Luas efektif angkur M16", _A["Ase"], "mm²", "4.8"),
    ("futa", "Kuat tarik angkur", _A["futa"], "MPa", "4.8"),
    ("hef", "Kedalaman tanam efektif", _A["hef"], "mm", "4.8"),
    ("s_a", "Jarak angkur (vertikal = horizontal)", _A["s"], "mm", "4.8"),
    ("fc", "Kuat tekan beton balok tepi", 30.0, "MPa", "4.6 (fc' 30)"),
]
TURUNAN = [
    ("e_kaca", "Eksentrisitas bidang kaca/terakota dari muka pelat", "d_fs-e_tepi", "m"),
    ("a_ov", "Lengan titik berat overstek", "e_kaca+L_ov/2", "m"),
    ("a_uj", "Lengan ujung overstek", "e_kaca+L_ov", "m"),
    ("q_tk", "Berat dinding terakota per luas", "g_tk*tb_tk", "kPa"),
    ("fp", "Fp/Wp pengencang (85), dibatasi (86)-(87)", "min(max(0.4*ap*SDS*Ip/Rp*(1+2*zh),0.3*SDS*Ip),1.6*SDS*Ip)", "-"),
    ("ev", "Gaya vertikal gempa/Wp", "0.2*SDS", "-"),
    ("p_up", "Hisap ke atas overstek (bawah + atas)", "qh*G*(cp_b+cp_a)", "kPa"),
    ("p_h", "Hisap keluar dinding", "qh*(G*cp_s+gcpi)", "kPa"),
    ("Dpl", "Perpindahan relatif sambungan panel Ie Dp", "max(Ip*r_sim*0.010*h*1000,13)", "mm"),
    # konsol U-S: kaca setinggi tingkat + overstek
    ("ns_DV", "U-S: D geser (kaca + overstek)", "q_kaca*h*s_ov+q_ov*L_ov*s_ov", "kN"),
    ("ns_DM", "U-S: D momen di muka pelat", "q_kaca*h*s_ov*e_kaca+q_ov*L_ov*s_ov*a_ov", "kNm"),
    ("ns_LV", "U-S: Lr geser (merata atau terpusat)", "max(lr_ov*L_ov*s_ov,P_pm)", "kN"),
    ("ns_LM", "U-S: Lr momen (merata atau terpusat di ujung)", "max(lr_ov*L_ov*s_ov*a_ov,P_pm*a_uj)", "kNm"),
    ("ns_WV", "U-S: W geser (hisap ke atas, negatif)", "-p_up*L_ov*s_ov", "kN"),
    ("ns_WM", "U-S: W momen", "-p_up*L_ov*s_ov*a_ov", "kNm"),
    ("ns_WH", "U-S: W tarik keluar", "p_h*h*s_ov", "kN"),
    ("ns_EH", "U-S: Fp tarik keluar", "fp*ns_DV", "kN"),
    # konsol B-T: terakota setinggi tingkat
    ("tk_DV", "B-T: D geser", "q_tk*h*s_tk", "kN"),
    ("tk_DM", "B-T: D momen", "q_tk*h*s_tk*e_kaca", "kNm"),
    ("tk_WH", "B-T: W tarik keluar", "p_h*h*s_tk", "kN"),
    ("tk_EH", "B-T: Fp tarik keluar", "fp*tk_DV", "kN"),
    # kapasitas angkur
    ("z", "Lengan kopel angkur (baris atas-bawah)", "s_a/1000", "m"),
    ("phiNsa", "φNsa dua angkur baris atas", "0.75*2*Ase*futa/1000", "kN"),
    ("Nb", "Nb satu angkur", "10*sqrt(fc)*hef**1.5/1000", "kN"),
    ("ANc", "ANc baris atas (tepi 1,5 hef di atas)", "(s_a+3*hef)*(3*hef)", "mm²"),
    ("phiNcbg", "φNcbg baris atas", "0.70*ANc/(9*hef**2)*Nb", "kN"),
    ("phiVsa", "φVsa empat angkur", "0.65*n_a*0.6*Ase*futa/1000", "kN"),
]
# kombinasi: (kode, uraian, faktor D, faktor Lr, faktor W, faktor Ev, faktor Eh)
KOMBINASI = [("K1", "1,4D", 1.4, 0, 0, 0, 0), ("K2", "1,2D + 1,6Lr", 1.2, 1.6, 0, 0, 0),
             ("K3", "1,2D + 0,5Lr + 1,0W", 1.2, 0.5, 1, 0, 0), ("K4", "0,9D + 1,0W", 0.9, 0, 1, 0, 0),
             ("K5", "1,2D + Ev + Fp", 1.2, 0, 0, 1, 1), ("K6", "0,9D - Ev + Fp", 0.9, 0, 0, -1, 1)]


def _komb():
    """Baris kombinasi per sisi: V, M, H, lalu tarik baris atas Nu = |M|/z + H/2 dan geser Vu = |V|."""
    out = []
    for s in ("ns", "tk"):
        for k, ur, fd, fl, fw, fe, fh in KOMBINASI:
            if s == "tk" and fl:
                fl = 0
            if s == "tk" and k == "K2":
                continue
            v = [f"{fd}*{s}_DV"]
            m = [f"{fd}*{s}_DM"]
            h = ["0"]
            if fl:
                v.append(f"{fl}*{s}_LV")
                m.append(f"{fl}*{s}_LM")
            if fw:
                if s == "ns" and k == "K4":   # hisap ke atas hanya dipakai bila berlawanan dengan berat (0,9D)
                    v.append(f"{s}_WV")
                    m.append(f"{s}_WM")
                h.append(f"{s}_WH")
            if fe:
                v.append(f"{fe}*ev*{s}_DV")
                m.append(f"{fe}*ev*{s}_DM")
            if fh:
                h.append(f"{s}_EH")
            out += [(f"{s}_{k}_V", f"{s.upper()} {ur}: V", "+".join(v), "kN"),
                    (f"{s}_{k}_M", f"{s.upper()} {ur}: M", "+".join(m), "kNm"),
                    (f"{s}_{k}_H", f"{s.upper()} {ur}: H", "+".join(h), "kN"),
                    (f"{s}_{k}_N", f"{s.upper()} {ur}: Nu baris atas", f"abs({s}_{k}_M)/z+{s}_{k}_H/2", "kN")]
    return out


def _cek():
    out = []
    for s, nama in (("ns", "U-S"), ("tk", "B-T")):
        ks = [k for k, *_ in KOMBINASI if not (s == "tk" and k == "K2")]
        gempa = [k for k in ks if k in ("K5", "K6")]
        lain = [k for k in ks if k not in gempa]
        out += [
            (f"{s}_Nu", f"{nama}: Nu maks (non-gempa)", "max(" + ",".join(f"{s}_{k}_N" for k in lain) + ")", "kN"),
            (f"{s}_NuE", f"{nama}: Nu maks (gempa)", "max(" + ",".join(f"{s}_{k}_N" for k in gempa) + ")", "kN"),
            (f"{s}_Vu", f"{nama}: Vu maks", "max(" + ",".join(f"abs({s}_{k}_V)" for k in ks) + ")", "kN"),
            (f"{s}_rN", f"{nama}: rasio tarik", f"max({s}_Nu/min(phiNsa,phiNcbg),{s}_NuE/min(phiNsa,0.75*phiNcbg))",
             "-"),
            (f"{s}_rV", f"{nama}: rasio geser", f"{s}_Vu/phiVsa", "-"),
            (f"{s}_rNV", f"{nama}: interaksi 17.6.3 (<= 1,2)", f"{s}_rN+{s}_rV", "-"),
        ]
    out += [
        ("gar42", "Beban garis balok tepi asumsi 4.2/4.6", "((1-%s)*%s+%s*%s+%s)*4.2" % (
            tb.BUKAAN, tb.DINDING_LUAR["bata"][0], tb.BUKAAN, tb.DINDING_LUAR["kaca"][0],
            tb.DINDING_LUAR["fasad"][0]), "kN/m"),
        ("gar_tk", "Beban garis V3 B-T (terakota)", "q_tk*h", "kN/m"),
        ("gar_ns", "Beban garis V3 U-S (kaca + overstek)", "q_kaca*h+q_ov*L_ov", "kN/m"),
        ("t_tk", "Torsi keseimbangan balok tepi B-T terhadap as balok, 1,4D, di muka kolom", "1.4*q_tk*h*d_fs*(8-0.75)/2",
         "kNm"),
        ("t_ns", "Torsi keseimbangan balok tepi U-S terhadap as balok, 1,2D + 1,6Lr",
         "(1.2*(ns_DM+ns_DV*e_tepi)+1.6*(ns_LM+ns_LV*e_tepi))/s_ov*(8-0.75)/2", "kNm"),
        ("r_ttk", "Rasio torsi B-T / Tu desain 4.6 menara", f"t_tk/{TU_TEPI['menara']}", "-"),
        ("r_tns", "Rasio torsi U-S / Tu desain 4.6 menara", f"t_ns/{TU_TEPI['menara']}", "-"),
    ]
    return out


def baris_semua():
    return [(k, u, v, s, src) for k, u, v, s, src in PARAM] + \
        [(k, u, r, s, "") for k, u, r, s in TURUNAN + _komb() + _cek()]


def hitung():
    """Evaluasi semua baris (rumus sama dengan Excel)."""
    nilai = {}
    env = {"min": min, "max": max, "abs": abs, "sqrt": math.sqrt}
    for k, _, v, _, _ in baris_semua():
        nilai[k] = float(eval(v, env, nilai)) if isinstance(v, str) else float(v)
    return nilai


# ------------------------------------------------------------------ berat fasad per sisi (V3 vs 4.2)
def sisi_fasad():
    """(pita, tingkat, orientasi, panjang as, panjang bidang fasad, tinggi, jumlah overstek)."""
    out = []
    for poli, a, c in bim._pita():
        tingkat = tb.URUT[tb.URUT.index(a):tb.URUT.index(c) + 1]
        tinggi = tb.LEVEL[c] - tb.LEVEL[a]
        luar = list(poli.buffer(bim.FASAD_JARAK, join_style=2).exterior.coords)
        dalam = list(poli.exterior.coords)
        for (p0, p1), (q0, q1) in zip(zip(dalam[:-1], dalam[1:]), _sejajar(dalam, luar)):
            bt = abs(p0[0] - p1[0]) < 1e-6
            out.append({"pita": f"{a}-{c}", "orientasi": "B-T" if bt else "U-S",
                        "x": (round(min(p0[0], p1[0]), 2), round(max(p0[0], p1[0]), 2)),
                        "y": (round(min(p0[1], p1[1]), 2), round(max(p0[1], p1[1]), 2)),
                        "L_as": math.dist(p0, p1), "L_fs": math.dist(q0, q1), "h": tinggi,
                        "n_ov": 0 if bt else len(tingkat) - 1})
    return out


def _sejajar(dalam, luar):
    """Sisi poligon luar (offset) yang sejajar dan terdekat dengan tiap sisi poligon dalam."""
    sl = list(zip(luar[:-1], luar[1:]))
    hasil = []
    for p0, p1 in zip(dalam[:-1], dalam[1:]):
        bt = abs(p0[0] - p1[0]) < 1e-6
        cocok = [s for s in sl if (abs(s[0][0] - s[1][0]) < 1e-6) == bt]
        mid = ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2)
        hasil.append(min(cocok, key=lambda s: math.dist(mid, ((s[0][0] + s[1][0]) / 2, (s[0][1] + s[1][1]) / 2))))
    return hasil


def berat_fasad(n=None):
    n = n or hitung()
    q42 = n["gar42"] / 4.2
    tot42 = totv3 = 0.0
    rinci = []
    for s in sisi_fasad():
        w42 = q42 * s["L_as"] * s["h"]
        q = n["q_tk"] if s["orientasi"] == "B-T" else n["q_kaca"]
        wv3 = q * s["L_fs"] * s["h"] + n["q_ov"] * n["L_ov"] * s["L_fs"] * s["n_ov"]
        rinci.append({**s, "w42": w42, "wv3": wv3})
        tot42 += w42
        totv3 += wv3
    return {"rinci": rinci, "w42": tot42, "wv3": totv3, "selisih": totv3 - tot42, "rasio_W": (totv3 - tot42) / W_K2}


def luas_fasad_python():
    """Luas bidang fasad V3 per jenis (m²) dari geometri skrip (bidang 0,6 m di luar as) untuk T-87."""
    a = {"terakota": 0.0, "kaca": 0.0}
    for s in sisi_fasad():
        a["terakota" if s["orientasi"] == "B-T" else "kaca"] += s["L_fs"] * s["h"]
    return a


def luas_fasad_ifc(ifc=None):
    """Luas dinding FS-Terakota dan FS-Kaca di model BIMCraft V3 (IFC) dari geometri (luas sisi terbesar). T-87."""
    import ifcopenshell
    import ifcopenshell.geom
    import ifcopenshell.util.element
    import numpy as np
    ifc = ifc or ekspor_ifc_v3()
    f = ifcopenshell.open(str(ifc))
    st = ifcopenshell.geom.settings()
    st.set("use-world-coords", True)
    a = {"terakota": 0.0, "kaca": 0.0}
    for w in f.by_type("IfcWall"):
        tipe = ifcopenshell.util.element.get_type(w)
        nama = (tipe.Name if tipe else "") or w.Name or ""
        if "Terakota" not in nama and "Kaca" not in nama:
            continue
        sh = ifcopenshell.geom.create_shape(st, w)
        v = np.array(sh.geometry.verts).reshape(-1, 3)
        dx, dy, dz = v.max(0) - v.min(0)
        a["terakota" if "Terakota" in nama else "kaca"] += max(dx, dy) * dz
    return a


def ekspor_ifc_v3():
    from bimcraft import Sesi
    keluar = AKAR / "model" / "RSTB-ARS-T4-Fasad-V3.ifc"
    with Sesi(AKAR / "model" / "RSTB-ARS-T4-Fasad-V3.bimc") as b:
        b.simpan(keluar)
    return keluar


# ------------------------------------------------------------------ Excel
def _ke_excel(rumus, alamat):
    s = re.sub(r"[A-Za-z_][A-Za-z_0-9]*", lambda m: {"min": "MIN", "max": "MAX", "abs": "ABS", "sqrt": "SQRT"}.get(
        m.group(0), alamat.get(m.group(0), m.group(0))), rumus)
    return "=" + s.replace("**", "^")


def buat_excel(keluar=BERKAS, hitung_ulang=True):
    import openpyxl

    from format_dokumen import AI, Lembar, hitung_ulang_excel, set_font_bawaan

    n = hitung()
    bf = berat_fasad(n)
    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)
    lab = f"DIISI AI ATAS PERMINTAAN DEFSA (20 Nov 2026), sel hijau; {STATUS}. Kunci jawaban tidak dibuka."

    lb = Lembar(wb.create_sheet("Petunjuk"), 1, "Petunjuk rincian fasad V3 (4.10)", [6, 120])
    lb.catatan(LABEL + " " + lab)
    lb.kosong()
    lb.tabel(["No", "Petunjuk"], [[i + 1, t] for i, t in enumerate([
        "Fasad V3 (keputusan Defsa 20 Nov 2026): sisi utara-selatan kaca setinggi tingkat + overstek 0,9 m di atas "
        "jendela tiap lantai; sisi barat-timur dinding blok terakota 200 mm. Bidang fasad 0,6 m di luar as grid tepi "
        "(model 4.9), tepi pelat 0,175 m di luar as: konsol baja ke muka balok tepi menjembatani 0,425 m.",
        "Konsol U-S tiap 1,6 m memikul panel kaca setinggi tingkat dan overstek; konsol B-T (siku penumpu) tiap 1,2 m "
        "memikul terakota satu tingkat [Asumsi detail, dikonfirmasi pemasok di Tahap 7]. Pelat dasar konsol diangkur "
        "ke muka balok tepi 600 dengan 4 M16 cor di tempat hef 150, jarak 150, di tengah tinggi balok (tepi atas "
        "225 mm = 1,5 hef).",
        "Kombinasi SNI 1726 4.2.2: 1,4D; 1,2D + 1,6Lr; 1,2D + 0,5Lr + 1,0W; 0,9D + 1,0W; (1,2D + Ev) + Fp; "
        "(0,9D - Ev) + Fp. Fp pengencang (Tabel 25: ap 1,25, Rp 1,0, Ip 1,5) arah keluar bidang (tarik angkur); "
        "Ev = 0,2 SDS Wp (9.2.1.2). Faktor redundansi 1,0 (9.2.1).",
        "Tarik baris atas Nu = |M|/z + H/2 dengan z = jarak baris angkur (konservatif, tekan di baris bawah). Geser "
        "dipikul 4 angkur. Gaya gempa: kuat beton 0,75 φNcbg (17.2.3.4.4). Geser jebol beton ke tepi bawah balok "
        "(17.5.2) dan cabut (17.5.3) dicek bersama detail pemasok di Tahap 7.",
        "Pembanding 4.2: q seragam (0,65 bata 150 + 0,35 kaca + 0,50 fasad) di keliling as dipakai untuk berat "
        "seismik dan balok tepi 4.6 (dinding 4,2 m). V3 dihitung pada bidang fasad 0,6 m di luar as (lebih panjang).",
        "Kolom Rumus Excel memakai sel lembar ini (Python `tahap4_fasad.hitung()` memakai rumus yang sama). Cek silang "
        "T-87 (luas fasad skrip vs model BIM V3) dan T-88 (Excel = Python) di VERIFIKASI.md.",
    ])], rata=["c", "l"])

    lb = Lembar(wb.create_sheet("Hitungan"), 2, "Parameter, beban angkur, dan cek", [12, 52, 14, 10, 40])
    lb.catatan(LABEL + " " + lab)
    lb.kosong()
    semua = baris_semua()
    r0 = lb.baris + 1
    alamat = {k: f"$E${r0 + i}" for i, (k, *_) in enumerate(semua)}
    data = []
    for k, u, v, s, src in semua:
        data.append([k, u, _ke_excel(v, alamat) if isinstance(v, str) else v, s, src or (v if isinstance(v, str) else "")])
    lb.tabel(["Kode", "Uraian", "Nilai", "Satuan", "Sumber / rumus"], data, rata=["c", "l", "c", "c", "l"],
             fmt=[None, None, "#,##0.000", None, None], fill_kolom={2: AI})

    lb = Lembar(wb.create_sheet("Berat Fasad"), 3, "Berat fasad V3 vs asumsi 4.2", [10, 8, 16, 16, 12, 12, 10, 14, 14])
    lb.catatan(LABEL + " " + lab)
    lb.kosong()
    r0 = lb.baris + 1
    rows = []
    for i, s in enumerate(bf["rinci"]):
        r = r0 + i
        q = "Hitungan!" + (alamat["q_tk"] if s["orientasi"] == "B-T" else alamat["q_kaca"])
        rows.append([s["pita"], s["orientasi"], f"x {s['x'][0]:g}-{s['x'][1]:g}", f"y {s['y'][0]:g}-{s['y'][1]:g}",
                     round(s["L_as"], 3), round(s["L_fs"], 3), round(s["h"], 3),
                     f"=Hitungan!{alamat['gar42']}/4.2*G{r}*I{r}",
                     f"={q}*H{r}*I{r}+Hitungan!{alamat['q_ov']}*Hitungan!{alamat['L_ov']}*H{r}*{s['n_ov']}"])
    # kolom: C pita, D sisi, E x, F y, G L as, H L fasad, I tinggi, J berat 4.2, K berat V3
    lb.tabel(["Pita", "Sisi", "Rentang x (m)", "Rentang y (m)", "L as (m)", "L fasad (m)", "Tinggi (m)",
              "Berat 4.2 (kN)", "Berat V3 (kN)"], rows, rata=["c"] * 9,
             fmt=[None, None, None, None, "#,##0.00", "#,##0.00", "#,##0.00", "#,##0", "#,##0"], fill_kolom={7: AI, 8: AI})
    r1 = r0 + len(rows) - 1
    lb.tabel(["Uraian", "", "", "", "", "", "", "Nilai", "Satuan"], [
        ["Jumlah berat fasad 4.2", "", "", "", "", "", "", f"=SUM(J{r0}:J{r1})", "kN"],
        ["Jumlah berat fasad V3", "", "", "", "", "", "", f"=SUM(K{r0}:K{r1})", "kN"],
        ["Selisih V3 - 4.2 terhadap W K2 = 159.156 kN", "", "", "", "", "", "", f"=(J{r1 + 3}-J{r1 + 2})/{W_K2}", "-"],
    ], rata=["l"] + ["c"] * 8, fmt=[None] * 7 + ["#,##0.0000", None], fill_kolom={7: AI}, beku=False)
    keluar.parent.mkdir(parents=True, exist_ok=True)
    wb.save(keluar)
    if hitung_ulang:
        ok, err = hitung_ulang_excel(keluar)
        if not ok:
            raise RuntimeError(err)
    return keluar


def cek_excel(berkas=BERKAS):
    """T-88: selisih terbesar Excel (dihitung ulang) vs Python untuk semua baris lembar Hitungan dan jumlah berat."""
    import openpyxl
    from format_dokumen import baca_tabel
    wb = openpyxl.load_workbook(berkas, data_only=True)
    _, d = baca_tabel(wb["Hitungan"], "Kode")
    n = hitung()
    sel = max(abs(float(r[2]) - n[r[0]]) for r in d)
    _, b = baca_tabel(wb["Berat Fasad"], "Pita")
    bf = berat_fasad(n)
    sel_b = max(max(abs(float(r[7]) - x["w42"]), abs(float(r[8]) - x["wv3"])) for r, x in zip(b, bf["rinci"]))
    return {"hitungan": sel, "berat": sel_b}


def cek_balok_tepi(n=None):
    """Balok tepi yang memikul fasad eksentris: torsi keseimbangan tidak boleh direduksi (SNI 2847 22.7.3.1), jadi
    kelompok balok tepi 4.6 didesain ulang dengan Tu = maks(Tu 4.6, T keseimbangan) memakai fungsi desain 4.6."""
    import tahap4_balok as bk
    n = n or hitung()
    r = bk.rancang()
    sel = r["selubung"]
    kel = {}
    for k, s in sel.items():
        if s["sisi"] == 1:
            kel.setdefault(bk.kelompok(s["b"], 1), []).append(s)
    out = []
    lama = {x["kelompok"]: x for x in r["kelompok"]}
    for nama, ss in sorted(kel.items()):
        b, h = r["ukuran"].get(nama, (tb.BALOK_B, tb.BALOK_H))
        hc = min(s["hc"] for s in ss)
        tu46 = max(bk.torsi_tepi(s["panel"], s["hc"]) for s in ss)
        t_eq = max(n["t_tk"], n["t_ns"])
        x = bk.desain_penampang(b, h, max(s["neg"] for s in ss), max(s["pos_ujung"] for s in ss),
                                max(s["pos_lap"] for s in ss), max(s["Vg"] for s in ss), max(s["Vu_g"] for s in ss),
                                tu=max(tu46, t_eq), hc=hc)
        a = lama[nama]
        out.append({"kelompok": nama, "Tu46": a["Tu_d"], "T_eq": t_eq, "phiTcr": x["phiTcr"], "lebih_Tcr": t_eq > x["phiTcr"],
                    "s46": (a["s_sendi"], a["s_lap"]), "s_baru": (x["s_sendi"], x["s_lap"]), "samping46": a["samping"],
                    "samping": x["samping"], "ok": x["ok"], "berubah": (x["s_sendi"], x["s_lap"], x["samping"]) !=
                    (a["s_sendi"], a["s_lap"], a["samping"])})
    return out


def ringkas():
    n = hitung()
    return {"n": n, "berat": berat_fasad(n)}


if __name__ == "__main__":
    r = ringkas()
    n = r["n"]
    for k in ("fp", "p_up", "p_h", "Dpl", "ns_Nu", "ns_NuE", "ns_Vu", "ns_rNV", "tk_Nu", "tk_NuE", "tk_Vu", "tk_rNV",
              "phiNsa", "phiNcbg", "phiVsa", "gar42", "gar_tk", "gar_ns", "t_tk", "t_ns", "r_ttk", "r_tns"):
        print(f"{k:8s} {n[k]:10.3f}")
    b = r["berat"]
    print("berat 4.2", round(b["w42"]), "V3", round(b["wv3"]), "rasio W", round(b["rasio_W"], 4))
    if "--balok" in sys.argv:
        for x in cek_balok_tepi(n):
            print(x)
    if "--excel" in sys.argv:
        print(buat_excel(), cek_excel())
