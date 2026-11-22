"""Tahap 6 langkah 6.2: gesekan negatif (NSF, downdrag) dan bidang netral tiang bor Ø800.

DATA SIMULASI untuk studi kasus portofolio. Disusun AI atas permintaan Defsa (21 Nov 2026); draf, menunggu
persetujuan Defsa. Kunci jawaban tidak dibuka. Profil tanah, irisan, fs metode A dan Qb diimpor dari
`tahap6_tiang_tunggal` (6.1) dan `tahap3_pondasi`; penurunan urugan dari `tahap2_penurunan_urugan`.

Acuan (halaman = nomor halaman PDF di acuan/; nomor cetak dalam kurung):
- SNI 8460:2017 Pasal 9.7.2.1 hal. 204: gesekan negatif diperhitungkan sebagai beban desain, tidak dibagi FK; FK >= 2,5
  Pasal 9.2.3.1 hal. 194; likuifaksi FK 1,1 hal. 295 (seperti Tahap 3).
- FHWA GEC10 (NHI-18-024) 10.6.2 hal. 327-328 (10-47..10-48), Gambar 10-20: bidang netral = perpotongan Kurva A
  (Qb + tahanan selimut di bawah z) dan Kurva B (Q + seret kumulatif dari atas); fDN memakai cara 10.3.5.
  10.6.1 hal. 326 (10-46): seret hanya pada batas kuat struktur dan batas layan, bukan batas kuat geoteknik; kriteria
  Briaud-Tucker; ujung tiang menembus lapisan penyebab seret. 10.6.3 hal. 10-49: perpanjang tiang lebih efektif
  daripada memperbesar diameter. 10.7 hal. 332 (10-52): seret pasca-likuifaksi = 50 % selimut beta pra-gempa pada
  lapisan terlikuifaksi, tidak digabung dengan beban gempa.
- FHWA-NHI-06-089 Vol II hal. 275-276 (PDF; 9-165, 9-166) Gambar 9-68: garis Davisson dan tangen ganda (uji beban);
  9.8 (PDF 197-199): seret kelompok dari keliling blok (untuk 6.3, tidak dihitung di sini).
- Belum ada di acuan/: GEC12 (Hannigan 2016) 7.3.6.1, Fellenius (buku), Chin (1970) dan Asaoka (1978) asli.
"""
from __future__ import annotations

import math
import re
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import tahap2_penurunan_urugan as t2  # noqa: E402
import tahap2_stratigrafi as st  # noqa: E402
import tahap6_tiang_tunggal as t6  # noqa: E402

t3 = t6.t3
AKAR = t6.AKAR
KELUAR = t6.KELUAR
UJI = KELUAR / "Data Uji"
BERKAS = KELUAR / "6.2 Gesekan Negatif.xlsx"
MD = KELUAR / "6.2 Gesekan Negatif.md"
GAMBAR = KELUAR / "Gambar"
VERIFIKASI = AKAR / "VERIFIKASI.md"
REAKSI = KELUAR / "6.0 Telaah Data Tahap 6.xlsx"

LABEL = t6.LABEL
STATUS = "disetujui Defsa 21 Nov 2026"
LABEL_AI = f"DIISI AI ATAS PERMINTAAN DEFSA (21 Nov 2026), sel hijau; {STATUS}. Kunci jawaban tidak dibuka."
idn = t6.idn

D, PA, KEL = t6.D, t6.PA, math.pi * t6.D
AG = math.pi * D ** 2 / 4
Q_KERJA = 911.0                      # kN, beban kerja rencana (Tahap 3, 6.1)
BETA_GAMBUT = 0.25                   # [Asumsi Fellenius, seperti Tahap 3]
FC = 30.0                            # MPa, fc' rencana RKS [Asumsi: dari lembar Mutu Beton]
KAP_STR = 0.65 * 0.8 * 0.85 * FC * 1000 * AG   # kN, beton polos [Asumsi konservatif; tulangan di 6.7]
ZONA2 = ["SELATAN", "UTARA"]
TOL = {"excel": 0.5, "np": 0.25, "t3": 30.0, "capwap": 25.0}   # %, m, %, % ; ditetapkan sebelum membandingkan
TGL_TIANG = date(2027, 5, 3)         # tiang kerja mulai
SPL_ZONA = {"SELATAN": [1, 2, 3], "TENGAH": [4, 5, 6], "UTARA": [7, 8, 9, 10], "KAKI": [11]}
BOR_ZONA = {"SELATAN": "BH-5", "UTARA": "BH-3", "TENGAH": "BH-7", "KAKI": "BH-7"}


# ------------------------------------------------------------------ fDN dan irisan
def su_irisan(s):
    return 5.2 + 1.09 * s["z"] if s["unit"] == "U4" else s["su"]


def fdn(s, mode="A"):
    """Gesekan seret satuan (kPa) di U1-U4. A: lempung alpha su (alpha <= 1 [Asumsi]), gambut beta 0,25 sigma'v.
    T3: beta Tahap 3 (0,25 sigma'v)."""
    if s["unit"] not in ("U1", "U2", "U3", "U4"):
        return 0.0
    if s["jenis"] == "gambut" or mode == "T3":
        return BETA_GAMBUT * s["sv"]
    su = su_irisan(s)
    return min(1.0, 0.30 + 0.17 / (su / PA)) * su


def profil_f(zona, ujung=None, mode="A"):
    """Irisan dengan f1 (statis, seret = tahanan), f2d (seret pasca-likuifaksi), f2r (tahanan pasca-likuifaksi), kPa."""
    out = []
    for s in t6.irisan(zona, ujung):
        d = fdn(s, mode)
        fs = t6.fs_unit("A", s, "statis")
        f1 = d if s["unit"] in ("U1", "U2", "U3", "U4") else fs
        s = dict(s, fdn=d, fs=fs, f1=f1, f2d=0.5 * fs if s["unit"] == "U5" else f1,
                 f2r=0.0 if s["unit"] == "U5" else f1)
        out.append(s)
    return out


def bidang_netral(sl, Q, Qb, kasus=1):
    """Bidang netral dua cara. Kembalikan z (m dari tanah asli), Qn, Q + Qn, z cara tertutup, Qn tertutup, kurva."""
    kd, kr = ("f1", "f1") if kasus == 1 else ("f2d", "f2r")
    sd, sr, zb = [0.0], [0.0], [0.0]
    for s in sl:
        sd.append(sd[-1] + s[kd] * KEL * s["dz"])
        sr.append(sr[-1] + s[kr] * KEL * s["dz"])
        zb.append(zb[-1] + s["dz"])
    A = [Qb + sr[-1] - x for x in sr]
    B = [Q + x for x in sd]
    zn = zb[-1]
    qn = sd[-1]
    for i in range(1, len(zb)):
        if B[i] >= A[i]:
            fr = (A[i - 1] - B[i - 1]) / ((B[i] - B[i - 1]) - (A[i] - A[i - 1]))
            zn = zb[i - 1] + fr * (zb[i] - zb[i - 1])
            qn = sd[i - 1] + fr * (sd[i] - sd[i - 1])
            break
    # cara tertutup: Sd(z) + Sr(z) = Qb + Sr_tot - Q, z dicari dengan interpolasi pada jumlah kumulatif
    tot = [a + b for a, b in zip(sd, sr)]
    tgt = Qb + sr[-1] - Q
    zt, qt = zb[-1], sd[-1]
    for i in range(1, len(zb)):
        if tot[i] >= tgt:
            fr = (tgt - tot[i - 1]) / (tot[i] - tot[i - 1]) if tot[i] > tot[i - 1] else 0.0
            zt = zb[i - 1] + fr * (zb[i] - zb[i - 1])
            qt = sd[i - 1] + fr * (sd[i] - sd[i - 1])
            break
    return {"z": zn, "Qn": qn, "Qmaks": Q + qn, "z_tertutup": zt, "Qn_tertutup": qt, "Sd_tot": sd[-1], "Sr_tot": sr[-1],
            "zb": zb, "A": A, "B": B, "sd": sd, "sr": sr}


def elev(zona, z):
    return t3.PROFIL[zona]["elev"] - z


def qb_a(zona, ujung=None):
    return t6.hitung("A", zona, ujung)["Qb"]


def np_zona(zona, ujung=None, Q=Q_KERJA, qb_fak=1.0, mode="A"):
    sl = profil_f(zona, ujung, mode)
    qb = qb_a(zona, ujung) * qb_fak
    return {k: bidang_netral(sl, Q, qb, k) for k in (1, 2)} | {"sl": sl, "Qb": qb}


# ------------------------------------------------------------------ penurunan tanah
def baca_spl():
    import openpyxl
    ws = openpyxl.load_workbook(UJI / "Pemantauan Urugan dan PVD.xlsx", data_only=True)["Pelat Penurunan"]
    d = {}
    for r in ws.iter_rows(min_row=5, values_only=True):
        if r[2] and str(r[2]).startswith("SPL-"):
            d.setdefault(r[2], []).append((datetime.strptime(r[3], "%Y-%m-%d").date(), float(r[5]), r[7]))
    return d


def seri_kontinu(k, v):
    """Seri penurunan (tanggal, mm). SPL-05 dipasang ulang 12 Mei: nol baru disambung dengan offset = bacaan terakhir
    sebelum pasang ulang + kenaikan satu minggu sebelumnya [Asumsi]. Kembalikan seri dan keterangan."""
    s = [(a, b) for a, b, _ in v]
    ket = None
    for i, (_, _, c) in enumerate(v):
        if c and "dipasang ulang" in str(c):
            off = s[i - 1][1] + (s[i - 1][1] - s[i - 2][1])
            s = s[:i] + [(a, b + off) for a, b in s[i:]]
            ket = f"{k}: pelat dipasang ulang {v[i][0]}, offset {off:.0f} mm [Asumsi]; pasangan lintas penyambungan dibuang"
            s = [(a, b, i) for (a, b) in s]   # tandai indeks awal segmen
            return s, ket, i
    return [(a, b) for a, b in s], ket, None


def asaoka(seri, sambung=None):
    """Asaoka, selang 7 hari (titik mingguan sejak 31 Mar 2027). Kembalikan b0, b1, s_inf (mm), n."""
    t0 = date(2027, 3, 31)
    pts = [(x[0], x[1]) for x in seri if x[0] >= t0 and (x[0] - t0).days % 7 == 0]
    idx = {x[0]: i for i, x in enumerate(seri)}
    xs, ys = [], []
    for (a0, b0), (a1, b1) in zip(pts[:-1], pts[1:]):
        if sambung is not None and idx[a0] < sambung <= idx[a1]:
            continue
        xs.append(b0)
        ys.append(b1)
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    b1 = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    b0 = my - b1 * mx
    return {"b0": b0, "b1": b1, "s_inf": b0 / (1 - b1), "n": n, "akhir": pts[-1][1]}


def s_pada(seri, tgl):
    for (a0, b0, *_), (a1, b1, *_) in zip(seri[:-1], seri[1:]):
        if a0 <= tgl <= a1:
            return b0 + (b1 - b0) * (tgl - a0).days / max(1, (a1 - a0).days)
    return seri[-1][1]


def titik(nama):
    return next(t for t in st.semua_titik() if t["nama"] == nama)


def prediksi(nama, tebal=None):
    """hitung_titik Tahap 2; tebal urugan tertentu (m) bila diberikan, jika tidak sampai +11,50."""
    t = titik(nama)
    lama = t2.ELEV_RENCANA
    try:
        if tebal is not None:
            t2.ELEV_RENCANA = t["elev"] + tebal
        return t2.hitung_titik(t)
    finally:
        t2.ELEV_RENCANA = lama


def penurunan_sisa():
    """Asaoka per pelat, kalibrasi per zona, sisa setelah tiang (3 Mei 2027) dan profil terhadap kedalaman."""
    spl = baca_spl()
    pel, temuan = {}, []
    for zk, ids in SPL_ZONA.items():
        pr = prediksi(BOR_ZONA[zk], 0.6 if zk == "KAKI" else 1.05)   # kaki urugan hanya ±0,6 m (lembar Titik)
        for i in ids:
            k = f"SPL-{i:02d}"
            seri, ket, sambung = seri_kontinu(k, spl[k])
            if ket:
                temuan.append(ket)
            a = asaoka(seri, sambung)
            s3 = s_pada(seri, TGL_TIANG)
            pel[k] = {"zona": zk, **a, "s_3mei": s3, "primer_pred": pr["primer"] * 1000, "rasio": a["s_inf"] / (pr["primer"] * 1000)}
    out = {"pelat": pel, "temuan": temuan, "zona": {}}
    for z in ZONA2 + ["TENGAH"]:
        ids = [f"SPL-{i:02d}" for i in SPL_ZONA[z]]
        k = sum(pel[i]["rasio"] for i in ids) / len(ids)
        s3 = sum(pel[i]["s_3mei"] for i in ids) / len(ids)
        sinf = sum(pel[i]["s_inf"] for i in ids) / len(ids)
        fin = prediksi(BOR_ZONA[z])
        pu = {u: v * 1000 * k for u, v in fin["per_unit"].items()}
        s_akhir = sum(pu.values()) + fin["sekunder"] * 1000
        sisa = max(0.0, s_akhir - s3)
        out["zona"][z] = {"k": k, "s_inf_1_05": sinf, "s_3mei": s3, "primer_final": sum(pu.values()), "sek": fin["sekunder"] * 1000,
                          "s_akhir": s_akhir, "sisa": sisa, "per_unit": pu, "urug": fin["urug"], "ids": ids,
                          "bor": BOR_ZONA[z]}
    return out


def profil_sisa(zona, ps):
    """Penurunan sisa tanah (mm) sebagai fungsi kedalaman z: tiap unit mampat dibagi seragam [Asumsi], sisa dibagi
    sebanding dengan penurunan akhir terkalibrasi per unit [Asumsi]. Kembalikan fungsi s(z)."""
    zz = ps["zona"][zona]
    tot = sum(zz["per_unit"].values())
    batas, atas = {}, 0.0
    for u, bawah, *_ in t3.PROFIL[zona]["lapisan"]:
        batas[u] = (atas, bawah)
        atas = bawah
    sisa_u = {u: v / tot * zz["sisa"] for u, v in zz["per_unit"].items() if u in batas}

    def s(z):
        tt = 0.0
        for u, v in sisa_u.items():
            a, b = batas[u]
            tt += v * max(0.0, min(1.0, (b - max(z, a)) / (b - a)))
        return tt
    return s


# ------------------------------------------------------------------ telaah data uji
def baca_kurva():
    import openpyxl
    wb = openpyxl.load_workbook(UJI / "Uji Beban Statis Tiang.xlsx", data_only=True)
    rg = {r[2]: r for r in wb["Ringkasan"].iter_rows(min_row=1, values_only=True) if r[2] and str(r[2]).startswith("TP-")}
    out = {}
    for tp in ("TP-1", "TP-2", "TP-3", "TP-4"):
        ws = wb[f"Kurva {tp}"]
        rows = [r for r in ws.iter_rows(min_row=5, values_only=True) if r[3] is not None and r[2] and str(r[2])[:2] == "20"]
        grup, prev = [], None
        for r in rows:
            if prev is not None and r[3] == prev:
                grup[-1].append(r)
            else:
                grup.append([r])
            prev = r[3]
        mx, pts = 0, []
        for g in grup:
            pct = g[0][3]
            if pct > mx:
                pts.append((pct, sum(x[4] for x in g[-3:]) / len(g[-3:]), g[-1][11]))
                mx = pct
        rr = rg[tp]
        out[tp] = {"pts": pts, "L": rr[9], "tanah": rr[6], "kepala": rr[7], "zona": rr[5].upper(), "s200": rr[14], "sisa": rr[15]}
    return out


def baca_regangan():
    import openpyxl
    ws = openpyxl.load_workbook(UJI / "Uji Beban Statis Tiang.xlsx", data_only=True)["Regangan"]
    d = {}
    for r in ws.iter_rows(min_row=5, values_only=True):
        if r[2] and str(r[2]).startswith("TP-"):
            d.setdefault((r[2], r[3]), []).append({"P": r[4], "lv": r[5], "elev": r[6], "A": r[7], "B": r[8]})
    return d


def gaya_level(lev):
    """Regangan rata-rata per level; bila A dan B berselisih > 40 % dipilih sensor yang lebih dekat ke rata-rata level
    tetangga (sensor rusak). Kembalikan daftar (elev, eps, catatan)."""
    avg = [(x["A"] + x["B"]) / 2 for x in lev]
    out = []
    for i, x in enumerate(lev):
        cat = ""
        e = avg[i]
        if abs(x["A"] - x["B"]) / max(x["A"], x["B"], 1e-9) > 0.4 and 0 < i < len(lev) - 1:
            m = (avg[i - 1] + avg[i + 1]) / 2
            e = x["A"] if abs(x["A"] - m) < abs(x["B"] - m) else x["B"]
            cat = f"sensor {'B' if e == x['A'] else 'A'} diabaikan (selisih > 40 %)"
        out.append((x["elev"], e, cat))
    return out


def model_uji(zona, tanah, ujung_elev=-27.6):
    """Irisan kondisi uji (tanpa urugan di sekitar tiang): fdn di U1-U4 sebagai batas atas, fs metode A di U5-U7."""
    return profil_f(zona, tanah - ujung_elev)


def qult_uji(zona, tanah, ujung_elev=-27.6):
    sl = model_uji(zona, tanah, ujung_elev)
    qs = sum(s["f1"] * KEL * s["dz"] for s in sl)
    qb = qb_a(zona, tanah - ujung_elev)
    return {"Qs": qs, "Qb": qb, "Qult": qs + qb}


def f_model_antar(sl, z1, z2):
    sel = [s for s in sl if z1 <= s["z"] < z2]
    return sum(s["f1"] * s["dz"] for s in sel) / sum(s["dz"] for s in sel) if sel else 0.0


def telaah_uji():
    kv, rg = baca_kurva(), baca_regangan()
    hasil = {"kurva": {}, "gaya": {}, "capwap": []}
    ea200 = {}
    for tp in ("TP-1", "TP-3"):
        lev = rg[(tp, 200)]
        ea200[tp] = lev[0]["P"] / ((lev[0]["A"] + lev[0]["B"]) / 2 * 1e-6)
    ea_rata = sum(ea200.values()) / 2
    for tp, k in kv.items():
        ea = ea200.get(tp, ea_rata)
        pts = k["pts"]
        s_el = 1822 * k["L"] / ea * 1000
        dav = s_el + 4.0 + D * 1000 / 120
        # Chin: s/P = C1 s + C2 -> Qult = 1/C1 ; regresi s/P terhadap s
        sx = [p[2] for p in pts if p[0] >= 100]
        sy = [p[2] / p[1] for p in pts if p[0] >= 100]
        mxs, mys = sum(sx) / len(sx), sum(sy) / len(sy)
        c1 = sum((a - mxs) * (b - mys) for a, b in zip(sx, sy)) / sum((a - mxs) ** 2 for a in sx)
        s100 = next(p[2] for p in pts if p[0] == 100)
        hasil["kurva"][tp] = {**k, "ea": ea, "s_el": s_el, "davisson": dav, "s200_ukur": next(p[2] for p in pts if p[0] == 200),
                              "s100": s100, "kaku100": 911 / s100, "chin": 1 / c1 if c1 > 0 else None,
                              "ea_sendiri": tp in ea200}
    for tp in ("TP-1", "TP-3"):
        k = kv[tp]
        zona = k["zona"]
        sl = model_uji(zona, k["tanah"])
        for pct in (100, 200):
            lev = rg[(tp, pct)]
            P = lev[0]["P"]
            ea = P / ((lev[0]["A"] + lev[0]["B"]) / 2 * 1e-6)
            gl = gaya_level(lev)
            rows = []
            for (e1, x1, c1), (e2, x2, c2) in zip(gl[:-1], gl[1:]):
                z1, z2 = k["tanah"] - e1, k["tanah"] - e2
                fs = (x1 - x2) * 1e-6 * ea / (KEL * (z2 - z1))
                rows.append({"z1": z1, "z2": z2, "F1": x1 * 1e-6 * ea, "F2": x2 * 1e-6 * ea, "fs": fs,
                             "f_model": f_model_antar(sl, z1, z2), "cat": (c1 + " " + c2).strip()})
            hasil["gaya"][(tp, pct)] = {"P": P, "ea": ea, "rows": rows, "Qb_ukur": gl[-1][1] * 1e-6 * ea}
    pda = baca_pda()
    ru_ok = []
    for r in pda:
        zona = r["zona"]
        tanah = k_tanah(zona, r["tiang"], kv)
        q = qult_uji(zona, tanah)
        r.update({"Qult_A": q["Qult"], "Qs_A": q["Qs"], "Qb_A": q["Qb"], "rasio": r["Ru"] / q["Qult"]})
        if r["tiang"] != "T218":
            ru_ok.append(r)
    hasil["capwap"] = pda
    hasil["rasio_rata"] = sum(r["rasio"] for r in ru_ok) / len(ru_ok)
    hasil["Ru_rata"] = sum(r["Ru"] for r in ru_ok) / len(ru_ok)
    hasil["Qult_A_rata"] = sum(r["Qult_A"] for r in ru_ok) / len(ru_ok)
    return hasil


def k_tanah(zona, tiang, kv):
    return kv[tiang]["tanah"] if tiang in kv else t3.PROFIL[zona]["elev"]


def baca_pda():
    import openpyxl
    ws = openpyxl.load_workbook(UJI / "PDA dan Integritas Tiang.xlsx", data_only=True)["PDA CAPWAP"]
    out = []
    for r in ws.iter_rows(min_row=5, values_only=True):
        if r[2] and re.match(r"T(P-)?\d", str(r[2])):
            z = {"TP-1": "UTARA", "TP-3": "SELATAN"}.get(r[2]) or t3.zona(r[3], r[4])
            out.append({"tiang": r[2], "x": r[3], "y": r[4], "zona": z, "umur": r[6], "set": r[9], "dmax": r[10],
                        "Ru": r[12], "Rs": r[13], "Rb": r[14]})
    return out


# ------------------------------------------------------------------ izin akhir dan panjang
def q_maks_zona():
    """Pmax layan per tiang = Pmax kelompok / jumlah tiang di cap Tahap 3 (6.0, lembar Reaksi), maksimum per zona."""
    import openpyxl
    ws = openpyxl.load_workbook(REAKSI, data_only=True)["Reaksi"]
    out = {}
    for r in ws.iter_rows(min_row=5, values_only=True):
        if isinstance(r[2], int) and r[8] and r[11]:
            m = re.search(r"(\d+)T", str(r[11]))
            if not m:
                continue
            z = t3.zona(r[4], r[5])
            v = r[8] / int(m.group(1))
            if v > out.get(z, (0,))[0]:
                out[z] = (v, r[3])
    return out


def izin_sni(zona, ujung=None, Q=Q_KERJA, qb_fak=1.0):
    n = np_zona(zona, ujung, Q, qb_fak)
    a = t6.hitung("A", zona, ujung)
    b = t6.hitung("A", zona, ujung, u5_statis=False)
    # Qn hanya dari lapisan yang menurun (seperti Tahap 3); Qn bidang netral memuat gesekan U5/U6 yang sudah ada di Qult
    # (hitungan ganda), jadi hanya dipakai untuk cek struktur dan layan (GEC10). Keputusan Defsa 21 Nov 2026.
    pf = profil_f(zona, ujung)
    qn1 = sum(x["fdn"] * KEL * x["dz"] for x in pf)
    qn2 = sum(x["f2d"] * KEL * x["dz"] for x in pf if x["unit"] in ("U1", "U2", "U3", "U4", "U5"))
    i1 = a["Qult_st"] / t6.FK - qn1
    i2 = b["Qult_st"] / t6.FK_GM - qn2
    return {"izin": min(i1, i2), "izin_st": i1, "izin_lik": i2, "Qult_st": a["Qult_st"], "Qult_tanpaU5": b["Qult_st"],
            "Qn1": qn1, "Qn2": qn2, "Qn1_np": n[1]["Qn"], "Qn2_np": n[2]["Qn"], "z1": n[1]["z"], "z2": n[2]["z"], "n": n}


def izin_gec10(zona, ps, ujung=None, Q=Q_KERJA):
    n = np_zona(zona, ujung, Q)
    a = t6.hitung("A", zona, ujung)
    s = profil_sisa(zona, ps)
    out = {"geo": a["Qult_st"] / t6.FK, "str_maks": Q + n[1]["Qn"], "kap_str": KAP_STR,
           "Q_izin_str": KAP_STR - n[1]["Qn"], "s_np1": s(n[1]["z"]), "s_np2": s(n[2]["z"]),
           "str_maks2": Q + n[2]["Qn"]}
    out["izin"] = min(out["geo"], out["Q_izin_str"])
    return out


def panjang_min(zona, target):
    top = t6.u7_atas(zona)
    dasar_u5 = next(lp[1] for lp in t3.PROFIL[zona]["lapisan"] if lp[0] == "U5")
    e = 0.5
    while e <= 14.0:
        r = izin_sni(zona, top + e, Q=target)
        if r["izin"] >= target and r["z1"] >= dasar_u5 and r["z2"] >= dasar_u5:
            return e, top + e, r
        e += 0.5
    return None, None, None


def panjang_min_gec(zona, target):
    """Benam minimum (GEC10): Qult/2,5 >= target, beban struktur Q + Qn <= kapasitas beton, bidang netral di bawah U5."""
    top = t6.u7_atas(zona)
    dasar_u5 = next(lp[1] for lp in t3.PROFIL[zona]["lapisan"] if lp[0] == "U5")
    e = 0.5
    while e <= 14.0:
        n = np_zona(zona, top + e, target)
        a = t6.hitung("A", zona, top + e)
        if a["Qult_st"] / t6.FK >= target and target + n[1]["Qn"] <= KAP_STR and n[1]["z"] >= dasar_u5 and n[2]["z"] >= dasar_u5:
            return e, top + e, n
        e += 0.5
    return None, None, None


def nsf_u1u4_beta(zona):
    """Gesekan negatif U1-U4 dengan beta Tahap 3 (penuh sampai dasar U4): harus sama dengan t3.kapasitas NSF_statis."""
    return sum(fdn(s, "T3") * KEL * s["dz"] for s in t6.irisan(zona))


def panjang_usul(zona, benam):
    return t6.panjang_usulan(zona, benam)


def semua():
    ps = penurunan_sisa()
    n = {z: np_zona(z) for z in ZONA2}
    n50 = {z: np_zona(z, qb_fak=0.5) for z in ZONA2}
    nt3 = {z: np_zona(z, mode="T3") for z in ZONA2}
    return {"ps": ps, "np": n, "np50": n50, "npT3": nt3, "izin": {z: izin_sni(z) for z in ZONA2},
            "gec": {z: izin_gec10(z, ps) for z in ZONA2}, "qmaks": q_maks_zona(), "uji": telaah_uji()}


def panjang_zona(h):
    out = {}
    for z in ZONA2:
        tgt = max(Q_KERJA, h["qmaks"].get(z, (0,))[0])
        out[z] = {"target": tgt, "sni": panjang_min(z, Q_KERJA), "sni_qmaks": panjang_min(z, tgt),
                  "gec": panjang_min_gec(z, Q_KERJA), "gec_qmaks": panjang_min_gec(z, tgt),
                  "L_ada": t6.hitung("A", z)["panjang"]}
    return out


# ------------------------------------------------------------------ grafik
def grafik(h):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    GAMBAR.mkdir(parents=True, exist_ok=True)
    out = []
    for z in ZONA2:
        fig, ax = plt.subplots(1, 2, figsize=(10, 6), sharey=True)
        for a, k, jd in zip(ax, (1, 2), ("Kasus 1: urugan + PVD, statis jangka panjang", "Kasus 2: pasca-likuifaksi U5")):
            r = h["np"][z][k]
            ez = [elev(z, x) for x in r["zb"]]
            a.plot(r["A"], ez, label="Kurva A: Qb + selimut di bawah z", color="#c0392b")
            a.plot(r["B"], ez, label="Kurva B: Q + seret dari atas", color="#1f4e9c")
            a.axhline(elev(z, r["z"]), color="gray", ls="--", lw=0.8)
            a.annotate(f"bidang netral {elev(z, r['z']):.2f} m\nQ + Qn = {r['Qmaks']:.0f} kN", (r["Qmaks"], elev(z, r["z"])),
                       xytext=(10, 15), textcoords="offset points", fontsize=8)
            a.set_title(jd, fontsize=10)
            a.set_xlabel("Beban aksial (kN)")
            a.grid(alpha=0.3)
            a.legend(fontsize=7, loc="lower right")
        ax[0].set_ylabel("Elevasi (m)")
        fig.suptitle(f"6.2 Bidang netral tiang bor Ø800, zona {z.lower()} (DATA SIMULASI; {STATUS})", fontsize=10)
        fig.tight_layout()
        p = GAMBAR / f"6.2 Kurva A B {z.capitalize()}.png"
        fig.savefig(p, dpi=130)
        plt.close(fig)
        out.append(p)
    return out


# ------------------------------------------------------------------ Excel
ACUAN = [
    ("SNI 8460:2017 Pasal 9.7.2.1 (gesekan negatif sebagai beban, tidak dibagi FK), 9.2.3.1 (FK 2,5), FK likuifaksi 1,1",
     "ada", "acuan/privat; hal. 204, 194, 295 (PDF)"),
    ("FHWA GEC10 10.6.1-10.6.3, 10.7 (bidang netral, batas layan dan struktur, Briaud-Tucker, pasca-likuifaksi 50 %)", "ada",
     "acuan/pustaka/FHWA-NHI-18-024-GEC10-Drilled-Shafts.pdf; hal. 326-328, 10-49, 332 (PDF)"),
    ("FHWA-NHI-06-089 Vol II, Gambar 9-68 (Davisson, tangen ganda), 9.8 (seret kelompok)", "ada",
     "acuan/pustaka/FHWA-NHI-06-089-Soils-and-Foundations-Vol-II.pdf; hal. 275-276 (PDF), 197-199 (kelompok, untuk 6.3)"),
    ("GEC12 (Hannigan 2016) 7.3.6.1, langkah rinci downdrag tiang", "belum ada", "Tidak dikutip halamannya."),
    ("Fellenius, buku dasar (bidang netral, gesekan negatif)", "belum ada", "Hanya lewat ringkasan GEC10."),
    ("Chin (1970) dan Asaoka (1978) asli", "belum ada",
     "[Literatur, belum ada di acuan/]: dipakai untuk ekstrapolasi uji beban dan penurunan akhir pelat; hasil informasi."),
]

KEPUTUSAN = [
    ("Aturan izin (disetujui Defsa 21 Nov 2026)", "Izin akhir = min(SNI 8460 hal. 204: Qult/2,5 - Qn lapisan menurun U1-U4; "
     "Qult tanpa U5/1,1 - Qn U1-U4 + 50 % U5; GEC10 geoteknik Qult/2,5). Qn bidang netral memuat gesekan U5/U6 yang sudah ada "
     "di Qult (hitungan ganda bila dikurangkan), jadi dipakai hanya untuk cek struktur (Q + Qn) dan layan (penurunan di bidang netral)."),
    ("Layan utara", "Penurunan tiang = penurunan tanah sisa di bidang netral: utara ±20 mm > δ 16 mm Tahap 5, selatan ±13 mm. "
     "Pilihan (6.6): pra-beban urugan + PVD selesai sebelum tiang kerja, perpanjang tiang (GEC10 §10.6.3), atau terima dan cek ulang."),
    ("Uji beban", "Uji 200 % tanpa runtuh hanya membuktikan FK 2,0 pada 911 kN; FK 2,5 perlu uji ≥ 2.278 kN (6.8)."),
    ("fDN di U1-U4", "alpha su dibatasi alpha <= 1 [Asumsi] (Pers. 10-18 memberi alpha > 1 untuk su kecil); gambut beta 0,25 "
     "[Asumsi Fellenius]. Pembanding beta Tahap 3 memberi hasil serupa."),
    ("Seret sampai bidang netral", "Seret di U5 dan U6 di atas bidang netral dihitung penuh (tahanan satuan 6.1) karena penurunan "
     "tanah di bidang netral 9-20 mm [Asumsi: cukup untuk memobilisasi selimut]. Tidak ada kurva t-z di acuan/."),
    ("Qb termobilisasi", "Qb penuh (866 kN) di kasus utama; 50 % sebagai kepekaan [Asumsi]. Uji beban: Qb terukur 70-260 kN pada 100-200 % "
     "(penurunan 1,8-4,5 mm)."),
    ("Beban kerja Q", "911 kN (Tahap 3) dan Pmax layan per tiang dari 6.0 (hasil terbesar per zona, lihat Izin Akhir)."),
    ("Kapasitas struktur", f"0,85 f'c Ag x 0,65 x 0,8, f'c 30 MPa [Asumsi konservatif, beton polos] = {KAP_STR:,.0f} kN; tulangan di 6.7."),
    ("Panjang tiang", "Usulan, bukan keputusan; 38,45 m tetap sampai Defsa memutuskan."),
    ("Sisa penurunan", "Kalibrasi satu faktor per zona dari Asaoka (selang 7 hari); sekunder 50 tahun tidak dikalibrasi; sisa dibagi "
     "sebanding penurunan akhir tiap unit [Asumsi]; SPL-05 disambung dengan offset 239 mm [Asumsi]."),
]


def _lembar_irisan(wb, nomor, zona, h):
    from format_dokumen import AI, Lembar
    n = h["np"][zona]
    sl = n["sl"]
    nama = f"Irisan {zona.capitalize()}"
    lebar = [7, 8, 7, 7, 9, 9, 8, 9, 9, 9, 11, 11, 11, 11, 11, 8, 9, 9, 11, 11, 11, 11, 11, 11, 8]
    lb = Lembar(wb.create_sheet(nama), nomor, f"Bidang netral zona {zona.lower()}: irisan 0,25 m", lebar)
    lb.catatan(LABEL + " " + LABEL_AI)
    lb.catatan("Irisan 0,25 m dari muka tanah asli (z = titik tengah). fDN (U1-U4): lempung alpha su (alpha <= 1, su U4 = 5,2 + 1,09 z), "
               "gambut 0,25 sigma'v [Asumsi]. fs 6.1 (U5-U7): metode A, nilai dari tahap6_tiang_tunggal.fs_unit. Kasus 1: seret = "
               "tahanan (f1). Kasus 2 (pasca-likuifaksi, GEC10 hal. 10-52): seret U5 = 50 % fs beta, tahanan U5 = 0. Kurva A = Qb + "
               "tahanan di bawah z; Kurva B = Q + seret kumulatif dari atas; bidang netral di perpotongan (interpolasi linear dalam irisan).")
    lb.kosong()
    lb.bagian("A", "Parameter")
    _, p1, _ = lb.tabel(["D (m)", "Q kerja (kN)", "Qb 6.1 (kN)", "Faktor Qb", "Qb dipakai (kN)", "Muka tanah asli (m)", "Ujung z (m)"],
                        [[D, Q_KERJA, round(qb_a(zona), 3), 1.0, None, t3.PROFIL[zona]["elev"], round(t3.PROFIL[zona]["ujung"], 2)]],
                        rata=list("ccccccc"), fmt=["0.00", "#,##0.0", "#,##0.0", "0.00", "#,##0.0", "0.00", "0.00"], fill=AI, beku=False)
    Q, QBD, DC = f"$D${p1}", f"$G${p1}", f"$C${p1}"
    lb.ws[f"G{p1}"].value = f"=E{p1}*F{p1}"
    lb.kosong()
    lb.bagian("B", "Bidang netral (rumus dari irisan di bawah)")
    hr0 = lb.baris
    lb.tabel(["Kasus", "Irisan ke-", "Fraksi", "z bidang netral (m)", "Elevasi (m)", "Qn (kN)", "Q + Qn (kN)", "Seret total (kN)", "Tahanan total (kN)"],
             [[f"Kasus {k}"] for k in (1, 2)], rata=list("lcccccccc"),
             fmt=[None, "0", "0.000", "0.00", "0.00", "#,##0.0", "#,##0.0", "#,##0.0", "#,##0.0"], fill=AI, beku=False)
    lb.kosong()
    lb.bagian("C", "Irisan 0,25 m")
    sl1 = lb.baris + 1
    sl2 = sl1 + len(sl) - 1
    c = lb.kol

    def rng(i):
        return f"${c(i)}${sl1}:${c(i)}${sl2}"
    rows = []
    for i, s in enumerate(sl):
        r = sl1 + i
        pv = r - 1
        u14 = s["unit"] in ("U1", "U2", "U3", "U4")
        su = su_irisan(s)
        rows.append([i + 1, round(s["z"], 3), s["dz"], s["unit"], s["jenis"], round(s["sv"], 3), round(su, 2) if su else None,
                     round(s["fdn"], 4), round(s["fs"], 4), f"={c(7 if u14 else 8)}{r}",
                     f"={c(9)}{r}*PI()*{DC}*{c(2)}{r}" + (f"+{c(10)}{pv}" if i else ""),
                     f"={QBD}+${c(10)}${sl2}-{c(10)}{r}", f"={Q}+{c(10)}{r}",
                     f"={QBD}+${c(10)}${sl2}" if i == 0 else f"={c(11)}{pv}", f"={Q}" if i == 0 else f"={c(12)}{pv}",
                     f"=IF({c(12)}{r}>={c(11)}{r},1,0)",
                     f'=IF({c(3)}{r}="U5",0.5*{c(8)}{r},{c(9)}{r})', f'=IF({c(3)}{r}="U5",0,{c(9)}{r})',
                     f"={c(16)}{r}*PI()*{DC}*{c(2)}{r}" + (f"+{c(18)}{pv}" if i else ""),
                     f"={c(17)}{r}*PI()*{DC}*{c(2)}{r}" + (f"+{c(19)}{pv}" if i else ""),
                     f"={QBD}+${c(19)}${sl2}-{c(19)}{r}", f"={Q}+{c(18)}{r}",
                     f"={QBD}+${c(19)}${sl2}" if i == 0 else f"={c(20)}{pv}", f"={Q}" if i == 0 else f"={c(21)}{pv}",
                     f"=IF({c(21)}{r}>={c(20)}{r},1,0)"])
    lb.tabel(["No", "z (m)", "dz (m)", "Unit", "Jenis", "sigma'v (kPa)", "su (kPa)", "fDN (kPa)", "fs 6.1 (kPa)", "f1 (kPa)", "Seret kum. 1 (kN)",
              "Kurva A1 (kN)", "Kurva B1 (kN)", "A1 atas", "B1 atas", "Lewat 1", "f2 seret (kPa)", "f2 tahanan (kPa)", "Seret kum. 2 (kN)",
              "Tahanan kum. 2 (kN)", "Kurva A2 (kN)", "Kurva B2 (kN)", "A2 atas", "B2 atas", "Lewat 2"], rows,
             rata=["c"] * 25, fmt=[None, "0.000", "0.00", None, None, "0.0", "0.0", "0.00", "0.00", "0.00", "#,##0.0", "#,##0.0", "#,##0.0",
                                   "#,##0.0", "#,##0.0", "0", "0.00", "0.00", "#,##0.0", "#,##0.0", "#,##0.0", "#,##0.0", "#,##0.0",
                                   "#,##0.0", "0"], beku=False,
             fill_kolom={i: AI for i in range(7, 25)})
    ws = lb.ws
    ads = {}
    for k, (hr, col) in enumerate(((hr0 + 1, (15, 11, 12, 13, 14, 10, 10)), (hr0 + 2, (24, 20, 21, 22, 23, 18, 19))), 1):
        flag, A, B, At, Bt, sdc, src = col
        ws[f"D{hr}"] = f"=MATCH(1,{rng(flag)},0)"
        ws[f"E{hr}"] = (f"=(INDEX({rng(At)},D{hr})-INDEX({rng(Bt)},D{hr}))/((INDEX({rng(B)},D{hr})-INDEX({rng(Bt)},D{hr}))"
                        f"-(INDEX({rng(A)},D{hr})-INDEX({rng(At)},D{hr})))")
        ws[f"F{hr}"] = f"=INDEX({rng(1)},D{hr})-INDEX({rng(2)},D{hr})/2+E{hr}*INDEX({rng(2)},D{hr})"
        ws[f"G{hr}"] = f"=$H${p1}-F{hr}"
        ws[f"H{hr}"] = f"=INDEX({rng(Bt)},D{hr})+E{hr}*(INDEX({rng(B)},D{hr})-INDEX({rng(Bt)},D{hr}))-{Q}"
        ws[f"I{hr}"] = f"={Q}+H{hr}"
        ws[f"J{hr}"] = f"={c(sdc)}{sl2}"
        ws[f"K{hr}"] = f"={c(src)}{sl2}"
        q = f"'{nama}'!"
        ads[k] = {"z": f"{q}F{hr}", "elev": f"{q}G{hr}", "Qn": f"{q}H{hr}", "Qmaks": f"{q}I{hr}"}
    return ads


def buat_excel(keluar=BERKAS, h=None, pz=None):
    import openpyxl
    from format_dokumen import AI, Lembar, set_font_bawaan
    h = h or semua()
    pz = pz or panjang_zona(h)
    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)
    ket = LABEL + " " + LABEL_AI
    ps, u = h["ps"], h["uji"]
    lr = Lembar(wb.create_sheet("Ringkasan"), 1, "Gesekan negatif dan bidang netral tiang bor Ø800",
                [20, 8, 12, 12, 12, 12, 12, 13, 13, 13, 13])
    lt = Lembar(wb.create_sheet("Telaah Data Uji"), 2, "Telaah data uji beban, regangan, PDA", [10, 10, 11, 11, 11, 11, 11, 11, 11, 11, 11, 30])
    lp = Lembar(wb.create_sheet("Penurunan Sisa"), 3, "Sisa penurunan tanah setelah PVD (Asaoka)", [12, 10, 10, 11, 11, 11, 11, 11, 11, 11])
    ad = {z: _lembar_irisan(wb, 4 + i, z, h) for i, z in enumerate(ZONA2)}
    lq = Lembar(wb.create_sheet("Pasca-Likuifaksi"), 6, "Kasus 2: seret pasca-likuifaksi U5", [22, 12, 12, 12, 12, 12, 12, 12])
    li = Lembar(wb.create_sheet("Izin Akhir"), 7, "Izin akhir per zona", [52, 16, 80])
    la = Lembar(wb.create_sheet("Acuan"), 8, "Acuan", [60, 11, 70])
    lk = Lembar(wb.create_sheet("Keputusan"), 9, "Hal yang perlu diputuskan Defsa", [24, 110])

    # ---- Ringkasan
    lr.catatan(f"STATUS: {STATUS}. " + ket)
    lr.catatan("Selatan dan Utara: bidang netral dari rumus Excel hidup di lembar irisan; kolom lain nilai dari skrip "
               "`tahap6_nsf.py`. Elevasi dari muka tanah asli zona; kepala tiang +10,85.")
    lr.kosong()
    lr.bagian("A", "Bidang netral dan seret (Q kerja 911 kN)")
    rows, ring = [], {}
    r0 = lr.baris
    for z in ZONA2:
        for k in (1, 2):
            ring[(z, k)] = r0 + 1 + len(rows)
            n = h["np"][z][k]
            a = ad[z][k]
            rows.append([z.capitalize(), k, f"={a['z']}", f"={a['elev']}", f"={a['Qn']}", f"={a['Qmaks']}",
                         round(n["z_tertutup"], 3), round(h["np50"][z][k]["Qn"], 1), round(h["npT3"][z][k]["Qn"], 1),
                         round(profil_sisa(z, ps)(n["z"]), 2),
                         round(t3.kapasitas("BOR-800", profil=z)["NSF_statis" if k == 1 else "NSF_lik"], 1)])
    lr.tabel(["Zona", "Kasus", "z bidang netral (m)", "Elevasi (m)", "Qn (kN)", "Q + Qn (kN)", "z cara tertutup (m)", "Qn dengan Qb 50 % (kN)",
              "Qn dengan beta T3 (kN)", "Penurunan tanah di bidang netral (mm)", "NSF Tahap 3 (kN)"], rows, rata=list("lc") + ["c"] * 9,
             fmt=[None, "0", "0.00", "0.00", "#,##0.0", "#,##0.0", "0.00", "#,##0.0", "#,##0.0", "0.0", "#,##0.0"],
             fill_kolom={i: AI for i in range(2, 11)}, beku=True)
    lr.kosong()
    lr.bagian("B", "Temuan utama")
    zs, zu = h["np"]["SELATAN"], h["np"]["UTARA"]
    iz = h["izin"]
    for t in temuan_teks(h, pz):
        lr.catatan(t)

    # ---- Telaah Data Uji
    lt.catatan(ket)
    lt.kosong()
    lt.bagian("A", "Uji beban statis: beban-penurunan, kekakuan, Davisson (PL/AE + 4 mm + D/120), Chin")
    rows = []
    for tp, k in u["kurva"].items():
        rows.append([tp, k["zona"].capitalize(), k["L"], k["s100"], k["s200_ukur"], k["sisa"], round(k["kaku100"], 0), round(k["ea"] / 1e6, 2),
                     round(k["s_el"], 2), round(k["davisson"], 2), round(k["chin"], 0) if k["chin"] else None,
                     "Davisson tidak terlampaui: Qult > 1.822 kN" + ("" if k["ea_sendiri"] else "; EA rata-rata TP-1/TP-3")])
    lt.tabel(["Tiang", "Zona", "Panjang (m)", "s 100 % (mm)", "s 200 % (mm)", "s sisa (mm)", "Kekakuan 100 % (kN/mm)", "EA (MN)", "PL/AE (mm)",
              "Davisson pada 1.822 kN (mm)", "Chin Qult (kN)", "Kesimpulan"], rows, rata=list("lc") + ["c"] * 9 + ["l"],
             fmt=[None, None, "0.00", "0.00", "0.00", "0.00", "0", "0.00", "0.00", "0.00", "#,##0", None], fill=AI, beku=False)
    lt.kosong()
    lt.bagian("B", "Regangan: gaya aksial dan gesekan selimut terukur per interval (TP-1, TP-3; EA = P kepala / regangan SG-1 per tahap)")
    rows = []
    for (tp, pct), g in u["gaya"].items():
        for r in g["rows"]:
            rows.append([tp, pct, round(r["z1"], 2), round(r["z2"], 2), round(r["F1"], 0), round(r["F2"], 0), round(r["fs"], 1),
                         round(r["f_model"], 1), round(r["fs"] / r["f_model"], 2) if r["f_model"] else None, r["cat"] or None])
    lt.tabel(["Tiang", "Beban (%)", "z atas (m)", "z bawah (m)", "F atas (kN)", "F bawah (kN)", "fs terukur (kPa)", "fs model (kPa)",
              "Rasio ukur / model", "Catatan"], rows, rata=list("lc") + ["c"] * 7 + ["l"],
             fmt=[None, "0", "0.00", "0.00", "#,##0", "#,##0", "0.0", "0.0", "0.00", None], fill=AI, beku=False)
    lt.catatan("fs model: U1-U4 = fDN (batas atas; gesekan positif saat uji), U5-U7 = fs metode A 6.1. Beban 200 % belum mobilisasi penuh "
               "(penurunan 4,5 mm). Qb terukur (gaya di SG-7, 1 m di atas ujung): " + "; ".join(
                   f"{tp} {pct} %: {idn(g['Qb_ukur'], 0)} kN" for (tp, pct), g in u["gaya"].items()) + " vs Qb 6.1 866 kN.")
    lt.kosong()
    lt.bagian("C", "CAPWAP (Ru, Rs, Rb) dibanding Qult metode A kondisi uji (selimut U1-U4 positif dengan fDN + 6.1 untuk U5-U7)")
    rows = [[r["tiang"], r["zona"].capitalize(), r["umur"], r["set"], r["dmax"], r["Ru"], r["Rs"], r["Rb"], round(r["Qult_A"], 0),
             round(r["rasio"], 2), "ANOMALI, tidak dalam rata-rata" if r["tiang"] == "T218" else ("umur beton 5 hari (< 7)" if r["tiang"] == "T088" else None)]
            for r in u["capwap"]]
    lt.tabel(["Tiang", "Zona", "Umur (hari)", "Set (mm)", "dmax (mm)", "Ru (kN)", "Rs (kN)", "Rb (kN)", "Qult A uji (kN)", "Ru / Qult A", "Catatan"],
             rows, rata=list("lc") + ["c"] * 8 + ["l"], fmt=[None, None, "0", "0.0", "0.0", "#,##0", "#,##0", "#,##0", "#,##0", "0.00", None],
             fill=AI, beku=False)
    lt.catatan(f"Rata-rata Ru tanpa T218: {idn(u['Ru_rata'], 0)} kN; rata-rata Qult A uji {idn(u['Qult_A_rata'], 0)} kN; rasio rata-rata "
               f"{idn(u['rasio_rata'], 2)}. T218: set 0,6 mm dan Ru 2.723 kN jauh di bawah tiang lain (3.860-4.016): cek PIT/CSL T218 sebelum diterima.")
    lt.kosong()
    lt.bagian("D", "Temuan anomali")
    for t in ANOMALI:
        lt.catatan("- " + t)

    # ---- Penurunan Sisa
    lp.catatan(ket)
    lp.kosong()
    lp.bagian("A", "Asaoka per pelat (selang 7 hari, titik mingguan sejak 31 Mar 2027) dan rasio terhadap prediksi Tahap 2 (urugan 1,05 m)")
    rows = [[k, v["zona"].capitalize(), round(v["b0"], 2), round(v["b1"], 4), round(v["s_inf"], 1), v["akhir"], round(v["s_3mei"], 1),
             round(v["primer_pred"], 1), round(v["rasio"], 2), v["n"]] for k, v in ps["pelat"].items()]
    lp.tabel(["Pelat", "Zona", "b0 (mm)", "b1", "s akhir Asaoka (mm)", "s terakhir 14 Jul (mm)", "s pada 3 Mei (mm)", "Prediksi primer 2.8 (mm)",
              "Terukur / prediksi", "n pasangan"], rows, rata=list("lc") + ["c"] * 8,
             fmt=[None, None, "0.00", "0.0000", "0.0", "0", "0.0", "0.0", "0.00", "0"], fill=AI, beku=False)
    lp.catatan("Rasio terukur / prediksi dilaporkan sebagai informasi. SPL-11 di kaki urugan (±0,6 m): tidak dipakai kalibrasi. " + "; ".join(ps["temuan"]))
    lp.kosong()
    lp.bagian("B", "Kalibrasi per zona dan sisa setelah tiang dipasang (3 Mei 2027)")
    rows = []
    for z, v in ps["zona"].items():
        r = lp.baris + len(rows) + 1
        rows.append([z.capitalize(), v["bor"], round(v["urug"], 2), round(v["k"], 3), round(v["primer_final"], 1), round(v["sek"], 1),
                     round(v["s_akhir"], 1), round(v["s_3mei"], 1), f"=I{r}-J{r}", f'=IF(K{r}>10,"terlampaui","aman")'])
    lp.tabel(["Zona", "Bor", "Urugan ke +11,50 (m)", "Faktor kalibrasi", "Primer akhir terkalibrasi (mm)", "Sekunder 50 th (mm)",
              "Penurunan akhir (mm)", "Terukur pada 3 Mei (mm)", "Sisa setelah tiang (mm)", "Kriteria 10 mm"], rows,
             rata=list("lc") + ["c"] * 8, fmt=[None, None, "0.00", "0.000", "0.0", "0.0", "0.0", "0.0", "0.0", None], fill=AI, beku=False)

    # ---- Pasca-likuifaksi
    lq.catatan(ket + " GEC10 hal. 10-52: seret U5 = 50 % tahanan selimut beta pra-gempa; U5 tidak memberi tahanan; U1-U4 statis; tidak digabung dengan beban gempa.")
    lq.kosong()
    rows = []
    for z in ZONA2:
        n1, n2 = h["np"][z][1], h["np"][z][2]
        rows.append([z.capitalize(), round(elev(z, n1["z"]), 2), round(n1["Qn"], 0), round(elev(z, n2["z"]), 2), round(n2["Qn"], 0),
                     round(n2["Qmaks"], 0), round(t3.kapasitas("BOR-800", profil=z)["NSF_lik"], 0), round(profil_sisa(z, ps)(n2["z"]), 1)])
    lq.tabel(["Zona", "Elev. NP statis (m)", "Qn statis (kN)", "Elev. NP lik. (m)", "Qn lik. (kN)", "Q + Qn lik. (kN)", "NSF lik. Tahap 3 (kN)",
              "s tanah di NP (mm)"], rows, rata=list("l") + ["c"] * 7, fmt=[None, "0.00", "#,##0", "0.00", "#,##0", "#,##0", "#,##0", "0.0"],
             fill=AI, beku=True)
    lq.kosong()
    lq.catatan("Qn pasca-likuifaksi lebih kecil dari statis: seret U5 hanya 50 %. NSF likuifaksi Tahap 3 memakai beta penuh U1-U5 "
               "tanpa bidang netral.")

    # ---- Izin akhir
    li.catatan(ket)
    li.kosong()
    li.bagian("A", "Izin menurut SNI 8460 hal. 204 (utama)")
    rg = {}
    for z in ZONA2:
        r = h["izin"][z]
        a = ad[z]
        li.kosong()
        p1 = li.baris + 1
        li.tabel([f"Zona {z.capitalize()}", "Nilai (kN)", "Rumus / sumber"],
                            [["Qult statis A (6.1)", round(r["Qult_st"], 1), "tahap6_tiang_tunggal.hitung('A')"],
                             ["Qult tanpa U5 (U6 + U7 + Qb)", round(r["Qult_tanpaU5"], 1), "6.1, u5_statis = False"],
                             ["Qn statis lapisan menurun U1-U4", round(r["Qn1"], 1), "fDN metode A (U1-U4)"],
                             ["Qn likuifaksi U1-U4 + 50 % U5", round(r["Qn2"], 1), "GEC10 hal. 10-52"],
                             ["Izin statis = Qult / 2,5 - Qn", f"=D{p1}/{t6.FK}-D{p1 + 2}", "SNI 8460 hal. 204, 194"],
                             ["Izin likuifaksi = Qult tanpa U5 / 1,1 - Qn", f"=D{p1 + 1}/{t6.FK_GM}-D{p1 + 3}", "SNI 8460 hal. 295"],
                             ["Izin SNI = minimum", f"=MIN(D{p1 + 4},D{p1 + 5})", "≥ beban kerja"]],
                            rata=["l", "c", "l"], fmt=[None, "#,##0.0", None], fill=AI, beku=False)
        rg[z] = f"'Izin Akhir'!D{p1 + 6}"
    li.kosong()
    li.bagian("B", "Izin menurut GEC10 dan pembanding")
    rows = []
    for z in ZONA2:
        g = h["gec"][z]
        rows += [[f"{z.capitalize()}: geoteknik Qult / 2,5, tanpa seret", round(g["geo"], 0), "GEC10 hal. 326 (10-46): seret tidak ada di batas kuat geoteknik"],
                 [f"{z.capitalize()}: beban struktur Q + Qn (kasus 1)", round(g["str_maks"], 0),
                  f"kapasitas beton polos {idn(KAP_STR, 0)} kN [Asumsi]; Q izin sisa kapasitas {idn(g['Q_izin_str'], 0)} kN"],
                 [f"{z.capitalize()}: penurunan tiang = tanah di bidang netral (mm)", round(g["s_np1"], 1),
                  "batas layan; kriteria penurunan struktur belum ditetapkan (Briaud-Tucker 10 mm informasi)"],
                 [f"{z.capitalize()}: izin GEC10 = min(geoteknik, struktur)", round(g["izin"], 0), "banding Tahap 3: 911 (selatan), 877 (utara)"]]
    li.tabel(["Butir", "Nilai", "Keterangan"], rows, rata=["l", "c", "l"], fmt=[None, "#,##0.0", None], fill=AI, beku=False)
    li.kosong()
    li.bagian("C", "Beban layan per tiang terbesar dari 6.0 dan panjang minimum (usulan; benam ke U7, langkah 0,5 m)")
    rows = []
    for z in ZONA2:
        p = pz[z]

        def f(x, z=z):
            return f"benam {idn(x[0], 1)} m, panjang {idn(panjang_usul(z, x[0]), 1)} m" if x[0] else "tidak tercapai sampai benam 14 m"
        rows += [[f"{z.capitalize()}: SNI, target 911 kN", f(p["sni"]), f"panjang ada {idn(p['L_ada'], 2)} m"],
                 [f"{z.capitalize()}: SNI, target Pmax {idn(p['target'], 0)} kN", f(p["sni_qmaks"]), ""],
                 [f"{z.capitalize()}: GEC10, target 911 kN", f(p["gec"]), "Qult/2,5 >= target, Q + Qn <= kapasitas, NP di bawah U5"],
                 [f"{z.capitalize()}: GEC10, target Pmax {idn(p['target'], 0)} kN", f(p["gec_qmaks"]), ""]]
    li.tabel(["Kriteria", "Hasil", "Keterangan"], rows, rata=["l", "c", "l"], beku=False, fill=AI)

    # ---- Acuan, Keputusan
    la.catatan(ket)
    la.kosong()
    la.tabel(["Acuan", "Status", "Letak"], [list(a) for a in ACUAN], rata=list("lcl"), beku=True)
    lk.catatan(ket)
    lk.kosong()
    lk.tabel(["Butir", "Keterangan"], [list(k) for k in KEPUTUSAN], rata=list("ll"), beku=True)

    # ---- gambar
    try:
        from openpyxl.drawing.image import Image
        for p, z in zip(grafik(h), ZONA2):
            im = Image(str(p))
            im.width, im.height = 780, 468
            wb["Pasca-Likuifaksi"].add_image(im, f"C{12 if z == 'SELATAN' else 38}")
    except Exception as e:   # noqa: BLE001
        print("gambar dilewati:", e)
    keluar.parent.mkdir(parents=True, exist_ok=True)
    wb.save(keluar)
    return keluar, ring, rg


ANOMALI = [
    "TP-2: cor tertunda 4 jam, CSL cacat (D) di dasar 0,0-0,4 m di atas ujung; tidak dipakai untuk kalibrasi kapasitas.",
    "TP-3 SG-4: sensor B mengukur 15-32 µε vs sensor A 38-89 µε (sensor rusak); dipakai sensor A.",
    "T218: Ru 2.723 kN (set 0,6 mm, palu 4 t): cek PIT/CSL T218; tidak dipakai dalam rata-rata.",
    "T088: PDA pada umur beton 5 hari, cepat rambat 3.502 m/s rendah.",
    "SPL-05: pelat dipasang ulang 12 Mei 2027 (tersenggol dozer); seri disambung dengan offset 239 mm [Asumsi], pasangan lintas sambungan dibuang.",
]


def temuan_teks(h, pz):
    zs, zu, iz, ps, u = h["np"]["SELATAN"], h["np"]["UTARA"], h["izin"], h["ps"], h["uji"]
    return [
        f"T1. Bidang netral kasus 1 selatan elevasi {idn(elev('SELATAN', zs[1]['z']), 2)} m (kedalaman {idn(zs[1]['z'], 1)} m), Qn "
        f"{idn(zs[1]['Qn'], 0)} kN, Q + Qn {idn(zs[1]['Qmaks'], 0)} kN; utara {idn(elev('UTARA', zu[1]['z']), 2)} m, Qn "
        f"{idn(zu[1]['Qn'], 0)} kN, Q + Qn {idn(zu[1]['Qmaks'], 0)} kN. Bidang netral jauh di bawah dasar U5: seret mencakup U1-U4, U5 dan U6 bagian atas.",
        "T2. Qn jauh di atas NSF Tahap 3 (452 dan 487 kN) karena Tahap 3 hanya menghitung U1-U4 dengan beta; di sini seret mencapai bidang netral.",
        f"T3. Izin SNI 8460 (Qult/2,5 - Qn lapisan menurun) pada 38,45 m: selatan {idn(iz['SELATAN']['izin'], 0)} kN, utara {idn(iz['UTARA']['izin'], 0)} kN "
        "(≥ 911 kN). Qn bidang netral hanya untuk cek struktur: Q + Qn jauh di bawah kapasitas beton.",
        f"T4. Sisa penurunan tanah setelah tiang dipasang (3 Mei 2027): selatan {idn(ps['zona']['SELATAN']['sisa'], 0)} mm, utara "
        f"{idn(ps['zona']['UTARA']['sisa'], 0)} mm, jauh di atas 10 mm (Briaud-Tucker): seret nyata.",
        "T5. Uji beban 200 % (1.822 kN) tanpa runtuh, garis Davisson tidak terlampaui (4,5-5,1 mm vs 15,5 mm). Uji hanya membuktikan FK >= 2,0 pada "
        "911 kN, bukan 2,5. Anomali: T218 (PDA), TP-2 (cacat dasar), TP-3 SG-4 sensor B, SPL-05 pelat dipasang ulang.",
    ]


# ------------------------------------------------------------------ verifikasi T-100
def baca_excel(berkas=BERKAS, ring=None, rg=None):
    import openpyxl
    wb = openpyxl.load_workbook(berkas, data_only=True)
    ws = wb["Ringkasan"]
    out = {}
    if ring is None:
        ring = {}
        for r in range(1, ws.max_row + 1):
            if ws.cell(r, 3).value in ("Selatan", "Utara") and ws.cell(r, 4).value in (1, 2):
                ring[(ws.cell(r, 3).value.upper(), ws.cell(r, 4).value)] = r
    if rg is None:
        rg, wi = {}, wb["Izin Akhir"]
        zz = iter(ZONA2)
        for r in range(1, wi.max_row + 1):
            if wi.cell(r, 3).value == "Izin SNI = minimum":
                rg[next(zz)] = f"'Izin Akhir'!D{r}"
    for (z, k), r in ring.items():
        out[(z, k)] = {"z": ws.cell(r, 5).value, "elev": ws.cell(r, 6).value, "Qn": ws.cell(r, 7).value, "Qmaks": ws.cell(r, 8).value}
    iz = {}
    for z, a in (rg or {}).items():
        sh, ad = a.split("!")
        iz[z] = wb[sh.strip("'")][ad.replace("$", "")].value
    return out, iz


def t100(berkas=BERKAS, ring=None, rg=None, h=None):
    h = h or semua()
    ex, iz = baca_excel(berkas, ring, rg)
    dx = 0.0
    for (z, k), e in ex.items():
        n = h["np"][z][k]
        for a, b in ((e["z"], n["z"]), (e["Qn"], n["Qn"]), (e["Qmaks"], n["Qmaks"])):
            dx = max(dx, abs(a - b) / abs(b) * 100)
    for z, v in iz.items():
        dx = max(dx, abs(v - h["izin"][z]["izin"]) / abs(h["izin"][z]["izin"]) * 100)
    dnp = max(abs(h["np"][z][k]["z"] - h["np"][z][k]["z_tertutup"]) for z in ZONA2 for k in (1, 2))
    dt3 = max(abs(nsf_u1u4_beta(z) - t3.kapasitas("BOR-800", profil=z)["NSF_statis"]) / t3.kapasitas("BOR-800", profil=z)["NSF_statis"] * 100
              for z in ZONA2)
    dq = max(abs(h["np"][z][1]["Qn"] - h["npT3"][z][1]["Qn"]) / h["npT3"][z][1]["Qn"] * 100 for z in ZONA2)
    dcap = abs(h["uji"]["rasio_rata"] - 1) * 100
    asa = {z: h["ps"]["zona"][z]["k"] for z in ZONA2}
    lolos = dx <= TOL["excel"] and dt3 <= TOL["excel"] and dnp <= TOL["np"] and dq <= TOL["t3"] and dcap <= TOL["capwap"]
    return {"dx": dx, "dnp": dnp, "dt3": dt3, "dq": dq, "dcap": dcap, "asa": asa, "lolos": lolos}


def catat_t100(r=None, h=None, berkas=VERIFIKASI):
    h = h or semua()
    r = r or t100(h=h)
    zs, zu = h["np"]["SELATAN"][1], h["np"]["UTARA"][1]
    baris = ("| T-100 | Cek silang 6.2 gesekan negatif dan bidang netral tiang bor Ø800 (kasus 1 statis dan kasus 2 pasca-likuifaksi) "
             f"| (a) rumus Excel hidup (lembar irisan, dihitung ulang di Excel) vs skrip `tahap6_nsf.py`: z bidang netral, Qn, Q + Qn, izin SNI, selisih terbesar "
             f"{idn(r['dx'], 4)} %; setelan beta Tahap 3 vs `t3.kapasitas` NSF statis {idn(r['dt3'], 4)} %; (b) bidang netral dua cara (perpotongan irisan vs bentuk tertutup) "
             f"selisih {idn(r['dnp'], 3)} m "
             f"| (c) Qn metode A vs Qn dengan beta Tahap 3 (bidang netral sama): selisih {idn(r['dq'], 1)} %; (d) CAPWAP Ru rata-rata (tanpa T218) vs Qult A kondisi uji: "
             f"rasio {idn(h['uji']['rasio_rata'], 2)} (selisih {idn(r['dcap'], 1)} %); (e) kalibrasi Asaoka / prediksi 2.8: selatan {idn(r['asa']['SELATAN'], 2)}, "
             f"utara {idn(r['asa']['UTARA'], 2)} (informasi) "
             f"| (a) ≤ 0,5 %; (b) ≤ 0,25 m; (c) ±30 % [Asumsi]; (d) ±25 % [Asumsi]; (e) dilaporkan | {'Lolos' if r['lolos'] else 'GAGAL'}, {STATUS} "
             "| `skrip/tahap6_nsf.py`, `tests/test_tahap6_nsf.py` | Ditetapkan sebelum membandingkan. Data simulasi. "
             f"Bidang netral selatan {idn(elev('SELATAN', zs['z']), 2)} m, utara {idn(elev('UTARA', zu['z']), 2)} m. |")
    teks = Path(berkas).read_text(encoding="utf-8").split("\n")
    teks = [ln for ln in teks if not ln.startswith("| T-100 |")]
    i = next(k for k, ln in enumerate(teks) if ln.startswith("| T-99 |"))
    teks.insert(i + 1, baris)
    Path(berkas).write_text("\n".join(teks), encoding="utf-8")
    return baris


# ------------------------------------------------------------------ Markdown
def tulis_md(keluar=MD, h=None, pz=None, r=None):
    h = h or semua()
    pz = pz or panjang_zona(h)
    r = r or t100(h=h)
    ps, u, iz = h["ps"], h["uji"], h["izin"]
    L = [f"# 6.2 Gesekan negatif (NSF) dan bidang netral tiang bor Ø800 ({STATUS}, 21 Nov 2026)\n",
         "DATA SIMULASI. Disusun AI atas permintaan Defsa; kunci jawaban tidak dibuka. Rincian di `6.2 Gesekan Negatif.xlsx` "
         "(`skrip/tahap6_nsf.py`, uji `tests/test_tahap6_nsf.py`).\n",
         "## Tujuan\n",
         "Gesekan negatif (seret) pada tiang bor Ø800 (kepala +10,85 m, ujung -27,60 m, panjang 38,45 m) di zona selatan (BH-5) dan utara "
         "(BH-3) akibat urugan ke +11,50 m dan PVD; bidang netral; izin akhir; telaah data uji (uji beban, regangan, PDA, pelat penurunan); "
         "usulan panjang. Tengah hanya informasi.\n",
         "## Keputusan metode\n",
         "- Bidang netral (GEC10 10.6.2 hal. 327-328, Gambar 10-20): Kurva A = Qb + tahanan selimut di bawah z, Kurva B = Q + seret "
         "kumulatif dari atas (seret = tahanan selimut satuan). Dicari dua cara: perpotongan irisan 0,25 m dan bentuk tertutup "
         "S(z) = (Qb + S_tot - Q) / 2.",
         "- fDN: U1-U2 dan U4 lempung alpha su (alpha <= 1 [Asumsi]; su U4 = 5,2 + 1,09 z), U3 gambut 0,25 sigma'v [Asumsi Fellenius]; U5-U7 "
         "tahanan satuan metode A 6.1 (disetujui). Q = 911 kN; Qb = 866 kN (penuh); 50 % sebagai kepekaan [Asumsi].",
         "- Kasus 2 pasca-likuifaksi (GEC10 hal. 332): seret U5 = 50 % selimut beta pra-gempa, tahanan U5 = 0, U1-U4 statis; tidak digabung dengan beban gempa.",
         "- Izin: SNI 8460 hal. 204 (utama) dan GEC10 hal. 326 (seret hanya di batas struktur dan layan).\n",
         "## Telaah data uji\n",
         "**Uji beban statis (tiang uji TP-1..TP-4, 200 % = 1.822 kN, ujung -27,60 m).** Penurunan 200 %: " + ", ".join(
             f"{tp} {idn(k['s200_ukur'], 2)} mm" for tp, k in u["kurva"].items()) + f"; sisa 1,78-2,42 mm. Garis Davisson (PL/AE + 4 mm + D/120, "
         f"FHWA-NHI-06-089 hal. 275-276) pada 1.822 kN = {idn(min(k['davisson'] for k in u['kurva'].values()), 1)}-"
         f"{idn(max(k['davisson'] for k in u['kurva'].values()), 1)} mm, tidak terlampaui: Qult > 1.822 kN tanpa runtuh. Uji hanya membuktikan "
         "FK >= 2,0 pada 911 kN, bukan 2,5 (butuh 2.278 kN). Ekstrapolasi Chin [Literatur, belum ada di acuan/] "
         f"{idn(min(k['chin'] for k in u['kurva'].values()), 0)}-{idn(max(k['chin'] for k in u['kurva'].values()), 0)} kN (informasi). "
         f"Kekakuan pada 100 %: {idn(min(k['kaku100'] for k in u['kurva'].values()), 0)}-{idn(max(k['kaku100'] for k in u['kurva'].values()), 0)} kN/mm.\n",
         "**Regangan (TP-1 utara, TP-3 selatan).** EA dikalibrasi dari SG-1 tiap tahap (EA 14,05-14,32 MN, E ± 28 GPa). Gesekan terukur antar "
         "level pada 200 %: U1-U4 3-8 kPa (di bawah fDN, 12-17 kPa), U5-U7 13-33 kPa (model 6.1: 43-52 kPa), karena beban 200 % baru memobilisasi "
         "sebagian (penurunan 4,5 mm = 0,6 % D); Qb terukur 190-260 kN pada 200 % vs 866 kN (penuh). Detail per interval di lembar Telaah Data Uji.\n",
         f"**CAPWAP.** Ru rata-rata (tanpa T218) {idn(u['Ru_rata'], 0)} kN vs Qult metode A kondisi uji {idn(u['Qult_A_rata'], 0)} kN: rasio "
         f"{idn(u['rasio_rata'], 2)} (Rb 745-880 kN vs Qb 866 kN). Metode A tidak konservatif pada selimut U1-U4 di kondisi uji karena fDN dihitung "
         "penuh; di U5-U7 CAPWAP (Rs ≈ 3.100 kN) lebih rendah dari model.\n",
         "**Temuan anomali.**"] + [f"- {a}" for a in ANOMALI] + [
         "\n## Sisa penurunan tanah setelah PVD\n",
         "Asaoka (selang 7 hari, titik mingguan sejak 31 Mar 2027; Asaoka 1978 [Literatur, belum ada di acuan/]) per pelat, lalu faktor kalibrasi "
         "k = penurunan akhir Asaoka / primer prediksi 2.8 (urugan 1,05 m) rata-rata per zona. Penurunan akhir ke +11,50 m = k x primer + sekunder 50 th; "
         "sisa setelah tiang (3 Mei 2027) = akhir - terukur pada 3 Mei.\n",
         "| Zona | k | Terukur 3 Mei (mm) | Penurunan akhir (mm) | Sisa setelah tiang (mm) |", "|---|---|---|---|---|"]
    for z in ZONA2 + ["TENGAH"]:
        v = ps["zona"][z]
        L.append(f"| {z.capitalize()} | {idn(v['k'], 2)} | {idn(v['s_3mei'], 0)} | {idn(v['s_akhir'], 0)} | {idn(v['sisa'], 0)} |")
    L.append("\nSisa jauh di atas 10 mm (Briaud-Tucker, GEC10 hal. 326): seret nyata, tiang harus menembus lapisan penyebab seret (ujung di U7 terpenuhi). "
             "Rasio terukur / prediksi 2.8 per pelat di lembar Penurunan Sisa (informasi).\n")
    L.append("## Hasil bidang netral (Q = 911 kN)\n")
    L.append("| Zona | Kasus | Elev. bidang netral (m) | z (m) | Qn (kN) | Q + Qn (kN) | Qn Qb 50 % | Qn beta T3 | s tanah di NP (mm) | NSF Tahap 3 |")
    L.append("|---|---|---|---|---|---|---|---|---|---|")
    for z in ZONA2:
        for k in (1, 2):
            n = h["np"][z][k]
            L.append(f"| {z.capitalize()} | {k} | {idn(elev(z, n['z']), 2)} | {idn(n['z'], 1)} | {idn(n['Qn'], 0)} | {idn(n['Qmaks'], 0)} | "
                     f"{idn(h['np50'][z][k]['Qn'], 0)} | {idn(h['npT3'][z][k]['Qn'], 0)} | {idn(profil_sisa(z, ps)(n['z']), 1)} | "
                     f"{idn(t3.kapasitas('BOR-800', profil=z)['NSF_statis' if k == 1 else 'NSF_lik'], 0)} |")
    L.append("\nKasus 1 = urugan + PVD (statis jangka panjang); kasus 2 = pasca-likuifaksi U5. Penurunan tiang = penurunan tanah di bidang netral "
             "(GEC10 hal. 326). Qn jauh di atas NSF Tahap 3 karena Tahap 3 menghitung seret hanya di U1-U4 dengan beta.\n")
    L.append("## Izin akhir\n")
    L.append("| Zona | Izin SNI statis | Izin SNI likuifaksi | Izin SNI | Geoteknik GEC10 (Qult/2,5) | Q + Qn struktur | Kapasitas beton polos | Tahap 3 |")
    L.append("|---|---|---|---|---|---|---|---|")
    for z in ZONA2:
        g, i = h["gec"][z], iz[z]
        L.append(f"| {z.capitalize()} | {idn(i['izin_st'], 0)} | {idn(i['izin_lik'], 0)} | {idn(i['izin'], 0)} | {idn(g['geo'], 0)} | "
                 f"{idn(g['str_maks'], 0)} | {idn(KAP_STR, 0)} | {'911' if z == 'SELATAN' else '877'} |")
    qm = h["qmaks"]
    L.append(f"\nSNI 8460 hal. 204: seret sebagai beban, tidak dibagi FK. Qn SNI = seret lapisan menurun saja (U1-U4; U1-U4 + 50 % U5 pasca-likuifaksi); Qn bidang netral tidak dikurangkan dari Qult karena memuat gesekan U5/U6 yang sudah dihitung di Qult. "
             "Menurut GEC10, seret tidak mengurangi daya dukung geoteknik; yang dicek adalah beban struktur di bidang netral (Q + Qn) dan penurunan layan. "
             f"Beban layan per tiang terbesar dari 6.0: selatan {idn(qm.get('SELATAN', (0,))[0], 0)} kN, utara {idn(qm.get('UTARA', (0,))[0], 0)} kN. "
             f"Kapasitas beton polos {idn(KAP_STR, 0)} kN [Asumsi konservatif, f'c 30 MPa; silinder 28 hari 32-36 MPa; tulangan di 6.7].\n")
    L.append("## Panjang tiang (usulan)\n")
    L.append("| Zona | Panjang ada | SNI, 911 kN | SNI, Pmax | GEC10, 911 kN | GEC10, Pmax |\n|---|---|---|---|---|---|")

    def f(z, x):
        return f"benam {idn(x[0], 1)} m ({idn(panjang_usul(z, x[0]), 1)} m)" if x[0] else "tidak tercapai (benam <= 14 m)"
    for z in ZONA2:
        p = pz[z]
        L.append(f"| {z.capitalize()} | {idn(p['L_ada'], 2)} m | {f(z, p['sni'])} | {f(z, p['sni_qmaks'])} | {f(z, p['gec'])} | {f(z, p['gec_qmaks'])} |")
    L.append("\nPanjang 38,45 m tidak diubah (keputusan Defsa 21 Nov 2026); GEC10 10.6.3: memperpanjang tiang lebih efektif daripada memperbesar diameter. "
             "Seret kelompok (keliling blok, NHI-06-089 9.8) untuk 6.3.\n")
    L.append("## Verifikasi T-100\n")
    L.append(f"Toleransi ditetapkan dulu: (a) Python vs rumus Excel ≤ 0,5 %; (b) bidang netral dua cara ≤ 0,25 m; (c) Qn metode A vs beta Tahap 3 ±30 % [Asumsi]; "
             f"(d) CAPWAP Ru vs Qult A kondisi uji ±25 % [Asumsi]; (e) Asaoka vs prediksi 2.8 dilaporkan. Hasil: (a) {idn(r['dx'], 4)} % (setelan beta T3 vs "
             f"`t3.kapasitas` {idn(r['dt3'], 4)} %); (b) {idn(r['dnp'], 3)} m; (c) {idn(r['dq'], 1)} %; (d) {idn(r['dcap'], 1)} %; (e) k selatan "
             f"{idn(r['asa']['SELATAN'], 2)}, utara {idn(r['asa']['UTARA'], 2)}. Lolos: {'ya' if r['lolos'] else 'TIDAK'}.\n")
    L.append("## Acuan yang belum ada di acuan/\n")
    for a in ACUAN:
        if a[1] == "belum ada":
            L.append(f"- {a[0]}: {a[2]}")
    L.append("\n## Hal yang perlu diputuskan Defsa\n")
    for i, k in enumerate(KEPUTUSAN, 1):
        L.append(f"{i}. **{k[0]}**: {k[1]}")
    L.append(f"\nStatus: {STATUS}.\n")
    Path(keluar).write_text("\n".join(L), encoding="utf-8")
    return keluar


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    from format_dokumen import hitung_ulang_excel
    h = semua()
    pz = panjang_zona(h)
    berkas, ring, rg = buat_excel(h=h, pz=pz)
    print(berkas, hitung_ulang_excel(berkas))
    r = t100(berkas, ring, rg, h)
    print(r)
    print(catat_t100(r, h))
    print(tulis_md(h=h, pz=pz, r=r))
    for z in ZONA2:
        print(z, {k: (v[0], v[1]) if v and v[0] else None for k, v in pz[z].items() if k in ("sni", "sni_qmaks", "gec", "gec_qmaks")})


if __name__ == "__main__":
    main()
