"""6.7 Cap E sebagai pelat tebal di atas pegas tiang (keputusan Defsa 22 Nov 2026).

Model: pelat Mindlin-Reissner ShellMITC4 (openseespy; dipilih karena sudah dipakai Tahap 4 dan cepat untuk 1.900 simpul;
Pynite tidak dipakai). Jaring 0,4 m (simpul tepat di as tiang). Tiang = pegas vertikal k_eff di 3 × 3 simpul (kepala sendi 6.5:
tanpa tahanan rotasi dan lateral, jadi hanya DZ yang ditahan pegas; DX, DY, RZ dikunci karena tidak ada aksi selaput).
k_eff = k / (FJ sqrt(n)) dari 6.6 varian (d): s = FJ Q0 sqrt(n) / k (k 489 kN/mm, FJ 2,0, n 32) [Asumsi: sama untuk semua tiang].
Beban: dinding inti (cincin simpul pada kotak inti, 4 × 8 m INTI-LIF, 4 × 4 m INTI-T46/39 [Asumsi]) dengan P dan momen sebagai
gaya vertikal linear (kesetimbangan tepat), kolom 800 x 800 sebagai 3 x 3 simpul, berat sendiri sebagai tekanan merata.
Tanda momen dan kombinasi pemberi Pu maks / Pu min diambil dari 6.3 (`tahap6_struktur.muatan_tiang_cap`).
Ec bruto (tanpa retak) [Asumsi]; Wood-Armer untuk tulangan; geser, pons, STM lokal dari hasil pelat.
"""
from __future__ import annotations

import functools
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tahap6_struktur as ts  # noqa: E402
import tahap6_tata_letak as tl  # noqa: E402

AKAR = ts.AKAR
GAMBAR = AKAR / "06 Struktur Bawah dan Basement" / "Gambar"
PNG = GAMBAR / "6.7 Cap E Pelat Momen.png"

DX = 0.4                    # m, ukuran jaring
GAMMA_C = 25.0              # kN/m3
NU = 0.2
BOX_T46 = (44.0, 48.0, 37.0, 41.0)      # m, kotak INTI-T46/39 [Asumsi: 4 x 4 m, dinding 0,35 m; ukuran belum ada di acuan]
K_UJI = 489.0               # kN/mm, 6.6 (uji beban statik TP-1..4); dibaca ulang dari 6.6 bila bisa
FJ = 2.0                    # 6.6
W_PATCH = np.array([[1, 2, 1], [2, 4, 2], [1, 2, 1]], float) / 16
TOL_KESEIMBANGAN, TOL_REAKSI = 0.5, 25.0        # %, ditetapkan sebelum menghitung
FC = ts.FC_CAP
FY = ts.FY
DB = ts.DB_CAP
AS_BAR = math.pi * DB ** 2 / 4
NBAND = (9, 8)              # jumlah lajur (arah y untuk tulangan x, arah x untuk tulangan y), lebar ±2 m


def k_tiang(n):
    try:
        import tahap6_penurunan as pn
        k, fj = pn.uji_beban()["k"], pn.FJ
    except Exception:       # noqa: BLE001
        k, fj = K_UJI, FJ
    return k, fj, k * 1e3 / (fj * math.sqrt(n))      # kN/mm, -, kN/m


# ------------------------------------------------------------------ model
def _solve(c, h, komb, bs, k_eff):
    """Satu analisis statik. komb 'maks' (Pu, tanda pemberi Pu maks) atau 'min'; bs faktor berat sendiri. Mengembalikan dict hasil."""
    import openseespy.opensees as ops
    sm = tanda_momen()
    pos = np.array(c["pos"])
    R_, Rmin_, uls, umin = ts.muatan_tiang_cap(c)
    (sxm, sym), (sxn, syn), _, _ = c["_tanda"]
    sg = (sxm, sym) if komb == "maks" else (sxn, syn)
    X0, Y0 = pos[:, 0].min() - 0.8, pos[:, 1].min() - 0.8
    nx, ny = round(c["ukuran"][0] / DX), round(c["ukuran"][1] / DX)
    nid = lambda i, j: 1 + i * (ny + 1) + j
    ops.wipe()
    ops.model("basic", "-ndm", 3, "-ndf", 6)
    for i in range(nx + 1):
        for j in range(ny + 1):
            ops.node(nid(i, j), X0 + i * DX, Y0 + j * DX, 0.0)
            ops.fix(nid(i, j), 1, 1, 0, 0, 0, 1)
    ops.section("ElasticMembranePlateSection", 1, ts.ec(FC) * 1e3, NU, h / 1e3, 0.0)
    e = 0
    for i in range(nx):
        for j in range(ny):
            e += 1
            ops.element("ShellMITC4", e, nid(i, j), nid(i + 1, j), nid(i + 1, j + 1), nid(i, j + 1), 1)
    # pegas tiang
    base = 1 + (nx + 1) * (ny + 1)
    ops.uniaxialMaterial("Elastic", 1, 1.0)
    npile = 0
    nodes_pile = []
    for q in pos:
        ic, jc = round((q[0] - X0) / DX), round((q[1] - Y0) / DX)
        lst = []
        for a in (-1, 0, 1):
            for b in (-1, 0, 1):
                n = nid(ic + a, jc + b)
                npile += 1
                fn = base + npile
                ops.node(fn, X0 + (ic + a) * DX, Y0 + (jc + b) * DX, 0.0)
                ops.fix(fn, 1, 1, 1, 1, 1, 1)
                ops.uniaxialMaterial("Elastic", 1000 + npile, k_eff * W_PATCH[a + 1, b + 1])
                ops.element("zeroLength", 100000 + npile, fn, n, "-mat", 1000 + npile, "-dir", 3)
                lst.append((n, k_eff * W_PATCH[a + 1, b + 1]))
        nodes_pile.append(lst)
    # beban
    xy = lambda n: (X0 + ((n - 1) // (ny + 1)) * DX, Y0 + ((n - 1) % (ny + 1)) * DX)
    F = {}

    def tambah(lst, P, mx, my, xc, yc):
        """lst = [(simpul, luas tributari)]; F_i = a_i (q0 + q1 (y - yc) + q2 (x - xc)) memenuhi P, Mx = sum F (y - yc), My = sum F (x - xc)."""
        M = np.zeros((3, 3))
        for n, a in lst:
            x, y = xy(n)
            v = np.array([1.0, y - yc, x - xc])
            M += a * np.outer(v, v)
        q = np.linalg.solve(M, [P, mx, my])
        for n, a in lst:
            x, y = xy(n)
            F[n] = F.get(n, 0.0) + a * (q[0] + q[1] * (y - yc) + q[2] * (x - xc))

    def patch(x, y, w=1):
        ic, jc = round((x - X0) / DX), round((y - Y0) / DX)
        return [(nid(ic + a, jc + b), W_PATCH[a + 1, b + 1] * 16 * DX * DX / 4) for a in (-1, 0, 1) for b in (-1, 0, 1)]

    def cincin(box):
        i0, i1 = round((box[0] - X0) / DX), round((box[1] - X0) / DX)
        j0, j1 = round((box[2] - Y0) / DX), round((box[3] - Y0) / DX)
        s = {(i, j) for i in range(i0, i1 + 1) for j in range(j0, j1 + 1) if i in (i0, i1) or j in (j0, j1)}
        return [(nid(i, j), DX * ts.T_DINDING) for i, j in sorted(s)]
    boxes = {"INTI-LIF": ts.INTI_LIF_BOX, "INTI-T46/39": BOX_T46}
    patches = []
    for t in c["titik"]:
        P = t["Pu"] if komb == "maks" else t["Pumin"]
        if t["nama"] in boxes:
            bx = boxes[t["nama"]]
            tambah(cincin(bx), P, sg[1] * abs(t["Mux"]), sg[0] * abs(t["Muy"]), t["x"], t["y"])
            patches.append(bx)
        else:
            tambah(patch(t["x"], t["y"]), P, 0.0, 0.0, t["x"], t["y"])
            patches.append((t["x"] - 0.4, t["x"] + 0.4, t["y"] - 0.4, t["y"] + 0.4))
    # tanda: 6.3 memakai sx untuk Mux (ditahan sebaran y) dan sy untuk Muy (sebaran x); lihat muatan_tiang_cap: beban_tiang(pos, uls, sx * mux, sy * muy)
    # berat sendiri: tekanan merata bs * gamma * h
    q_sw = bs * tl.berat_cap(c["r"]["A"], h / 1e3) / c["r"]["A"]      # berat cap bersih (apung) seperti 6.3, kPa
    for i in range(nx + 1):
        for j in range(ny + 1):
            a = DX * DX * (0.5 if i in (0, nx) else 1.0) * (0.5 if j in (0, ny) else 1.0)
            F[nid(i, j)] = F.get(nid(i, j), 0.0) + q_sw * a
    ops.timeSeries("Linear", 1)
    ops.pattern("Plain", 1, 1)
    tot = 0.0
    for n, f in F.items():
        ops.load(n, 0.0, 0.0, -f, 0.0, 0.0, 0.0)
        tot += f
    ops.system("BandGeneral")
    ops.numberer("RCM")
    ops.constraints("Plain")
    ops.integrator("LoadControl", 1.0)
    ops.algorithm("Linear")
    ops.analysis("Static")
    if ops.analyze(1) != 0:
        raise RuntimeError("analisis pelat Cap E gagal")
    uz = {n: ops.nodeDisp(n, 3) for n in range(1, base)}
    reaksi = np.array([sum(-uz[n] * k for n, k in lst) for lst in nodes_pile])
    mx, my, mxy, vx, vy = (np.zeros((nx, ny)) for _ in range(5))
    e = 0
    for i in range(nx):
        for j in range(ny):
            e += 1
            ops.eleResponse(e, "forces")        # gaya elemen dihitung dulu; tanpa ini "stresses" bernilai nol
            s = np.array(ops.eleResponse(e, "stresses")).reshape(4, 8).mean(axis=0)
            mx[i, j], my[i, j], mxy[i, j], vx[i, j], vy[i, j] = s[3], s[4], s[5], s[6], s[7]
    ops.wipe()
    return dict(R=reaksi, mx=sm * mx, my=sm * my, mxy=sm * mxy, vx=vx, vy=vy, total=tot, nx=nx, ny=ny, X0=X0, Y0=Y0, patches=patches,
                uz=np.array([uz[nid(i, j)] for i in range(nx + 1) for j in range(ny + 1)]).reshape(nx + 1, ny + 1))


@functools.lru_cache(maxsize=1)
def tanda_momen():
    """Kalibrasi tanda Mxx ShellMITC4: pelat 4 x 4 m ditumpu sendi di empat sudut, beban turun merata: tengah melendut (sagging) harus positif."""
    import openseespy.opensees as ops
    ops.wipe()
    ops.model("basic", "-ndm", 3, "-ndf", 6)
    n = 8
    nid = lambda i, j: 1 + i * (n + 1) + j
    for i in range(n + 1):
        for j in range(n + 1):
            ops.node(nid(i, j), i * 0.5, j * 0.5, 0.0)
            ops.fix(nid(i, j), 1, 1, 0, 0, 0, 1)
    for k in (nid(0, 0), nid(n, 0), nid(0, n), nid(n, n)):
        ops.fix(k, 0, 0, 1, 0, 0, 0)
    ops.section("ElasticMembranePlateSection", 1, 3e7, 0.2, 0.3, 0.0)
    e = 0
    for i in range(n):
        for j in range(n):
            e += 1
            ops.element("ShellMITC4", e, nid(i, j), nid(i + 1, j), nid(i + 1, j + 1), nid(i, j + 1), 1)
    ops.timeSeries("Linear", 1)
    ops.pattern("Plain", 1, 1)
    for i in range(n + 1):
        for j in range(n + 1):
            ops.load(nid(i, j), 0, 0, -1.0, 0, 0, 0)
    ops.system("BandGeneral")
    ops.numberer("RCM")
    ops.constraints("Plain")
    ops.integrator("LoadControl", 1.0)
    ops.algorithm("Linear")
    ops.analysis("Static")
    ops.analyze(1)
    ops.eleResponse(n // 2 * n + n // 2, "forces")
    m = np.array(ops.eleResponse(n // 2 * n + n // 2, "stresses")).reshape(4, 8).mean(axis=0)[3]
    ops.wipe()
    return 1.0 if m > 0 else -1.0


# ------------------------------------------------------------------ Wood-Armer
def wood_armer(mx, my, mxy):
    """Momen desain tulangan bawah (m bawah) untuk momen sagging positif; atas dengan memanggil (-mx, -my, mxy)."""
    a = np.abs(mxy)
    bx, by = mx + a, my + a
    ix, iy = bx < 0, by < 0
    ex = np.where(np.abs(mx) < 1e-9, 1e-9, np.abs(mx))
    ey = np.where(np.abs(my) < 1e-9, 1e-9, np.abs(my))
    bx2 = np.where(ix, 0.0, np.where(iy, mx + mxy ** 2 / ey, bx))
    by2 = np.where(iy, 0.0, np.where(ix, my + mxy ** 2 / ex, by))
    return np.maximum(bx2, 0.0), np.maximum(by2, 0.0)


def pilih_besi(as_m):
    """As (mm2/m) -> (lapis, jarak mm) D32: jarak = kelipatan 25 mm >= 100 mm; lapis dinaikkan sampai jarak memenuhi."""
    for lap in (1, 2, 3, 4):
        s = AS_BAR * lap / max(as_m, 1.0) * 1e3
        sj = math.floor(s / 25) * 25
        if sj >= 100:
            return lap, min(sj, 300)
    return 4, 100


def as_perlu(m, d_mm, h):
    """As (mm2/m) dari Mu (kNm/m): lentur, minimum 9.6.1.2 (boleh 4/3 As perlu, 9.6.1.3), susut 24.4.3.2 (0,0018 b h per muka, usulan AI)."""
    req = ts.as_lentur(m, 1.0, d_mm / 1e3, FC)
    min96 = max(0.25 * math.sqrt(FC) / FY, 1.4 / FY) * 1e3 * d_mm
    sus = 0.0018 * 1e3 * h
    return max(req, min(min96, 4 / 3 * req), sus), req, sus


def lajur(m2d, arah):
    """Rata-rata momen per lajur: arah 0 = tulangan x (rata-rata sepanjang y per lajur y), maksimum sepanjang x; arah 1 sebaliknya."""
    nb = NBAND[arah]
    if arah == 0:
        grp = np.array_split(np.arange(m2d.shape[1]), nb)
        prof = np.array([m2d[:, g].mean(axis=1) for g in grp])      # (nb, nx)
    else:
        grp = np.array_split(np.arange(m2d.shape[0]), nb)
        prof = np.array([m2d[g, :].mean(axis=0) for g in grp])      # (nb, ny)
    return prof.max(axis=1), grp


def lentur(res_list, h):
    d = ts.d_efektif(h)
    out = {}
    for sisi, tnd in (("bawah", 1.0), ("atas", -1.0)):
        for arah in (0, 1):
            best = None
            for r in res_list:
                bx, by = wood_armer(tnd * r["mx"], tnd * r["my"], r["mxy"])
                m2 = (bx, by)[arah]
                mb, grp = lajur(m2, arah)
                best = mb if best is None else np.maximum(best, mb)
            asb = np.array([as_perlu(m, d, h)[0] for m in best])
            lap = [pilih_besi(a) for a in asb]
            kritis = int(np.argmax(asb))
            out[(sisi, "xy"[arah])] = dict(M=best, As=asb, lap=lap, M_maks=float(best.max()), As_maks=float(asb.max()), kritis=kritis,
                                           req=as_perlu(float(best.max()), d, h)[1], susut=as_perlu(0.0, d, h)[2], pilih=lap[kritis], grp=len(grp))
    return out


# ------------------------------------------------------------------ geser, pons, STM lokal
def _bebas(patches, ar, garis, ya, yb, d):
    """Jendela [ya, yb] pada garis (arah ar) boleh dipakai bila tidak ada muka beban lebih dekat dari d (22.5.1.2: penampang di d dari muka)."""
    for (x0, x1, y0, y1) in patches:
        lo, hi = (x0, x1) if ar == 0 else (y0, y1)
        a0, a1 = (y0, y1) if ar == 0 else (x0, x1)
        if lo - d + 1e-6 < garis < hi + d - 1e-6 and a0 < yb and a1 > ya:
            return False
    return True


def geser_satu_arah(r, c, h):
    """v per meter dari V elemen pelat di d dari muka inti dan muka tiang; rata-rata jendela 2d; rasio terhadap φVc per meter."""
    d = ts.d_efektif(h) / 1e3
    pos = np.array(c["pos"])
    nx, ny, X0, Y0 = r["nx"], r["ny"], r["X0"], r["Y0"]
    win = max(1, round(2 * d / DX))
    pvc = 0.75 * 0.17 * math.sqrt(FC) * 1e3 * d * 1e3 / 1e3        # kN/m: 0,75 x 0,17 sqrt(f'c) [MPa] x 1000 mm x d [mm] / 1000
    garis = {0: [], 1: []}
    bx = ts.INTI_LIF_BOX
    garis[0] += [bx[0] - d, bx[1] + d]
    garis[1] += [bx[2] - d, bx[3] + d]
    for xq in sorted({round(q[0], 3) for q in pos}):
        garis[0] += [xq - 0.4 - d, xq + 0.4 + d]
    for yq in sorted({round(q[1], 3) for q in pos}):
        garis[1] += [yq - 0.4 - d, yq + 0.4 + d]
    best = dict(rasio=0.0)
    for ar in (0, 1):
        V = (r["vx"], r["vy"])[ar]       # Vxz (garis x = const) dan Vyz
        for g in garis[ar]:
            u = (g - (X0 if ar == 0 else Y0)) / DX - 0.5          # pusat elemen di u = indeks; V diinterpolasi linear ke garis penampang
            i0 = math.floor(u)
            if not 0 <= i0 < (nx if ar == 0 else ny) - 1:
                continue
            w = u - i0
            Vm = V if ar == 0 else V.T
            prof = np.abs((1 - w) * Vm[i0, :] + w * Vm[i0 + 1, :])
            n = len(prof)
            for k in range(0, n - win + 1):
                ya = (Y0 if ar == 0 else X0) + k * DX
                if not _bebas(r["patches"], ar, g, ya, ya + win * DX, d):
                    continue
                v = prof[k:k + win].mean()
                if v / pvc > best["rasio"]:
                    best = dict(rasio=v / pvc, v=float(v), phiVc=pvc, arah="xy"[ar], garis=float(g), lebar=win * DX)
    return best


def pons(r, c, h):
    pos = np.array(c["pos"])
    R = r["R"]
    xmin, xmax, ymin, ymax = pos[:, 0].min() - 0.8, pos[:, 0].max() + 0.8, pos[:, 1].min() - 0.8, pos[:, 1].max() + 0.8
    best = None
    for q, ri in zip(pos, R):
        if ri <= 0:
            continue
        e = (q[0] - xmin, xmax - q[0], q[1] - ymin, ymax - q[1])
        p = ts.pons_tiang(float(ri), e, FC, h)
        if best is None or p["rasio"] > best["rasio"]:
            best = p
            best["pos"] = (float(q[0]), float(q[1]))
    inti = ts.pons_inti(c, R, h, FC)
    return best, inti


def stm_lokal(c, R, h):
    """STM hanya untuk tiang dalam 2d dari dinding inti (kotak INTI-LIF). Tiang di bawah kotak: tumpu langsung (tanpa strut)."""
    box = ts.INTI_LIF_BOX
    d = ts.d_efektif(h) / 1e3
    z = ts.Z_RASIO * d
    hta = 2 * (h - d * 1e3) / 1e3
    fce_s, fce_n, fce_c = 0.85 * ts.BETA_S * FC, 0.85 * ts.BETA_N_TIANG * FC, 0.85 * ts.BETA_N_KOL * FC
    ap = math.pi * (ts.D / 1e3) ** 2 / 4
    a_node = 2 * (box[1] - box[0] + box[3] - box[2]) * ts.T_DINDING
    rows, nod = [], 0.0
    for q, r in zip(c["pos"], R):
        dx, dy = max(box[0] - q[0], 0.0, q[0] - box[1]), max(box[2] - q[1], 0.0, q[1] - box[3])
        dist = math.hypot(dx, dy)
        if r <= 0 or dist > 2 * d or (dx == 0 and dy == 0):
            continue
        li = dist + ts.T_DINDING / 2
        th = math.degrees(math.atan2(z, li))
        row = dict(x=float(q[0]), y=float(q[1]), R=float(r), li=li, theta=th, stm=th >= 25.0)
        if row["stm"]:
            s = math.sin(math.radians(th))
            acs = (ts.LB_TIANG * s + hta * math.cos(math.radians(th))) * ts.LB_TIANG
            row["F"] = r / s
            row["r_strut"] = row["F"] / (0.75 * fce_s * acs * 1e3)
            row["r_tiang"] = r / (0.75 * fce_n * ap * 1e3)
            row["T"] = r * li / z
            nod += r
        rows.append(row)
    st = [w for w in rows if w["stm"]]
    r_node = nod / (0.75 * fce_c * a_node * 1e3) if st else 0.0
    rasio = max([w["r_strut"] for w in st] + [w["r_tiang"] for w in st] + [r_node, 0.0])
    return dict(rows=rows, n_stm=len(st), n_luar=len(rows) - len(st), r_node=r_node, rasio=rasio, d=d, z=z, jarak=2 * d,
                T_maks=max([w["T"] for w in st] + [0.0]), As_tie=max([w["T"] for w in st] + [0.0]) * 1e3 / (0.75 * FY))


# ------------------------------------------------------------------ satu tebal
def analisis(c, h):
    n = c["r"]["n"]
    k, fj, k_eff = k_tiang(n)
    R_, Rmin_, _, _ = ts.muatan_tiang_cap(c)
    r1 = _solve(c, h, "maks", tl.F_W["maks"], k_eff)  # Pu maks + 1,2 berat cap (seperti 6.3, berat cap ada di 6.3)
    r0 = r1                                           # pembanding 6.3: kombinasi yang sama
    r2 = _solve(c, h, "min", tl.F_W["min"], k_eff)    # Pu min + 0,9 berat cap
    len_ = lentur([r1, r2], h)
    gs = max((geser_satu_arah(r, c, h) for r in (r1, r2)), key=lambda z: z["rasio"])
    pt1, pi1 = pons(r1, c, h)
    pi2 = ts.pons_inti(c, r2["R"], h, FC)
    stm = stm_lokal(c, r1["R"], h)
    lap_maks = max(v["pilih"][0] for v in len_.values())
    rasio = dict(geser=gs["rasio"], pons_tiang=pt1["rasio"], pons_inti=max(pi1["rasio"], pi2["rasio"]), stm=stm["rasio"])
    penentu = max(rasio, key=rasio.get)
    ok = all(v <= 1.0 for v in rasio.values()) and lap_maks <= 3 and ts.d_efektif(h) >= 300
    return dict(h=h, d=ts.d_efektif(h), k=k, fj=fj, k_eff=k_eff, r0=r0, r1=r1, r2=r2, R_kaku=R_, Rmin_kaku=Rmin_, lentur=len_, geser=gs, pons_tiang=pt1,
                pons_inti=pi1 if pi1["rasio"] >= pi2["rasio"] else pi2, stm=stm, rasio=rasio, penentu=penentu, lolos=ok, lapis_maks=lap_maks,
                banding=banding(c, r0, R_, h), n=n)


def banding(c, r0, R_, h):
    sumP = sum(t["Pu"] for t in c["titik"]) + tl.F_W["maks"] * tl.berat_cap(c["r"]["A"], h / 1e3)
    d_sum = abs(r0["R"].sum() - sumP) / sumP * 100
    d_sum_kaku = abs(R_.sum() - sumP) / sumP * 100
    rm, rk = float(r0["R"].max()), float(R_.max())
    return dict(sumP=sumP, sum_fe=float(r0["R"].sum()), d_sum=d_sum, d_sum_kaku=d_sum_kaku, max_fe=rm, max_kaku=rk, d_max=abs(rm - rk) / rk * 100,
                min_fe=float(r0["R"].min()), min_kaku=float(R_.min()), lolos=d_sum <= TOL_KESEIMBANGAN and abs(rm - rk) / rk * 100 <= TOL_REAKSI)


H_COBA = [1500.0, 1800.0, 2000.0]
H_SCAN = [1500.0 + 100 * i for i in range(0, 13)]


def semua(c=None, scan=True):
    """Analisis pelat untuk h 1.500/1.800/2.000 (tabel), dan h minimum yang lolos dalam pindai 1.500-2.700 bila scan."""
    if c is None:
        import tahap6_tata_letak as tl
        c = next(x for x in tl.rancang("a")[1] if x["kode"] == "E")
    ts.muatan_tiang_cap(c)
    out = {}
    for h in sorted(set(H_COBA + ([ts.H_E] if ts.H_E not in H_COBA else []))):
        out[h] = analisis(c, h)
    hmin = None
    if scan:
        for h in H_SCAN:
            if h not in out:
                out[h] = analisis(c, h)
            if out[h]["lolos"]:
                hmin = h
                break
    return dict(c=c, hasil=out, h_min=hmin)


def gambar(a, c, keluar=PNG):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    r = a["r1"]
    nx, ny, X0, Y0 = r["nx"], r["ny"], r["X0"], r["Y0"]
    xs, ys = X0 + (np.arange(nx) + 0.5) * DX, Y0 + (np.arange(ny) + 0.5) * DX
    pos = np.array(c["pos"])
    fig, ax = plt.subplots(2, 2, figsize=(13, 14.5))
    for a_, nm, m in ((ax[0, 0], "mx (kNm/m), + sagging", r["mx"]), (ax[0, 1], "my (kNm/m), + sagging", r["my"]), (ax[1, 0], "mxy (kNm/m)", r["mxy"])):
        lim = np.percentile(np.abs(m), 99)
        cs = a_.contourf(xs, ys, m.T, levels=np.linspace(-lim, lim, 21), cmap="RdBu_r", extend="both")
        fig.colorbar(cs, ax=a_, shrink=0.8)
        a_.set_title(f"Cap E h {a['h']:.0f} mm, {nm}\nPu maks + 1,2 berat sendiri")
        a_.plot(pos[:, 0], pos[:, 1], "ko", ms=5)
        bx = ts.INTI_LIF_BOX
        a_.add_patch(plt.Rectangle((bx[0], bx[2]), bx[1] - bx[0], bx[3] - bx[2], fill=False, ec="k", lw=2))
        a_.set_aspect("equal")
        a_.set_xlabel("x (m)")
        a_.set_ylabel("y (m)")
    a_ = ax[1, 1]
    sc = a_.scatter(pos[:, 0], pos[:, 1], c=a["r0"]["R"], s=260, cmap="viridis")
    for q, rf, rk in zip(pos, a["r0"]["R"], a["R_kaku"]):
        a_.annotate(f"{rf:,.0f}\n({rk:,.0f})".replace(",", "."), q, ha="center", va="center", fontsize=6.5, color="w")
    fig.colorbar(sc, ax=a_, shrink=0.8)
    a_.set_title("Reaksi tiang Pu maks (kN): pelat (cap kaku 6.3)")
    a_.set_aspect("equal")
    a_.set_xlabel("x (m)")
    fig.tight_layout()
    Path(keluar).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(keluar, dpi=110)
    plt.close(fig)
    return keluar


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    import time
    t0 = time.time()
    s = semua()
    for h, a in s["hasil"].items():
        b = a["banding"]
        print(h, "lolos", a["lolos"], {k: round(v, 3) for k, v in a["rasio"].items()}, "lapis", a["lapis_maks"], "tiang maks FE/kaku", round(b["max_fe"]), round(b["max_kaku"]),
              round(b["d_max"], 1), "% sum", round(b["d_sum"], 3), "min", round(b["min_fe"]), round(b["min_kaku"]), "k_eff", round(a["k_eff"]))
    print("h min", s["h_min"], round(time.time() - t0), "s")


if __name__ == "__main__":
    main()
