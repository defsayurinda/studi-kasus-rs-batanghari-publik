"""Langkah 3.1: template BIMCraft proyek RS Tepian Batanghari (aturan di '3.1 BEP.docx').

Membuat 'model/RSTB-TPL-Template.bimc' (dibuka di BIMCraft sebagai awal setiap model) dan salinan IFC4-nya, lalu
memeriksa IFC dengan IfcOpenShell. Isi template: informasi proyek, level sementara (elevasi = datum lokal proyek,
BM-1 = +10,000), material beton kelas paparan S2, pustaka tipe struktur dan dinding, serta parameter proyek
Pset_RSTB_Umum. Grid kolom TIDAK dimasukkan (ditetapkan di langkah 3.6).
Disusun AI atas permintaan Defsa (19 Nov 2026); disetujui Defsa 19 Nov 2026.
Jalankan:  .venv\\Scripts\\python.exe skrip\\tahap3_template_bim.py
"""
import json
import subprocess
import tempfile
from pathlib import Path

AKAR = Path(__file__).resolve().parents[1]
CLI = AKAR / "alat" / "bimcraft" / "bimcraft-0.12.0-windows-x64-portable" / "bimcraft-cli.exe"
MODEL = AKAR / "model"
BIMC = MODEL / "RSTB-TPL-Template.bimc"
IFC = MODEL / "RSTB-TPL-Template.ifc"

# Level (mm, elevasi datum lokal). Lantai dasar +12,85 = Q100 + 0,50 (langkah 3.3, disetujui Defsa 19 Nov 2026);
# tinggi antarlantai [Asumsi: 4,5 m untuk IGD dan bedah sentral, 4,2 m rawat inap; ditetapkan di 3.4/3.6];
# B1 [Asumsi: opsi basement di 3.5].
LEVEL = [
    ("B1", 9050),
    ("LT1", 12850),
    ("LT2", 17350),
    ("LT3", 21850),
    ("LT4", 26050),
    ("LT5", 30250),
    ("LT6", 34450),
    ("ATAP", 38650),
]

MATERIAL = [
    # nama, warna, pola potongan
    ("Beton fc 30 S2", "#B4B4B4", "concrete"),
    ("Beton fc 35 S2", "#A0A0A0", "concrete"),
    ("Bata ringan", "#E6D2B4", "diagonal"),
]

# Pustaka tipe (dimensi pra-dimensi sementara; diganti hasil 3.6). Kode: KL kolom, BL balok, PL pelat,
# DG dinding geser, DB dinding basement, DD dinding pengisi.
TIPE = [
    {"category": "structuralcolumn", "name": "KL-600x600-fc35", "width": 600, "depth": 600, "material": "Beton fc 35 S2"},
    {"category": "structuralcolumn", "name": "KL-700x700-fc35", "width": 700, "depth": 700, "material": "Beton fc 35 S2"},
    {"category": "beam", "name": "BL-400x700-fc30", "width": 400, "depth": 700, "material": "Beton fc 30 S2"},
    {"category": "beam", "name": "BL-300x500-fc30", "width": 300, "depth": 500, "material": "Beton fc 30 S2"},
    {"category": "floor", "name": "PL-150-fc30", "layers": [{"function": "structure", "material": "Beton fc 30 S2", "thickness": 150}]},
    {"category": "floor", "name": "PL-200-fc30", "layers": [{"function": "structure", "material": "Beton fc 30 S2", "thickness": 200}]},
    {"category": "floor", "name": "PL-400-fc35-S2", "layers": [{"function": "structure", "material": "Beton fc 35 S2", "thickness": 400}]},
    {"category": "wall", "name": "DG-300-fc35", "layers": [{"function": "structure", "material": "Beton fc 35 S2", "thickness": 300}]},
    {"category": "wall", "name": "DB-400-fc35-S2", "layers": [{"function": "structure", "material": "Beton fc 35 S2", "thickness": 400}]},
    {"category": "wall", "name": "DD-150-Bata", "layers": [{"function": "structure", "material": "Bata ringan", "thickness": 150}]},
]

PSET = "Pset_RSTB_Umum"
KATEGORI_PARAM = ["wall", "floor", "column", "structuralcolumn", "beam", "footing", "roof", "stair", "railing", "room", "component"]
PARAMETER = [
    ("RSTB_Tahap", "Tahap pekerjaan yang terakhir mengubah elemen (3, 4, 5, 6, 7)"),
    ("RSTB_LOD", "Tingkat kematangan elemen menurut BEP (200, 300, 350)"),
    ("RSTB_Status", "draf AI / diperiksa / disetujui Defsa <tanggal>"),
    ("RSTB_Sumber", "Dasar dimensi: berkas hitungan atau [Asumsi]"),
    ("RSTB_KelasPaparan", "Kelas paparan beton (S2 bila menyentuh gambut/lempung, langkah 2.7)"),
]

INFO = {
    "name": "Rumah Sakit Tepian Batanghari",
    "number": "RSTB-2026",
    "client": "Yayasan Kesehatan Tepian Batanghari (simulasi)",
    "address": "Tepi utara Sungai Batanghari\nKota Jambi (lahan fiktif)",
    "status": "Desain Konsep LOD 200",
    "author": "Defsa Yurinda",
    "organization": "Studi kasus portofolio perencanaan",
    "organization_description": "DATA SIMULASI, TIDAK UNTUK KONSTRUKSI",
    "building": "Gedung utama RS (6 lantai + basement)",
}


def baris_skrip():
    b = [f"project_info {json.dumps(INFO, ensure_ascii=False)}"]
    for nama, warna, pola in MATERIAL:
        b.append(f'material {json.dumps({"name": nama, "color": warna, "cut": pola})}')
    # dua level bawaan diganti, sisanya dibuat baru
    (n0, e0), (n1, e1) = LEVEL[0], LEVEL[1]
    b.append(f'modify {json.dumps({"id": 100001, "name": n1, "elevation": e1})}')
    b.append(f'modify {json.dumps({"id": 100000, "name": n0, "elevation": e0})}')
    for nama, elev in LEVEL[2:]:
        b.append(f'level {json.dumps({"elevation": elev, "name": nama})}')
    for t in TIPE:
        b.append(f"type {json.dumps(t)}")
    for nama, ket in PARAMETER:
        b.append("parameter " + json.dumps({"name": nama, "kind": "text", "categories": KATEGORI_PARAM,
                                            "sets": {k: PSET for k in KATEGORI_PARAM}, "description": ket},
                                           ensure_ascii=False))
    return b


def bangun():
    MODEL.mkdir(exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write("\n".join(baris_skrip()) + "\n")
        skrip = f.name
    hasil = subprocess.run([str(CLI), "run", "--script", skrip, "--save", str(BIMC), "--save", str(IFC)],
                           capture_output=True, text=True, encoding="utf-8")
    Path(skrip).unlink(missing_ok=True)
    if hasil.returncode != 0:
        raise RuntimeError(hasil.stdout[-2000:] + hasil.stderr[-2000:])
    return BIMC, IFC


def periksa_ifc(path=IFC):
    """Cek minimum BEP: IFC4, hierarki proyek-situs-gedung-lantai, nama dan elevasi lantai, satuan mm."""
    import ifcopenshell
    import ifcopenshell.util.unit as uu

    f = ifcopenshell.open(str(path))
    lantai = sorted((s.Name, round(float(s.Elevation or 0) * uu.calculate_unit_scale(f) * 1000))
                    for s in f.by_type("IfcBuildingStorey"))
    return {
        "skema": f.schema,
        "proyek": [p.Name for p in f.by_type("IfcProject")],
        "situs": len(f.by_type("IfcSite")),
        "gedung": len(f.by_type("IfcBuilding")),
        "lantai": lantai,
        "satuan_mm": abs(uu.calculate_unit_scale(f) - 0.001) < 1e-9,
    }


if __name__ == "__main__":
    print(bangun())
    print(periksa_ifc())
