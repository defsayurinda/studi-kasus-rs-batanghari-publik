"""Tahap 5 langkah 5.1: kajian letak tangki air atap podium utara (opsi A tetap 12 x 6 m vs opsi B 8 x 8 m di bay as 7-8 / F-G).

DATA SIMULASI untuk studi kasus portofolio. Disusun AI atas permintaan Defsa (20 Nov 2026); draf, menunggu persetujuan
Defsa. Kunci jawaban tidak dibuka. Beban tangki dibaca dari `04 Struktur Atas/Data Owner/Data Beban MEP Rinci.xlsx`
(Daftar Alat M-02: berat operasi 2.168 kN), harga dari `03 Desain Konsep/3.8 Perkiraan Biaya.xlsx`.

Metode sama untuk A dan B (pemakaian ulang alat 4.5-4.7, tidak ada hitungan baru kecuali yang disebut):
- Balok penumpu: `tahap4_balok.balok_menerus` (PyNite) gravitasi dengan pegas putar di kedua ujung = kekakuan kolom di bawah
  balok (4 Ec (0,70 Ig) / h, Tabel 6.6.3.1.1 seperti `tahap4_model`); beban pelat dua arah sebagai 16 beban titik segitiga
  (`tahap4_kolom.TITIK_SEGITIGA`, q L²/4). Momen gempa diambil dari amplop analisis 3D 4.6 (`tahap4_balok.analisis`, K1 dan
  K2, 100 % + 30 %, rho 1,3) pada balok yang sama di posisi yang sama; 4.6 tidak memisahkan gravitasi dan gempa, jadi
  amplop gempa dihitung ulang dari hasil analisis yang sama. Kombinasi dan desain penampang = `selubung` dan
  `desain_penampang` 4.6. Balok anak = `_desain_anak` 4.6.
- Pelat dua arah opsi B: `tahap4_pelat.desain_panel` (metode desain langsung, SNI 2847 Pasal 8.10) dengan kekakuan balok
  tepi yang sebenarnya.
- Kolom opsi B: kriteria aksial 4.7 (Pu <= phi Pn,max = 0,65 x 0,80 Po, rho <= 0,04), ukuran dari daftar 4.7.
- Reaksi per kolom: analisis gravitasi 4.7 (`tahap4_kolom.analisis`), D dan L layan.
- Besi balok dari As desain (`desain_penampang`); pelat 100 kg/m3 dan kolom 200 kg/m3 [3.6, tahap3_struktur.BESI].
Pasal yang dikutip hanya yang sudah dipakai skrip 4.5-4.7; selain itu ditulis "belum ada di acuan".
"""
from __future__ import annotations

import functools
import math
import sys
from pathlib import Path

import numpy as np
import openpyxl

sys.path.insert(0, str(Path(__file__).parent))
import cache_analisis  # noqa: E402
import tahap4_balok as tbk  # noqa: E402
import tahap4_beban as tb  # noqa: E402
import tahap4_kolom as kl  # noqa: E402
import tahap4_model as tm  # noqa: E402
import tahap4_pelat as tp  # noqa: E402

AKAR = Path(__file__).resolve().parents[1]
MEP = AKAR / "04 Struktur Atas" / "Data Owner" / "Data Beban MEP Rinci.xlsx"
BIAYA = AKAR / "03 Desain Konsep" / "3.8 Perkiraan Biaya.xlsx"
KELUAR = AKAR / "05 Struktur Tengah"
BERKAS = KELUAR / "5.1 Kajian Letak Tangki.xlsx"
LABEL = "DATA SIMULASI untuk studi kasus portofolio. Bukan data proyek nyata. Tidak untuk konstruksi."
STATUS = "disetujui Defsa 21 Nov 2026: opsi B"
LABEL_AI = f"DIISI AI ATAS PERMINTAAN DEFSA (20 Nov 2026), sel hijau; {STATUS}. Kunci jawaban tidak dibuka."

GAMMA_C = tb.GAMMA_C                 # 23,6 kN/m3
P_TANGKI = 2168.0                    # kN berat operasi M-02 [Data Beban MEP Rinci, Daftar Alat]; dibaca ulang di baca_tangki()
Q_IZIN_TIANG = 911.0                 # kN per tiang bor Ø800 [3.7, LA.1 zona selatan]
VOL_CAP_PER_TIANG = 4.5              # m3 pile cap per tiang [3.8 Kebutuhan Nyata, Asumsi]
KOLOM = [(x, y) for y in (67.0, 75.0) for x in (60.0, 68.0, 76.0)]   # enam kolom di sekitar tangki
H_KOLOM = 9.0                        # m, kolom transfer menerus LT1-LT3 (2 x 4,5 m)
H_KOL_PEGAS = tm.TINGGI["LT3"]       # 4,5 m: tinggi kolom di bawah balok atap podium untuk kekakuan pegas
T_B_PILIHAN = (0.25, 0.30, 0.35)     # tebal pelat opsi B yang dicoba (m)
UKURAN_KOLOM_47 = (0.65, 0.75, 0.80, 0.95)   # ukuran kolom yang dipakai 4.7 (K-M, K-P, K-T, K-T68)
BESI_KG = {"kolom": 200.0, "pelat": 100.0}   # kg/m3 [Asumsi 3.6, tahap3_struktur.BESI]
RHO_BAJA = 7850.0
EV = 0.2 * tb.SDS

TANGKI_A = {"x": (60.0, 72.0), "y": (67.0, 73.0), "tinggi": 3.0}
TANGKI_B = {"x": (60.0, 68.0), "y": (67.0, 75.0), "tinggi": 3.5}
CHILLER = {"x": (66.0, 77.0), "y": (52.9, 65.7)}
LB2 = {"x": (58.0, 58.8), "y": (69.0, 69.8)}
GRID_X = {"7": 60.0, "8": 68.0, "9": 76.0}
GRID_Y = {"F": 67.0, "G": 75.0}


def idn(v, d=1):
    """Angka berkoma desimal, titik ribuan (untuk teks di sel)."""
    return f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ------------------------------------------------------------------ data masukan
def baca_tangki(berkas=MEP):
    """Berat operasi, berat kosong dan koordinat tangki M-02, chiller M-01 dan LB-2 dari Daftar Alat dan Shaft."""
    import tahap5_telaah as ts
    it = {i["kode"]: i for i in ts.baca_item(berkas)}
    m2 = it["M-02"]["raw"]
    return {"berat_operasi": float(m2["Berat operasi per unit (kN)"]), "berat_kosong": float(m2["Berat kosong per unit (kN)"]),
            "x": it["M-02"]["x"], "y": it["M-02"]["y"], "chiller_x": it["M-01"]["x"], "chiller_y": it["M-01"]["y"],
            "lb2_x": it["LB-2"]["x"], "lb2_y": it["LB-2"]["y"]}


@functools.lru_cache(maxsize=1)
def baca_harga(berkas=BIAYA):
    """Harga satuan dan parameter dari 3.8: lembar Parameter dan Kebutuhan Nyata."""
    wb = openpyxl.load_workbook(berkas, data_only=True)
    par = {}
    for r in wb["Parameter"].iter_rows(min_row=7, values_only=True):
        if r[3]:
            par[str(r[3])] = float(r[4]) if isinstance(r[4], (int, float)) else r[4]
    kn = {}
    for r in wb["Kebutuhan Nyata"].iter_rows(min_row=7, values_only=True):
        if r[3] and isinstance(r[4], (int, float)):
            kn[str(r[3])] = {"volume": float(r[4]), "besi_t": float(r[6] or 0.0), "biaya": float(r[7])}
    tiang = next(v for k, v in kn.items() if k.startswith("Tiang opsi A"))
    cap = kn["Pile cap"]
    return {"beton": par["Beton per m³"], "bekisting": par["Bekisting per m³ beton"],
            "besi": par["Baja tulangan terpasang"], "btl": par["Biaya tidak langsung"], "ppn": par["PPN"],
            "n_tiang_3_8": tiang["volume"], "biaya_tiang_total": tiang["biaya"],
            "biaya_tiang": tiang["biaya"] / tiang["volume"], "vol_cap_total": cap["volume"],
            "biaya_cap_total": cap["biaya"], "biaya_cap_m3": cap["biaya"] / cap["volume"],
            "besi_cap_t_m3": cap["besi_t"] / cap["volume"]}


# ------------------------------------------------------------------ amplop gempa dan reaksi 4.6 / 4.7
def _kunci_bal(x1, y1, x2, y2):
    return ("LT3", float(x1), float(y1), float(x2), float(y2))


@functools.lru_cache(maxsize=1)
@cache_analisis.disk
def hasil_46_47():
    """Satu kali jalan: rancangan 4.6, amplop gempa balok tangki (K1 + K2), reaksi layan dan Pu kolom 4.7."""
    r46 = tbk.rancang()
    um = r46["ukuran_model"]
    # --- amplop gempa per balok (ukuran balok dan kolom persis seperti 4.6)
    tm.UKURAN_BALOK = dict(um)
    amplop = {}
    try:
        for kf in ("K2", "K1"):
            h = tbk.analisis(kf)
            for k, (lfd, b) in h["D"].items():
                if k[0] != "LT3" or not (60 <= min(k[1], k[3]) and max(k[1], k[3]) <= 76 and 67 <= min(k[2], k[4])
                                          and max(k[2], k[4]) <= 75):
                    continue
                xs = tbk.titik_x(tbk.kolom_lebar(b))
                e_all = []
                for nama in ("E", "R"):
                    for a, o in (("X", "Y"), ("Y", "X")):
                        for s1 in "+-":
                            ea = tbk.momen(h[f"{nama}{a}{s1}"][k], xs)
                            for s2 in "+-":
                                eo = tbk.momen(h[f"{nama}{o}{s2}"][k], xs)
                                for sg in (1, -1):
                                    for so in (1, -1):
                                        e_all.append(tb.RHO * (sg * ea + 0.3 * so * eo))
                prof = np.abs(np.array(e_all)).max(axis=0)
                o = amplop.setdefault(k, {"x": [float(v) for v in xs], "e": np.zeros(len(xs))})
                o["e"] = np.maximum(o["e"], prof)
        for o in amplop.values():
            o["face"], o["mid"] = float(max(o["e"][0], o["e"][-1])), float(o["e"][len(o["e"]) // 2])
    finally:
        tm.UKURAN_BALOK = {}
    # --- reaksi layan dan Pu kolom 4.7
    hs = [kl.analisis("K2", um), kl.analisis("K1", um)]
    r47 = kl.rancang_dari(hs, r46)
    gk = kl.gaya_kolom(hs)
    kol = {}
    for (x, y) in KOLOM:
        k = ("LT2", x, y)
        rd = max(kl.ujung(h["gaya"]["D"][k])[0][0] for h in hs)
        rl = max(kl.ujung(h["gaya"]["L"][k])[0][0] for h in hs)
        kol[(x, y)] = {"R_D": float(rd), "R_L": float(rl), "R": float(rd + rl),
                       "Pu": float(gk[k]["F"][:, :, 0].max()), "b": float(gk[k]["b"]),
                       "kelompok": gk[k]["kelompok"]}
    return {"r46": r46, "amplop": amplop, "kolom": kol, "r47": r47, "um": um,
            "anak": tbk.balok_anak_tangki(),
            "W_K2": tb.elf("K2")["W"]}


# ------------------------------------------------------------------ balok: gravitasi + gempa 4.6
def k_pegas(b_kolom):
    """Kekakuan putar ujung balok (kNm/rad): 4 Ec 0,70 Ig / h kolom di bawah balok (Tabel 6.6.3.1.1 seperti tahap4_model)."""
    return 4 * tm.EC_35 * tm.RETAK["kolom"] * b_kolom ** 4 / 12 / H_KOL_PEGAS


def titik_segitiga(q_d, q_l):
    """Beban titik (x, P kN) pelat dua arah satu sisi balok 8 m: q L²/4 total [4.7]."""
    pd = [(float(x), float(q_d * w)) for x, w in zip(kl.TITIK_SEGITIGA, kl.BOBOT_SEGITIGA)]
    pl = [(float(x), float(q_l * w)) for x, w in zip(kl.TITIK_SEGITIGA, kl.BOBOT_SEGITIGA)]
    return pd, pl


def q_parapet():
    """Dinding luar/parapet pada balok tepi atap (kN/m): seperti `tahap4_balok.beban_balok` (sisi = 1)."""
    q = (1 - tb.BUKAAN) * tb.DINDING_LUAR["bata"][0] + tb.BUKAAN * tb.DINDING_LUAR["kaca"][0] + tb.DINDING_LUAR["fasad"][0]
    return q * tb.PARAPET


def desain_induk(beban, b_kolom, amp, ukuran=None, tu_fn=None, bentang=8.0, hc=None):
    """Ukuran balok terkecil yang memenuhi 4.6 (`desain_penampang`, SPGS) untuk satu bentang 8 m dengan pegas putar ujung.
    beban(b, h) -> (wD, wL, [(x, P) D], [(x, P) L]) kN/m dan kN. Mu dari selubung seperti `tahap4_balok.selubung`;
    gempa E(x) = amplop |E| 4.6 pada balok yang sama (amp), dipakai di dua arah (konservatif)."""
    ukuran = ukuran or tbk.UKURAN
    ep = lambda t: float(np.interp(t, amp["x"], amp["e"]))   # noqa: E731
    k = k_pegas(b_kolom)
    hc = hc or b_kolom
    for b, h in ukuran:
        w_d, w_l, p_d, p_l = beban(b, h)
        r = tbk.balok_menerus([bentang], [("D", w_d, 0.0, bentang), ("L", w_l, 0.0, bentang)],
                              [("D", p, x) for x, p in p_d] + [("L", p, x) for x, p in p_l], b, h, k_rot=k)
        x = r["x"]
        xf = [hc / 2, bentang - hc / 2]
        md, ml = r["M"]["D"], r["M"]["L"]
        vd, vl = np.abs(r["V"]["D"]), np.abs(r["V"]["L"])
        g = lambda arr, t: float(np.interp(t, x, arr))   # noqa: E731
        neg, pos_u = [], []
        for t in xf:
            mdt, mlt = g(md, t), g(ml, t)
            e_f = ep(t)
            neg += [1.4 * mdt, 1.2 * mdt + 1.6 * mlt, (1.2 + EV) * mdt + mlt - e_f, (0.9 - EV) * mdt - e_f]
            pos_u += [(1.2 + EV) * mdt + mlt + e_f, (0.9 - EV) * mdt + e_f]
        dalam = (x > xf[0] + 1e-6) & (x < xf[1] - 1e-6)
        e_x = np.array([ep(t) for t in x[dalam]])
        pos_l = max(np.max(np.maximum(1.4 * md[dalam], np.maximum(1.2 * md[dalam] + 1.6 * ml[dalam],
                                                                     (1.2 + EV) * md[dalam] + ml[dalam] + e_x))), 0.0)
        vgs = [(1.2 + EV) * g(vd, t) + g(vl, t) for t in xf]
        vug = [max(1.4 * g(vd, t), 1.2 * g(vd, t) + 1.6 * g(vl, t)) for t in xf]
        tu = tu_fn(hc) if tu_fn else 0.0
        des = tbk.desain_penampang(b, h, float(-min(min(neg), 0.0)), float(max(max(pos_u), 0.0)), float(pos_l),
                                   max(vgs), max(vug), tu=tu, hc=hc)
        if des["ok"] or (b, h) == ukuran[-1]:
            return {**des, "R_D": r["R"]["D"], "R_L": r["R"]["L"], "k_rot": k, "E_face": ep(xf[0]), "w_D": w_d, "w_L": w_l,
                    "M_muka_D": g(md, xf[0]), "M_tengah_D": g(md, bentang / 2), "wD_pts": p_d}


def besi_balok(des, panjang):
    """Berat besi balok (kg) dari As desain: tulangan atas dan bawah sepanjang bentang + 5 % lewatan/kait [Asumsi],
    sengkang rapat 2h di dua ujung dan jarang di tengah, tulangan samping D13 bila ada."""
    b, h, ds = des["b"], des["h"], des["ds"] / 1000
    a_lentur = (des["atas"]["As"] + des["bawah"]["As"]) * 1e-6
    lentur = a_lentur * panjang * 1.05 * RHO_BAJA
    sel = tbk.SEL
    keliling = 2 * (b - 2 * sel) + 2 * (h - 2 * sel) + 0.30 + max(des["kaki"] - 2, 0) / 2 * (b - 2 * sel + 0.30)
    l_sendi = min(des["l_sendi"], panjang / 2)
    n_set = 2 * l_sendi / des["s_sendi"] + (panjang - 2 * l_sendi) / des["s_lap"]
    seng = n_set * keliling * tbk.luas(ds * 1000) * 1e-6 * RHO_BAJA
    kulit = des["samping"] * 2 * panjang * tbk.luas(13) * 1e-6 * RHO_BAJA
    return lentur + seng + kulit


# ------------------------------------------------------------------ opsi A: balok metode 5.1 untuk dibandingkan dengan 4.6
def balok_a():
    """Balok penumpu tangki opsi A hasil metode 5.1 (kolom 4.7: 0,95 di x 68, 0,80 di x 60/76)."""
    d = hasil_46_47()
    an = d["anak"]
    pd_, pl_ = titik_segitiga(*tbk.beban_panel("LT3", 70.0, 71.0))
    out = {}
    q_tk = tb.atap_khusus()["tangki_kpa"]
    for nama, xb, kolom_b, i_anak in (("x 68", 68.0, 0.95, 1), ("x 60", 60.0, 0.80, 0), ("x 76", 76.0, 0.80, 2)):
        e = d["amplop"][_kunci_bal(xb, 67, xb, 75)]

        def beban(b, h, i_anak=i_anak):
            w_d = GAMMA_C * b * (h - tp.H)
            p_d = [(x, 2 * p) for x, p in pd_]          # dua sisi pelat
            p_l = [(x, 2 * p) for x, p in titik_segitiga(*tbk.beban_panel("LT3", 70.0, 71.0))[1]]
            return w_d, 0.0, p_d + [(4.0, float(an["R_D"][i_anak]))], p_l + [(4.0, float(an["R_L"][i_anak]))]
        out[nama] = desain_induk(beban, kolom_b, e, hc=tb.KOLOM_POD)
    for nama, (xa, xb_), kolom_b in (("y 67 (x 60-68)", (60.0, 68.0), 0.80), ("y 67 (x 68-76)", (68.0, 76.0), 0.80)):
        e = d["amplop"][_kunci_bal(xa, 67, xb_, 67)]
        n_d, n_l = tbk.beban_panel("LT3", (xa + xb_) / 2, 69.0)
        s_d, s_l = tbk.beban_panel("LT3", (xa + xb_) / 2, 65.0)
        pn = titik_segitiga(n_d, n_l)
        ps = titik_segitiga(s_d, s_l)

        def beban(b, h, pn=pn, ps=ps):
            w_d = GAMMA_C * b * (h - tp.H) + q_tk * 2.0     # lajur 2 m pelat tangki, penuh seperti 4.6
            return w_d, 0.0, [(x, p + q) for (x, p), (_, q) in zip(pn[0], ps[0])],                 [(x, p + q) for (x, p), (_, q) in zip(pn[1], ps[1])]
        out[nama] = desain_induk(beban, kolom_b, e, hc=tb.KOLOM_POD)
    return out


# ------------------------------------------------------------------ statika tangan dan reaksi tangki
def r_tengah_dua_bentang(segmen, L=8.0, n=4001):
    """Reaksi tumpuan tengah balok dua bentang sama L (statika tangan, garis pengaruh): R_B(P) = P a (3L² - a²) / (2L³),
    a = jarak ke tumpuan luar terdekat. segmen: [(w kN/m, x0, x1)]."""
    r = 0.0
    for w, x0, x1 in segmen:
        s = np.linspace(x0, x1, n)
        a = np.where(s <= L, s, 2 * L - s)
        f = a * (3 * L ** 2 - a ** 2) / (2 * L ** 3)
        r += w * float(np.trapezoid(f, s) if hasattr(np, "trapezoid") else np.trapz(f, s))
    return r


def reaksi_tangki_a():
    """Bagian beban tangki (kN) ke enam kolom, opsi A: pelat satu arah, lajur 2 m ke balok y 67 dan 4 m ke balok anak y 71,
    balok anak ke balok induk di y 71, balok induk ke kolom setengah-setengah (beban di tengah bentang)."""
    q = tb.atap_khusus()["tangki_kpa"]
    r_y67 = tbk.balok_menerus([8.0, 8.0], [("T", q * 2.0, 0.0, 12.0)], [], 0.4, 0.7)["R"]["T"]
    r_anak = tbk.balok_menerus([8.0, 8.0], [("T", q * 4.0, 0.0, 12.0)], [], 0.5, 0.9)["R"]["T"]
    out = {k: 0.0 for k in KOLOM}
    for i, x in enumerate((60.0, 68.0, 76.0)):
        out[(x, 67.0)] += r_y67[i] + r_anak[i] / 2
        out[(x, 75.0)] += r_anak[i] / 2
    tangan = {"anak_tangki_x68": r_tengah_dua_bentang([(q * 4.0, 0.0, 12.0)])}
    return out, {"R_y67": list(map(float, r_y67)), "R_anak": list(map(float, r_anak)), "q": q, "tangan": tangan}


def reaksi_tangki_b(p=P_TANGKI):
    """Opsi B: pelat 8 x 8 beban amplop 45 derajat, tiap balok W/4 (segitiga), ujung W/8 ke tiap kolom sudut."""
    q = p / 64.0
    pd, _ = titik_segitiga(q, 0.0)
    r = tbk.balok_menerus([8.0], [], [("T", pp, x) for x, pp in pd], 0.5, 0.9)["R"]["T"]
    out = {k: 0.0 for k in KOLOM}
    for (x, y) in ((60.0, 67.0), (68.0, 67.0), (60.0, 75.0), (68.0, 75.0)):
        out[(x, y)] = 2 * r[0]          # dua balok bertemu di tiap kolom sudut
    return out, {"q": q, "R_ujung": float(r[0]), "W_balok": float(sum(pp for _, pp in pd))}


# ------------------------------------------------------------------ pelat opsi B
class _balok_pelat:
    """Konteks: ganti kekakuan balok bawaan (350 x 600) di `tahap4_pelat.alpha_f`/`c_torsi` dengan balok tepi sebenarnya."""

    def __init__(self, bw, hb):
        self.bw, self.hb = bw, hb

    def __enter__(self):
        self.a, self.c = tp.alpha_f.__defaults__, tp.c_torsi.__defaults__
        tp.alpha_f.__defaults__ = (self.bw, self.hb) + self.a[2:]
        tp.c_torsi.__defaults__ = (self.bw, self.hb) + self.c[2:]

    def __exit__(self, *a):
        tp.alpha_f.__defaults__, tp.c_torsi.__defaults__ = self.a, self.c


def pelat_b(h, bw, hb, kolom_b=0.75):
    """Panel 8 x 8 opsi B (DDM 4.5) tebal h dengan beban tangki 33,9 kPa sebagai beban mati; kembalikan hasil dan 'ok'."""
    with _balok_pelat(bw, hb):
        r = tp.desain_panel("B", "Pelat tangki opsi B 8 x 8", h, tp.SIDL_ATAP + P_TANGKI / 64.0, 0.96, kolom_b)
    lentur = all(x["phiMn"] >= x["Mu"] for x in r["baris"])
    geser = r["Vu"] <= r["phiVc"]
    jelek = max(r["baris"], key=lambda x: x["Mu"] / x["phiMn"])
    return {**r, "lentur_ok": lentur, "geser_ok": geser, "ok": lentur and geser,
            "rasio_lentur": jelek["Mu"] / jelek["phiMn"], "rasio_geser": r["Vu"] / r["phiVc"]}


# ------------------------------------------------------------------ balok dan kolom opsi B
def balok_b(t_b, anak_y71=False):
    """Balok sekeliling tangki dan balok bay timur yang kembali standar, metode 5.1 (gempa = amplop 4.6 di posisi sama)."""
    d = hasil_46_47()
    q_td = GAMMA_C * t_b + tp.SIDL_ATAP + P_TANGKI / 64.0
    t_pd, t_pl = titik_segitiga(q_td, 0.96)
    sat = tbk.beban_panel("LT3", 70.0, 71.0)        # pelat standar atap podium (D, L)
    s_pd, s_pl = titik_segitiga(*sat)
    hasil = {}
    # --- x 60 dan x 68: tangki di timur, pelat standar di barat (x 60) dan timur (x 68)
    for nama, xb in (("x 60", 60.0), ("x 68", 68.0)):
        e = d["amplop"][_kunci_bal(xb, 67, xb, 75)]

        def beban(b, h):
            p_d = [(x, p + q) for (x, p), (_, q) in zip(t_pd, s_pd)]
            p_l = [(x, p + q) for (x, p), (_, q) in zip(t_pl, s_pl)]
            return GAMMA_C * b * (h - t_b), 0.0, p_d, p_l
        hasil[nama] = desain_induk(beban, 0.75, e)
    # --- y 67 (x 60-68): utara pelat tangki, selatan atap standar dengan chiller
    e = d["amplop"][_kunci_bal(60, 67, 68, 67)]
    ss_d, ss_l = tbk.beban_panel("LT3", 64.0, 65.0)
    sp_d, sp_l = titik_segitiga(ss_d, ss_l)

    def beban_y67(b, h):
        p_d = [(x, p + q) for (x, p), (_, q) in zip(t_pd, sp_d)]
        p_l = [(x, p + q) for (x, p), (_, q) in zip(t_pl, sp_l)]
        return GAMMA_C * b * (h - t_b), 0.0, p_d, p_l
    hasil["y 67 (x 60-68)"] = desain_induk(beban_y67, 0.75, e)
    # --- y 75 (x 60-68): tepi gedung, hanya pelat tangki di selatan, ditambah parapet dan dinding luar (sisi = 1)
    e = d["amplop"][_kunci_bal(60, 75, 68, 75)]
    tu_fn = lambda hc: tbk.torsi_tepi((q_td, 0.96), hc)   # noqa: E731

    def beban_y75(b, h):
        return GAMMA_C * b * (h - t_b) + q_parapet(), 0.0, t_pd, t_pl
    hasil["y 75 (x 60-68)"] = desain_induk(beban_y75, 0.75, e, tu_fn=tu_fn)
    # --- bay timur kembali standar: x 76, y 67 (x 68-76)
    e = d["amplop"][_kunci_bal(76, 67, 76, 75)]

    def beban_x76(b, h):
        p_d = [(x, 2 * p) for x, p in s_pd]
        p_l = [(x, 2 * p) for x, p in s_pl]
        return GAMMA_C * b * (h - tp.H), 0.0, p_d, p_l
    hasil["x 76 (standar)"] = desain_induk(beban_x76, 0.75, e)
    e = d["amplop"][_kunci_bal(68, 67, 76, 67)]
    n_d, n_l = titik_segitiga(*sat)

    def beban_y67e(b, h):
        p_d = [(x, p + q) for (x, p), (_, q) in zip(n_d, sp_d)]
        p_l = [(x, p + q) for (x, p), (_, q) in zip(n_l, sp_l)]
        return GAMMA_C * b * (h - tp.H), 0.0, p_d, p_l
    hasil["y 67 (x 68-76, standar)"] = desain_induk(beban_y67e, 0.75, e)
    return hasil


# ------------------------------------------------------------------ pelat: rasio besi, kolom, unsur dan berat
def laju_besi_pelat(r):
    """Besi pelat DDM (kg/m2 pelat, dua arah) dari As desain: bawah sepanjang bentang, atas 0,6 L (0,3 L tiap ujung) [Asumsi]."""
    def as_rata(posisi):
        xs = [x for x in r["baris"] if x["bentang"] == "interior" and x["posisi"] == posisi]
        return sum(x["As_ada"] for x in xs) / len(xs)
    return 2 * RHO_BAJA * (as_rata("pos") + 0.6 * as_rata("neg_int")) * 1e-6


def kolom_b(pu_a, d_d):
    """Ukuran kolom opsi B: terkecil dari daftar 4.7 yang memenuhi Pu <= phi Pn,max (0,65 x 0,80 Po, rho <= 0,04),
    tidak lebih kecil dari 0,80 (keputusan Defsa 21 Nov 2026, 5.6a: 800 seragam; sebelumnya batas 0,75 K-P). Pu B = Pu A (4.7) + 1,2 x selisih D layan (d_d = R_D B - R_D A)."""
    d = hasil_46_47()["kolom"]
    out = {}
    for k in KOLOM:
        pu = pu_a[k] + 1.2 * d_d[k]
        pilih = None
        for b in UKURAN_KOLOM_47:
            if b < 0.80 - 1e-9:      # Keputusan Defsa 21 Nov 2026 (5.6a): kolom tangki 800 seragam
                continue
            dg = kl.diagram(b, *kl.pilihan_tulangan(b)[-1][1:])
            if pu <= dg["phiPmax"]:
                pilih = (b, float(dg["phiPmax"]))
                break
        dg_a = kl.diagram(d[k]["b"], *kl.pilihan_tulangan(d[k]["b"])[-1][1:])
        out[k] = {"Pu_B": float(pu), "b_B": pilih[0], "phiPmax_B": pilih[1], "b_A": d[k]["b"], "Pu_A": pu_a[k],
                  "phiPmax_A": float(dg_a["phiPmax"])}
    return out


def n_tiang(r):
    """Tiang per pile cap = ceil(R / 911), paling sedikit 2 (kebiasaan 3.7: `max(2, ceil(P / izin))`)."""
    return max(2, math.ceil(r / Q_IZIN_TIANG - 1e-9))


def _berat_balok(unsur):
    """Berat beton balok (kN) ke kolom: setengah ke tiap ujung; balok anak 16 m: reaksi dua bentang 0,1875 / 0,625 / 0,1875
    ke balok induk, lalu setengah ke y 67 dan y 75."""
    w = {k: 0.0 for k in KOLOM}
    for u in unsur:
        wt = GAMMA_C * u["vol"]
        if u["ujung"] is None:
            for x, f in ((60.0, 0.1875), (68.0, 0.625), (76.0, 0.1875)):
                for y in (67.0, 75.0):
                    w[(x, y)] += wt * f / 2
        else:
            for k in u["ujung"]:
                w[k] += wt / 2
    return w


def _berat_pelat(per_bay):
    """per_bay: {'barat': [(luas, tebal)], 'timur': [...]}; berat tiap bay dibagi rata ke empat kolom sudutnya."""
    w = {k: 0.0 for k in KOLOM}
    for bay, xs in (("barat", (60.0, 68.0)), ("timur", (68.0, 76.0))):
        tot = sum(a * t for a, t in per_bay[bay]) * GAMMA_C
        for x in xs:
            for y in (67.0, 75.0):
                w[(x, y)] += tot / 4
    return w


def _unsur(daftar):
    out = []
    for nama, des, panjang, web, ujung in daftar:
        out.append({"nama": nama, "b": des["b"], "h": des["h"], "L": panjang, "web": web,
                    "vol": des["b"] * (des["h"] - web) * panjang, "besi_kg": besi_balok(des, panjang), "ujung": ujung,
                    "des": des})
    return out


@functools.lru_cache(maxsize=1)
def hitung():
    """Seluruh hitungan 5.1: unsur A dan B, reaksi, tiang, volume, besi, biaya, ruang, cek silang T-90."""
    d = hasil_46_47()
    kel = {x["kelompok"]: x for x in d["r46"]["kelompok"]}
    an = d["anak"]
    harga = baca_harga()
    tk = baca_tangki()
    metode_a = balok_a()
    t_a, info_tk = reaksi_tangki_a()
    g_x68, g_x60, g_y67, g_std = (kel["B-T induk tangki x 68"], kel["B-T induk tangki x 60/76"],
                                  kel["B-T induk tangki y 67"], kel["B-P tepi LT3"])
    # ---------------- opsi A: ukuran 4.5-4.7 (disetujui Defsa); metode 5.1 hanya cek silang
    ua = _unsur([
        ("x 60", g_x60, 8.0, tp.H, ((60.0, 67.0), (60.0, 75.0))),
        ("x 68", g_x68, 8.0, tp.H, ((68.0, 67.0), (68.0, 75.0))),
        ("x 76", g_x60, 8.0, tp.H, ((76.0, 67.0), (76.0, 75.0))),
        ("y 67 (x 60-68)", g_y67, 8.0, tp.H, ((60.0, 67.0), (68.0, 67.0))),
        ("y 67 (x 68-76)", g_y67, 8.0, tp.H, ((68.0, 67.0), (76.0, 67.0))),
        ("y 75 (x 60-68)", g_std, 8.0, tp.H, ((60.0, 75.0), (68.0, 75.0))),
        ("y 75 (x 68-76)", g_std, 8.0, tp.H, ((68.0, 75.0), (76.0, 75.0))),
        ("anak y 71 (x 60-76)", an, 16.0, tp.H_TANGKI, None),
    ])
    # ---------------- opsi B: tebal pelat terkecil yang cukup, balok metode 5.1
    pel = {h: pelat_b(h, 0.40, 0.70) for h in T_B_PILIHAN}
    t_b = next((h for h in T_B_PILIHAN if pel[h]["ok"]), None)
    if t_b is None:
        raise RuntimeError("pelat 350 mm belum cukup: tambah balok anak y 71 satu bentang (belum ada di skrip)")
    bb = balok_b(t_b)
    ub = _unsur([
        ("x 60", bb["x 60"], 8.0, t_b, ((60.0, 67.0), (60.0, 75.0))),
        ("x 68", bb["x 68"], 8.0, t_b, ((68.0, 67.0), (68.0, 75.0))),
        ("x 76", bb["x 76 (standar)"], 8.0, tp.H, ((76.0, 67.0), (76.0, 75.0))),
        ("y 67 (x 60-68)", bb["y 67 (x 60-68)"], 8.0, t_b, ((60.0, 67.0), (68.0, 67.0))),
        ("y 67 (x 68-76)", bb["y 67 (x 68-76, standar)"], 8.0, tp.H, ((68.0, 67.0), (76.0, 67.0))),
        ("y 75 (x 60-68)", bb["y 75 (x 60-68)"], 8.0, t_b, ((60.0, 75.0), (68.0, 75.0))),
        ("y 75 (x 68-76)", g_std, 8.0, tp.H, ((68.0, 75.0), (76.0, 75.0))),
    ])
    # ---------------- berat dan reaksi per kolom
    k_a = {k: d["kolom"][k]["b"] for k in KOLOM}
    r_a = {k: d["kolom"][k]["R"] for k in KOLOM}
    r_ad = {k: d["kolom"][k]["R_D"] for k in KOLOM}
    pelat_a = {"barat": [(48.0, 0.25), (16.0, 0.20)], "timur": [(24.0, 0.25), (40.0, 0.20)]}
    pelat_bb = {"barat": [(64.0, t_b)], "timur": [(64.0, 0.20)]}
    t_bk, info_b = reaksi_tangki_b()
    wb_a, wb_b = _berat_balok(ua), _berat_balok(ub)
    wp_a, wp_b = _berat_pelat(pelat_a), _berat_pelat(pelat_bb)
    w_a = {k: t_a[k] + wb_a[k] + wp_a[k] + GAMMA_C * k_a[k] ** 2 * H_KOLOM for k in KOLOM}
    # kolom B: dua langkah (ukuran kolom mempengaruhi berat sendiri, tetapi kolom 0,80 (batas bawah) dipakai untuk tebakan awal)
    w_b0 = {k: t_bk[k] + wb_b[k] + wp_b[k] + GAMMA_C * 0.80 ** 2 * H_KOLOM for k in KOLOM}
    kb = kolom_b({k: d["kolom"][k]["Pu"] for k in KOLOM}, {k: w_b0[k] - w_a[k] for k in KOLOM})
    b_kol_b = {k: kb[k]["b_B"] for k in KOLOM}
    w_b = {k: t_bk[k] + wb_b[k] + wp_b[k] + GAMMA_C * b_kol_b[k] ** 2 * H_KOLOM for k in KOLOM}
    r_b = {k: r_a[k] - w_a[k] + w_b[k] for k in KOLOM}
    n_a = {k: n_tiang(r_a[k]) for k in KOLOM}
    n_b = {k: n_tiang(r_b[k]) for k in KOLOM}
    # ---------------- volume dan besi
    r_std = tp.desain_panel("P6", "pelat atap standar", tp.H, tp.SIDL_ATAP, 0.96, 0.75)
    kg_m3_b = BESI_KG["pelat"] * (laju_besi_pelat(pel[t_b]) / t_b) / (laju_besi_pelat(r_std) / tp.H)
    vp_a = {"250": 72.0 * 0.25, "200": 56.0 * 0.20}
    vp_b = {f"{int(t_b * 1000)}": 64.0 * t_b, "200": 64.0 * 0.20}
    besi_pa = (vp_a["250"] + vp_a["200"]) * BESI_KG["pelat"]
    besi_pb = vp_b[f"{int(t_b * 1000)}"] * kg_m3_b + vp_b["200"] * BESI_KG["pelat"]

    def ringkas_opsi(unsur, vol_pelat, besi_pelat, k_kol):
        vb, bb_ = sum(u["vol"] for u in unsur), sum(u["besi_kg"] for u in unsur)
        vp, vk = sum(vol_pelat.values()), sum(k_kol[k] ** 2 * H_KOLOM for k in KOLOM)
        return {"vol_balok": vb, "vol_pelat": vp, "vol_kolom": vk, "vol": vb + vp + vk, "besi_balok": bb_,
                "besi_pelat": besi_pelat, "besi_kolom": vk * BESI_KG["kolom"],
                "besi": bb_ + besi_pelat + vk * BESI_KG["kolom"]}
    sa = ringkas_opsi(ua, vp_a, besi_pa, k_a)
    sb = ringkas_opsi(ub, vp_b, besi_pb, b_kol_b)
    # ---------------- cek silang T-90
    a4, m46 = metode_a["x 68"], kel["B-T induk tangki x 68"]
    d_pel = (GAMMA_C * tp.H_TANGKI + tp.SIDL_ATAP) * 4.0 + GAMMA_C * an["b"] * (an["h"] - tp.H_TANGKI)
    t90 = {"P": P_TANGKI, "a_A": sum(t_a.values()), "a_B": sum(t_bk.values()),
           "b_ukuran_51": (a4["b"], a4["h"]), "b_ukuran_46": (m46["b"], m46["h"]),
           "b_Mneg_51": a4["Mneg"], "b_Mneg_46": m46["Mneg"], "b_Mpos_51": a4["Mpos"], "b_Mpos_46": m46["Mpos"],
           "c_tangan_total": r_tengah_dua_bentang([(d_pel, 0.0, 16.0), (info_tk["q"] * 4.0, 0.0, 12.0)]),
           "c_pynite_RD": float(an["R_D"][1]), "c_tangan_tangki": info_tk["tangan"]["anak_tangki_x68"],
           "c_pynite_tangki": info_tk["R_anak"][1]}
    return {"harga": harga, "tangki": tk, "info_tk": info_tk, "info_b": info_b, "metode_a": metode_a, "ua": ua, "ub": ub,
            "pelat": pel, "t_b": t_b, "balok_b": bb, "r_a": r_a, "r_ad": r_ad, "r_b": r_b, "w_a": w_a, "w_b": w_b,
            "t_a": t_a, "t_bk": t_bk, "n_a": n_a, "n_b": n_b, "kolom_b": kb, "k_a": k_a, "k_b": b_kol_b, "sa": sa, "sb": sb,
            "vp_a": vp_a, "vp_b": vp_b, "kg_m3_b": kg_m3_b, "biaya": hitung_biaya(sa, sb, n_a, n_b, harga),
            "ruang": hitung_ruang(ua, ub, b_kol_b, k_a), "t90": t90, "r_std": r_std, "d46": d, "pelat_a": pelat_a,
            "pelat_bb": pelat_bb, "wb_a": wb_a, "wb_b": wb_b, "wp_a": wp_a, "wp_b": wp_b}


def hitung_biaya(sa, sb, n_a, n_b, h):
    """Selisih B - A: beton, bekisting (per m3 beton), besi, tiang dan pile cap; total = langsung x (1 + BTL) x (1 + PPN)."""
    dv, db_ = sb["vol"] - sa["vol"], (sb["besi"] - sa["besi"]) / 1000.0
    dn = sum(n_b.values()) - sum(n_a.values())
    d_cap = dn * VOL_CAP_PER_TIANG
    beton, bekis, besi = dv * h["beton"], dv * h["bekisting"], db_ * h["besi"]
    tiang, cap = dn * h["biaya_tiang"], d_cap * h["biaya_cap_m3"]
    langsung = beton + bekis + besi + tiang + cap
    return {"d_vol": dv, "d_besi_t": db_, "d_tiang": dn, "d_cap_m3": d_cap, "beton": beton, "bekisting": bekis,
            "besi": besi, "tiang": tiang, "cap": cap, "langsung": langsung,
            "total": langsung * (1 + h["btl"]) * (1 + h["ppn"])}


def overlap(a, b):
    return max(0.0, min(a[1], b[1]) - max(a[0], b[0]))


def hitung_ruang(ua, ub, k_b, k_a):
    """Akibat ruang: tinggi bersih LT2, kolom, chiller, fasad, pusat massa."""
    na, ha = (lambda u: (u["nama"], u["h"]))(max(ua, key=lambda u: u["h"]))
    nb, hb_ = (lambda u: (u["nama"], u["h"]))(max(ub, key=lambda u: u["h"]))
    lantai = tb.LEVEL["LT3"] - tb.LEVEL["LT2"]
    pusat_a = ((TANGKI_A["x"][0] + TANGKI_A["x"][1]) / 2, (TANGKI_A["y"][0] + TANGKI_A["y"][1]) / 2)
    pusat_b = ((TANGKI_B["x"][0] + TANGKI_B["x"][1]) / 2, (TANGKI_B["y"][0] + TANGKI_B["y"][1]) / 2)
    return {"lantai": lantai, "balok_dalam_A": (na, ha), "balok_dalam_B": (nb, hb_), "bersih_A": lantai - ha,
            "bersih_B": lantai - hb_, "gap_chiller": TANGKI_A["y"][0] - CHILLER["y"][1],
            "hadap_A": overlap(TANGKI_A["x"], CHILLER["x"]), "hadap_B": overlap(TANGKI_B["x"], CHILLER["x"]),
            "puncak_A": tb.LEVEL["LT3"] + TANGKI_A["tinggi"], "puncak_B": tb.LEVEL["LT3"] + TANGKI_B["tinggi"],
            "parapet": tb.LEVEL["LT3"] + tb.PARAPET, "pusat_A": pusat_a, "pusat_B": pusat_b,
            "geser_pusat": math.hypot(pusat_b[0] - pusat_a[0], pusat_b[1] - pusat_a[1]),
            "jarak_lb2_A": TANGKI_A["x"][0] - LB2["x"][1], "jarak_lb2_B": TANGKI_B["x"][0] - LB2["x"][1],
            "tepi_utara_A": 75.0 - TANGKI_A["y"][1], "tepi_utara_B": 75.0 - TANGKI_B["y"][1]}


# ------------------------------------------------------------------ Excel
def _sel(lb, i, baris):
    return f"{lb.kol(i)}{baris}"


def _gabung(lb, r_awal, r_akhir, k0, k1):
    """Gabung kolom k0..k1 pada tiap baris data dan hitung ulang tinggi baris dari lebar gabungan."""
    from format_dokumen import tinggi_baris
    for rr in range(r_awal, r_akhir + 1):
        lb.ws.merge_cells(f"{lb.kol(k0)}{rr}:{lb.kol(k1)}{rr}")
        teks = [lb.ws[f"{lb.kol(i)}{rr}"].value for i in (0, k0, k1 + 1)]
        lebar = [lb.lebar[0], sum(lb.lebar[k0:k1 + 1]), lb.lebar[k1 + 1]]
        lb.ws.row_dimensions[rr].height = tinggi_baris(teks, lebar, 12)


def _lembar_opsi(wb, nama, nomor, judul, unsur, pelat, kolom, ket_ai, catatan):
    """Lembar unsur satu opsi: balok, pelat, kolom (volume, besi); kembalikan alamat jumlah untuk lembar lain."""
    from format_dokumen import AI, Lembar
    lb = Lembar(wb[nama], nomor, judul, [5, 30, 11, 11, 11, 13, 14, 14, 13, 60])
    lb.catatan(ket_ai + " " + catatan)
    lb.bagian("A", "Balok (volume = b x (h - tebal pelat di sisi balok) x L; besi dari As desain)")
    kep = ["No", "Unsur", "b (m)", "h (m)", "L (m)", "Tebal pelat (m)", "Volume (m³)", "Besi (kg)", "kg/m³", "Dasar ukuran"]
    baris = [[i + 1, u["nama"], u["b"], u["h"], u["L"], u["web"], None, u["besi_kg"], None, u["dasar"]]
             for i, u in enumerate(unsur)] + [["", "Jumlah balok", None, None, None, None, None, None, None, ""]]
    r0, a0, a1 = lb.tabel(kep, baris, rata=list("clcccccccl"),
                          fmt=[None, None, "0.00", "0.00", "0.0", "0.00", "0.00", "#,##0", "0", None],
                          fill_kolom={7: AI})
    ws = lb.ws
    for i in range(a0, a1):
        ws[_sel(lb, 6, i)] = f"={_sel(lb, 2, i)}*({_sel(lb, 3, i)}-{_sel(lb, 5, i)})*{_sel(lb, 4, i)}"
        ws[_sel(lb, 8, i)] = f"={_sel(lb, 7, i)}/{_sel(lb, 6, i)}"
    ws[_sel(lb, 6, a1)] = f"=SUM({_sel(lb, 6, a0)}:{_sel(lb, 6, a1 - 1)})"
    ws[_sel(lb, 7, a1)] = f"=SUM({_sel(lb, 7, a0)}:{_sel(lb, 7, a1 - 1)})"
    hasil = {"vol_balok": f"'{nama}'!{_sel(lb, 6, a1)}", "besi_balok": f"'{nama}'!{_sel(lb, 7, a1)}", "balok_a0": a0}
    lb.kosong()
    lb.bagian("B", "Pelat atap podium utara x 60-76 / y 67-75 (volume = luas x tebal)")
    baris = [[i + 1, p[0], p[1], p[2], None, p[3], None, p[4]] for i, p in enumerate(pelat)] + \
        [["", "Jumlah pelat", None, None, None, None, None, ""]]
    r0, p0, p1 = lb.tabel(["No", "Bagian", "Luas (m²)", "Tebal (m)", "Volume (m³)", "kg/m³", "Besi (kg)", "Dasar"],
                          baris, rata=list("clccccccl"), fmt=[None, None, "0.0", "0.00", "0.00", "0.0", "#,##0", None],
                          fill_kolom={5: AI}, beku=False)
    for i in range(p0, p1):
        ws[_sel(lb, 4, i)] = f"={_sel(lb, 2, i)}*{_sel(lb, 3, i)}"
        ws[_sel(lb, 6, i)] = f"={_sel(lb, 4, i)}*{_sel(lb, 5, i)}"
    ws[_sel(lb, 4, p1)] = f"=SUM({_sel(lb, 4, p0)}:{_sel(lb, 4, p1 - 1)})"
    ws[_sel(lb, 6, p1)] = f"=SUM({_sel(lb, 6, p0)}:{_sel(lb, 6, p1 - 1)})"
    hasil.update({"vol_pelat": f"'{nama}'!{_sel(lb, 4, p1)}", "besi_pelat": f"'{nama}'!{_sel(lb, 6, p1)}"})
    lb.kosong()
    lb.bagian("C", f"Kolom menerus LT1-LT3 (tinggi {idn(H_KOLOM, 1)} m, 2 x 4,5 m)")
    baris = [[i + 1, k[0], k[1], H_KOLOM, None, BESI_KG["kolom"], None, k[2]] for i, k in enumerate(kolom)] + \
        [["", "Jumlah kolom", None, None, None, None, None, ""]]
    r0, k0, k1 = lb.tabel(["No", "Kolom", "b (m)", "Tinggi (m)", "Volume (m³)", "kg/m³", "Besi (kg)", "Dasar"],
                          baris, rata=list("clccccccl"), fmt=[None, None, "0.00", "0.0", "0.00", "0", "#,##0", None],
                          beku=False)
    for i in range(k0, k1):
        ws[_sel(lb, 4, i)] = f"={_sel(lb, 2, i)}*{_sel(lb, 2, i)}*{_sel(lb, 3, i)}"
        ws[_sel(lb, 6, i)] = f"={_sel(lb, 4, i)}*{_sel(lb, 5, i)}"
    ws[_sel(lb, 4, k1)] = f"=SUM({_sel(lb, 4, k0)}:{_sel(lb, 4, k1 - 1)})"
    ws[_sel(lb, 6, k1)] = f"=SUM({_sel(lb, 6, k0)}:{_sel(lb, 6, k1 - 1)})"
    hasil.update({"vol_kolom": f"'{nama}'!{_sel(lb, 4, k1)}", "besi_kolom": f"'{nama}'!{_sel(lb, 6, k1)}"})
    lb.kosong()
    lb.bagian("D", "Jumlah opsi")
    r0, j0, j1 = lb.tabel(["No", "Besaran", "Nilai", "Satuan"], [
        [1, "Volume beton total unsur", None, "m³"], [2, "Besi total unsur", None, "kg"]],
        rata=list("clcc"), fmt=[None, None, "#,##0.00", None], beku=False)
    ws[_sel(lb, 2, j0)] = f"={hasil['vol_balok'].split('!')[1]}+{hasil['vol_pelat'].split('!')[1]}+{hasil['vol_kolom'].split('!')[1]}"
    ws[_sel(lb, 2, j1)] = f"={hasil['besi_balok'].split('!')[1]}+{hasil['besi_pelat'].split('!')[1]}+{hasil['besi_kolom'].split('!')[1]}"
    hasil.update({"vol": f"'{nama}'!{_sel(lb, 2, j0)}", "besi": f"'{nama}'!{_sel(lb, 2, j1)}", "lb": lb})
    return hasil


def buat_excel(keluar=BERKAS):
    from format_dokumen import AI, Lembar, set_font_bawaan

    r = hitung()
    h, a, b, kn = r["harga"], r["metode_a"], r["balok_b"], r["tangki"]
    bi, ru, t90, d46 = r["biaya"], r["ruang"], r["t90"], r["d46"]
    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)
    nama_lembar = ["Petunjuk", "Ringkasan dan Keputusan", "Data dan Letak", "Opsi A", "Opsi B", "Reaksi", "Biaya",
                   "Akibat Ruang", "Cek Silang T-90"]
    for n in nama_lembar:
        wb.create_sheet(n)
    ket_ai = LABEL + " " + LABEL_AI
    t_b = r["t_b"]
    ub_d = {u["nama"]: u for u in r["ub"]}

    # ---- 3 Data dan Letak
    lb = Lembar(wb["Data dan Letak"], 3, "Data dan letak tangki, opsi A dan opsi B", [5, 46, 16, 16, 10, 62])
    lb.catatan(ket_ai + " Tangki M-02 [Data Beban MEP Rinci, Daftar Alat]: panel baja dua kompartemen (150 + 60 m³), "
               f"berat operasi {idn(kn['berat_operasi'], 0)} kN (= 210 m³ x 9,81 + {idn(kn['berat_kosong'])} kN), di atap "
               "podium utara +21,85. Grid: as 7/8/9 = x 60/68/76, as F/G = y 67/75. Isi tangki = beban mati (SNI 1727 "
               "Pasal 3.1.3, seperti 4.6). Kolom hitung adalah rumus Excel.")
    ra, rb = TANGKI_A, TANGKI_B
    pd, pb = (ra["x"][1] - ra["x"][0], ra["y"][1] - ra["y"][0]), (rb["x"][1] - rb["x"][0], rb["y"][1] - rb["y"][0])
    isi = [
        ["Panjang x (m)", pd[0], pb[0], "m", "Opsi A tetap (4.6-4.7); opsi B = bay as 7-8."],
        ["Lebar y (m)", pd[1], pb[1], "m", ""],
        ["Tinggi tangki (m)", ra["tinggi"], rb["tinggi"], "m", "Opsi B: tinggi air 3,3 m (211 m³)."],
        ["Tepi barat x (m)", ra["x"][0], rb["x"][0], "m", "Tetap x 60 sehingga LB-2 tidak berubah."],
        ["Tepi timur x (m)", ra["x"][1], rb["x"][1], "m", ""],
        ["Tepi selatan y (m)", ra["y"][0], rb["y"][0], "m", ""],
        ["Tepi utara y (m)", ra["y"][1], rb["y"][1], "m", ""],
        ["Luas tapak (m²)", None, None, "m²", "Rumus: panjang x lebar."],
        ["Berat operasi (kN)", kn["berat_operasi"], kn["berat_operasi"], "kN", "Sama; isi 210 m³ + panel."],
        ["Tekanan di pelat (kPa)", None, None, "kPa", "Berat operasi / luas tapak."],
        ["Volume air (m³)", 210.0, None, "m³", "A: 150 + 60 m³ (data owner); B: 8 x 8 x 3,3 m (≥ 210 m³)."],
        ["Selisih tepi barat ke as 7 (m)", None, None, "m", "0,0 = tepat di as."],
        ["Selisih tepi timur ke as terdekat (m)", None, None, "m", "A: x 72 di tengah bentang as 8-9; B: tepat di as 8."],
        ["Selisih tepi selatan ke as F (m)", None, None, "m", ""],
        ["Selisih tepi utara ke as G (m)", None, None, "m", "A: y 73 2,0 m dari as G."],
        ["Jarak tepi barat tangki ke LB-2 (m)", None, None, "m", f"LB-2 x {idn(LB2['x'][0])}-{idn(LB2['x'][1])} / y {idn(LB2['y'][0])}-{idn(LB2['y'][1])}; pipa Δ ≈ 0."],
        ["Jarak tepi selatan ke chiller M-01 (m)", None, None, "m", f"Chiller y {idn(CHILLER['y'][0])}-{idn(CHILLER['y'][1])}."],
    ]
    r0, a0, a1 = lb.tabel(["No", "Besaran", "Opsi A", "Opsi B", "Satuan", "Keterangan"],
                          [[i + 1, *v] for i, v in enumerate(isi)], rata=list("clccll"),
                          fmt=[None, None, "0.00", "0.00", None, None], fill_kolom={3: AI})
    ws = lb.ws
    c = lambda i, k: _sel(lb, k, a0 + i)   # noqa: E731
    for k in (2, 3):
        ws[c(7, k)] = f"={c(0, k)}*{c(1, k)}"
        ws[c(9, k)] = f"={c(8, k)}/{c(7, k)}"
        ws[c(11, k)] = f"=ABS({c(3, k)}-{GRID_X['7']})"
        ws[c(12, k)] = f"=MIN(ABS({c(4, k)}-{GRID_X['8']}),ABS({c(4, k)}-{GRID_X['9']}))"
        ws[c(13, k)] = f"=ABS({c(5, k)}-{GRID_Y['F']})"
        ws[c(14, k)] = f"=ABS({c(6, k)}-{GRID_Y['G']})"
        ws[c(15, k)] = f"={c(3, k)}-{LB2['x'][1]}"
        ws[c(16, k)] = f"={c(5, k)}-{CHILLER['y'][1]}"
    ws[c(10, 3)] = f"={c(0, 3)}*{c(1, 3)}*3.3"
    ws[c(10, 3)].number_format = "0.0"
    lb.kosong()
    lb.catatan("Tepi dianggap di as bila selisih ≤ 0,05 m [tahap5_telaah.TOL_AS]. Opsi B: keempat tepi tepat di as 7, 8, F, G; "
               "opsi A: tepi timur dan utara di tengah bentang.")

    # ---- 4 Opsi A
    dasar_a = {"x 60": "4.6 B-T induk x 60/76", "x 68": "4.6 B-T induk x 68", "x 76": "4.6 B-T induk x 60/76",
               "y 67 (x 60-68)": "4.6 B-T induk y 67", "y 67 (x 68-76)": "4.6 B-T induk y 67",
               "y 75 (x 60-68)": "4.6 B-P tepi LT3", "y 75 (x 68-76)": "4.6 B-P tepi LT3",
               "anak y 71 (x 60-76)": "4.6 balok anak tangki (500 x 900, 2 bentang)"}
    ua = [dict(u, dasar=dasar_a[u["nama"]]) for u in r["ua"]]
    pelat_a = [("Pelat tangki 250 di bawah tangki (x 60-72, y 67-73)", 72.0, 0.25, "4.5", BESI_KG["pelat"]),
               ("Pelat atap standar 200 di sisanya", 56.0, 0.20, "4.5", BESI_KG["pelat"])]
    pelat_a = [[p[0], p[1], p[2], p[4], p[3]] for p in pelat_a]
    kolom_a = [(f"K ({idn(k[0], 0)}; {idn(k[1], 0)})", r["k_a"][k], "4.7") for k in KOLOM]
    ha = _lembar_opsi(wb, "Opsi A", 4, "Opsi A: tangki 12 x 6 x 3,0 m tetap (4.5-4.7)", ua, pelat_a, kolom_a, ket_ai,
                      "Ukuran = hasil 4.5-4.7 yang disetujui Defsa (kolom 0,95 di as 8 dan 0,80 di as 7 dan 9, 4.7). Besi balok dari As desain 4.6 (tulangan atas + bawah "
                      "+ 5 % lewatan, sengkang rapat 2h dan jarang, tulangan samping); pelat dan kolom pakai rasio 3.6 (100 dan 200 kg/m³).")
    ws = wb["Opsi A"]
    lb_a = ha["lb"]
    lb_a.kosong()
    lb_a.bagian("E", "Cek silang metode 5.1 terhadap 4.6 (balok penumpu opsi A)")
    rows = []
    kel46 = {"x 68": "B-T induk tangki x 68", "x 60": "B-T induk tangki x 60/76", "x 76": "B-T induk tangki x 60/76",
             "y 67 (x 60-68)": "B-T induk tangki y 67", "y 67 (x 68-76)": "B-T induk tangki y 67"}
    kel = {x["kelompok"]: x for x in d46["r46"]["kelompok"]}
    for i, (nm, m) in enumerate(a.items()):
        k46 = kel[kel46[nm]]
        rows.append([i + 1, nm, f"{idn(m['b'], 2)} x {idn(m['h'], 2)}", f"{idn(k46['b'], 2)} x {idn(k46['h'], 2)}",
                     m["Mneg"], k46["Mneg"], None, m["Mpos"], k46["Mpos"],
                     "Kelompok 4.6 = terburuk x 60 dan x 76" if nm in ("x 60", "x 76") else ""])
    e0, e_a0, e_a1 = lb_a.tabel(["No", "Balok", "Ukuran 5.1", "Ukuran 4.6", "Mu- 5.1 (kNm)", "Mu- 4.6 (kNm)", "Selisih Mu-",
                                 "Mu+ 5.1 (kNm)", "Mu+ 4.6 (kNm)", "Keterangan"], rows, rata=list("clccccccc") + ["l"],
                                fmt=[None, None, None, None, "#,##0", "#,##0", "0.0%", "#,##0", "#,##0", None],
                                fill_kolom={4: AI, 7: AI}, beku=False)
    for i in range(len(rows)):
        ws[_sel(lb_a, 6, e_a0 + i)] = f"={_sel(lb_a, 4, e_a0 + i)}/{_sel(lb_a, 5, e_a0 + i)}-1"
    lb_a.catatan("Metode 5.1 = PyNite dengan pegas putar kolom + amplop gempa 4.6; muka kolom hc = 0,75 m seperti 4.6. Mu+ 4.6 "
                 "dari 3D penuh. Dikerjakan sendiri-sendiri, x 76 lebih ringan (400 x 700); kelompok 4.6 memakai yang "
                 "terburuk dari x 60 dan x 76.")

    # ---- 5 Opsi B
    dasar_b = {n: "5.1 metode sama (pegas kolom + amplop gempa 4.6)" for n in ub_d}
    dasar_b["y 75 (x 68-76)"] = "4.6 B-P tepi LT3 (standar, tidak berubah)"
    dasar_b["x 76"] = "5.1; kembali ke standar 350 x 600"
    ub = [dict(u, dasar=dasar_b[u["nama"]]) for u in r["ub"]]
    pelat_b_ = [[f"Pelat tangki {int(t_b * 1000)} di bay as 7-8 / F-G (x 60-68, y 67-75)", 64.0, t_b, r["kg_m3_b"],
                 "5.1"],
                ["Pelat atap standar 200 di bay as 8-9 / F-G (kembali standar)", 64.0, 0.20, BESI_KG["pelat"], "4.5"]]
    kolom_b_ = [(f"K ({idn(k[0], 0)}; {idn(k[1], 0)})", r["k_b"][k],
                 "5.1") for k in KOLOM]
    hb = _lembar_opsi(wb, "Opsi B", 5, f"Opsi B: tangki 8 x 8 x 3,5 m di bay as 7-8 / F-G", ub, pelat_b_, kolom_b_, ket_ai,
                      "Metode sama dengan opsi A. Pelat B: besi = 100 kg/m³ x rasio As desain B terhadap pelat 200 standar (DDM 4.5). Beban amplop 45 derajat: tiap balok W/4. Momen gempa = amplop 4.6 di posisi "
                      "yang sama (konservatif: balok lebih kecil menarik gempa lebih kecil).")
    lb_b = hb["lb"]
    lb_b.kosong()
    lb_b.bagian("E", "Pelat dua arah 8 x 8 (DDM 4.5, beban tangki 33,9 kPa sebagai beban mati)")
    rows = [[i + 1, f"{int(t * 1000)}", p["rasio_lentur"], p["rasio_geser"], p["lentur_ok"], p["geser_ok"],
             "Dipilih" if t == t_b else "Tidak cukup"] for i, (t, p) in enumerate(r["pelat"].items())]
    lb_b.tabel(["No", "Tebal (mm)", "Mu/φMn terburuk", "Vu/φVc", "Lentur", "Geser", "Status"],
               [[x[0], x[1], x[2], x[3], "OK" if x[4] else "TIDAK", "OK" if x[5] else "TIDAK", x[6]] for x in rows],
               rata=list("clcccc") + ["l"], fmt=[None, None, "0.00", "0.00", None, None, None], fill_kolom={2: AI, 3: AI},
               beku=False)
    lb_b.catatan("Geser satu arah seperti 4.5 (Pers. 22.5.5.1, lebar 1 m, qu penuh) menentukan: 250 dan 300 mm tidak "
                 "cukup. Kekakuan balok tepi αf diambil dari balok terkecil di sekeliling (400 x 700).")
    lb_b.kosong()
    lb_b.bagian("F", "Balok opsi B, hasil metode 5.1")
    rows = [[i + 1, nm, f"{idn(d_['b'], 2)} x {idn(d_['h'], 2)}", d_["Mneg"], d_["Mpos"], d_["Vu"], d_["E_face"],
             d_["Tu"], "OK" if d_["ok"] else "TIDAK"] for i, (nm, d_) in enumerate(b.items())]
    lb_b.tabel(["No", "Balok", "Ukuran", "Mu- (kNm)", "Mu+ (kNm)", "Vu (kN)", "E muka (kNm)", "Tu (kNm)", "Cek 4.6"], rows,
               rata=list("clcccccc") + ["c"], fmt=[None, None, None, "#,##0", "#,##0", "#,##0", "#,##0", "#,##0", None],
               fill_kolom={3: AI, 4: AI}, beku=False)
    lb_b.kosong()
    lb_b.bagian("G", "Kolom opsi B: kriteria aksial 4.7")
    rows = [[i + 1, f"({idn(k[0], 0)}; {idn(k[1], 0)})", v["b_A"], v["Pu_A"], v["phiPmax_A"], v["Pu_B"], v["b_B"],
             v["phiPmax_B"], v["Pu_B"] / v["phiPmax_B"]] for i, (k, v) in enumerate(r["kolom_b"].items())]
    lb_b.tabel(["No", "Kolom", "b A (m)", "Pu A (kN)", "φPn,maks A (kN)", "Pu B (kN)", "b B (m)", "φPn,maks B (kN)", "Pu/φPn,maks B"],
               rows, rata=list("clcccccc") + ["c"], fmt=[None, None, "0.00", "#,##0", "#,##0", "#,##0", "0.00", "#,##0", "0.00"],
               fill_kolom={5: AI, 6: AI}, beku=False)
    lb_b.catatan("Pu A = Pu terfaktor maksimum kolom di 4.7 (semua kombinasi); Pu B = Pu A + 1,2 x selisih D layan B - A. "
                 "φPn,maks = 0,65 x 0,80 Po (SNI 2847 Tabel 22.4.2.1 hal. 480 dan Tabel 21.2.2 hal. 471), ρ ≤ 0,04 [4.7]. "
                 "Kolom 0,95/0,80 di opsi A ditetapkan P-M dan kolom kuat balok lemah (4.7), bukan aksial; untuk opsi B "
                 "P-M dan ΣMnc/ΣMnb belum dihitung ulang (balok lebih kecil: lebih ringan; wajib dicek bila Defsa memilih B).")

    # ---- 6 Reaksi
    lb = Lembar(wb["Reaksi"], 6, "Reaksi tangki ke kolom dan jumlah tiang", [5, 16, 14, 14, 16, 14, 16, 14, 11, 11, 11])
    lb.catatan(ket_ai + " Bagian tangki: pelat → balok → kolom dengan statika sederhana. Opsi A: pelat satu arah 4 m, lajur 2 m ke "
               "balok y 67 dan 4 m ke balok anak y 71 (seperti 4.6), balok anak dua bentang (PyNite), balok induk x 60/68/76 "
               "meneruskan beban tengah bentang setengah-setengah ke y 67 dan y 75. Opsi B: pelat 8 x 8 beban amplop 45 derajat, "
               "tiap balok W/4, tiap ujung W/8. R layan A = D + L di dasar kolom LT1-LT2 dari analisis gravitasi 4.7 (A sudah "
               "memuat tangki).")
    lb.bagian("A", "Konstanta")
    kr0, ka0, ka1 = lb.tabel(["No", "Besaran", "Nilai", "Satuan", "Sumber"], [
        [1, "Beban izin tiang bor Ø800", Q_IZIN_TIANG, "kN", "3.7"],
        [2, "Tiang minimum per pile cap (max(2, ceil(R/izin)))", 2, "tiang", "3.7"],
        [3, "Berat operasi tangki", kn["berat_operasi"], "kN", "Daftar Alat"],
        [4, "Volume pile cap per tiang", VOL_CAP_PER_TIANG, "m³", "3.8"],
    ], rata=list("clccl"), fmt=[None, None, "#,##0.0", None, None])
    ws = lb.ws
    q_izin, n_min, p_tk = (f"${lb.kol(2)}${ka0 + i}" for i in range(3))
    lb.kosong()
    lb.bagian("B", "Rincian berat unsur lain per kolom (kN): balok, pelat, kolom sendiri")
    rows = []
    for i, k in enumerate(KOLOM):
        rows.append([i + 1, f"({idn(k[0], 0)}; {idn(k[1], 0)})", r["wb_a"][k], r["wp_a"][k], GAMMA_C * r["k_a"][k] ** 2 * H_KOLOM,
                     r["wb_b"][k], r["wp_b"][k], GAMMA_C * r["k_b"][k] ** 2 * H_KOLOM])
    d0, da0, da1 = lb.tabel(["No", "Kolom", "Balok A", "Pelat A", "Kolom A", "Balok B", "Pelat B", "Kolom B"], rows,
                            rata=list("clcccccc"), fmt=[None, None] + ["#,##0.0"] * 6, fill_kolom={k: AI for k in range(2, 8)},
                            beku=False)
    lb.catatan("Alokasi [Asumsi]: balok setengah ke tiap ujung; balok anak y 71 ke tiga balok induk (0,1875/0,625/0,1875) lalu "
               "setengah ke y 67 dan y 75; pelat tiap bay dibagi rata ke empat kolom sudutnya; kolom = berat sendiri 9,0 m.")
    lb.kosong()
    lb.bagian("C", "Reaksi layan dan jumlah tiang per pile cap")
    rows = []
    for i, k in enumerate(KOLOM):
        rows.append([i + 1, f"({idn(k[0], 0)}; {idn(k[1], 0)})", r["r_a"][k], r["t_a"][k], None, r["t_bk"][k], None, None, None, None, None])
    r0, a0, a1 = lb.tabel(["No", "Kolom (x; y)", "R layan A (kN)", "Tangki A (kN)", "Unsur lain A (kN)", "Tangki B (kN)",
                           "Unsur lain B (kN)", "R layan B (kN)", "Tiang A", "Tiang B", "Δ tiang"],
                          rows + [["", "Jumlah", None, None, None, None, None, None, None, None, None]],
                          rata=["c", "c"] + ["c"] * 9, fmt=[None, None] + ["#,##0.0"] * 6 + ["0", "0", "0"],
                          fill_kolom={2: AI, 3: AI, 5: AI}, beku=False)
    for i in range(6):
        row = a0 + i
        dr = da0 + i
        ws[_sel(lb, 4, row)] = f"=SUM({_sel(lb, 2, dr)}:{_sel(lb, 4, dr)})"
        ws[_sel(lb, 6, row)] = f"=SUM({_sel(lb, 5, dr)}:{_sel(lb, 7, dr)})"
        ws[_sel(lb, 7, row)] = f"={_sel(lb, 2, row)}-{_sel(lb, 3, row)}-{_sel(lb, 4, row)}+{_sel(lb, 5, row)}+{_sel(lb, 6, row)}"
        ws[_sel(lb, 8, row)] = f"=MAX({n_min},ROUNDUP({_sel(lb, 2, row)}/{q_izin},0))"
        ws[_sel(lb, 9, row)] = f"=MAX({n_min},ROUNDUP({_sel(lb, 7, row)}/{q_izin},0))"
        ws[_sel(lb, 10, row)] = f"={_sel(lb, 9, row)}-{_sel(lb, 8, row)}"
    for k in range(2, 11):
        ws[_sel(lb, k, a1)] = f"=SUM({_sel(lb, k, a0)}:{_sel(lb, k, a1 - 1)})"
    reaksi = {"a0": a0, "a1": a1, "lb": lb}
    lb.catatan("R layan B = R layan A - (tangki A + unsur lain A) + (tangki B + unsur lain B). Beban hidup atap dan SIDL sama di "
               "A dan B sehingga saling meniadakan. Gempa tidak ikut (reaksi layan statis); 4.3 tidak menyimpan reaksi per "
               "kolom, jadi dasar R layan A = analisis gravitasi 4.7. Tiang A per pile cap dapat berbeda dari tiang 3.7/LA.1 "
               "(hitungan kasar 3.7); yang dipakai hanya selisihnya.")
    lb.kosong()
    lb.bagian("D", "Keseimbangan bagian tangki (jumlah ke kolom = berat operasi)")
    q0, q_a0, q_a1 = lb.tabel(["No", "Opsi", "Jumlah ke kolom (kN)", "Berat operasi (kN)", "Selisih (%)", "Status"], [
        [1, "A", None, None, None, None], [2, "B", None, None, None, None]], rata=list("clcccc"),
        fmt=[None, None, "#,##0.0", "#,##0.0", "0.000%", None], beku=False)
    for i, kol in enumerate((3, 5)):
        rr = q_a0 + i
        ws[_sel(lb, 2, rr)] = f"={_sel(lb, kol, a1)}"
        ws[_sel(lb, 3, rr)] = f"={p_tk}"
        ws[_sel(lb, 4, rr)] = f"={_sel(lb, 2, rr)}/{_sel(lb, 3, rr)}-1"
        ws[_sel(lb, 5, rr)] = f'=IF(ABS({_sel(lb, 4, rr)})<=0.005,"Lolos","TIDAK")'
    reaksi.update({"jumlah_tangki_A": f"'Reaksi'!{_sel(lb, 2, q_a0)}", "jumlah_tangki_B": f"'Reaksi'!{_sel(lb, 2, q_a0 + 1)}",
                   "berat": f"'Reaksi'!{p_tk}", "tiang_A": f"'Reaksi'!{_sel(lb, 8, a1)}",
                   "tiang_B": f"'Reaksi'!{_sel(lb, 9, a1)}", "d_tiang": f"'Reaksi'!{_sel(lb, 10, a1)}"})

    # ---- 7 Biaya
    lb = Lembar(wb["Biaya"], 7, "Selisih biaya opsi B terhadap opsi A", [5, 46, 14, 14, 14, 14, 16, 46])
    lb.catatan(ket_ai + " Harga satuan dari 3.8 (lembar Parameter dan Kebutuhan Nyata). Biaya langsung = volume x harga; total = "
               "langsung x (1 + biaya tidak langsung) x (1 + PPN). Hanya selisih unsur di bay as 7-9 / F-G yang dihitung; "
               "unsur yang sama di A dan B tidak ikut. Pipa air: selisih ≈ 0 (LB-2 tetap 1,2 m dari tepi barat).")
    lb.bagian("A", "Parameter harga (juta Rp)")
    pr0, p_a0, p_a1 = lb.tabel(["No", "Parameter", "Nilai", "Satuan", "Sumber"], [
        [1, "Beton per m³", h["beton"], "juta/m³", "3.8 Parameter 8"],
        [2, "Bekisting per m³ beton", h["bekisting"], "juta/m³", "3.8 Parameter 9"],
        [3, "Baja tulangan terpasang", h["besi"], "juta/ton", "3.8 Parameter 10"],
        [4, "Biaya tiang bor Ø800 per tiang", h["biaya_tiang"], "juta/tiang",
         f"3.8 Kebutuhan Nyata baris 1: {idn(h['biaya_tiang_total'], 1)} juta / {idn(h['n_tiang_3_8'], 0)} tiang"],
        [5, "Biaya pile cap per m³", h["biaya_cap_m3"], "juta/m³",
         f"3.8 Kebutuhan Nyata baris Pile cap: {idn(h['biaya_cap_total'], 1)} juta / {idn(h['vol_cap_total'], 1)} m³"],
        [6, "Biaya tidak langsung", h["btl"], "-", "3.8 Parameter 5"],
        [7, "PPN", h["ppn"], "-", "3.8 Parameter 6"],
    ], rata=list("clccl") + ["l"], fmt=[None, None, "0.0000", None, None])
    ws = lb.ws
    pc = {nm: f"${lb.kol(2)}${p_a0 + i}" for i, nm in enumerate(("beton", "bekisting", "besi", "tiang", "cap", "btl", "ppn"))}
    lb.kosong()
    lb.bagian("B", "Selisih volume dan biaya (B - A)")
    rows = [
        [1, "Volume beton unsur (m³)", None, None, None, None, None, "Opsi A / Opsi B jumlah"],
        [2, "Besi (ton)", None, None, None, None, None, "Opsi A / Opsi B jumlah"],
        [3, "Tiang bor Ø800 (buah)", None, None, None, None, None, "Reaksi: ceil(R / 911), minimum 2 per cap"],
        [4, "Volume pile cap (m³)", None, None, None, None, None, "4,5 m³ per tiang [3.8]"],
    ]
    b0, b_a0, b_a1 = lb.tabel(["No", "Besaran", "Opsi A", "Opsi B", "Selisih B-A", "Harga (juta)", "Biaya (juta Rp)", "Dasar"], rows,
                              rata=list("clccccc") + ["l"], fmt=[None, None, "#,##0.00", "#,##0.00", "#,##0.00", "0.0000",
                                                                  "#,##0.0", None], beku=False)
    ref_ha, ref_hb = ha, hb
    ws[_sel(lb, 2, b_a0)] = f"={ref_ha['vol']}"
    ws[_sel(lb, 3, b_a0)] = f"={ref_hb['vol']}"
    ws[_sel(lb, 2, b_a0 + 1)] = f"={ref_ha['besi']}/1000"
    ws[_sel(lb, 3, b_a0 + 1)] = f"={ref_hb['besi']}/1000"
    ws[_sel(lb, 2, b_a0 + 2)] = f"={reaksi['tiang_A']}"
    ws[_sel(lb, 3, b_a0 + 2)] = f"={reaksi['tiang_B']}"
    ws[_sel(lb, 2, b_a0 + 3)] = f"={_sel(lb, 2, b_a0 + 2)}*{VOL_CAP_PER_TIANG}"
    ws[_sel(lb, 3, b_a0 + 3)] = f"={_sel(lb, 3, b_a0 + 2)}*{VOL_CAP_PER_TIANG}"
    for i in range(4):
        ws[_sel(lb, 4, b_a0 + i)] = f"={_sel(lb, 3, b_a0 + i)}-{_sel(lb, 2, b_a0 + i)}"
    ws[_sel(lb, 5, b_a0)] = f"={pc['beton']}+{pc['bekisting']}"
    ws[_sel(lb, 5, b_a0 + 1)] = f"={pc['besi']}"
    ws[_sel(lb, 5, b_a0 + 2)] = f"={pc['tiang']}"
    ws[_sel(lb, 5, b_a0 + 3)] = f"={pc['cap']}"
    for i in range(4):
        ws[_sel(lb, 6, b_a0 + i)] = f"={_sel(lb, 4, b_a0 + i)}*{_sel(lb, 5, b_a0 + i)}"
    lb.kosong()
    r0, t_a0, t_a1 = lb.tabel(["No", "Rekap", "Nilai (juta Rp)", "Rumus"], [
        [1, "Δ biaya langsung", None, "jumlah baris 1-4 kolom Biaya"],
        [2, "Δ biaya tidak langsung", None, "langsung x BTL"],
        [3, "Δ subtotal", None, "langsung + tidak langsung"],
        [4, "Δ PPN", None, "subtotal x PPN"],
        [5, "Δ total dengan tidak langsung dan PPN", None, "langsung x (1 + BTL) x (1 + PPN)"],
    ], rata=list("clcl"), fmt=[None, None, "#,##0.0", None], beku=False)
    ws[_sel(lb, 2, t_a0)] = f"=SUM({_sel(lb, 6, b_a0)}:{_sel(lb, 6, b_a1)})"
    ws[_sel(lb, 2, t_a0 + 1)] = f"={_sel(lb, 2, t_a0)}*{pc['btl']}"
    ws[_sel(lb, 2, t_a0 + 2)] = f"={_sel(lb, 2, t_a0)}+{_sel(lb, 2, t_a0 + 1)}"
    ws[_sel(lb, 2, t_a0 + 3)] = f"={_sel(lb, 2, t_a0 + 2)}*{pc['ppn']}"
    ws[_sel(lb, 2, t_a0 + 4)] = f"={_sel(lb, 2, t_a0 + 2)}+{_sel(lb, 2, t_a0 + 3)}"
    biaya = {"langsung": f"'Biaya'!{_sel(lb, 2, t_a0)}", "total": f"'Biaya'!{_sel(lb, 2, t_a0 + 4)}",
             "vol": f"'Biaya'!{_sel(lb, 4, b_a0)}", "besi": f"'Biaya'!{_sel(lb, 4, b_a0 + 1)}",
             "tiang": f"'Biaya'!{_sel(lb, 4, b_a0 + 2)}", "a0": b_a0, "t0": t_a0, "lb": lb}
    lb.catatan("Selisih negatif = opsi B lebih murah. Besi balok dari As desain, pelat dan kolom dari rasio kg/m³ (3.6): estimasi "
               "tingkat konsep, bukan RAB.")

    # ---- 8 Akibat Ruang
    lb = Lembar(wb["Akibat Ruang"], 8, "Akibat ruang dan lingkungan tangki", [5, 48, 18, 18, 8, 64])
    lb.catatan(ket_ai + " Tinggi bersih = tinggi lantai LT2 4,50 m - tinggi total balok terdalam di bawah atap podium (balok "
               "menyatu dengan pelat sehingga tebal pelat tidak dikurangi lagi). Belum termasuk plafon dan MEP gantung.")
    rows = [
        ["Balok terdalam di atas ruang LT2", f"{ru['balok_dalam_A'][0]} ({idn(ru['balok_dalam_A'][1], 2)} m)",
         f"{ru['balok_dalam_B'][0]} ({idn(ru['balok_dalam_B'][1], 2)} m)", "", "Opsi A: balok induk x 68 600 x 1.200."],
        ["Tinggi lantai LT2 (m)", ru["lantai"], ru["lantai"], "m", "LT2 +17,35 ke atap podium +21,85 [tahap4_beban.LEVEL]."],
        ["Tinggi balok terdalam (m)", ru["balok_dalam_A"][1], ru["balok_dalam_B"][1], "m", ""],
        ["Tinggi bersih di bawah balok terdalam (m)", None, None, "m", "Rumus: tinggi lantai - tinggi balok. x 60-62 di bawah "
         "tangki adalah void/taman LT2 (VOID_LT2), tinggi bersih di sisi timur as 7."],
        ["Kolom di ruang LT2 as 8 (m)", r["k_a"][(68.0, 67.0)], r["k_b"][(68.0, 67.0)], "m", "Kolom transfer 0,95 (A) vs kolom podium (B)."],
        ["Kolom di ruang LT2 as 7 dan 9 (m)", r["k_a"][(60.0, 67.0)], r["k_b"][(60.0, 67.0)], "m", "0,80 (A) vs kolom podium (B)."],
        ["Sisi tangki menghadap chiller: panjang (m)", ru["hadap_A"], ru["hadap_B"], "m",
         "Irisan x tangki dengan x chiller 66-77."],
        ["Jarak tepi selatan tangki ke chiller (m)", ru["gap_chiller"], ru["gap_chiller"], "m",
         "Syarat jarak bebas chiller berpendingin udara: belum ada di acuan (data pabrikan)."],
        ["Puncak tangki (+m)", ru["puncak_A"], ru["puncak_B"], "m", "Lantai atap +21,85 + tinggi tangki."],
        ["Puncak parapet (+m)", ru["parapet"], ru["parapet"], "m", "Parapet 1,2 m [tahap4_beban.PARAPET]."],
        ["Jarak tepi utara tangki ke as G / fasad (m)", ru["tepi_utara_A"], ru["tepi_utara_B"], "m",
         "Opsi B sejajar tepi utara gedung: terlihat dari jalan, 3,5 m menjulang 2,3 m di atas parapet; perlu keputusan arsitek (skrining)."],
        ["Jarak tepi barat ke LB-2 (m)", ru["jarak_lb2_A"], ru["jarak_lb2_B"], "m", "Tetap: pipa turun ke koridor LT2 tidak berubah."],
        ["Pusat tangki (x; y)", f"({idn(ru['pusat_A'][0], 1)}; {idn(ru['pusat_A'][1], 1)})",
         f"({idn(ru['pusat_B'][0], 1)}; {idn(ru['pusat_B'][1], 1)})", "m", "Pergeseran 2,2 m."],
        ["Pergeseran pusat massa gempa (m)", None, ru["geser_pusat"], "m",
         f"Tangki {idn(kn['berat_operasi'], 0)} kN = {idn(kn['berat_operasi'] / d46['W_K2'] * 100, 1)} % dari W K2 "
         f"{idn(d46['W_K2'], 0)} kN; geser pusat massa gedung ≈ {idn(kn['berat_operasi'] / d46['W_K2'] * ru['geser_pusat'] * 1000, 0)} mm, "
         "jauh di bawah eksentrisitas tak terduga 5 %: diabaikan."],
    ]
    r0, a0, a1 = lb.tabel(["No", "Besaran", "Opsi A", "Opsi B", "Satuan", "Keterangan"], [[i + 1, *v] for i, v in enumerate(rows)],
                          rata=list("clccll"), fmt=[None, None, "0.00", "0.00", None, None], fill_kolom={2: AI, 3: AI})
    ws = lb.ws
    for k in (2, 3):
        ws[_sel(lb, k, a0 + 3)] = f"={_sel(lb, k, a0 + 1)}-{_sel(lb, k, a0 + 2)}"
    ruang = {"bersih_A": f"'Akibat Ruang'!{_sel(lb, 2, a0 + 3)}", "bersih_B": f"'Akibat Ruang'!{_sel(lb, 3, a0 + 3)}"}

    # ---- 9 Cek Silang T-90
    lb = Lembar(wb["Cek Silang T-90"], 9, "Cek silang T-90 (langkah 5.1)", [5, 52, 16, 16, 12, 12, 12, 56])
    lb.catatan(ket_ai + " Toleransi ditetapkan sebelum dihitung: (a) 0,5 %; (b) Mu 15 % dan ukuran sama; (c) 10 %.")
    rows = [
        ["(a) Jumlah bagian tangki ke kolom, opsi A (kN)", t90["a_A"], t90["P"], None, 0.005, None, "Keseimbangan pelat → balok → kolom."],
        ["(a) Jumlah bagian tangki ke kolom, opsi B (kN)", t90["a_B"], t90["P"], None, 0.005, None, "Segitiga 45 derajat, 4 x 542 kN."],
        ["(b) Mu- balok induk x 68 opsi A: 5.1 vs 4.6 (kNm)", t90["b_Mneg_51"], t90["b_Mneg_46"], None, 0.15, None,
         f"Ukuran 5.1 {idn(t90['b_ukuran_51'][0], 2)} x {idn(t90['b_ukuran_51'][1], 2)} = 4.6 "
         f"{idn(t90['b_ukuran_46'][0], 2)} x {idn(t90['b_ukuran_46'][1], 2)}."],
        ["(b) Mu+ balok induk x 68 opsi A: 5.1 vs 4.6 (kNm)", t90["b_Mpos_51"], t90["b_Mpos_46"], None, 0.15, None, "4.6 dari 3D penuh."],
        ["(c) Reaksi balok anak di x 68, total D: statika tangan vs R_D 4.6 (kN)", t90["c_tangan_total"], t90["c_pynite_RD"], None,
         0.10, None, "Tangan: garis pengaruh dua bentang R = P a (3L² - a²)/(2L³), dijumlahkan."],
        ["(c) Bagian tangki saja ke x 68: tangan vs PyNite (kN)", t90["c_tangan_tangki"], t90["c_pynite_tangki"], None, 0.10, None,
         "Beban tangki saja, lajur 4 m x 30,1 kPa x 12 m."],
    ]
    r0, a0, a1 = lb.tabel(["No", "Cek", "Cara 1", "Cara 2", "Selisih", "Toleransi", "Status", "Keterangan"],
                          [[i + 1, *v] for i, v in enumerate(rows)], rata=list("clcccccl"),
                          fmt=[None, None, "#,##0.0", "#,##0.0", "0.00%", "0.0%", None, None], fill_kolom={2: AI, 3: AI})
    ws = lb.ws
    for i in range(len(rows)):
        rr = a0 + i
        ws[_sel(lb, 4, rr)] = f"={_sel(lb, 2, rr)}/{_sel(lb, 3, rr)}-1"
        ws[_sel(lb, 6, rr)] = f'=IF(ABS({_sel(lb, 4, rr)})<={_sel(lb, 5, rr)},"Lolos","TIDAK")'
    ws[_sel(lb, 2, a0)] = f"={reaksi['jumlah_tangki_A']}"
    ws[_sel(lb, 3, a0)] = f"={reaksi['berat']}"
    ws[_sel(lb, 2, a0 + 1)] = f"={reaksi['jumlah_tangki_B']}"
    ws[_sel(lb, 3, a0 + 1)] = f"={reaksi['berat']}"
    t90_ref = {"a0": a0}
    lb.kosong()
    lb.catatan("(b) Mu- dan Mu+ = momen terfaktor di muka kolom dan lapangan (selubung kombinasi 4.6). Metode 5.1: pegas putar "
               "ujung = 4 Ec 0,70 Ig / 4,5 m kolom 0,95 (kekakuan retak Tabel 6.6.3.1.1 seperti 4.3); gravitasi D dan L dari PyNite; "
               "gempa dari amplop |E| 4.6 pada balok yang sama dengan K1 dan K2 (dipakai dua arah, konservatif).")

    # ---- 2 Ringkasan dan Keputusan
    lb = Lembar(wb["Ringkasan dan Keputusan"], 2, "Ringkasan dan keputusan, opsi A vs opsi B", [5, 60, 24, 24, 14, 34])
    lb.catatan(f"STATUS: {STATUS}. " + ket_ai)
    lb.kosong()
    lb.bagian("A", "Perbandingan")
    sa, sb = r["sa"], r["sb"]
    kunci_a = {u["nama"]: u for u in r["ua"]}
    rows = [
        ["Tangki (x 60-72 / y 67-73) vs (x 60-68 / y 67-75)", "12 x 6 x 3,0 m", "8 x 8 x 3,5 m", "", "Data dan Letak"],
        ["Tekanan di pelat (kPa)", idn(r["info_tk"]["q"], 1), idn(P_TANGKI / 64, 1), "", "Data dan Letak"],
        ["Tepi tepat di as", "2 dari 4", "4 dari 4", "", "Data dan Letak"],
        ["Pelat di bawah tangki", "250, satu arah, anak y 71", f"{int(t_b * 1000)}, dua arah, tanpa anak", "", "Opsi A, Opsi B"],
        ["Balok induk as 8 (x 68)", f"{idn(kunci_a['x 68']['b'], 2)} x {idn(kunci_a['x 68']['h'], 2)}",
         f"{idn(ub_d['x 68']['b'], 2)} x {idn(ub_d['x 68']['h'], 2)}", "", "Opsi A, Opsi B"],
        ["Balok induk as 7 (x 60)", f"{idn(kunci_a['x 60']['b'], 2)} x {idn(kunci_a['x 60']['h'], 2)}",
         f"{idn(ub_d['x 60']['b'], 2)} x {idn(ub_d['x 60']['h'], 2)}", "", "Opsi A, Opsi B"],
        ["Kolom di ruang LT2 as 8 (m)", idn(r["k_a"][(68.0, 67.0)], 2), idn(r["k_b"][(68.0, 67.0)], 2), "", "Akibat Ruang"],
        ["Volume beton unsur (m³)", None, None, None, "Opsi A, Opsi B"],
        ["Besi unsur (ton)", None, None, None, "Opsi A, Opsi B"],
        ["Tiang bor Ø800 (buah)", None, None, None, "Reaksi"],
        ["Tinggi bersih di bawah balok terdalam LT2 (m)", None, None, None, "Akibat Ruang"],
        ["Δ biaya langsung (juta Rp)", "", None, "", "Biaya"],
        ["Δ biaya dengan BTL dan PPN (juta Rp)", "", None, "", "Biaya"],
        ["Sisi tangki menghadap chiller (m)", idn(ru["hadap_A"], 1), idn(ru["hadap_B"], 1), "", "Akibat Ruang"],
        ["Puncak tangki di atas parapet (m)", idn(ru["puncak_A"] - ru["parapet"], 2), idn(ru["puncak_B"] - ru["parapet"], 2), "",
         "Akibat Ruang"],
    ]
    r0, a0, a1 = lb.tabel(["No", "Besaran", "Opsi A", "Opsi B", "Selisih B-A", "Lembar"], [[i + 1, *v] for i, v in enumerate(rows)],
                          rata=list("clcccl"), fmt=[None, None, None, None, "#,##0.0", None], fill_kolom={2: AI, 3: AI})
    ws = lb.ws
    for i, (ka, kb_, fm) in enumerate(((ha["vol"], hb["vol"], "#,##0.0"), (f"{ha['besi']}/1000", f"{hb['besi']}/1000", "#,##0.0"),
                                       (reaksi["tiang_A"], reaksi["tiang_B"], "0"), (ruang["bersih_A"], ruang["bersih_B"], "0.00"))):
        rr = a0 + 7 + i
        ws[_sel(lb, 2, rr)] = f"={ka}"
        ws[_sel(lb, 3, rr)] = f"={kb_}"
        ws[_sel(lb, 4, rr)] = f"={_sel(lb, 3, rr)}-{_sel(lb, 2, rr)}"
        for k in (2, 3, 4):
            ws[_sel(lb, k, rr)].number_format = fm
    ws[_sel(lb, 4, a0 + 11)] = f"={biaya['langsung']}"
    ws[_sel(lb, 4, a0 + 12)] = f"={biaya['total']}"
    lb.kosong()
    lb.bagian("B", "Temuan")
    t0, ta0, ta1 = lb.tabel(["No", "Temuan", "", "", "", "Lembar"], [
        [1, f"Opsi B memuat tangki dalam satu bay (tepi di as 7, 8, F, G). Pelat {int(t_b * 1000)} mm dua arah menentukan geser "
            f"(250 dan 300 tidak cukup), tetapi balok induk x 68 turun dari 600 x 1.200 ke {idn(ub_d['x 68']['b'], 2)} x "
            f"{idn(ub_d['x 68']['h'], 2)} dan tinggi bersih LT2 naik dari {idn(ru['bersih_A'], 2)} ke {idn(ru['bersih_B'], 2)} m.",
         "", "", "", "Opsi A, Opsi B, Akibat Ruang"],
        [2, f"Selisih beton {idn(sb['vol'] - sa['vol'], 1)} m³, besi {idn((sb['besi'] - sa['besi']) / 1000, 1)} t, tiang "
            f"{idn(bi['d_tiang'], 0)}; Δ biaya langsung {idn(bi['langsung'], 1)} juta Rp (dengan BTL dan PPN "
            f"{idn(bi['total'], 1)} juta). Selisih kecil: keputusan lebih ditentukan ruang dan fasad.", "", "", "", "Biaya"],
        [3, f"Opsi B sejajar tepi utara gedung: tangki 3,5 m menjulang {idn(ru['puncak_B'] - ru['parapet'], 2)} m di atas parapet "
            f"(opsi A {idn(ru['puncak_A'] - ru['parapet'], 2)} m dan mundur 2,0 m dari as G); sisi menghadap chiller 6 m (A) turun "
            "ke 2 m (B), jarak tetap 1,3 m. Syarat jarak bebas chiller belum ada di acuan (data pabrikan).", "", "", "",
         "Akibat Ruang"],
        [4, "Kolom opsi B dipilih dengan kriteria aksial 4.7 (Pu ≤ φPn,maks); P-M dan ΣMnc/ΣMnb belum dihitung ulang dengan "
            "balok B dan harus dicek bila Defsa memilih B. Gempa balok B memakai amplop 4.6 (konservatif).", "", "", "",
         "Opsi B"],
        [5, "LB-2 dan pipa tetap (tepi barat x 60, 1,2 m dari bukaan). Pusat massa tangki bergeser 2,2 m, setara ±0,03 m pada "
            "pusat massa gedung: diabaikan.", "", "", "", "Akibat Ruang"],
    ], rata=list("cllllc"), fill_kolom={1: AI}, beku=False)
    _gabung(lb, ta0, ta1, 1, 4)
    lb.kosong()
    lb.bagian("C", "Keputusan Defsa (draf, menunggu persetujuan)")
    k0_, ka_0, ka_1 = lb.tabel(["No", "Pilihan", "", "", "", "Akibat"], [
        [1, "Opsi A: tangki 12 x 6 m tetap", "", "", "", "Tidak ada perubahan; 4.5-4.7 berlaku."],
        [2, "Opsi B: tangki 8 x 8 x 3,5 m di bay as 7-8 / F-G", "", "", "",
         "Ubah 4.5-4.7 (pelat, balok x 60/68/y 67/y 75, kolom), rancang ulang P-M dan SCWB kolom, usulan arsitek untuk fasad "
         "utara, minta data jarak chiller ke pemasok."],
    ], rata=list("clllll"), beku=False)
    _gabung(lb, ka_0, ka_1, 1, 4)

    # ---- 1 Petunjuk
    lb = Lembar(wb["Petunjuk"], 1, "Petunjuk kajian letak tangki (langkah 5.1)", [6, 120])
    lb.catatan(f"STATUS: {STATUS}. " + ket_ai)
    lb.kosong()
    lb.tabel(["No", "Petunjuk"], [[i + 1, s] for i, s in enumerate([
        "Dasar sama untuk dua opsi: beban operasi tangki 2.168 kN (Data Beban MEP Rinci, Daftar Alat M-02), isi tangki sebagai "
        "beban mati (SNI 1727 Pasal 3.1.3, seperti 4.6). A = 12 x 6 x 3,0 m di x 60-72 / y 67-73 (keputusan 4.6-4.7). B = "
        "8 x 8 x 3,5 m di x 60-68 / y 67-75 (tinggi air 3,3 m = 211 m³, 33,9 kPa).",
        "Metode sama untuk A dan B: balok penumpu = PyNite (tahap4_balok.balok_menerus) dengan pegas putar kolom ditambah amplop "
        "gempa 4.6; desain penampang SPGS = tahap4_balok.desain_penampang (SNI 2847:2019 Pasal 18.6, 22.5, 22.7 seperti 4.6). "
        "Pelat B = metode desain langsung tahap4_pelat (Pasal 8.10). Balok anak = tahap4_balok._desain_anak. Pasal lain "
        "(getaran, jarak chiller): belum ada di acuan.",
        "Ukuran opsi A di biaya = hasil 4.5-4.7 yang disetujui; hasil metode 5.1 untuk A hanya cek silang (lembar Opsi A, E, "
        "dan Cek Silang T-90).",
        "Reaksi layan A diambil dari analisis gravitasi 4.7 (A sudah memuat tangki); B = A dikurangi bagian tangki dan "
        "berat unsur lain A, ditambah bagian tangki dan berat unsur lain B. Tiang = ceil(R / 911 kN), minimum 2 (3.7).",
        "Harga dari 3.8; biaya langsung = volume x harga, total x (1 + BTL) x (1 + PPN). Besi balok dari As desain, pelat dan "
        "kolom rasio 3.6 [Asumsi]. Hanya selisih A vs B yang dihitung.",
        "Sel hijau diisi AI atas permintaan Defsa. Kolom bukan hijau berisi rumus Excel (dihitung ulang dan dicocokkan dengan "
        "Python di cocokkan()).",
        "Lembar: Ringkasan dan Keputusan; Data dan Letak; Opsi A; Opsi B; Reaksi; Biaya; Akibat Ruang; Cek Silang T-90.",
    ])], rata=list("cl"))

    keluar.parent.mkdir(parents=True, exist_ok=True)
    wb.save(keluar)
    return keluar


def cocokkan(berkas=BERKAS):
    """Hitung ulang di Excel, lalu bandingkan rumus dengan Python. Kembalikan (ok, pesan)."""
    from format_dokumen import hitung_ulang_excel
    ok, err = hitung_ulang_excel(berkas)
    if not ok:
        return False, f"Excel tidak bisa menghitung ulang: {err[:120]}"
    r = hitung()
    wb = openpyxl.load_workbook(berkas, data_only=True)
    pesan = []

    def cari(ws, label, kolom):
        for row in ws.iter_rows():
            for c in row:
                if c.value == label:
                    return ws.cell(c.row, c.column + kolom).value
        return None

    def bandingkan(nama, x, y, tol=0.01):
        if x is None or abs(x - y) > tol:
            pesan.append(f"{nama}: Excel {x} vs Python {y}")

    bandingkan("volume A", cari(wb["Opsi A"], "Volume beton total unsur", 1), r["sa"]["vol"])
    bandingkan("volume B", cari(wb["Opsi B"], "Volume beton total unsur", 1), r["sb"]["vol"])
    bandingkan("besi A", cari(wb["Opsi A"], "Besi total unsur", 1), r["sa"]["besi"], 0.5)
    bandingkan("besi B", cari(wb["Opsi B"], "Besi total unsur", 1), r["sb"]["besi"], 0.5)
    ws = wb["Reaksi"]
    for i, k in enumerate(KOLOM):
        lab = f"({idn(k[0], 0)}; {idn(k[1], 0)})"
        baris = [row for row in ws.iter_rows() if any(c.value == lab for c in row)][-1]
        v = [c.value for c in baris if c.value is not None]
        bandingkan(f"R_B {lab}", v[7], r["r_b"][k], 0.05)
        bandingkan(f"tiang A {lab}", v[8], r["n_a"][k], 0)
        bandingkan(f"tiang B {lab}", v[9], r["n_b"][k], 0)
    bandingkan("biaya langsung", cari(wb["Biaya"], "Δ biaya langsung", 1), r["biaya"]["langsung"], 0.05)
    bandingkan("biaya total", cari(wb["Biaya"], "Δ total dengan tidak langsung dan PPN", 1), r["biaya"]["total"], 0.05)
    return not pesan, "; ".join(pesan) or "semua rumus Excel cocok dengan Python"


# ------------------------------------------------------------------ ringkasan .md
def buat_md(keluar=KELUAR / "5.1 Kajian Letak Tangki.md"):
    r = hitung()
    sa, sb, bi, ru, t90, kn = r["sa"], r["sb"], r["biaya"], r["ruang"], r["t90"], r["tangki"]
    ua = {u["nama"]: u for u in r["ua"]}
    ub = {u["nama"]: u for u in r["ub"]}
    t_b = r["t_b"]
    sat = lambda u: f"{idn(u['b'], 2)} × {idn(u['h'], 2)}"   # noqa: E731
    pil = lambda dct: " / ".join(str(dct[k]) for k in KOLOM)   # noqa: E731
    teks = f"""# 5.1 Kajian Letak Tangki ({STATUS})

Disusun AI 20 Nov 2026. Data simulasi. Rincian angka di `5.1 Kajian Letak Tangki.xlsx` (`skrip/tahap5_tangki.py`, uji
`tests/test_tahap5_tangki.py`). Dasar sama untuk dua opsi: beban operasi tangki M-02 {idn(kn['berat_operasi'], 0)} kN,
isi tangki sebagai beban mati, metode balok yang sama (PyNite dengan pegas kolom + amplop gempa 4.6).

## Opsi A vs opsi B

| Hal | Opsi A (tetap, 4.6-4.7) | Opsi B (usulan) |
|---|---|---|
| Tangki | 12 × 6 × 3,0 m, x 60-72 / y 67-73 | 8 × 8 × 3,5 m, x 60-68 / y 67-75 (tinggi air 3,3 m = 211 m³) |
| Tekanan di pelat | {idn(r['info_tk']['q'], 1)} kPa | {idn(P_TANGKI / 64, 1)} kPa |
| Tepi tepat di as | 2 dari 4 (x 72 dan y 73 di tengah bentang) | 4 dari 4 (as 7, 8, F, G) |
| Pelat di bawah tangki | 250 mm satu arah + balok anak y 71 500 × 900 | {int(t_b * 1000)} mm dua arah, tanpa balok anak |
| Balok induk as 8 | {sat(ua['x 68'])} | {sat(ub['x 68'])} |
| Balok induk as 7 | {sat(ua['x 60'])} | {sat(ub['x 60'])} |
| Balok y 67 / y 75 (x 60-68) | {sat(ua['y 67 (x 60-68)'])} / {sat(ua['y 75 (x 60-68)'])} | {sat(ub['y 67 (x 60-68)'])} / {sat(ub['y 75 (x 60-68)'])} |
| Kolom (as 7, 8, 9; y 67 dan 75) | {idn(r['k_a'][(60.0, 67.0)], 2)} / {idn(r['k_a'][(68.0, 67.0)], 2)} / {idn(r['k_a'][(76.0, 67.0)], 2)} | {idn(r['k_b'][(60.0, 67.0)], 2)} (seragam, keputusan 5.6a) |
| Volume beton unsur | {idn(sa['vol'], 1)} m³ | {idn(sb['vol'], 1)} m³ ({idn(sb['vol'] - sa['vol'], 1)}) |
| Besi unsur | {idn(sa['besi'] / 1000, 1)} t | {idn(sb['besi'] / 1000, 1)} t ({idn((sb['besi'] - sa['besi']) / 1000, 1)}) |
| Tiang bor Ø800 (enam kolom) | {sum(r['n_a'].values())} | {sum(r['n_b'].values())} ({idn(bi['d_tiang'], 0)}) |
| Δ biaya langsung (B - A) | - | {idn(bi['langsung'], 1)} juta Rp |
| Δ biaya dengan BTL 12 % dan PPN 11 % | - | {idn(bi['total'], 1)} juta Rp |
| Tinggi bersih LT2 di bawah balok terdalam | {idn(ru['bersih_A'], 2)} m | {idn(ru['bersih_B'], 2)} m |
| Sisi tangki menghadap chiller (jarak 1,3 m) | 6 m | 2 m (syarat jarak bebas: belum ada di acuan, data pabrikan) |
| Puncak tangki di atas parapet | {idn(ru['puncak_A'] - ru['parapet'], 2)} m, mundur 2,0 m dari as G | {idn(ru['puncak_B'] - ru['parapet'], 2)} m, tepat di tepi utara |
| LB-2 dan pipa | tidak berubah (1,2 m dari tepi barat) | tidak berubah |

Reaksi layan per kolom (kN) dan tiang, urutan (60;67) (68;67) (76;67) (60;75) (68;75) (76;75):
A = {', '.join(idn(r['r_a'][k], 0) for k in KOLOM)}; tiang {pil(r['n_a'])}.
B = {', '.join(idn(r['r_b'][k], 0) for k in KOLOM)}; tiang {pil(r['n_b'])}.

## Cek silang T-90

| Cek | Cara 1 | Cara 2 | Selisih | Toleransi |
|---|---|---|---|---|
| (a) Σ bagian tangki ke kolom, A / B | {idn(t90['a_A'], 1)} / {idn(t90['a_B'], 1)} kN | {idn(t90['P'], 0)} kN | {idn((t90['a_A'] / t90['P'] - 1) * 100, 3)} / {idn((t90['a_B'] / t90['P'] - 1) * 100, 3)} % | 0,5 % |
| (b) Mu- balok induk x 68, A | 5.1: {idn(t90['b_Mneg_51'], 0)} kNm ({sat({'b': t90['b_ukuran_51'][0], 'h': t90['b_ukuran_51'][1]})}) | 4.6: {idn(t90['b_Mneg_46'], 0)} kNm ({sat({'b': t90['b_ukuran_46'][0], 'h': t90['b_ukuran_46'][1]})}) | {idn((t90['b_Mneg_51'] / t90['b_Mneg_46'] - 1) * 100, 1)} % | 15 %, ukuran sama |
| (b) Mu+ balok induk x 68, A | {idn(t90['b_Mpos_51'], 0)} kNm | {idn(t90['b_Mpos_46'], 0)} kNm | {idn((t90['b_Mpos_51'] / t90['b_Mpos_46'] - 1) * 100, 1)} % | 15 % |
| (c) Reaksi anak di x 68 (D total) | tangan {idn(t90['c_tangan_total'], 1)} kN | R_D 4.6 {idn(t90['c_pynite_RD'], 1)} kN | {idn((t90['c_tangan_total'] / t90['c_pynite_RD'] - 1) * 100, 3)} % | 10 % |

## Yang perlu dipilih Defsa

1. **Opsi A atau B.** Selisih biaya kecil ({idn(bi['total'], 1)} juta Rp dengan BTL dan PPN); yang menentukan: tinggi bersih LT2
   ({idn(ru['bersih_A'], 2)} m vs {idn(ru['bersih_B'], 2)} m), tangki 3,5 m di tepi utara (fasad), dan sisi tangki ke chiller.
2. Bila B: 4.5-4.7 dirancang ulang untuk pelat, balok x 60/68/y 67/y 75 dan kolom (P-M dan kolom kuat balok lemah belum
   dicek untuk balok B), serta tanya pemasok chiller soal jarak bebas.
3. Asumsi yang dipakai (dapat diubah): gempa balok B = amplop 4.6 di posisi sama (konservatif); alokasi berat sendiri ke
   kolom setengah-setengah; tiang minimum 2 per pile cap seperti 3.7.

## Keputusan Defsa 21 Nov 2026

**Opsi B dipilih:** tangki panel 8,0 × 8,0 × 3,5 m (air 3,3 m, 211 m³) di bay as 7-8 / F-G (x 60-68 / y 67-75), pelat
dua arah 350, kolom 750. Tindak lanjut: P-M dan kolom kuat-balok lemah kolom 750 di as 7/8 dicek di 5.6; desain
4.5-4.7 yang berubah ditulis ulang lokal; model 4.9 dan gambar diperbarui di 5.7-5.8; data owner M-02 (ukuran dan
letak baru) dikonfirmasi lewat surat teknis; tampak tangki di tepi utara masuk arsitektur Tahap 7.

**Tambahan 21 Nov 2026 (5.6a): kolom tangki 800 seragam.** Desain ulang di `5.6a Kolom Tangki Opsi B.xlsx` menunjukkan
kolom 750 gagal di LT3 (P-M dan kolom kuat balok lemah); Defsa memutuskan keenam kolom tangki 800 (batas bawah `kolom_b`
di `tahap5_tangki.py` 0,75 menjadi 0,80). Angka lama → baru: volume beton unsur B 73,9 → 78,1 m³ (selisih B - A -14,3 →
-10,1 m³); besi unsur B 14,7 → 15,6 t (selisih -1,8 → -0,9 t); tiang tetap (selisih -1 tiang); Δ biaya langsung
-259,2 → -234,8 juta Rp (dengan BTL dan PPN -322,3 → -291,9); reaksi enam kolom B naik 16,4 kN per kolom (berat kolom
9 m, 0,80² - 0,75²). Tindak lanjut: 5.6 diperbarui (reaksi dan stek kolom tangki).
"""
    keluar.write_text(teks, encoding="utf-8")
    return keluar


def ke_pdf(berkas=BERKAS, pdf=None):
    """Cetak semua lembar xlsx ke PDF lewat Microsoft Excel (ExportAsFixedFormat); kembalikan (ok, pesan)."""
    import subprocess
    pdf = pdf or Path(berkas).with_suffix(".pdf")
    perintah = ("$x = New-Object -ComObject Excel.Application; $x.Visible = $false; $x.DisplayAlerts = $false; "
                f"$b = $x.Workbooks.Open('{Path(berkas).resolve()}'); $b.ExportAsFixedFormat(0, '{Path(pdf).resolve()}'); "
                "$b.Close($false); $x.Quit()")
    h = subprocess.run(["powershell", "-NoProfile", "-Command", perintah], capture_output=True, text=True)
    return h.returncode == 0, h.stderr.strip()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    r = hitung()
    print({k: round(v, 2) for k, v in r["sa"].items()})
    print({k: round(v, 2) for k, v in r["sb"].items()})
    print({k: round(v, 1) for k, v in r["biaya"].items()})
    print(buat_excel())
    print(cocokkan())
    print(buat_md())
