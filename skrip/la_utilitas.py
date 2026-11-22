"""Laporan antara LA.4: dermaga ambulans air, helipad dan tata atap, tangki solar/O₂/IPAL, ramp beratap.

Tindak lanjut evaluasi kunci Tahap 3 no. 5-7 dan rapat konsep (Tabel 1.2 no. 3, 5, 6).
Data: TOR Lampiran A (muka air rata-rata bulanan terendah +4,00, Sep) dan Lampiran B (puncak tebing +10,2-10,4);
Data MEP Awal (Daftar Peralatan E-05, M-01, M-02, G-01, M-07); surat Kantor SAR (AW139 panjang keseluruhan 16,66 m);
peil 3.3; massa 3.4; sempadan 3.2.
Belum ada di acuan, jadi berlabel [Asumsi]: kemiringan ramp 1:12 (pejalan/brankar) dan 1:10 (kendaraan), kemiringan
jembatan berengsel ponton 1:3, FATO 1,5 D dan area aman 0,25 D (ICAO Annex 14 Vol. II), FK angkat 1,25, jarak tangki O₂ ke
tangki bahan bakar 10 m (NFPA 55), berat kosong tangki solar dari berat operasi dikurangi solar (ρ 0,84).
Disusun AI atas permintaan Defsa (19 Nov 2026); disetujui Defsa 19 Nov 2026 (LA.4).
"""
import math
from pathlib import Path

import tahap3_basement as bs
import tahap3_peil as pl
import tahap3_program as pr
import tahap3_template_bim as tpl
import tahap3_zonasi as zn

AKAR = Path(__file__).resolve().parents[1]
KELUAR = AKAR / "03 Desain Konsep"
BERKAS = KELUAR / "LA.4 Utilitas dan Fungsi Khusus.xlsx"
PDF = KELUAR / "LA.4 Gambar Utilitas Halaman dan Atap.pdf"
LABEL = "DATA SIMULASI untuk studi kasus portofolio. Bukan data proyek nyata. Tidak untuk konstruksi."
LABEL_AI = "DIISI AI ATAS PERMINTAAN DEFSA (19 Nov 2026), sel hijau; disetujui Defsa 19 Nov 2026 (LA.4)."
GW = 9.81

MUKA_AIR_RENDAH = 4.00  # TOR Lampiran A, rata-rata bulanan September
PUNCAK_TEBING = 10.3  # TOR Lampiran B, +10,2-10,4
MIRING_RAMP = 12.0  # 1:12 pejalan/brankar [Asumsi]
MIRING_KENDARAAN = 10.0  # 1:10 ramp kendaraan [Asumsi]
MIRING_GANGWAY = 3.0  # 1:3 jembatan berengsel ponton [Asumsi]
DEK_PONTON = 0.5  # m di atas muka air [Asumsi]
D_AW139 = 16.66  # m, panjang keseluruhan rotor berputar (surat SAR Tabel 1)
FATO_FAKTOR, AMAN_FAKTOR = 1.5, 0.25  # [Asumsi: ICAO Annex 14 Vol. II belum ada di acuan]
FK_ANGKAT = 1.25  # [Asumsi]
GAMMA_BETON = 24.0
TANGKI_SOLAR = {"jumlah": 2, "D": 2.4, "L": 3.6, "berat_operasi": 13800.0, "isi_L": 15000.0, "rho": 0.84}
DERMAGA_X = (8.0, 22.0)  # m, di x 0-40: sempadan tersempit, jauh dari longsoran x 70-110 (3.2)
LOKASI = {  # (x0, x1, y0, y1) di grid lokal; di zona gambut < 0,5 m, di antara retensi dan gedung utilitas
    "Tangki solar di atas tanah dalam tanggul": (114.0, 128.0, 40.5, 43.5),
    "Tangki oksigen cair di panggung": (100.0, 104.0, 40.5, 43.5),
    "IPAL (3.4)": zn.IPAL[:4] if len(zn.IPAL) > 4 else zn.IPAL,
}
PERALATAN_ATAP = {"chiller": (4, 11.0, 2.3, 3900.0), "tangki air": (1, 10.0, 6.0, 158000.0)}  # n, p, l, kg (M-01, M-02)
LUAS_ATAP_MEP = 520.0  # m², Data MEP Kebutuhan Ruang no. 8


def dermaga():
    pe = pl.peil_usulan()
    dh = pe["lantai"] - MUKA_AIR_RENDAH
    turun = PUNCAK_TEBING - (MUKA_AIR_RENDAH + DEK_PONTON)
    return {"beda_tinggi": dh, "ramp_1_12": dh * MIRING_RAMP, "ramp_1_10": dh * MIRING_KENDARAAN,
            "gangway": turun * MIRING_GANGWAY, "angkat_lif": pe["halaman"] - PUNCAK_TEBING,
            "rentang_air": pe["q50"] - MUKA_AIR_RENDAH}


def helipad():
    mn = pr.MASSA["MENARA"]
    lebar = mn["y"][1] - mn["y"][0]
    panjang = mn["x"][1] - mn["x"][0]
    fato = FATO_FAKTOR * D_AW139
    aman = fato + 2 * AMAN_FAKTOR * D_AW139
    sisa = (panjang - aman) * lebar
    pd = pr.MASSA["PODIUM"]
    atap_podium = (pd["x"][1] - pd["x"][0]) * (pd["y"][1] - pd["y"][0]) - panjang * lebar
    beban_tangki = PERALATAN_ATAP["tangki air"][3] * GW / 1000 / (PERALATAN_ATAP["tangki air"][1] *
                                                                   PERALATAN_ATAP["tangki air"][2])
    return {"lebar_menara": lebar, "panjang_menara": panjang, "fato": fato, "area_aman": aman,
            "kantilever": max(0.0, (aman - lebar) / 2), "sisa_atap_menara": sisa, "atap_podium": atap_podium,
            "perlu_mep": LUAS_ATAP_MEP, "beban_tangki_kPa": beban_tangki,
            "elev_atap_menara": dict(tpl.LEVEL)["ATAP"] / 1000, "elev_atap_podium": dict(tpl.LEVEL)["LT4"] / 1000}


def tangki_solar():
    t = TANGKI_SOLAR
    vol = math.pi * (t["D"] / 2) ** 2 * t["L"]
    kosong = (t["berat_operasi"] - t["isi_L"] * t["rho"]) * GW / 1000  # kN
    angkat = GW * vol
    pemberat = (FK_ANGKAT * angkat - kosong) / (GAMMA_BETON - GW)  # m³ beton terendam per tangki
    pe = pl.peil_usulan()
    return {"volume": vol, "berat_kosong": kosong, "angkat": angkat, "fk_tanpa_pemberat": kosong / angkat,
            "pemberat_beton": pemberat, "tanggul_m3": 1.1 * t["isi_L"] / 1000, "elev_pad": pe["lantai"]}


def ramp():
    pe = pl.peil_usulan()
    dh = pe["lantai"] - pe["halaman"]
    return {"beda": dh, "lobi": dh * MIRING_RAMP, "igd_kendaraan": dh * MIRING_KENDARAAN}


def jarak_o2_solar():
    a, b = LOKASI["Tangki oksigen cair di panggung"], LOKASI["Tangki solar di atas tanah dalam tanggul"]
    return b[0] - a[1]


def ringkasan():
    return {"dermaga": dermaga(), "helipad": helipad(), "tangki": tangki_solar(), "ramp": ramp(),
            "jarak_o2": jarak_o2_solar()}


def fmt(v, d=2):
    s = f"{v:,.{d}f}"
    return s.replace(",", "#").replace(".", ",").replace("#", ".")


def buat_excel(keluar=BERKAS):
    import openpyxl

    from format_dokumen import AI, Lembar, set_font_bawaan

    r = ringkasan()
    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)
    lb = Lembar(wb.create_sheet("Petunjuk"), 1, "Petunjuk utilitas dan fungsi khusus (LA.4)", [6, 120])
    lb.catatan(LABEL + " " + LABEL_AI)
    lb.kosong()
    lb.tabel(["No", "Petunjuk"], [[i + 1, s] for i, s in enumerate([
        "Tindak lanjut evaluasi kunci Tahap 3 no. 5-7 dan rapat konsep (Tabel 1.2 no. 3, 5, 6): dermaga, helipad dan tata "
        "atap, tangki solar/O₂/IPAL, ramp beratap.",
        "Data: TOR Lampiran A (muka air rendah +4,00) dan B (puncak tebing ±+10,3); Data MEP Awal (E-05, M-01, M-02, G-01, "
        "M-07); surat SAR (AW139 16,66 m); peil 3.3; massa 3.4.",
        "Belum ada di acuan, berlabel [Asumsi]: kemiringan ramp 1:12 dan 1:10, jembatan ponton 1:3, FATO 1,5 D dan area aman "
        "0,25 D (ICAO Annex 14 Vol. II), FK angkat 1,25, jarak O₂-bahan bakar 10 m (NFPA 55).",
        "Letak di halaman ada di gambar 'LA.4 Gambar Utilitas Halaman dan Atap.pdf' (GK-12).",
    ])], rata=list("cl"))

    lb = Lembar(wb.create_sheet("Dermaga"), 2, "Dermaga ambulans air ke IGD", [52, 16, 60])
    lb.catatan(LABEL)
    d = r["dermaga"]
    lb.tabel(["Butir", "Nilai", "Keterangan"], [
        ["Beda tinggi lantai IGD - muka air rendah (m)", round(d["beda_tinggi"], 2), "+12,85 - +4,00"],
        ["Panjang ramp brankar 1:12 (m)", round(d["ramp_1_12"], 1), "tanpa bordes; tidak muat di sempadan 6-8 m"],
        ["Panjang ramp 1:10 (m)", round(d["ramp_1_10"], 1), "tetap tidak muat"],
        ["Rentang muka air rendah - Q50 (m)", round(d["rentang_air"], 2), "ponton mengikuti muka air"],
        ["Jembatan berengsel ponton 1:3 (m)", round(d["gangway"], 1), "dari puncak tebing ke dek ponton saat air rendah"],
        ["Angkat lif brankar puncak tebing → halaman (m)", round(d["angkat_lif"], 2), "lif vertikal di puncak tebing"],
        ["Lokasi", f"x {DERMAGA_X[0]:.0f}-{DERMAGA_X[1]:.0f}", "sempadan tersempit, jauh dari longsoran x 70-110"],
    ], rata=list("lcl"), fill_kolom={1: AI})

    lb = Lembar(wb.create_sheet("Helipad dan Atap"), 3, "Helipad AW139 dan tata atap", [52, 16, 60])
    lb.catatan(LABEL)
    h = r["helipad"]
    lb.tabel(["Butir", "Nilai", "Keterangan"], [
        ["Lebar atap menara (m)", h["lebar_menara"], "menara 64 × 24 m (3.4)"],
        ["FATO 1,5 D (m)", round(h["fato"], 1), "D 16,66 m (AW139) [Asumsi ICAO]"],
        ["FATO + area aman 0,25 D tiap sisi (m)", round(h["area_aman"], 1), "lebih lebar dari menara"],
        ["Kantilever dek helipad tiap sisi (m)", round(h["kantilever"], 1), "dek baja di atas atap menara"],
        ["Sisa atap menara di luar area aman (m²)", round(h["sisa_atap_menara"]), "peralatan tinggi tidak boleh di jalur"],
        ["Kebutuhan area chiller + tangki air (m²)", h["perlu_mep"], "Data MEP no. 8"],
        ["Atap podium di luar menara (m²)", round(h["atap_podium"]), "usulan letak chiller dan tangki air"],
        ["Beban tangki air 158 t di atas 60 m² (kPa)", round(h["beban_tangki_kPa"], 1), "balok khusus di Tahap 4"],
    ], rata=list("lcl"), fill_kolom={1: AI})

    lb = Lembar(wb.create_sheet("Tangki dan IPAL"), 4, "Tangki solar, oksigen, IPAL", [52, 16, 60])
    lb.catatan(LABEL)
    t = r["tangki"]
    lb.tabel(["Butir", "Nilai", "Keterangan"], [
        ["Volume tangki solar per unit (m³)", round(t["volume"], 1), "Ø 2,4 × 3,6 m (E-05)"],
        ["Berat kosong (kN)", round(t["berat_kosong"], 1), "operasi 13,8 t - solar 15.000 L × 0,84"],
        ["Gaya angkat saat terendam (kN)", round(t["angkat"], 1), "γw × V; lahan utara tergenang/artesis"],
        ["FK angkat tanpa pemberat", round(t["fk_tanpa_pemberat"], 2), "jauh < 1: tangki kosong mengapung"],
        ["Pemberat beton per tangki bila tetap ditanam (m³)", round(t["pemberat_beton"], 1), "FK 1,25 [Asumsi]"],
        ["Usulan", "di atas tanah", f"dalam tanggul ±{fmt(t['tanggul_m3'], 1)} m³ (110 %), pelat +12,85, di zona gambut < 0,5 m"],
        ["Jarak tangki O₂ ke tangki solar (m)", round(r["jarak_o2"], 1), "≥ 10 m [Asumsi NFPA 55]"],
        ["IPAL", "x 96-108, y 30-38", "3.4; dinding di atas banjir, pompa angkat + pintu klep ke saluran"],
    ], rata=list("lcl"), fill_kolom={1: AI})

    lb = Lembar(wb.create_sheet("Ramp"), 5, "Ramp beratap lobi dan IGD", [52, 16, 60])
    lb.catatan(LABEL)
    rp = r["ramp"]
    lb.tabel(["Butir", "Nilai", "Keterangan"], [
        ["Beda tinggi lantai - halaman (m)", round(rp["beda"], 2), "+12,85 - +12,05 (3.3)"],
        ["Ramp lobi 1:12 (m)", round(rp["lobi"], 1), "tanpa bordes; beratap"],
        ["Ramp ambulans IGD 1:10 (m)", round(rp["igd_kendaraan"], 1), "drop-off beratap"],
    ], rata=list("lcl"), fill_kolom={1: AI})
    wb.save(keluar)
    return keluar


def gambar_cad(status=None):
    from cad_lembar import STATUS_SETUJU, Gambar
    import tahap3_tapak as tp

    def k(x0, x1, y0, y1):
        return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]

    h = helipad()
    dwg = KELUAR / "Gambar" / "DWG" / "GK-12 Utilitas Halaman dan Atap.dwg"
    png = KELUAR / "Gambar" / "GK-12 Utilitas Halaman dan Atap.png"
    pd, mn, gu = pr.MASSA["PODIUM"], pr.MASSA["MENARA"], bs.GEDUNG_UP
    with Gambar(750) as g:
        # denah tapak
        g.layer("C-SEMPADAN", 3, 0.25)
        g.arsir(list(tp.ruang_sempadan().exterior.coords)[:-1], "C-SEMPADAN", pola="DOTS", skala_pola=0.6)
        g.legenda_tambah("arsir", "Ruang sempadan sungai", pola="DOTS", skala_pola=0.6)
        g.layer("A-MASSA", 7, 0.7)
        g.pline(k(*pd["x"], *pd["y"]), "A-MASSA", tutup=True)
        g.pline(k(*gu["x"], *gu["y"]), "A-MASSA", tutup=True)
        g.legenda_tambah("garis", "Massa bangunan", tebal=0.7)
        g.layer("M-UTILITAS", 7, 0.35)
        for nama, (x0, x1, y0, y1) in LOKASI.items():
            g.arsir_lubang(k(x0, x1, y0, y1), [], "M-UTILITAS", pola="ANSI37", skala_pola=0.6)
            g.pline(k(x0, x1, y0, y1), "M-UTILITAS", tutup=True)
        g.legenda_tambah("arsir", "Utilitas halaman (pelat +12,85)", pola="ANSI37", skala_pola=0.6)
        g.layer("C-KOLAM", 7, 0.35)
        g.pline(k(*zn.RETENSI), "C-KOLAM", tutup=True)
        g.layer("A-TEKS", 7, 0.25)
        g.teks((48, 51), "PODIUM", "A-TEKS", 2.0, j="MC", tebal=True)
        g.teks((117, 62), "GEDUNG UTILITAS", "A-TEKS", 1.8, j="MC", tebal=True)
        g.teks((123, 31), "KOLAM RETENSI", "C-KOLAM", 1.5, j="MC")
        g.tunjuk((127, 42), (146, 47), "TANGKI SOLAR", layer="M-TEKS")
        g.tunjuk((102, 42), (90, 56), "TANGKI O2", layer="M-TEKS")
        g.tunjuk((102, 34), (88, 22), "IPAL", layer="M-TEKS")
        # dermaga, lif, jalur ke IGD
        g.layer("A-DERMAGA", 7, 0.35, "DASHED")
        g.pline(k(DERMAGA_X[0], DERMAGA_X[1], -6.0, -3.0), "A-DERMAGA", tutup=True)
        g.pline([(15.0, -3.0), (15.0, 7.0)], "A-DERMAGA")
        g.pline(k(13.0, 17.0, 7.0, 10.0), "A-DERMAGA", tutup=True)
        g.pline([(15.0, 10.0), (15.0, 22.0), (62.0, 22.0), (62.0, 27.0)], "A-DERMAGA")
        g.legenda_tambah("garis", "Dermaga ponton, lif, selasar ke IGD (tahap 2)", garis="DASHED")
        g.tunjuk((21, -4.5), (34, -5.5), "PONTON + JEMBATAN BERENGSEL", layer="A-TEKS")
        g.tunjuk((16, 8.5), (32, 12), "LIF BRANKAR PUNCAK TEBING", layer="A-TEKS")
        g.layer("C-PERSIL", 7, 0.7, "PHANTOM")
        g.pline(k(0, 140, 0, 90), "C-PERSIL", tutup=True)
        g.teks((70, 91.5), "JALAN KOLEKTOR", "C-TEKS", 2.2, j="MC", tebal=True)
        # denah atap (viewport kedua, model di y -150)
        oy, ox = -105.0, 0.0  # denah atap di bawah tapak, viewport yang sama 1:750
        g.layer("A-ATAP", 7, 0.5)
        g.pline(k(pd["x"][0] + ox, pd["x"][1] + ox, pd["y"][0] + oy, pd["y"][1] + oy), "A-ATAP", tutup=True)
        g.layer("A-ATAP-MENARA", 7, 0.7)
        g.pline(k(mn["x"][0] + ox, mn["x"][1] + ox, mn["y"][0] + oy, mn["y"][1] + oy), "A-ATAP-MENARA", tutup=True)
        cx = mn["x"][1] - h["area_aman"] / 2 + ox
        cy = (mn["y"][0] + mn["y"][1]) / 2 + oy
        g.layer("A-HELIPAD", 7, 0.5)
        f, a = h["fato"] / 2, h["area_aman"] / 2
        g.pline(k(cx - f, cx + f, cy - f, cy + f), "A-HELIPAD", tutup=True)
        g.layer("A-HELIPAD-AMAN", 7, 0.25, "DASHED")
        g.pline(k(cx - a, cx + a, cy - a, cy + a), "A-HELIPAD-AMAN", tutup=True)
        g.legenda_tambah("garis", "Area aman helipad (0,25 D)", garis="DASHED")
        g.teks((cx, cy + 2), "FATO AW139", "A-TEKS", 1.6, j="MC", tebal=True)
        g.teks((cx, cy - 1.5), f"{fmt(h['fato'], 1)} × {fmt(h['fato'], 1)} M", "A-TEKS", 1.4, j="MC")
        g.layer("M-ATAP", 7, 0.35)
        for i in range(4):
            g.pline(k(24 + i * 3.5 + ox, 26.3 + i * 3.5 + ox, 57 + oy, 68 + oy), "M-ATAP", tutup=True)
        g.pline(k(44 + ox, 54 + ox, 62 + oy, 68 + oy), "M-ATAP", tutup=True)
        g.teks((30 + ox, 71 + oy), "4 CHILLER", "A-TEKS", 1.5, j="MC")
        g.teks((49 + ox, 71 + oy), "TANGKI AIR 150 M3", "A-TEKS", 1.5, j="MC")
        g.teks((48 + ox, 80 + oy), "DENAH ATAP MENARA DAN PODIUM", "A-TEKS", 2.0, j="MC", tebal=True)
        g.teks((48 + ox, 77 + oy), "ATAP PODIUM +26,05; ATAP MENARA +38,65", "A-TEKS", 1.5, j="MC")
        g.lembar("GK-12", "Utilitas halaman dan atap", "1:750", pusat=(70, 2), vp=((24, 38), (331, 283)),
                 judul_kop="Utilitas dan atap",
                 subjudul="LA.4: dermaga di x 8-22, tangki solar dan O2 di atas tanah +12,85, helipad AW139 di atap menara",
                 status=status or STATUS_SETUJU,
                 catatan=[
                     f"Dermaga: beda tinggi IGD - air rendah {fmt(dermaga()['beda_tinggi'])} m; ramp 1:12 "
                     f"{fmt(dermaga()['ramp_1_12'], 0)} m tidak muat, diganti ponton + lif.",
                     f"Helipad: FATO + area aman {fmt(h['area_aman'], 1)} m > lebar menara 24 m; dek kantilever "
                     f"{fmt(h['kantilever'], 1)} m tiap sisi.",
                     "Chiller dan tangki air pindah ke atap podium; tangki solar tidak ditanam.",
                     "Ukuran FATO, ramp, jarak O2 [Asumsi]; acuan belum ada.",
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
    for k_, v in ringkasan().items():
        print(k_, {a: (round(b, 2) if isinstance(b, float) else b) for a, b in v.items()} if isinstance(v, dict) else v)
