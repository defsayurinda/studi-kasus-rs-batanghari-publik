"""Pembantu format Word dan Excel sesuai `FORMAT LAPORAN DAN EXCEL.md`.

Word  : class Laporan  (python-docx)
Excel : class Lembar   (openpyxl)
Akhir : perbarui_word(path) memperbarui daftar isi/tabel/gambar lewat Microsoft Word (bila terpasang).
"""
from __future__ import annotations

import math
import re
import subprocess
from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_TAB_ALIGNMENT
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

FONT = "Times New Roman"
TEKS_LEBAR_POTRET = 21.0 - 4.0 - 3.0      # cm
TEKS_LEBAR_LANSKAP = 29.7 - 4.0 - 3.0     # cm

# posisi butir bertingkat: level -> (posisi penanda, posisi teks) dalam cm
BUTIR = {4: (0.0, 0.75), 5: (0.75, 1.25), 6: (1.25, 1.75), 7: (1.75, 2.25)}


# =====================================================================  WORD
def _rfonts(el):
    rpr = el.get_or_add_rPr()
    rf = rpr.get_or_add_rFonts()
    for a in ["w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"]:
        rf.attrib.pop(qn(a), None)
    for a in ["w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"]:
        rf.set(qn(a), FONT)


def _gaya(doc, nama, ukuran=12, tebal=False, rata=WD_ALIGN_PARAGRAPH.JUSTIFY, spasi=1.5, sebelum=0, sesudah=0,
          dasar="Normal", jenis=WD_STYLE_TYPE.PARAGRAPH, outline=None):
    try:
        st = doc.styles[nama]
    except KeyError:
        st = doc.styles.add_style(nama, jenis)
        st.base_style = doc.styles[dasar]
    st.font.name = FONT
    _rfonts(st.element)
    st.font.size = Pt(ukuran)
    st.font.bold = tebal
    st.font.italic = False
    st.font.color.rgb = RGBColor(0, 0, 0)
    pf = st.paragraph_format
    pf.alignment = rata
    pf.line_spacing = spasi
    pf.space_before = Pt(sebelum)
    pf.space_after = Pt(sesudah)
    pf.left_indent = Cm(0)
    pf.first_line_indent = Cm(0)
    if outline is not None:
        ppr = st.element.get_or_add_pPr()
        for o in ppr.findall(qn("w:outlineLvl")):
            ppr.remove(o)
        el = OxmlElement("w:outlineLvl")
        el.set(qn("w:val"), str(outline))
        ppr.append(el)
    return st


def _field(par, kode, teks_awal=""):
    """Sisipkan field Word (PAGE, TOC, ...)."""
    def fc(jenis):
        el = OxmlElement("w:fldChar")
        el.set(qn("w:fldCharType"), jenis)
        return el
    r = par.add_run()
    r._r.append(fc("begin"))
    r = par.add_run()
    it = OxmlElement("w:instrText")
    it.set(qn("xml:space"), "preserve")
    it.text = f" {kode} "
    r._r.append(it)
    par.add_run()._r.append(fc("separate"))
    par.add_run(teks_awal)
    par.add_run()._r.append(fc("end"))


def _isi_markup(par, teks, ukuran=None, tebal=False, miring=False):
    """**tebal** dan *miring* sederhana."""
    for bagian in re.split(r"(\*\*.+?\*\*|\*[^*]+?\*)", str(teks)):
        if not bagian:
            continue
        b, i, t = tebal, miring, bagian
        if t.startswith("**") and t.endswith("**"):
            b, t = True, t[2:-2]
        elif t.startswith("*") and t.endswith("*") and len(t) > 1:
            i, t = True, t[1:-1]
        r = par.add_run(t)
        r.bold = b or None
        r.italic = i or None
        if ukuran:
            r.font.size = Pt(ukuran)


class Laporan:
    """Penyusun laporan bergaya panduan UNJA."""

    def __init__(self):
        self.doc = Document()
        d = self.doc
        sec = d.sections[0]
        sec.page_width, sec.page_height = Cm(21), Cm(29.7)
        self._margin(sec)
        _gaya(d, "Normal")
        _gaya(d, "Heading 1", tebal=True, rata=WD_ALIGN_PARAGRAPH.CENTER, sesudah=24, outline=0)
        _gaya(d, "Heading 2", tebal=True, rata=WD_ALIGN_PARAGRAPH.LEFT, sebelum=12, outline=1)
        _gaya(d, "Heading 3", tebal=True, rata=WD_ALIGN_PARAGRAPH.LEFT, sebelum=6, outline=2)
        for h in ["Heading 1", "Heading 2", "Heading 3"]:
            d.styles[h].paragraph_format.keep_with_next = True
        _gaya(d, "Keterangan Tabel", ukuran=11, rata=WD_ALIGN_PARAGRAPH.LEFT, spasi=1.0, sebelum=6)
        _gaya(d, "Keterangan Gambar", ukuran=11, rata=WD_ALIGN_PARAGRAPH.CENTER, spasi=1.0, sesudah=6)
        _gaya(d, "Isi Tabel", ukuran=11, rata=WD_ALIGN_PARAGRAPH.LEFT, spasi=1.0)
        _gaya(d, "Sumber", ukuran=10, rata=WD_ALIGN_PARAGRAPH.LEFT, spasi=1.0, sesudah=6)
        for nama in ["TOC 1", "TOC 2", "TOC 3", "Table of Figures"]:
            _gaya(d, nama, rata=WD_ALIGN_PARAGRAPH.LEFT)
        d.styles["TOC 2"].paragraph_format.left_indent = Cm(0.75)
        d.styles["TOC 3"].paragraph_format.left_indent = Cm(1.5)
        self._awal_bagian = True
        self.lebar = TEKS_LEBAR_POTRET
        self._baru_judul_bab = False
        self.no_tabel = 0
        self.no_gambar = 0
        self.bab_aktif = ""

    # ---------- halaman dan bagian ----------
    @staticmethod
    def _margin(sec):
        sec.left_margin, sec.top_margin, sec.right_margin, sec.bottom_margin = Cm(4), Cm(3), Cm(3), Cm(3)
        sec.header_distance, sec.footer_distance = Cm(1.25), Cm(1.5)

    @staticmethod
    def _nomor_halaman(sec, fmt=None, mulai=None):
        sectPr = sec._sectPr
        for o in sectPr.findall(qn("w:pgNumType")):
            sectPr.remove(o)
        el = OxmlElement("w:pgNumType")
        if fmt:
            el.set(qn("w:fmt"), fmt)
        if mulai is not None:
            el.set(qn("w:start"), str(mulai))
        sectPr.append(el)

    @staticmethod
    def _isi_footer(footer, rata):
        footer.is_linked_to_previous = False
        par = footer.paragraphs[0]
        for r in list(par.runs):
            r._r.getparent().remove(r._r)
        par.alignment = rata
        _field(par, "PAGE", "1")

    def bagian_awal(self):
        """Halaman romawi (ringkasan, daftar isi). Dipanggil sekali setelah sampul."""
        sec = self.doc.add_section(WD_SECTION.NEW_PAGE)
        self._margin(sec)
        self._nomor_halaman(sec, fmt="lowerRoman", mulai=1)
        self._isi_footer(sec.footer, WD_ALIGN_PARAGRAPH.CENTER)
        self._awal_bagian = True

    def sampul_selesai(self):
        """Sampul tanpa nomor halaman: footer bagian pertama dikosongkan."""
        self.doc.sections[0].footer.is_linked_to_previous = False

    def judul_depan(self, teks):
        """Judul bagian awal tanpa nomor (Ringkasan, Daftar Isi, ...), halaman baru."""
        par = self.doc.add_paragraph(teks.upper(), style="Heading 1")
        par.paragraph_format.page_break_before = not self._awal_bagian
        self._awal_bagian = False
        self._baru_judul_bab = True
        return par

    def bab(self, romawi, judul, lanskap=False, mulai_arab=False):
        """BAB baru: bagian baru, halaman pertama nomor tengah, selanjutnya kanan."""
        sec = self.doc.add_section(WD_SECTION.NEW_PAGE)
        self._margin(sec)
        if lanskap:
            sec.orientation = WD_ORIENT.LANDSCAPE
            sec.page_width, sec.page_height = Cm(29.7), Cm(21)
        else:
            sec.orientation = WD_ORIENT.PORTRAIT
            sec.page_width, sec.page_height = Cm(21), Cm(29.7)
        sec.different_first_page_header_footer = True
        if mulai_arab:
            self._nomor_halaman(sec, fmt="decimal", mulai=1)
        else:
            self._nomor_halaman(sec, fmt="decimal")
        self._isi_footer(sec.first_page_footer, WD_ALIGN_PARAGRAPH.CENTER)
        self._isi_footer(sec.footer, WD_ALIGN_PARAGRAPH.RIGHT)
        par = self.doc.add_paragraph(style="Heading 1")
        self._awal_bagian = False
        par.add_run(f"BAB {romawi}" if romawi else "")
        if romawi:
            par.add_run().add_break(WD_BREAK.LINE)
        par.add_run(judul.upper())
        self._baru_judul_bab = True
        self.bab_aktif = str(self._arab(romawi)) if romawi else "A"
        self.no_tabel = self.no_gambar = 0
        self.lebar = TEKS_LEBAR_LANSKAP if lanskap else TEKS_LEBAR_POTRET

    def lampiran(self, huruf, judul, lanskap=False):
        self.bab("", f"LAMPIRAN {huruf}. {judul}", lanskap=lanskap)
        self.bab_aktif = huruf

    @staticmethod
    def _arab(romawi):
        nilai = {"I": 1, "V": 5, "X": 10}
        total = 0
        for i, c in enumerate(romawi):
            v = nilai[c]
            total += -v if i + 1 < len(romawi) and nilai[romawi[i + 1]] > v else v
        return total


    # ---------- judul subbab ----------
    def _judul_bernomor(self, gaya, nomor, teks):
        par = self.doc.add_paragraph(style=gaya)
        pf = par.paragraph_format
        pf.left_indent = Cm(1.25)
        pf.first_line_indent = Cm(-1.25)
        pf.tab_stops.add_tab_stop(Cm(1.25))
        if self._baru_judul_bab:
            pf.space_before = Pt(0)
            self._baru_judul_bab = False
        _isi_markup(par, f"{nomor}\t{teks}")
        return par

    def subbab(self, nomor, teks):
        return self._judul_bernomor("Heading 2", nomor, teks)

    def anak_subbab(self, nomor, teks):
        return self._judul_bernomor("Heading 3", nomor, teks)

    # ---------- paragraf dan butir ----------
    def paragraf(self, teks, inden=True):
        par = self.doc.add_paragraph()
        if inden:
            par.paragraph_format.first_line_indent = Cm(1.25)
        _isi_markup(par, teks)
        self._baru_judul_bab = False
        return par

    def butir(self, penanda, teks, level=4):
        """Butir bernomor/berhuruf: level 4 '1.', 5 'a.', 6 '1)', 7 'a)'."""
        pos_penanda, pos_teks = BUTIR[level]
        par = self.doc.add_paragraph()
        pf = par.paragraph_format
        pf.left_indent = Cm(pos_teks)
        pf.first_line_indent = Cm(pos_penanda - pos_teks)
        pf.tab_stops.add_tab_stop(Cm(pos_teks))
        _isi_markup(par, f"{penanda}\t{teks}")
        self._baru_judul_bab = False
        return par

    def daftar(self, butir_butir, level=4, jenis="angka"):
        for i, t in enumerate(butir_butir, start=1):
            if jenis == "angka":
                penanda = f"{i}." if level in (4,) else f"{i})"
            else:
                huruf = chr(96 + i)
                penanda = f"{huruf}." if level in (4, 5) else f"{huruf})"
            self.butir(penanda, t, level=level)

    def paragraf_butir(self, teks, level=4):
        """Paragraf penjelasan di bawah butir: sejajar teks butir, tanpa inden baris pertama."""
        par = self.doc.add_paragraph()
        par.paragraph_format.left_indent = Cm(BUTIR[level][1])
        _isi_markup(par, teks)
        return par

    # ---------- tabel ----------
    def keterangan_tabel(self, judul, kiri_cm=0.0):
        self.no_tabel += 1
        nomor = f"{self.bab_aktif}.{self.no_tabel}"
        par = self.doc.add_paragraph(style="Keterangan Tabel")
        par.paragraph_format.keep_with_next = True
        par.paragraph_format.left_indent = Cm(kiri_cm)
        r = par.add_run(f"Tabel {nomor}")
        r.bold = True
        _isi_markup(par, f" {judul}")
        return nomor

    def tabel(self, judul, kepala, baris, lebar_cm, rata=None, sumber=None, ukuran=11, warna=None, kiri_cm=0.0):
        """Tabel tanpa garis vertikal. rata: daftar 'l'/'c'/'r' per kolom. warna: {kolom: {nilai: hex}}."""
        nomor = self.keterangan_tabel(judul, kiri_cm)
        total = sum(lebar_cm)
        skala = (self.lebar - kiri_cm) / total if total > self.lebar - kiri_cm else 1.0
        lebar = [w * skala for w in lebar_cm]
        rata = rata or ["l"] * len(kepala)
        t = self.doc.add_table(rows=1, cols=len(kepala))
        t.alignment = WD_TABLE_ALIGNMENT.LEFT if kiri_cm else WD_TABLE_ALIGNMENT.CENTER
        t.autofit = False
        tblPr = t._tbl.tblPr
        for tag, nilai in [("w:tblLayout", {"w:type": "fixed"})]:
            el = OxmlElement(tag)
            for k, v in nilai.items():
                el.set(qn(k), v)
            tblPr.append(el)
        if kiri_cm:
            ind = OxmlElement("w:tblInd")
            ind.set(qn("w:w"), str(int(kiri_cm / 2.54 * 1440)))
            ind.set(qn("w:type"), "dxa")
            tblPr.append(ind)
        borders = OxmlElement("w:tblBorders")
        for sisi, ada in [("top", True), ("left", False), ("bottom", True), ("right", False),
                          ("insideH", True), ("insideV", False)]:
            el = OxmlElement(f"w:{sisi}")
            el.set(qn("w:val"), "single" if ada else "nil")
            if ada:
                el.set(qn("w:sz"), "4")
                el.set(qn("w:space"), "0")
                el.set(qn("w:color"), "000000")
            borders.append(el)
        tblPr.append(borders)
        mar = OxmlElement("w:tblCellMar")
        for sisi, w in [("left", 80), ("right", 80), ("top", 20), ("bottom", 20)]:
            el = OxmlElement(f"w:{sisi}")
            el.set(qn("w:w"), str(w))
            el.set(qn("w:type"), "dxa")
            mar.append(el)
        tblPr.append(mar)
        # grid
        grid = t._tbl.tblGrid
        for gc, w in zip(grid.findall(qn("w:gridCol")), lebar):
            gc.set(qn("w:w"), str(int(w / 2.54 * 1440)))

        def isi_sel(sel, teks, tebal=False, ral="l", fill=None):
            sel.text = ""
            par = sel.paragraphs[0]
            par.style = self.doc.styles["Isi Tabel"]
            par.alignment = {"l": WD_ALIGN_PARAGRAPH.LEFT, "c": WD_ALIGN_PARAGRAPH.CENTER,
                             "r": WD_ALIGN_PARAGRAPH.RIGHT, "j": WD_ALIGN_PARAGRAPH.JUSTIFY}[ral]
            _isi_markup(par, teks, ukuran=ukuran, tebal=tebal)
            if fill:
                shd = OxmlElement("w:shd")
                shd.set(qn("w:val"), "clear")
                shd.set(qn("w:color"), "auto")
                shd.set(qn("w:fill"), fill)
                sel._tc.get_or_add_tcPr().append(shd)

        for i, k in enumerate(kepala):
            isi_sel(t.rows[0].cells[i], k, tebal=True, ral="c")
        trPr = t.rows[0]._tr.get_or_add_trPr()
        for tag in ["w:tblHeader", "w:cantSplit"]:
            trPr.append(OxmlElement(tag))
        for r in baris:
            cells = t.add_row().cells
            for i, v in enumerate(r):
                teks = angka_id(v)
                fill = (warna or {}).get(i, {}).get(str(v))
                isi_sel(cells[i], teks, ral=rata[i], fill=fill)
        for row in t.rows[1:]:
            row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
        # tabel pendek tidak boleh terpisah dari keterangannya; tabel panjang cukup kepala ikut baris pertama
        tahan = t.rows[:-1] if len(t.rows) <= 15 else t.rows[:2]
        for row in tahan:
            for sel in row.cells:
                for par in sel.paragraphs:
                    par.paragraph_format.keep_with_next = True
        for row in t.rows:
            for i, w in enumerate(lebar):
                row.cells[i].width = Cm(w)
        if sumber:
            par = self.doc.add_paragraph(style="Sumber")
            par.paragraph_format.left_indent = Cm(kiri_cm)
            r = par.add_run(f"(Sumber: {sumber})")
            r.italic = True
        else:
            self.doc.add_paragraph(style="Sumber")
        return nomor

    # ---------- gambar ----------
    def gambar(self, path, judul, lebar_cm=14.0, sumber=None):
        par = self.doc.add_paragraph()
        par.alignment = WD_ALIGN_PARAGRAPH.CENTER
        par.paragraph_format.line_spacing = 1.0
        par.paragraph_format.keep_with_next = True
        par.add_run().add_picture(str(path), width=Cm(min(lebar_cm, self.lebar)))
        self.no_gambar += 1
        nomor = f"{self.bab_aktif}.{self.no_gambar}"
        cap = self.doc.add_paragraph(style="Keterangan Gambar")
        r = cap.add_run(f"Gambar {nomor}")
        r.bold = True
        _isi_markup(cap, f" {judul}")
        if sumber:
            s = self.doc.add_paragraph(style="Sumber")
            s.alignment = WD_ALIGN_PARAGRAPH.CENTER
            s.add_run(f"(Sumber: {sumber})").italic = True
        return nomor

    # ---------- daftar ----------
    def daftar_isi(self):
        self.judul_depan("Daftar Isi")
        _field(self.doc.add_paragraph(), 'TOC \\o "1-3" \\h \\z \\u', "Perbarui field untuk menampilkan daftar isi.")

    def daftar_tabel(self):
        self.judul_depan("Daftar Tabel")
        _field(self.doc.add_paragraph(), 'TOC \\h \\z \\t "Keterangan Tabel;1"', "Perbarui field untuk menampilkan daftar tabel.")

    def daftar_gambar(self):
        self.judul_depan("Daftar Gambar")
        _field(self.doc.add_paragraph(), 'TOC \\h \\z \\t "Keterangan Gambar;1"', "Perbarui field untuk menampilkan daftar gambar.")

    def simpan(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.doc.save(path)


def angka_id(v):
    """Angka ke teks Indonesia: koma desimal, titik ribuan."""
    if isinstance(v, bool) or v is None:
        return "" if v is None else str(v)
    if isinstance(v, int):
        return f"{v:,}".replace(",", ".")
    if isinstance(v, float):
        s = f"{v:,.3f}".rstrip("0").rstrip(".") if abs(v) < 1e6 else f"{v:,.0f}"
        return s.replace(",", "#").replace(".", ",").replace("#", ".")
    return str(v)


def perbarui_word(path, pdf=None):
    """Perbarui semua field (daftar isi/tabel/gambar, nomor halaman) lewat Word; opsional ekspor PDF."""
    path = str(Path(path).resolve())
    perintah = (
        "$w = New-Object -ComObject Word.Application; $w.Visible = $false; "
        f"$d = $w.Documents.Open('{path}'); "
        "$d.Fields.Update() | Out-Null; foreach ($t in $d.TablesOfContents) { $t.Update() }; "
        "$d.Fields.Update() | Out-Null; $d.Save(); "
        + (f"$d.ExportAsFixedFormat('{Path(pdf).resolve()}', 17); " if pdf else "")
        + "$d.Close(0); $w.Quit()"
    )
    hasil = subprocess.run(["powershell", "-NoProfile", "-Command", perintah], capture_output=True, text=True)
    return hasil.returncode == 0, hasil.stderr.strip()


# =====================================================================  EXCEL
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side  # noqa: E402
from openpyxl.utils import get_column_letter  # noqa: E402

KUNING = "FFFF00"
ABU = "D9D9D9"
ISIAN = "FFF2CC"
AI = "E2EFDA"
_tipis = Side(style="thin", color="000000")
GARIS = Border(left=_tipis, right=_tipis, top=_tipis, bottom=_tipis)
KOLOM_AWAL = 3  # kolom C


def font_xl(ukuran=12, tebal=False, miring=False):
    return Font(name=FONT, size=ukuran, bold=tebal, italic=miring)


def set_font_bawaan(wb):
    """Font gaya Normal workbook menjadi Times New Roman 12."""
    try:
        normal = next(s for s in wb._named_styles if s.name == "Normal")
        normal.font = font_xl()
    except StopIteration:
        pass
    if wb._fonts:
        wb._fonts[0] = font_xl()


class Lembar:
    """Satu lembar kerja bergaya IGC: margin A-B, isi mulai C2, judul kuning, kepala abu."""

    def __init__(self, ws, nomor, judul, lebar_kolom, zoom=90):
        self.ws = ws
        self.lebar = list(lebar_kolom)
        self.n = len(self.lebar)
        ws.sheet_view.showGridLines = False
        ws.sheet_view.zoomScale = zoom
        ws.sheet_format.defaultRowHeight = 15.6
        ws.column_dimensions["A"].width = 3
        ws.column_dimensions["B"].width = 3
        for i, w in enumerate(self.lebar):
            ws.column_dimensions[get_column_letter(KOLOM_AWAL + i)].width = w
        ws.page_setup.orientation = "landscape"
        ws.page_setup.paperSize = ws.PAPERSIZE_A4
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.print_options.horizontalCentered = True
        self.baris = 2
        self._gabung_judul(f"LEMBAR {nomor} - {judul.upper()}", KUNING, rata="center")
        self.baris += 2

    # ---------- unsur ----------
    def kol(self, i):
        return get_column_letter(KOLOM_AWAL + i)

    def _gabung_judul(self, teks, fill, rata="left", ukuran=12, tebal=True, garis=True):
        ws, r = self.ws, self.baris
        ws.merge_cells(f"{self.kol(0)}{r}:{self.kol(self.n - 1)}{r}")
        c = ws[f"{self.kol(0)}{r}"]
        c.value = teks
        c.font = font_xl(ukuran, tebal)
        c.alignment = Alignment(horizontal=rata, vertical="center", wrap_text=True)
        if fill:
            c.fill = PatternFill("solid", fgColor=fill)
        if garis:
            for i in range(self.n):
                ws[f"{self.kol(i)}{r}"].border = GARIS
        self._tinggi(r, [teks], [sum(self.lebar)], ukuran)
        self.baris += 1

    def bagian(self, huruf, teks):
        self._gabung_judul(f"{huruf}.  {teks.upper()}", KUNING)

    def catatan(self, teks, fill=None):
        self._gabung_judul(teks, fill, ukuran=10, tebal=False, garis=False)
        self.ws[f"{self.kol(0)}{self.baris - 1}"].alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)

    def kosong(self, n=1):
        self.baris += n

    def tabel(self, kepala, baris, rata=None, fmt=None, fill=None, fill_kolom=None, beku=True, beku_kolom=0):
        """Tulis tabel; kembalikan (baris kepala, baris data pertama, baris data terakhir).
        rata: 'l'/'c' per kolom. fmt: format angka per kolom. fill: warna isi sel data (mis. AI/ISIAN).
        fill_kolom: {indeks kolom: warna} menimpa fill. beku: freeze panes di bawah kepala."""
        ws = self.ws
        rata = rata or ["l"] * self.n
        r0 = self.baris
        for i, k in enumerate(kepala):
            c = ws[f"{self.kol(i)}{r0}"]
            c.value = k
            c.font = font_xl(12, True)
            c.fill = PatternFill("solid", fgColor=ABU)
            c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            c.border = GARIS
        self._tinggi(r0, kepala, self.lebar[:len(kepala)], 12)
        r = r0
        for data in baris:
            r += 1
            for i in range(len(kepala)):
                v = data[i] if i < len(data) else None
                c = ws[f"{self.kol(i)}{r}"]
                c.value = v
                c.font = font_xl()
                c.border = GARIS
                c.alignment = Alignment(horizontal={"l": "left", "c": "center", "r": "right"}[rata[i]],
                                        vertical="center", wrap_text=True)
                if fmt and fmt[i]:
                    c.number_format = fmt[i]
                warna = (fill_kolom or {}).get(i, fill)
                if warna:
                    c.fill = PatternFill("solid", fgColor=warna)
            self._tinggi(r, [data[i] if i < len(data) else "" for i in range(len(kepala))], self.lebar, 12)
        if beku:
            ws.freeze_panes = f"{self.kol(beku_kolom) if beku_kolom else 'A'}{r0 + 1}"
            ws.print_title_rows = f"{r0}:{r0}"
        self.baris = r + 1
        return r0, r0 + 1, r

    # ---------- tinggi baris ----------
    def _tinggi(self, r, nilai, lebar, ukuran):
        self.ws.row_dimensions[r].height = tinggi_baris(nilai, lebar, ukuran)

    def rapikan_tinggi(self, r_awal, r_akhir):
        """Hitung ulang tinggi baris setelah isi diubah."""
        for r in range(r_awal, r_akhir + 1):
            nilai = [self.ws[f"{self.kol(i)}{r}"].value for i in range(self.n)]
            ukuran = self.ws[f"{self.kol(0)}{r}"].font.sz or 12
            self._tinggi(r, nilai, self.lebar, ukuran)


def tinggi_baris(nilai, lebar, ukuran=12):
    """Perkiraan tinggi baris (pt) agar teks terbungkus terlihat utuh."""
    per_baris = 15.6 if ukuran >= 12 else 13.2
    faktor = 1.05 if ukuran >= 12 else 1.3   # karakter per satuan lebar kolom
    maks = 1
    for v, w in zip(nilai, lebar):
        if v is None or (isinstance(v, str) and v.startswith("=")):
            continue
        teks = angka_id(v) if not isinstance(v, str) else v
        cpl = max(1, int(w * faktor) - 1)
        n = sum(max(1, math.ceil(len(bagian) / cpl)) for bagian in teks.split("\n"))
        maks = max(maks, n)
    return round(maks * per_baris + 2, 1)


def baca_tabel(ws, kepala_pertama="No"):
    """Baca tabel bergaya Lembar: cari baris kepala yang sel pertamanya = kepala_pertama (kolom C atau A)."""
    for row in ws.iter_rows():
        for c in row[:4]:
            if c.value == kepala_pertama:
                r0, c0 = c.row, c.column
                kepala = []
                col = c0
                while ws.cell(r0, col).value not in (None, ""):
                    kepala.append(ws.cell(r0, col).value)
                    col += 1
                data = []
                r = r0 + 1
                while any(ws.cell(r, c0 + j).value not in (None, "") for j in range(len(kepala))):
                    data.append(["" if ws.cell(r, c0 + j).value is None else ws.cell(r, c0 + j).value
                                 for j in range(len(kepala))])
                    r += 1
                return kepala, data
    raise ValueError(f"Kepala '{kepala_pertama}' tidak ditemukan di {ws.title}")


def hitung_ulang_excel(path):
    """Buka workbook di Microsoft Excel, hitung ulang semua rumus, simpan (nilai tersimpan untuk openpyxl data_only).
    Pelajaran evaluasi no. 4: rumus Excel dicocokkan dengan Python setelah dihitung di Excel."""
    path = str(Path(path).resolve())
    perintah = (
        "$x = New-Object -ComObject Excel.Application; $x.Visible = $false; $x.DisplayAlerts = $false; "
        f"$b = $x.Workbooks.Open('{path}'); $x.CalculateFull(); $b.Save(); $b.Close($false); $x.Quit()"
    )
    hasil = subprocess.run(["powershell", "-NoProfile", "-Command", perintah], capture_output=True, text=True)
    return hasil.returncode == 0, hasil.stderr.strip()
