"""Tahap 2 langkah 2.3: Excel '02 Olah Data Tanah/2.3 Air Tanah.xlsx' (format wajib).

Jalankan:  .venv\\Scripts\\python.exe skrip\\tahap2_lembar_air_tanah.py
"""
from pathlib import Path

import openpyxl

import tahap2_air_tanah as at
from format_dokumen import AI, Lembar, set_font_bawaan

AKAR = Path(__file__).resolve().parents[1]
BERKAS = AKAR / "02 Olah Data Tanah" / "2.3 Air Tanah.xlsx"
LABEL = "DATA SIMULASI untuk studi kasus portofolio. Bukan data proyek nyata. Tidak untuk konstruksi."
LABEL_AI = ("DIISI AI ATAS PERMINTAAN DEFSA (19 Nov 2026), sel hijau; disetujui Defsa 19 Nov 2026. "
            "Kunci jawaban tidak dibuka.")
H_GRID = [5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.2]

PETUNJUK = [
    "Langkah 2.3 menafsirkan data air tanah: uji pemompaan PW-1 (k, T, S akuifer pasir U5), uji bertahap (kehilangan "
    "tinggi tekan sumur), piezometer PZ-2 s.d. PZ-4 dan PZ-1 terhadap muka sungai, usulan MAT desain, dan pemeriksaan "
    "blow-in dasar galian.",
    "Sumber rumus: Thiem akuifer tertekan FHWA GEC 5 (NHI-16-072) Pers. 10.24 hal. 10-47; FK blow-in ≥ 1,25 "
    "SNI 8460:2017 Pasal 10.3.6.7.2 hal. 211; uplift Pasal 13.2 hal. 280. Cooper-Jacob, pemulihan Theis-Jacob, uji "
    "bertahap Jacob, dan sumur bayangan dipakai sebagai cek silang [Literatur: dokumen belum ada di acuan/].",
    "Gambar pendukung di '2.3 Gambar Air Tanah.pdf': GT-06 hidrograf, GT-07 uji pemompaan, GT-08 batas dasar galian.",
    "Skrip: skrip/tahap2_air_tanah.py (analisis), tahap2_lembar_air_tanah.py (Excel), tahap2_gambar_air_tanah.py.",
]

CATATAN = [
    "Akuifer pasir U5 (tebal ±9,3 m di PW-1) tertekan: S ≈ 1,4 × 10⁻⁴, ditutup lempung lunak U4 di atas dan lempung "
    "kaku U6 di bawah. k ≈ 8 × 10⁻⁵ m/s (Thiem). Nilai ini 3-4 orde lebih besar dari laporan lama (1,2 × 10⁻⁸) dan "
    "sesuai perkiraan Hazen Tahap 1 (2,8-8,5 × 10⁻⁵, VERIFIKASI T-03).",
    "Penurunan muka air menjadi tunak setelah ±4 jam pemompaan: ada batas isian (sungai) yang memasok akuifer. "
    "Sumur bayangan dengan tebing pada ±49 m dari PW-1 memberi T yang sama dengan Thiem (selisih 6-8 %).",
    "Pengaruh kenaikan sungai selama uji (+0,18 m) dan pompa mati 18 menit pada jam ke-31: Thiem memakai selisih "
    "penurunan dua sumur pantau, jadi kenaikan latar yang sama di keduanya tidak berpengaruh; jendela tunak dipilih "
    "sebelum dan ±5 jam sesudah pompa mati.",
    "Uji bertahap: kehilangan sumur kecil (efisiensi 94-98 %). Bacaan PW-1 pada menit 400 (9,308 m) turun 0,9 m tanpa "
    "perubahan debit; dianggap salah baca dan tidak dipakai.",
    "Piezometer pasir mengikuti sungai dengan jeda 3 hari (PZ-2B, dekat tebing), 6 hari (PZ-3B), dan 7 hari (PZ-4B, "
    "utara); kenaikan di puncak banjir Januari 2027 61-84 % dari kenaikan sungai. Saat sungai surut, tinggi tekan pasir "
    "lebih tinggi dari sungai (aliran ke sungai).",
    "Data dibersihkan: sensor B pada 7-13 Des 2026 (terpengaruh pemompaan PW-1), PZ-3A 14 Feb 2027 (lonjakan setelah "
    "petir, 10,10 m), PZ-4B 24 Jan-2 Feb 2027 (logger mati).",
    "Tinggi tekan setimbang dari uji disipasi CPTu di pasir (+7,62 s.d. +7,77) cocok dengan piezometer B pada hari yang "
    "sama (VERIFIKASI T-16).",
    "Lempung (sensor A) dan pipa tegak SP-1: muka air 0,3-1,5 m di bawah muka tanah saat normal; saat lahan tergenang "
    "mengikuti muka genangan. Tinggi tekan lempung lebih tinggi dari pasir saat normal: aliran ke bawah (rembesan).",
    "Blow-in: tanpa galian pun FK di zona gambut (BH-3) hanya 1,20 bila tinggi tekan pasir +11,20 tanpa genangan; "
    "di lapangan banjir selalu disertai genangan yang menambah berat. Galian basement dalam (dasar ±+6) hanya aman "
    "bila tinggi tekan pasir ≤ ±+6,4-7,1: praktis hanya musim kemarau (Jul-Okt) atau dengan sumur pelepas tekanan. "
    "Rancangan galian dan dewatering di Tahap 6.",
    "Uji disipasi CPTu-5 9,0 m (120 menit) dan CPTu-8 24,0 m (60 menit) belum setimbang, tetapi t50 dibaca penyedia "
    "dengan u akhir sebagai patokan, bukan u0. Nilai t50 itu perlu dihitung ulang di langkah 2.4 (cv).",
]


def buat(keluar=BERKAS):
    up = at.ringkas_uji_pompa()
    bt = at.uji_bertahap_jacob()
    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)

    lb = Lembar(wb.create_sheet("Petunjuk"), 1, "Petunjuk langkah 2.3 air tanah", [6, 120])
    lb.catatan(LABEL + " " + LABEL_AI)
    lb.kosong()
    lb.tabel(["No", "Petunjuk"], [[i, t] for i, t in enumerate(PETUNJUK, start=1)], rata=list("cl"))

    # ---- Uji pompa
    lb = Lembar(wb.create_sheet("Uji Pompa"), 2, "Uji pemompaan PW-1 (debit tetap 72 jam)",
                [6, 30, 14, 12, 44])
    lb.catatan(LABEL + " Data: 'Uji Pompa dan Piezometer.xlsx' lembar Uji Debit Tetap dan Pemulihan. " + LABEL_AI)
    lb.kosong()
    lb.bagian("A", "Masukan Thiem (kondisi tunak)")
    r0 = lb.baris + 1
    masukan = [
        ("Q debit rata-rata setelah katup disetel", round(up["q_rata"] * 1000, 3), "L/s", "Menit 35-4.320, tanpa jeda"),
        ("r2 jarak OW-1", 10, "m", "Lembar Sumur dan Instrumen"),
        ("r1 jarak OW-2", 30, "m", "Lembar Sumur dan Instrumen"),
        ("s2 penurunan tunak OW-1", round(up["s1"], 3), "m", "Rata-rata menit 960-1.800 dan 2.160-4.320"),
        ("s1 penurunan tunak OW-2", round(up["s2"], 3), "m", "Idem"),
        ("B tebal akuifer di PW-1", at.TEBAL_AKUIFER, "m", "Langkah 2.2: U5 di BH-5 dan BH-2"),
    ]
    lb.tabel(["No", "Besaran", "Nilai", "Satuan", "Sumber / keterangan"],
             [[i + 1, a, b, c, d] for i, (a, b, c, d) in enumerate(masukan)], rata=list("clccl"),
             fmt=[None, None, "0.000", None, None], fill_kolom={2: AI}, beku=False)
    q, r2, r1, s2, s1, b = (f"E{r0 + i}" for i in range(6))
    lb.kosong()
    lb.bagian("B", "Hasil dan cek silang")
    r_k = lb.baris + 1
    hasil = [
        ["Thiem (FHWA GEC 5 Pers. 10.24 hal. 10-47)", f"={q}/1000*LN({r1}/{r2})/(2*PI()*{b}*({s2}-{s1}))*{b}",
         f"={q}/1000*LN({r1}/{r2})/(2*PI()*{b}*({s2}-{s1}))", "-", "Utama; tidak peka kenaikan latar"],
        ["Sumur bayangan, OW-1 (batas isian di tebing ±49 m)", up["T_bayangan"]["OW-1"],
         up["T_bayangan"]["OW-1"] / at.TEBAL_AKUIFER, "-", "[Literatur: teori sumur bayangan]"],
        ["Sumur bayangan, OW-2", up["T_bayangan"]["OW-2"], up["T_bayangan"]["OW-2"] / at.TEBAL_AKUIFER, "-", "Idem"],
        ["Cooper-Jacob, OW-1 (menit 1-20)", up["cj"]["OW-1"]["T"], up["cj"]["OW-1"]["T"] / at.TEBAL_AKUIFER,
         up["cj"]["OW-1"]["S"], "[Literatur: Cooper dan Jacob 1946]"],
        ["Cooper-Jacob, OW-2 (menit 3-20)", up["cj"]["OW-2"]["T"], up["cj"]["OW-2"]["T"] / at.TEBAL_AKUIFER,
         up["cj"]["OW-2"]["S"], "Idem; data awal sedikit"],
        ["Pemulihan Theis-Jacob, OW-1 (t' 1-20 menit)", up["T_pulih"], up["T_pulih"] / at.TEBAL_AKUIFER, "-",
         "[Literatur: Theis 1935]"],
        ["Hazen dari saringan (Tahap 1, VERIFIKASI T-03)", "-", "2,8-8,5 × 10⁻⁵", "-", "Perkiraan orde"],
        ["Laporan TRG (Tahap 1)", "-", 1.2e-8, "-", "Ditolak di Tahap 1"],
    ]
    lb.tabel(["No", "Metode", "T (m²/s)", "k (m/s)", "S / keterangan"],
             [[i + 1, h[0], h[1], h[2], h[4] if h[3] == "-" else f"S = {h[3]:.1e}; {h[4]}".replace(".", ",")]
              for i, h in enumerate(hasil)], rata=list("clccl"), fmt=[None, None, "0.00E+00", "0.00E+00", None],
             fill_kolom={2: AI, 3: AI, 4: AI}, beku=False)
    lb.ws._print_rows = None
    lb.catatan(f"k desain akuifer U5 [usulan]: 8 × 10⁻⁵ m/s (Thiem), rentang cek silang "
               f"{min(up['T_bayangan'].values()) / at.TEBAL_AKUIFER:.1e}-"
               f"{up['cj']['OW-2']['T'] / at.TEBAL_AKUIFER:.1e} m/s; S = 1,4 × 10⁻⁴.".replace(".", ",")
               .replace("8 × 10⁻⁵", "8 × 10⁻⁵"), fill=AI)
    _ = r_k

    # ---- Uji bertahap
    lb = Lembar(wb.create_sheet("Uji Bertahap"), 3, "Uji bertahap PW-1: kehilangan tinggi tekan sumur",
                [6, 12, 14, 14, 14, 44])
    lb.catatan(LABEL + " s_w = B Q + C Q² [Literatur: Jacob 1947; belum ada di acuan/]. Penurunan akhir tiap tahap "
               "(menit 90, 190, 290, 390). " + LABEL_AI)
    lb.kosong()
    r0 = lb.baris + 1
    baris = []
    for i, (qq, sw) in enumerate(zip(bt["q"], bt["sw"])):
        r = r0 + i
        baris.append([i + 1, round(qq * 1000, 3), round(sw, 3), f"=D{r}/(C{r}/1000)",
                      f"={bt['B']:.2f}*C{r}/1000/({bt['B']:.2f}*C{r}/1000+{bt['C']:.1f}*(C{r}/1000)^2)*100",
                      "Bacaan menit 400 (9,308 m) dianggap salah baca" if i == 3 else ""])
    lb.tabel(["Tahap", "Q (L/s)", "s_w (m)", "s_w/Q (s/m²)", "Efisiensi sumur (%)", "Catatan"], baris,
             rata=list("cccccl"), fmt=[None, "0.000", "0.000", "0", "0.0", None], fill_kolom={3: AI, 4: AI, 5: AI},
             beku=False)
    lb.catatan(f"Regresi s_w/Q = B + C Q: B = {bt['B']:.0f} s/m², C = {bt['C']:.0f} s²/m⁵. Kehilangan sumur kecil."
               .replace(".", ",", 0), fill=AI)

    # ---- Piezometer
    lb = Lembar(wb.create_sheet("Piezometer"), 4, "Piezometer terhadap muka sungai",
                [6, 12, 9, 10, 10, 9, 12, 14, 14, 36])
    lb.catatan(LABEL + " h(t) = a + b · H_sungai(t - L). L dipilih dengan korelasi terbesar (0-10 hari). Data harian "
               "27 Nov 2026-31 Mar 2027 (dibersihkan, lihat Catatan); PZ-1 mingguan Sep 2026-Mar 2027. " + LABEL_AI)
    lb.kosong()
    r0 = lb.baris + 1
    pk = at.puncak_banjir()
    baris = []
    for i, s in enumerate(at.SENSOR_B + at.SENSOR_A):
        g = at.regresi_jeda(s)
        r = r0 + i
        tg, v, rasio = pk[s]
        baris.append([i + 1, s.replace(" (m)", ""), g["L"], round(g["a"], 3), round(g["b"], 3), round(g["r"], 3),
                      f"=D{r}+E{r}*11.2", f"{v:.2f} ({tg:%d %b})".replace(".", ","), round(rasio, 2),
                      "Pasir" if s.endswith("B (m)") else "Lempung; mengikuti genangan"])
    g = at.regresi_pz1()
    r = r0 + len(baris)
    baris.append([len(baris) + 1, "PZ-1 (BH-1)", "mingguan", round(g["a"], 3), round(g["b"], 3), round(g["r"], 3),
                  f"=D{r}+E{r}*11.2", "-", "-", "Pasir 14 m; tindak lanjut no. 2 Tahap 1"])
    lb.tabel(["No", "Sensor", "Jeda L (hari)", "a (m)", "b (-)", "r", "h pada sungai +11,20 (m)",
              "Puncak Jan 2027 (m)", "Rasio kenaikan di puncak", "Keterangan"], baris, rata=list("cccccccccl"),
             fmt=[None, None, "0", "0.000", "0.000", "0.000", "0.00", None, "0.00", None],
             fill_kolom={i: AI for i in range(2, 10)})
    lb.catatan("Puncak sungai 10,83 m (15 Jan 2027). Ekstrapolasi regresi ke +11,20 berlaku untuk banjir sepanjang "
               "banjir 2027; banjir yang lebih lama memberi tinggi tekan lebih dekat ke muka sungai.", fill=AI)

    # ---- MAT desain
    lb = Lembar(wb.create_sheet("MAT Desain"), 5, "Usulan muka air dan tinggi tekan desain",
                [6, 30, 22, 16, 56])
    lb.catatan(LABEL + " USULAN untuk diputuskan Defsa; dipakai di Tahap 3 dan 6. " + LABEL_AI)
    lb.kosong()
    usul = [
        ["Muka air tanah dangkal (lempung, urugan), kondisi normal", "Muka tanah asli", "±+9,2 s.d. +10,5",
         "SP-1 0,4-1,5 m di bawah muka tanah; PZ-A di atas PZ-B. Ganti 'MAT di muka tanah' Tahap 1 secara resmi."],
        ["Muka air tanah dangkal, banjir rencana", "Muka banjir", "+11,20",
         "TOR Lampiran A (maks. tercatat Jan); lahan tergenang dan PZ-A mengikuti genangan (Jan 2027)."],
        ["Tinggi tekan akuifer pasir U5, desain operasi (uplift basement, blow-in)", "Muka banjir", "+11,20",
         "Konservatif: regresi memberi 10,25-10,80 untuk banjir sepanjang 2027; banjir lebih lama mendekati muka "
         "sungai. [Asumsi: tidak ada pengurangan]"],
        ["Tinggi tekan akuifer U5, tahap konstruksi per bulan", "Sungai bulanan", "Lihat lembar Blow-in",
         "maks(H maks bulanan; H rata-rata bulanan + 0,9) [Asumsi: PZ-1 0,8-0,9 m di atas sungai saat surut Sep 2026]."],
        ["Muka air sungai terendah (untuk tebing, kondisi surut cepat)", "Sungai", "+4,0",
         "TOR Lampiran A; dipakai di langkah 2.7 dan Tahap 6."],
    ]
    lb.tabel(["No", "Kondisi", "Acuan", "Elevasi (m)", "Dasar"], [[i + 1] + u for i, u in enumerate(usul)],
             rata=list("clccl"), fill_kolom={i: AI for i in range(1, 5)})

    # ---- Blow-in
    lb = Lembar(wb.create_sheet("Blow-in"), 6, "Pemeriksaan blow-in dasar galian (FK ≥ 1,25)",
                [6, 22, 10, 10, 10, 10, 10, 10, 10, 12])
    lb.catatan(LABEL + " FK = σv total lempung antara dasar galian dan atas pasir U5 / u di atas pasir; "
               "u = γw (h akuifer - elevasi atas pasir). SNI 8460:2017 Pasal 10.3.6.7.2 hal. 211 (FK blow-in ≥ 1,25). "
               "Galian kering (tanpa air di dalam galian), tanpa beban tambahan. " + LABEL_AI)
    lb.kosong()
    lb.bagian("A", "Berat isi sementara (kN/m³), dari langkah 2.1 dan 2.2")
    r_g = lb.baris + 1
    lb.tabel(["No", "Unit", "γ", "γw", "Sumber", "", "", "", "", ""][:5] + ["", "", "", "", ""],
             [[1, "U1 urugan", 17.0, 9.81, "[Asumsi]"] + [""] * 5,
              [2, "U2 kerak", 17.8, "", "[Uji sendiri: BH-1, BH-2 UD-1]"] + [""] * 5,
              [3, "U3 gambut", 10.7, "", "[Uji sendiri: BH-7 UD-2]"] + [""] * 5,
              [4, "U4 lempung lunak", 15.2, "", "[Uji sendiri: 21 contoh]"] + [""] * 5],
             rata=list("clccl") + ["c"] * 5, fmt=[None, None, "0.0", "0.00"] + [None] * 6, beku=False)
    for rr in range(r_g - 1, r_g + 4):
        lb.ws.merge_cells(start_row=rr, start_column=7, end_row=rr, end_column=12)
    gam = {"U1": f"$E${r_g}", "U2": f"$E${r_g + 1}", "U3": f"$E${r_g + 2}", "U4": f"$E${r_g + 3}"}
    gw = f"$F${r_g}"
    lb.kosong()
    lb.bagian("B", "FK blow-in: elevasi dasar galian (baris) dan tinggi tekan akuifer (kolom)")
    for nama, (elev0, lap) in at.PROFIL.items():
        z_pasir = elev0 - lap[-1][0]
        lb.catatan(f"{nama}: muka tanah +{elev0:.2f}, atas pasir U5 {z_pasir:+.2f}".replace(".", ","))
        r0 = lb.baris + 1
        baris = []
        for i, e in enumerate([9.0, 8.0, 7.0, 6.0, 5.0, 4.0]):
            r = r0 + i
            suku, atas = [], 0.0
            for bawah, u in lap:
                za, zb = elev0 - atas, elev0 - bawah
                suku.append(f"{gam[u]}*MAX(0,MIN({za:.2f},$E{r})-{zb:.2f})")
                atas = bawah
            sig = "+".join(suku)
            sel = [f"=IF($E{r}<={z_pasir:.2f},0,({sig})/({gw}*MAX(0.001,{h}-{z_pasir:.2f})))" for h in H_GRID]
            baris.append([i + 1, "Dasar galian", e] + sel)
        kep = ["No", "Keterangan", "Elevasi dasar (m)"] + [f"h = {h:g}".replace(".", ",") for h in H_GRID]
        lb.tabel(kep, baris, rata=list("clcccccccc"), fmt=[None, None, "0.0"] + ["0.00"] * 7,
                 fill_kolom={i: AI for i in range(3, 10)}, beku=False)
        lb.kosong()
    lb.bagian("C", "Elevasi dasar galian terendah (FK = 1,25) per bulan, tinggi tekan konstruksi")
    r0 = lb.baris + 1
    baris = []
    for i, (bln, rata, maks) in enumerate(at.SUNGAI_BULANAN):
        h = max(maks, rata + at.SELISIH_SURUT)
        nilai = []
        for p in at.PROFIL:
            e = at.elev_dasar_min(p, h)
            nilai.append("tidak bisa" if e is None else round(e, 2))
        baris.append([i + 1, bln, rata, maks, round(h, 2)] + nilai + ["", ""])
    lb.tabel(["No", "Bulan", "H rata-rata", "H maks", "h akuifer", "Tengah (BH-5)", "Utara (BH-3)",
              "Tebing (CPTu-6)", "", "Catatan"], baris, rata=list("cccccccccl"),
             fmt=[None, None, "0.00", "0.00", "0.00", "0.00", "0.00", "0.00", None, None],
             fill_kolom={i: AI for i in range(4, 8)}, beku=False)
    lb.catatan("Contoh: dasar galian basement ±+6,0 [Asumsi, ditetapkan di Tahap 3] hanya memenuhi FK 1,25 bila "
               "dasar galian minimum di tabel ≤ +6,0, yaitu Juni-Oktober di tengah tapak. 'tidak bisa' = tanpa galian "
               "pun FK < 1,25 (zona gambut, tanpa genangan).", fill=AI)

    # ---- Catatan
    lb = Lembar(wb.create_sheet("Catatan"), 7, "Catatan dan temuan langkah 2.3", [6, 120])
    lb.catatan(LABEL + " " + LABEL_AI)
    lb.kosong()
    lb.tabel(["No", "Catatan"], [[i, t] for i, t in enumerate(CATATAN, start=1)], rata=list("cl"),
             fill_kolom={1: AI})

    keluar.parent.mkdir(parents=True, exist_ok=True)
    wb.save(keluar)
    return keluar


if __name__ == "__main__":
    print(buat())
