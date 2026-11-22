"""Tahap 9: jadwal pelaksanaan (CPM sederhana), bobot dari RAB 8b, kurva S, Gantt, Excel, MSPDI XML, T-122..T-125.

Pakai ulang `tahap8_rab.rab()`/`rekap()` (biaya, tanpa hitung ulang volume) dan `tahap8_volume` (tiang bor).
Jalankan: .venv\\Scripts\\python.exe skrip\\tahap9_jadwal.py [--tanpa-excel]
"""
import datetime as dt
import math
import pathlib
import sys

import tahap8_rab as rb
import tahap8_volume as t8

AKAR = pathlib.Path(__file__).resolve().parents[1]
FOLDER = AKAR / "09 Jadwal"
KELUAR = FOLDER / "9 Jadwal dan Kurva S.xlsx"
GAMBAR = FOLDER / "9 Gantt dan Kurva S.png"
XML = FOLDER / "9 Jadwal.xml"
STATUS = "disetujui Defsa 23 Nov 2026"
LABEL = "Data simulasi studi kasus. Durasi selain tiang bor [Asumsi: praktik gedung beton 6 lantai]."
MULAI = dt.date(2028, 1, 3)          # K9-1 [Asumsi], digeser K10-8 (sesudah Laporan Akhir Agu 2027 + tender)
MGG_BLN = 52 / 12                    # minggu per bulan (K9-1)
SMKK_BLN, TC_BLN = 24, 18            # durasi SMKK dan sewa tower crane di RAB 8b (rb.SMKK, P5)
RIG, JAM_HARI, HARI_MGG = 2, 8, 6    # K9-3: 2 rig (P4), 8 jam efektif [Asumsi], 6 hari kerja
TOL = {"T-122a": 0.01, "T-122b": 1.0, "T-122c": 0.01, "T-123": 30.0, "T-124": (-15.0, 0.0), "T-125": 15.0}
SIKLUS = [5, 5, 5, 4, 4, 4, 4]       # K9-4 minggu per lantai LT1..LT6, atap [Asumsi]
MEP_KASAR = 0.60                     # K9-5 [Asumsi]


def biaya_kelompok():
    """Biaya (Rp, tanpa PPN) per kelompok kegiatan dari RAB 8b."""
    r = rb.rekap()
    item = {no: isi for no, _, isi in r["divisi"]}
    j = lambda xs: sum(x["jumlah"] for x in xs)  # noqa: E731
    i1 = {x["kode"]: x["jumlah"] for x in item["I"]}
    tiang = j(rb._struktur(["Tiang bor Ø800"]))
    fasad = j(x for x in item["IV"] if x["kode"] in ("A9", "A10", "R-OV"))
    lahan = j(x for x in item["V"] if x["kode"].startswith("L"))
    lift = j(x for x in item["VI"] if x["kode"] == "M-LIF")
    mep = j(item["VI"]) - lift
    return {
        "PER": i1["P1"] + i1["P3"] + i1["P4"], "MP": i1["P2"] + i1["P6"] + i1["P7"], "TC": i1["P5"], "UJI": i1["P8"],
        "LHN": lahan, "TPK": j(item["V"]) - lahan, "TB": tiang, "GAL": j(item["II"]) - tiang,
        "STR": j(item["III"]), "FAS": fasad, "ARS": j(item["IV"]) - fasad,
        "MEP1": MEP_KASAR * mep, "MEP2": (1 - MEP_KASAR) * mep, "LIF": lift, "SMKK": r["j_smkk"],
    }, r


def durasi_tiang():
    """(minggu SE 47/2026, minggu pembanding 1 tiang/rig/hari, jam alat)."""
    s = t8.volume_struktur()["Tiang bor Ø800"]
    jam = s["panjang"] * t8.koef_bor(s["panjang"] / s["n"])
    return math.ceil(jam / (RIG * JAM_HARI * HARI_MGG)), s["n"] / RIG / HARI_MGG, jam, s


def kegiatan():
    """Daftar kegiatan: kode, uraian, biaya, durasi, hubungan [(pendahulu, FS/SS, jeda)], sumber; hammock = durasi None."""
    b, _ = biaya_kelompok()
    tb, *_ = durasi_tiang()
    lantai = ["LT1 (kolom/dinding inti + pelat LT2)", "LT2 (+ pelat LT3, atap podium)", "LT3 (+ pelat LT4)",
              "LT4 (+ pelat LT5)", "LT5 (+ pelat LT6)", "LT6 (+ pelat atap)", "atap (ruang alat, tangki, dek helipad)"]
    k = [
        ("PER", "Persiapan: uitzet, pagar, mobilisasi alat", b["PER"], 6, [], "[Asumsi]"),
        ("LHN", "Pematangan lahan (urugan, perkuatan tepi sungai)", b["LHN"], 10, [("PER", "SS", 2)], "[Asumsi]"),
        ("TB", "Tiang bor Ø800 (321 tiang, 2 rig)", b["TB"], tb, [("LHN", "SS", 4)], "SE 47/2026 Lamp. II hal. 187-188"),
        ("GAL", "Galian, dewatering, pile cap, sloof, pelat LT1, pit lift", b["GAL"], 14, [("TB", "SS", 8)], "[Asumsi]"),
    ]
    for i, (nama, d) in enumerate(zip(lantai, SIKLUS)):
        rel = [("GAL", "SS", 6)] if i == 0 else [(f"STR{i}", "FS", 0)]
        k.append((f"STR{i + 1}", f"Struktur {nama}", b["STR"] / 7, d, rel, "[Asumsi] siklus K9-4"))
    k += [
        ("ARS", "Arsitektur dalam: dinding, plester, lantai, plafon, pintu, cat", b["ARS"], 40, [("STR3", "FS", 0)], "[Asumsi]"),
        ("FAS", "Fasad kaca dan panel komposit", b["FAS"], 24, [("STR4", "FS", 0)], "[Asumsi]"),
        ("MEP1", "MEP instalasi kasar (pipa, kabel, ducting, sprinkler)", b["MEP1"], 44, [("STR2", "FS", 0)], "[Asumsi] K9-5"),
        ("MEP2", "MEP alat utama (chiller, genset, gas medis) dan finishing", b["MEP2"], 30, [("MEP1", "SS", 30)], "[Asumsi] K9-5"),
        ("LIF", "Lift (pemasangan dan uji)", b["LIF"], 26, [("STR7", "FS", 0)], "[Asumsi]"),
        ("TPK", "Tapak: jalan, parkir, drainase, taman, dermaga", b["TPK"], 20, [("STR7", "FS", 6)], "[Asumsi]"),
        ("UJI", "Uji fungsi, commissioning, pembersihan, serah terima", b["UJI"], 8,
         [("ARS", "FS", 0), ("FAS", "FS", 0), ("MEP2", "FS", 0), ("LIF", "FS", 0), ("TPK", "FS", 0)], "[Asumsi]"),
        ("TC", "Sewa tower crane 2 unit (struktur LT1 s.d. fasad)", b["TC"], None, [("STR1", "SS", 0), ("FAS", "FF", 0)], "K9-6"),
        ("MP", "Manajemen lapangan: direksi keet, listrik/air kerja, dokumentasi", b["MP"], None, [], "K9-6"),
        ("SMKK", "Penerapan SMKK (9 komponen)", b["SMKK"], None, [], "K9-6"),
    ]
    return [dict(zip(("kode", "uraian", "biaya", "dur", "rel", "sumber"), x)) for x in k]


def jadwal():
    """CPM maju-mundur; kembalikan kegiatan + mulai/selesai/kritis, durasi total, bobot, kurva S."""
    ks = kegiatan()
    d = {k["kode"]: k for k in ks}
    nyata = [k for k in ks if k["dur"] is not None]
    for k in nyata:   # urutan daftar sudah topologis
        k["mulai"] = max([0] + [d[p]["selesai"] + lag if t == "FS" else d[p]["mulai"] + lag for p, t, lag in k["rel"]])
        k["selesai"] = k["mulai"] + k["dur"]
    T = max(k["selesai"] for k in nyata)
    for k in nyata:
        k["ls"] = T - k["dur"]
    for k in reversed(nyata):
        for p, t, lag in k["rel"]:
            q = d[p]
            batas = k["ls"] - lag if t == "FS" else k["ls"] - lag + q["dur"]
            q["ls"] = min(q["ls"], batas - q["dur"])
    for k in nyata:
        k["float"] = k["ls"] - k["mulai"]
        k["kritis"] = k["float"] == 0
    d["TC"].update(mulai=d["STR1"]["mulai"], selesai=d["FAS"]["selesai"])
    for c in ("MP", "SMKK"):
        d[c].update(mulai=0, selesai=T)
    total = sum(k["biaya"] for k in ks)
    for k in ks:
        k.setdefault("kritis", False)
        k["dur"] = k["selesai"] - k["mulai"]
        k["bobot"] = k["biaya"] / total * 100
    mingguan = [sum(k["bobot"] / k["dur"] for k in ks if k["mulai"] < w <= k["selesai"]) for w in range(1, T + 1)]
    kum = [sum(mingguan[:i + 1]) for i in range(T)]
    return {"kegiatan": ks, "T": T, "total": total, "mingguan": mingguan, "kumulatif": kum}


def tanggal(minggu):
    return MULAI + dt.timedelta(weeks=minggu)


def cek_silang(j=None):
    j = j or jadwal()
    r = rb.rekap()
    d = {k["kode"]: k for k in j["kegiatan"]}
    tb, tb2, *_ = durasi_tiang()
    bln = j["T"] / MGG_BLN
    tc = d["TC"]["dur"] / MGG_BLN
    out = [
        ("T-122a", "Σ bobot kegiatan (%)", sum(k["bobot"] for k in j["kegiatan"]), 100.0),
        ("T-122b", "Σ biaya kegiatan vs jumlah RAB 8b I-VII (Rp)", j["total"], r["jumlah"]),
        ("T-122c", "Kumulatif kurva S minggu akhir (%)", j["kumulatif"][-1], 100.0),
        ("T-123", "Durasi tiang bor (minggu): SE 47/2026 vs 1 tiang/rig/hari", tb, tb2),
        ("T-124", "Durasi lintasan kritis (bulan) vs SMKK RAB 8b", bln, SMKK_BLN),
        ("T-125", "Masa pakai tower crane (bulan) vs sewa P5 RAB 8b", tc, TC_BLN),
    ]
    hasil = []
    for kode, besaran, x1, x2 in out:
        tol = TOL[kode]
        if kode in ("T-122a", "T-122c"):
            sel, lolos = x1 - x2, abs(x1 - x2) <= tol
        elif kode == "T-122b":
            sel, lolos = x1 - x2, abs(x1 - x2) <= tol
        else:
            sel = (x1 / x2 - 1) * 100
            lolos = tol[0] <= sel <= tol[1] if isinstance(tol, tuple) else abs(sel) <= tol
        hasil.append({"kode": kode, "besaran": besaran, "x1": x1, "x2": x2, "selisih": sel, "lolos": lolos})
    return hasil


def idn(v, d=1):
    return f"{v:,.{d}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def gambar(j=None, keluar=GAMBAR):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    j = j or jadwal()
    ks = j["kegiatan"]
    fig, ax = plt.subplots(figsize=(16.5, 10.5))
    for i, k in enumerate(ks):
        warna = "#c0392b" if k["kritis"] else ("#bbbbbb" if k["kode"] in ("TC", "MP", "SMKK") else "#2e6da4")
        ax.barh(i, k["dur"], left=k["mulai"], color=warna, edgecolor="black", linewidth=0.4, height=0.6)
        ax.text(k["selesai"] + 0.6, i, f"{idn(k['bobot'], 2)} %", va="center", fontsize=8)
    ax.set_yticks(range(len(ks)), [f"{k['kode']}  {k['uraian'][:58]}" for k in ks], fontsize=8.5)
    ax.invert_yaxis()
    ax.set_xlim(0, j["T"] + 4)
    ax.set_xlabel(f"Minggu ke- (mulai {MULAI:%d-%m-%Y} [Asumsi])")
    for b in range(0, j["T"] + 4, 13):
        ax.axvline(b, color="#dddddd", lw=0.6, zorder=0)
    ax2 = ax.twinx()
    ax2.plot(range(0, j["T"] + 1), [0] + j["kumulatif"], color="black", lw=1.8, label="Kurva S rencana (bobot kumulatif)")
    ax2.set_ylim(0, 105)
    ax2.set_ylabel("Bobot kumulatif (%)")
    ax2.legend(loc="upper center", bbox_to_anchor=(0.82, -0.06), fontsize=9)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color="#c0392b", label="Lintasan kritis"), Patch(color="#2e6da4", label="Kegiatan"),
                       Patch(color="#bbbbbb", label="Kegiatan ringkas (biaya waktu)")], loc="upper center", bbox_to_anchor=(0.3, -0.06), ncol=3, fontsize=9)
    ax.set_title(f"Jadwal pelaksanaan RS tipe C tepi Batanghari: {j['T']} minggu ({idn(j['T'] / MGG_BLN, 1)} bulan); "
                 f"bobot = biaya RAB 8b. Data simulasi.", fontsize=11)
    fig.tight_layout()
    keluar.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(keluar, dpi=150)
    fig.savefig(keluar.with_suffix(".pdf"))
    plt.close(fig)
    return keluar


def tulis_xml(j=None, keluar=XML):
    """MSPDI (dibuka ProjectLibre/MS Project). Kalender standar 5 hari; durasi minggu × 40 jam."""
    from xml.sax.saxutils import escape
    j = j or jadwal()
    uid = {k["kode"]: i + 1 for i, k in enumerate(j["kegiatan"])}
    tipe = {"FF": 0, "FS": 1, "SS": 3}
    t = []
    for k in j["kegiatan"]:
        tautan = "" if k["kode"] in ("TC", "MP", "SMKK") else "".join(
            f"<PredecessorLink><PredecessorUID>{uid[p]}</PredecessorUID><Type>{tipe[ty]}</Type>"
            f"<LinkLag>{lag * 5 * 8 * 600}</LinkLag><LagFormat>7</LagFormat></PredecessorLink>" for p, ty, lag in k["rel"])
        t.append(f"<Task><UID>{uid[k['kode']]}</UID><ID>{uid[k['kode']]}</ID><Name>{escape(k['kode'] + ' ' + k['uraian'])}</Name>"
                 f"<Start>{tanggal(k['mulai'])}T08:00:00</Start><Finish>{tanggal(k['selesai'])}T17:00:00</Finish>"
                 f"<Duration>PT{k['dur'] * 40}H0M0S</Duration><DurationFormat>11</DurationFormat>"
                 f"<ConstraintType>4</ConstraintType><ConstraintDate>{tanggal(k['mulai'])}T08:00:00</ConstraintDate>"
                 f"<Critical>{int(k['kritis'])}</Critical><Notes>{escape(f'Bobot {k['bobot']:.3f} %; sumber {k['sumber']}')}</Notes>"
                 f"{tautan}</Task>")
    keluar.write_text('<?xml version="1.0" encoding="UTF-8"?>\n<Project xmlns="http://schemas.microsoft.com/project">'
                      f"<Name>RSTB Jadwal Tahap 9</Name><StartDate>{MULAI}T08:00:00</StartDate><Tasks>{''.join(t)}</Tasks>"
                      "</Project>\n", encoding="utf-8")
    return keluar


def buat_excel(j=None, keluar=KELUAR):
    import openpyxl
    from format_dokumen import Lembar, set_font_bawaan
    j = j or jadwal()
    ks = j["kegiatan"]
    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)
    rp = "#,##0"
    # 2 Kegiatan
    s = Lembar(wb.create_sheet("Kegiatan"), 2, "Daftar kegiatan, bobot dan jadwal",
               [5, 8, 54, 22, 18, 10, 9, 9, 9, 8, 26])
    s.ws.page_setup.paperSize = s.ws.PAPERSIZE_A3  # 11 kolom: A3 agar huruf cetak terbaca (AU-09)
    s.catatan("Bobot = biaya / Σ biaya (rumus). Biaya dari RAB 8b sebelum PPN (K9-2). Mulai dari CPM Python (hubungan di kolom "
              "Pendahulu, FS/SS + jeda minggu); Selesai = Mulai + Durasi (rumus). Kegiatan TC, MP, SMKK ringkas (K9-6).")
    r0 = s.baris + 1
    rn = r0 + len(ks) - 1
    E, F, G, H, I = (s.kol(i) for i in (4, 5, 6, 7, 8))
    rows = []
    for i, k in enumerate(ks):
        rel = ", ".join(f"{p} {t}{'+' + str(lag) if lag else ''}" for p, t, lag in k["rel"]) or "-"
        rows.append([i + 1, k["kode"], k["uraian"], rel, round(k["biaya"], 2), f"={E}{r0 + i}/SUM({E}${r0}:{E}${rn})",
                     k["mulai"], k["dur"], f"={G}{r0 + i}+{H}{r0 + i}", "ya" if k["kritis"] else "", k["sumber"]])
    rows.append(["", "", "Jumlah / durasi total", "", f"=SUM({E}{r0}:{E}{rn})", f"=SUM({F}{r0}:{F}{rn})", "", "",
                 f"=MAX({I}{r0}:{I}{rn})", "", ""])
    s.tabel(["No", "Kode", "Kegiatan", "Pendahulu", "Biaya (Rp)", "Bobot", "Mulai (mgg)", "Durasi (mgg)", "Selesai (mgg)",
             "Kritis", "Sumber durasi"], rows, rata=list("cclllrrrrcl"),
            fmt=[None, None, None, None, rp, "0.00%", "0", "0", "0", None, None])
    tot = f"Kegiatan!{F}{rn + 1}"
    T_sel = f"Kegiatan!{I}{rn + 1}"
    # 3 Kurva S
    s = Lembar(wb.create_sheet("Kurva S"), 3, "Kurva S rencana (bobot mingguan dan kumulatif)", [9, 13, 18, 18, 30])
    s.catatan("Bobot mingguan = Σ bobot/durasi kegiatan yang berjalan di minggu itu (Mulai < minggu ≤ Selesai), rumus SUMPRODUCT "
              "ke lembar Kegiatan; kumulatif = jumlah berjalan.")
    k0 = s.baris + 1
    A, B, C = s.kol(0), s.kol(2), s.kol(3)
    rng = lambda c: f"Kegiatan!${c}${r0}:${c}${rn}"  # noqa: E731
    rows = []
    for w in range(1, j["T"] + 1):
        rr = k0 + w - 1
        rows.append([w, tanggal(w - 1).strftime("%d-%m-%Y"),
                     f"=SUMPRODUCT(({rng(G)}<{A}{rr})*({rng(I)}>={A}{rr})*{rng(F)}/{rng(H)})",
                     f"={B}{rr}" if w == 1 else f"={C}{rr - 1}+{B}{rr}", ""])
    s.tabel(["Minggu", "Mulai minggu", "Bobot mingguan", "Bobot kumulatif", "Catatan"], rows,
            rata=list("ccrrl"), fmt=[None, None, "0.000%", "0.00%", None])
    kum_akhir = f"'Kurva S'!{C}{k0 + j['T'] - 1}"
    # 4 Verifikasi dan acuan
    cs = cek_silang(j)
    s = Lembar(wb.create_sheet("Verifikasi dan Acuan"), 4, "Cek silang T-122..T-125 dan acuan", [9, 52, 17, 17, 12, 14, 9])
    fm = {"T-122b": rp}
    rows = []
    for b in cs:
        tol = TOL[b["kode"]]
        bt = f"{tol[0]:g} s.d. {tol[1]:g} %" if isinstance(tol, tuple) else (f"≤ Rp {tol:g}" if b["kode"] == "T-122b" else
                                                                             f"± {tol:g} {'%' if b['kode'] in ('T-123', 'T-125') else 'poin %'}")
        rows.append([b["kode"], b["besaran"], round(b["x1"], 4 if b["kode"] != "T-122b" else 0),
                     round(b["x2"], 4 if b["kode"] != "T-122b" else 0), round(b["selisih"], 4), bt,
                     "lolos" if b["lolos"] else "gagal"])
    s.tabel(["Kode", "Besaran", "Cara 1", "Cara 2", "Selisih", "Batas", "Hasil"], rows,
            rata=list("clrrrcc"), fmt=[None, None, "#,##0.00", "#,##0.00", "#,##0.0000", None, None])
    s.catatan("T-122a/c versi Excel (rumus dihitung Excel) dicatat di md dan VERIFIKASI.md.")
    _ = fm
    s.kosong()
    s.bagian("B", "Acuan")
    s.tabel(["No", "Acuan", "Dipakai untuk", "", "", "", "Status"], [
        [1, "SE Dirjen Binkon 47/2026 Lamp. II hal. 187-188", "produktivitas mesin bor (via tahap8_volume.koef_bor)", "", "", "", "publik"],
        [2, "RAB 8b (skrip/tahap8_rab.py)", "biaya/bobot, 2 rig (P4), TC 18 bulan (P5), SMKK 24 bulan", "", "", "", "proyek"],
        [3, "Durasi dan siklus selain tiang bor", "K9-1..K9-7", "", "", "", "[Asumsi]"],
    ], rata=list("clllllc"), beku=False)
    # 1 Ringkasan
    s = Lembar(wb.create_sheet("Ringkasan", 0), 1, "Ringkasan jadwal Tahap 9", [8, 62, 22])
    s.catatan(f"STATUS: {STATUS}. {LABEL}")
    s.catatan("Petunjuk: lembar 2 kegiatan (ubah Mulai/Durasi/Biaya, bobot dan kurva S ikut), lembar 3 kurva S mingguan, lembar 4 "
              "cek silang dan acuan. Gantt: 09 Jadwal/9 Gantt dan Kurva S.pdf; ProjectLibre: 09 Jadwal/9 Jadwal.xml. "
              "Hitung ulang: .venv\\Scripts\\python.exe skrip\\tahap9_jadwal.py")
    s.kosong()
    s.bagian("A", "Angka kunci")
    r1 = s.baris + 1
    C3 = s.kol(2)
    s.tabel(["No", "Besaran", "Nilai"], [
        [1, "Σ biaya kegiatan = jumlah RAB 8b I-VII sebelum PPN (Rp)", f"=Kegiatan!{E}{rn + 1}"],
        [2, "Σ bobot (harus 100 %)", f"={tot}"],
        [3, "Durasi total lintasan kritis (minggu)", f"={T_sel}"],
        [4, "Durasi total (bulan)", f"={C3}{r1 + 2}/(52/12)"],
        [5, "Bobot kumulatif minggu akhir", f"={kum_akhir}"],
        [6, "Selesai rencana (tanggal)", tanggal(j["T"]).strftime("%d-%m-%Y")],
    ], rata=list("clr"), fmt=[None, None, "#,##0.00"])
    for rr, f in ((r1 + 1, "0.00%"), (r1 + 4, "0.00%"), (r1, rp), (r1 + 2, "0")):  # durasi minggu bulat (AU-09)
        s.ws[f"{C3}{rr}"].number_format = f
    keluar.parent.mkdir(parents=True, exist_ok=True)
    wb.save(keluar)
    return keluar, {"bobot": f"{C3}{r1 + 1}", "kum": f"{C3}{r1 + 4}", "T": f"{C3}{r1 + 2}"}


def cek_excel(keluar=KELUAR, sel=None):
    """T-122a/c versi Excel: (Σ bobot, kumulatif akhir, durasi) setelah dihitung Excel."""
    import openpyxl
    from format_dokumen import hitung_ulang_excel
    ok, err = hitung_ulang_excel(keluar)
    if not ok:
        return None, err
    ws = openpyxl.load_workbook(keluar, data_only=True)["Ringkasan"]
    return {k: ws[v].value for k, v in sel.items()}, ""


def tulis_md(j, cs, xl, keluar=KELUAR.with_suffix(".md")):
    L = [f"# Tahap 9: Jadwal dan Kurva S", "", f"Status: {STATUS}. {LABEL}", "",
         f"Mulai {MULAI:%d-%m-%Y} [Asumsi], durasi **{j['T']} minggu ({idn(j['T'] / MGG_BLN, 1)} bulan)**, selesai "
         f"{tanggal(j['T']):%d-%m-%Y}. Bobot = biaya RAB 8b sebelum PPN (Rp {idn(j['total'] / 1e9, 2)} miliar).", "",
         "| Kode | Kegiatan | Bobot (%) | Mulai (mgg) | Durasi (mgg) | Selesai (mgg) | Kritis | Sumber |",
         "|---|---|---:|---:|---:|---:|:-:|---|"]
    for k in j["kegiatan"]:
        L.append(f"| {k['kode']} | {k['uraian']} | {idn(k['bobot'], 2)} | {k['mulai']} | {k['dur']} | {k['selesai']} | "
                 f"{'ya' if k['kritis'] else ''} | {k['sumber']} |")
    tb, tb2, jam, s = durasi_tiang()
    L += ["", f"Tiang bor: {s['n']} tiang, {idn(s['panjang'], 0)} m', {idn(jam, 0)} jam alat (koef "
          f"{idn(t8.koef_bor(s['panjang'] / s['n']), 4)} jam/m', SE 47/2026 Lamp. II hal. 187-188) / ({RIG} rig × {JAM_HARI} jam × "
          f"{HARI_MGG} hari) = {tb} minggu.", "", "## Kurva S (tiap 13 minggu)", "", "| Minggu | Kumulatif (%) |", "|---:|---:|"]
    L += [f"| {w} | {idn(j['kumulatif'][w - 1], 1)} |" for w in list(range(13, j["T"], 13)) + [j["T"]]]
    L += ["", "## Cek silang", "", "| Kode | Besaran | Cara 1 | Cara 2 | Selisih | Hasil |", "|---|---|---:|---:|---:|---|"]
    for b in cs:
        d = 0 if b["kode"] == "T-122b" else 2
        L.append(f"| {b['kode']} | {b['besaran']} | {idn(b['x1'], d)} | {idn(b['x2'], d)} | {idn(b['selisih'], 4)} | "
                 f"{'lolos' if b['lolos'] else 'gagal'} |")
    if xl:
        L.append(f"| T-122a/c Excel | Σ bobot / kumulatif akhir / durasi (rumus dihitung Excel) | {idn(xl['bobot'] * 100, 4)} % / "
                 f"{idn(xl['kum'] * 100, 4)} % / {xl['T']} mgg | 100 / 100 / {j['T']} | | "
                 f"{'lolos' if abs(xl['bobot'] - 1) < 1e-4 and abs(xl['kum'] - 1) < 1e-4 and xl['T'] == j['T'] else 'gagal'} |")
    L += ["", "Keluaran: `9 Jadwal dan Kurva S.xlsx`, `9 Gantt dan Kurva S.png/.pdf`, `9 Jadwal.xml` (ProjectLibre).", ""]
    keluar.write_text("\n".join(L), encoding="utf-8")
    return keluar


def main():
    j = jadwal()
    cs = cek_silang(j)
    for b in cs:
        print(b["kode"], round(b["x1"], 3), round(b["x2"], 3), round(b["selisih"], 3), "lolos" if b["lolos"] else "GAGAL")
    print("durasi", j["T"], "minggu;", [k["kode"] for k in j["kegiatan"] if k["kritis"]])
    gambar(j)
    tulis_xml(j)
    xl = None
    if "--tanpa-excel" not in sys.argv:
        path, sel = buat_excel(j)
        xl, err = cek_excel(path, sel)
        print("excel", xl, err)
    tulis_md(j, cs, xl)


if __name__ == "__main__":
    main()
