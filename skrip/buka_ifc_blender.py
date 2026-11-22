"""Dipanggil Blender (Bonsai) untuk membuka model IFC proyek di jendela 3D.

Pakai:  alat\blender\blender.exe --python skrip\buka_ifc_blender.py -- model\RSTB-T3-Konsep.ifc
Jalan lain melihat dan mengedit model saat jendela BIMCraft 0.12.0 tidak mau tetap terbuka di laptop ini.
"""
import sys
from pathlib import Path

import bpy

AKAR = Path(__file__).resolve().parents[1]
argumen = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
berkas = Path(argumen[0]) if argumen else AKAR / "model" / "RSTB-T3-Konsep.ifc"
if not berkas.is_absolute():
    berkas = AKAR / berkas


def muat():
    bpy.ops.bim.load_project(filepath=str(berkas))
    print(f"Model dimuat: {berkas} ({len(bpy.data.objects)} objek)")
    return None


bpy.app.timers.register(muat, first_interval=1.0)
