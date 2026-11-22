r"""Unduh aset render 7.8 dari Poly Haven (CC0, https://polyhaven.com/license) ke `alat/aset-render/` (tidak di-commit).

Pakai: .venv\Scripts\python.exe skrip\aset_render.py
Isi: HDRI langit murni (pencahayaan .exr 4k + latar JPG tonemapped), tekstur PBR 2k (warna, normal GL, kekasaran),
model pohon/semak/rumput glTF 1k. Berkas yang sudah ada dilewati.
"""
import json
import sys
import urllib.request
from pathlib import Path

AKAR = Path(__file__).resolve().parents[1]
ASET = AKAR / "alat" / "aset-render"
API = "https://api.polyhaven.com/files/"
UA = {"User-Agent": "render-script"}

HDRI = ["lonely_road_afternoon_puresky", "kloofendal_48d_partly_cloudy_puresky", "kloppenheim_06_puresky", "qwantani_dusk_2_puresky"]
TEKSTUR = ["ganges_river_pebbles", "asphalt_02", "leafy_grass", "concrete_pavement", "concrete_wall_008", "brown_mud_leaves_01", "pavement_02"]
MODEL = ["jacaranda_tree", "searsia_lucida", "island_tree_01", "island_tree_02", "island_tree_03", "tree_small_02", "shrub_02", "shrub_04", "grass_medium_01"]


def ambil(url, tujuan, ukuran=None):
    tujuan.parent.mkdir(parents=True, exist_ok=True)
    if tujuan.exists() and tujuan.stat().st_size > 0 and (ukuran is None or tujuan.stat().st_size == ukuran):
        return
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=300) as r, open(tujuan.with_suffix(tujuan.suffix + ".part"), "wb") as f:
        while blok := r.read(1 << 20):
            f.write(blok)
    part = tujuan.with_suffix(tujuan.suffix + ".part")
    if ukuran is not None and part.stat().st_size != ukuran:  # sambungan putus: jangan simpan berkas terpotong
        raise IOError(f"unduhan terpotong {tujuan.name}: {part.stat().st_size} != {ukuran}")
    part.replace(tujuan)
    print("unduh", tujuan.relative_to(ASET), flush=True)


def info(nama):
    with urllib.request.urlopen(urllib.request.Request(API + nama, headers=UA), timeout=60) as r:
        return json.load(r)


def main():
    for n in HDRI:
        d = info(n)
        ambil(d["hdri"]["4k"]["exr"]["url"], ASET / "hdri" / f"{n}_4k.exr", d["hdri"]["4k"]["exr"]["size"])
        ambil(d["tonemapped"]["url"], ASET / "hdri" / f"{n}_latar.jpg", d["tonemapped"]["size"])
    for n in TEKSTUR:
        d = info(n)
        for kunci, akhir in (("Diffuse", "diff"), ("nor_gl", "nor_gl"), ("Rough", "rough")):
            if kunci in d:
                ambil(d[kunci]["2k"]["jpg"]["url"], ASET / "tekstur" / n / f"{n}_{akhir}_2k.jpg", d[kunci]["2k"]["jpg"]["size"])
    for n in MODEL:
        g = info(n)["gltf"]["1k"]["gltf"]
        ambil(g["url"], ASET / "model" / n / Path(g["url"]).name, g["size"])
        for rel, f in g["include"].items():
            ambil(f["url"], ASET / "model" / n / rel, f["size"])


if __name__ == "__main__":
    main()
    sys.exit(0)
