import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))

import tahap3_template_bim as tpl  # noqa: E402


def test_level_naik_dan_lantai_dasar_tor():
    elev = [e for _, e in tpl.LEVEL]
    assert elev == sorted(elev) and len(set(elev)) == len(elev)
    assert dict(tpl.LEVEL)["LT1"] == 12850  # langkah 3.3: lantai dasar +12,85 (Q100 + 0,50)
    assert dict(tpl.LEVEL)["LT1"] > 11200  # di atas banjir tercatat +11,20


def test_nama_tipe_ikut_pola_bep():
    for t in tpl.TIPE:
        kode = t["name"].split("-")[0]
        assert kode in {"KL", "BL", "PL", "DG", "DB", "DD"}, t["name"]
        if t["name"].endswith("-S2") or kode in {"KL", "DG", "DB"}:
            mat = t.get("material") or t["layers"][0]["material"]
            assert "S2" in mat


def test_skrip_template_memuat_level_dan_parameter():
    s = "\n".join(tpl.baris_skrip())
    for nama, _ in tpl.LEVEL:
        assert f'"name": "{nama}"' in s
    for nama, _ in tpl.PARAMETER:
        assert nama in s
    assert "structuralcolumn" in s and "beam" in s  # kategori parameter (uji BIMCraft 0.12.0)


@pytest.mark.skipif(not tpl.IFC.exists(), reason="template belum dibangun")
def test_ifc_template_sesuai_bep():
    h = tpl.periksa_ifc()
    assert h["skema"] == "IFC4" and h["satuan_mm"]
    assert h["situs"] == 1 and h["gedung"] == 1
    assert sorted(h["lantai"]) == sorted(tpl.LEVEL)
