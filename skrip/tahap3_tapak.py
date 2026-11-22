"""Langkah 3.2: kajian aturan tapak dan perizinan (sempadan sungai, PKKPR, amplop bangunan).

Data: '03 Desain Konsep/Data Owner/' (surat sempadan BPSB/117 22 Feb 2027, PKKPR 503/KKPR/0412/III/2027 1 Mar 2027,
surat owner 034/YKTB/III/2027) dan TOR (Lampiran B, C). Keluaran: '3.2 Kajian Tapak.xlsx' dan gambar GK-01
'3.2 Gambar Batasan Tapak.pdf' (CADCraft, kop KOP_A3).
Disusun AI atas permintaan Defsa (19 Nov 2026); disetujui Defsa 19 Nov 2026.
Jalankan:  .venv\\Scripts\\python.exe skrip\\tahap3_tapak.py
"""
from functools import lru_cache
from pathlib import Path

import docx
import numpy as np
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

AKAR = Path(__file__).resolve().parents[1]
DATA = AKAR / "03 Desain Konsep" / "Data Owner"
KELUAR = AKAR / "03 Desain Konsep"
BERKAS = KELUAR / "3.2 Kajian Tapak.xlsx"
PDF = KELUAR / "3.2 Gambar Batasan Tapak.pdf"
LABEL = "DATA SIMULASI untuk studi kasus portofolio. Bukan data proyek nyata. Tidak untuk konstruksi."
LABEL_AI = "DIISI AI ATAS PERMINTAAN DEFSA (19 Nov 2026), sel hijau; disetujui Defsa 19 Nov 2026."

LX, LY = 140.0, 90.0  # persil (TOR 4.1)
GUDANG = (144, 18, 24, 40)  # x, y, lebar, tinggi (Tahap 2, survei gudang)

# TOR Lampiran B (Agustus 2026): jarak puncak tebing di luar batas selatan menurut x
TEBING_2026 = {0: 14, 20: 13, 40: 12, 60: 10, 80: 7, 100: 6, 120: 8, 140: 11}

# PKKPR 503/KKPR/0412/III/2027 Tabel 1 dan persyaratan 1-3
KKPR = {
    "KDB": 0.50, "KLB": 2.4, "KDH": 0.20, "KTB": 0.50, "tinggi_lantai": 8, "tinggi_m": 40.0,
    "gsb_utara": 12.0, "gsb_barat": 5.0, "samping_timur_4": 4.0, "samping_timur_8": 6.0,
    "rumija_utara": 2.0,  # jalan kolektor 12 → 16 m, simetris: 2 m masuk persil
    "rumija_barat": 1.0,  # jalan lingkungan 6 → 8 m, 1 m ke sisi persil
    "akses_min_simpang": 50.0, "akses_maks": 2,
}
TOR = {"KDB": 0.60, "KLB": 3.0, "KDH": 0.15, "gsb_utara": 10.0, "gsb_barat": 5.0, "gsb_selatan_owner": 5.0}
SEMPADAN_DARI_PUNCAK = 20.0  # surat sempadan butir 1
LABIL_STA = (30, 70)  # surat sempadan butir 4
LABIL_LEBAR = 10.0
LABIL_URUG_MAKS = 1.0


# ------------------------------------------------------------------ data
@lru_cache(maxsize=1)
def sempadan():
    """Tabel 1 surat sempadan: [(STA, puncak di luar persil, garis sempadan dari batas selatan, x)].
    STA 0+000 di sudut TENGGARA dan bertambah ke barat (butir 2), jadi x = 140 - STA."""
    d = docx.Document(DATA / "Surat Penetapan Garis Sempadan Sungai.docx")
    t = d.tables[0]
    hasil = []
    for r in t.rows[1:]:
        sta_txt, puncak, garis = (c.text.strip() for c in r.cells[:3])
        sta = float(sta_txt.replace("0+", ""))
        hasil.append((sta, float(puncak.replace(",", ".")), float(garis.replace(",", ".")), LX - sta))
    return tuple(sorted(hasil, key=lambda r: r[3]))


def kedalaman_sempadan(x):
    s = sempadan()
    return float(np.interp(x, [r[3] for r in s], [r[2] for r in s]))


def puncak_2026(x):
    xs = sorted(TEBING_2026)
    return float(np.interp(x, xs, [TEBING_2026[k] for k in xs]))


def cek_sempadan():
    """Cek murah: garis = 20 - puncak (butir 1) dan bandingkan puncak Feb 2027 dengan Agustus 2026."""
    baris = []
    for sta, pk, gs, x in sempadan():
        baris.append({"STA": sta, "x": x, "puncak_2027": pk, "garis": gs, "garis_hitung": SEMPADAN_DARI_PUNCAK - pk,
                      "puncak_2026": puncak_2026(x), "mundur": puncak_2026(x) - pk,
                      "labil": LABIL_STA[0] <= sta <= LABIL_STA[1]})
    return baris


# ------------------------------------------------------------------ geometri
def persil():
    return box(0, 0, LX, LY)


def ruang_sempadan():
    s = sempadan()
    return Polygon([(0, 0)] + [(r[3], r[2]) for r in s] + [(LX, 0)])


def rumija():
    utara = box(0, LY - KKPR["rumija_utara"], LX, LY)
    barat = box(0, 0, KKPR["rumija_barat"], LY)
    return unary_union([utara, barat])


def lahan_perencanaan():
    return persil().difference(unary_union([ruang_sempadan(), rumija()]))


def zona_labil():
    """Jalur 10 m di belakang garis sempadan pada STA 0+030 s.d. 0+070 (x 70-110)."""
    x0, x1 = LX - LABIL_STA[1], LX - LABIL_STA[0]
    xs = np.linspace(x0, x1, 41)
    bawah = [(x, kedalaman_sempadan(x)) for x in xs]
    atas = [(x, kedalaman_sempadan(x) + LABIL_LEBAR) for x in xs[::-1]]
    return Polygon(bawah + atas)


def amplop(lantai=6, tanpa_labil=True):
    """Daerah boleh dibangun: dalam GSB utara/barat, jarak bebas timur, di utara garis sempadan."""
    timur = KKPR["samping_timur_8"] if lantai > 4 else KKPR["samping_timur_4"]
    x0 = KKPR["rumija_barat"] + KKPR["gsb_barat"]
    y1 = LY - KKPR["rumija_utara"] - KKPR["gsb_utara"]
    a = box(x0, 0, LX - timur, y1).difference(ruang_sempadan())
    if tanpa_labil:
        a = a.difference(zona_labil())
    return a


def luas_amplop_strip(lantai=6, tanpa_labil=True, n=14001):
    """Cara kedua (bukan shapely): integrasi lebar arah y per irisan x."""
    timur = KKPR["samping_timur_8"] if lantai > 4 else KKPR["samping_timur_4"]
    x0 = KKPR["rumija_barat"] + KKPR["gsb_barat"]
    x1 = LX - timur
    y1 = LY - KKPR["rumija_utara"] - KKPR["gsb_utara"]
    xs = np.linspace(x0, x1, n)
    tinggi = []
    for x in xs:
        bawah = kedalaman_sempadan(x)
        if tanpa_labil and LX - LABIL_STA[1] <= x <= LX - LABIL_STA[0]:
            bawah += LABIL_LEBAR
        tinggi.append(max(0.0, y1 - bawah))
    return float(np.trapezoid(tinggi, xs))


def ringkasan():
    lp = lahan_perencanaan().area
    a6, a6l, a4 = amplop(6).area, amplop(6, False).area, amplop(4).area
    return {
        "persil": persil().area, "sempadan": ruang_sempadan().area,
        "rumija": rumija().difference(ruang_sempadan()).area, "lahan_perencanaan": lp,
        "kdb_maks": KKPR["KDB"] * lp, "klb_maks": KKPR["KLB"] * lp, "kdh_min": KKPR["KDH"] * lp,
        "ktb_maks": KKPR["KTB"] * lp,
        "amplop_6": a6, "amplop_6_dengan_labil": a6l, "amplop_4": a4, "labil": zona_labil().area,
        "owner_tapak": KKPR["KDB"] * LX * LY,
        "tor_kdb": TOR["KDB"] * LX * LY, "tor_klb": TOR["KLB"] * LX * LY,
    }


# ------------------------------------------------------------------ penilaian
def telaah():
    """Temuan telaah data owner Tahap 3 (semua berkas), langkah yang menyelesaikan."""
    r = ringkasan()
    return [
        ["Surat sempadan", "STA 0+000 di sudut tenggara, bertambah ke barat; tabel memakai STA, bukan x",
         "x = 140 - STA; dicek: puncak STA 0+140 (x 0) 14,0 m dan STA 0+020 (x 120) 8,0 m sama dengan TOR Lampiran B",
         "3.2"],
        ["Surat sempadan", "Puncak tebing mundur setelah longsoran Januari 2027",
         "Mundur 1,0-2,0 m di x 80-100 (STA 0+040 s.d. 0+060) dibanding Agustus 2026; zona labil butir 4 meliputi x 70-110",
         "3.2, Tahap 6"],
        ["Surat sempadan", "Ruang sempadan tidak boleh diurug atau diperkeras (butir 3); zona labil maks urugan 1,0 m (butir 4)",
         "Bertentangan dengan arahan owner butir 3 (urug seluruh persil ke +11,50)", "3.2, 3.3"],
        ["Surat sempadan", "Q50 +13,69 m dpl, datum dpl (bukan datum lokal)",
         "Datum lokal = dpl - 1,840 (Data Hidrologi lembar 1): Q50 = +11,85 lokal, di atas lantai dasar +11,80 TOR", "3.3"],
        ["PKKPR", "KDB 50 %, KLB 2,4, KDH 20 % (lebih ketat dari TOR 60 %, 3,0, 15 %) dan dihitung dari luas lahan perencanaan",
         f"Lahan perencanaan {fmt(r['lahan_perencanaan'], 0)} m², bukan 12.600 m²", "3.2"],
        ["PKKPR", "Rencana rumija: utara +2 m, barat +1 m masuk persil; GSB diukur dari rencana rumija",
         "GSB utara efektif 14 m dari batas persil (TOR 10 m); GSB barat 6 m", "3.2"],
        ["PKKPR", "Jarak bebas timur 6 m untuk 5-8 lantai (4 m sampai 4 lantai)",
         "Menara ≥ 6 m dari batas timur (≥ 10 m dari gudang); podium ≤ 4 lantai boleh 4 m", "3.2, 3.4"],
        ["PKKPR", "Akses dari jalan kolektor maks 2 titik, ≥ 50 m dari simpang barat laut; jalan barat hanya servis/ambulans",
         "Pintu masuk utama di x ≥ 50 m", "3.4"],
        ["PKKPR", "Tanpa tambahan limpasan (kolam retensi); urugan tidak boleh menutup aliran persil sekitar", "-",
         "3.3"],
        ["PKKPR", "Andalalin, dokumen lingkungan, rekomendasi helipad sebelum PBG", "Masuk jadwal perizinan", "3.2, Tahap 9"],
        ["Surat owner butir 1", "Tapak 6.300 m² dihitung dari luas persil bruto",
         f"KDB maks {fmt(r['kdb_maks'], 0)} m² dari lahan perencanaan; amplop menara {fmt(r['amplop_6'], 0)} m²", "3.2"],
        ["Surat owner butir 2", "Lantai dasar diturunkan ke +11,50; MEP memakai +11,30 dengan acuan +11,20",
         "Di bawah Q50 (+11,85 lokal); perlu analisis peil", "3.3"],
        ["Surat owner butir 3", "Urug 22.000 m³ tanah merah 6 minggu termasuk sempadan dan tepi sungai",
         "Dilarang di ruang sempadan; kecepatan urugan di tanah lunak (beban > 3 su, langkah 2.8)", "3.3"],
        ["Surat owner butir 5 + Kantor SAR", "Helikopter rencana H145 3.700 kg, padahal SAR meminta landasan untuk AW139 6.800 kg",
         "Helikopter rencana yang menentukan: AW139 (lebih berat dan lebih panjang)", "3.6, Tahap 4"],
        ["Data Hidrologi", "Nol papan duga 1990-2007 dipakai +3,150, padahal pengikatan ulang 2008 +3,500",
         "Elevasi 1990-2007 0,35 m terlalu rendah; analisis frekuensi penyedia perlu diulang", "3.3"],
        ["Data Hidrologi", "Data 1999 hanya 6 bulan (papan rusak); 2027 belum masuk deret", "Perlakuan data tidak lengkap",
         "3.3"],
        ["Data MEP", "Gedung utilitas +11,30 berdasar banjir +11,20 (bukan banjir rencana)",
         "Utilitas vital di atas banjir rencana + jagaan (keputusan rapat no. 2)", "3.3, 3.4"],
        ["Data MEP", "IPAL tanam di (125, 78) dan tangki solar tanam di (30, 72)",
         "IPAL di zona GSB utara dan zona gambut tebal; tangki di zona gambut; tinjau letak", "3.4"],
    ]


def tanggapan_owner():
    r = ringkasan()
    return [
        ["1 Tapak 6.300 m²", "Tidak dapat dipenuhi",
         f"KDB 50 % dihitung dari lahan perencanaan {fmt(r['lahan_perencanaan'], 0)} m² (PKKPR persyaratan 2), "
         f"sehingga tapak maks {fmt(r['kdb_maks'], 0)} m². Amplop menara 5-8 lantai di luar zona labil "
         f"{fmt(r['amplop_6'], 0)} m²; podium ≤ 4 lantai {fmt(r['amplop_4'], 0)} m². KLB 2,4 memberi luas lantai maks "
         f"{fmt(r['klb_maks'], 0)} m², cukup untuk kebutuhan ±14.800-17.000 m²."],
        ["3 Urugan seluruh persil", "Tidak dapat dipenuhi untuk ruang sempadan",
         f"Ruang sempadan {fmt(r['sempadan'], 0)} m² tidak boleh diurug atau diperkeras (surat sempadan butir 3). Di zona labil "
         f"{fmt(r['labil'], 0)} m² urugan maks 1,0 m sampai tebing diperkuat (butir 4). Volume, kecepatan, dan mutu urugan "
         "dibahas di 3.3."],
        ["6 Jalur dari sungai ke IGD", "Dapat dipenuhi bersyarat",
         "Jalan inspeksi berpermukaan lolos air dan dermaga apung boleh di ruang sempadan dengan izin pemanfaatan "
         "ruang sempadan (butir 3); jalur tidak boleh menambah beban di zona labil."],
    ]


def fmt(v, d=2):
    s = f"{v:,.{d}f}"
    return s.replace(",", "#").replace(".", ",").replace("#", ".")


# ------------------------------------------------------------------ Excel
def buat_excel(keluar=BERKAS):
    import openpyxl
    from openpyxl.styles import PatternFill

    from format_dokumen import AI, Lembar, set_font_bawaan

    r = ringkasan()
    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)

    lb = Lembar(wb.create_sheet("Petunjuk"), 1, "Petunjuk kajian aturan tapak (langkah 3.2)", [6, 120])
    lb.catatan(LABEL + " " + LABEL_AI)
    lb.kosong()
    lb.tabel(["No", "Petunjuk"], [[i + 1, t] for i, t in enumerate([
        "Sumber: surat penetapan sempadan SA.02.03/BPSB/117 (22 Feb 2027), PKKPR 503/KKPR/0412/III/2027 (1 Mar 2027), "
        "surat owner 034/YKTB/III/2027 (8 Mar 2027), TOR Lampiran B dan C. Semua di '03 Desain Konsep/Data Owner/'.",
        "Koordinat lokal: titik nol sudut barat daya persil, x ke timur, y ke utara. STA surat sempadan diubah ke x = 140 - STA.",
        "Luas lahan perencanaan = persil - rencana rumija - ruang sempadan (PKKPR persyaratan 2). Lembar 3 memakai rumus "
        "Excel (trapesium); Python memakai poligon shapely (cek silang T-35).",
        "Amplop bangunan = daerah di dalam GSB rencana rumija, jarak bebas timur, dan di utara garis sempadan; zona labil "
        "dikeluarkan sampai tebing diperkuat. Luas dihitung dua cara (T-36).",
        "Gambar GK-01: '3.2 Gambar Batasan Tapak.pdf'. Peraturan sempadan sungai (Permen PUPR 28/2015) belum ada di acuan; "
        "kajian ini memakai penetapan instansi (simulasi) sebagai dasar.",
    ])], rata=list("cl"))

    # Lembar 2: sempadan
    lb = Lembar(wb.create_sheet("Sempadan"), 2, "Garis sempadan sungai dan puncak tebing",
                [8, 8, 14, 14, 14, 14, 14, 12])
    lb.catatan(LABEL + " Kolom 'garis hitung' = 20 - puncak (butir 1) dengan rumus Excel; 'mundur' = puncak Agustus "
               "2026 (TOR Lampiran B, diinterpolasi) - puncak Februari 2027.")
    data = cek_sempadan()
    r0, r1, r2 = lb.tabel(
        ["STA", "x (m)", "Puncak tebing Feb 2027 di luar persil (m)", "Garis sempadan dari batas selatan (m)",
         "Garis hitung 20 - puncak (m)", "Puncak tebing Agu 2026 (m)", "Mundur (m)", "Zona labil"],
        [[f"0+{int(d['STA']):03d}", d["x"], d["puncak_2027"], d["garis"], None, round(d["puncak_2026"], 2), None,
          "ya" if d["labil"] else "-"] for d in data],
        rata=list("cccccccc"), fmt=[None, "0", "0.0", "0.0", "0.0", "0.00", "0.00", None], fill_kolom={4: AI, 6: AI})
    ws = lb.ws
    for rr in range(r1, r2 + 1):
        ws[f"G{rr}"] = f"={SEMPADAN_DARI_PUNCAK}-E{rr}"
        ws[f"I{rr}"] = f"=H{rr}-E{rr}"
    lb.ws.freeze_panes = f"A{r1}"

    # Lembar 3: luas
    lb3 = Lembar(wb.create_sheet("Luas Lahan"), 3, "Luas lahan perencanaan dan batas intensitas",
                 [6, 48, 18, 22, 40])
    lb3.catatan(LABEL + " Sel hijau berisi rumus Excel. Kolom Python dari skrip tahap3_tapak.py untuk cek silang.")
    baris3 = [
        [1, "Luas persil 140 × 90 (TOR 4.1; PKKPR ±12.600)", f"={LX}*{LY}", "m²", fmt(r["persil"])],
        [2, "Ruang sempadan sungai (trapesium tabel surat sempadan)",
         f"=SUMPRODUCT((Sempadan!D{r1 + 1}:D{r2}-Sempadan!D{r1}:D{r2 - 1})*(Sempadan!F{r1 + 1}:F{r2}+Sempadan!F{r1}:F{r2 - 1})/2)",
         "m²", fmt(r["sempadan"])],
        [3, "Rencana rumija utara 2 m × 140 m", f"={KKPR['rumija_utara']}*{LX}", "m²", "-"],
        [4, "Rencana rumija barat 1 m, dari garis sempadan sampai rumija utara",
         f"={KKPR['rumija_barat']}*({LY}-{KKPR['rumija_utara']}-Sempadan!F{r1})", "m²", "-"],
        [5, "Luas lahan perencanaan = 1 - 2 - 3 - 4", None, "m²", fmt(r["lahan_perencanaan"])],
        [6, "KDB maks 50 % × lahan perencanaan", None, "m²", fmt(r["kdb_maks"])],
        [7, "KLB maks 2,4 × lahan perencanaan (luas lantai)", None, "m²", fmt(r["klb_maks"])],
        [8, "KDH min 20 % × lahan perencanaan (ruang sempadan tidak dihitung)", None, "m²", fmt(r["kdh_min"])],
        [9, "KTB maks 50 % × lahan perencanaan (tapak basement)", None, "m²", fmt(r["ktb_maks"])],
        [10, "Tapak menurut surat owner butir 1 (50 % × 12.600)", f"=0.5*{LX}*{LY}", "m²", fmt(r["owner_tapak"])],
        [11, "Kelebihan tapak owner terhadap KDB maks = 10 - 6", None, "m²", "-"],
    ]
    a0, a1, a2 = lb3.tabel(["No", "Uraian", "Nilai", "Satuan", "Python (cek silang)"], baris3,
                           rata=list("clccc"), fmt=[None, None, "#,##0.0", None, None], fill_kolom={2: AI})
    w3 = lb3.ws
    E = lambda n: f"E{a1 + n - 1}"  # noqa: E731  kolom nilai (kolom E) baris ke-n
    w3[E(5)] = f"={E(1)}-{E(2)}-{E(3)}-{E(4)}"
    w3[E(6)] = f"=0.5*{E(5)}"
    w3[E(7)] = f"=2.4*{E(5)}"
    w3[E(8)] = f"=0.2*{E(5)}"
    w3[E(9)] = f"=0.5*{E(5)}"
    w3[E(11)] = f"={E(10)}-{E(6)}"
    for rr in range(a1, a2 + 1):
        w3[f"E{rr}"].fill = PatternFill("solid", fgColor=AI)
    lb3.kosong()
    lb3.bagian("B", "Ketentuan TOR dan PKKPR")
    lb3.tabel(["No", "Ketentuan", "TOR (sementara)", "PKKPR", "Akibat"], [
        [1, "KDB maks", "60 % persil", "50 % lahan perencanaan", f"{fmt(r['tor_kdb'], 0)} → {fmt(r['kdb_maks'], 0)} m²"],
        [2, "KLB maks", "3,0 persil", "2,4 lahan perencanaan", f"{fmt(r['tor_klb'], 0)} → {fmt(r['klb_maks'], 0)} m²"],
        [3, "KDH min", "15 %", "20 % lahan perencanaan", f"≥ {fmt(r['kdh_min'], 0)} m² hijau di luar sempadan"],
        [4, "KTB maks", "-", "50 % lahan perencanaan", f"basement ≤ {fmt(r['ktb_maks'], 0)} m²"],
        [5, "Ketinggian", "8 lantai", "8 lantai atau 40 m termasuk bangunan atap", "ATAP +37,60; cek di 3.6"],
        [6, "GSB utara", "10 m dari batas", "12 m dari rencana rumija (+2 m)", "garis bangunan y ≤ 76"],
        [7, "GSB barat", "5 m dari batas", "5 m dari rencana rumija (+1 m)", "garis bangunan x ≥ 6"],
        [8, "Samping timur", "-", "4 m (≤ 4 lantai), 6 m (5-8 lantai)", "x ≤ 136 podium, x ≤ 134 menara"],
        [9, "Selatan", "GSB 5 m (keinginan owner)", "garis sempadan sungai", "6,0-15,5 m dari batas selatan"],
    ], rata=list("clccl"), beku=False)

    # Lembar 4: amplop
    lb4 = Lembar(wb.create_sheet("Amplop"), 4, "Amplop bangunan (cek silang dua cara)", [6, 60, 18, 18, 12])
    lb4.catatan(LABEL + " Cara 1 poligon shapely, cara 2 integrasi lebar per irisan x (14.001 irisan).")
    lb4.tabel(["No", "Amplop", "Cara 1 (m²)", "Cara 2 (m²)", "Selisih (%)"], [
        [1, "Menara 5-8 lantai, tanpa zona labil", r["amplop_6"], luas_amplop_strip(6), None],
        [2, "Menara 5-8 lantai, zona labil sudah diperkuat", r["amplop_6_dengan_labil"], luas_amplop_strip(6, False), None],
        [3, "Podium ≤ 4 lantai, tanpa zona labil", r["amplop_4"], luas_amplop_strip(4), None],
    ], rata=list("clccc"), fmt=[None, None, "#,##0.0", "#,##0.0", "0.000"], fill_kolom={2: AI, 3: AI, 4: AI})
    for rr in range(lb4.baris - 3, lb4.baris):
        lb4.ws[f"G{rr}"] = f"=ABS(E{rr}-F{rr})/E{rr}*100"

    # Lembar 5-6: telaah dan tanggapan
    lb5 = Lembar(wb.create_sheet("Telaah Data Owner"), 5, "Telaah data owner Tahap 3", [6, 18, 48, 52, 12])
    lb5.catatan(LABEL + " Semua berkas data owner ditelaah sebelum dipakai (pelajaran evaluasi: cek murah setiap data).")
    lb5.tabel(["No", "Berkas", "Temuan", "Akibat / angka", "Langkah"], [[i + 1] + t for i, t in enumerate(telaah())],
              rata=list("cllll"), fill=AI)
    lb6 = Lembar(wb.create_sheet("Tanggapan Owner"), 6, "Tanggapan atas arahan owner (bagian tapak)", [6, 22, 22, 90])
    lb6.catatan(LABEL + " Butir lain surat owner dijawab di langkah 3.3 (peil, urugan), 3.4-3.5 (parkir), 3.6 (helikopter).")
    lb6.tabel(["No", "Arahan owner", "Tanggapan", "Dasar dan angka"], [[i + 1] + t for i, t in enumerate(tanggapan_owner())],
              rata=list("clll"), fill=AI)
    lb6.kosong()
    lb6.bagian("B", "Akibat untuk desain konsep")
    lb6.tabel(["No", "Butir", "Nilai", "Dipakai di"], [
        [1, "Amplop menara", f"{fmt(r['amplop_6'], 0)} m²", "3.4 zonasi, 3.6 grid"],
        [2, "Tapak maks (KDB)", f"{fmt(r['kdb_maks'], 0)} m²", "3.4 massa podium"],
        [3, "Luas lantai maks (KLB)", f"{fmt(r['klb_maks'], 0)} m²", "3.4, 3.8"],
        [4, "Tapak basement maks (KTB)", f"{fmt(r['ktb_maks'], 0)} m²", "3.5"],
        [5, "Hijau min (KDH)", f"{fmt(r['kdh_min'], 0)} m² di luar sempadan", "3.3 drainase, 3.4"],
        [6, "Garis tepi selatan bangunan", "garis sempadan + 10 m di x 70-110", "3.4, 3.7, Tahap 6"],
    ], rata=list("clll"), beku=False)
    wb.save(keluar)
    return keluar


# ------------------------------------------------------------------ gambar (CAD asli)
def kontur_gambut(level=3.0):
    """Garis tebal organik U3 = level (m), interpolasi linear titik penyelidikan (langkah 2.2)."""
    from contourpy import contour_generator
    from scipy.interpolate import griddata

    import tahap2_stratigrafi as st

    titik = st.semua_titik()
    pts = np.array([[t["x"], t["y"]] for t in titik])
    nil = np.array([st.tebal_organik(t) for t in titik])
    gx, gy = np.meshgrid(np.linspace(0, LX, 141), np.linspace(0, LY, 91))
    gz = griddata(pts, nil, (gx, gy), method="linear")
    return [g for g in contour_generator(gx, gy, np.ma.masked_invalid(gz)).lines(level) if len(g) > 2]


def gambar_cad(status=None):
    """GK-01 digambar langsung di CADCraft: model space 1:1 (mm), layout A3 1:750 berkop KOP_A3."""
    from cad_lembar import STATUS_SETUJU, Gambar

    r = ringkasan()
    s = cek_sempadan()
    dwg = KELUAR / "Gambar" / "DWG" / "GK-01 Batasan Tapak.dwg"
    png = KELUAR / "Gambar" / "GK-01 Batasan Tapak.png"
    with Gambar(750) as g:
        # sungai dan tebing
        pk27 = [(d["x"], -d["puncak_2027"]) for d in s]
        pk26 = [(x, -puncak_2026(x)) for x in range(0, 141, 10)]
        g.layer("C-SUNGAI", 150, 0.18)
        for k, dy in enumerate((4, 7, 10)):
            g.pline([(x, yy - dy) for x, yy in pk27[k:len(pk27) - k]], "C-SUNGAI", garis="DASHED")
        g.teks((70, -24), "SUNGAI BATANGHARI", "C-SUNGAI", 3.0, j="MC", tebal=True)
        g.layer("C-TEBING", 34, 0.35)
        g.pline(pk27, "C-TEBING", tebal=0.5)
        g.layer("C-TEBING-2026", 34, 0.18, "DASHED")
        g.pline(pk26, "C-TEBING-2026")
        g.legenda_tambah("garis", "Puncak tebing Feb 2027 (surat sempadan)", warna=34, tebal=0.5)
        g.legenda_tambah("garis", "Puncak tebing Agu 2026 (TOR Lampiran B)", warna=34, garis="DASHED", tebal=0.18)
        # ruang sempadan, zona labil, rumija
        g.layer("C-SEMPADAN", 3, 0.35)
        g.arsir(list(ruang_sempadan().exterior.coords)[:-1], "C-SEMPADAN", pola="DOTS", skala_pola=0.6, warna=3)
        g.legenda_tambah("arsir", "Ruang sempadan sungai: tanpa bangunan dan urugan",
                         pola="DOTS", skala_pola=0.6, warna=3)
        g.layer("C-LABIL", 1, 0.35)
        g.arsir(list(zona_labil().exterior.coords)[:-1], "C-LABIL", pola="ANSI31", skala_pola=1.2, warna=1)
        g.legenda_tambah("arsir", "Zona labil: urugan maks 1,0 m, tanpa bangunan",
                         pola="ANSI31", skala_pola=1.2, warna=1)
        g.layer("C-RUMIJA", 8, 0.25)
        rj = rumija()
        for geom in getattr(rj, "geoms", [rj]):
            g.arsir(list(geom.exterior.coords)[:-1], "C-RUMIJA", pola="ANSI37", skala_pola=0.8, warna=8)
        g.legenda_tambah("arsir", "Rencana rumija (diserahkan saat pelebaran)", pola="ANSI37", skala_pola=0.8, warna=8)
        # amplop
        g.layer("C-AMPLOP", 5, 0.5)
        g.pline(list(amplop(6).exterior.coords)[:-1], "C-AMPLOP", tutup=True, tebal=0.7)
        g.teks((70, 50), "AMPLOP MENARA", "C-AMPLOP", 3.0, j="MC", tebal=True)
        g.teks((70, 45.5), f"{fmt(r['amplop_6'], 0)} m²", "C-AMPLOP", 2.4, j="MC")
        g.legenda_tambah("garis", "Amplop menara 5-8 lantai", tebal=0.7)
        g.layer("C-AMPLOP-PODIUM", 5, 0.25, "DASHED")
        g.pline(list(amplop(4).exterior.coords)[:-1], "C-AMPLOP-PODIUM", tutup=True)
        g.legenda_tambah("garis", "Amplop podium ≤ 4 lantai", garis="DASHED", tebal=0.25)
        # gambut 3 m
        g.layer("C-GAMBUT", 32, 0.35, "DASHDOT")
        for seg in kontur_gambut():
            g.pline([tuple(p) for p in seg], "C-GAMBUT")
        g.teks((107.5, 82.0), "TEBAL GAMBUT 3 M", "C-GAMBUT", 1.6, warna=32)
        # jalan
        g.layer("C-JALAN", 8, 0.25)
        g.pline([(-8, 90), (148, 90)], "C-JALAN")
        g.pline([(-8, 102), (148, 102)], "C-JALAN")
        g.pline([(-6, -6), (-6, 90)], "C-JALAN")
        g.layer("C-JALAN-RENCANA", 8, 0.18, "DASHED")
        g.pline([(-8, 104), (148, 104)], "C-JALAN-RENCANA")
        g.pline([(-7, -6), (-7, 104)], "C-JALAN-RENCANA")
        g.teks((70, 96), "JALAN KOLEKTOR (EKSISTING 12 M, RENCANA 16 M)", "C-JALAN", 2.4, j="MC", tebal=True)
        g.teks((-3.5, 45), "JALAN LINGKUNGAN (6 M, RENCANA 8 M)", "C-JALAN", 2.0, j="MC", rot=90, tebal=True)
        g.layer("C-AKSES", 30, 0.7)
        g.pline([(50, 90.6), (140, 90.6)], "C-AKSES")
        g.teks((95, 92.4), "ZONA AKSES KOLEKTOR (MAKS 2 TITIK, ≥ 50 M DARI SIMPANG)", "C-AKSES", 1.6,
               j="MC", warna=30)
        # gudang
        g.layer("C-GUDANG", 8, 0.35)
        x, y, w, h = GUDANG
        g.arsir([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], "C-GUDANG", pola="ANSI31", skala_pola=1.5, warna=8)
        g.teks((x + w / 2, y - 3), "GUDANG TETANGGA", "C-GUDANG", 2.2, j="MC", tebal=True)
        # persil, GSB
        g.layer("C-PERSIL", 7, 0.7, "PHANTOM")
        g.pline([(0, 0), (LX, 0), (LX, LY), (0, LY)], "C-PERSIL", tutup=True)
        g.legenda_tambah("garis", "Batas persil 140 × 90 m", warna=7, garis="PHANTOM", tebal=0.7)
        g.layer("C-GSB", 5, 0.25, "HIDDEN")
        g.pline([(0, 76), (LX, 76)], "C-GSB")
        g.pline([(6, 0), (6, LY)], "C-GSB")
        g.pline([(134, 0), (134, LY)], "C-GSB")
        g.legenda_tambah("garis", "Garis sempadan bangunan (PKKPR)", warna=5, garis="HIDDEN", tebal=0.25)
        g.teks((30, 73.6), "GSB UTARA (12 M DARI RENCANA RUMIJA)", "C-GSB", 1.6, warna=5)
        g.teks((8.2, 40), "GSB BARAT", "C-GSB", 1.6, rot=90, warna=5)
        g.teks((133.3, 40), "JARAK BEBAS TIMUR 6 M", "C-GSB", 1.6, rot=90, warna=5)
        # STA dan BM
        g.layer("C-STA", 7, 0.18)
        for d in s:
            if d["STA"] % 20 == 0:
                g.pline([(d["x"], 0), (d["x"], -1.2)], "C-STA")
                g.teks((d["x"], -1.8), f"STA 0+{int(d['STA']):03d}", "C-STA", 1.4, j="TC")
        g.titik_tinggi((0, 0), "BM-1 +10,000", teks_at=(-21, -10.5))
        g.pline([(-0.7, -0.7), (-5.2, -0.7), (-8, -9.3), (-11.5, -9.3)], "C-TEKS")
        # ukuran
        g.ukur((0, 0), (LX, 0), (70, -31))
        g.ukur((LX, 0), (LX, LY), (172, 45))
        g.ukur((0, LY - 2), (0, 76), (-12, 82))
        g.ukur((0, LY), (0, LY - 2), (-16, 89))
        for xx in (20, 90, 130):
            g.ukur((xx, 0), (xx, kedalaman_sempadan(xx)), (xx + 3, kedalaman_sempadan(xx) / 2))
        g.ukur((110, kedalaman_sempadan(110)), (110, kedalaman_sempadan(110) + 10), (114, kedalaman_sempadan(110) + 5))
        g.ukur((LX, 30), (GUDANG[0], 30), (142, 34))
        g.ukur((134, 60), (LX, 60), (137, 64))
        g.grid_koordinat(0, 140, 0, 80, 20, label=False)
        g.lembar("GK-01", "Batasan tapak", "1:750", pusat=(76, 38),
                 subjudul="Surat sempadan SA.02.03/BPSB/117 (22 Feb 2027); PKKPR 503/KKPR/0412/III/2027 (1 Mar 2027); "
                          "TOR Lampiran B; tebal gambut langkah 2.2",
                 status=status or STATUS_SETUJU,
                 catatan=[
                     f"Lahan perencanaan {fmt(r['lahan_perencanaan'], 0)} m²; KDB maks {fmt(r['kdb_maks'], 0)} m²; "
                     f"KLB maks {fmt(r['klb_maks'], 0)} m²; KDH min {fmt(r['kdh_min'], 0)} m².",
                     "Garis sempadan 20 m dari puncak tebing Feb 2027; STA dihitung dari sudut tenggara.",
                     "Q50 +13,69 m dpl = +11,85 lokal (lokal = dpl - 1,840).",
                     "Ukuran dalam meter; tanda + grid koordinat 20 m.",
                 ])
        g.skala_grafis(205, 22, 50)
        g.panah_utara(318, 262, 10)
        g.simpan(dwg, PDF, png)
    return dwg


def buat():
    buat_excel()
    gambar_cad()
    return BERKAS, PDF


if __name__ == "__main__":
    import json

    print(json.dumps({k: round(v, 1) for k, v in ringkasan().items()}, indent=1))
    print(buat())
