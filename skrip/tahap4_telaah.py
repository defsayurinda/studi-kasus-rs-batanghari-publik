"""Tahap 4 langkah 4.0: telaah data skenario Tahap 4 (Vs dalam + HVSR, data beban MEP rinci, surat owner).

DATA SIMULASI untuk studi kasus portofolio. Disusun AI atas permintaan Defsa (20 Nov 2026); draf, menunggu persetujuan
Defsa. Kunci jawaban tidak dibuka.

Acuan: SNI 1726:2019 Tabel 5 hal. 29 (SB batuan v̄s 750-1500 m/s), Pasal 6.10.1.1 hal. 40 (gerak batuan dasar
kelas situs SB); SESAME (2004) untuk kriteria puncak HVSR [Literatur, belum ada di acuan/].
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import openpyxl

AKAR = Path(__file__).resolve().parents[1]
VS = AKAR / "01 Penyelidikan Tanah" / "Penyelidikan Tambahan" / "Geofisika Vs Dalam.xlsx"
MEP = AKAR / "04 Struktur Atas" / "Data Owner" / "Data Beban MEP Rinci.xlsx"
BERKAS = AKAR / "04 Struktur Atas" / "4.0 Telaah Data Tahap 4.xlsx"
LABEL = "DATA SIMULASI untuk studi kasus portofolio. Bukan data proyek nyata. Tidak untuk konstruksi."
STATUS = "draf, menunggu persetujuan Defsa"
LABEL_AI = f"DIISI AI ATAS PERMINTAAN DEFSA (20 Nov 2026), sel hijau; {STATUS}. Kunci jawaban tidak dibuka."
JARAK_SUMBER = 3.0      # m, sumber S dari mulut lubang (lembar Downhole BH-9)
GANTI_PEMICU = 47.0     # m, pembacaan pertama dengan sakelar cadangan


# ------------------------------------------------------------------ downhole
def baca_downhole(berkas=VS):
    ws = openpyxl.load_workbook(berkas, data_only=True)["Downhole BH-9"]
    d, t = [], []
    for r in ws.iter_rows(values_only=True):
        v = [x for x in r if x is not None]
        if len(v) == 2 and all(isinstance(x, (int, float)) for x in v):
            d.append(float(v[0]))
            t.append(float(v[1]) / 1000.0)
    return np.array(d), np.array(t)


def koreksi_lintasan(d, t, x=JARAK_SUMBER):
    """Waktu tegak: t · d / √(d² + x²)."""
    return t * d / np.sqrt(d ** 2 + x ** 2)


def loncatan_pemicu(d, tc, z=GANTI_PEMICU):
    """Selisih waktu (s) garis 40-46 m dan 47-56 m di kedalaman 46,5 m (Vs kedua ruas hampir sama)."""
    a = np.polyfit(d[(d >= 40) & (d < z)], tc[(d >= 40) & (d < z)], 1)
    b = np.polyfit(d[(d >= z) & (d <= 56)], tc[(d >= z) & (d <= 56)], 1)
    return float(np.polyval(b, z - 0.5) - np.polyval(a, z - 0.5)), 1 / a[0], 1 / b[0]


def waktu_terkoreksi(berkas=VS):
    d, t = baca_downhole(berkas)
    tc = koreksi_lintasan(d, t)
    off = loncatan_pemicu(d, tc)[0]
    tk = np.where(d >= GANTI_PEMICU, tc - off, tc)
    return d, t, tc, tk, off


RUAS = [(1, 3), (3, 6), (6, 10), (10, 14), (14, 19), (19, 24), (24, 30), (30, 34), (34, 40), (40, 46), (46, 47),
        (47, 52), (52, 56), (56, 62), (62, 70), (70, 80)]


def vs_ruas(d, tt, a, b):
    m = (d >= a) & (d <= b)
    return float(1 / np.polyfit(d[m], tt[m], 1)[0])


def vs30(d, tc):
    return 30.0 / float(np.interp(30.0, d, tc))


def frek_seperempat(d, tk, z):
    """f = 1 / (4 Σh/Vs) dengan waktu tegak terkoreksi sampai kedalaman z."""
    return 1.0 / (4.0 * float(np.interp(z, d, tk)))


# ------------------------------------------------------------------ MEP: beban atap podium utara
def beban_atap(berkas=MEP):
    ws = openpyxl.load_workbook(berkas, data_only=True)["Daftar Alat"]
    hasil = []
    for r in ws.iter_rows(values_only=True):
        v = list(r)
        kode = next((x for x in v if isinstance(x, str) and x.startswith("M-")), None)
        if not kode:
            continue
        i = v.index(kode)
        jml, bidang, berat = v[i + 2], v[i + 3], v[i + 9]
        if "Atap podium utara" in str(bidang):
            hasil.append((kode, v[i + 1], int(jml), float(berat)))
    return hasil


def temuan_vs(r):
    return [
        ["V-1", "Downhole BH-9 46-47 m; kesimpulan penyedia butir 2",
         f"Lapisan Vs 167 m/s di 46-47 m palsu. Waktu tempuh meloncat {r['off'] * 1000:.2f} ms tepat saat sakelar "
         f"pemicu diganti (catatan lapangan 11 Juni 2027); Vs 40-46 m {r['vs_a']:.0f} dan 47-56 m {r['vs_b']:.0f} m/s "
         "hampir sama.",
         "Waktu ≥ 47 m dikurangi loncatan; lapisan 40-56 m dipakai Vs ±408 m/s. Butir 2 penyedia ditolak.", "Diperbaiki"],
        ["V-2", "Kesimpulan penyedia butir 3 (batuan dasar teknis 33-34 m, Vs ≥ 360)",
         "Tidak sesuai SNI 1726:2019 Pasal 6.10.1.1 hal. 40: gerak masukan adalah MCER batuan kelas situs SB "
         "(Tabel 5 hal. 29: v̄s 750-1.500 m/s). Pasir padat U7 (Vs ±400) dan batulempung lapuk (Vs 490-600) belum "
         "batuan SB; memotong kolom di 33 m membuang amplifikasi lapisan 33-85 m.",
         "Kolom tanah dimodelkan sampai lapisan keras ±85 m, lalu setengah ruang Vs 750 m/s [Asumsi, batas bawah SB]; "
         "kepekaan 79/93 m dan Vs 1.000 m/s.", "Ditolak"],
        ["V-3", "Kesimpulan penyedia butir 4 (f0 ±2,5 Hz, T ±0,40 s)",
         f"Puncak tertinggi HVSR (2,3-2,7 Hz) adalah resonansi lempung lunak U4 di atas pasir U5: 1/(4Σh/Vs) sampai "
         f"9,5 m = {r['f95']:.2f} Hz. Frekuensi dasar endapan lebih rendah: sampai 33 m {r['f33']:.2f} Hz (bahu kurva "
         f"1,3-1,5 Hz), sampai 80 m {r['f80']:.2f} Hz; kajian kota dataran banjir 1,0-1,6 Hz. Periode situs 0,40 s "
         "terlalu pendek padahal T gedung ±0,5-0,8 s.",
         "Periode dasar dari fungsi transfer model 4.1 dan dicocokkan dengan HVSR (cek silang T-66).", "Ditolak"],
        ["V-4", "HVSR H-4 (x 128, y 56)",
         "Puncak sangat tajam 3,17 Hz dengan komponen vertikal ikut naik dan mesin pendingin gudang menyala: puncak "
         "industri, bukan resonansi tanah (SESAME 2004 [Literatur]). Titik juga di luar gedung.",
         "H-4 tidak dipakai.", "Dikeluarkan"],
        ["V-5", "HVSR H-5 (x 66, y 82)",
         "5 dari 6 kriteria; 10 menit pertama hujan. Amplitudo tertinggi wajar di zona gambut tebal utara.",
         "Dipakai sebagai pendukung saja.", "Catatan"],
        ["V-6", "Informasi regional; kesimpulan penyedia butir 5 (rata-rata ±70 m)",
         "Rata-rata mencampur SB-4 di perbukitan (24 m). Sumur dataran banjir SB-1..SB-3: 84, 93, 79 m (rata 85 m).",
         "Kedalaman lapisan keras 85 m (kepekaan 79 dan 93 m).", "Diperbaiki"],
        ["V-7", "Kesimpulan penyedia butir 1 (Vs30 ±156 m/s)",
         f"Dicek ulang dari waktu tegak di 30 m: Vs30 = {r['vs30']:.0f} m/s; cocok, kelas SE menurut v̄s, tetap SF "
         "karena U5 mudah likuifaksi (2.5-2.6).", "Dipakai.", "Cocok"],
        ["V-8", "Lembar Vs Interval (pengolahan penyedia)",
         "Koreksi lintasan miring dan regresi per ruas diulang AI: sama dengan penyedia (selisih ≤ 1 m/s) kecuali "
         "ruas 46-47 m (V-1).", "Dipakai setelah V-1.", "Cocok"],
        ["V-9", "Log BH-9",
         "Elevasi atas lapisan cocok dengan kedalaman. Urutan U1-U7 sama dengan BH-5 (zona selatan); lempung organik "
         "0,4 m di 1,51-1,91 m. Di bawah U7: batulempung lapuk 54,9-71,4 m (U8) dan selang-seling batulempung-"
         "batupasir lapuk 71,4-80,45 m (U9), perolehan inti 60-85 %. Bor berhenti 80,45 m (lumpur hilang).",
         "U8, U9 dipakai di kolom tanah; 80-85 m diperpanjang dengan Vs U9 [Asumsi].", "Cocok"],
    ]


def temuan_mep(r):
    a = r["atap"]
    return [
        ["M-1", "Lembar Ringkasan Atap",
         f"Ringkasan memakai angka Data MEP Awal: chiller 153,2 kN (4 × 3.900 kg) dan tangki 1.550 kN (158 t). "
         f"Daftar Alat sendiri: chiller 4 × 115,8 = {a['chiller']:.1f} kN, tangki {a['tangki']:.0f} kN (210 m³). "
         f"Jumlah benar {a['jumlah']:.0f} kN, bukan 1.748,1 kN (+{(a['jumlah'] / 1748.1 - 1) * 100:.0f} %). "
         f"Rata-rata 1,5 kPa menyesatkan: tangki {a['q_tangki']:.1f} kPa lokal pada 72 m² (> 25,8 kPa di LA.4).",
         "Beban 4.2 dari Daftar Alat; konsultan MEP diminta memperbaiki ringkasan.", "Diperbaiki"],
        ["M-2", "Chiller M-01: dudukan langsung pada balok tanpa peredam",
         "Bertentangan dengan lembar Data Pabrikan butir 1 (pegas 25 mm bila di atas ruang hunian atau sensitif). Di "
         "bawah atap podium utara ada ruang LT2 (CSSD x 70-76, y 52-56) dan di sebelahnya MRI LT1 (syarat getaran "
         "≤ 0,5 × 10⁻³ g). Kompresor 49,2 Hz, kipas 14,5 Hz.",
         "Minta pegas 25 mm; frekuensi alami pelat/balok atap dicek terhadap 14,5 Hz di 4.5-4.6.", "Ditanyakan"],
        ["M-3", "Lembar Lift: pit +11,25..+11,45 'di atas muka air, tidak perlu kedap'",
         "Keliru. Muka tanah asli ±+9,1..+9,9; MAT 0,3-1,5 m di bawahnya; tinggi tekan akuifer desain +11,20 (Tahap 2); "
         "banjir Q50 +11,85, Q100 +12,31 (LA.2). Dasar pit di bawah muka banjir rencana.",
         "Pit lift kedap air dan dicek gaya angkat di Tahap 5.", "Ditolak"],
        ["M-4", "Surat owner butir 2 dan 3 (atap LT4 baja ringan; helipad dipakai sejak tahap 1)",
         "Bertentangan: helipad dirancang di atap menara +38,65 yang baru dibangun bersama LT5-LT6; atap tahap 1 di "
         "LT4 hanya baja ringan sementara.",
         "Perlu keputusan owner/Defsa: (a) pelat atap LT4 beton untuk helipad sementara (+26,05; struktur dan jalur "
         "terbang dicek), (b) helipad permukaan sementara di tapak, atau (c) evakuasi udara mulai tahap 2.",
         "Diputuskan Defsa 20 Nov 2026: (c) evakuasi udara mulai tahap 2"],
        ["M-5", "Surat owner butir 1 (LT3 cangkang tanpa instalasi) vs Daftar Alat M-10..M-12",
         "AHU kamar operasi, ICU, dan CSSD ada di ruang AHU LT3 (x 63-83, y 28-49), padahal yang dilayani (LT2) "
         "beroperasi sejak tahap 1.",
         "Ruang AHU LT3 masuk tahap 1 (beban alat ±340 kN + gantung 0,8 kPa); disampaikan ke owner.", "Ditanyakan"],
        ["M-6", "Kipas buang M-06 di tepi atap menara",
         "Area aman helipad 33,3 m lebih lebar dari menara 24 m (LA.4), jadi tepi atap termasuk area aman; benda "
         "tetap setinggi 1,0 m tidak diizinkan di sana [Asumsi: acuan helipad belum ada di acuan/].",
         "Kipas dipindah ke atap LT3 barat atau dibuat rata dek; koordinasi MEP.", "Ditanyakan"],
        ["M-7", "MRI R-03 dekat IGD dan jalur ambulans (surat owner butir 5)",
         "Syarat pabrikan: benda logam bergerak besar ≥ 12 m dari isocenter (80,5; 57,0). Tepi timur gedung x 84 hanya "
         "3,5 m dari isocenter; jalur ambulans/drop-off di sisi timur perlu dicek di rencana tapak. Lift ≥ 8 m: L-1..L-7 "
         "≥ 22 m, memenuhi. Pelat LT1 tanpa tulangan baja dalam radius 1 m (Tahap 5).",
         "Cek jarak jalur kendaraan di GK-03/GK-12; bila < 12 m, MRI digeser ke barat atau jalur dialihkan.",
         "Ditanyakan"],
        ["M-8", "Berat chiller 115,8 kN per unit (Data MEP Awal 3.900 kg)",
         "Data awal terlalu ringan; 11,8 t wajar untuk chiller berpendingin udara 350 TR [Asumsi, cek brosur].",
         "Dipakai data baru.", "Catatan"],
        ["M-9", "Lembar Umum (elevasi)",
         "LT1 +12,85, tinggi lantai 4,5/4,5/4,2/4,2/4,2/4,2 m sampai atap +38,65: sama dengan 3.6 dan template BIM. "
         "Data MEP Awal (+11,30) sudah diganti.", "Dipakai.", "Cocok"],
        ["M-10", "Tangki air atap 150 + 60 m³ (surat owner butir 4)",
         "Naik dari 158 t (LA.4) menjadi 2.168 kN operasi; balok dudukan 7 buah @ 1,0 m.",
         "Balok khusus atap podium dihitung ulang di 4.6; biaya dicatat.", "Dipakai"],
    ]


def ringkas():
    d, t, tc, tk, off = waktu_terkoreksi()
    _, vs_a, vs_b = loncatan_pemicu(d, tc)
    atap = beban_atap()
    jml = {k: n * w for k, _, n, w in atap}
    chiller, tangki = jml["M-01"], jml["M-02"]
    return {
        "d": d, "t": t, "tc": tc, "tk": tk, "off": off, "vs_a": vs_a, "vs_b": vs_b,
        "vs_penyedia": [vs_ruas(d, tc, a, b) for a, b in RUAS],
        "vs_koreksi": [vs_ruas(d, tk, a, b) for a, b in RUAS],
        "vs30": vs30(d, tc),
        "f95": frek_seperempat(d, tk, 9.5), "f33": frek_seperempat(d, tk, 33.0), "f80": frek_seperempat(d, tk, 80.0),
        "atap": {"daftar": atap, "chiller": chiller, "tangki": tangki, "jumlah": sum(jml.values()),
                 "q_tangki": tangki / (12.0 * 6.0)},
    }


def buat_excel(keluar=BERKAS):
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from format_dokumen import AI, Lembar, set_font_bawaan

    r = ringkas()
    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)

    lb = Lembar(wb.create_sheet("Petunjuk"), 1, "Petunjuk telaah data Tahap 4", [6, 120])
    lb.catatan(LABEL + " " + LABEL_AI)
    lb.kosong()
    lb.tabel(["No", "Petunjuk"], [[i + 1, x] for i, x in enumerate([
        "Data yang ditelaah: 'Geofisika Vs Dalam.xlsx' (paket 12, 25 Juni 2027), 'Data Beban MEP Rinci.xlsx' (24 Mei "
        "2027), dan 'Surat Owner Data MEP dan Pentahapan.docx' (26 Mei 2027). Semua lembar dibaca, termasuk kesimpulan "
        "penyedia.",
        "Lembar 2: waktu tempuh downhole BH-9 diolah ulang dengan rumus Excel (koreksi lintasan miring, koreksi "
        "loncatan pemicu); kemiringan per ruas dari regresi Python.",
        "Lembar 3 dan 4: daftar temuan data Vs/HVSR (V-) dan MEP/owner (M-) dengan bukti dan tindakan.",
        "Lembar 5: beban alat atap podium utara dihitung ulang dari Daftar Alat (rumus Excel).",
        "Status: " + STATUS + ".",
    ])], rata=list("cl"))

    lb = Lembar(wb.create_sheet("Olah Downhole"), 2, "Waktu tempuh downhole BH-9 diolah ulang",
                [8, 14, 16, 16, 16])
    lb.catatan(LABEL + f" Sumber S {JARAK_SUMBER:.1f} m dari lubang. Waktu tegak = t·d/√(d²+3²). Pembacaan ≥ 47 m "
               "memakai sakelar pemicu cadangan; loncatan dikurangkan (sel kuning di bawah tabel).")
    r0 = lb.baris
    baris = [[float(d), float(t * 1000), None, None] for d, t in zip(r["d"], r["t"])]
    _, a, b = lb.tabel(["Kedalaman (m)", "Waktu terbaca (ms)", "Waktu tegak (ms)", "Waktu terkoreksi (ms)"],
                       baris, rata=list("cccc"), fmt=["0.0", "0.00", "0.00", "0.00"], fill_kolom={2: AI, 3: AI})
    ws = lb.ws
    lb.kosong()
    _, off_baris, _ = lb.tabel(["Besaran", "Nilai", "Satuan", "Cara"], [
        ["Loncatan pemicu", round(r["off"] * 1000, 3), "ms", "selisih garis 40-46 dan 47-56 m di 46,5 m"],
        ["Vs30 (waktu tegak 30 m)", f"=30/({lb.kol(2)}{a + 29}/1000)", "m/s", "30 / t(30 m)"],
    ], rata=list("lccl"), fmt=[None, "0.00", None, None], fill=AI, beku=False)
    for i in range(a, b + 1):
        ws[f"{lb.kol(2)}{i}"] = f"={lb.kol(1)}{i}*{lb.kol(0)}{i}/SQRT({lb.kol(0)}{i}^2+{JARAK_SUMBER}^2)"
        ws[f"{lb.kol(3)}{i}"] = (f"=IF({lb.kol(0)}{i}>={GANTI_PEMICU},{lb.kol(2)}{i}-${lb.kol(1)}${off_baris},"
                                 f"{lb.kol(2)}{i})")
    ws.freeze_panes = f"A{r0 + 1}"
    lb.kosong()
    lb.tabel(["Ruas (m)", "Vs penyedia (m/s)", "Vs ulang AI (m/s)", "Vs terkoreksi (m/s)", "Keterangan"],
             [[f"{x}-{y}", v0, round(v1), round(v2), "loncatan pemicu" if (x, y) == (46, 47) else ""]
              for (x, y), v0, v1, v2 in zip(RUAS, [73, 91, 106, 206, 225, 235, 262, 295, 391, 409, 167, 412, 404,
                                                   493, 494, 599], r["vs_penyedia"], r["vs_koreksi"])],
             rata=list("ccccl"), fmt=[None, "0", "0", "0", None], fill_kolom={2: AI, 3: AI}, beku=False)

    for no, nama, judul, data in [(3, "Telaah Vs", "Temuan data Vs dalam dan HVSR", temuan_vs(r)),
                                  (4, "Telaah MEP", "Temuan data beban MEP dan surat owner", temuan_mep(r))]:
        lb = Lembar(wb.create_sheet(nama), no, judul, [7, 26, 62, 42, 14])
        lb.catatan(LABEL + " " + LABEL_AI)
        lb.tabel(["Kode", "Data", "Temuan dan bukti", "Tindakan", "Status"], data, rata=list("cllll"),
                 fill_kolom={2: AI, 3: AI, 4: AI})

    lb = Lembar(wb.create_sheet("Beban Atap"), 5, "Beban alat atap podium utara dihitung ulang",
                [8, 60, 10, 18, 18])
    lb.catatan(LABEL + " Dari lembar Daftar Alat (berat operasi). Bandingkan dengan lembar Ringkasan Atap konsultan "
               "MEP: 1.748,1 kN.")
    _, a, b = lb.tabel(["Kode", "Uraian", "Jumlah", "Berat operasi per unit (kN)", "Jumlah (kN)"],
                       [[k, u, n, w, None] for k, u, n, w in r["atap"]["daftar"]],
                       rata=list("clccc"), fmt=[None, None, "0", "#,##0.0", "#,##0.0"], fill_kolom={4: AI})
    for i in range(a, b + 1):
        lb.ws[f"{lb.kol(4)}{i}"] = f"={lb.kol(2)}{i}*{lb.kol(3)}{i}"
    lb.tabel(["", "Jumlah", "", "Ringkasan MEP", "Jumlah"],
             [["", "Jumlah beban alat atap podium utara", "", 1748.1, f"=SUM({lb.kol(4)}{a}:{lb.kol(4)}{b})"],
              ["", "Tekanan tangki pada tapak 12,0 × 6,0 m (kPa)", "", 25.8,
               f"={lb.kol(4)}{a + 1}/(12*6)"]],
             rata=list("clccc"), fmt=[None, None, None, "#,##0.0", "#,##0.0"], fill_kolom={4: AI}, beku=False)

    keluar.parent.mkdir(parents=True, exist_ok=True)
    wb.save(keluar)
    return keluar


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    r = ringkas()
    print(f"loncatan {r['off'] * 1000:.2f} ms; Vs30 {r['vs30']:.1f}; f9,5 {r['f95']:.2f} f33 {r['f33']:.2f} "
          f"f80 {r['f80']:.2f} Hz")
    print(f"atap: {r['atap']['jumlah']:.1f} kN; tangki {r['atap']['q_tangki']:.1f} kPa")
    print(buat_excel())
