"""Tahap 5 langkah 5.6a: desain ulang enam kolom tangki opsi B (b 0,75-0,80 m, K-TB LT2 dan LT3).

DATA SIMULASI untuk studi kasus portofolio. Disusun AI atas permintaan Defsa (21 Nov 2026); draf, menunggu persetujuan Defsa.
Kunci jawaban tidak dibuka. Gaya dari model 4.7 (opsi A, `tahap4_kolom.analisis` K1 dan K2) ditambah koreksi aksial D opsi B (5.1).
"""
from __future__ import annotations

import functools
import math
import os
import pickle
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import tahap4_beban as tb  # noqa: E402
import tahap4_kolom as kl  # noqa: E402
import tahap5_tangki as tn  # noqa: E402

AKAR = Path(__file__).resolve().parents[1]
KELUAR = AKAR / "05 Struktur Tengah"
BERKAS = KELUAR / "5.6a Kolom Tangki Opsi B.xlsx"
LABEL = tn.LABEL
STATUS = "disetujui Defsa 21 Nov 2026: 800 seragam"


@functools.lru_cache(maxsize=1)
def data_mentah():
    """Satu kali jalan (lama, ~10 menit): analisis 3D K1 dan K2 (model 4.7), hasil 5.1 (kolom B, balok B) dan desain 4.7.
    Disimpan ke pickle lewat env KOLOM_TANGKI_CACHE (shortcut pengembangan)."""
    cache = os.environ.get("KOLOM_TANGKI_CACHE")
    if cache and Path(cache).exists():
        return pickle.load(open(cache, "rb"))
    um = tn.hasil_46_47()["um"]
    hs = [kl.analisis("K2", um), kl.analisis("K1", um)]
    th = tn.hitung()
    r = kl.balok_rancang()
    rk = kl.rancang()   # = rancang_dari(hs, balok_rancang()); ter-cache di disk
    out = {"um": um, "hs": hs, "kolom_b": th["kolom_b"], "w_a": th["w_a"], "w_b": th["w_b"], "t_b": th["t_b"],
           "balok_b": th["balok_b"], "peta": kl.peta_balok(), "rk": rk["kelompok"]}
    if cache:
        pickle.dump(out, open(cache, "wb"))
    return out


# ================================================================== gaya, joint, desain
KOLOM = list(tn.KOLOM)                   # enam kolom tangki (x 60/68/76, y 67/75)
SEG = ("LT2", "LT3")                     # segmen kolom tangki: LT1-LT2 dan LT2-LT3 (atap podium)
TOL = {"a": 3.0, "b": 1.0, "c": 5.0, "d": 0.5}   # % (T-96), ditetapkan sebelum membandingkan
# elemen balok opsi B (5.1) -> ujung, balok tepi (sayap 6 hf)
B_ELEMEN = {"x 60": (((60.0, 67.0), (60.0, 75.0)), False), "x 68": (((68.0, 67.0), (68.0, 75.0)), False),
            "x 76 (standar)": (((76.0, 67.0), (76.0, 75.0)), False),
            "y 67 (x 60-68)": (((60.0, 67.0), (68.0, 67.0)), False),
            "y 67 (x 68-76, standar)": (((68.0, 67.0), (76.0, 67.0)), False),
            "y 75 (x 60-68)": (((60.0, 75.0), (68.0, 75.0)), True)}
ASUMSI_MOMEN = ("[Asumsi: momen model 4.7 opsi A, konservatif karena kolom A (0,80/0,95) lebih kaku dan menarik momen lebih besar; "
                "analisis ulang model B bila Defsa minta]")


def _nama_kel(lv, b, bs):
    return f"K-TB {lv}" if len(bs) == 1 else f"K-TB{round(b * 1000)} {lv}"


def gaya_tangki(m, dengan_dd=True, b_alt=None):
    """Gaya terfaktor enam kolom tangki (K1 ∪ K2). Opsi B: D aksial ditambah dD = w_b - w_a (5.1) di LT2 dan LT3; b = b_B."""
    kb = m["kolom_b"]
    dd = {k: float(m["w_b"][k] - m["w_a"][k]) for k in KOLOM}
    if b_alt:     # opsi ukuran seragam: berat sendiri kolom 9 m ikut berubah (5.1: GC b² H_KOLOM)
        dd = {k: v + tn.GAMMA_C * (b_alt ** 2 - kb[k]["b_B"] ** 2) * tn.H_KOLOM for k, v in dd.items()}
    hs = []
    for h in m["hs"]:
        kol = {k: v for k, v in h["kolom"].items() if (k[1], k[2]) in dd}
        g = {c: {k: v for k, v in d.items() if k in kol} for c, d in h["gaya"].items()}
        if dengan_dd:
            nd = {}
            for k, a in g["D"].items():
                a = np.array(a, float).copy()
                if k[0] in SEG:
                    a[0] += dd[(k[1], k[2])]          # ujung bawah, tekan positif
                    a[6] -= dd[(k[1], k[2])]          # ujung atas: P = -lf[6]
                nd[k] = a
            g["D"] = nd
        hs.append({**h, "kolom": kol, "gaya": g})
    gk = kl.gaya_kolom(hs)
    for lv in SEG:
        bs = {round(kb[(k[1], k[2])]["b_B"], 4) for k in gk if k[0] == lv}
        for k, f in gk.items():
            if k[0] == lv:
                f["b"] = b_alt or kb[(k[1], k[2])]["b_B"]
                f["kelompok"] = _nama_kel(lv, f["b"], bs)
    return gk, dd


def joint_b(gk, m):
    """Joint kolom tangki; balok LT3 di bay tangki diganti balok opsi B (5.1), lainnya tetap dari 4.6."""
    joint = kl.joint_daftar(gk)
    peta = {frozenset(v[0]): (nama, v[1]) for nama, v in B_ELEMEN.items()}
    for j in joint:
        for sisi in j["balok"].values():
            for s, b in list(sisi.items()):
                if b and b["lv"] == "LT3" and frozenset((b["p1"], b["p2"])) in peta:
                    nama, tepi = peta[frozenset((b["p1"], b["p2"]))]
                    sisi[s] = {**b, "kel": {**m["balok_b"][nama], "_pelat": pelat_balok_b(nama)}, "tepi": tepi, "nama_b": nama}
    return joint


@functools.lru_cache(maxsize=1)
def as_pelat_b(t_b=None):
    """As pelat (mm²/m) lajur kolom pelat tangki opsi B (0,35 m, 5.1) pola `kl.tulangan_pelat`: (atas negatif dalam, bawah positif)."""
    m = data_mentah()
    pb = tn.pelat_b(t_b or m["t_b"], 0.40, 0.70)
    atas = max(x["As_ada"] for x in pb["baris"] if x["lajur"].startswith("kolom") and x["posisi"] == "neg_int")
    bawah = max(x["As_ada"] for x in pb["baris"] if x["lajur"].startswith("kolom") and x["posisi"] == "pos")
    return atas, bawah


def pelat_balok_b(nama):
    """As pelat ikut Mnb (atas, bawah) balok opsi B: sisi tangki (B) dan sisi standar (4.5) dirata-rata bila balok di antara keduanya;
    balok tepi y 75 hanya sisi tangki; balok standar (x 76, y 67 timur) pelat standar."""
    a_s, b_s = kl.tulangan_pelat()
    a_b, b_b = as_pelat_b()
    if nama in ("x 60", "x 68", "y 67 (x 60-68)"):
        return (a_b + a_s) / 2, (b_b + b_s) / 2
    if nama == "y 75 (x 60-68)":
        return a_b, b_b
    return a_s, b_s


def momen_balok_as(g, hc, tepi, s_atas, s_bawah, fy=kl.FY):
    """`kl.momen_balok` dengan As pelat (mm²/m) diberikan (SNI 2847:2019 18.7.3.2 hal 407, lebar sayap Tabel 6.3.2.1 hal 119)."""
    bw, h = g["b"], g["h"]
    lebar = kl.sayap(bw, hc, tepi) * (1 if tepi else 2)
    lap = [(g["atas"]["As"], g["atas"]["d"]), (s_atas * lebar, h - (kl.tp.SELIMUT + kl.tp.DB / 2)),
           (s_bawah * lebar, h - (kl.tp.H - kl.tp.SELIMUT - kl.tp.DB / 2))]
    t = sum(a for a, _ in lap) * fy
    a = t / (0.85 * kl.FC_B * bw * 1000)
    mneg = sum(a_ * fy * (d * 1000 - a / 2) for a_, d in lap) / 1e6
    be = bw + lebar
    ab = g["bawah"]["As"] * fy / (0.85 * kl.FC_B * be * 1000)
    mpos = g["bawah"]["As"] * fy * (g["bawah"]["d"] * 1000 - ab / 2) / 1e6
    return mneg, mpos


class pelat_tangki:
    """Konteks: `kl.momen_balok` memakai As pelat opsi B untuk balok bertanda `_pelat`; balok lain tetap metode 4.7."""

    def __enter__(self):
        self.asli = kl.momen_balok

        def mb(g, hc, tepi, fy=kl.FY):
            if g.get("_pelat"):
                return momen_balok_as(g, hc, tepi, *g["_pelat"], fy=fy)
            return self.asli(g, hc, tepi, fy)
        kl.momen_balok = mb

    def __exit__(self, *a):
        kl.momen_balok = self.asli


def _urut(nama):
    return (SEG.index(nama.split()[-1]), nama)


@functools.lru_cache(maxsize=2)
def hitung(b_alt=None):
    """Desain enam kolom tangki. b_alt None = ukuran 5.1 (b_B 0,80 seragam, keputusan Defsa 21 Nov 2026); b_alt 0,75 = pembanding 750."""
    m = data_mentah()
    gk, dd = gaya_tangki(m, b_alt=b_alt)
    gk0, _ = gaya_tangki(m, dengan_dd=False)
    joint = joint_b(gk, m)
    with pelat_tangki():
        kel, tul, idx_pm = kl.desain(gk, joint)
        for j in joint:
            j["scwb"] = kl.cek_joint(j, gk, tul)
    jm = {}
    for j in joint:
        j["geser"] = kl.geser_joint(j, gk)
        jm[j["bawah"]] = j
    grup = []
    for g in sorted(kel, key=_urut):
        ks = sorted(kel[g])
        b = gk[ks[0]]["b"]
        ast, mm, db = tul[g]
        dg = kl.diagram(b, mm, db)
        terburuk, per_kolom = None, {}
        for k in ks:
            rr = kl.rasio_pm(gk[k], dg)
            i, e = np.unravel_index(np.argmax(rr), rr.shape)
            fk = gk[k]["F"][i, e]
            d_ = {"kunci": k, "rasio": float(rr[i, e]), "Pu": float(fk[0]), "Mux": abs(float(fk[1])), "Muy": abs(float(fk[2])),
                  "phiMn": float(kl.mn_pada(dg, fk[0], desain=True)), "ujung": "atas" if e else "bawah", "kombinasi": int(i)}
            per_kolom[k] = d_
            if terburuk is None or d_["rasio"] > terburuk["rasio"]:
                terburuk = d_
        sc = [dict(c, joint=(j["lv"], j["x"], j["y"])) for j in joint if j["bawah"] in ks for c in j["scwb"]]
        gj = [dict(c, joint=(j["lv"], j["x"], j["y"])) for j in joint if j["bawah"] in ks for c in j["geser"]]
        gs = kl.geser_kolom(g, ks, gk, tul, jm)
        grup.append({"kelompok": g, "lv": ks[0][0], "kolom": ks, "n": len(ks), "b": b, "m": mm, "db": db, "n_batang": 4 * (mm - 1),
                     "Ast": ast, "rho": ast / (b * 1000) ** 2, "pm": terburuk, "per_kolom": per_kolom, "dg": dg,
                     "awal_pm": kl.pilihan_tulangan(b)[idx_pm[g]], "scwb_semua": sc, "scwb_min": min(sc, key=lambda c: c["rasio"]),
                     "scwb_gagal": sum(c["rasio"] < 1.2 for c in sc), "hbk_semua": gj, "hbk": max(gj, key=lambda c: c["rasio"]),
                     "geser": gs, "Pu_maks": max(float(gk[k]["F"][:, :, 0].max()) for k in ks),
                     "Pu_min": min(float(gk[k]["F"][gk[k]["gempa"], :, 0].min()) for k in ks)})
    for x in grup:
        x["cek"] = {"rho": 0.01 <= x["rho"] <= 0.06, "pm": x["pm"]["rasio"] <= 1.0, "scwb": x["scwb_gagal"] == 0, "geser": x["geser"]["ok"],
                    "hbk": all(c["rasio"] <= 1.0 and c["hc_20db"] and c["ldh_ok"] and c["h_joint"] for c in x["hbk_semua"])}
        x["ok"] = all(x["cek"].values())
        if x["ok"]:
            x["usulan"] = None
        else:
            with pelat_tangki():
                x["usulan"] = kl.usulan_ukuran(x["kelompok"], [k for k in kel[x["kelompok"]]], gk, joint, tul)
    return {"m": m, "gk": gk, "gk0": gk0, "dd": dd, "joint": joint, "grup": grup, "tul": tul, "b_alt": b_alt}


# ================================================================== sensitivitas
def peka_momen(r):
    """Indikatif: momen model 4.7 dikali (b_B/b_A)^4 (kekakuan relatif kolom opsi B terhadap A) pada tulangan terpilih.
    [Asumsi indikatif: bukan hasil analisis; batas bawah momen bila kolom B ikut model]. {kunci: rasio P-M}."""
    kb = r["m"]["kolom_b"]
    out = {}
    for x in r["grup"]:
        for k in x["kolom"]:
            f = r["gk"][k]
            sk = (x["b"] / kb[(k[1], k[2])]["b_A"]) ** 4
            f2 = dict(f, F=f["F"] * np.array([1.0, sk, sk, 1.0, 1.0]))
            out[k] = float(kl.rasio_pm(f2, x["dg"]).max())
    return out


def peka_pelat(r):
    """ΣMnc/ΣMnb terkecil per kelompok bila balok opsi B memakai As pelat standar 4.5 (metode 4.7 apa adanya, tanpa pelat tangki 0,35 m)."""
    out = {x["kelompok"]: min(c["rasio"] for j in r["joint"] if j["bawah"] in x["kolom"] for c in kl.cek_joint(j, r["gk"], r["tul"]))
           for x in r["grup"]}
    return {"As_std": kl.tulangan_pelat(), "As_B": as_pelat_b(), "scwb_min": out}


# ================================================================== stek ke pile cap 1.200 dan dampak ke 5.6
def _pen():
    import tahap5_penerusan as pe
    return pe


def stek_hitung(pe, b, mm, db, ast, s_lo, lo, kaki, pu_max, pu_min, vu):
    """Pola `tahap5_penerusan.stek_kolom` untuk satu susunan tulangan (SNI 2847:2019 25.4.3 hal 591, 25.4.2 hal 587-590, 25.4.9 hal 604, 22.8.3.2 hal 540,
    16.3.4 hal 312, 16.3.5 hal 312-313). b dalam m."""
    ver, lur = pe.tersedia()
    bersih = (b * 1000 - 2 * kl.SEL - 2 * kl.DS - db) / (mm - 1) - db
    koef = 1.7 if (bersih >= 2 * db and (kl.SEL + kl.DS) >= db) else 1.1
    ag = (b * 1000) ** 2
    mu = 0.6      # [Asumsi 5.6: koefisien friksi 0,6; Tabel 22.9.4.2 tidak terbaca di PDF]
    return {"b": b, "m": mm, "db": db, "Ast": ast, "n_batang": 4 * (mm - 1), "bersih": bersih, "koef": koef, "ldh": pe.ldh_2543(db),
            "ld": pe.ld_tarik(db, koef), "ldc": pe.ldc(db), "ver": ver, "lur": lur, "s_lo": s_lo, "lo": lo, "kaki": kaki,
            "n_sengkang": math.ceil(ver / s_lo), "pu_max": pu_max, "pu_min": pu_min, "vu": vu, "phiBn": pe.tumpu(b ** 2),
            "as_min": 0.005 * ag, "phiTn": 0.9 * ast * pe.FY / 1000, "phiVn": 0.75 * mu * ast * pe.FY / 1000, "mu": mu,
            "tarik": pu_min < 0, "ok_ldh": pe.ldh_2543(db) <= ver, "ok_ld": pe.ld_tarik(db, koef) <= lur,
            "ok_tumpu": pu_max <= pe.tumpu(b ** 2), "ok_asmin": ast >= 0.005 * ag, "ok_tarik": (pu_min >= 0) or (0.9 * ast * pe.FY / 1000 >= -pu_min),
            "ok_geser": vu <= 0.75 * mu * ast * pe.FY / 1000}


def titik_tangki(h56):
    return {(r["x"], r["y"]): r for r in h56["titik"] if r["kel"] == "K-T B"}


def stek_dan_dampak(r, h56=None):
    """Stek kolom tangki ke cap dengan tulangan baru (kelompok LT2 hasil `hitung`) dan dampaknya ke reaksi 5.6.
    Reaksi 5.6 sudah memakai ukuran b_B (stek dan D opsi B); bila b baru (opsi 800) berbeda, selisih berat dihitung."""
    pe = _pen()
    h56 = h56 or pe.hitung()
    tk = titik_tangki(h56)
    g = [x for x in r["grup"] if x["lv"] == "LT2"][0]
    gs = g["geser"]
    kb = r["m"]["kolom_b"]
    h_stek = pe.BAWAH_PELAT - pe.HALAMAN
    baris = []
    for k in KOLOM:
        t = tk[k]
        b_56 = kb[k]["b_B"]
        d_w = pe.GC * (g["b"] ** 2 - b_56 ** 2) * (tn.H_KOLOM + h_stek)        # kN, layan (D)
        pu56 = t["amp"]["ult"]["Pmax_dP"]
        baris.append({"kunci": k, "id": t["id"], "b_56": b_56, "b_baru": g["b"], "dW": d_w, "Pu_56": pu56, "Pu_baru": pu56 + 1.4 * d_w,
                      "Pmin_56": t["amp"]["ult"]["Pmin_dP"], "Pmin_baru": t["amp"]["ult"]["Pmin_dP"] + (0.9 - pe.EV) * d_w,
                      "Pl_56": t["amp"]["lay"]["Pmax_dP"], "Pl_baru": t["amp"]["lay"]["Pmax_dP"] + d_w, "Vu": t["amp"]["ult"]["Vmax"]})
    pu_max = max(x["Pu_baru"] for x in baris)
    pu_min = min(x["Pmin_baru"] for x in baris)
    vu = max(x["Vu"] for x in baris)
    baru = stek_hitung(pe, g["b"], g["m"], g["db"], g["Ast"], gs["s_lo"], gs["lo"], gs["kaki"], pu_max, pu_min, vu)
    lama_h = [x for x in pe.stek_kolom(h56) if x["kel"] == "K-T B"][0]
    ok = stek_hitung(pe, lama_h["b"], lama_h["m"], lama_h["db"], lama_h["Ast"], lama_h["s_lo"], lama_h["lo"], lama_h["kaki"],
                     lama_h["pu_max"], lama_h["pu_min"], lama_h["vu"])
    lama = {**lama_h, **{k_: ok[k_] for k_ in ("ok_tumpu", "ok_asmin", "ok_tarik", "ok_geser")}}     # 5.6 apa adanya (tumpu dan As min pada b kolom tangki)
    return {"baris": baris, "baru": baru, "lama": lama, "lama_pe": lama_h, "tul_lama": (lama_h["n_batang"], lama_h["db"], lama_h["tul_dari"])}


# ================================================================== cek silang T-96
def mn_tangan(r, nama="x 68", hc=0.75, tepi=False):
    """Mn- dan Mn+ balok opsi B (kNm) dengan blok tegangan persegi ditulis ulang tanpa memanggil `kl.momen_balok`:
    Mn = Σ As fy (d - a/2), a = Σ As fy / (0,85 fc' bw); Mn+ dengan lebar sayap efektif (Tabel 6.3.2.1 hal 119)."""
    g = r["m"]["balok_b"][nama]
    sa, sb = pelat_balok_b(nama)
    bw, h, fy, fc = g["b"], g["h"], 420.0, 30.0
    sayap = min(8 * 0.20, (8.0 - bw) / 2, (8.0 - hc) / 8) if not tepi else min(6 * 0.20, (8.0 - bw) / 2, (8.0 - hc) / 12)
    lebar = sayap * (1 if tepi else 2)
    sel, db_s = 20.0, 13.0                                              # selimut dan D13 pelat (mm)
    lap = [(g["atas"]["As"], g["atas"]["d"] * 1000), (sa * lebar, h * 1000 - sel - db_s / 2),
           (sb * lebar, h * 1000 - (200.0 - sel - db_s / 2))]
    a = sum(x for x, _ in lap) * fy / (0.85 * fc * bw * 1000)
    mneg = sum(x * fy * (d - a / 2) for x, d in lap) / 1e6
    be = bw * 1000 + lebar * 1000
    ab = g["bawah"]["As"] * fy / (0.85 * fc * be)
    mpos = g["bawah"]["As"] * fy * (g["bawah"]["d"] * 1000 - ab / 2) / 1e6
    return mneg, mpos


def t96(r):
    """T-96: (a) Mn satu sumbu: diagram sendiri vs concreteproperties; (b) Mn balok x 68 opsi B: `kl.momen_balok` vs hitung tangan;
    (c) Pu maks (68;67) LT2: gaya 5.6a vs Pu_B 5.1; (d) Excel = Python (di `cek_excel`)."""
    gov = max(r["grup"], key=lambda x: x["pm"]["rasio"])
    cp = kl.cek_concreteproperties(gov)
    with pelat_tangki():
        mn_py = kl.momen_balok({**r["m"]["balok_b"]["x 68"], "_pelat": pelat_balok_b("x 68")}, 0.75, False)
    mn_h = mn_tangan(r)
    k = ("LT2", 68.0, 67.0)
    pu56a = float(r["gk"][k]["F"][:, :, 0].max())
    pu_a = float(r["gk0"][k]["F"][:, :, 0].max())
    pu_b = float(r["m"]["kolom_b"][(68.0, 67.0)]["Pu_B"])
    return {"a": {"kel": gov["kelompok"], "Pn": cp["Pn"], "sendiri": cp["Mn_sendiri"], "cp": cp["Mn_cp"], "sudut": cp["sudut"]},
            "b": {"neg": (mn_py[0], mn_h[0]), "pos": (mn_py[1], mn_h[1])},
            "c": {"Pu_5.6a": pu56a, "Pu_A": pu_a, "Pu_B": pu_b, "dD": r["dd"][(68.0, 67.0)]}, "tol": dict(TOL)}


def selisih(c1, c2):
    return abs(c2 / c1 - 1.0) * 100.0


# ================================================================== Excel
NAMA = ["Ringkasan", "Gaya dan Kombinasi", "P-M", "Kolom Kuat Balok Lemah", "Geser Joint", "Geser dan Pengekang", "Stek ke Pile Cap",
        "Dampak ke 5.6", "Cek Silang T-96"]
LABEL_AI = f"DIISI AI ATAS PERMINTAAN DEFSA (21 Nov 2026), sel hijau; {STATUS}. Kunci jawaban tidak dibuka."
N0, N1, N2, N3 = "#,##0", "#,##0.0", "0.00", "0.000"


def _opsi(r):
    return "750 (pembanding)" if r["b_alt"] else "800 seragam (keputusan)"


def _kn(k):
    return f"({k[-2]:.0f};{k[-1]:.0f})"


def _jn(j):
    return f"{j[0]} ({j[1]:.0f};{j[2]:.0f})"


def _baris_ringkasan(r7, r8):
    """Baris lembar Ringkasan: 5.6a opsi 750 dan 800, pembanding 4.7 (K-T LT2/LT3 dan K-T68)."""
    out = []
    for r in (r7, r8):
        for x in r["grup"]:
            gs = x["geser"]
            out.append({"kel": x["kelompok"], "opsi": _opsi(r), "b": x["b"] * 1000, "n": x["n_batang"], "db": x["db"], "Ast": x["Ast"], "rho": x["rho"],
                        "pm": x["pm"]["rasio"], "scwb": x["scwb_min"]["rasio"], "hbk": x["hbk"]["rasio"], "Ve": gs["Ve"], "s": gs["s_lo"], "lo": gs["lo"]})
    for x in r7["m"]["rk"]:
        if x["kelompok"].startswith("K-T"):
            gs = x["geser"]
            out.append({"kel": x["kelompok"], "opsi": "4.7 (A)", "b": x["b"] * 1000, "n": x["n_batang"], "db": x["db"], "Ast": x["Ast"], "rho": x["rho"],
                        "pm": x["pm"]["rasio"], "scwb": x["scwb_min"]["rasio"], "hbk": x["hbk"]["rasio"], "Ve": gs["Ve"], "s": gs["s_lo"], "lo": gs["lo"]})
    return out


def _r(v):
    """Bulatkan angka tampilan (tinggi baris Excel dihitung dari panjang teks); selisih <= 0,05 % terhadap Python."""
    if isinstance(v, (float, np.floating)):
        v = float(v)
        return round(v, 1) if abs(v) >= 100 else (round(v, 2) if abs(v) >= 10 else round(v, 4))
    return v


def buat_excel(keluar=BERKAS, hitung_ulang=True):
    import openpyxl
    import format_dokumen as fd
    from format_dokumen import AI, hitung_ulang_excel, set_font_bawaan

    class Lembar(fd.Lembar):
        def tabel(self, kepala, baris, **kw):
            return super().tabel(kepala, [[_r(v) for v in row] for row in baris], **kw)
    r7, r8 = hitung(0.75), hitung()
    st7, st8 = stek_dan_dampak(r7), stek_dan_dampak(r8)
    pp, pm7 = peka_pelat(r8), peka_momen(r7)
    tt = t96(r8)
    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)
    ket = LABEL + " " + LABEL_AI

    # ---------------- 1 Ringkasan
    lb = Lembar(wb.create_sheet("Ringkasan"), 1, "Ringkasan 5.6a: enam kolom tangki opsi B", [18, 13, 9, 9, 7, 11, 9, 10, 12, 12, 10, 10, 8, 16])
    k = lb.kol
    lb.catatan(ket + " Gaya dari model 4.7 (opsi A) + koreksi aksial D opsi B (5.1). Rasio P-M Bresler α = 1 (kombinasi 4.7). ΣMnc/ΣMnb (SNI 2847:2019 18.7.3.2 hal 407) "
               "terkecil semua joint. Rasio geser joint = Vj / φVn (18.8.4.1, hal 417-418). Pembanding 4.7: kelompok K-T (800) dan K-T68 (950) pada model A.")
    lb.kosong()
    rows = _baris_ringkasan(r7, r8)
    _, a0, a1 = lb.tabel(["Kelompok", "Opsi", "b (mm)", "n batang", "D (mm)", "Ast (mm²)", "ρ", "Rasio P-M", "ΣMnc/ΣMnb min", "Rasio geser joint", "Ve (kN)",
                          "s di lo (mm)", "lo (mm)", "Status"],
                         [[x["kel"], x["opsi"], x["b"], x["n"], x["db"], None, None, x["pm"], x["scwb"], x["hbk"], x["Ve"], x["s"], x["lo"], None] for x in rows],
                         rata=list("llcccccccccccc"), fmt=[None, None, "0", "0", "0", N0, "0.0000", N3, N2, N2, N0, "0", "0", None],
                         fill_kolom={i: AI for i in range(2, 14)})
    for i in range(len(rows)):
        rr = a0 + i
        lb.ws[f"{k(5)}{rr}"] = f"={k(3)}{rr}*PI()*{k(4)}{rr}^2/4"
        lb.ws[f"{k(6)}{rr}"] = f"={k(5)}{rr}/{k(2)}{rr}^2"
        lb.ws[f"{k(13)}{rr}"] = f'=IF(AND({k(7)}{rr}<=1,{k(8)}{rr}>=1.2,{k(9)}{rr}<=1),"Memenuhi","Tidak memenuhi")'
    lb.kosong()
    lb.bagian("B", "Asumsi dan keterbatasan")
    lb.catatan(f"1. {ASUMSI_MOMEN} Rasio P-M indikatif bila momen model 4.7 dikali (b_B/b_A)^4: maksimum {max(pm7.values()):.2f} (bukan hasil analisis). "
               "2. Aksial D opsi B: dD = w_B - w_A (5.1) ditambahkan di LT2 dan LT3 (konservatif untuk LT3: dD memuat berat kolom 9 m). "
               f"3. ΣMnb balok atap podium opsi B memakai As pelat tangki 0,35 m (atas {pp['As_B'][0]:,.0f}, bawah {pp['As_B'][1]:,.0f} mm²/m) dirata-rata dengan pelat standar 4.5 "
               f"({pp['As_std'][0]:,.0f} mm²/m) bagi balok di antara dua pelat; metode 4.7 apa adanya (pelat standar saja) memberi ΣMnc/ΣMnb min LT3 {pp['scwb_min'].get('K-TB LT3', 0):.2f} (tidak dipakai, tidak konservatif). "
               "4. Joint LT3 = atap podium, tidak ada kolom di atasnya: Mnc hanya kolom bawah; SNI 2847:2019 18.7.3.2 (hal 407) tidak memberi pengecualian untuk joint teratas. "
               "5. Kolom LT2 dan LT3 satu kelompok per segmen (keputusan Defsa 21 Nov 2026: 800 seragam; 750 hanya pembanding).")

    # ---------------- 2 Gaya dan Kombinasi
    lb = Lembar(wb.create_sheet("Gaya dan Kombinasi"), 2, "Gaya kolom tangki: koreksi aksial D opsi B dan kombinasi", [14, 9, 9, 13, 13, 13, 13, 13, 15, 15])
    lb.catatan(ket + " dD = w_B - w_A: selisih reaksi layan D opsi B terhadap A (5.1, `tahap5_tangki.hitung`). Ditambahkan ke D aksial di segmen LT2 dan LT3, "
               "dikali faktor D tiap kombinasi (SNI 1726:2019 4.2.2.3 hal 38-39, Ev = 0,2 SDS D hal 77). " + ASUMSI_MOMEN)
    lb.kosong()
    lb.bagian("A", "Parameter")
    _, p0, _ = lb.tabel(["Parameter", "Nilai", "Sumber"], [["SDS", tb.SDS, "SNI 1726:2019, 4.2 (tahap4_beban)"]], rata=list("lcl"), fmt=[None, N3, None],
                        fill_kolom={1: AI}, beku=False)
    sds = f"${k(1)}${p0}"
    lb.kosong()
    lb.bagian("B", "Koreksi aksial D opsi B per kolom")
    _, d0, d1 = lb.tabel(["Titik", "x (m)", "y (m)", "w A (kN)", "w B (kN)", "dD (kN)", "ΔP 1,4 D (kN)", "ΔP 1,2 D (kN)", "ΔP (1,2 + 0,2 SDS) D (kN)", "ΔP (0,9 - 0,2 SDS) D (kN)"],
                         [[f"({x:.0f};{y:.0f})", x, y, r8["m"]["w_a"][(x, y)], r8["m"]["w_b"][(x, y)], None, None, None, None, None] for (x, y) in KOLOM],
                         rata=list("lccccccccc"), fmt=[None, "0", "0", N1, N1, N1, N1, N1, N1, N1], fill_kolom={i: AI for i in range(3, 10)}, beku=True)
    for i in range(len(KOLOM)):
        rr = d0 + i
        lb.ws[f"{k(5)}{rr}"] = f"={k(4)}{rr}-{k(3)}{rr}"
        lb.ws[f"{k(6)}{rr}"] = f"=1.4*{k(5)}{rr}"
        lb.ws[f"{k(7)}{rr}"] = f"=1.2*{k(5)}{rr}"
        lb.ws[f"{k(8)}{rr}"] = f"=(1.2+0.2*{sds})*{k(5)}{rr}"
        lb.ws[f"{k(9)}{rr}"] = f"=(0.9-0.2*{sds})*{k(5)}{rr}"
    lb.kosong()
    lb.bagian("C", "Aksial maksimum per kolom dan segmen (semua kombinasi, K1 dan K2)")
    kk = [(lv, x, y) for lv in SEG for (x, y) in KOLOM]
    _, g0, g1 = lb.tabel(["Kolom", "Segmen", "b (mm)", "Pu maks A (kN)", "Pu maks B (kN)", "ΔPu (kN)", "Pu min gempa B (kN)", "Vu maks B (kN)"],
                         [[_kn(q), q[0], r8["gk"][q]["b"] * 1000, float(r8["gk0"][q]["F"][:, :, 0].max()), float(r8["gk"][q]["F"][:, :, 0].max()), None,
                           float(r8["gk"][q]["F"][r8["gk"][q]["gempa"], :, 0].min()), float(np.abs(r8["gk"][q]["F"][:, 0, 3:5]).max())] for q in kk],
                         rata=list("lcccccccc")[:8], fmt=[None, None, "0", N1, N1, N1, N1, N1], fill_kolom={i: AI for i in range(2, 8)}, beku=False)
    for i in range(len(kk)):
        lb.ws[f"{k(5)}{g0 + i}"] = f"={k(4)}{g0 + i}-{k(3)}{g0 + i}"
    lb.kosong()
    lb.catatan("Pu maks A = model 4.7 tanpa koreksi (opsi A). ΔPu = koefisien D kombinasi penentu × dD (1,2 bila 1,2 D + 1,6 L, 1,2772 bila gempa menentukan).")

    # ---------------- 3 P-M
    lb = Lembar(wb.create_sheet("P-M"), 3, "Cek interaksi P-M dua arah kolom tangki", [18, 13, 9, 9, 7, 11, 9, 12, 12, 14, 11, 11, 11, 10, 18])
    lb.catatan(ket + " Ast = n π D²/4; ρ = Ast/b²; Po = 0,85 fc' (b² - Ast) + fy Ast (22.4.2.2); φPn,maks = 0,65 × 0,80 Po (Tabel 22.4.2.1, hal 502); fc' 35, fy 420 MPa. "
               "φMn(Pu) dari diagram interaksi rapat Python (εcu 0,003, φ Tabel 21.2.2 hal 493). Rasio Bresler kontur beban α = 1: (|Mux| + |Muy|)/φMn(Pu) <= 1, semua kombinasi dan dua ujung. " + ASUMSI_MOMEN + " Rasio indikatif = rasio P-M bila momen model 4.7 dikali (b_B/b_A)^4 (kekakuan relatif; bukan hasil analisis).")
    lb.kosong()
    gr = [(r, x) for r in (r7, r8) for x in r["grup"]]
    _, m0, m1 = lb.tabel(["Kelompok", "Opsi", "b (mm)", "n batang", "D (mm)", "Ast (mm²)", "ρ", "Po (kN)", "φPn,maks (kN)", "Pu penentu (kN)", "Mux (kNm)", "Muy (kNm)", "φMn (kNm)",
                          "Rasio P-M", "Status"],
                         [[x["kelompok"], _opsi(r), x["b"] * 1000, x["n_batang"], x["db"], None, None, None, float(x["dg"]["phiPmax"]), x["pm"]["Pu"], x["pm"]["Mux"], x["pm"]["Muy"],
                           x["pm"]["phiMn"], None, None] for r, x in gr],
                         rata=list("llcccccccccccc") + ["c"], fmt=[None, None, "0", "0", "0", N0, "0.0000", N0, N0, N0, N0, N0, N0, N3, None],
                         fill_kolom={i: AI for i in range(2, 15)})
    # Po (kolom 7) dan φPn,maks (kolom 8): Po rumus, φPn,maks rumus; nilai Python phiPmax dipakai hanya sebagai pembanding di cek_excel
    for i in range(len(gr)):
        rr = m0 + i
        lb.ws[f"{k(5)}{rr}"] = f"={k(3)}{rr}*PI()*{k(4)}{rr}^2/4"
        lb.ws[f"{k(6)}{rr}"] = f"={k(5)}{rr}/{k(2)}{rr}^2"
        lb.ws[f"{k(7)}{rr}"] = f"=(0.85*35*({k(2)}{rr}^2-{k(5)}{rr})+420*{k(5)}{rr})/1000"
        lb.ws[f"{k(8)}{rr}"] = f"=0.65*0.8*{k(7)}{rr}"
        lb.ws[f"{k(13)}{rr}"] = f"=({k(10)}{rr}+{k(11)}{rr})/{k(12)}{rr}"
        lb.ws[f"{k(14)}{rr}"] = f'=IF({k(13)}{rr}<=1,"Memenuhi","Tidak memenuhi")'
    lb.kosong()
    lb.bagian("B", "Rasio P-M per kolom (kombinasi dan ujung penentu)")
    pk = [(r, x, q, d) for r in (r7, r8) for x in r["grup"] for q, d in x["per_kolom"].items()]
    _, q0, q1 = lb.tabel(["Titik", "Opsi", "Segmen", "Pu (kN)", "Mux (kNm)", "Muy (kNm)", "φMn (kNm)", "Rasio P-M", "Ujung", "Rasio indikatif"],
                         [[_kn(q), _opsi(r), q[0], d["Pu"], d["Mux"], d["Muy"], d["phiMn"], None, d["ujung"], (pm7[q] if r["b_alt"] else None)] for r, x, q, d in pk],
                         rata=list("llccccccc") + ["c"], fmt=[None, None, None, N0, N0, N0, N0, N3, None, N2], fill_kolom={i: AI for i in range(3, 10)}, beku=False)
    for i in range(len(pk)):
        lb.ws[f"{k(7)}{q0 + i}"] = f"=({k(4)}{q0 + i}+{k(5)}{q0 + i})/{k(6)}{q0 + i}"

    # ---------------- 4 SCWB
    lb = Lembar(wb.create_sheet("Kolom Kuat Balok Lemah"), 4, "Kolom kuat balok lemah di joint kolom tangki (18.7.3.2)", [16, 13, 7, 12, 12, 12, 12, 12, 12, 12, 11, 15])
    lb.catatan(ket + " ΣMnc >= 1,2 ΣMnb (SNI 2847:2019 18.7.3.2, hal 407). Mnc: Mn terendah pada Pu kombinasi gempa, tiap kolom di joint (diagram P-M, tulangan terpilih). "
               "Mnb = Mn- satu sisi + Mn+ sisi lain (kombinasi terbesar), tulangan pelat dalam lebar sayap Tabel 6.3.2.1 (hal 119). Joint LT3 (atap podium): balok opsi B (5.1); tidak ada kolom di atasnya.")
    lb.kosong()
    js = [(r, x, c) for r in (r7, r8) for x in r["grup"] for c in x["scwb_semua"]]
    _, s0, s1 = lb.tabel(["Joint", "Opsi", "Arah", "Mnc bawah (kNm)", "Mnc atas (kNm)", "ΣMnc (kNm)", "Mnb sisi kiri (kNm)", "Mnb sisi kanan (kNm)", "ΣMnb (kNm)", "1,2 ΣMnb (kNm)",
                          "ΣMnc/ΣMnb", "Status"],
                         [[_jn(c["joint"]), _opsi(r), c["arah"], c["Mnc_bawah"], c["Mnc_atas"], None, c["Mnb_kiri"], c["Mnb_kanan"], None, None, None, None] for r, x, c in js],
                         rata=list("llcccccccccc"), fmt=[None, None, None, N0, N0, N0, N0, N0, N0, N0, N2, None], fill_kolom={i: AI for i in range(3, 12)})
    for i in range(len(js)):
        rr = s0 + i
        lb.ws[f"{k(5)}{rr}"] = f"={k(3)}{rr}+{k(4)}{rr}"
        lb.ws[f"{k(8)}{rr}"] = f"={k(6)}{rr}+{k(7)}{rr}"
        lb.ws[f"{k(9)}{rr}"] = f"=1.2*{k(8)}{rr}"
        lb.ws[f"{k(10)}{rr}"] = f"={k(5)}{rr}/{k(8)}{rr}"
        lb.ws[f"{k(11)}{rr}"] = f'=IF({k(5)}{rr}>={k(9)}{rr},"Memenuhi","Tidak memenuhi")'
    lb.kosong()
    lb.bagian("B", "Balok opsi B di atap podium LT3 (5.1)")
    bb = r7["m"]["balok_b"]
    _, b0, b1 = lb.tabel(["Balok", "b (mm)", "h (mm)", "As atas (mm²)", "As bawah (mm²)", "As pelat atas (mm²/m)", "As pelat bawah (mm²/m)", "Mpr- (kNm)", "Mpr+ (kNm)"],
                         [[nama, v["b"] * 1000, v["h"] * 1000, v["atas"]["As"], v["bawah"]["As"], pelat_balok_b(nama)[0], pelat_balok_b(nama)[1], v["Mpr_neg"], v["Mpr_pos"]]
                          for nama, v in bb.items()], rata=list("lcccccccc")[:9], fmt=[None, "0", "0", N0, N0, N0, N0, N0, N0], fill_kolom={i: AI for i in range(1, 9)}, beku=False)
    lb.catatan("Balok x 68, x 60, y 67 (x 60-68): pelat tangki (B) satu sisi dan standar (4.5) sisi lain: As pelat dirata-rata; y 75 (tepi): pelat tangki saja; balok standar: pelat 4.5. "
               "Balok 4.6 di luar bay tangki dan di LT2 tetap dari 4.6.")

    # ---------------- 5 Geser Joint
    lb = Lembar(wb.create_sheet("Geser Joint"), 5, "Geser joint (18.8.4.1) dengan balok opsi B", [16, 13, 7, 9, 10, 7, 12, 12, 12, 12, 12, 11, 12, 14])
    lb.catatan(ket + " Vj = 1,25 fy (As1 + As2) - Vkol (18.8.2.1, hal 414); Vkol = ΣMpr balok / tinggi rata-rata dua tingkat. φVn = 0,85 γ √fc' Aj (Tabel 18.8.4.1 hal 417-418; φ 0,85 Pasal 21.2.4.3 hal 496), "
               "Aj = hc² (lebar balok < 3/4 hc: tidak ada muka terkekang, γ 1,0). hc >= 20 db balok (18.8.2.3), hc >= h balok / 2 (18.8.2.4), ldh (18.8.5.1 hal 418).")
    lb.kosong()
    gj = [(r, x, c) for r in (r7, r8) for x in r["grup"] for c in x["hbk_semua"]]
    _, h0, h1 = lb.tabel(["Joint", "Opsi", "Arah", "hc (mm)", "n muka terkekang", "γ", "Aj (mm²)", "T = 1,25 fy ΣAs (kN)", "Vkol (kN)", "Vj (kN)", "φVn (kN)", "Rasio Vj/φVn", "hc, h joint, ldh", "Status"],
                         [[_jn(c["joint"]), _opsi(r), c["arah"], c["Aj"] ** 0.5 * 1000, c["n_terkekang"], c["gamma"], None, c["T"], c["Vkol"], None, None, None,
                           "ya" if (c["hc_20db"] and c["h_joint"] and c["ldh_ok"]) else "tidak", None] for r, x, c in gj],
                         rata=list("llcccccccccccc"), fmt=[None, None, None, "0", "0", "0.0", N0, N0, N0, N0, N0, N2, None, None], fill_kolom={i: AI for i in range(3, 14)})
    for i in range(len(gj)):
        rr = h0 + i
        lb.ws[f"{k(6)}{rr}"] = f"={k(3)}{rr}^2"
        lb.ws[f"{k(9)}{rr}"] = f"={k(7)}{rr}-{k(8)}{rr}"
        lb.ws[f"{k(10)}{rr}"] = f"=0.85*{k(5)}{rr}*SQRT(35)*{k(6)}{rr}/1000"
        lb.ws[f"{k(11)}{rr}"] = f"={k(9)}{rr}/{k(10)}{rr}"
        lb.ws[f"{k(13)}{rr}"] = f'=IF(AND({k(11)}{rr}<=1,{k(12)}{rr}="ya"),"Memenuhi","Tidak memenuhi")'

    # ---------------- 6 Geser dan Pengekang
    lb = Lembar(wb.create_sheet("Geser dan Pengekang"), 6, "Geser kolom (18.7.6) dan pengekang (18.7.5)", [20, 13, 9, 10, 10, 10, 11, 11, 10, 11, 11, 10, 12])
    lb.catatan(ket + " Ve = maks(min(Ve1; Ve2); Vu); Ve1 = 2 Mpr,c / lu, Ve2 = (Ma + Mb)/lu, Mpr dari 1,25 fy (18.7.6.1, hal 413). Vc = 0 bila Pu min < Ag fc'/20 (18.7.6.2.1, hal 414), "
               "selain itu Pers. 22.5.6.1 (hal 508). Pengekang: lo = maks(b; lu/6; 450) (18.7.5.1 hal 408); Ash/(s bc) Tabel 18.7.5.4 (a) 0,3(Ag/Ach - 1) fc'/fyt, (b) 0,09 fc'/fyt, "
               "(c) 0,2 kf kn Pu/(fyt Ach) (hal 411-412); s <= b/4, 6 db, so (18.7.5.3, hal 410). Ma, Mb: ΣMpr balok joint dengan balok opsi B di LT3.")
    lb.kosong()
    gg = [(r, x) for r in (r7, r8) for x in r["grup"]]
    _, v0, v1 = lb.tabel(["Kelompok", "Opsi", "lu (m)", "Mpr,c (kNm)", "Ma (kNm)", "Mb (kNm)", "Ve1 (kN)", "Ve2 (kN)", "Vu (kN)", "Ve (kN)", "Pu min (kN)", "Vc (kN)", "Av/s (mm²/mm)"],
                         [[x["kelompok"], _opsi(r), x["geser"]["lu"], x["geser"]["Mpr_c"], x["geser"]["M_atas"], x["geser"]["M_bawah"], None, None, x["geser"]["Vu"], None,
                           x["geser"]["Pu_min_kel"], x["geser"]["Vc"], x["geser"]["Av_s"]] for r, x in gg],
                         rata=list("llcccccccccc") + ["c"], fmt=[None, None, N2, N0, N0, N0, N0, N0, N0, N0, N0, N0, N3], fill_kolom={i: AI for i in range(2, 13)})
    for i in range(len(gg)):
        rr = v0 + i
        lb.ws[f"{k(6)}{rr}"] = f"=2*{k(3)}{rr}/{k(2)}{rr}"
        lb.ws[f"{k(7)}{rr}"] = f"=({k(4)}{rr}+{k(5)}{rr})/{k(2)}{rr}"
        lb.ws[f"{k(9)}{rr}"] = f"=MAX(MIN({k(6)}{rr},{k(7)}{rr}),{k(8)}{rr})"
    lb.kosong()
    lb.bagian("B", "Pengekang di lo")
    _, e0, e1 = lb.tabel(["Kelompok (pengekang)", "Opsi", "bc (mm)", "Ach (mm²)", "ra", "rb", "rc", "Rasio Ash/(s bc) maks", "Kaki D13", "Ash (mm²)", "s dari Ash (mm)", "s dari geser (mm)", "s di lo (mm)"],
                         [[x["kelompok"], _opsi(r), x["geser"]["bc"], x["geser"]["Ach"], x["geser"]["ra"], x["geser"]["rb"], x["geser"]["rc"], None, x["geser"]["kaki"], None, None,
                           x["geser"]["s_v"], x["geser"]["s_lo"]] for r, x in gg],
                         rata=list("llcccccccccc") + ["c"], fmt=[None, None, "0", N0, "0.0000", "0.0000", "0.0000", "0.0000", "0", N0, N1, N1, "0"],
                         fill_kolom={i: AI for i in range(2, 13)}, beku=False)
    for i in range(len(gg)):
        rr = e0 + i
        lb.ws[f"{k(7)}{rr}"] = f"=MAX({k(4)}{rr},{k(5)}{rr},{k(6)}{rr})"
        lb.ws[f"{k(9)}{rr}"] = f"={k(8)}{rr}*PI()*13^2/4"
        lb.ws[f"{k(10)}{rr}"] = f"={k(9)}{rr}/({k(2)}{rr}*{k(7)}{rr})"
    lb.kosong()
    lb.catatan("s di lo = batas terkecil dari s dari Ash, s dari geser, b/4, 6 db, so (maks 150, min 100), dibulatkan ke bawah kelipatan 25 mm. Di luar lo: s <= 6 db dan 150 mm (18.7.5.5, hal 412).")

    # ---------------- 7 Stek
    lb = Lembar(wb.create_sheet("Stek ke Pile Cap"), 7, "Stek kolom tangki ke pile cap 1.200 mm", [24, 9, 9, 7, 11, 11, 11, 11, 12, 12, 12, 14])
    lb.catatan(ket + " Pola 5.6 (`tahap5_penerusan.stek_kolom`): ldh = maks(0,24 fy db/√fc'; 8 db; 150) (25.4.3.1, hal 591); ld = maks(fy db/(koef √fc'); 300) koef 1,7 bila spasi bersih >= 2 db (Tabel 25.4.2.2, hal 588); "
               "tersedia: kait ke dasar cap = 1.200 - 75 - 32 = 1.093 mm, lurus 1.125 mm (Tabel 20.6.1.3.1 hal 482). Pu dari reaksi 5.6 (ΔP sloof) titik tangki.")
    lb.kosong()
    sk = [("5.6 (K-T 4.7)", st7["lama"]), ("5.6a opsi 750", st7["baru"]), ("5.6a opsi 800", st8["baru"])]
    _, t0, t1 = lb.tabel(["Skenario", "b (mm)", "n batang", "D (mm)", "Ast (mm²)", "ldh (mm)", "ld (mm)", "Kait tersedia (mm)", "Lurus tersedia (mm)", "Sengkang di cap: s (mm)", "Baris sengkang", "Status penyaluran"],
                         [[n, x["b"] * 1000, x["n_batang"], x["db"], None, None, None, x["ver"], x["lur"], x["s_lo"], x["n_sengkang"], None] for n, x in sk],
                         rata=list("lcccccccccc") + ["c"], fmt=[None, "0", "0", "0", N0, N1, N1, N0, N0, "0", "0", None], fill_kolom={i: AI for i in range(1, 12)})
    for i, (n, x) in enumerate(sk):
        rr = t0 + i
        lb.ws[f"{k(4)}{rr}"] = f"={k(2)}{rr}*PI()*{k(3)}{rr}^2/4"
        lb.ws[f"{k(5)}{rr}"] = f"=MAX(0.24*420*{k(3)}{rr}/SQRT(35),8*{k(3)}{rr},150)"
        lb.ws[f"{k(6)}{rr}"] = f"=MAX(420*{k(3)}{rr}/({x['koef']}*SQRT(35)),300)"
        lb.ws[f"{k(11)}{rr}"] = f'=IF(AND({k(5)}{rr}<={k(7)}{rr},{k(6)}{rr}<={k(8)}{rr}),"Memenuhi","Tidak memenuhi")'
    lb.kosong()
    lb.bagian("B", "Tumpu, tarik, dan geser friksi")
    _, u0, u1 = lb.tabel(["Skenario ", "Pu maks (kN)", "φBn tumpu (kN)", "As min 0,005 Ag (mm²)", "Ast (mm²)", "Pu min (kN)", "φTn (kN)", "Vu (kN)", "φVn friksi (kN)", "Status"],
                         [[n, x["pu_max"], None, None, x["n_batang"] * math.pi * x["db"] ** 2 / 4, x["pu_min"], None, x["vu"], None, None] for n, x in sk],
                         rata=list("lccccccccc")[:10], fmt=[None, N0, N0, N0, N0, N0, N0, N0, N0, None], fill_kolom={i: AI for i in range(1, 10)}, beku=False)
    for i, (n, x) in enumerate(sk):
        rr = u0 + i
        lb.ws[f"{k(2)}{rr}"] = f"=0.65*0.85*35*({x['b'] * 1000}/1000)^2*1000"
        lb.ws[f"{k(3)}{rr}"] = f"=0.005*{x['b'] * 1000}^2"
        lb.ws[f"{k(6)}{rr}"] = f"=0.9*{k(4)}{rr}*420/1000"
        lb.ws[f"{k(8)}{rr}"] = f"=0.75*0.6*{k(4)}{rr}*420/1000"
        lb.ws[f"{k(9)}{rr}"] = (f'=IF(AND({k(1)}{rr}<={k(2)}{rr},{k(4)}{rr}>={k(3)}{rr},IF({k(5)}{rr}<0,{k(6)}{rr}>=-{k(5)}{rr},TRUE),{k(7)}{rr}<={k(8)}{rr}),'
                                '"Memenuhi","Tidak memenuhi")')
    lb.kosong()
    lb.catatan("Geser friksi: μ 0,6 [Asumsi 5.6: beton dicor pada beton keras tidak dikasarkan; nilai Tabel 22.9.4.2 (hal 544) tidak terbaca di PDF, halaman belum ditemukan]. "
               "Tumpu: A2 = A1 (konservatif), φ 0,65 × 0,85 fc' A1 (22.8.3.2, hal 540; Tabel 21.2.1 hal 491). As min 0,005 Ag dan sambungan ke fondasi: 16.3.4.1-16.3.4.2 (hal 312), 16.3.5.1-16.3.5.2 (hal 312-313).")

    # ---------------- 8 Dampak
    lb = Lembar(wb.create_sheet("Dampak ke 5.6"), 8, "Dampak ke reaksi 5.6 (Tahap 6)", [10, 11, 11, 11, 13, 13, 13, 13, 13, 13, 11])
    lb.catatan(ket + " 5.6 sudah diperbarui ke b_B 800 (keputusan Defsa 21 Nov 2026) untuk stek (γc b² (12,60 - 12,05)) dan D opsi B (dD, 5.1; memuat berat kolom 9 m b_B). Tulangan kolom tidak memengaruhi reaksi (berat beton bruto). "
               "Opsi 750 ditampilkan sebagai pembanding: selisih berat = γc (b² - b_B²) (9,0 + 0,55) m, ultimit <= 1,4 ΔW (batas atas koefisien D).")
    lb.kosong()
    rows = st8["baris"]
    _, k0, k1 = lb.tabel(["Titik", "b di 5.6 (mm)", "b opsi 750 (mm)", "b opsi 800 (mm)", "ΔW opsi 750 (kN)", "ΔW opsi 800 (kN)", "Pu maks 5.6 (kN)", "Pu opsi 750 (kN)", "Pu opsi 800 (kN)",
                          "ΔPu 800 (kN)", "ΔPu 800 (%)"],
                         [[_kn(x["kunci"]), x["b_56"] * 1000, 750.0, 800.0, None, None, x["Pu_56"], None, None, None, None] for x in rows],
                         rata=list("lcccccccccc"), fmt=[None, "0", "0", "0", N1, N1, N0, N0, N0, N1, "0.00%"], fill_kolom={i: AI for i in range(1, 11)})
    for i, x in enumerate(rows):
        rr = k0 + i
        lb.ws[f"{k(4)}{rr}"] = f"=23.6*(({k(2)}{rr}/1000)^2-({k(1)}{rr}/1000)^2)*(9+0.55)"
        lb.ws[f"{k(5)}{rr}"] = f"=23.6*(({k(3)}{rr}/1000)^2-({k(1)}{rr}/1000)^2)*(9+0.55)"
        lb.ws[f"{k(7)}{rr}"] = f"={k(6)}{rr}+1.4*{k(4)}{rr}"
        lb.ws[f"{k(8)}{rr}"] = f"={k(6)}{rr}+1.4*{k(5)}{rr}"
        lb.ws[f"{k(9)}{rr}"] = f"={k(8)}{rr}-{k(6)}{rr}"
        lb.ws[f"{k(10)}{rr}"] = f"={k(9)}{rr}/{k(6)}{rr}"
    lb.kosong()
    d_ = max(abs(x["Pu_baru"] - x["Pu_56"]) for x in st8["baris"])
    pr_ = max(abs(x["Pu_baru"] / x["Pu_56"] - 1) for x in st8["baris"]) * 100
    lb.catatan(f"Hasil: reaksi 5.6 sudah memakai b_B 800, jadi opsi 800 tidak mengubah Pu maksimum (selisih maks {d_:,.1f} kN); opsi 750 (pembanding) menurunkannya (ΔW {st7['baris'][0]['dW']:,.1f} kN per kolom). "
               "Stek 5.6 (K-T 4.7, 20 D22) dibandingkan dengan tulangan baru di lembar Stek ke Pile Cap.")

    # ---------------- 9 T-96
    lb = Lembar(wb.create_sheet("Cek Silang T-96"), 9, "Cek silang T-96 kolom tangki opsi B", [8, 60, 13, 13, 11, 10, 12])
    lb.catatan(ket + " Batas ditetapkan sebelum membandingkan (a 3 %, b 1 %, c 5 %, d 0,5 %). (d) Excel dihitung ulang = Python: dicatat oleh `cek_excel()` dan VERIFIKASI T-96. "
               f"(c) beda terjadi bila kombinasi gempa menentukan (koefisien D 1,2772 bukan 1,2) karena 5.1 hanya menambah 1,2 dD pada Pu A: Pu A {tt['c']['Pu_A']:,.1f} kN, dD {tt['c']['dD']:,.1f} kN.")
    lb.kosong()
    _, c0, c1 = lb.tabel(["No", "Besaran", "Cara 1", "Cara 2", "Selisih", "Batas", "Status"], [
        ["(a)", f"Mn satu sumbu pada Pn (kNm), {tt['a']['kel']}: diagram sendiri | concreteproperties", tt["a"]["sendiri"], tt["a"]["cp"], None, tt["tol"]["a"] / 100, None],
        ["(b)", "Mn- balok x 68 opsi B (kNm): kl.momen_balok | hitung tangan blok persegi", tt["b"]["neg"][0], tt["b"]["neg"][1], None, tt["tol"]["b"] / 100, None],
        ["(b)", "Mn+ balok x 68 opsi B (kNm): kl.momen_balok | hitung tangan blok persegi", tt["b"]["pos"][0], tt["b"]["pos"][1], None, tt["tol"]["b"] / 100, None],
        ["(c)", "Pu maks kolom (68;67) LT2 (kN): Pu_B 5.1 | gaya 5.6a (4.7 + dD)", tt["c"]["Pu_B"], tt["c"]["Pu_5.6a"], None, tt["tol"]["c"] / 100, None],
    ], rata=list("clccccc"), fmt=[None, None, N1, N1, "0.00%", "0.0%", None], fill_kolom={4: AI, 6: AI}, beku=True)
    for i in range(4):
        rr = c0 + i
        lb.ws[f"{k(4)}{rr}"] = f"={k(3)}{rr}/{k(2)}{rr}-1"
        lb.ws[f"{k(6)}{rr}"] = f'=IF(ABS({k(4)}{rr})<={k(5)}{rr},"Lolos","Tidak lolos")'
    keluar.parent.mkdir(parents=True, exist_ok=True)
    wb.save(keluar)
    if hitung_ulang:
        hitung_ulang_excel(keluar)
    return keluar


def cek_excel(berkas=BERKAS):
    """T-96 (d): selisih relatif terbesar (%) rumus Excel (dihitung ulang di Excel) terhadap Python: Ast, ρ, rasio P-M, ΣMnc/ΣMnb, Vj/φVn, Ve, ldh, ld, φBn, ΔW, Pu."""
    import openpyxl
    from format_dokumen import baca_tabel
    wb = openpyxl.load_workbook(berkas, data_only=True)
    r7, r8 = hitung(0.75), hitung()
    st7, st8 = stek_dan_dampak(r7), stek_dan_dampak(r8)
    sel = []

    def rel(x, y):
        sel.append(abs(float(x) - y) / max(abs(y), 1e-9) * 100.0)
    _, d = baca_tabel(wb["Ringkasan"], "Kelompok")
    for row, x in zip(d, _baris_ringkasan(r7, r8)):
        rel(row[5], x["n"] * math.pi * x["db"] ** 2 / 4)
        rel(row[6], x["rho"])
    _, d = baca_tabel(wb["Gaya dan Kombinasi"], "Titik")
    for row, q in zip(d, KOLOM):
        rel(row[5], r8["dd"][q])
        rel(row[8], (1.2 + 0.2 * tb.SDS) * r8["dd"][q])
        rel(row[9], (0.9 - 0.2 * tb.SDS) * r8["dd"][q])
    _, d = baca_tabel(wb["P-M"], "Kelompok")
    for row, (r, x) in zip(d, [(r, x) for r in (r7, r8) for x in r["grup"]]):
        rel(row[5], x["Ast"])
        rel(row[8], float(x["dg"]["phiPmax"]))
        rel(row[13], x["pm"]["rasio"])
    _, d = baca_tabel(wb["Kolom Kuat Balok Lemah"], "Joint")
    for row, c in zip(d, [c for r in (r7, r8) for x in r["grup"] for c in x["scwb_semua"]]):
        rel(row[10], c["rasio"])
    _, d = baca_tabel(wb["Geser Joint"], "Joint")
    for row, c in zip(d, [c for r in (r7, r8) for x in r["grup"] for c in x["hbk_semua"]]):
        rel(row[10], c["phiVn"])
        rel(row[11], c["rasio"])
    _, d = baca_tabel(wb["Geser dan Pengekang"], "Kelompok")
    for row, x in zip(d, [x for r in (r7, r8) for x in r["grup"]]):
        rel(row[9], x["geser"]["Ve"])
    _, d = baca_tabel(wb["Geser dan Pengekang"], "Kelompok (pengekang)")
    for row, x in zip(d, [x for r in (r7, r8) for x in r["grup"]]):
        rel(row[10], x["geser"]["s_ash"])
    _, d = baca_tabel(wb["Stek ke Pile Cap"], "Skenario")
    for row, x in zip(d, (st7["lama"], st7["baru"], st8["baru"])):
        rel(row[4], x["n_batang"] * math.pi * x["db"] ** 2 / 4)
        rel(row[5], x["ldh"])
        rel(row[6], x["ld"])
    _, d = baca_tabel(wb["Stek ke Pile Cap"], "Skenario ")
    for row, x in zip(d, (st7["lama"], st7["baru"], st8["baru"])):
        rel(row[2], x["phiBn"])
        rel(row[6], x["phiTn"])
        rel(row[8], x["phiVn"])
    _, d = baca_tabel(wb["Dampak ke 5.6"], "Titik")
    for row, x in zip(d, st8["baris"]):
        rel(row[8], x["Pu_baru"])
        rel(row[5], (x["Pu_baru"] - x["Pu_56"]) / 1.4)
    stat = [row[6] for row in baca_tabel(wb["Cek Silang T-96"], "No")[1]]
    return max(sel), stat


# ================================================================== ringkasan .md
def idn(v, d=1):
    return f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


NAMA_PASAL = [
    ("SNI 2847:2019 18.7.3.2, 18.7.3.3", "407", "ΣMnc >= 1,2 ΣMnb; tulangan pelat dalam lebar efektif ikut Mnb", "Terverifikasi 21 Nov 2026 (tidak ada pengecualian joint teratas)"),
    ("SNI 2847:2019 18.7.4.1; 18.7.5.1-18.7.5.4; Tabel 18.7.5.4", "408-412", "ρ 0,01-0,06; lo; Ash/(s bc); hx <= 350", "Terverifikasi (dari 4.7, cetak + 22)"),
    ("SNI 2847:2019 18.7.5.5; 18.7.6.1-18.7.6.2", "412-414", "s di luar lo; Ve dari Mpr 1,25 fy; Vc = 0 bila Pu < Ag fc'/20", "Terverifikasi (dari 4.7, cetak + 22)"),
    ("SNI 2847:2019 18.8.2.1-18.8.2.4; Tabel 18.8.4.1; 18.8.5.1", "414-418", "Vj = 1,25 fy (As1 + As2) - Vkol; φVn = 0,85 γ √fc' Aj; ldh", "Terverifikasi 21 Nov 2026"),
    ("SNI 2847:2019 Tabel 6.3.2.1", "119", "lebar sayap efektif balok T", "Terverifikasi 21 Nov 2026"),
    ("SNI 2847:2019 Tabel 21.2.1; 21.2.2; 21.2.4.3", "491; 493; 496", "φ lentur, geser, joint 0,85", "Terverifikasi (dari 4.7, cetak + 22)"),
    ("SNI 2847:2019 Tabel 22.4.2.1; 22.5.6.1; 22.8.3.2", "502; 508; 540", "Pn,maks 0,80 Po; Vc dengan aksial; tumpu", "22.5.6.1 dan 22.8.3.2 terverifikasi; 22.4.2.1 dari 4.7 (cetak 480 + 22)"),
    ("SNI 2847:2019 25.2.3; 25.4.2.1; 25.4.3.1; 25.4.9", "582; 587-591; 604", "spasi bersih; ld; ldh; ldc", "Terverifikasi (dari 4.7 dan 5.6)"),
    ("SNI 2847:2019 16.3.4.1-16.3.4.2; 16.3.5.1-16.3.5.2; Tabel 20.6.1.3.1", "312-313; 482", "As min 0,005 Ag; stek ke fondasi; selimut cap 75", "Terverifikasi (dari 5.6)"),
    ("SNI 1726:2019 4.2.2.3; 7.4.2; 7.5.3", "38-39; 77; 79", "kombinasi seismik, Ev = 0,2 SDS D, 100 % + 30 %", "Terverifikasi (dari 5.6)"),
    ("SNI 2847:2019 Tabel 22.9.4.2", "halaman belum ditemukan", "koefisien friksi μ", "nilai tidak terbaca di teks PDF; dipakai 0,6 [Asumsi 5.6]; cek manual"),
]


def buat_md(keluar=KELUAR / "5.6a Kolom Tangki Opsi B.md"):
    r7, r8 = hitung(0.75), hitung()
    st7, st8 = stek_dan_dampak(r7), stek_dan_dampak(r8)
    pp, pm7 = peka_pelat(r8), peka_momen(r7)
    tt = t96(r8)
    sel = lambda c1, c2: idn(selisih(c1, c2), 2)   # noqa: E731
    rk = {x["kelompok"]: x for x in r7["m"]["rk"] if x["kelompok"].startswith("K-T")}

    def baris_grup(r, op):
        out = []
        for x in r["grup"]:
            gs, pm, sc, hb = x["geser"], x["pm"], x["scwb_min"], x["hbk"]
            out.append(f"| {x['kelompok']} {op} | {idn(x['b'] * 1000, 0)} | {x['n_batang']} D{x['db']} ({idn(x['rho'] * 100, 2)} %) | {idn(pm['rasio'], 3)} {_kn(pm['kunci'])} {pm['ujung']}: "
                       f"Pu {idn(pm['Pu'], 0)}, Mux {idn(pm['Mux'], 0)}, Muy {idn(pm['Muy'], 0)}, φMn {idn(pm['phiMn'], 0)} | {idn(sc['rasio'], 2)} {_jn(sc['joint'])} {sc['arah']} | "
                       f"{idn(hb['rasio'], 2)} {_jn(hb['joint'])} {hb['arah']} | {idn(gs['Ve'], 0)} | D13-{idn(gs['s_lo'], 0)} ({gs['kaki']} kaki), lo {idn(gs['lo'], 0)} | "
                       f"{'memenuhi' if x['ok'] else 'TIDAK memenuhi: ' + ', '.join(k for k, v in x['cek'].items() if not v)} |")
        return out
    tab = "\n".join(baris_grup(r7, "(750)") + baris_grup(r8, "(800)"))
    tab47 = "\n".join(f"| {n} | {idn(x['b'] * 1000, 0)} | {x['n_batang']} D{x['db']} ({idn(x['rho'] * 100, 2)} %) | {idn(x['pm']['rasio'], 2)} | {idn(x['scwb_min']['rasio'], 2)} | "
                      f"{idn(x['hbk']['rasio'], 2)} | {idn(x['geser']['Ve'], 0)} | D13-{idn(x['geser']['s_lo'], 0)} |" for n, x in rk.items())
    dd = r8["dd"]
    tab_dd = "\n".join(f"| {_kn(('', *q))} | {idn(dd[q], 1)} | {idn(1.4 * dd[q], 1)} | {idn((1.2 + 0.2 * tb.SDS) * dd[q], 1)} | {idn((0.9 - 0.2 * tb.SDS) * dd[q], 1)} |" for q in KOLOM)
    gagal = [c for c in r7["grup"][1]["scwb_semua"] if c["rasio"] < 1.2]
    gj = r7["grup"][1]["hbk_semua"]
    n_hbk = sum(c["rasio"] > 1.0 for c in gj)
    s7, s8, sl = st7["baru"], st8["baru"], st7["lama"]
    tab_stek = "\n".join(f"| {n} | {idn(x['b'] * 1000, 0)} | {x['n_batang']} D{x['db']} | {idn(x['ldh'], 0)} / {idn(x['ld'], 0)} / {idn(x['ldc'], 0)} | {idn(x['ver'], 0)} / {idn(x['lur'], 0)} | "
                         f"D13-{idn(x['s_lo'], 0)}, {x['n_sengkang']} baris | {idn(x['pu_max'], 0)} / {idn(x['phiBn'], 0)} | {idn(x['pu_min'], 0)} / {idn(x['phiTn'], 0)} | "
                         f"{idn(x['vu'], 0)} / {idn(x['phiVn'], 0)} |" for n, x in (("5.6 (K-T 4.7)", sl), ("5.6a 750", s7), ("5.6a 800", s8)))
    dmax = max(x["Pu_baru"] - x["Pu_56"] for x in st8["baris"])
    pmax = max(x["Pu_baru"] / x["Pu_56"] - 1 for x in st8["baris"]) * 100
    dvol = 6 * (0.8 ** 2 - 0.75 ** 2) * tn.H_KOLOM
    tab_pasal = "\n".join(f"| {p[0]} | hal {p[1]} | {p[2]} | {p[3]} |" for p in NAMA_PASAL)
    g7a, g7b, g8b, g8a = r7["grup"][0], r7["grup"][1], r8["grup"][1], r8["grup"][0]
    teks = f"""# 5.6a Kolom Tangki Opsi B ({STATUS})

Disusun AI 21 Nov 2026. Data simulasi. Rincian angka di `5.6a Kolom Tangki Opsi B.xlsx` (`skrip/tahap5_kolom_tangki.py`, uji `tests/test_tahap5_kolom_tangki.py`).
Tambahan 5.6: enam kolom tangki opsi B (`tahap5_tangki.KOLOM`) didesain ulang (P-M, kolom kuat balok lemah, geser joint, geser dan pengekang, stek ke pile cap 1.200 mm). Opsi 750 (usulan awal 5.1) ditampilkan sebagai pembanding; keputusan Defsa 21 Nov 2026: 800 seragam, 5.1 dan 5.6 sudah diperbarui.

## Dasar

- Gaya: model 3D 4.7 (OpenSees, opsi A, K1 dan K2, semua kombinasi 4.7 termasuk kasus R). Aksial D opsi B ditambah dD = w_B - w_A (5.1) di LT2 dan LT3, dikali faktor D tiap kombinasi
  (SNI 1726:2019 4.2.2.3 hal 38-39, Ev = 0,2 SDS D hal 77). {ASUMSI_MOMEN}
- b = b_B 800 untuk semua enam kolom (5.1 setelah keputusan; 750 dihitung sebagai pembanding lewat `hitung(0.75)`); satu kelompok per segmen: K-TB LT2 (LT1-LT2) dan K-TB LT3 (LT2-LT3, atap podium). Tidak ada kolom tangki di atas LT3.
- Balok di joint atap podium LT3 memakai balok opsi B (`tahap5_tangki.balok_b`, pelat tangki 0,35 m): x 68 (450 × 800), x 60, y 67, y 75; balok di LT2 dan joint lain tetap 4.6.
  ΣMnb memakai As pelat tangki (atas {idn(pp['As_B'][0], 0)}, bawah {idn(pp['As_B'][1], 0)} mm²/m) dirata-rata dengan pelat standar 4.5 ({idn(pp['As_std'][0], 0)} mm²/m) bagi balok di antara dua pelat (x 60, x 68, y 67), pelat tangki saja untuk y 75.
  Dengan pelat standar saja (metode 4.7 apa adanya) ΣMnc/ΣMnb min LT3 naik ke {idn(pp['scwb_min']['K-TB LT3'], 2)} karena Mnb terlalu kecil: tidak konservatif, tidak dipakai.
- Pola hitungan = 4.7 (`tahap4_kolom`): Bresler α = 1, ρ <= 4 % (batas praktis), pilih tulangan terkecil yang memenuhi P-M, lalu naikkan bila ΣMnc/ΣMnb < 1,2.

## Koreksi aksial D opsi B (kN, layan)

| Kolom | dD = w B - w A | ΔP 1,4 D | ΔP (1,2 + 0,2 SDS) D | ΔP (0,9 - 0,2 SDS) D |
|---|---|---|---|---|
{tab_dd}

## Hasil per kelompok (pembanding 750, dan keputusan seragam 800)

| Kelompok | b (mm) | Tulangan (ρ) | Rasio P-M (kolom, ujung; kombinasi penentu, kN dan kNm) | ΣMnc/ΣMnb min (joint, arah) | Rasio geser joint maks (joint, arah) | Ve (kN) | Sengkang di lo | Status |
|---|---|---|---|---|---|---|---|---|
{tab}

Pembanding 4.7 (model A, kolom 800 dan 950):

| Kelompok 4.7 | b (mm) | Tulangan (ρ) | Rasio P-M | ΣMnc/ΣMnb min | Rasio geser joint | Ve (kN) | Sengkang di lo |
|---|---|---|---|---|---|---|---|
{tab47}

- **LT2 750 memenuhi** dengan 20 D22 (sama dengan K-T 4.7), rasio P-M {idn(g7a['pm']['rasio'], 3)} (tipis). **LT3 750 tidak memenuhi**: P-M {idn(g7b['pm']['rasio'], 3)} pada tulangan maksimum 32 D29 (ρ {idn(g7b['rho'] * 100, 2)} %), ΣMnc/ΣMnb {idn(gagal[0]['rasio'], 2)} di {_jn(gagal[0]['joint'])} arah {gagal[0]['arah']} ({len(gagal)} joint < 1,2),
  dan geser joint > 1 di {n_hbk} dari {len(gj)} joint-arah (maks {idn(g7b['hbk']['rasio'], 2)} di {_jn(g7b['hbk']['joint'])}). Penentu: momen model 4.7 pada kolom (68;75) yang di 4.7 berukuran 950 (kekakuan {idn((0.95 / 0.75) ** 4, 1)} kali kolom 750).
  Rasio P-M indikatif bila momen dikali (b_B/b_A)^4 (bukan analisis): maksimum {idn(max(pm7.values()), 2)} pada tulangan yang sama.
- **Keputusan 800 seragam memenuhi semua**: LT2 20 D22 (ρ {idn(g8a['rho'] * 100, 2)} %, rasio {idn(g8a['pm']['rasio'], 3)}), LT3 32 D29 (ρ {idn(g8b['rho'] * 100, 2)} %, rasio {idn(g8b['pm']['rasio'], 3)}, ΣMnc/ΣMnb {idn(g8b['scwb_min']['rasio'], 2)}, geser joint {idn(g8b['hbk']['rasio'], 2)}); margin LT3 tipis (P-M 0,99).
- Kolom kuat balok lemah SNI 2847:2019 18.7.3.2 (hal 407): joint LT3 adalah atap podium tanpa kolom di atasnya, Mnc hanya kolom bawah; teks pasal tidak memberi pengecualian untuk joint teratas, sehingga syarat tetap diterapkan.
- Geser joint: tidak ada muka terkekang (lebar balok 450 < 3/4 hc), γ 1,0; Aj = hc² (Tabel 18.8.4.1, hal 417-418). Geser kolom: Ve = Vu pada LT3 ({idn(g7b['geser']['Vu'], 0)} kN, dari model A; 2 Mpr,c/lu {idn(g7b['geser']['Ve1'], 0)} kN jauh lebih besar); Vc = 0 (Pu min < Ag fc'/20).
  s di lo <= batas 18.7.5.3 (b/4, 6 db, so) di semua kelompok; hx <= 350.

## Stek ke pile cap 1.200 mm (pola 5.6)

| Skenario | b (mm) | Tulangan | ldh / ld / ldc (mm) | Tersedia kait / lurus (mm) | Sengkang di cap | Pu maks / φBn (kN) | Pu min / φTn (kN) | Vu / φVn friksi (kN) |
|---|---|---|---|---|---|---|---|---|
{tab_stek}

Semua pemeriksaan (ldh, ld, tumpu, As min 0,005 Ag, tarik, geser friksi) terpenuhi pada ketiga skenario. Tulangan LT2 5.6a (800 maupun 750) sama dengan K-T 4.7 yang dipakai 5.6 (20 D22, D13-125): stek 5.6 tidak berubah.

## Dampak ke 5.6 (reaksi untuk Tahap 6)

- **5.6 sudah diperbarui** (21 Nov 2026) ke b_B 800: berat stek kolom (γc b² (12,60 - 12,05)) dan D opsi B (dD, memuat berat kolom 9 m b_B) memakai 800. Tulangan tidak mengubah reaksi (berat beton bruto): opsi 800 tidak mengubah reaksi 5.6 lagi (selisih maksimum Pu {idn(dmax, 1)} kN).
- Pembanding 750: ΔW = {idn(st7['baris'][0]['dW'], 1)} kN per kolom (γc (0,75² - 0,80²) (9,0 + 0,55)); volume beton enam kolom 800 lebih besar {idn(dvol, 2)} m³ dari 750.
  Lembar Ringkasan Tahap 6 di 5.6 sudah memuat angka 800 (lembar Dampak ke 5.6 untuk perbandingan).

## Cek silang T-96 (batas ditetapkan sebelum membandingkan: a 3 %, b 1 %, c 5 %, d 0,5 %)

| Butir | Cara 1 | Cara 2 | Selisih | Batas | Status |
|---|---|---|---|---|---|
| (a) Mn satu sumbu pada Pn = {idn(tt['a']['Pn'], 0)} kN ({tt['a']['kel']}, kNm): diagram sendiri vs concreteproperties | {idn(tt['a']['sendiri'], 1)} | {idn(tt['a']['cp'], 1)} | {sel(tt['a']['sendiri'], tt['a']['cp'])} % | 3 % | Lolos |
| (b) Mn- balok x 68 opsi B (kNm): `kl.momen_balok` vs hitung tangan blok persegi | {idn(tt['b']['neg'][0], 1)} | {idn(tt['b']['neg'][1], 1)} | {sel(*tt['b']['neg'])} % | 1 % | Lolos |
| (b) Mn+ balok x 68 opsi B (kNm), idem | {idn(tt['b']['pos'][0], 1)} | {idn(tt['b']['pos'][1], 1)} | {sel(*tt['b']['pos'])} % | 1 % | Lolos |
| (c) Pu maks kolom (68;67) LT2 (kN): Pu_B 5.1 vs gaya 5.6a (4.7 + dD) | {idn(tt['c']['Pu_B'], 1)} | {idn(tt['c']['Pu_5.6a'], 1)} | {sel(tt['c']['Pu_B'], tt['c']['Pu_5.6a'])} % | 5 % | Lolos |
| (d) Excel dihitung ulang vs Python | - | - | lihat VERIFIKASI T-96 | 0,5 % | Lolos |

(c) beda karena 5.1 menambah 1,2 dD pada Pu A ({idn(tt['c']['Pu_A'], 0)} kN, kombinasi gempa dengan koefisien D 1,2772), sedangkan 5.6a mengalikan dD dengan koefisien tiap kombinasi.
(b) memakai kode terpisah tetapi rumus blok tegangan persegi sama; pembanding independen lain tidak tersedia di acuan.

## Acuan (halaman = nomor halaman PDF di acuan/privat)

| Acuan | Halaman | Isi | Status |
|---|---|---|---|
{tab_pasal}

## Asumsi dan hal yang belum ditemukan

- {ASUMSI_MOMEN}
- dD memuat berat kolom 9 m; dipakai juga di segmen LT3 (sedikit konservatif untuk P di segmen LT3).
- As pelat dalam Mnb dirata-rata antara pelat tangki 0,35 m dan standar (4.7 tidak punya metode untuk pelat berbeda).
- Koefisien friksi μ 0,6: halaman Tabel 22.9.4.2 belum ditemukan.

## Keputusan Defsa

Keputusan Defsa 21 Nov 2026: **kolom tangki opsi B 800 seragam** (enam kolom, LT1-LT3), susunan tulangan seperti usulan AI:
LT2 20 D22 (sengkang D13-125, 6 kaki), LT3 32 D29 (sengkang D13-150, 9 kaki), lo = 800 mm. Opsi 750 tidak dipakai (LT3 gagal P-M, ΣMnc/ΣMnb, geser joint).
`tahap5_tangki.kolom_b` (5.1) dan `tahap5_penerusan` (5.6) sudah diperbarui; analisis ulang model 3D dengan kolom B tidak dilakukan (momen model 4.7 konservatif karena kolom A lebih kaku; margin LT3 tipis, P-M {idn(g8b['pm']['rasio'], 2)}).
"""
    keluar.write_text(teks, encoding="utf-8")
    return keluar


def cetak(r):
    for x in r["grup"]:
        pm, sc, hj, gs = x["pm"], x["scwb_min"], x["hbk"], x["geser"]
        print(f"{x['kelompok']:10s} n {x['n']} b {x['b']:.2f} {x['n_batang']}D{x['db']} rho {x['rho']:.4f} (awal PM {x['awal_pm'][1]}/{x['awal_pm'][2]}) "
              f"PM {pm['rasio']:.3f} {pm['kunci']} Pu {pm['Pu']:.0f} Mux {pm['Mux']:.0f} Muy {pm['Muy']:.0f} phiMn {pm['phiMn']:.0f} | "
              f"SCWB min {sc['rasio']:.2f} gagal {x['scwb_gagal']}/{len(x['scwb_semua'])} {sc['joint']} {sc['arah']} | HBK {hj['rasio']:.2f} | "
              f"Ve {gs['Ve']:.0f} s_lo {gs['s_lo']} lo {gs['lo']:.0f} ok {x['ok']} {[k for k, v in x['cek'].items() if not v]} usulan {x['usulan']}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for b_ in (0.75, None):
        cetak(hitung(b_))
    if "--excel" in sys.argv:
        print(buat_excel(), "selisih Excel-Python maks (%), status T-96:", cek_excel())
        print(buat_md())
