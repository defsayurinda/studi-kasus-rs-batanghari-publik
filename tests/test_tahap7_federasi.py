"""Uji kecil 7.2: penetrasi 2,5D, klasifikasi clash, dan koreksi tapak/shaft model ARS (tanpa membuka IFC)."""
import sys
from pathlib import Path

from shapely.geometry import Point, box

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))
import tahap7_arsitektur as ta  # noqa: E402
import tahap7_federasi as tf  # noqa: E402


def test_potong_menempel_bukan_clash():
    a = (box(0, 0, 1, 1), 0.0, 3.0)
    assert tf.potong(a, (box(1, 0, 2, 1), 0.0, 3.0))[0] == 0.0          # bersinggungan sisi
    assert tf.potong(a, (box(0, 0, 1, 1), 3.0, 4.0))[0] == 0.0          # bertumpuk di atas
    d, _ = tf.potong(a, (box(0.85, 0, 2, 1), 1.0, 2.0))
    assert abs(d - 0.15) < 1e-9                                          # masuk 150 mm


def test_golong():
    c = {"set": "Shaft vs STR", "ka": "IfcOpeningElement:Shaft", "kb": "IfcBeam:BL"}
    assert tf.golong(c) == "K-01"
    assert tf.golong({**c, "set": "STR vs ARS", "ka": "IfcColumn:KL", "kb": "IfcWall:DP"}) == "K-07"
    assert tf.golong({**c, "set": "STR vs ARS", "ka": "IfcFooting:PC", "kb": "IfcSlab:TP"}) == "K-09"
    assert all(k in tf.KELOMPOK for k in ("K-01", "K-03", "K-99"))


def test_daftar_clash_status():
    akhir = [{"set": "STR vs ARS", "ka": "IfcColumn:KL", "kb": "IfcWall:DP", "d": 0.30, "na": "a", "nb": "b", "p": [0, 0, 0]}]
    d = {r["kode"]: r for r in tf.daftar_clash(akhir, [])}
    assert d["K-07"]["status"] == "ditanyakan"   # penetrasi 0,30 > batas 0,15


def test_jalur_kendaraan_jauh_dari_mri():
    iso = Point(tf.ISOCENTER)
    for k in ta.JALAN + [ta.RAMP_IGD, ta.APRON, ta.DROPOFF]:
        assert box(*k).distance(iso) >= tf.JARAK_LOGAM - 1e-9, k


def test_shaft_jadi_rintangan():
    kode = [s[0] for s in ta.shaft_lantai("LT2")]
    assert {"SH-1", "SH-2", "SH-3", "SH-4", "SH-5"} <= set(kode)
    S = ta.susun_lantai("LT2")
    sh = [r for r in S.ruang if "lubang pelat STR" in r.nama]
    assert sh and all(r.fin == "VOID" for r in sh)
    assert all(r.poli.intersection(s[3]).area < 1e-6 for r in S.ruang if r.kel != "Inti" for s in ta.shaft_lantai("LT2"))
