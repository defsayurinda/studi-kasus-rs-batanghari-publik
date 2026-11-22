"""Tahap 2 langkah 2.7: kimia tanah dan air, tebing sungai, gudang timur.

Keluaran: '02 Olah Data Tanah/2.7 Kimia Tebing Gudang.xlsx', gambar GT-13 (tebing) dan GT-14 (gudang).
Jalankan:  .venv\\Scripts\\python.exe skrip\\tahap2_kimia_tebing_gudang.py
"""
from datetime import datetime
from pathlib import Path

import numpy as np
import openpyxl
from gambar_teknik import BukuPDF as PdfPages
from matplotlib.patches import Rectangle

import tahap2_stratigrafi as st
from format_dokumen import AI, Lembar, set_font_bawaan
from gambar_teknik import Kertas
from tahap2_gambar_air_tanah import gaya_sumbu
from tahap2_gambar_geoteknik import kotak_catatan

AKAR = Path(__file__).resolve().parents[1]
BARU = AKAR / "01 Penyelidikan Tanah" / "Penyelidikan Tambahan"
KELUAR = AKAR / "02 Olah Data Tanah"
BERKAS = KELUAR / "2.7 Kimia Tebing Gudang.xlsx"
PDF = KELUAR / "2.7 Gambar Tebing dan Gudang.pdf"
LABEL = "DATA SIMULASI untuk studi kasus portofolio. Bukan data proyek nyata. Tidak untuk konstruksi."
LABEL_AI = ("DIISI AI ATAS PERMINTAAN DEFSA (19 Nov 2026), sel hijau; disetujui Defsa 19 Nov 2026. "
            "Kunci jawaban tidak dibuka.")
SO3_KE_SO4 = 96.06 / 80.06  # massa molar SO4 / SO3
MA_ACUAN, MA_3DES = 8.05, 7.64  # muka air PS-1 untuk konversi batimetri


def _baris(path, sheet, kunci):
    ws = openpyxl.load_workbook(path, data_only=True)[sheet]
    kepala, hasil = None, []
    for r in ws.iter_rows(values_only=True):
        isi = list(r)
        while isi and isi[0] is None:
            isi.pop(0)
        if not isi:
            continue
        if kepala is None and isi[0] == kunci:
            kepala = [k for k in isi if k is not None]
            continue
        if kepala and isi[0] is not None and not str(isi[0]).startswith(("LEMBAR", "DATA")):
            hasil.append(dict(zip(kepala, isi)))
    return hasil


# ------------------------------------------------------------------ kimia
def kelas_s_tanah(persen):
    """SNI 2847:2019 Tabel 19.3.1.1 hal. 437 (SO4 larut air dalam tanah, % massa)."""
    return "S0" if persen < 0.10 else "S1" if persen < 0.20 else "S2" if persen <= 2.00 else "S3"


def kelas_s_air(ppm):
    return "S0" if ppm < 150 else "S1" if ppm < 1500 else "S2" if ppm <= 10000 else "S3"


def kimia():
    f = BARU / "Kimia Tanah dan Air.xlsx"
    tanah = []
    for b in _baris(f, "Hasil Uji Tanah", "Kode"):
        if b["Satuan sulfat"].startswith("%"):
            so4 = b["Sulfat"] * SO3_KE_SO4
            cat = f"Sulfat dilaporkan {str(b['Sulfat']).replace('.', ',')} % SO₃ (satuan berbeda), dikonversi ×1,2 ke SO₄"
        else:
            so4 = b["Sulfat"] / 10000
            cat = ""
        agresif = b["pH"] < 4.5 or b["Resistivitas (Ω·cm)"] < 2000
        tanah.append(dict(b, so4=so4, kelas=kelas_s_tanah(so4), agresif=agresif, catatan=cat))
    air = []
    for b in _baris(f, "Hasil Uji Air", "Kode"):
        air.append(dict(b, kelas=kelas_s_air(b["Sulfat SO₄ (mg/L)"])))
    return tanah, air


# ------------------------------------------------------------------ tebing
def penampang(nama):
    f = BARU / "Survei Tebing.xlsx"
    data = _baris(f, f"Penampang {nama}", "Jarak dari batas lahan (m)")
    titik = []
    for b in data:
        j, e, s = b["Jarak dari batas lahan (m)"], b["Elevasi (m)"], b["Sumber"]
        d = b.get("Kedalaman air (m)")
        e_kor = e
        if nama == "P-3" and "Batimetri" in s:
            e_kor = MA_3DES - d  # diukur 3 Des 2026, bukan pada muka air acuan 14 Des
        titik.append(dict(jarak=j, elev=e, elev_kor=e_kor, sumber=s, kedalaman=d))
    return titik


def ringkas_tebing():
    f = BARU / "Survei Tebing.xlsx"
    ring = {b["Potongan"]: b for b in _baris(f, "Ringkasan", "Potongan")}
    hasil = []
    for n in ("P-1", "P-2", "P-3"):
        p = penampang(n)
        cr = ring[n]
        j0, e0 = cr["Jarak puncak tebing (m)"], cr["Elevasi puncak (m)"]
        air = [t for t in p if t["jarak"] > j0]
        tepi = next(t for t in air if t["elev_kor"] <= 7.64)
        thal = min(p, key=lambda t: t["elev_kor"])
        sudut_atas = np.degrees(np.arctan((e0 - tepi["elev_kor"]) / (tepi["jarak"] - j0)))
        sudut_total = np.degrees(np.arctan((e0 - thal["elev_kor"]) / (thal["jarak"] - j0)))
        hasil.append(dict(potongan=n, x=cr["x lokal (m)"], jarak_puncak=j0, elev_puncak=e0, jarak_tepi=tepi["jarak"],
                          thal_elev=thal["elev_kor"], thal_jarak=thal["jarak"], tinggi=e0 - thal["elev_kor"],
                          sudut_atas=float(sudut_atas), sudut_total=float(sudut_total),
                          koreksi=-(MA_ACUAN - MA_3DES) if n == "P-3" else 0.0))
    return hasil


def bor_tebing():
    f = BARU / "Survei Tebing.xlsx"
    wb = openpyxl.load_workbook(f, data_only=True)
    titik = {b["Titik"]: b for b in _baris(f, "Titik Bor Tebing", "Titik")}
    hasil = {}
    for nama in titik:
        lap = []
        for r in wb["Log " + nama].iter_rows(values_only=True):
            isi = [c for c in r if c is not None]
            if len(isi) >= 6 and isinstance(isi[0], (int, float)):
                u, _ = st.unit_dari_teks(isi[5])
                if "longsoran" in isi[5].lower():
                    u = "Longsoran"
                if "slickensided" in isi[5].lower():
                    u = "Bidang licin"
                lap.append(dict(atas=isi[0], bawah=isi[1], ea=isi[2], eb=isi[3], unit=u, uraian=isi[5]))
        spt = []
        for r in wb["SPT " + nama].iter_rows(values_only=True):
            isi = [c for c in r if c is not None]
            if len(isi) >= 6 and isinstance(isi[0], (int, float)) and isinstance(isi[5], (int, float)):
                spt.append((isi[0], isi[5]))
        hasil[nama] = dict(titik[nama], lapisan=lap, spt=spt)
    return hasil


# ------------------------------------------------------------------ gudang
def patok():
    f = BARU / "Survei Gudang Timur.xlsx"
    data = _baris(f, "Patok Penurunan", "Patok")
    tgl = [datetime(2026, 12, 3), datetime(2027, 1, 6), datetime(2027, 2, 3), datetime(2027, 3, 3),
           datetime(2027, 3, 31)]
    hasil = []
    for b in data:
        e = [b[k] for k in b if str(k).startswith("Elev.")]
        d = [(x - e[0]) * 1000 for x in e]
        cat = b.get("Catatan") or ""
        if "bengkok" in cat:  # loncatan 3 Feb - 3 Mar akibat pelurusan, bukan penurunan
            lonc = d[3] - d[2]
            d_kor = d[:3] + [d[2], d[2] + (d[4] - d[3])]
            cat = f"{cat}; loncatan {lonc:.1f} mm 3 Feb-3 Mar dianggap bukan penurunan"
        else:
            d_kor = d
        hasil.append(dict(patok=b["Patok"], x=b["x lokal (m)"], y=b["y lokal (m)"], elev=e, d=d, d_kor=d_kor,
                          laju=d_kor[-1] / ((tgl[-1] - tgl[0]).days / 30.44), catatan=cat))
    return tgl, hasil


def lantai():
    f = BARU / "Survei Gudang Timur.xlsx"
    data = _baris(f, "Elevasi Lantai", "Titik")
    hasil = []
    for b in data:
        y = b["y lokal (m)"]
        naik = 0.10 if y >= 50 else 0.0  # lantai sisi utara ditinggikan 10 cm (2009) [Asumsi: baris 5-6]
        hasil.append(dict(titik=b["Titik"], x=b["x lokal (m)"], y=y, elev=b["Elevasi lantai (m)"],
                          elev_kor=b["Elevasi lantai (m)"] - naik))
    return hasil


def kemiringan_lantai(lt):
    """Kemiringan antar kolom bersebelahan (asli dan terkoreksi peninggian 2009)."""
    d = {(t["x"], t["y"]): t for t in lt}
    hasil = []
    for (x, y), t in d.items():
        for dx, dy in ((6, 0), (0, 8)):
            u = d.get((x + dx, y + dy))
            if u:
                L = dx + dy
                hasil.append(dict(a=t["titik"], b=u["titik"], L=L, beta=abs(t["elev_kor"] - u["elev_kor"]) / L,
                                  beta_asli=abs(t["elev"] - u["elev"]) / L))
    return sorted(hasil, key=lambda h: -h["beta"])


def kategori_ciria(beta):
    """SNI 8460:2017 Tabel 33 hal. 159 (CIRIA PR30)."""
    return 1 if beta < 1 / 500 else 2 if beta < 1 / 200 else 3 if beta <= 1 / 50 else 4


if __name__ == "__main__":
    t, a = kimia()
    for x in t:
        print(x["Kode"], round(x["so4"], 3), x["kelas"], x["pH"], x["agresif"], x["catatan"])
    for x in a:
        print(x["Kode"], x["kelas"], x["pH"])
    for r in ringkas_tebing():
        print({k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items()})
    tg, p = patok()
    for x in p:
        print(x["patok"], [round(v, 1) for v in x["d_kor"]], round(x["laju"], 2), x["catatan"])
    km = kemiringan_lantai(lantai())
    for h in km[:5]:
        print(h["a"], h["b"], f"1/{1 / h['beta']:.0f}", f"asli 1/{1 / max(h['beta_asli'], 1e-9):.0f}",
              kategori_ciria(h["beta"]))
