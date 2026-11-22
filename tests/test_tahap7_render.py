"""Uji 7.8 render: skrip Blender sah, delapan kamera, PNG akhir >= 3.000 px (T-117 dicatat di md)."""
import ast
import re
from pathlib import Path

from PIL import Image

AKAR = Path(__file__).resolve().parents[1]
SKRIP = AKAR / "skrip" / "tahap7_render.py"
RENDER = AKAR / "07 DED dan RKS" / "Render"


def test_skrip_sah_dan_delapan_kamera():
    teks = SKRIP.read_text(encoding="utf-8")
    ast.parse(teks)
    assert sorted(set(re.findall(r'"(R-0[1-8])":', teks))) == [f"R-0{i}" for i in range(1, 9)]


def test_png_akhir_resolusi():
    png = sorted(RENDER.glob("R-0?.png"))
    assert len(png) == 8, [p.name for p in png]
    for p in png:
        with Image.open(p) as im:
            assert im.width >= 3000, (p.name, im.size)


def test_t117_unsur_blender_sama_ifc():
    """T-117: jumlah unsur per kelas IFC yang diimpor Bonsai = ifcopenshell (0 selisih); pembukaan tidak diimpor Bonsai."""
    import json
    from collections import Counter

    import ifcopenshell

    log = sorted((AKAR / "cache" / "tahap7_render").glob("log R-0?.json"))
    log = [p for p in log if "kelas_ifc" in json.loads(p.read_text(encoding="utf-8"))]
    if not log:
        import pytest
        pytest.skip("belum ada log render dengan kelas_ifc (cache tidak di-commit)")
    blender = json.loads(log[-1].read_text(encoding="utf-8"))["kelas_ifc"]
    f = ifcopenshell.open(str(AKAR / "model" / "RSTB-FED-T7.ifc"))
    ifc = Counter(e.is_a() for e in f.by_type("IfcProduct") if not e.is_a("IfcOpeningElement"))
    produk = {k: v for k, v in blender.items() if not k.endswith("Type") and k not in ("IfcProject", "IfcGridAxis")}
    assert produk == dict(ifc)


def test_skrip_detail_dan_video_sah():
    """Modul detail render dan perakit video: sintaks sah, enam shot V-01..V-06."""
    for nama in ("tahap7_render_detail.py", "tahap7_video.py", "aset_render.py"):
        ast.parse((AKAR / "skrip" / nama).read_text(encoding="utf-8"))
    teks = (AKAR / "skrip" / "tahap7_render_detail.py").read_text(encoding="utf-8")
    assert sorted(set(re.findall(r'"(V-0[1-6])":', teks))) == [f"V-0{i}" for i in range(1, 7)]
