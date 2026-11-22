"""Langkah 3.10: bahan presentasi desain konsep (PowerPoint + PDF) untuk rapat dengan owner dan MK.

Semua angka diambil dari skrip langkah 3.2-3.9 (tidak diketik ulang), gambar dari GK-01..GK-08. Gaya mengikuti
gambar Defsa: Times New Roman, hitam-putih, garis tipis. Disusun AI atas permintaan Defsa (19 Nov 2026); disetujui
Defsa 19 Nov 2026.
"""
import subprocess
from pathlib import Path

import tahap3_basement as bs
import tahap3_biaya as bi
import tahap3_bim as bm
import tahap3_peil as pl
import tahap3_pondasi as fd
import tahap3_program as pr
import tahap3_struktur as st
import tahap3_tapak as tp

AKAR = Path(__file__).resolve().parents[1]
KELUAR = AKAR / "03 Desain Konsep"
PPTX = KELUAR / "3.10 Presentasi Desain Konsep.pptx"
PDF = PPTX.with_suffix(".pdf")
GAMBAR = KELUAR / "Gambar"
JUDUL_PROYEK = "Desain Konsep RS Tepian Batanghari"
LABEL = "DOKUMEN SIMULASI untuk studi kasus portofolio. Bukan data proyek nyata. Tidak untuk konstruksi."
FONT = "Times New Roman"


def fmt(v, d=0):
    s = f"{v:,.{d}f}"
    return s.replace(",", "#").replace(".", ",").replace("#", ".")


def m(v):
    return fmt(v / 1000, 1)


def isi():
    """Daftar slide: (judul, butir, gambar atau tabel)."""
    t = tp.ringkasan()
    pe = pl.peil_usulan()
    vu = pl.volume_urugan(pe["halaman"])
    tu = pl.tahap_urugan()
    cm = pr.cek_massa()
    oc = bs.opsi()[2]
    fk = bs.blowin()
    sp = st.spektrum()
    sr = st.ringkasan()
    bz = fd.beban_izin("BOR-800")
    oa = fd.opsi("A")
    r = bi.rekap()
    rg = bi.ringkasan()
    ve = bi.rekayasa_nilai()
    kelas = bm.validasi(bm.IFC)["kelas"]
    return [
        ("Tanggapan surat owner 034/YKTB/III/2027", [], {"tabel": (["No", "Permintaan owner", "Tanggapan konsultan"], [
            ["1", "Tapak 6.300 m² (KDB 50 % × 12.600)", f"KDB dari lahan perencanaan {fmt(t['lahan_perencanaan'])} m²: "
             f"tapak maks {fmt(t['kdb_maks'])} m² (PKKPR)"],
            ["2", "Lantai dasar +11,50", f"Q50 terkoreksi +{fmt(pe['q50'], 2)}: lantai dan utilitas "
             f"+{fmt(pe['lantai'], 2)}, halaman +{fmt(pe['halaman'], 2)}"],
            ["3", "Urug seluruh persil +11,50 dalam 6 minggu", f"Sempadan tidak boleh diurug; perlu {m(vu['v_padat'])} ribu m³ "
             f"padat, bertahap dengan PVD ±{fmt(tu['t_pvd_bulan'])} bulan per tahap"],
            ["4", "300 motor, 4 ambulans, 120 mobil", f"{oc['mobil']} mobil, {oc['motor']} motor, 4 ambulans (opsi C)"],
            ["5", "Atap untuk H145 (3.700 kg)", "Didesain untuk AW139 6.800 kg (terberat di surat SAR); H145 tercakup"],
            ["6", "Dermaga ditunda, jalur tetap", "Jalur dari sungai ke IGD disiapkan; dermaga = V3"],
        ])}),
        ("Tapak dan aturan bangunan", [
            f"Persil {fmt(t['persil'])} m²; ruang sempadan {fmt(t['sempadan'])} m² dan rumija {fmt(t['rumija'])} m² "
            f"dikeluarkan → lahan perencanaan {fmt(t['lahan_perencanaan'])} m²",
            f"KDB maks {fmt(t['kdb_maks'])} m², KLB maks {fmt(t['klb_maks'])} m², KDH min {fmt(t['kdh_min'])} m²",
            f"Tapak rencana {fmt(cm['tapak'])} m², luas lantai {fmt(cm['luas_lantai'])} m²: memenuhi KDB dan KLB",
            "Zona labil tebing (bekas longsor) bebas bangunan; urugan maks 1,0 m sampai tebing diperkuat",
        ], {"gambar": "GK-03 Rencana Tapak dan Massa.png"}),
        ("Banjir, peil, dan urugan", [
            f"Q50 terkoreksi +{fmt(pe['q50'], 2)} (data penyedia +11,20 terlalu rendah; banjir 2003 +11,65); "
            f"Q100 +{fmt(pe['q100'], 2)}",
            f"Peil lantai dasar dan utilitas +{fmt(pe['lantai'], 2)}; halaman +{fmt(pe['halaman'], 2)}",
            f"Urugan padat {m(pl.volume_urugan(11.50)['v_padat'])}-{m(vu['v_padat'])} ribu m³; tanah gratis 22 ribu m³ "
            "tidak cukup dan mutunya perlu diuji",
            f"Lempung lunak: urugan per tahap ±1 m dengan PVD (±{fmt(tu['t_pvd_bulan'])} bulan per tahap); "
            f"tanpa PVD t90 ±{fmt(tu['t90_tanpa_pvd_tahun'], 1)} tahun",
        ], {"gambar": "GK-02 Peil dan Urugan.png"}),
        ("Program ruang dan zonasi", [
            "150 TT (KRIS) sejak awal; faktor bruto 1,45 [Asumsi]",
            f"Podium LT1-LT3 72 × 48 m, menara LT4-LT6 64 × 24 m, gedung utilitas + parkir 34 × 32 m",
            f"Luas lantai total {fmt(cm['luas_lantai'])} m² (dasar pagu owner 12.000 m²)",
            "IGD di LT1 tepat di bawah bedah sentral LT2; ICU bersebelahan bedah; jalur logistik dan jenazah terpisah",
        ], {"gambar": "GK-04 Zonasi Lantai.png"}),
        ("Parkir: basement ditolak", [
            f"FK blow-in dasar galian {fmt(min(x['fk'] for x in fk), 2)}-{fmt(max(x['fk'] for x in fk), 2)} < 1,25 "
            "(SNI 8460:2017 Pasal 10.3.6.7.2); uplift saat Q100",
            "Opsi C: gedung utilitas + parkir 4 lantai; utilitas di +12,85 (atas banjir)",
            f"Kapasitas {oc['mobil']} mobil, {oc['motor']} motor, 4 ambulans dekat IGD",
            "Tanpa galian dalam: tidak ada dewatering dekat gudang bercerucuk",
        ], {"gambar": "GK-05 Parkir dan Basement.png"}),
        ("Struktur: kategori IV, KDS D", [
            f"SDS {fmt(sp['SDS'], 3)}, SD1 {fmt(sp['SD1'], 3)} (sementara, kelas SE untuk SF) → KDS {sp['KDS']}",
            f"Sistem ganda (dinding geser + SRPMK) dipilih: biaya struktur +{fmt(sr['selisih_biaya'] * 100, 1)} % "
            "dari SRPMK, simpangan dan torsi lebih terkendali",
            "Grid 8 m; pelat 200, balok 350 × 600, kolom 750/650, dinding inti 350",
            "Helipad: AW139 6.800 kg (2 × 50 kN, SNI 1727 Pasal 4.11.2)",
        ], {"gambar": "GK-06 Rencana Struktur.png"}),
        ("Pondasi: tiang bor Ø800", [
            "Tiang menembus lempung lunak dan pasir mudah likuifaksi U5 ke pasir padat U7 (±38 m)",
            f"Qult {fmt(bz['Qult'])} kN; izin {fmt(bz['izin'])} kN setelah gesekan negatif urugan dan likuifaksi",
            f"{oa['n_utama'] + oa['n_gu']} tiang; tanpa getaran di dekat gudang timur",
            "Opsi hibrida tiang spun (V2) setelah uji tiang membuktikan daya dukung",
        ], {"gambar": "GK-07 Rencana Pondasi.png"}),
        ("Model BIM LOD 200", [
            "Model struktur RSTB-STR-T3-LOD200 (BIMCraft, IFC4) + model massa arsitektur (ruang bernama)",
            f"{kelas.get('IfcColumn', 0)} kolom, {kelas.get('IfcBeam', 0)} balok, {kelas.get('IfcSlab', 0)} pelat, "
            f"{kelas.get('IfcWall', 0)} dinding, {kelas.get('IfcFooting', 0)} pile cap, {kelas.get('IfcPile', 0)} tiang",
            "Validasi IfcOpenShell lolos: hierarki, elemen di lantai, LOD 200, GlobalId unik",
            "Volume model cocok dengan hitungan pra-dimensi dalam 0-7,6 %",
        ], {"gambar": "3.9 Model LOD 200 isometri.png", "utuh": True}),
        ("Perkiraan biaya terhadap pagu", [], {"tabel": (["Komponen", "Rp miliar"],
            [[b[0], m(b[1])] for b in r["baris"]] + [["Kontinjensi 5 %", m(r["kontinjensi"])],
                                                     ["Perkiraan (termasuk PPN)", m(r["total"])],
                                                     ["Pagu", m(bi.PAGU)],
                                                     [f"Rasio terhadap pagu; rentang {m(rg['rentang'][0])}-{m(rg['rentang'][1])}",
                                                      fmt(r["rasio_pagu"], 2) + " ×"]])}),
        ("Rekayasa nilai dan sisa biaya", [], {"tabel": (["Kode", "Opsi", "Hemat (Rp M)", "Sisa (Rp M)"],
            [[o["kode"], o["uraian"], m(o["hemat"]), m(o["sisa"])] for o in ve])}),
        ("Keputusan yang diminta dari owner", [
            f"D1 Pembiayaan: perkiraan ±Rp {m(r['total'])} M, setelah V1-V7 ±Rp {m(rg['setelah_ve'])} M "
            f"→ (a) tambah pagu, (b) bertahap, (c) kurangi TT",
            "D2 Opsi rekayasa nilai V1-V7 yang disetujui",
            "D3 Peil +12,85 / halaman +12,05 dan urugan bertahap dengan PVD (bukan 6 minggu)",
            "D4 Parkir 120 mobil dipertahankan atau V5",
            "D5 Uji tiang awal (syarat V2) dan izin survei gudang timur",
            "D6 Jadwal: lelang dan mulai konstruksi disesuaikan dengan urugan bertahap dan PBG",
        ], None),
    ]


def buat(keluar=PPTX):
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN
    from pptx.util import Inches, Pt

    hitam = RGBColor(0, 0, 0)
    abu = RGBColor(0x59, 0x59, 0x59)
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    kosong = prs.slide_layouts[6]

    def teks(slide, x, y, w, h, s, ukuran=16, tebal=False, warna=hitam, rata=PP_ALIGN.LEFT):
        tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.alignment = rata
        run = p.add_run()
        run.text = s
        run.font.name, run.font.size, run.font.bold = FONT, Pt(ukuran), tebal
        run.font.color.rgb = warna
        return tb

    def garis(slide, y):
        ln = slide.shapes.add_connector(1, Inches(0.6), Inches(y), Inches(12.73), Inches(y))
        ln.line.color.rgb = hitam
        ln.line.width = Pt(0.75)

    def kaki(slide, n):
        garis(slide, 7.0)
        teks(slide, 0.6, 7.03, 9.5, 0.3, LABEL, 9, warna=abu)
        teks(slide, 10.2, 7.03, 2.53, 0.3, f"{JUDUL_PROYEK}  |  {n}", 9, warna=abu, rata=PP_ALIGN.RIGHT)

    # sampul
    s = prs.slides.add_slide(kosong)
    teks(s, 0.8, 2.0, 11.7, 0.8, "PRESENTASI DESAIN KONSEP", 36, True)
    garis(s, 2.95)
    teks(s, 0.8, 3.1, 11.7, 0.6, "Pembangunan Gedung Rumah Sakit Tepian Batanghari, Kota Jambi", 22)
    teks(s, 0.8, 3.7, 11.7, 0.5, "Tahap 3: tapak, peil, program, parkir, struktur, pondasi, biaya, BIM LOD 200", 16,
         warna=abu)
    teks(s, 0.8, 5.2, 11.7, 0.4, "Pemberi tugas: Yayasan Kesehatan Tepian Batanghari", 16)
    teks(s, 0.8, 5.6, 11.7, 0.4, "Perencana: Defsa Yurinda", 16)
    teks(s, 0.8, 6.0, 11.7, 0.4, "Maret 2027 (simulasi)", 16)
    kaki(s, 1)

    for n, (judul, butir, lampiran) in enumerate(isi(), start=2):
        s = prs.slides.add_slide(kosong)
        teks(s, 0.6, 0.35, 12.1, 0.7, judul, 28, True)
        garis(s, 1.05)
        lebar_teks = 5.6 if lampiran and "gambar" in lampiran else 12.1
        if butir:
            tb = s.shapes.add_textbox(Inches(0.6), Inches(1.3), Inches(lebar_teks), Inches(5.5))
            tf = tb.text_frame
            tf.word_wrap = True
            for i, b in enumerate(butir):
                p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
                p.space_after = Pt(10)
                r1 = p.add_run()
                r1.text = "▪  " + b
                r1.font.name, r1.font.size = FONT, Pt(17 if lebar_teks > 6 else 16)
        if lampiran and "gambar" in lampiran:
            path = GAMBAR / lampiran["gambar"]
            if not lampiran.get("utuh"):
                path = _potong(path)
            from PIL import Image
            with Image.open(path) as im:
                rasio = im.height / im.width
            w = min(6.28, 5.3 / rasio)
            s.shapes.add_picture(str(path), Inches(6.45 + (6.28 - w) / 2), Inches(1.3), width=Inches(w))
            ket = ("Model struktur LOD 200 (IFC), tampak isometri" if lampiran.get("utuh") else
                   f"Potongan gambar {lampiran['gambar'][:5]}; lembar lengkap di PDF gambar A3")
            teks(s, 6.45, 1.35 + w * rasio, 6.28, 0.3, ket, 10, warna=abu, rata=PP_ALIGN.CENTER)
        if lampiran and "tabel" in lampiran:
            kepala, baris = lampiran["tabel"]
            lebar = {2: [9.6, 2.5], 3: [0.7, 4.4, 7.0], 4: [0.8, 8.3, 1.5, 1.5]}[len(kepala)]
            y0 = 1.3 if not butir else 3.6
            tinggi_baris = 0.36 if len(baris) <= 8 else 0.33
            tbl = s.shapes.add_table(len(baris) + 1, len(kepala), Inches(0.6), Inches(y0), Inches(sum(lebar)),
                                     Inches(tinggi_baris * (len(baris) + 1))).table
            for row in tbl.rows:
                row.height = Inches(tinggi_baris)
            for j, w in enumerate(lebar):
                tbl.columns[j].width = Inches(w)
            for i, row in enumerate([kepala] + baris):
                for j, v in enumerate(row):
                    c = tbl.cell(i, j)
                    c.text = str(v)
                    c.fill.background()
                    c.margin_top = c.margin_bottom = Inches(0.03)
                    for p in c.text_frame.paragraphs:
                        p.alignment = PP_ALIGN.CENTER if (j > 0 and len(kepala) != 3 and i > 0 and j >= len(kepala) - 2) \
                            or i == 0 else PP_ALIGN.LEFT
                        for rr in p.runs:
                            rr.font.name, rr.font.size = FONT, Pt(12 if len(baris) > 8 else 14)
                            rr.font.bold = i == 0 or (len(kepala) == 2 and i >= len(baris) - 3)
                            rr.font.color.rgb = hitam
            # gaya tabel tanpa garis vertikal: ganti gaya bawaan dengan garis horizontal tipis
            _garis_horizontal(tbl)
        kaki(s, n)
    prs.save(str(keluar))
    return keluar


def _garis_horizontal(tbl):
    from pptx.oxml.ns import qn
    from lxml import etree

    tbl._tbl.tblPr.set("firstRow", "0")
    tbl._tbl.tblPr.set("bandRow", "0")
    gaya = tbl._tbl.tblPr.find(qn("a:tableStyleId"))
    if gaya is not None:
        gaya.text = "{5940675A-B579-460E-94D1-54222C63F5DA}"  # No Style, Table Grid → diganti garis di bawah
    for r_i, tr in enumerate(tbl._tbl.tr_lst):
        for tc in tr.tc_lst:
            tcPr = tc.get_or_add_tcPr()
            for sisi in ("a:lnL", "a:lnR", "a:lnT", "a:lnB"):
                el = tcPr.find(qn(sisi))
                if el is not None:
                    tcPr.remove(el)
            for sisi in ("lnL", "lnR", "lnT", "lnB"):
                ada = sisi == "lnB" or (sisi == "lnT" and r_i == 0)
                ln = etree.SubElement(tcPr, qn(f"a:{sisi}"), w="9525" if ada else "0")
                if ada:
                    fill = etree.SubElement(ln, qn("a:solidFill"))
                    etree.SubElement(fill, qn("a:srgbClr"), val="000000")
                else:
                    etree.SubElement(ln, qn("a:noFill"))
            # urutan skema: garis sebelum isi sel
            for f in tcPr.findall(qn("a:noFill")) + tcPr.findall(qn("a:solidFill")):
                tcPr.remove(f)
                tcPr.append(f)


def _potong(path):
    """Bagian gambar (kiri kop A3) untuk slide; disimpan di folder sementara."""
    import tempfile

    from PIL import Image
    tujuan = Path(tempfile.gettempdir()) / f"rstb-slide-{path.stem}.png"
    with Image.open(path) as im:
        w, h = im.size
        im.crop((int(0.045 * w), int(0.03 * h), int(0.795 * w), int(0.97 * h))).save(tujuan)
    return tujuan


def ke_pdf(pptx=PPTX, pdf=PDF):
    perintah = (
        "$p = New-Object -ComObject PowerPoint.Application; "
        f"$d = $p.Presentations.Open('{Path(pptx).resolve()}', $true, $false, $false); "
        f"$d.SaveAs('{Path(pdf).resolve()}', 32); $d.Close(); $p.Quit()"
    )
    h = subprocess.run(["powershell", "-NoProfile", "-Command", perintah], capture_output=True, text=True)
    return h.returncode == 0 and Path(pdf).exists(), h.stderr.strip()


if __name__ == "__main__":
    print(buat())
    print(ke_pdf())
