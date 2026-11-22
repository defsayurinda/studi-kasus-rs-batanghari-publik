"""Tahap 4: visualisasi 3D model analisis (gaya ETABS/RFEM) dari model OpenSeesPy `tahap4_model` konfigurasi K2.

Keluaran PNG (latar putih, render off-screen pyvista) di `04 Struktur Atas/Gambar/Analisis 3D/`:
01 model 3D, 02-04 ragam 1-3, 05a/05b deformasi gempa statik ekivalen X/Y, 06a/06b momen dan geser portal tipikal.
DATA SIMULASI; model dan angka sama dengan `4.3 Analisis Struktur.xlsx` (tidak ada hitungan baru).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pyvista as pv

sys.path.insert(0, str(Path(__file__).parent))
import tahap4_beban as tb  # noqa: E402
import tahap4_model as tm  # noqa: E402

pv.OFF_SCREEN = True
KELUAR = tm.KELUAR / "Gambar" / "Analisis 3D"
UKURAN = (3000, 2000)
CATATAN = "Model OpenSeesPy, data simulasi"
WARNA = {"Kolom": "#2b6cb0", "Balok": "#dd8a1f", "Inti geser": "#c0392b", "Tumpuan jepit": "#2f2f2f"}


def koma(x, d=2):
    return f"{x:.{d}f}".replace(".", ",")


# ------------------------------------------------------------------ geometri dari model yang sedang aktif di openseespy
def ambil_geometri(m):
    import openseespy.opensees as ops
    ele = []
    for tipe, daftar in (("kolom", m["kolom"]), ("balok", m["balok"]), ("inti", m["inti"])):
        for e in daftar:
            n1, n2 = ops.eleNodes(e["ele"])
            ele.append({**e, "tipe": tipe, "n": (n1, n2)})
    tags = sorted({n for e in ele for n in e["n"]})
    xyz = {n: np.array(ops.nodeCoord(n)) for n in tags}
    return ele, xyz


def medan(tags, fungsi):
    return {n: np.array(fungsi(n), dtype=float) for n in tags}


def dimensi_inti(nama):
    if nama.startswith("Ujung"):
        return tm.PANJANG_UJUNG, tb.DINDING_T
    return tm.UKURAN_INTI[nama.split()[0]]


# ------------------------------------------------------------------ mesh
def mesh_rangka(ele, xyz, u, skala, tipe, radius):
    """Garis kolom/balok (dua titik per elemen) -> tabung; skalar = |u| (titik)."""
    pts, sk, sel = [], [], []
    for e in (x for x in ele if x["tipe"] == tipe):
        for n in e["n"]:
            pts.append(xyz[n] + skala * u[n][:3])
            sk.append(np.linalg.norm(u[n][:3]))
        k = len(pts)
        sel += [2, k - 2, k - 1]
    pd = pv.PolyData(np.array(pts), lines=np.array(sel))
    pd["u"] = np.array(sk)
    return pd.tube(radius=radius, n_sides=8)


def mesh_inti(ele, xyz, u, skala):
    """Kotak inti per tingkat (8 titik sudut, perpindahan + rotasi ujung); skalar = |u| sudut."""
    pts, sk, sel = [], [], []
    for e in (x for x in ele if x["tipe"] == "inti"):
        dx, dy = dimensi_inti(e["nama"])
        sudut = [(-dx / 2, -dy / 2), (dx / 2, -dy / 2), (dx / 2, dy / 2), (-dx / 2, dy / 2)]
        for n in e["n"]:   # bawah lalu atas
            for rx, ry in sudut:
                th = u[n][3:]
                d = u[n][:3] + np.array([-th[2] * ry, th[2] * rx, th[0] * ry - th[1] * rx])
                pts.append(xyz[n] + np.array([rx, ry, 0.0]) + skala * d)
                sk.append(np.linalg.norm(d))
        k = len(pts) - 8
        sel += [8, k, k + 1, k + 2, k + 3, k + 4, k + 5, k + 6, k + 7]
    g = pv.UnstructuredGrid(np.array(sel), np.full(len(sel) // 9, pv.CellType.HEXAHEDRON), np.array(pts))
    g["u"] = np.array(sk)
    return g.extract_surface()


def tumpuan(xyz):
    ms = []
    for n, p in xyz.items():
        if abs(p[2]) < 1e-6:
            ms.append(pv.Cone(center=(p[0], p[1], -0.9), direction=(0, 0, 1), height=1.8, radius=1.1, resolution=4))
    return ms[0].merge(ms[1:]) if len(ms) > 1 else ms[0]


# ------------------------------------------------------------------ pemandangan
def pelat():
    p = pv.Plotter(off_screen=True, window_size=list(UKURAN))
    p.set_background("white")
    p.enable_anti_aliasing("ssaa")
    return p


def label_lantai(p, tk, xyz):
    x0 = min(v[0] for v in xyz.values())
    y0 = min(v[1] for v in xyz.values())
    lv = [("LT1", 0.0)] + [(t["lv"], t["z"]) for t in tk]
    pts = np.array([[x0 - 4, y0 - 4, z] for _, z in lv])
    p.add_point_labels(pts, [f"{n} (+{koma(tb.LEVEL[n])})" for n, _ in lv], font_size=22, text_color="black",
                       point_size=1, shape="rounded_rect", shape_color="white", shape_opacity=0.9, show_points=False,
                       always_visible=True)


def judul(p, teks):
    p.add_text(teks, position=(60, UKURAN[1] - 110), font_size=26, color="black")
    p.add_text(CATATAN, position=(UKURAN[0] - 560, 45), font_size=14, color="#555555")


def simpan(p, nama, kamera=None):
    if kamera:
        p.camera_position = kamera
    else:
        p.view_vector((0.9, -1.3, 0.55))
        p.reset_camera()
    p.camera.zoom(1.25 if not kamera else 1.2)
    KELUAR.mkdir(parents=True, exist_ok=True)
    p.screenshot(str(KELUAR / nama))
    p.close()
    return KELUAR / nama


def anotasi(lo, hi, n=6):
    return {float(v): koma(v, 2 if hi - lo < 100 else 0) for v in np.linspace(lo, hi, n)}


def gambar_kontur(ele, xyz, tk, u, skala, nama, teks, satuan, faktor_u=1.0, sub=None):
    p = pelat()
    umax = max(np.linalg.norm(v[:3]) for v in u.values()) * faktor_u
    kw = dict(scalars="u", cmap="jet", clim=[0, umax], show_scalar_bar=False)
    ug = {n: v.copy() for n, v in u.items()}
    meshes = [mesh_rangka(ele, xyz, ug, skala, "kolom", 0.28), mesh_rangka(ele, xyz, ug, skala, "balok", 0.2),
              mesh_inti(ele, xyz, ug, skala)]
    akt = []
    for g in meshes:
        g["u"] = g["u"] * faktor_u
        akt.append(p.add_mesh(g, **kw))
    # bayangan model awal (tanpa deformasi)
    p.add_mesh(mesh_rangka(ele, xyz, ug, 0.0, "kolom", 0.07), color="#bbbbbb", opacity=0.5)
    p.add_mesh(mesh_rangka(ele, xyz, ug, 0.0, "balok", 0.05), color="#bbbbbb", opacity=0.5)
    p.add_mesh(tumpuan(xyz), color=WARNA["Tumpuan jepit"])
    akt[0].mapper.lookup_table.annotations = anotasi(0, umax)
    p.add_scalar_bar(mapper=akt[0].mapper, title=satuan, n_labels=0, vertical=True, position_x=0.91, position_y=0.2,
                     height=0.6, width=0.05, title_font_size=22, label_font_size=20, color="black")
    label_lantai(p, tk, xyz)
    judul(p, teks)
    p.add_text(sub or "", position=(60, 45), font_size=16, color="black")
    return simpan(p, nama)


# ------------------------------------------------------------------ gambar 1: model
def gambar_model(ele, xyz, tk):
    p = pelat()
    nol = {n: np.zeros(6) for n in xyz}
    p.add_mesh(mesh_rangka(ele, xyz, nol, 0, "kolom", 0.28), color=WARNA["Kolom"])
    p.add_mesh(mesh_rangka(ele, xyz, nol, 0, "balok", 0.2), color=WARNA["Balok"])
    p.add_mesh(mesh_inti(ele, xyz, nol, 0), color=WARNA["Inti geser"])
    p.add_mesh(tumpuan(xyz), color=WARNA["Tumpuan jepit"])
    p.add_legend([[k, v] for k, v in WARNA.items()], bcolor="white", border=True, size=(0.17, 0.14), loc="upper right",
                 face="rectangle")
    label_lantai(p, tk, xyz)
    judul(p, "Model analisis 3D struktur atas (konfigurasi K2): kolom, balok, dan inti dinding geser")
    p.add_text("Satuan: m; tumpuan jepit di LT1 (+12,85); diafragma kaku per lantai", position="lower_left",
               font_size=16, color="black")
    return simpan(p, "01_model_3d.png")


# ------------------------------------------------------------------ gambar 6: portal tipikal
def pilih_portal(m):
    from collections import Counter
    c = Counter(e["y1"] for e in m["balok"] if e["arah"] == "X")
    inti_y = {v[1] for v in tm.PUSAT_INTI.values()}
    # portal terbanyak bentang yang tidak dekat inti
    skor = {y: n for y, n in c.items() if all(abs(y - yi) > 5 for yi in inti_y)}
    return max(skor, key=skor.get)


def gambar_portal(m, ele, xyz, tk, yp, nama, jenis):
    import openseespy.opensees as ops
    p = pelat()
    el = [e for e in ele if (e["tipe"] == "kolom" and abs(e["y"] - yp) < 1e-6)
          or (e["tipe"] == "balok" and e["arah"] == "X" and abs(e["y1"] - yp) < 1e-6)]
    gaya = {e["ele"]: np.array(ops.eleResponse(e["ele"], "localForce")) for e in el}
    # nilai penampang di ujung: M = (-My_i, My_j); V = Vz_j (linier)
    def nilai(e):
        f = gaya[e["ele"]]
        return (-f[4], f[10]) if jenis == "M" else (-f[2], -f[2])
    # kalibrasi sisi tarik: kolom dasar, beban +X -> tarik di sisi -X
    kd = [e for e in el if e["tipe"] == "kolom" and e["i"] == 1]
    kal = 1.0
    if jenis == "M":   # offset sisi tarik = kal*M*z_lokal; z_lokal kolom = +X; tumpuan beban +X: tarik di sisi -X
        kal = -np.sign(max((nilai(e)[0] for e in kd), key=abs))
    vmaks = max(abs(v) for e in el for v in nilai(e))
    off_maks = 3.2
    kuad_pts, kuad_val, kuad = [], [], []
    for e in el:
        a, b = (xyz[n] for n in e["n"])
        z = np.array([1.0, 0, 0]) if e["tipe"] == "kolom" else np.array([0, 0, 1.0])
        base = len(kuad_pts)
        for pt, v in zip((a, b), nilai(e)):
            kuad_pts += [pt, pt + kal * z * v / vmaks * off_maks]
            kuad_val += [v, v]
        kuad += [4, base, base + 1, base + 3, base + 2]
    s = pv.PolyData(np.array(kuad_pts), faces=np.array(kuad))
    s["v"] = np.array(kuad_val)
    akt = p.add_mesh(s, scalars="v", cmap="coolwarm", clim=[-vmaks, vmaks], show_edges=False, opacity=0.95,
                     show_scalar_bar=False)
    for e in el:
        a, b = (xyz[n] for n in e["n"])
        p.add_mesh(pv.Line(a, b), color="black", line_width=5)
    p.add_mesh(tumpuan({n: v for n, v in xyz.items() if abs(v[1] - yp) < 1e-6}), color=WARNA["Tumpuan jepit"])
    sat = "Momen lentur M (kN·m)" if jenis == "M" else "Gaya geser V (kN)"
    akt.mapper.lookup_table.annotations = anotasi(-vmaks, vmaks, 7)
    p.add_scalar_bar(title=sat, n_labels=0, vertical=True, position_x=0.91, position_y=0.2, height=0.6, width=0.05,
                     title_font_size=22, label_font_size=20, color="black", mapper=akt.mapper)
    x0 = min(xyz[n][0] for e in el for n in e["n"])
    lv = [("LT1", 0.0)] + [(t["lv"], t["z"]) for t in tk]
    p.add_point_labels(np.array([[x0 - 9, yp, z] for _, z in lv]), [f"{n} (+{koma(tb.LEVEL[n])})" for n, _ in lv],
                       font_size=22, text_color="black", point_size=1, shape="rounded_rect", shape_color="white",
                       shape_opacity=0.9, show_points=False, always_visible=True)
    # angka: ujung kolom dasar dan satu balok tengah per lantai
    lp, lt = [], []
    def tambah(e, ujung):
        a, b = (xyz[n] for n in e["n"])
        z = np.array([1.0, 0, 0]) if e["tipe"] == "kolom" else np.array([0, 0, 1.0])
        v = nilai(e)
        if jenis == "M":
            q = (a, b)[ujung]
            lp.append(q + kal * z * v[ujung] / vmaks * off_maks)
            lt.append(koma(v[ujung], 1))
        else:
            lp.append((a + b) / 2 + kal * z * v[0] / vmaks * off_maks)
            lt.append(koma(v[0], 1))
    for e in kd:
        tambah(e, 0)
    for lvl in sorted({e["lv"] for e in el if e["tipe"] == "balok"}):
        bl = sorted((e for e in el if e["tipe"] == "balok" and e["lv"] == lvl), key=lambda e: e["x1"])
        e = bl[len(bl) // 2]
        for u in ((0, 1) if jenis == "M" else (0,)):
            tambah(e, u)
    p.add_point_labels(np.array(lp), lt, font_size=18, text_color="black", point_size=1, shape="rounded_rect",
                       shape_color="white", shape_opacity=0.85, show_points=False, always_visible=True)
    nm = "Diagram momen lentur" if jenis == "M" else "Diagram gaya geser"
    judul(p, f"{nm}: portal tipikal as y = {koma(yp, 1)} m, gempa statik ekivalen arah X")
    p.add_text(f"{'M' if jenis == 'M' else 'V'} maks (mutlak) = {koma(vmaks, 1)} {'kN·m' if jenis == 'M' else 'kN'}"
               + ("; diagram di sisi tarik" if jenis == "M" else ""), position=(60, 45), font_size=16, color="black")
    return simpan(p, nama, kamera="xz")


# ------------------------------------------------------------------ utama
def buat_semua():
    import openseespy.opensees as ops
    hasil = {}
    # ragam
    rg = tm.ragam("K2", n=3)
    m = rg["model"]
    ele, xyz = ambil_geometri(m)
    tk = m["tk"]
    tags = list(xyz)
    tinggi = max(t["z"] for t in tk)
    hasil["T"] = rg["T"][:3]
    hasil["files"] = [gambar_model(ele, xyz, tk)]
    for j in (1, 2, 3):
        u = medan(tags, lambda n: ops.nodeEigenvector(n, j))
        mx = max(np.linalg.norm(v[:3]) for v in u.values())
        u = {n: v / mx for n, v in u.items()}
        k = int(np.argmax([rg["mx"][j - 1], rg["my"][j - 1], rg["mrz"][j - 1]]))
        dom = ["translasi arah X", "translasi arah Y", "torsi (rotasi sumbu Z)"][k]
        hasil["files"].append(gambar_kontur(
            ele, xyz, tk, u, 0.07 * tinggi, f"0{j + 1}_ragam_{j}.png",
            f"Ragam {j}: T = {koma(rg['T'][j - 1], 3)} s, {dom}", "Perpindahan relatif (-)",
            sub=f"Massa efektif: X {koma(100 * rg['mx'][j - 1], 1)} %, Y {koma(100 * rg['my'][j - 1], 1)} %, "
                f"Rz {koma(100 * rg['mrz'][j - 1], 1)} %; perpindahan relatif 1,00 digambar sebesar "
                f"{koma(0.07 * tinggi, 1)} m"))
    # gempa statik ekivalen
    for arah, nm in (("X", "05a_deformasi_gempa_X.png"), ("Y", "05b_deformasi_gempa_Y.png")):
        r = tm.elf_statik("K2", arah)
        mm = r["tk"]
        ele2, xyz2 = ambil_geometri(_model_aktif())
        u = medan(list(xyz2), lambda n: ops.nodeDisp(n))
        umax = max(np.linalg.norm(v[:3]) for v in u.values())
        skala = 0.06 * tinggi / umax
        hasil["umax_" + arah] = umax * 1000
        hasil["files"].append(gambar_kontur(
            ele2, xyz2, mm, u, skala, nm,
            f"Deformasi akibat gempa statik ekivalen arah {arah} (V = {koma(r['V'], 0)} kN)",
            "Perpindahan total (mm)", faktor_u=1000.0,
            sub=f"Skala perpindahan diperbesar {koma(skala, 0)}x; perpindahan maks {koma(umax * 1000, 1)} mm"))
        if arah == "X":
            yp = pilih_portal(_model_aktif())
            hasil["portal_y"] = yp
            for j, nama in (("M", "06a_momen_portal.png"), ("V", "06b_geser_portal.png")):
                hasil["files"].append(gambar_portal(_model_aktif(), ele2, xyz2, mm, yp, nama, j))
    return hasil


_AKTIF = {}


def _model_aktif():
    return _AKTIF["m"]


# elf_statik tidak mengembalikan struktur model; tangkap hasil bangun() terakhir
_bangun_asli = tm.bangun


def _bangun_catat(*a, **k):
    m = _bangun_asli(*a, **k)
    _AKTIF["m"] = m
    return m


os.environ["TANPA_CACHE"] = "1"   # perekam butuh model benar-benar dibangun, bukan hasil cache
tm.bangun = _bangun_catat

if __name__ == "__main__":
    h = buat_semua()
    print("T (s):", [round(t, 4) for t in h["T"]])
    for f in h["files"]:
        print(f)
