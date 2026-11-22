"""Model konsep gabungan Tahap 3 di BIMCraft: struktur LOD 200 + arsitektur (dinding luar, jendela, ruang, halaman).

Arahan Defsa 19 Nov 2026: apa yang dibuat di BIMCraft harus jadi model utuh yang bisa dilihat 3D dan dilanjutkan
manual. Model ini membuka model struktur 3.9 (RSTB-STR-T3-LOD200.bimc) lalu menambahkan, dengan tipe dan level asli
BIMCraft:
- dinding luar bata ringan 150 di podium, menara, dan gedung utilitas + parkir;
- jendela 5,0 × 2,4 m di tengah tiap bentang 8 m (bukaan ±35 %, rekayasa nilai V4 yang disetujui di rapat 3.10);
- pemisah ruang dan ruang bernama per zona (zonasi 3.4), ruang utilitas dan parkir;
- halaman urugan +12,05 di luar bangunan dan di luar ruang sempadan (3.2, 3.3).
Lalu menyimpan view 3D bernama dan gambar tampaknya. Keluaran: model/RSTB-T3-Konsep.bimc dan .ifc (tiang → IfcPile).
Disusun AI atas permintaan Defsa (19 Nov 2026); disetujui Defsa 19 Nov 2026.
"""
from pathlib import Path

import tahap3_basement as bs
import tahap3_bim as bm
import tahap3_program as pr
import tahap3_tapak as tp
import tahap3_zonasi as zn

AKAR = Path(__file__).resolve().parents[1]
BIMC = AKAR / "model" / "RSTB-T3-Konsep.bimc"
IFC = BIMC.with_suffix(".ifc")
GAMBAR_3D = AKAR / "03 Desain Konsep" / "Gambar" / "3.11 Model Konsep 3D.png"
STATUS = "disetujui Defsa 19 Nov 2026"
JENDELA = (5000, 2400, 900)  # lebar, tinggi, ambang (mm) [Asumsi; bukaan ±35 % sesuai V4]
VIEW_3D = "3D KONSEP TENGGARA"
KAMERA = {"eye": [190000, -90000, 95000], "target": [70000, 50000, 18000], "lens": 35, "name": VIEW_3D}


def _mm(x, y):
    return [round(x * 1000), round(y * 1000)]


def _kotak(x0, x1, y0, y1):
    return [_mm(x0, y0), _mm(x1, y0), _mm(x1, y1), _mm(x0, y1)]


def massa_dinding():
    """(nama, x0, x1, y0, y1, [(level bawah, level atas)]) dinding luar tiap massa."""
    pd, mn = pr.MASSA["PODIUM"], pr.MASSA["MENARA"]
    gu = bs.GEDUNG_UP
    return [
        ("PODIUM", *pd["x"], *pd["y"], [("LT1", "LT2"), ("LT2", "LT3"), ("LT3", "LT4")]),
        ("MENARA", *mn["x"], *mn["y"], [("LT4", "LT5"), ("LT5", "LT6"), ("LT6", "ATAP")]),
        ("GU", *gu["x"], *gu["y"], [("LT1", "LT2")]),  # dek parkir LT2-LT4 terbuka (ventilasi alami)
    ]


def bukaan_per_sisi(panjang):
    """Offset (mm, dari awal sisi) pusat jendela: tengah tiap bentang ±8 m sepanjang sisi."""
    n = max(1, round(panjang / 8000))
    b = panjang / n
    return [round(b * (i + 0.5)) for i in range(n)]


def bangun(status=STATUS):
    from bimcraft import Sesi, tampilkan

    jendela = False  # dibangun dengan CLI 0.12.0; hasilnya ditampilkan di jendela 0.11.0 lewat tampilkan()

    ids = []

    def catat(r):
        if isinstance(r, dict):
            ids.extend(i for i in (r.get("ids") or [r.get("id")]) if isinstance(i, int))
        return r

    with (Sesi(jendela=True) if jendela else Sesi(bm.BIMC)) as b:
        if jendela:
            b.buka(bm.BIMC)
        b.cmd("project_info", {"status": "Desain Konsep - model gabungan struktur + arsitektur (langkah 3.11)"})
        w, h, sill = JENDELA
        b.cmd("type", {"category": "window", "name": f"JD-{w}x{h}", "width": w, "height": h, "sill": sill})
        b.cmd("type", {"category": "floor", "name": "HL-300-Urugan",
                       "layers": [{"function": "structure", "material": "Bata ringan", "thickness": 300}]})
        # dinding luar + jendela
        for nama, x0, x1, y0, y1, tingkat in massa_dinding():
            sisi = [((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))]
            for bawah, atas in tingkat:
                for a, c in sisi:
                    r = catat(b.cmd("wall", {"points": [_mm(*a), _mm(*c)], "type": "DD-150-Bata", "level": bawah,
                                             "top_level": atas}))
                    wid = (r.get("ids") or [r.get("id")])[0]
                    panjang = abs(c[0] - a[0]) * 1000 + abs(c[1] - a[1]) * 1000
                    for off in bukaan_per_sisi(panjang):
                        b.cmd("window", {"wall": wid, "offset": off, "type": f"JD-{w}x{h}"})
        # ruang per zona
        rencana = [(lt, lt) for lt in ("LT1", "LT2", "LT3")] + [("LT4-LT6", lt) for lt in ("LT4", "LT5", "LT6")]
        for kunci, lt in rencana:
            inti = [(cx - 2.6, cy - 3.6, cx + 2.6, cy + 3.6) for cx, cy in zn.TANGGA
                    if not (kunci == "LT4-LT6" and cy > 51)] + [(zn.LIF[0] - .8, zn.LIF[2] - .8, zn.LIF[1] + .8,
                                                                 zn.LIF[3] + .8)]
            for nama, x0, x1, y0, y1, _ in zn.ZONA[kunci] + zn.KOSONG.get(kunci, []):
                b.cmd("room_separator", {"points": _kotak(x0, x1, y0, y1), "level": lt, "closed": True})
                cx, cy, _, _ = zn.tempat_label(nama, x0, x1, y0, y1, 1, inti)
                catat(b.cmd("room", {"point": _mm(cx, cy), "level": lt, "name": nama.replace(",", ""),
                                     "number": f"{lt}-{len(ids) % 1000:03d}"}))
        gu = bs.GEDUNG_UP
        for i, lt in enumerate(("LT1", "LT2", "LT3", "LT4")):
            b.cmd("room_separator", {"points": _kotak(*gu["x"], *gu["y"]), "level": lt, "closed": True})
            catat(b.cmd("room", {"point": _mm(sum(gu["x"]) / 2, sum(gu["y"]) / 2), "level": lt,
                                 "name": "UTILITAS MEP" if lt == "LT1" else "PARKIR MOBIL", "number": f"GU-{i + 1:02d}"}))
        # halaman urugan +12,05: persil di utara ruang sempadan, berlubang di tapak bangunan
        y_s = tp.ruang_sempadan().bounds[3]
        pd = pr.MASSA["PODIUM"]
        lubang = [_kotak(pd["x"][0] - 0.5, pd["x"][1] + 0.5, pd["y"][0] - 0.5, pd["y"][1] + 0.5),
                  _kotak(gu["x"][0] - 0.5, gu["x"][1] + 0.5, gu["y"][0] - 0.5, gu["y"][1] + 0.5)]
        catat(b.cmd("floor", {"boundary": _kotak(0, 140, y_s, 90), "openings": lubang, "level": "LT1",
                              "type": "HL-300-Urugan", "offset": round((bm.HALAMAN - bm.LT1))}))
        b.cmd("modify", {"ids": ids, "params": {"RSTB_Tahap": "3", "RSTB_LOD": "200", "RSTB_Status": status,
                                                "RSTB_KelasPaparan": "-",
                                                "RSTB_Sumber": "arsitektur konsep 3.4/3.10/3.11 [Asumsi ukuran jendela]"}})
        # view 3D bernama dari tenggara (sisi sungai dan IGD)
        b.cmd("camera", KAMERA)
        b.cmd("visual_style", {"view": VIEW_3D, "style": "shaded"})
        b.cmd("render", {"view": VIEW_3D, "path": str(GAMBAR_3D), "width": 2400, "height": 1500})
        b.simpan(BIMC)
        b.simpan(IFC)
    bm.ubah_kelas_tiang(IFC)
    tampilkan(BIMC, KAMERA)  # juga membuat model/RSTB-T3-Konsep-v0.11.bimc untuk jendela BIMCraft 0.11.0
    return {"elemen": len(ids), "bimc": BIMC, "ifc": IFC, "png": GAMBAR_3D}


if __name__ == "__main__":
    print(bangun())
