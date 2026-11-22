import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))

import tahap3_program as pr  # noqa: E402
import tahap3_zonasi as zn  # noqa: E402


def test_owner_138_tt_dan_konsultan_150():
    assert sum(b["n"] * b["tt_per"] for b in pr.program_owner()) == 138  # temuan Tahap 0
    assert sum(b["tt"] for b in pr.program_konsultan()) == 150


def test_utilitas_tidak_di_basement():
    assert not any(b["kelompok"].startswith("Utilitas (basement)") for b in pr.program_konsultan())
    assert all(b["lantai"] in ("GU", "HALAMAN") for b in pr.program_konsultan() if b["kelompok"].startswith("Utilitas"))


def test_program_muat_di_massa():
    rk = pr.rekap_lantai()
    podium, menara = pr.poligon("PODIUM").area, pr.poligon("MENARA").area
    # LT1 boleh sedikit melebihi tapak karena drop-off IGD beratap (80 m² × 1,45) di luar massa
    assert rk["LT1"]["bruto"] <= podium + 80 * pr.FAKTOR_BRUTO
    assert rk["LT2"]["bruto"] <= podium and rk["LT3"]["bruto"] <= podium
    assert all(rk[k]["bruto"] <= menara for k in ("LT4", "LT5", "LT6"))
    assert rk["GU"]["bruto"] <= 2 * pr.poligon("GEDUNG UTILITAS").area


def test_massa_dalam_batas_pkkpr():
    cm = pr.cek_massa()
    assert all(m["dalam_amplop"] for m in cm["massa"])
    assert all(m["jarak_labil"] > 0 for m in cm["massa"])
    assert cm["tapak"] <= cm["kdb_maks"] and cm["luas_lantai"] <= cm["klb_maks"]


def test_tangga_darurat_maks_25_m():
    assert zn.cek_tangga() <= 25.0  # PMK 40/2022 hal. 12 butir G.3.e.3.c


def test_zona_di_dalam_massa():
    for lt, zs in zn.ZONA.items():
        m = pr.MASSA["MENARA" if lt == "LT4-LT6" else "PODIUM"]
        for _, x0, x1, y0, y1, _ in zs:
            assert m["x"][0] <= x0 < x1 <= m["x"][1] and m["y"][0] <= y0 < y1 <= m["y"][1]


def test_model_bim_punya_ruang_dan_grid():
    import ifcopenshell
    import ifcopenshell.util.element as ue

    if not zn.IFC.exists():
        return
    f = ifcopenshell.open(str(zn.IFC))
    ruang = f.by_type("IfcSpace")
    assert len(ruang) >= 29 and len(f.by_type("IfcGridAxis")) == 17
    assert ue.get_psets(ruang[0])["Pset_RSTB_Umum"]["RSTB_LOD"] == "200"
