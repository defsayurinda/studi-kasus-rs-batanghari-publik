"""Tahap 2 langkah 2.1: lembar kerja koreksi data (tugas A: energi palu SPT).

Membuat '02 Olah Data Tanah/2.1 Koreksi Data.xlsx' berformat FORMAT LAPORAN DAN EXCEL.md.
Data ukur disalin dari berkas penyelidikan tambahan; sel hijau diisi AI atas permintaan Defsa.
Jalankan:  .venv\\Scripts\\python.exe skrip\\tahap2_koreksi_data.py
"""
from pathlib import Path

import openpyxl

import tahap2_mutu_contoh as mc
from format_dokumen import AI, Lembar, set_font_bawaan

AKAR = Path(__file__).resolve().parents[1]
SUMBER = AKAR / "01 Penyelidikan Tanah" / "Penyelidikan Tambahan" / "Bor Tambahan dan SPT.xlsx"
BERKAS = AKAR / "02 Olah Data Tanah" / "2.1 Koreksi Data.xlsx"
LABEL = "DATA SIMULASI untuk studi kasus portofolio. Bukan data proyek nyata. Tidak untuk konstruksi."
RIG = {"BH-4": "A", "BH-5": "A", "BH-6": "A", "BH-7": "B", "BH-8": "B"}
SUMBER_CPTU = AKAR / "01 Penyelidikan Tanah" / "Penyelidikan Tambahan" / "CPTu.xlsx"
A_KONUS = 0.80  # rasio luas bersih, lembar Titik CPTu.xlsx
SUMBER_LAMA = AKAR / "01 Penyelidikan Tanah" / "Bor dan SPT.xlsx"
RIG_SEMUA = {**RIG, "BH-1": "Lama", "BH-2": "Lama", "BH-3": "Lama"}

LABEL_AI = ("DIISI AI ATAS PERMINTAAN DEFSA (19 Nov 2026), sel hijau; disetujui Defsa 19 Nov 2026. "
            "Kunci jawaban tidak dibuka.")

CATATAN_UKUR = {
    ("BH-8", 1.5): "ER dipakai. N = 10 tidak mewakili tanah: pukulan pertama mengenai pecahan beton di urugan "
                   "(catatan SPT BH-8); tandai di tugas B.",
    ("BH-6", 13.5): "Lumpur ditambah, tidak ada pasir naik ke casing (catatan SPT BH-6): N layak.",
}

CATATAN_STAT = {
    "BH-6": "Lebih rendah sistematis dari BH-4 dan BH-5: kelima nilai 80-82 %. Uji t Welch BH-6 terhadap "
            "BH-4+BH-5: p = 0,0003 (beda nyata).",
    "BH-7": "Tidak berbeda nyata dengan BH-8 (uji t Welch, p = 0,27).",
    "BH-8": "Lihat BH-7.",
    "A": "Tidak dipakai langsung karena BH-6 berbeda nyata; ER rig A ditetapkan per bor.",
    "B": "Dipakai untuk BH-7 dan BH-8 (digabung).",
}

ALASAN_C = [
    "ER tidak berubah menurut kedalaman (regresi rig A: -0,02 %/m, p = 0,88), jadi satu nilai per bor. "
    "Rata-rata 5 ukuran per bor.",
    "Sama dengan BH-4.",
    "Per bor, karena ER BH-6 lebih rendah nyata (selisih ±4 %, mengubah N60 ±5 %). Penyebab tidak dicatat "
    "(BH-6 bor terakhir rig A, 5-8 Des 2026); tanyakan ke penyedia apakah palu atau rig diservis.",
    "BH-7 dan BH-8 tidak berbeda nyata, jadi digabung (10 ukuran). Regresi terhadap kedalaman: +0,01 %/m, p = 0,91.",
    "Jenis palu sama dengan rig B. Lebih rendah dari nilai bawaan AASHTO 60 %, jadi N60 lebih kecil "
    "(konservatif untuk daya dukung, likuifaksi, dan kelas situs). Rig dan operator lama berbeda (PT TRG), "
    "sehingga ketidakpastiannya besar: rentang praktik palu donat 35-85 % (FHWA hal. 3-55).",
    "Dipakai untuk menunjukkan pengaruh asumsi pada N60 bor lama (selisih 13 %) di langkah 2.5 dan 2.6.",
]

CATATAN_D = [
    "N lapangan di lembar Energi Palu cocok dengan lembar SPT tiap bor (25 dari 25).",
    "Tidak ada pengukuran yang dibuang. Semua ER berada dalam rentang jenis palunya (FHWA NHI-06-088 hal. 3-55: "
    "palu otomatis 80-100 %, palu donat 35-85 %).",
    "ER diukur pada batang, jadi pengaruh panjang batang terhadap energi sudah termasuk dalam ER terukur. ER pada "
    "1,5 m (BH-4: 86 %, BH-8: 53 %) tidak lebih rendah daripada di kedalaman lain. Koreksi lain (panjang batang, "
    "diameter lubang, tabung tanpa lapisan) belum diterapkan; dibahas di langkah 2.6 bersama sumbernya.",
    "Muka cairan di lubang 0,21-0,70 m dari muka tanah, di atas MAT terukur 0,8-1,5 m (Tahap 1, SP-1). "
    "Syarat pengeboran di lembar Titik terpenuhi, sehingga risiko pasir naik ke lubang (N terlalu rendah) kecil.",
    "Pengaruh koreksi pada pasir 10,5-19,5 m (7 uji per bor): N lapangan rata-rata rig A 10,9-11,7 dan rig B "
    "15,6-17,7 (rig B ±47 % lebih tinggi). Setelah koreksi N60 rig A 15,6-16,0 dan rig B 13,8-15,6 (rata-rata selisih ±7 %). "
    "Koreksi menyatukan kedua rig, jadi ER terukur masuk akal. Rincian di VERIFIKASI.md T-08.",
    "Ketidakcocokan administrasi: ringkasan laporan menyebut BH-7 dikerjakan rig B karena rig A masih di BH-5, "
    "padahal BH-7 dibor 24-28 Nov 2026 saat rig A di BH-4 (23-26 Nov). Tidak memengaruhi ER, cukup dicatat.",
]

RINGKAS_CAT = {
    "BH-1": "ER 53 % [Asumsi]. Dekat BH-4 (±16 m): N60 pasir lebih rendah ±25 %.",
    "BH-2": "4 uji pasir 12-18 m tidak dipakai (pasir naik ke casing); hanya uji 10 m yang tersisa.",
    "BH-3": "ER 53 % [Asumsi]. Dekat BH-7 (±9 m): N60 pasir lebih rendah ±17 %.",
    "BH-5": "Penolakan 37,5-54 m, lalu N 35-46 di 55,5-60 m: lapisan berganti (dibahas di 2.2).",
    "BH-8": "Uji 1,5 m tidak dipakai (pecahan beton).",
}

CATATAN_B = [
    "Uji WOH dihitung N = 0. Uji penolakan (50 pukulan sebelum 30 cm) dihitung N = 50, sehingga N60-nya batas bawah. "
    "Penolakan mulai 34-37,5 m di semua bor (lapisan pasir padat dalam).",
    "Lima uji tidak dipakai: BH-2 12, 14, 16, 18 m (pasir naik ke casing, muka air lubang di bawah MAT; FHWA "
    "NHI-06-088 Tabel 3-10 hal. 3-61) dan BH-8 1,5 m (pecahan beton). Nilainya tetap ditampilkan agar bisa ditelusuri.",
    "N60 rata-rata pasir 10-20 m bor baru 13,8-16,0 dan cukup seragam. Bor lama dengan ER 53 % [Asumsi]: BH-1 11,7, "
    "BH-3 12,9. Bila ER lama 60 % (bawaan AASHTO), nilainya 13,2 dan 14,6. Selisih dengan bor baru terdekat "
    "(BH-1 terhadap BH-4 -25 %, BH-3 terhadap BH-7 -17 %) memberi petunjuk bahwa ER bor lama mungkin lebih dari 53 %. "
    "53 % tetap dipakai karena hasilnya lebih rendah (konservatif); pengaruhnya diuji di langkah 2.5 dan 2.6.",
    "Batas 10-20 m hanya perkiraan letak lapisan pasir untuk perbandingan. Batas lapisan per bor ditetapkan di "
    "langkah 2.2 dari log bor dan CPTu.",
    "Koreksi tambahan (panjang batang, diameter lubang, tabung, dan normalisasi tegangan N1,60) belum diterapkan; "
    "dipakai di langkah 2.6 (likuifaksi) bersama sumbernya.",
]

CATATAN_CPTU_RINGKAS = {
    "CPTu-1": "2 m dari S-03. qc melonjak 4,4-4,7 MPa di 8,25-8,35 m (lapisan tipis keras): cocok dengan kayu "
              "terkubur BH-2, bukan lapisan pendukung.",
    "CPTu-4": "Data 0-1 m di lubang awal tidak dipakai. u2 sampai 4,5 m tidak andal (filter tak jenuh); koreksi 2-9 m lebih kecil.",
    "CPTu-8": "Diperpanjang sampai gaya dorong maksimum; qc sampai 30 MPa di dasar (pasir padat).",
}

CATATAN_C = [
    "Koreksi qt penting di lempung lunak 2-9 m: qt ±11-12 % lebih besar dari qc (maks ±14 %), karena qc kecil "
    "(0,15-0,35 MPa) sedangkan u2 besar. Di pasir 12-18 m koreksinya ±1 % (u2 kecil terhadap qc besar). Di lempung "
    "20-30 m ±7 %. Jadi parameter lempung (su, OCR) wajib memakai qt, bukan qc.",
    "CPTu-4: u2 negatif sampai 2,15 m dan naik lambat, baru setara CPTu lain di ±4,5 m. Penyebabnya filter tidak "
    "jenuh lagi setelah melewati lubang awal 1 m di lapisan kering (catatan laporan no. 4). Akibatnya qt 2-4,5 m "
    "terlalu kecil ±7 % dibanding bila memakai u2 rata-rata CPTu lain. Data u2 dan qt CPTu-4 0-4,5 m tidak "
    "dipakai untuk parameter; qc dan fs tetap bisa dipakai untuk stratigrafi.",
    "CPTu-4 mencatat qc, fs, dan u2 sejak 0,1 m, padahal 0-1,0 m adalah lubang awal bor tangan (catatan laporan "
    "no. 4). Data 0-1,0 m itu bukan tahanan tanah asli (konus bergerak di lubang yang sudah dibuka atau tanah runtuhan), "
    "jadi tidak dipakai. Kedalamannya kemungkinan sudah dari muka tanah: batas lapisan CPTu-4 (lempung lunak mulai "
    "1,35 m, pasir mulai 10,1 m) setara CPTu lain (1,15-1,95 m dan 8,3-10,1 m). Tetap tanyakan ke penyedia.",
    "u2 negatif kecil (sampai -4 kPa) di 0,1-0,45 m pada semua CPTu: di atas muka air, tanah tak jenuh (isapan). "
    "Pengaruhnya ke qt < 1 kPa, jadi dipakai apa adanya.",
    "Kemiringan maksimum 3,6-4,2°. Pengaruhnya ke kedalaman sebenarnya kecil: cos 4,2° = 0,997, atau ±0,09 m di "
    "34 m. Koreksi kedalaman tidak diterapkan.",
    "CPTu-1 (2 m dari S-03) mencatat qc 4,4-4,7 MPa hanya setebal ±0,15 m di 8,25-8,35 m, lalu kembali ±0,3 MPa. "
    "Ini menguatkan temuan Tahap 1: 'lapisan keras' S-03 di 8,4 m adalah kayu terkubur, bukan lapisan pendukung tiang.",
    "Di pasir 12-18 m, u2 rata-rata 127-192 kPa, mendekati tekanan hidrostatik bila MAT ±1 m (±137 kPa di 15 m). "
    "Ini bahan cek silang MAT di langkah 2.3.",
    "Bq, Qt, Fr, dan klasifikasi tanah (SBT) memerlukan σv0 dan u0 (berat isi dan MAT). Semuanya dihitung di "
    "langkah 2.2-2.4 setelah MAT desain ditetapkan.",
]

CATATAN_MUTU = {
    ("BH-2", "UD-1"): "Kerak teguh, OCR ±10: di luar tabel Lunne. εv 1,6 % (B): mutu baik.",
    ("BH-2", "UD-2"): "Tidak dipakai. Perolehan 64 %, tabung retak (temuan Tahap 1 no. 9); σ'p < σ'v0.",
    ("BH-3", "UD-2"): "Gambut: kriteria Lunne disusun untuk lempung, tidak berlaku. e = 0,16 di 800 kPa tidak wajar "
                      "(temuan Tahap 1 no. 12).",
    ("BH-5", "UD-1"): "σ'p lab 100 kPa tidak cocok dengan kurva: e sudah turun 0,117 di 25-50 kPa, jadi σ'p ±30-50 "
                      "kPa. Dengan OCR ±2, Δe/e0 0,035 = sangat baik. σ'p ditetapkan ulang di 2.4.",
    ("BH-6", "UD-1"): "Peka MAT: dengan MAT 1 m menjadi baik-cukup.",
    ("BH-7", "UD-2"): "Gambut: kriteria Lunne tidak berlaku; dipakai hanya sebagai petunjuk.",
    ("BH-7", "UD-3"): "Buruk (perolehan 87 %). Cc dan σ'p (32 kPa) hanya batas bawah; jangan dirata-ratakan.",
    ("BH-4", "UD-4"): "Pitcher, lempung kaku: sangat baik.",
    ("BH-5", "UD-5"): "Pitcher, lempung kaku: sangat baik.",
}

CATATAN_D_MUTU = [
    "Hasil Lunne (MAT di muka tanah): lempung lunak 2-9 m umumnya baik-cukup (Δe/e0 0,035-0,052), satu sangat "
    "baik (BH-6 UD-1). Dua contoh buruk: BH-2 UD-2 (0,139, sudah ditolak di Tahap 1) dan BH-7 UD-3 (0,093). "
    "Lempung kaku 21-24 m (tabung Pitcher) sangat baik (0,016-0,029).",
    "Kriteria εv (SQD) lebih ketat: semua lempung lunak mendapat C (εv 2,4-3,6 %), padahal GEC 5 hal. 6-6 meminta "
    "minimal B (εv < 2 %) untuk lempung lunak. Perbedaannya karena εv = Δe/(1 + e0); dengan e0 ±2, εv ±2/3 Δe/e0. "
    "Δe/e0 memperhitungkan angka pori awal yang besar, jadi Lunne dipakai sebagai kriteria utama. SQD C tetap dicatat: "
    "nilai Cc dan σ'p contoh lunak lebih tepat dianggap sedikit di bawah nilai sebenarnya.",
    "Kepekaan terhadap MAT: bila MAT 1 m, σ'v0 naik ±10 kPa dan Δe/e0 naik ±0,01-0,03. Peringkat hanya berubah di BH-6 "
    "UD-1 (sangat baik menjadi baik-cukup) dan BH-2 UD-2 (buruk menjadi sangat buruk). Kesimpulan tetap.",
    "OCR di sini memakai σ'p lab dan hanya untuk memilih kolom tabel Lunne. σ'p BH-5 UD-1 (100 kPa) tidak sesuai "
    "dengan kurvanya dan perlu ditetapkan ulang. σ'p, Cc, Cr, dan cv desain ditetapkan di langkah 2.4 dari contoh "
    "yang lolos (bukan BH-2 UD-2 dan BH-7 UD-3).",
    "Gambut (BH-3 UD-2, BH-7 UD-2): kriteria Lunne dan SQD disusun untuk lempung; nilainya hanya petunjuk. Pemampatan "
    "gambut (Cc, Cα besar) dibahas tersendiri di 2.4.",
    "Contoh yang tidak diuji konsolidasi (indeks dan UU saja) belum dinilai. Mutu contoh UU dinilai di 2.4 lewat "
    "pembandingan cu UU dengan su CPTu (qt dari tugas C).",
]

PETUNJUK = [
    "Langkah 2.1 menyetarakan data mentah sebelum diolah: energi SPT (tugas A-B), qt CPTu (tugas C), "
    "mutu contoh tak terganggu (tugas D). Lembar ini memuat tugas A dan B; lembar lain ditambah saat tugasnya dimulai.",
    "N60 = (ER/60) x N lapangan. Sumber: FHWA NHI-06-088 Vol. I, Pers. 3-2, hal. 3-55.",
    "Sel putih = data ukur disalin dari 'Bor Tambahan dan SPT.xlsx' lembar Energi Palu (jangan diubah). "
    "Sel hijau = diisi AI atas permintaan Defsa, disetujui Defsa 19 Nov 2026. Statistik dan ER desain berupa rumus Excel "
    "yang merujuk ke tabel A, jadi bisa ditelusuri dan berubah otomatis bila pilihan 'Dipakai?' diubah.",
    "Tugas A1: tandai pengukuran yang dipakai atau dibuang (beserta alasannya), lalu hitung statistik ER per rig di bagian B.",
    "Tugas A2: tetapkan ER desain per rig di bagian C. Putuskan satu nilai per rig atau berubah menurut kedalaman, "
    "dan nilai mana yang dipakai (rata-rata, nilai lain) beserta alasannya.",
    "Tugas A3: bor lama BH-1 s.d. BH-3 (palu donat tali-katrol, ER tidak diukur): tetapkan asumsi ER dan labelnya "
    "([Asumsi: ...] atau [Literatur: ...]).",
    "Tugas B: N60 semua uji SPT BH-1 s.d. BH-8 di lembar N60, ringkasan per bor di lembar Ringkasan N60.",
    "Tugas C: qt = qc + u2 (1 - a) tiap CPTu (FHWA GEC 5 Pers. 4.23 hal. 4-29) di lembar 'qt CPTu-1' s.d. "
    "'qt CPTu-8'; parameter a dan ringkasan di lembar Ringkasan qt.",
    "Tugas D: mutu contoh konsolidasi (Δe/e0 Lunne, εv SQD) di lembar Mutu Contoh.",
    "Setelah selesai, minta AI memeriksa. Cek silang dicatat di VERIFIKASI.md (kode T-06 dst.).",
]


def baca_energi(path=SUMBER):
    """Baris data lembar Energi Palu: (titik, kedalaman, jenis palu, ER %, N lapangan)."""
    ws = openpyxl.load_workbook(path, data_only=True)["Energi Palu"]
    data = []
    for r in ws.iter_rows(values_only=True):
        isi = [c for c in r if c is not None]
        if len(isi) == 5 and str(isi[0]).startswith("BH-") and isinstance(isi[3], (int, float)):
            data.append(tuple(isi))
    return data


def baca_spt():
    """Semua uji SPT BH-1 s.d. BH-8: dict bor, dari, sampai, n1, n2, n3, n (angka), jenis, catatan."""
    hasil = []
    for path, bor_list in [(SUMBER_LAMA, ["BH-1", "BH-2", "BH-3"]),
                           (SUMBER, ["BH-4", "BH-5", "BH-6", "BH-7", "BH-8"])]:
        wb = openpyxl.load_workbook(path, data_only=True)
        for bor in bor_list:
            ws = wb["SPT " + bor]
            kolom = None
            for row in ws.iter_rows(values_only=True):
                if "Dari (m)" in row:
                    kolom = {v: i for i, v in enumerate(row) if v is not None}
                    continue
                if kolom is None or not isinstance(row[kolom["Dari (m)"]], (int, float)):
                    continue
                g = lambda k: row[kolom[k]] if k in kolom else None  # noqa: E731
                n_teks, n2 = g("N-SPT"), g("N2 (15-30 cm)")
                if isinstance(n2, str) and "/" in n2:
                    jenis, n = "Penolakan", 50
                elif isinstance(n_teks, str) and "WOH" in n_teks:
                    jenis, n = "WOH", 0
                else:
                    jenis, n = "Biasa", n_teks
                hasil.append(dict(bor=bor, dari=g("Dari (m)"), sampai=g("Sampai (m)"), n1=g("N1 (0-15 cm)"),
                                  n2=n2, n3=g("N3 (30-45 cm)"), n=n, jenis=jenis,
                                  catatan=g("Catatan pengeboran") or ""))
    return hasil


def status_spt(u):
    """(dipakai 'Ya'/'Tidak', catatan) untuk satu uji SPT."""
    if u["bor"] == "BH-2" and "Pasir naik" in u["catatan"]:
        return "Tidak", ("Pasir naik ke casing dan muka air lubang di bawah MAT: dasar lubang terganggu, N terlalu "
                         "rendah (FHWA NHI-06-088 Tabel 3-10 hal. 3-61; temuan Tahap 1 no. 14).")
    if u["bor"] == "BH-8" and u["dari"] == 1.5:
        return "Tidak", "Urugan berpuing: pukulan mengenai pecahan beton, N tidak mewakili tanah."
    if u["jenis"] == "Penolakan":
        return "Ya", f"Penolakan ({u['n2']}): N ≥ 50, N60 adalah batas bawah."
    if u["jenis"] == "WOH":
        return "Ya", "WOH: tabung turun oleh berat palu, N = 0."
    if u["bor"] == "BH-2" and u["dari"] == 8:
        return "Ya", "Kayu lapuk di 8,4-8,7 m (ujung tabung); N tidak terpengaruh nyata."
    if u["bor"] in ("BH-1", "BH-2", "BH-3"):
        return "Ya", ""
    return "Ya", u["catatan"]


def baca_cptu(path=SUMBER_CPTU):
    """{nama: [(z, qc MPa, fs kPa, u2 kPa, kemiringan), ...]} untuk CPTu-1 s.d. CPTu-8."""
    wb = openpyxl.load_workbook(path, data_only=True)
    hasil = {}
    for i in range(1, 9):
        nama, data, mulai = f"CPTu-{i}", [], False
        for r in wb[nama].iter_rows(values_only=True):
            isi = [c for c in r if c is not None]
            if "Kedalaman (m)" in isi:
                mulai = True
                continue
            if mulai and isi and isinstance(isi[0], (int, float)):
                data.append(tuple(isi[:5]))
        hasil[nama] = data
    return hasil


def catatan_cptu(nama, z, qc, u2):
    """Catatan mutu per baris CPTu (singkat; rinciannya di lembar Ringkasan qt)."""
    if nama == "CPTu-4" and z <= 1.0:
        return "Di lubang awal 0-1 m: tidak dipakai (catatan C.3)."
    if nama == "CPTu-4" and z <= 4.5:
        return "u2 tidak andal, qt terlalu kecil (catatan C.2)."
    if nama == "CPTu-1" and 8.2 <= z <= 8.45 and qc > 2:
        return "qc melonjak tipis: kayu terkubur? (catatan C.6)."
    if u2 < 0:
        return "u2 negatif di atas MAT (catatan C.4)."
    return ""

def lembar_mutu_contoh(wb):
    """Tugas D: Δe/e0 (Lunne dkk. 1997) dan εv (Terzaghi dkk. 1996) tiap contoh konsolidasi."""
    hasil = mc.hitung(0.0)
    sens = {(h["titik"], h["contoh"]): h for h in mc.hitung(1.0)}
    lb = Lembar(wb.create_sheet("Mutu Contoh"), 15, "Tugas D - mutu contoh tak terganggu",
                [5, 7, 8, 8, 8, 8, 8, 7, 7, 7, 7, 7, 8, 8, 7, 8, 7, 21, 6, 11, 36])
    lb.catatan(LABEL + " Sumber: Ringkasan Konsolidasi dan Konsolidasi di 'Laboratorium.xlsx' dan "
               "'Laboratorium Tambahan.xlsx'; lapisan dari lembar Log tiap bor. Kriteria: FHWA GEC 5 (NHI-16-072) "
               "Tabel 6-1 (εv, Terzaghi dkk. 1996) dan Tabel 6-2 (Δe/e0, Lunne dkk. 1997), hal. 6-7. " + LABEL_AI)
    lb.kosong()
    lb.bagian("A", "Berat isi sementara per jenis lapisan (untuk σv0; parameter desain ditetapkan di 2.4)")
    for i, (j, (g, sumber)) in enumerate(mc.GAMMA.items(), start=1):
        lb.catatan(f"{i}. {j}: γ = {str(g).replace('.', ',')} kN/m³ {sumber}")
    lb.catatan("Batas lapisan dari log bor. MAT di muka tanah [Asumsi: keputusan Tahap 1, MAT desain sementara]; "
               "u0 = 9,81 z. Kolom 'Δe/e0 bila MAT 1 m' menunjukkan kepekaan terhadap asumsi ini.")
    lb.kosong()
    lb.bagian("B", "Δe/e0 dan εv saat dibebani ulang sampai σ'v0")
    r0 = lb.baris + 1
    baris = []
    for i, h in enumerate(hasil):
        r = r0 + i
        de, ocr, ev = f"P{r}", f"S{r}", f"Q{r}"
        lunne = (f'=IF({ocr}>4,"Di luar tabel (OCR > 4)",IF({ocr}<=2,'
                 f'IF({de}<0.04,"Sangat baik-istimewa",IF({de}<0.07,"Baik-cukup",IF({de}<0.14,"Buruk","Sangat buruk"))),'
                 f'IF({de}<0.03,"Sangat baik-istimewa",IF({de}<0.05,"Baik-cukup",IF({de}<0.1,"Buruk","Sangat buruk")))))')
        sqd = f'=IF({ev}<1,"A",IF({ev}<2,"B",IF({ev}<4,"C",IF({ev}<8,"D","E"))))'
        baris.append([i + 1, h["titik"], h["contoh"], h["z"], round(h["sv"], 1), f"=9.81*F{r}", f"=G{r}-H{r}",
                      h["e0"], h["s1"], h["e1"], h["s2"], h["e2"],
                      f"=L{r}+(N{r}-L{r})*LOG10(I{r}/K{r})/LOG10(M{r}/K{r})",
                      f"=(J{r}-O{r})/J{r}", f"=(J{r}-O{r})/(1+J{r})*100", h["sp"], f"=R{r}/I{r}", lunne, sqd,
                      round(sens[(h["titik"], h["contoh"])]["de"], 3), CATATAN_MUTU.get((h["titik"], h["contoh"]), "")])
    lb.tabel(["No", "Titik", "Contoh", "z tengah (m)", "σv0 (kPa)", "u0 (kPa)", "σ'v0 (kPa)", "e0",
              "σ'1 (kPa)", "e1", "σ'2 (kPa)", "e2", "e pada σ'v0", "Δe/e0", "εv (%)", "σ'p lab (kPa)", "OCR",
              "Peringkat Lunne", "SQD", "Δe/e0 bila MAT 1 m", "Catatan"],
             baris, rata=list("ccccccccccccccccccccl"),
             fmt=[None, None, None, "0.00", "0.0", "0.0", "0.0", "0.000", "0.00", "0.000", "0.00", "0.000", "0.000",
                  "0.000", "0.0", "0", "0.00", None, None, "0.000", None],
             fill_kolom={i: AI for i in (5, 6, 12, 13, 14, 16, 17, 18, 19, 20)})
    lb.ws._print_rows = None  # catatan C di halaman 2 tidak perlu kepala tabel
    lb.catatan("σ'1, e1, σ'2, e2 = dua tahap beban yang mengapit σ'v0 (kurva lab); e pada σ'v0 diinterpolasi linear "
               "terhadap log σ'. εv = Δe/(1 + e0). Pasangan tahap dipilih untuk MAT di muka tanah.")
    lb.kosong()
    lb.bagian("C", "Catatan tugas D")
    for i, t in enumerate(CATATAN_D_MUTU, start=1):
        lb.catatan(f"{i}. {t}", fill=AI)
    return r0, r0 + len(hasil) - 1


def buat(keluar=BERKAS):
    energi = baca_energi()
    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)

    lb = Lembar(wb.create_sheet("Petunjuk"), 1, "Petunjuk langkah 2.1 koreksi data", [6, 120])
    lb.catatan(LABEL + " " + LABEL_AI)
    lb.kosong()
    lb.tabel(["No", "Petunjuk"], [[i, t] for i, t in enumerate(PETUNJUK, start=1)], rata=list("cl"))

    lb = Lembar(wb.create_sheet("Energi Palu"), 2, "Tugas A - energi palu SPT", [6, 12, 7, 12, 20, 12, 12, 13, 44])
    lb.catatan(LABEL + " Sumber data: Bor Tambahan dan SPT.xlsx, lembar Energi Palu (ASTM D4633). " + LABEL_AI)
    lb.kosong()
    lb.bagian("A", "Data pengukuran energi (disalin) dan pilihan pakai")
    baris = [[i, t, RIG[t], z, palu, er, n, "Ya", CATATAN_UKUR.get((t, z), "")]
             for i, (t, z, palu, er, n) in enumerate(energi, start=1)]
    _, a1, a2 = lb.tabel(["No", "Titik", "Rig", "Kedalaman (m)", "Jenis palu", "ER terukur (%)", "N lapangan",
                          "Dipakai? (Ya/Tidak)", "Alasan bila dibuang / catatan"],
                         baris, rata=list("ccccl" "ccc" "l"), fmt=[None, None, None, "0.0", None, "0", "0", None, None],
                         fill_kolom={7: AI, 8: AI})
    titik, rig, er, pakai = (f"'Energi Palu'!${k}${a1}:${k}${a2}" for k in "DEHJ")

    lb = Lembar(wb.create_sheet("ER Desain"), 3, "Tugas A - statistik dan keputusan ER desain",
                [6, 22, 10, 11, 26, 9, 14, 13, 44])
    lb.catatan(LABEL + " Rumus merujuk ke lembar Energi Palu tabel A. " + LABEL_AI)
    lb.kosong()
    lb.bagian("B", "Statistik ER per bor dan per rig (dari pengukuran yang dipakai)")
    kelompok = [("BH-4", titik), ("BH-5", titik), ("BH-6", titik), ("BH-7", titik), ("BH-8", titik),
                ("A", rig), ("B", rig)]
    r_b = lb.baris + 1
    baris_b = []
    for i, (k, rentang) in enumerate(kelompok):
        r = r_b + i
        syarat = f'{rentang},"{k}",{pakai},"Ya"'
        baris_b.append([
            i + 1, k if k.startswith("BH") else f"Rig {k} gabungan",
            f"=COUNTIFS({syarat})", f"=AVERAGEIFS({er},{syarat})",
            f'=SQRT(SUMPRODUCT(({rentang}="{k}")*({pakai}="Ya")*({er}-F{r})^2)/(E{r}-1))',
            f"=_xlfn.MINIFS({er},{syarat})", f"=_xlfn.MAXIFS({er},{syarat})", f"=G{r}/F{r}*100",
            CATATAN_STAT.get(k, "")])
    lb.tabel(["No", "Kelompok", "n", "Rata-rata (%)", "Simpangan baku (%)", "Min (%)", "Maks (%)",
              "Koefisien variasi (%)", "Catatan"],
             baris_b, rata=list("ccccccccl"), fmt=[None, None, "0", "0.0", "0.0", "0", "0", "0.0", None],
             fill_kolom={8: AI})
    lb.ws._print_rows = None  # tabel B pendek; kepalanya tidak diulang di atas tabel C saat dicetak
    ref = {k: f"F{r_b + i}" for i, (k, _) in enumerate(kelompok)}

    lb.kosong()
    lb.bagian("C", "Keputusan ER desain")
    r_c = lb.baris + 1
    baris_c = [
        ["BH-4", f"=ROUND({ref['BH-4']},0)", "[Uji sendiri: ASTM D4633, rata-rata BH-4]", "A", "Otomatis", "Tetap"],
        ["BH-5", f"=ROUND({ref['BH-5']},0)", "[Uji sendiri: ASTM D4633, rata-rata BH-5]", "A", "Otomatis", "Tetap"],
        ["BH-6", f"=ROUND({ref['BH-6']},0)", "[Uji sendiri: ASTM D4633, rata-rata BH-6]", "A", "Otomatis", "Tetap"],
        ["BH-7, BH-8", f"=ROUND({ref['B']},0)", "[Uji sendiri: ASTM D4633, rata-rata rig B]", "B", "Donat",
         "Tetap"],
        ["BH-1, BH-2, BH-3", f"=E{r_c + 3}", "[Asumsi: sama dengan rig B terukur]", "Lama",
         "Donat, tidak diukur", "Tetap"],
        ["BH-1, BH-2, BH-3 (cek sensitivitas)", 60,
         "[Literatur: AASHTO, dikutip FHWA NHI-06-088 hal. 3-55]", "Lama", "Donat, tidak diukur",
         "Hanya sensitivitas"],
    ]
    lb.tabel(["No", "Bor", "ER desain (%)", "Faktor ER/60", "Label sumber", "Rig", "Palu",
              "Bentuk (tetap / per kedalaman)", "Dasar / alasan"],
             [[i + 1, b, e, f"=E{r_c + i}/60", lab, rg, pl, bt, ALASAN_C[i]]
              for i, (b, e, lab, rg, pl, bt) in enumerate(baris_c)],
             rata=list("clcclcccl"), fmt=[None, None, "0", "0.00", None, None, None, None, None],
             fill_kolom={2: AI, 3: AI, 4: AI, 7: AI, 8: AI}, beku=False)

    lb.kosong()
    lb.bagian("D", "Catatan telaah data energi dan SPT")
    for i, t in enumerate(CATATAN_D, start=1):
        lb.catatan(f"{i}. {t}", fill=AI)

    er_sel = {"BH-4": r_c, "BH-5": r_c + 1, "BH-6": r_c + 2, "BH-7": r_c + 3, "BH-8": r_c + 3,
              "BH-1": r_c + 4, "BH-2": r_c + 4, "BH-3": r_c + 4}

    spt = baca_spt()
    lb = Lembar(wb.create_sheet("N60"), 4, "Tugas B - N60 semua bor",
                [6, 8, 7, 9, 9, 7, 10, 7, 10, 9, 9, 11, 45])
    lb.catatan(LABEL + " Sumber: SPT BH-1 s.d. BH-3 dari 'Bor dan SPT.xlsx', BH-4 s.d. BH-8 dari "
               "'Bor Tambahan dan SPT.xlsx'. N60 = N x ER/60 (FHWA NHI-06-088 Pers. 3-2 hal. 3-55). "
               "ER dari lembar ER Desain. " + LABEL_AI)
    lb.kosong()
    lb.bagian("A", "N lapangan, ER, dan N60 tiap uji")
    r_a = lb.baris + 1
    baris = []
    for i, u in enumerate(spt):
        r = r_a + i
        pakai, cat = status_spt(u)
        baris.append([i + 1, u["bor"], RIG_SEMUA[u["bor"]], u["dari"], u["sampai"], u["n1"], u["n2"],
                      "-" if u["n3"] is None else u["n3"], u["n"], f"='ER Desain'!$E${er_sel[u['bor']]}",
                      f"=K{r}*L{r}/60", pakai, cat])
    _, d1, d2 = lb.tabel(["No", "Bor", "Rig", "Dari (m)", "Sampai (m)", "N1", "N2", "N3", "N lapangan",
                          "ER (%)", "N60", "Dipakai? (Ya/Tidak)", "Catatan"],
                         baris, rata=list("cccccccccccc") + ["l"],
                         fmt=[None, None, None, "0.00", "0.00", "0", "0", "0", "0", "0", "0.0", None, None],
                         fill_kolom={9: AI, 10: AI, 11: AI, 12: AI})

    lb = Lembar(wb.create_sheet("Ringkasan N60"), 5, "Tugas B - ringkasan N60 per bor",
                [6, 10, 8, 9, 9, 9, 10, 12, 12, 46])
    lb.catatan(LABEL + " Rumus merujuk ke lembar N60. " + LABEL_AI)
    lb.kosong()
    lb.bagian("B", "Jumlah uji per bor dan N60 rata-rata pasir 10-20 m")
    rg = lambda k: f"N60!${k}${d1}:${k}${d2}"  # noqa: E731
    bor_r, dari_r, n60_r, pakai_r, cat_r = rg("D"), rg("F"), rg("M"), rg("N"), rg("O")
    r_s = lb.baris + 1
    ringkas = []
    for i, bor in enumerate(["BH-1", "BH-2", "BH-3", "BH-4", "BH-5", "BH-6", "BH-7", "BH-8"]):
        r = r_s + i
        pasir = f'{bor_r},"{bor}",{pakai_r},"Ya",{dari_r},">=10",{dari_r},"<20"'
        ringkas.append([i + 1, bor, RIG_SEMUA[bor], f'=COUNTIFS({bor_r},"{bor}")',
                        f'=COUNTIFS({bor_r},"{bor}",{pakai_r},"Ya")',
                        f'=COUNTIFS({bor_r},"{bor}",{pakai_r},"Tidak")',
                        f'=COUNTIFS({bor_r},"{bor}",{cat_r},"Penolakan*")',
                        f"=COUNTIFS({pasir})", f"=IFERROR(AVERAGEIFS({n60_r},{pasir}),\"-\")",
                        RINGKAS_CAT.get(bor, "")])
    lb.tabel(["No", "Bor", "Rig", "Jumlah uji", "Dipakai", "Tidak dipakai", "Penolakan (N ≥ 50)",
              "Uji 10-20 m dipakai", "N60 rata-rata 10-20 m (pasir)", "Catatan"],
             ringkas, rata=list("ccccccccc") + ["l"], fmt=[None, None, None, "0", "0", "0", "0", "0", "0.0", None],
             fill_kolom={9: AI})
    lb.ws._print_rows = None
    lb.kosong()
    lb.bagian("C", "Catatan tugas B")
    for i, t in enumerate(CATATAN_B, start=1):
        lb.catatan(f"{i}. {t}", fill=AI)

    cptu = baca_cptu()
    lb = Lembar(wb.create_sheet("Ringkasan qt"), 6, "Tugas C - koreksi qt CPTu, ringkasan",
                [6, 10, 12, 9, 14, 12, 13, 12, 42])
    lb.catatan(LABEL + " Sumber: CPTu.xlsx. qt = qc + u2 (1 - a), FHWA GEC 5 (NHI-16-072) Pers. 4.23 hal. 4-29. "
               "Rf = fs/qt. Rumus merujuk ke lembar 'qt CPTu-n'. " + LABEL_AI)
    lb.kosong()
    lb.bagian("A", "Parameter")
    r_par = lb.baris + 1
    lb.tabel(["No", "Simbol", "Nilai", "Satuan", "Sumber", "Luas konus (cm²)", "Laju (mm/s)", "Posisi filter",
              "Keterangan"],
             [[1, "a", A_KONUS, "-", "CPTu.xlsx lembar Titik", 10, 20, "u2",
               "Rasio luas bersih konus (kalibrasi penyedia)"]],
             rata=list("cccclcccl"), fmt=[None, None, "0.00", None, None, "0", "0", None, None])
    a_sel = f"'Ringkasan qt'!$E${r_par}"
    lb.ws._print_rows = None
    lb.kosong()
    lb.bagian("B", "Besar koreksi qt per CPTu (rata-rata per rentang kedalaman)")
    r1 = 8  # baris data pertama di setiap lembar 'qt CPTu-n' (diperiksa di bawah)
    ringkas = []
    for i, (nama, data) in enumerate(cptu.items()):
        r2 = r1 + len(data) - 1
        z, kor, inc = (f"'qt {nama}'!${k}${r1}:${k}${r2}" for k in "CJG")

        def rata(a, b):
            return f'=AVERAGEIFS({kor},{z},">={a}",{z},"<={b}")'

        ringkas.append([i + 1, nama, f"=MAX({z})", len(data), rata(2, 9), rata(12, 18), rata(20, 30),
                        f"=MAX({inc})", CATATAN_CPTU_RINGKAS.get(nama, "")])
    lb.tabel(["No", "CPTu", "Kedalaman akhir (m)", "Jumlah data", "Koreksi lempung lunak 2-9 m (%)",
              "Koreksi pasir 12-18 m (%)", "Koreksi lempung 20-30 m (%)", "Kemiringan maks (°)", "Catatan"],
             ringkas, rata=list("ccccccccl"), fmt=[None, None, "0.00", "0", "0.0", "0.0", "0.0", "0.0", None],
             fill_kolom={8: AI}, beku=False)
    lb.kosong()
    lb.bagian("C", "Catatan tugas C")
    for i, t in enumerate(CATATAN_C, start=1):
        lb.catatan(f"{i}. {t}", fill=AI)

    for j, (nama, data) in enumerate(cptu.items()):
        lb = Lembar(wb.create_sheet(f"qt {nama}"), 7 + j, f"Tugas C - qt {nama}",
                    [11, 10, 10, 10, 12, 10, 10, 11, 50])
        lb.catatan(f"{LABEL} Data {nama} dari CPTu.xlsx (disalin). {LABEL_AI}")
        lb.kosong()
        r0 = lb.baris
        baris = []
        for k, (z, qc, fs, u2, inc) in enumerate(data):
            r = r0 + 1 + k
            baris.append([z, qc, fs, u2, inc, f"=D{r}+F{r}/1000*(1-{a_sel})", f"=E{r}/(H{r}*1000)*100",
                          f"=(H{r}-D{r})/D{r}*100", catatan_cptu(nama, z, qc, u2)])
        _, d1, _ = lb.tabel(["Kedalaman (m)", "qc (MPa)", "fs (kPa)", "u2 (kPa)", "Kemiringan (°)", "qt (MPa)",
                             "Rf = fs/qt (%)", "Koreksi qt (%)", "Catatan"],
                            baris, rata=list("ccccccccl"),
                            fmt=["0.00", "0.000", "0.0", "0.0", "0.0", "0.000", "0.00", "0.0", None],
                            fill_kolom={5: AI, 6: AI, 7: AI, 8: AI})
        if d1 != r1:
            raise RuntimeError(f"Data {nama} mulai baris {d1}, rumus ringkasan memakai baris {r1}")

    lembar_mutu_contoh(wb)

    keluar.parent.mkdir(parents=True, exist_ok=True)
    wb.save(keluar)
    return keluar


if __name__ == "__main__":
    print(buat())
