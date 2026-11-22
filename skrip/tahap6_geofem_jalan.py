"""Pembantu 6.6: jalankan satu model GeoFEM3D (elastis, cap terisolasi) di venv GeoFEM3D. Argumen: JSON {B, L, q, lap[(tebal, E kPa, nu)], halus, kasar, lebar, app}.
Keluaran: satu baris JSON {settlement (mm, titik kendali pusat fondasi), max (mm), waktu (s), dof}."""
import json
import sys
import time

a = json.loads(sys.argv[1])
sys.path.insert(0, a["app"])
from geofem.mesher import generate_mesh  # noqa: E402
from geofem.project import Layer, Material, default_project  # noqa: E402
from geofem.solver import run_analysis  # noqa: E402

p = default_project()
p.materials, lay, z = [], [], 0.0
for i, (t, E, nu) in enumerate(a["lap"]):
    p.materials.append(Material(f"L{i}", 0.0, 0.0, E, nu, 1e6, 0.0, 0.0))   # elastis: c besar, γ 0 (hanya perpindahan akibat beban)
    lay.append(Layer(z, z - t, f"L{i}"))
    z -= t
p.borehole.layers, p.borehole.water_level = lay, -1000.0
p.domain.Lx = p.domain.Ly = a["lebar"]
p.domain.symmetry = True
p.footing.B, p.footing.L, p.footing.q, p.footing.kind = a["B"], a["L"], a["q"], "flexible"
p.mesh.coarse, p.mesh.fine = a["kasar"], a["halus"]
p.phases.run_safety = False
err = p.validate()
if err:
    raise SystemExit(f"masukan tidak valid: {err}")
t0 = time.time()
mesh = generate_mesh(p)
res = run_analysis(p, mesh)
print(json.dumps(dict(settlement=res.footing_settlement * 1000, max=res.max_settlement * 1000, waktu=time.time() - t0,
                      dof=int(getattr(res, "log", [""])[0].split("derajat")[0].split()[-1]) if res.log else None)))
