"""Bangun Laporan Audit Akhir (.docx + PDF) dari `10 Laporan/Audit Akhir.md` (satu sumber isi).

Markdown yang dipakai: `# judul` (sampul), `## Ringkasan Eksekutif`, `## I. Judul` (bab), `## Lampiran A. Judul`,
`### 1.1 Judul` (subbab), paragraf, daftar `- ` / `1. `, `**Tabel: judul**` + tabel pipa + `Sumber: ...`,
`![judul](path relatif)`. Bab dengan tabel >= 5 kolom atau gambar dibuat lanskap.
Jalankan:  .venv\\Scripts\\python.exe skrip\\audit_akhir.py
"""
import re
from pathlib import Path

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

from format_dokumen import Laporan, perbarui_word

AKAR = Path(__file__).resolve().parents[1]
SUMBER = AKAR / "10 Laporan" / "Audit Akhir.md"
KELUAR = SUMBER.with_suffix(".docx")
PDF = SUMBER.with_suffix(".pdf")


def bersih(t):
    return t.replace("`", "").strip()


def blok(md):
    """Pecah md menjadi daftar (jenis, isi)."""
    hasil, para, i = [], [], 0
    baris = md.splitlines()

    def tutup():
        if para:
            hasil.append(("p", " ".join(para)))
            para.clear()
    while i < len(baris):
        b = baris[i].rstrip()
        if not b:
            tutup()
        elif b.startswith("#"):
            tutup()
            hasil.append(("h" + str(len(b) - len(b.lstrip("#"))), b.lstrip("#").strip()))
        elif b.startswith("|"):
            tutup()
            rows = []
            while i < len(baris) and baris[i].startswith("|"):
                sel = [bersih(s) for s in baris[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r"-+", s) for s in sel):
                    rows.append(sel)
                i += 1
            hasil.append(("t", rows))
            continue
        elif re.match(r"!\[", b):
            tutup()
            m = re.match(r"!\[(.+?)\]\((.+?)\)", b)
            hasil.append(("g", (m.group(1), m.group(2))))
        elif re.match(r"(- |\d+\. )", b):
            tutup()
            jenis = "huruf" if b.startswith("- ") else "angka"
            if hasil and hasil[-1][0] == "l" and hasil[-1][1][0] == jenis:
                hasil[-1][1][1].append(bersih(re.sub(r"^(- |\d+\. )", "", b)))
            else:
                hasil.append(("l", (jenis, [bersih(re.sub(r"^(- |\d+\. )", "", b))])))
        else:
            para.append(b)
        i += 1
    tutup()
    return hasil


def lebar_kolom(rows):
    n = len(rows[0])
    # kolom pendek (No, Tingkat) jangan terpotong: lebar minimum = kata terpanjang di kolom
    return [max(len(rows[0][k]) + 2, 7, max(len(w) for r in rows for w in (r[k] if k < len(r) else "").split() or [""]) + 1,
                min(60, max(len(r[k]) if k < len(r) else 0 for r in rows)) ** 0.75) for k in range(n)]


def sampul(lap, judul, status):
    d = lap.doc

    def baris(teks, ukuran=12, tebal=False, miring=False, sesudah=0):
        p = d.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(sesudah)
        r = p.add_run(teks)
        r.font.size, r.bold, r.italic = Pt(ukuran), tebal, miring
    for _ in range(4):
        d.add_paragraph()
    baris("LAPORAN AUDIT AKHIR", 16, True, sesudah=36)
    baris("STUDI KASUS PERENCANAAN", 12, True)
    baris("RUMAH SAKIT TEPIAN BATANGHARI", 14, True)
    baris("Konsistensi Angka, Cek Silang, Sumber, Skrip, dan Format Dokumen", 12, sesudah=48)
    baris("Disusun oleh:")
    baris("Defsa Yurinda", tebal=True)
    baris("(Studi kasus portofolio perencanaan)", sesudah=60)
    baris("JAMBI", tebal=True)
    baris("NOVEMBER 2026", tebal=True, sesudah=36)
    baris(bersih(status).replace("**", ""), 10, miring=True)
    lap.sampul_selesai()


def bangun():
    bl = blok(SUMBER.read_text(encoding="utf-8"))
    judul = next(t for j, t in bl if j == "h1")
    pertama_h2 = next(k for k, (j, _) in enumerate(bl) if j == "h2")
    status = " ".join(t for j, t in bl[:pertama_h2] if j == "p")
    lap = Laporan()
    sampul(lap, judul, status)
    lap.bagian_awal()
    sudah_daftar = False
    k, tabel_judul = pertama_h2, None
    while k < len(bl):
        j, isi = bl[k]
        if j == "h2":
            # cari isi bagian sampai h2 berikutnya, untuk menentukan lanskap
            akhir = next((m for m in range(k + 1, len(bl)) if bl[m][0] == "h2"), len(bl))
            lanskap = any((jj == "t" and len(ii[0]) >= 5) or jj == "g" for jj, ii in bl[k + 1:akhir])
            m_bab = re.match(r"([IVX]+)\. (.+)", isi)
            m_lamp = re.match(r"Lampiran ([A-Z])\. (.+)", isi)
            if m_bab:
                if not sudah_daftar:
                    lap.daftar_isi()
                    lap.daftar_tabel()
                    lap.daftar_gambar()
                    sudah_daftar = True
                lap.bab(m_bab.group(1), m_bab.group(2), lanskap=lanskap, mulai_arab=m_bab.group(1) == "I")
            elif m_lamp:
                lap.lampiran(m_lamp.group(1), m_lamp.group(2), lanskap=lanskap)
            else:
                lap.judul_depan(isi)
        elif j == "h3":
            m = re.match(r"(\d+\.\d+) (.+)", isi)
            lap.subbab(m.group(1), m.group(2))
        elif j == "p":
            m = re.fullmatch(r"\*\*Tabel: (.+)\*\*", isi)
            if m:
                tabel_judul = m.group(1)
            else:
                lap.paragraf(bersih(isi))
        elif j == "l":
            lap.daftar(isi[1], jenis=isi[0])
        elif j == "t":
            sumber = None
            if k + 1 < len(bl) and bl[k + 1][0] == "p" and bl[k + 1][1].startswith("Sumber:"):
                sumber = bersih(bl[k + 1][1][len("Sumber:"):])
                k += 1
            kepala, baris = isi[0], isi[1:]
            rata = ["c" if max(len(r[c]) for r in isi) <= 8 else "l" for c in range(len(kepala))]
            lap.tabel(tabel_judul or "", kepala, baris, lebar_kolom(isi), rata=rata, sumber=sumber,
                      ukuran=10 if len(kepala) >= 5 else 11)
            tabel_judul = None
        elif j == "g":
            lap.gambar(SUMBER.parent / isi[1], isi[0], lebar_cm=lap.lebar)
        k += 1
    lap.simpan(KELUAR)
    return lap


def main():
    bangun()
    ok, pesan = perbarui_word(KELUAR, PDF)
    print("ditulis:", KELUAR, "| field dan PDF lewat Word" if ok else f"| Word gagal: {pesan[:200]}")


if __name__ == "__main__":
    main()
