"""Langkah 3.1: BIM Execution Plan (BEP) proyek RS Tepian Batanghari dalam .docx (format FORMAT LAPORAN DAN EXCEL.md).

Isi template diambil dari skrip/tahap3_template_bim.py supaya BEP dan template BIMCraft selalu sama.
Disusun AI atas permintaan Defsa (19 Nov 2026); disetujui Defsa 19 Nov 2026.
Jalankan:  .venv\\Scripts\\python.exe skrip\\tahap3_bep.py
"""
from pathlib import Path

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

import tahap3_template_bim as tpl
from format_dokumen import Laporan, angka_id, perbarui_word

AKAR = Path(__file__).resolve().parents[1]
KELUAR = AKAR / "03 Desain Konsep" / "3.1 BEP.docx"
PDF = KELUAR.with_suffix(".pdf")
STATUS = "disetujui Defsa 19 Nov 2026"


def sampul(lap):
    d = lap.doc

    def baris(teks, ukuran=12, tebal=False, miring=False, sesudah=0):
        p = d.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(sesudah)
        r = p.add_run(teks)
        r.font.size, r.bold, r.italic = Pt(ukuran), tebal, miring

    for _ in range(4):
        d.add_paragraph()
    baris("RENCANA PELAKSANAAN BIM", 16, True)
    baris("(BIM EXECUTION PLAN)", 14, True, sesudah=36)
    baris("JASA KONSULTANSI PERENCANAAN PEMBANGUNAN GEDUNG", 12, True)
    baris("RUMAH SAKIT TEPIAN BATANGHARI", 14, True)
    baris("6 Lantai + 1 Basement, Tepi Utara Sungai Batanghari, Kota Jambi", 12, sesudah=48)
    baris("Pemberi tugas: Yayasan Kesehatan Tepian Batanghari")
    baris("Nomor dokumen: RSTB-KOO-T3-BEP, revisi B", sesudah=48)
    baris("Disusun oleh:")
    baris("Defsa Yurinda", tebal=True)
    baris("(Studi kasus portofolio perencanaan)", sesudah=60)
    baris("JAMBI", tebal=True)
    baris("NOVEMBER 2026", tebal=True, sesudah=36)
    baris("DOKUMEN SIMULASI untuk studi kasus portofolio; tidak untuk konstruksi. Disusun AI atas permintaan penulis "
          f"(19 Nov 2026); status: {STATUS}.", 10, miring=True)


def bab1(lap):
    lap.bab("I", "Pendahuluan", mulai_arab=True)
    lap.subbab("1.1", "Informasi Proyek")
    lap.tabel("Informasi Proyek", ["Butir", "Keterangan"], [
        ["Nama proyek", "Pembangunan Gedung Rumah Sakit Tepian Batanghari (kode RSTB)"],
        ["Pemberi tugas", "Yayasan Kesehatan Tepian Batanghari (simulasi)"],
        ["Lokasi", "Tepi utara Sungai Batanghari, Kota Jambi; lahan fiktif 140 m × 90 m"],
        ["Bangunan", "Rumah sakit 150 tempat tidur, 6 lantai + basement, kategori risiko IV"],
        ["Tahap", "Desain konsep (Tahap 3) sampai DED dan RAB (Tahap 7-9)"],
        ["Perangkat utama", "BIMCraft 0.12.0, IfcOpenShell, Blender + Bonsai, CADCraft"],
    ], [4.0, 11.5], rata=list("ll"), sumber="TOR Owner bagian 1-4")
    lap.subbab("1.2", "Maksud Dokumen")
    lap.paragraf("Dokumen ini menetapkan cara model BIM proyek dibuat, dinamai, diperiksa, dan dipertukarkan, supaya "
                 "model yang dibuat di BIMCraft dapat dipakai langsung untuk analisis struktur, gambar DED, volume RAB, "
                 "dan jadwal tanpa pemodelan ulang. Setiap model proyek dimulai dari template "
                 f"*{tpl.BIMC.name}* yang isinya dirinci di Lampiran A.")
    lap.subbab("1.3", "Dasar Penyusunan")
    lap.daftar([
        "TOR Owner bagian 7A butir 4: model BIM berformat IFC sebagai sumber gambar, volume, dan jadwal; bagian 9 "
        "butir 3: model BIM termasuk keluaran laporan akhir.",
        "Permen PUPR 22/2018 Lampiran hal. 201 butir 13: BIM wajib untuk bangunan gedung negara tidak sederhana "
        "di atas 2.000 m² dan di atas 2 lantai, dengan keluaran gambar arsitektur, struktur, utilitas, lansekap, "
        "rincian volume, dan RAB. Rumah sakit ini milik yayasan (bukan bangunan gedung negara), sehingga ketentuan "
        "itu dipakai sebagai acuan praktik, bukan kewajiban.",
        "Standar internasional manajemen informasi BIM (seri ISO 19650) dan spesifikasi LOD BIMForum belum ada di "
        "folder *acuan/*; definisi di dokumen ini ditulis sendiri dan tidak mengutip pasal standar tersebut.",
    ])
    lap.subbab("1.4", "Status Dokumen")
    lap.paragraf(f"Revisi B, 19 November 2026, {STATUS}. Revisi B mengganti level sesuai peil lantai dasar +12,85 (langkah 3.3); revisi A memakai +11,80 dari TOR. Level, tinggi lantai, dan dimensi tipe di template bersifat "
                 "sementara dan diperbarui setelah langkah 3.3 (peil), 3.4 (program ruang), 3.5 (opsi basement), dan "
                 "3.6 (pra-dimensi). Setiap perubahan dicatat sebagai revisi BEP.")


def bab2(lap):
    lap.bab("II", "Tujuan dan Penggunaan BIM")
    lap.subbab("2.1", "Penggunaan per Tahap")
    lap.tabel("Penggunaan BIM per Tahap", ["Tahap", "Penggunaan model", "Keluaran"], [
        ["3 Desain konsep", "Massa, level, grid, pra-dimensi; perbandingan opsi basement dan sistem struktur",
         "Model LOD 200, luas per lantai, volume kasar"],
        ["4 Struktur atas", "Geometri dan beban ke model analisis (OpenSeesPy); hasil desain kembali ke tipe",
         "Model struktur LOD 300"],
        ["5-6 Struktur tengah dan bawah", "Pelat basement, pile cap, tiang, dinding penahan; koordinasi dengan tanah",
         "Model LOD 300, cek tumpang tindih"],
        ["7 DED dan RKS", "Denah, potongan, detail dari model; digambar ulang di CADCraft dengan kop KOP_A3",
         "Model LOD 350, gambar DED"],
        ["8 RAB (5D)", "Volume bersih dari IFC dengan skrip (aturan potong di pertemuan)", "Daftar volume, RAB"],
        ["9 Jadwal (4D)", "Elemen dikelompokkan per zona dan urutan kerja; kalender kerja proyek",
         "Jadwal dan simulasi 4D (Bonsai)"],
    ], [3.4, 7.0, 5.1], rata=list("lll"), sumber="00 RANCANGAN.md bagian 3 dan 6")
    lap.subbab("2.2", "Batas Penggunaan")
    lap.daftar([
        "Desain MEP di luar lingkup (TOR 7A butir 7): model hanya memuat ruang, beban, dan lubang MEP.",
        "Model bukan sumber hitungan inti. Gaya dalam, tulangan, dan daya dukung dihitung di Excel/Python dengan "
        "pasal SNI, lalu dimensinya dimasukkan ke model.",
        "Model tanah (stratigrafi U1-U8) tetap di gambar GT-01 s.d. GT-15 Tahap 2; model BIM memuat pondasi, bukan "
        "lapisan tanah.",
    ])


def bab3(lap):
    lap.bab("III", "Peran dan Tanggung Jawab")
    lap.tabel("Peran dan Tanggung Jawab", ["Pihak", "Peran", "Tanggung jawab model"], [
        ["Defsa Yurinda", "Insinyur perencana, manajer BIM",
         "Keputusan teknis, pemodelan inti di BIMCraft, pemeriksaan dan persetujuan model"],
        ["Asisten AI", "Penyusun skrip dan draf, pemeriksa",
         "Template, skrip IFC (validasi, volume, pelengkap material), cek silang; tidak menyetujui"],
        ["Pemberi tugas (simulasi)", "Pemilik informasi kebutuhan", "Data ruang, MEP, tipe helikopter; persetujuan opsi"],
        ["Sesi skenario", "Pembangkit data simulasi", "Data owner dan kejadian; tidak menyentuh model"],
    ], [3.6, 4.4, 7.5], rata=list("lll"))
    lap.paragraf("Setiap berkas model berstatus *draf AI*, *diperiksa*, atau *disetujui Defsa <tanggal>*. Status yang "
                 "sama ditulis di parameter *RSTB_Status* elemen yang diubah dan di catatan commit.")


def bab4(lap):
    lap.bab("IV", "Standar Pemodelan")
    lap.subbab("4.1", "Satuan dan Koordinat")
    lap.daftar([
        "Satuan model milimeter (mm); luas m², volume m³. Satuan ini juga satuan IFC yang diekspor BIMCraft.",
        "Titik asal model (0, 0) di sudut barat daya lahan; sumbu x ke timur dan y ke utara, sama dengan koordinat "
        "lokal TOR bagian 4.1 dan semua gambar Tahap 1-2.",
        "Sumbu z model = elevasi datum lokal proyek. BM-1 di sudut barat daya bernilai +10,000 m, sehingga di model "
        "berada di z = 10.000 mm. Level diberi elevasi absolut (misalnya LT1 = 12.850 mm = +12,85), sehingga elevasi "
        "di model, gambar tanah, dan muka air (+11,20) dapat dibandingkan langsung tanpa konversi.",
        "Arah utara proyek = utara sebenarnya (sudut 0°) sampai ada data survei yang menyatakan lain.",
    ])
    lap.subbab("4.2", "Struktur Model dan Hierarki IFC")
    lap.paragraf("Hierarki IFC: IfcProject (Rumah Sakit Tepian Batanghari) - IfcSite - IfcBuilding (gedung utama) - "
                 "IfcBuildingStorey (B1 s.d. ATAP). Setiap elemen harus berada di satu lantai; elemen tanpa lantai "
                 "ditolak pada pemeriksaan mutu. Di Tahap 3 arsitektur dan struktur berada dalam satu model konsep; "
                 "mulai Tahap 4 model dipisah per disiplin (ARS, STR, GEO) dengan titik asal yang sama.")
    lap.subbab("4.3", "Level Sementara")
    rows = []
    for i, (nama, elev) in enumerate(tpl.LEVEL):
        tinggi = (tpl.LEVEL[i + 1][1] - elev) / 1000 if i + 1 < len(tpl.LEVEL) else None
        rows.append([nama, angka_id(elev), f"+{elev / 1000:.2f}".replace(".", ","),
                     "-" if tinggi is None else f"{tinggi:.2f}".replace(".", ",")])
    lap.tabel("Level Template (Sementara)", ["Level", "Elevasi model (mm)", "Elevasi datum (m)", "Tinggi ke level atas (m)"],
              rows, [3.0, 4.0, 4.0, 4.5], rata=list("cccc"),
              sumber="LT1 +12,85 dari langkah 3.3 (Q100 + 0,50); tinggi lantai dan B1 [Asumsi], "
                     "ditetapkan di 3.4-3.6")
    lap.subbab("4.4", "Penamaan Berkas")
    lap.paragraf("Pola: *RSTB-<disiplin>-<tahap>-<deskripsi>[-R<nn>].<ekstensi>*. Kode disiplin: TPL (template), "
                 "KOO (koordinasi dan dokumen BIM), ARS (arsitektur), STR (struktur), GEO (pondasi dan galian). "
                 "Contoh: *RSTB-STR-T4-StrukturAtas-R01.bimc* dan salinan IFC-nya dengan nama sama.")
    lap.subbab("4.5", "Penamaan Tipe")
    lap.tabel("Kode Tipe Elemen", ["Kode", "Elemen", "Pola nama", "Contoh"], [
        ["KL", "Kolom struktur", "KL-<b>x<h>-fc<mutu>", "KL-600x600-fc35"],
        ["BL", "Balok", "BL-<b>x<h>-fc<mutu>", "BL-400x700-fc30"],
        ["PL", "Pelat lantai", "PL-<tebal>-fc<mutu>[-S2]", "PL-400-fc35-S2"],
        ["DG", "Dinding geser", "DG-<tebal>-fc<mutu>", "DG-300-fc35"],
        ["DB", "Dinding basement", "DB-<tebal>-fc<mutu>-S2", "DB-400-fc35-S2"],
        ["DD", "Dinding pengisi", "DD-<tebal>-<bahan>", "DD-150-Bata"],
        ["TP, PC", "Tiang, pile cap (Tahap 6)", "TP-<diameter>-<jenis>, PC-<n tiang>", "TP-800-Bor"],
    ], [1.8, 3.6, 5.2, 4.9], rata=list("clll"))
    lap.paragraf("Akhiran *-S2* menandai beton yang menyentuh gambut atau lempung dan wajib memenuhi kelas paparan S2 "
                 "dengan perlindungan asam (keputusan Tahap 2 nomor 4).")
    lap.subbab("4.6", "Material")
    lap.tabel("Material Template", ["Material", "Dipakai untuk", "Catatan"], [
        ["Beton fc 30 S2", "Balok, pelat atas", "Mutu sementara; ditetapkan di Tahap 4"],
        ["Beton fc 35 S2", "Kolom, dinding geser, elemen basement", "Kelas paparan S2 untuk elemen kontak tanah"],
        ["Bata ringan", "Dinding pengisi", "Beban dinding dihitung di Tahap 4"],
    ], [4.0, 5.5, 6.0], rata=list("lll"))
    lap.subbab("4.7", "Parameter Proyek")
    lap.tabel("Parameter Pset_RSTB_Umum", ["Parameter", "Isi"], [[n, k] for n, k in tpl.PARAMETER],
              [4.5, 11.0], rata=list("ll"))
    lap.paragraf("Parameter ini berlaku untuk dinding, pelat, kolom, kolom struktur, balok, telapak, atap, tangga, "
                 "pagar, ruang, dan komponen, dan diekspor ke IFC sebagai property set *Pset_RSTB_Umum* (sudah diuji: "
                 "nilai pada kolom, balok, dan pelat terbaca IfcOpenShell).")


def bab5(lap):
    lap.bab("V", "Tingkat Kematangan Model (LOD)")
    lap.paragraf("Definisi ringkas yang dipakai proyek: LOD 200 = elemen ada dengan ukuran, letak, dan jenis perkiraan; "
                 "LOD 300 = ukuran, letak, dan jenis hasil hitungan desain; LOD 350 = LOD 300 ditambah sambungan dan "
                 "pertemuan antarelemen yang cukup untuk gambar DED dan volume RAB.")
    lap.tabel("Matriks LOD per Tahap", ["Elemen", "Tahap 3", "Tahap 4-6", "Tahap 7"], [
        ["Level dan grid", "200", "300", "300"],
        ["Kolom, balok, pelat", "200", "300", "350"],
        ["Dinding geser dan inti", "200", "300", "350"],
        ["Pelat dan dinding basement", "200", "300", "350"],
        ["Tiang dan pile cap", "-", "300", "350"],
        ["Dinding pengisi, pintu, jendela", "200", "200", "300"],
        ["Ruang (room)", "200", "200", "300"],
        ["Lubang MEP utama", "-", "200", "300"],
    ], [6.0, 3.0, 3.2, 3.3], rata=list("lccc"))


def bab6(lap):
    lap.bab("VI", "Kendali Mutu Model")
    lap.paragraf("Setiap model yang diserahkan diperiksa dengan skrip IfcOpenShell sebelum disetujui. Toleransi volume "
                 "terhadap hitungan terpisah 5 % (*00 RANCANGAN.md* bagian 7, struktur ≤ 5-10 %).")
    lap.tabel("Pemeriksaan Mutu Model", ["No", "Pemeriksaan", "Cara", "Syarat lolos"], [
        ["1", "Skema dan satuan", "Baca IFC", "IFC4, satuan mm"],
        ["2", "Hierarki dan lantai", "Daftar IfcBuildingStorey dan wadah elemen",
         "Semua elemen di satu lantai; nama dan elevasi sesuai Tabel 4.1"],
        ["3", "Parameter", "Baca Pset_RSTB_Umum", "RSTB_LOD dan RSTB_Status terisi"],
        ["4", "Material", "Baca IfcMaterial tiap elemen", "Elemen struktur bermaterial beton sesuai kode tipe"],
        ["5", "Tumpang tindih", "Cek benturan antarelemen", "Tidak ada benturan keras yang tidak disengaja"],
        ["6", "Volume", "Volume bersih skrip vs hitungan Excel", "Selisih ≤ 5 %"],
    ], [1.0, 3.5, 5.5, 5.5], rata=list("clll"))
    lap.subbab("6.1", "Keterbatasan Perangkat yang Diketahui")
    lap.daftar([
        "BIMCraft 0.12.0 tidak mengekspor material kolom beton ke IFC (balok, pelat, dan dinding terekspor). "
        "Material kolom diisi skrip pasca-ekspor dari kode tipe (*-fc35*) sebelum pemeriksaan nomor 4.",
        "Tabel volume BIMCraft tidak mengurangi tumpang tindih di pertemuan (3,1 % dobel pada uji portal); volume RAB "
        "memakai skrip volume bersih: kolom dan balok *GrossVolume*, pelat dan telapak *NetVolume*.",
        "Tipe pelat bawaan BIMCraft tebal 200 mm; selalu pakai tipe proyek dari template.",
        "Versi BIMCraft dikunci 0.12.0 selama proyek supaya berkas tetap terbaca.",
    ])


def bab7(lap):
    lap.bab("VII", "Pertukaran, Penyimpanan, dan Jadwal")
    lap.subbab("7.1", "Alur Pertukaran")
    lap.paragraf("BIMCraft (*.bimc*, model induk) diekspor ke IFC4, lalu IFC dipakai oleh Python (validasi, volume, "
                 "tiang, RAB), Blender + Bonsai (4D/5D), dan sebagai acuan gambar DED yang digambar di CADCraft "
                 "dengan kop tunggal *KOP_A3*. Perubahan dilakukan di model induk, tidak di IFC. Agen AI bekerja lewat "
                 "server MCP *bimcraft* (tanpa jendela) atau *bimcraft-jendela* (jendela dibuka dengan "
                 "*bimcraft.exe --control 0*).")
    lap.subbab("7.2", "Penyimpanan dan Versi")
    lap.daftar([
        "Model dan IFC disimpan di folder *model/* repo Git privat; setiap perubahan lewat cabang *fitur/...* dan PR.",
        "Berkas lebih dari 20 MB (IFC besar, video 4D) diterbitkan lewat GitHub Releases.",
        "Revisi model ditandai akhiran *-R<nn>* dan dicatat di *PROGRES.md*.",
    ])
    lap.subbab("7.3", "Jadwal Penyerahan Model")
    lap.tabel("Jadwal Penyerahan Model", ["Penyerahan", "Isi", "Tahap"], [
        ["M0 Template", f"{tpl.BIMC.name} dan IFC-nya", "3.1"],
        ["M1 Model konsep", "Massa, level, grid, pra-dimensi, basement opsi terpilih (LOD 200)", "3.9"],
        ["M2 Model struktur", "Struktur atas, tengah, bawah (LOD 300)", "4-6"],
        ["M3 Model DED", "Model LOD 350 untuk gambar, volume, dan jadwal", "7-9"],
    ], [3.5, 9.5, 2.5], rata=list("llc"))


def lampiran_a(lap):
    lap.lampiran("A", "Isi Template BIMCraft")
    lap.paragraf(f"Berkas: *model/{tpl.BIMC.name}* dan *model/{tpl.IFC.name}*, dibangun ulang dengan "
                 "*skrip/tahap3_template_bim.py*. Grid kolom belum dimasukkan (langkah 3.6).", inden=False)
    rows = []
    for t in tpl.TIPE:
        if "layers" in t:
            ukuran = f"tebal {t['layers'][0]['thickness']}"
            mat = t["layers"][0]["material"]
        else:
            ukuran = f"{t['width']} × {t['depth']}"
            mat = t["material"]
        rows.append([t["name"], t["category"], ukuran, mat])
    lap.tabel("Pustaka Tipe Template", ["Tipe", "Kategori BIMCraft", "Ukuran (mm)", "Material"], rows,
              [4.4, 3.6, 3.5, 4.0], rata=list("lccl"), sumber="Dimensi sementara [Asumsi]; diganti hasil langkah 3.6")


def buat(perbarui=True):
    lap = Laporan()
    sampul(lap)
    lap.sampul_selesai()
    lap.bagian_awal()
    lap.daftar_isi()
    lap.daftar_tabel()
    for f in (bab1, bab2, bab3, bab4, bab5, bab6, bab7, lampiran_a):
        f(lap)
    lap.simpan(KELUAR)
    if perbarui:
        ok, pesan = perbarui_word(KELUAR, PDF)
        if not ok:
            print("Word gagal:", pesan[:300])
    return KELUAR


if __name__ == "__main__":
    print(buat())
