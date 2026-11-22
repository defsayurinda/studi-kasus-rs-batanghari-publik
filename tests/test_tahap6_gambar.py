import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))

import tahap6_gambar as gm  # noqa: E402
import tahap6_tata_letak as tl  # noqa: E402

DWG = {"GS-28": "GS-28 Denah Tiang dan Pile Cap", "GS-29": "GS-29 Pile Cap Inti", "GS-30": "GS-30 Pile Cap Tipikal",
       "GS-31": "GS-31 Detail Tiang Bor", "GS-32": "GS-32 Tabel Tiang dan Pile Cap", "GT-16": "GT-16 Potongan Tebing P-2"}


def test_dwg_ada():
    for n in DWG.values():
        assert (gm.DWG / f"{n}.dwg").exists(), n
    assert gm.PDF.exists()


def test_cad_cek_nol():
    import cad_cek
    for n in DWG.values():
        assert cad_cek.cek(gm.DWG / f"{n}.dwg") == [], n


def test_tiang_gs28_319():
    from cadcraft import Sesi
    with Sesi() as c:
        c.buka(gm.DWG / f"{DWG['GS-28']}.dwg")
        c.cmd("layout.set", {"name": "Model"})
        ent = c.alat("query_entities", {"type": "Insert", "limit": 5000}).get("entities", [])
    n = sum(1 for e in ent if str(e["geometry"].get("block", "")).startswith("TIANG_"))
    assert n == 319 == 251 + 68


def test_tabel_gs32_sama_rancang():
    ck, ci = tl.rancang("a")
    rek = gm.tabel_cap()
    assert sum(r[3] for r in rek) == len(ck) + len(ci) + 25 == 83
    assert sum(r[4] for r in rek) == sum(c["r"]["n"] for c in ck + ci) + 68 == 319
    assert sum(r[4] for r in rek if r[1] == "inti") == sum(c["r"]["n"] for c in ci) == 108
