"""Langkah 3.9: model BIM LOD 200 (struktur + pondasi + gedung utilitas) dan validasi IFC.

Model struktur pra-dimensi 3.6 (RSTB-STR-T3-Pradimensi.bimc) dilengkapi di BIMCraft dengan: pelat lantai dasar
struktural dan sloof, pile cap dan tiang bor Ø800 opsi A (3.7, disetujui), dan struktur gedung utilitas + parkir
(3.5 opsi C). BIMCraft belum punya perintah tiang, jadi tiang dimodelkan sebagai kolom struktur bulat Ø800 lalu di
IFC diubah kelasnya menjadi IfcPile (PredefinedType BORED) dengan IfcOpenShell (ifcopenshell.api root.reassign_class).
Validasi: hierarki ruang IFC (proyek-situs-gedung-lantai), setiap elemen berada di lantai, Pset_RSTB_Umum dengan
RSTB_LOD 200 pada setiap elemen struktur, jumlah tiang = 3.7, volume IFC (ifcopenshell.util.shape) dicocokkan dengan
volume 3.6 dan anggapan 3.8. Model arsitektur massa 3.4 (IfcSpace) ikut divalidasi.
Ukuran gedung utilitas (kolom 600, balok 350 × 600, pelat 200), pelat lantai dasar 250, sloof 400 × 800 berlabel
[Asumsi] (Tahap 4/5 menghitung ulang). Disusun AI atas permintaan Defsa (19 Nov 2026); disetujui Defsa 19 Nov 2026.
"""
import math
from collections import Counter, defaultdict
from pathlib import Path

import tahap3_pondasi as fd
import tahap3_program as pr
import tahap3_struktur as st
import tahap3_zonasi as zn

AKAR = Path(__file__).resolve().parents[1]
KELUAR = AKAR / "03 Desain Konsep"
BERKAS = KELUAR / "3.9 Model BIM LOD 200.xlsx"
BIMC = AKAR / "model" / "RSTB-STR-T3-LOD200.bimc"
IFC = BIMC.with_suffix(".ifc")
LABEL = "DATA SIMULASI untuk studi kasus portofolio. Bukan data proyek nyata. Tidak untuk konstruksi."
LABEL_AI = "DIISI AI ATAS PERMINTAAN DEFSA (19 Nov 2026), sel hijau; disetujui Defsa 19 Nov 2026."
STATUS = "disetujui Defsa 19 Nov 2026"

LT1 = 12850.0  # mm, peil lantai (3.3)
HALAMAN = 12050.0
TEBAL_CAP = 1200.0
D_TIANG = 800.0
JARAK_TIANG = 3 * D_TIANG / 1000  # m (3D)
TEPI_CAP = D_TIANG / 2000 + 0.4  # m dari as tiang ke tepi cap [Asumsi]
PANJANG_TIANG = fd.kapasitas("BOR-800")["panjang"] * 1000  # mm dari bawah cap
DASAR_CAP = HALAMAN - TEBAL_CAP  # bawah cap (3.7: panjang tiang dari halaman - 1,2 m)
PELAT_LT1, SLOOF = 250, (400, 800)  # [Asumsi]
GU_KOLOM, GU_BALOK, GU_PELAT = 600, (350, 600), 200  # [Asumsi]
GU_TINGKAT = ["LT1", "LT2", "LT3", "LT4", "LT5"]  # LT5 = atap gedung utilitas + parkir
INTI_LIF = (54.0, 39.0)
TOLERANSI_VOLUME = 0.10  # T-50: volume IFC vs 3.6 per unsur struktur atas, ditetapkan sebelum dihitung


def pola(n):
    """Posisi tiang relatif (m) dan ukuran cap (m) untuk n tiang Ø800 jarak 3D (pola 3.7)."""
    p = fd._pola_kelompok(n, JARAK_TIANG)
    xs, ys = [a for a, _ in p], [b for _, b in p]
    return p, (max(xs) - min(xs) + 2 * TEPI_CAP, max(ys) - min(ys) + 2 * TEPI_CAP)


def kelompok_tiang():
    """Semua kelompok (x, y, n, sudut) gedung utama, inti, dan gedung utilitas (opsi A)."""
    o = fd.opsi("A")
    hasil = [(c["x"], c["y"], c["n"], 0) for c in o["utama"] + o["gu"]]
    hasil += [(x, y, 6, 90) for x, y in st.INTI + [INTI_LIF]]  # 6 tiang per inti (3.7 [Asumsi])
    return hasil


def posisi_tiang():
    pos = []
    for x, y, n, sudut in kelompok_tiang():
        p, _ = pola(n)
        for dx, dy in p:
            if sudut:
                dx, dy = -dy, dx
            pos.append((x + dx, y + dy))
    return pos


def _mm(x, y):
    return [round(x * 1000), round(y * 1000)]


def _kotak(x0, x1, y0, y1):
    return [_mm(x0, y0), _mm(x1, y0), _mm(x1, y1), _mm(x0, y1)]


def bangun_bim(status=STATUS):
    from bimcraft import Sesi, tampilkan

    ids = defaultdict(list)

    def catat(kunci, r):
        if isinstance(r, dict):
            ids[kunci] += [i for i in (r.get("ids") or [r.get("id")]) if isinstance(i, int)]

    with Sesi(st.BIMC) as b:
        b.cmd("project_info", {"status": "Desain Konsep - model struktur LOD 200 (langkah 3.9)"})
        b.cmd("type", {"category": "structuralcolumn", "name": "TB-800-fc30", "width": D_TIANG, "depth": D_TIANG,
                       "round": True, "material": "Beton fc 30 S2"})
        for n in sorted({g[2] for g in kelompok_tiang()}):
            _, (w, d) = pola(n)
            b.cmd("type", {"category": "footing", "name": f"PC-{n}T", "width": round(w * 1000), "depth": round(d * 1000),
                           "material": "Beton fc 30 S2"})
        b.cmd("type", {"category": "floor", "name": f"PL-{PELAT_LT1}-fc30-LT1",
                       "layers": [{"function": "structure", "material": "Beton fc 30 S2", "thickness": PELAT_LT1}]})
        b.cmd("type", {"category": "beam", "name": "SL-{}x{}-fc30".format(*SLOOF), "width": SLOOF[0], "depth": SLOOF[1],
                       "material": "Beton fc 30 S2"})
        b.cmd("type", {"category": "structuralcolumn", "name": f"KL-{GU_KOLOM}x{GU_KOLOM}-fc35", "width": GU_KOLOM,
                       "depth": GU_KOLOM, "material": "Beton fc 35 S2"})
        b.cmd("type", {"category": "beam", "name": "BL-{}x{}-fc30".format(*GU_BALOK), "width": GU_BALOK[0],
                       "depth": GU_BALOK[1], "material": "Beton fc 30 S2"})
        b.cmd("type", {"category": "floor", "name": f"PL-{GU_PELAT}-fc30-GU",
                       "layers": [{"function": "structure", "material": "Beton fc 30 S2", "thickness": GU_PELAT}]})
        # pile cap dan tiang
        for x, y, n, sudut in kelompok_tiang():
            catat("cap", b.cmd("footing", {"at": _mm(x, y), "type": f"PC-{n}T", "thickness": TEBAL_CAP,
                                           "offset": round(HALAMAN - LT1), "angle": sudut, "level": "LT1"}))
        for x, y in posisi_tiang():
            catat("tiang", b.cmd("structural_column", {
                "at": _mm(x, y), "type": "TB-800-fc30", "level": "LT1",
                "base_offset": round(DASAR_CAP - PANJANG_TIANG - LT1), "height": round(PANJANG_TIANG)}))
        # pelat lantai dasar dan sloof: podium dan gedung utilitas
        pd = pr.MASSA["PODIUM"]
        gx, gy = fd.GU_GRID_X, fd.GU_GRID_Y
        for kotak in (_kotak(pd["x"][0] - 0.5, pd["x"][1] + 0.5, pd["y"][0] - 0.5, pd["y"][1] + 0.5),
                      _kotak(gx[0] - 0.5, gx[-1] + 0.5, gy[0] - 0.5, gy[-1] + 0.5)):
            catat("pelat_lt1", b.cmd("floor", {"boundary": kotak, "level": "LT1", "type": f"PL-{PELAT_LT1}-fc30-LT1",
                                               "structural": True}))
        sl = "SL-{}x{}-fc30".format(*SLOOF)
        for xs, ys in ((st.GRID_X, st.GRID_Y), (gx, gy)):
            for y in ys:
                catat("sloof", b.cmd("beam", {"points": [_mm(xs[0], y), _mm(xs[-1], y)], "type": sl, "level": "LT1"}))
            for x in xs:
                catat("sloof", b.cmd("beam", {"points": [_mm(x, ys[0]), _mm(x, ys[-1])], "type": sl, "level": "LT1"}))
        # gedung utilitas + parkir
        for x in gx:
            for y in gy:
                for a, c in zip(GU_TINGKAT[:-1], GU_TINGKAT[1:]):
                    catat("gu", b.cmd("structural_column", {"at": _mm(x, y), "type": f"KL-{GU_KOLOM}x{GU_KOLOM}-fc35",
                                                            "level": a, "top_level": c}))
        bl = "BL-{}x{}-fc30".format(*GU_BALOK)
        for lv in GU_TINGKAT[1:]:
            for y in gy:
                catat("gu", b.cmd("beam", {"points": [_mm(gx[0], y), _mm(gx[-1], y)], "type": bl, "level": lv}))
            for x in gx:
                catat("gu", b.cmd("beam", {"points": [_mm(x, gy[0]), _mm(x, gy[-1])], "type": bl, "level": lv}))
            catat("gu", b.cmd("floor", {"boundary": _kotak(gx[0] - 0.5, gx[-1] + 0.5, gy[0] - 0.5, gy[-1] + 0.5),
                                        "level": lv, "type": f"PL-{GU_PELAT}-fc30-GU", "structural": True}))
        sumber = {"cap": "pile cap opsi A (3.7); tebal 1200, tepi 0,8 m [Asumsi]",
                  "tiang": "tiang bor Ø800 opsi A (3.7) ke U7; kelas IFC IfcPile",
                  "pelat_lt1": "pelat lantai dasar struktural 250 [Asumsi]", "sloof": "sloof 400 × 800 [Asumsi]",
                  "gu": "gedung utilitas + parkir (3.5 opsi C); ukuran [Asumsi]"}
        for k, daftar in ids.items():
            b.cmd("modify", {"ids": daftar, "params": {"RSTB_Tahap": "3", "RSTB_LOD": "200", "RSTB_Status": status,
                                                      "RSTB_KelasPaparan": "S2" if k in ("cap", "tiang") else "-",
                                                      "RSTB_Sumber": sumber[k]}})
        b.simpan(BIMC)
        b.simpan(IFC)
    ubah_kelas_tiang(IFC)
    tampilkan(BIMC)
    return {k: len(v) for k, v in ids.items()}


def ubah_kelas_tiang(path=IFC):
    """IfcColumn bertipe TB-800 → IfcPile BORED (BIMCraft belum punya kategori tiang)."""
    import ifcopenshell
    import ifcopenshell.api
    import ifcopenshell.util.element as ue

    f = ifcopenshell.open(str(path))
    # mengubah kelas tipe ikut mengubah semua occurrence-nya (IfcColumn → IfcPile)
    for t in list(f.by_type("IfcColumnType")):
        if (t.Name or "").startswith("TB-"):
            ifcopenshell.api.run("root.reassign_class", f, product=t, ifc_class="IfcPileType",
                                 predefined_type="BORED")
    for e in list(f.by_type("IfcColumn")):  # bila ada tiang tanpa tipe
        if (e.ObjectType or "").startswith("TB-") and ue.get_type(e) is None:
            ifcopenshell.api.run("root.reassign_class", f, product=e, ifc_class="IfcPile", predefined_type="BORED")
    for p in f.by_type("IfcPile"):
        p.PredefinedType = "BORED"
    n = len(f.by_type("IfcPile"))
    f.write(str(path))
    return n


# ------------------------------------------------------------------ validasi IFC
def _pset(e, nama="Pset_RSTB_Umum"):
    import ifcopenshell.util.element as ue
    return ue.get_psets(e).get(nama, {})


def _lantai(e):
    import ifcopenshell.util.element as ue
    c = ue.get_container(e)
    return c.Name if c is not None and c.is_a("IfcBuildingStorey") else None


def volume_elemen(f):
    """Volume (m³) dan x pusat (m) per elemen dari geometri IFC (ifcopenshell.geom + util.shape; keluaran SI)."""
    import ifcopenshell.geom
    import ifcopenshell.util.shape as us

    s = ifcopenshell.geom.settings()
    hasil = {}
    it = ifcopenshell.geom.iterator(s, f, include=f.by_type("IfcElement"))
    if it.initialize():
        while True:
            sh = it.get()
            v = us.get_shape_vertices(sh, sh.geometry)
            hasil[sh.id] = (us.get_volume(sh.geometry), float(v[:, 0].mean()) if len(v) else 0.0)
            if not it.next():
                break
    return hasil


def validasi(path=IFC, wajib_lod=True):
    import ifcopenshell

    f = ifcopenshell.open(str(path))
    el = f.by_type("IfcElement")
    cek = []

    def tambah(butir, lolos, ket):
        cek.append({"butir": butir, "lolos": bool(lolos), "ket": ket})

    tambah("Skema IFC4", f.schema == "IFC4", f.schema)
    tambah("Satu IfcProject, IfcSite, IfcBuilding",
           len(f.by_type("IfcProject")) == 1 and len(f.by_type("IfcSite")) == 1 and len(f.by_type("IfcBuilding")) == 1,
           f"{len(f.by_type('IfcProject'))}/{len(f.by_type('IfcSite'))}/{len(f.by_type('IfcBuilding'))}")
    lantai = {s.Name: s.Elevation for s in f.by_type("IfcBuildingStorey")}
    tambah("Lantai LT1-ATAP sesuai BEP 3.1", all(k in lantai for k in ("LT1", "LT2", "LT3", "LT4", "LT5", "LT6", "ATAP")),
           ", ".join(f"{k} {v / 1000:.2f}".replace(".", ",") for k, v in lantai.items()))
    tanpa = [e for e in el if _lantai(e) is None]
    tambah("Setiap elemen berada di lantai", not tanpa, f"{len(tanpa)} elemen tanpa lantai dari {len(el)}")
    if wajib_lod:
        tanpa_p = [e for e in el if str(_pset(e).get("RSTB_LOD", "")) != "200"]
        tambah("Pset_RSTB_Umum RSTB_LOD = 200", not tanpa_p, f"{len(tanpa_p)} elemen tidak lengkap")
    guid = [e.GlobalId for e in f.by_type("IfcRoot")]
    tambah("GlobalId unik", len(guid) == len(set(guid)), f"{len(guid)} entitas")
    kosong = [k for k in lantai if not any(_lantai(e) == k for e in el)]
    tambah("Lantai tanpa elemen", not [k for k in kosong if k != "B1"],
           ("kosong: " + ", ".join(kosong) + (" (B1 sisa template; basement ditolak 3.5)" if "B1" in kosong else ""))
           if kosong else "tidak ada")
    return {"cek": cek, "kelas": Counter(e.is_a() for e in el), "lolos": all(c["lolos"] for c in cek), "file": f}


GU_X_MIN = (pr.MASSA["PODIUM"]["x"][1] + fd.GU_GRID_X[0]) / 2  # m, batas gedung utama / gedung utilitas


def volume_per_kelompok(f):
    """Volume IFC (m³) per kelompok pembanding."""
    import ifcopenshell.util.element as ue

    vol = volume_elemen(f)
    g = defaultdict(float)
    n = Counter()
    for e in f.by_type("IfcElement"):
        v, x = vol.get(e.id(), (0.0, 0.0))
        t = ue.get_type(e)
        nama = (t.Name if t else e.ObjectType) or ""
        lv = _lantai(e)
        if e.is_a("IfcPile"):
            k = "tiang"
        elif e.is_a("IfcFooting"):
            k = "pile cap"
        elif nama.startswith(("SL-", "PL-250")) or (lv == "LT1" and e.is_a("IfcSlab")):
            k = "pelat LT1 + sloof"
        elif x >= GU_X_MIN:
            k = "gedung utilitas"
        elif e.is_a("IfcColumn"):
            k = "kolom"
        elif e.is_a("IfcBeam"):
            k = "balok"
        elif e.is_a("IfcSlab"):
            k = "pelat"
        elif e.is_a("IfcWall"):
            k = "dinding"
        else:
            k = e.is_a()
        g[k] += v
        n[k] += 1
    return dict(g), dict(n)


def pembanding(f):
    """Volume IFC vs 3.6 (struktur atas) dan anggapan 3.8; kembalikan baris pembanding."""
    g, n = volume_per_kelompok(f)
    v36 = st.volume("GANDA")
    h_b = st.PRA["GANDA"]["balok"][1]
    n_tiang = len(posisi_tiang())
    luas_tiang = math.pi * (D_TIANG / 2000) ** 2
    baris = [
        ("kolom", g.get("kolom", 0), v36["kolom"], "3.6 tinggi bersih per tingkat"),
        ("balok", g.get("balok", 0), v36["balok"] * h_b / (h_b - st.PRA["GANDA"]["pelat"]),
         "3.6 dikembalikan ke tinggi penuh (3.6 memotong bagian setebal pelat)"),
        ("pelat", g.get("pelat", 0), v36["pelat"], "3.6 luas massa × tebal"),
        ("dinding", g.get("dinding", 0), v36["dinding"], "3.6 keliling inti × tinggi × 0,75"),
        ("tiang", g.get("tiang", 0), n_tiang * luas_tiang * PANJANG_TIANG / 1000, "jumlah 3.7 × π D²/4 × panjang"),
    ]
    return [{"unsur": u, "ifc": a, "acuan": b, "selisih": (a / b - 1) if b else None, "dasar": d} for u, a, b, d in baris], g, n


def tambahan_38(g):
    """Unsur yang di 3.8 masih anggapan kasar: pelat lantai dasar + sloof, gedung utilitas, pile cap."""
    import tahap3_biaya as bi
    sn = bi.struktur_nyata()["item"]
    return [
        {"unsur": "pelat LT1 + sloof", "ifc": g.get("pelat LT1 + sloof", 0), "acuan": sn[2][1],
         "dasar": "3.8: 0,30 m³/m² [Asumsi]; model: pelat 250 + sloof 400 × 800 pada semua as"},
        {"unsur": "gedung utilitas", "ifc": g.get("gedung utilitas", 0), "acuan": sn[1][1],
         "dasar": "3.8: rasio SRPMK 3.6 × luas"},
        {"unsur": "pile cap", "ifc": g.get("pile cap", 0), "acuan": len(posisi_tiang()) * 4.5,
         "dasar": "3.8: 4,5 m³ per tiang; model: ukuran cap per pola 3.7"},
    ]


def ringkasan():
    import ifcopenshell
    v = validasi(IFC)
    va = validasi(zn.IFC, wajib_lod=False)
    rows, g, n = pembanding(v["file"])
    fa = ifcopenshell.open(str(zn.IFC))
    return {"lolos": v["lolos"], "kelas": v["kelas"], "pembanding": rows, "volume": g, "jumlah": n,
            "ars_lolos": va["lolos"], "ars_kelas": va["kelas"], "ruang": len(fa.by_type("IfcSpace")),
            "n_tiang_3_7": fd.opsi("A")["n_utama"] + fd.opsi("A")["n_gu"]}


def fmt(v, d=2):
    s = f"{v:,.{d}f}"
    return s.replace(",", "#").replace(".", ",").replace("#", ".")


# ------------------------------------------------------------------ Excel
def buat_excel(keluar=BERKAS):
    import openpyxl

    from format_dokumen import AI, Lembar, set_font_bawaan

    v = validasi(IFC)
    va = validasi(zn.IFC, wajib_lod=False)
    rows, g, n = pembanding(v["file"])
    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)
    lb = Lembar(wb.create_sheet("Petunjuk"), 1, "Petunjuk model BIM LOD 200 (langkah 3.9)", [6, 120])
    lb.catatan(LABEL + " " + LABEL_AI)
    lb.kosong()
    lb.tabel(["No", "Petunjuk"], [[i + 1, s] for i, s in enumerate([
        f"Model struktur: model/{BIMC.name} (BIMCraft) dan {IFC.name} (IFC4). Model arsitektur massa: "
        f"model/{zn.IFC.name} (3.4). Buka dengan BUKA BIMCRAFT.cmd atau penampil IFC mana pun.",
        "Isi LOD 200 (BEP 3.1): grid, lantai, kolom, balok, pelat, dinding inti sistem ganda (3.6); pelat lantai dasar "
        "dan sloof; pile cap dan tiang bor Ø800 opsi A (3.7); struktur gedung utilitas + parkir (3.5 opsi C).",
        "Tiang dimodelkan sebagai kolom bulat di BIMCraft lalu diubah ke IfcPile (BORED) dengan IfcOpenShell.",
        "Validasi dengan IfcOpenShell: hierarki ruang, elemen di lantai, Pset_RSTB_Umum RSTB_LOD 200, GlobalId unik.",
        f"Volume IFC dari geometri (ifcopenshell.util.shape) dibanding volume 3.6 dan anggapan 3.8; toleransi "
        f"{TOLERANSI_VOLUME:.0%} ditetapkan sebelum dihitung (T-50). Selisih yang berasal dari cara hitung dijelaskan.",
        "Ukuran gedung utilitas, pelat lantai dasar, sloof, dan tepi pile cap [Asumsi]; dihitung ulang di Tahap 4-6.",
    ])], rata=list("cl"))

    lb = Lembar(wb.create_sheet("Isi Model"), 2, "Isi model per kelas IFC", [6, 30, 14, 60])
    lb.catatan(LABEL)
    ket = {"IfcColumn": "kolom gedung utama + gedung utilitas", "IfcBeam": "balok + sloof", "IfcSlab": "pelat",
           "IfcWall": "dinding inti sistem ganda", "IfcFooting": "pile cap", "IfcPile": "tiang bor Ø800"}
    lb.tabel(["No", "Kelas IFC", "Jumlah", "Keterangan"],
             [[i + 1, k, c, ket.get(k, "")] for i, (k, c) in enumerate(sorted(v["kelas"].items()))],
             rata=list("clcl"), fill_kolom={2: AI})
    lb.kosong()
    lb.bagian("B", "Model arsitektur massa (3.4)")
    lb.tabel(["No", "Kelas IFC", "Jumlah", "Keterangan"],
             [[i + 1, k, c, ""] for i, (k, c) in enumerate(sorted(va["kelas"].items()))] +
             [[len(va["kelas"]) + 1, "IfcSpace", len(va["file"].by_type("IfcSpace")), "ruang bernama (zonasi 3.4)"]],
             rata=list("clcl"), fill_kolom={2: AI}, beku=False)

    lb = Lembar(wb.create_sheet("Validasi"), 3, "Validasi IFC (IfcOpenShell)", [6, 16, 44, 10, 70])
    lb.catatan(LABEL)
    data = [[i + 1, "Struktur", c["butir"], "Lolos" if c["lolos"] else "Gagal", c["ket"]] for i, c in enumerate(v["cek"])]
    data += [[len(data) + i + 1, "Arsitektur", c["butir"], "Lolos" if c["lolos"] else "Gagal", c["ket"]]
             for i, c in enumerate(va["cek"])]
    n_t = len(posisi_tiang())
    n37 = fd.opsi("A")["n_utama"] + fd.opsi("A")["n_gu"]
    data.append([len(data) + 1, "Struktur", "Jumlah tiang = 3.7 opsi A", "Lolos" if g and n.get("tiang") == n37 else "Gagal",
                 f"IFC {n.get('tiang', 0)}, rencana {n_t}, 3.7 {n37}"])
    lb.tabel(["No", "Model", "Butir", "Hasil", "Keterangan"], data, rata=list("cclcl"), fill_kolom={3: AI})

    lb = Lembar(wb.create_sheet("Volume"), 4, "Volume IFC terhadap 3.6 dan 3.8", [6, 20, 14, 14, 12, 12, 50])
    lb.catatan(LABEL + f" Toleransi {TOLERANSI_VOLUME:.0%} (T-50) untuk unsur struktur atas.")
    h, a, z = lb.tabel(["No", "Unsur", "IFC (m³)", "Acuan (m³)", "Selisih", "Hasil", "Dasar acuan"],
                       [[i + 1, r["unsur"], r["ifc"], r["acuan"], r["selisih"], _hasil(r), r["dasar"]]
                        for i, r in enumerate(rows)],
                       rata=list("clccccl"), fmt=[None, None, "#,##0", "#,##0", "0.0%", None, None],
                       fill_kolom={2: AI, 4: AI})
    c2, c3, c4 = lb.kol(2), lb.kol(3), lb.kol(4)
    for rr in range(a, z + 1):
        lb.ws[f"{c4}{rr}"] = f"=IF({c3}{rr}=0,\"-\",{c2}{rr}/{c3}{rr}-1)"
    lb.kosong()
    lb.tabel(["No", "Unsur tambahan", "IFC (m³)", "3.8 (m³)", "Selisih", "Hasil", "Keterangan"],
             [[i + 1, r["unsur"], r["ifc"], r["acuan"], r["ifc"] / r["acuan"] - 1, "Info", r["dasar"]]
              for i, r in enumerate(tambahan_38(g))],
             rata=list("clccccl"), fmt=[None, None, "#,##0", "#,##0", "0.0%", None, None], fill_kolom={2: AI, 4: AI},
             beku=False)
    wb.save(keluar)
    return keluar


def _hasil(r):
    if r["selisih"] is None:
        return "-"
    if r["unsur"] in ("kolom", "balok", "pelat", "dinding", "tiang"):
        return "Lolos" if abs(r["selisih"]) <= TOLERANSI_VOLUME else "Dijelaskan"
    return "Info"


ISOMETRI = KELUAR / "Gambar" / "3.9 Model LOD 200 isometri.png"


def gambar_isometri(path=IFC, keluar=ISOMETRI):
    """Tampak isometri model IFC (geometri ifcopenshell, matplotlib) untuk bahan presentasi 3.10."""
    import ifcopenshell
    import ifcopenshell.geom
    import matplotlib
    import numpy as np
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    f = ifcopenshell.open(str(path))
    s = ifcopenshell.geom.settings()
    s.set("use-world-coords", True)
    warna = {"IfcPile": "0.55", "IfcFooting": "0.45", "IfcSlab": "0.85", "IfcWall": "0.6", "IfcColumn": "0.35",
             "IfcBeam": "0.5"}
    poli, isi = [], []
    it = ifcopenshell.geom.iterator(s, f, include=f.by_type("IfcElement"))
    if it.initialize():
        while True:
            sh = it.get()
            v = np.array(sh.geometry.verts).reshape(-1, 3)
            fc = np.array(sh.geometry.faces).reshape(-1, 3)
            poli += [v[t] for t in fc]
            isi += [warna.get(f.by_id(sh.id).is_a(), "0.6")] * len(fc)
            if not it.next():
                break
    fig = plt.figure(figsize=(12, 8), dpi=150)
    ax = fig.add_subplot(projection="3d")
    ax.add_collection3d(Poly3DCollection(poli, facecolors=isi, edgecolors="none", linewidths=0))
    semua = np.vstack(poli)
    mn, mx = semua.min(0), semua.max(0)
    ax.set_xlim(mn[0], mx[0])
    ax.set_ylim(mn[1], mx[1])
    ax.set_zlim(mn[2], mx[2])
    ax.set_box_aspect(mx - mn)
    ax.view_init(elev=18, azim=-60)
    ax.set_axis_off()
    plt.tight_layout()
    plt.savefig(keluar, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return keluar


def buat():
    hasil = bangun_bim()
    buat_excel()
    gambar_isometri()
    return hasil


if __name__ == "__main__":
    import sys
    if "--bangun" in sys.argv:
        print(bangun_bim())
    r = ringkasan()
    print("lolos", r["lolos"], dict(r["kelas"]), "ars", r["ars_lolos"], r["ruang"], "ruang")
    for b in r["pembanding"]:
        print(b)
    print({k: round(v, 1) for k, v in r["volume"].items()}, r["jumlah"])
