"""Tahap 1: isi draf telaah oleh AI (atas permintaan Defsa, 19 Nov 2026) ke 'Telaah Penyelidikan Tanah.xlsx'.

Sel yang diisi AI berwarna hijau. Membuat ulang seluruh lembar (format FORMAT LAPORAN DAN EXCEL.md) beserta isinya.
Angka cek silang dihitung ulang dari data mentah di fungsi cek_silang() dan dicatat di VERIFIKASI.md.
"""
from pathlib import Path
import statistics as st

import openpyxl

from tahap1_lembar_telaah import baca_titik, buat_lembar

AKAR = Path(__file__).resolve().parents[1]
FOLDER = AKAR / "01 Penyelidikan Tanah"
BERKAS = FOLDER / "Telaah Penyelidikan Tanah.xlsx"
KG_CM2 = 98.07  # kPa per kg/cm²

SNI8460 = "SNI 8460:2017"
SNI1726 = "SNI 1726:2019"
FHWA1 = "FHWA NHI-06-088 Vol I"
GEC5 = "FHWA NHI-16-072 (GEC 5)"


def cek_silang():
    """Hitung ulang angka kunci dari data mentah."""
    s = openpyxl.load_workbook(FOLDER / "Sondir.xlsx", data_only=True)
    qc = []
    for t in ["S-01", "S-02", "S-03", "S-04", "S-05", "S-06"]:
        for r in s[t].iter_rows(min_row=7, values_only=True):
            if isinstance(r[0], (int, float)) and 2 <= r[0] <= 9.6 and r[1] < 10:
                qc.append(r[1])
    lab = openpyxl.load_workbook(FOLDER / "Laboratorium.xlsx", data_only=True)
    uu = [r[5] for r in lab["Triaksial UU"].iter_rows(min_row=5, values_only=True)
          if r[0] and str(r[0]).startswith("BH-") and r[2] >= 3]
    cc = {(r[0], r[1]): r[6] for r in lab["Ringkasan Konsolidasi"].iter_rows(min_row=5, values_only=True)
          if r[0] and str(r[0]).startswith("BH-")}
    return dict(
        qc_rata=st.mean(qc),
        cu_laporan=st.mean(qc) * KG_CM2 / 10,
        uu_rata=st.mean(uu), uu_min=min(uu), uu_max=max(uu),
        cc_laporan=st.mean([cc[("BH-1", "UD-2")], cc[("BH-1", "UD-4")], cc[("BH-2", "UD-2")], cc[("BH-3", "UD-4")]]),
        cc_tanpa_rusak=st.mean([cc[("BH-1", "UD-2")], cc[("BH-1", "UD-4")], cc[("BH-3", "UD-4")]]),
        cc_gambut=cc[("BH-3", "UD-2")],
    )


def temuan(c):
    # (kelompok, berkas, temuan, acuan, dampak, keparahan, tindak lanjut)
    return [
        ("4 Kebutuhan desain", "Ringkasan 4; Bor dan SPT > Muka Air",
         "MAT rencana 3,80 m diambil dari satu bacaan BH-2 dua jam setelah pengeboran, padahal itu bacaan terdalam dari tiga lubang "
         "(BH-1 2,60; BH-3 1,10). Pipa tegak SP-1 (Sep-Nov) terukur 0,79-1,49 m di bawah muka tanah (+8,84 s.d. +9,54) dan terus naik.",
         f"{SNI8460} Pasal 5.3.2 a-c hal. 41; Pasal 5.3.1 butir n hal. 41",
         "MAT desain hampir di muka tanah, bukan 3,8 m. Mengubah tekanan air pada dinding basement, uplift pelat, dewatering, dan tegangan efektif semua hitungan.",
         "Tinggi", "Tetapkan MAT desain dari SP-1 + muka banjir; lihat usulan pemantauan air tanah."),
        ("4 Kebutuhan desain", "Bor dan SPT > Muka Air (PZ-1)",
         "Piezometer PZ-1 di pasir (14 m) mengikuti muka sungai: +4,91 -> +7,26 saat sungai +4,1 -> +7,6. Lapisan pasir 10-19 m "
         "berhubungan dengan sungai dan tertutup lempung lunak (akuifer tertekan). Saat banjir (+11,20, TOR 4.3) tekanannya bisa melebihi muka tanah. Laporan tidak membahasnya.",
         f"{GEC5} Pasal 12.5.1 hal. 12-25 (artesis: heave/blow-out galian); {SNI8460} Pasal 5.3.2",
         "Risiko dasar galian basement terangkat atau jebol (blow-out) dan gaya angkat pada pelat basement. Menentukan metode galian dan tebal pelat basement.",
         "Tinggi", "Pemantauan piezometer di pasir sampai musim banjir; uji pompa; analisis heave di Tahap 6."),
        ("2 Dipercaya", "Bor dan SPT > Muka Air",
         "Pemantauan hanya 7 Sep - 2 Nov 2026 (kemarau ke awal hujan). Puncak banjir (Januari, TOR 4.3) belum tertangkap.",
         f"{SNI8460} Pasal 5.3.2 b-c hal. 41 (maksimum-minimum dan periode pengamatan)",
         "Batas atas tekanan air belum terukur; desain harus memakai asumsi konservatif sampai data musim banjir ada.",
         "Sedang", "Lanjutkan pembacaan mingguan SP-1, PZ-1, dan papan duga sungai minimal sampai Maret 2027."),
        ("3 Konsisten", "Laboratorium > Permeabilitas; Analisis Saringan; Ringkasan 5",
         "k pasir 1,2 x 10^-8 m/s berasal dari satu contoh SPT-12 BH-1 yang dibentuk ulang, dan deskripsinya 'lempung lanau'. Padahal saringan contoh "
         "yang sama menunjukkan SM/SP-SM (lolos no. 200 = 6,6%). Hazen dengan D10 ≈ 0,08 mm (interpolasi saringan) memberi k ≈ 3-8 x 10^-5 m/s, jadi 3-4 orde lebih besar.",
         f"{FHWA1} pers. 5-14 hal. 5-62 (Hazen, hanya perkiraan orde karena butir halus > 5%)",
         "Debit dewatering diremehkan ribuan kali. Rekomendasi 'dewatering ringan dengan sumur dangkal' tidak berdasar.",
         "Tinggi", "Uji pompa lapangan di lapisan pasir; uji permeabilitas di lubang bor."),
        ("3 Konsisten", "Sondir S-03; Log/SPT BH-2; Ringkasan 6.3",
         "S-03 berhenti di 8,4 m dengan qc melonjak dari 4 ke 180 kg/cm². BH-2 yang hanya ±11 m dari S-03 mencatat potongan kayu lapuk "
         "(batang kayu terkubur) di 8,4-8,7 m, dan di bawahnya masih lempung lunak sampai 9,5 m. Ringkasan menulis 180 kg/cm², lembar Titik menulis kapasitas alat 250 kg/cm².",
         f"{SNI8460} Pasal 5.4.1.2 hal. 42 (hasil menyimpang: uji tambahan); Pasal 5.7.3 e hal. 63 (kondisi tidak lazim)",
         "'Lapisan keras' di S-03 hampir pasti kayu, bukan lapisan tanah. Saran tiang 9 m di zona ini membuat ujung tiang berada di lempung lunak dan berbahaya.",
         "Tinggi", "Batalkan saran tiang 9 m; sondir/CPTu ulang di sekitar S-03 bergeser 2-3 m."),
        ("3 Konsisten", "Log BH-3; Lab Indeks BH-3 UD-1/UD-2; Sondir S-04, S-05; Ringkasan 3",
         "BH-3 punya lempung organik berserat 1,13-3,97 m: kadar organik 77-84%, w 290-324%, N = 0 (WOH). Ringkasan tidak menyebutnya dan menulis "
         "'relatif seragam'. Rasio gesekan (fs/qc) S-04 dan S-05 di 1,4-3,6 m sebesar 6-12,6%, padahal titik lain 2-5%. Ini mengindikasikan zona organik di bagian utara.",
         f"{SNI1726} Tabel 5 dan Pasal 5.3.1 butir 2 hal. 29-30 (gambut/organik H > 3 m -> SF); {SNI8460} Pasal 5.7.3 hal. 63-64",
         "Bila tebalnya > 3 m: kelas situs SF dan analisis respons spesifik situs. Di bawah urugan 1,5 m, lapisan ini memberi penurunan besar, rangkak (Cα 0,18), dan gesekan negatif tiang.",
         "Tinggi", "Petakan sebaran dan tebal lapisan organik (CPTu + bor tangan); uji organik dan konsolidasi tambahan."),
        ("3 Konsisten", "Ringkasan 5 (cu lempung lunak); Sondir; Lab Triaksial UU",
         f"cu = 29 kPa berasal dari qc/10 dengan rata-rata qc lempung {c['qc_rata']:.2f} kg/cm², sehingga qc/10 ≈ {c['cu_laporan']:.0f} kPa. Tegangan vertikal total tidak dikurangi "
         f"dan faktor konus diambil 10. UU pada 3-9,5 m memberi {c['uu_min']:.1f}-{c['uu_max']:.1f} kPa (rata {c['uu_rata']:.1f}). Jadi klaim 'sesuai orde UU' tidak benar: cu laporan ±2,3 kali rata-rata UU.",
         f"{SNI8460} Pasal 5.4.1.3 hal. 42-43 (syarat korelasi); {SNI8460} Pasal 5.7.3 hal. 64",
         "cu terlalu besar 2-3 kali. Akibatnya stabilitas dasar galian, gaya lateral pada tiang, dan daya dukung jadi tidak aman.",
         "Tinggi", "Pakai cu dari UU/CPTu dengan faktor konus terkalibrasi; tetapkan di Tahap 2."),
        ("3 Konsisten", "Lab Ringkasan Konsolidasi; Ringkasan 5 (Cc)",
         f"Cc 0,61 = rata-rata empat contoh ({c['cc_laporan']:.3f}). Gambut BH-3 UD-2 (Cc {c['cc_gambut']:.2f}) dan kerak BH-2 UD-1 dibuang tanpa penjelasan, "
         f"sedangkan BH-2 UD-2 yang rusak (Cc 0,355) tetap ikut dihitung. Tanpa contoh rusak, Cc = {c['cc_tanpa_rusak']:.2f}.",
         f"{SNI8460} Pasal 5.7.3 hal. 63-64 (pembahasan nilai turunan, zona lemah)",
         "Penurunan konsolidasi lempung lunak diremehkan ±12%, dan penurunan gambut tidak dihitung sama sekali.",
         "Sedang", "Parameter per lapisan (lempung lunak, organik/gambut) ditetapkan ulang di Tahap 2."),
        ("2 Dipercaya", "Log BH-2 (UD-2); Lab Konsolidasi dan UU BH-2 UD-2",
         "BH-2 UD-2 punya perolehan 64% dan tabung retak (catatan juru bor). σ'p Casagrande 19 kPa lebih kecil daripada σ'v0 perkiraan ±34 kPa (tanda gangguan), "
         "dan cu-nya 5,7 kPa, terendah dari semua contoh. Contoh ini tetap dipakai di Cc dan cu.",
         f"{SNI8460} Pasal 5.3.4.1 hal. 37, Tabel 3 hal. 30 (kompresibilitas/kuat geser hanya dari kelas 1)",
         "Data dari contoh terganggu ikut mencemari parameter desain.",
         "Sedang", "Keluarkan BH-2 UD-2 dari parameter desain; ganti dengan contoh baru."),
        ("2 Dipercaya", "Log BH-1, BH-2, BH-3 (perolehan UD)",
         "Perolehan contoh UD tercatat tepat 92% pada 14 dari 15 tabung. Keseragaman seperti ini tidak wajar untuk lempung sangat lunak dan gambut.",
         f"{SNI8460} Pasal 5.7.2 hal. 62-63 (laporan faktual)",
         "Keandalan catatan lapangan diragukan.",
         "Rendah", "Minta log lapangan asli dan foto tabung."),
        ("3 Konsisten", "Lab Indeks BH-3 (berat isi)",
         "Berat isi BH-3: CH 8,26-9,03 kN/m³ (titik lain 15,2-15,4 untuk w serupa); gambut 2,54-2,78 kN/m³. Untuk contoh jenuh, angka ini lebih kecil "
         "daripada berat isi air (9,81). Itu mustahil. Hitungan balik CH (Gs 2,63, w 75%, S = 1) memberi ±15,2 kN/m³.",
         "Hubungan fase: γ = Gs(1+w)γw/(1+wGs) untuk S = 1",
         "Tegangan efektif BH-3 dan berat urugan/galian salah bila angka ini dipakai.",
         "Sedang", "Konfirmasi ke laboratorium (kemungkinan salah satuan atau salah ketik)."),
        ("2 Dipercaya", "Lab Konsolidasi BH-3 UD-2",
         "Pada gambut BH-3 UD-2, angka pori turun dari 4,44 ke 0,16 di 800 kPa. e = 0,16 tidak wajar untuk gambut berserat (setara tanah yang sangat padat).",
         f"{SNI8460} Pasal 5.7.3 hal. 63 (review hasil uji)",
         "Kurva e-log σ' gambut tidak bisa dipercaya untuk hitungan penurunan.",
         "Sedang", "Ulang uji konsolidasi gambut dengan contoh baru."),
        ("2 Dipercaya", "SPT BH-1, BH-2, BH-3 (catatan atas)",
         "SPT memakai palu donat dengan tali-cathead, dan efisiensi energinya tidak diukur. Untuk sistem ini rasio energi berkisar 35-85%, sehingga N tidak bisa dikonversi ke N60 dengan pasti.",
         f"{FHWA1} hal. 3-55, pers. 3-2; {SNI8460} Pasal 5.4.2 hal. 43 (SNI 4153-2008; dokumen SNI 4153 belum ada di acuan/)",
         "Kelas situs (N rata-rata 30 m) dan evaluasi likuifaksi (N1,60) menjadi tidak pasti.",
         "Sedang", "Ukur energi palu (ASTM D4633) atau pakai palu otomatis di bor tambahan."),
        ("2 Dipercaya", "SPT BH-2 12-18 m",
         "Di BH-2 12-18 m pasir naik ±0,5 m ke dalam casing dan air bor hilang (muka air di lubang di bawah MAT). N = 4-7, sedangkan BH-1 dan BH-3 di kedalaman sama 10-20. "
         "Ringkasan memasukkan nilai ini ke rentang '3-20'.",
         f"{FHWA1} Tabel 3-10 hal. 3-61 (tinggi air di lubang tidak dijaga: dasar lubang 'quick', N turun); {SNI8460} Pasal 5.4.2",
         "N rendah palsu bisa membuat zona pasir tampak lebih lepas atau lebih mudah likuifaksi daripada sebenarnya, atau menutupi zona lepas sungguhan.",
         "Sedang", "Abaikan N BH-2 12-18 m; ulang dengan CPTu di dekat BH-2."),
        ("4 Kebutuhan desain", "Ringkasan (seluruhnya)",
         "Kelas situs tidak ditetapkan. Data hanya N-SPT sampai 30 m (satu parameter), su lab hanya sampai 9,5 m, dan tidak ada vs. Lempung lunak 2-10 m "
         "(PI 35-56, w 64-80%, su 6-19 kPa, tebal > 3 m) sudah memenuhi kriteria SE. Gambut dan likuifaksi bisa membuatnya SF.",
         f"{SNI1726} Pasal 5.1 hal. 29 (dua dari tiga parameter); Tabel 5 hal. 29-30",
         "Spektrum desain gempa belum bisa ditetapkan; minimal SE, kemungkinan SF.",
         "Tinggi", "Ukur vs (MASW/downhole) dan lengkapi su; klasifikasi di Tahap 2."),
        ("4 Kebutuhan desain", "Log dan SPT pasir 10-19 m; Saringan",
         "Potensi likuifaksi tidak dievaluasi. Pasir halus lepas sampai agak padat, jenuh, butir halus 5-9%, N 8-20 (belum dikoreksi), dan MAT dangkal. "
         "Laporan justru menempatkan ujung tiang di lapisan ini.",
         f"{SNI1726} Pasal 6.7.2 b dan 6.7.3 butir 2 hal. 38-39",
         "Bila terjadi likuifaksi: daya dukung ujung tiang hilang, ada gesekan negatif pascagempa, dan kelas situs SF.",
         "Tinggi", "Gradasi tiap 1,5 m dan CPTu di pasir; evaluasi likuifaksi di Tahap 2."),
        ("4 Kebutuhan desain", "Ringkasan 5-6; Log 19-33 m",
         "Tiang disarankan berujung di 16-18 m, hanya 1-3 m di atas dasar pasir. Di bawahnya ada lempung kaku 19-33 m (±14 m) tanpa contoh UD dan tanpa uji kompresibilitas. "
         "cu 90 kPa untuk lapisan ini tidak punya dasar uji (hanya indeks dari SPT-24).",
         f"{SNI8460} Pasal 5.7.3 d hal. 63 (sifat deformasi dan kekuatan tiap lapisan dari penyelidikan)",
         "Penurunan kelompok tiang dan risiko tiang menembus pasir tipis (punching) tidak bisa dihitung. Alternatif tiang ke pasir padat > 33 m belum dibahas.",
         "Sedang", "Contoh UD (tabung tebal/Pitcher) di lempung kaku: UU + konsolidasi."),
        ("4 Kebutuhan desain", "Ringkasan 6; TOR 5 butir 4",
         "Urugan ±1,5 m (TOR) di atas lempung lunak dan gambut akan menimbulkan konsolidasi dan gesekan negatif pada tiang. Laporan tidak membahasnya.",
         f"{SNI8460} Pasal 5.7.1 hal. 62 (evaluasi geoteknik untuk struktur yang direncanakan)",
         "Kapasitas tiang berkurang dan halaman/utilitas di luar gedung turun.",
         "Sedang", "Hitung di Tahap 6 setelah parameter lapisan lunak dan organik ditetapkan."),
        ("1 Cukup", "Denah titik; TOR 4.1 dan 5 butir 3",
         "Tidak ada titik di tebing atau di luar batas selatan. Titik terdekat ke sungai ada di y = 10-15 m. Owner ingin gedung sedekat mungkin ke sungai, ditambah dermaga ambulans air.",
         f"{SNI8460} Pasal 5.2.4.1.3 d hal. 23; Tabel 2 (stabilitas lereng: 3-5 titik per potongan kritis) hal. 26",
         "Stabilitas tebing (termasuk saat air surut cepat) dan pondasi dermaga tidak bisa dievaluasi; garis aman bangunan dari tebing belum bisa ditetapkan.",
         "Tinggi", "Survei penampang tebing + batimetri; bor di kepala dan kaki tebing pada 2-3 potongan."),
        ("1 Cukup", "Denah titik; TOR 4.1 (gudang timur)",
         "Gudang lama berpondasi cerucuk kayu berdiri ±4 m dari batas timur. Titik terdekat (S-06) berjarak ±15 m, dan tidak ada catatan kondisi bangunan sekitar.",
         f"{SNI8460} Pasal 5.2.4.1.3 f hal. 23; Pasal 5.7.2 e hal. 62 (perilaku struktur bangunan sekitar)",
         "Galian dan dewatering bisa menurunkan MAT dan menggerakkan tanah di bawah gudang. Cerucuk kayu yang terekspos udara bisa membusuk. Ini risiko klaim pihak ketiga.",
         "Tinggi", "Survei kondisi pra-konstruksi gudang; titik penyelidikan di sisi timur; patok penurunan."),
        ("1 Cukup", "Lembar Cek Kecukupan; Titik",
         "Hanya 3 bor (perlu ±10 untuk tapak ±3.900 m², asumsi). Sondir mekanis berhenti di 20 m karena batas panjang stang, sehingga tidak ada yang menembus lempung kaku. "
         "Kedalaman perlu menurut Gambar 1 jauh di atas 40 m (lihat Cek Kecukupan).",
         f"{SNI8460} Tabel 2 hal. 25; Gambar 1 hal. 27; Pasal 5.2.4.1.3 hal. 22-23",
         "Variasi lateral (gambut, kayu terkubur) tidak terpetakan; lapisan pendukung di bawah 40 m belum diketahui.",
         "Sedang", "Bor dan CPTu tambahan dalam grid ≤ 30 m setelah denah konsep; satu bor diperdalam."),
        ("4 Kebutuhan desain", "Laboratorium (tidak ada uji kimia)",
         "Tidak ada uji pH, sulfat, atau klorida tanah dan air tanah, padahal ada lempung organik dan gambut (umumnya asam) dan beton serta turap baja akan berada di bawah air.",
         f"{SNI8460} Pasal 5.2.3 d hal. 21 (kontaminasi yang merusak daya tahan bahan); {GEC5} hal. 5-50 (sulfat merusak pasta semen)",
         "Kelas paparan beton, selimut, dan korosi turap/tiang belum bisa ditetapkan.",
         "Sedang", "Uji kimia tanah dan air tanah di zona organik dan di pasir."),
        ("2 Dipercaya", "Lab Geser Langsung",
         "Geser langsung pasir memakai contoh SPT yang dibentuk ulang pada 'kepadatan perkiraan'. φ 27,6-29,1° bergantung pada kepadatan yang ditebak.",
         f"{SNI8460} Pasal 5.3.4.1 hal. 37, Tabel 3 hal. 30",
         "φ pasir lebih baik diturunkan dari CPTu/SPT terkoreksi; angka lab hanya pembanding.",
         "Rendah", "Turunkan φ dari CPTu di Tahap 2."),
        ("2 Dipercaya", "Bor dan SPT > Muka Air (catatan pemasangan)",
         "PZ-1 dan SP-1 dipasang di lubang yang sama (BH-1). Pembacaan pertama PZ-1 tanggal 7 Sep, padahal BH-1 baru selesai dibor sampai 40 m tanggal 9 Sep.",
         f"{SNI8460} Pasal 5.3.1 butir o hal. 41 (keterhubungan akuifer, segel)",
         "Segel antara saringan SP-1 (1,5-3 m) dan PZ-1 (14 m) diragukan. Bisa jadi PZ-1 tidak murni membaca tekanan pasir.",
         "Sedang", "Minta catatan pemasangan; pasang piezometer baru di lubang terpisah."),
        ("1 Cukup", "Ringkasan (struktur laporan)",
         "Laporan tidak memuat kategori geoteknik, kelas situs, keterbatasan tiap uji, dan usulan penyelidikan lanjutan.",
         f"{SNI8460} Pasal 5.7.1 dan 5.7.2 b hal. 62",
         "Laporan belum memenuhi isi minimum laporan penyelidikan tanah.",
         "Rendah", "Diminta ke PT Tapak Rawa Geoteknik sebagai revisi laporan."),
        ("4 Kebutuhan desain", "Ringkasan 6 butir 4",
         "Rekomendasi turap baja + dewatering ringan disusun dari MAT 3,8 m, k 10^-8 m/s, dan cu 29 kPa. Ketiganya keliru (temuan 1, 4, 7) dan tekanan artesis tidak dipertimbangkan (temuan 2).",
         f"{SNI8460} Pasal 5.7.1 hal. 62; {GEC5} Pasal 12.5.1 hal. 12-25",
         "Metode galian basement harus dikaji ulang (dinding kaku, pelat dasar/jet grout, recharge untuk gudang). Ini juga mendukung tanggapan Tahap 0 soal basement di bawah banjir.",
         "Tinggi", "Kaji alternatif galian di Tahap 3 dan 6."),
    ]


def usulan():
    # (jenis uji, lokasi, kedalaman, jumlah, alasan, acuan, prioritas, catatan)
    return [
        ("Bor mesin + SPT (energi palu diukur, tinggi air di lubang dijaga) + UD tabung piston", "Grid ≤ 30 m di tapak gedung setelah denah konsep; 1 di sisi timur dekat gudang",
         "40", "5", "Temuan 13, 14, 21, 20", f"{SNI8460} Tabel 2, Gambar 1; FHWA Tabel 3-10", "Wajib sebelum desain", "Satu dari lima diperdalam (lihat baris 2)."),
        ("Perdalam satu bor", "Tengah tapak gedung", "≥ 60", "1", "Temuan 17, 21: kepastian pasir padat > 33 m menerus, untuk alternatif tiang panjang",
         f"{SNI8460} Gambar 1(d)", "Wajib sebelum desain", "Kedalaman akhir diputuskan bersama konsep pondasi Tahap 3."),
        ("CPTu (sondir elektrik dengan pori) + uji disipasi", "Sekitar S-03 (geser 2-3 m), dekat BH-2, zona utara (S-04, S-05, BH-3), dan sisi tebing",
         "30 atau menolak", "8", "Temuan 5, 6, 7, 14, 16: profil menerus, su, likuifaksi", f"{SNI8460} Pasal 5.4.3 (SNI 2827-2008)", "Wajib sebelum desain", "Disipasi di pasir dan lempung untuk ch dan tekanan pori."),
        ("Pemetaan lapisan organik/gambut (bor tangan + uji organik, w, γ)", "Grid 15-20 m di bagian utara lahan", "5", "10", "Temuan 6, 11",
         f"{SNI1726} Tabel 5 (H > 3 m)", "Wajib sebelum desain", "Murah dan cepat."),
        ("Pengukuran vs (MASW dan/atau downhole)", "Dua lintasan/lokasi di tapak gedung", "≥ 30", "2", "Temuan 15", f"{SNI1726} Pasal 5.1",
         "Wajib sebelum desain", "Downhole bisa di lubang bor tambahan."),
        ("Lab tambahan: konsolidasi (termasuk Cα), UU, CU dengan tekanan pori pada lempung lunak dan gambut; UU + konsolidasi pada lempung kaku; saringan pasir tiap 1,5 m",
         "Dari bor tambahan", "-", "± 30 contoh", "Temuan 7, 8, 9, 12, 16, 17", f"{SNI8460} Pasal 5.3.4.1, Tabel 3", "Wajib sebelum desain", "Contoh BH-2 UD-2 dan gambut BH-3 diganti."),
        ("Uji pompa di pasir 10-19 m + 2 sumur pantau", "Tengah area basement", "20", "1 sumur uji", "Temuan 2, 4, 26: k lapangan, hubungan dengan sungai",
         f"{GEC5} Pasal 12.5.1", "Wajib sebelum desain", "Hasilnya dasar desain dewatering/cutoff."),
        ("Piezometer (vibrating wire) terpisah di pasir dan lempung + papan duga sungai", "3 lokasi: dekat sungai, tengah, utara", "5 dan 14", "6", "Temuan 1, 2, 3, 24",
         f"{SNI8460} Pasal 5.3.1-5.3.2", "Wajib sebelum desain", "Baca mingguan minimal sampai Maret 2027 (lewat puncak banjir Januari)."),
        ("Uji kimia tanah dan air tanah (pH, sulfat, klorida, organik)", "Zona organik + akuifer pasir", "-", "6", "Temuan 22", f"{SNI8460} Pasal 5.2.3 d", "Sebelum DED", ""),
        ("Survei topografi penampang tebing + batimetri; bor di kepala dan kaki tebing", "2-3 potongan kritis di sisi selatan", "30", "4-6 bor", "Temuan 19",
         f"{SNI8460} Pasal 5.2.4.1.3 d; Tabel 2 (lereng)", "Wajib sebelum desain", "Perlu izin; sebagian di luar batas lahan."),
        ("Survei kondisi pra-konstruksi gudang tetangga + patok penurunan", "Gudang sisi timur", "-", "1 paket", "Temuan 20, 26",
         f"{SNI8460} Pasal 5.7.2 e", "Sebelum DED", "Dokumentasi retak dan foto; perlu persetujuan pemilik."),
        ("Uji beban tiang uji (statik/PDA) sebelum pemancangan massal", "Tiang uji di 2 zona (utara organik, selatan)", "-", "2-3", "Temuan 17 dan rekomendasi laporan butir 5",
         f"{SNI8460} (uji beban tiang)", "Saat konstruksi", "Masuk RKS Tahap 7."),
    ]


def main():
    c = cek_silang()
    cek = {1: 3900, 2: 400, 4: 3, 5: 6, 6: 3, 7: 14, 8: 60, 13: 40, 14: 3, 16: "Kurang"}
    cek_ket = {
        1: "[Asumsi: ±60 × 65 m; basement parkir 120 mobil + utilitas ≈ 3.600-4.000 m²]",
        2: "Tabel 2, gedung 4-7 lantai (grid 15-40 m). Basement < 6 m: 1 titik per 15-40 m keliling (±250 m → 7-17 titik)",
        4: "BH-1 s.d. BH-3", 5: "S-01 s.d. S-06; mekanis, maksimum 20 m; S-03 berhenti di 8,4 m",
        6: "[Asumsi: muka tanah asli ±+9,7; dasar raft ±+6,7]",
        7: "[Asumsi: ujung tiang 16-18 m dari muka tanah, saran laporan]",
        8: "[Asumsi: lebar terpendek tapak ±60 m]",
        14: "[Asumsi: dari muka tanah asli ±+9,7 ke dasar galian ±+6,7]",
        16: "Bor 3 < 10 titik; kedalaman Gambar 1(d) ≈ 102 m > 40 m. Kriteria Gambar 1 untuk tapak selebar 60 m sangat "
            "dalam; praktisnya satu bor diperdalam ≥ 60 m untuk memastikan lapisan padat menerus (keputusan akhir di "
            "Tahap 3). Galian (f) 5 m: tercakup.",
    }
    inventaris = {"S-03": "Berhenti 8,4 m: kemungkinan kayu terkubur (lihat BH-2 8,4-8,7 m)",
                  "BH-2": "SPT 12-18 m terganggu (pasir naik, air hilang); UD-2 retak",
                  "BH-3": "Lempung organik/gambut 1,13-3,97 m; berat isi lab tidak wajar",
                  "S-04": "Rasio gesekan 6-10% pada 1,4-3,6 m (indikasi organik)",
                  "S-05": "Rasio gesekan 6-12,6% pada 1,4-3,6 m (indikasi organik)"}
    buat_lembar(baca_titik(), ai=dict(temuan=temuan(c), usulan=usulan(), cek=cek, cek_ket=cek_ket,
                                      inventaris=inventaris), keluar=BERKAS)
    print({k: round(v, 3) for k, v in c.items()})
    print(len(temuan(c)), "temuan,", len(usulan()), "usulan")


if __name__ == "__main__":
    main()
