"""Tahap 6, langkah 6.7: desain struktur tiang bor Ø800, pile cap (kolom dan inti), angkur pit, dan cek sloof pada δ 24,6 mm.

Data SIMULASI. Sumber angka (semua dari berkas proyek, bukan tebakan):
- tiang, gaya, elevasi: 6.1, 6.2 (Q+Qn, bidang netral), 6.3 (`tahap6_tata_letak.rancang("a")`, cap), 6.5 (M inersia 177 kNm utara,
  Youd 966 kNm, V 366 dan 53,95 kN), `06 Struktur Bawah dan Basement/6.7 Lembar Isian Tiang dan Cap.md`;
- SNI 2847:2019 (halaman PDF di ACUAN): 13.4, 18.13.4, 18.7.5, 21.2, 22.4-22.6, 23, 25.4, 25.7.3, 24.4.3;
- SNI 8460:2017 Ps. 9.3.3 b dan 9.3.4 (hal. PDF 197); SNI 1726:2019 Ps. 7.13.8.3.3 (hal. PDF 108);
- pit: `05 Struktur Tengah/5.5 Desain Pit Lift.md` (FK, W, U, letak); sloof: `5.4 Desain Sloof.xlsx` (φMn, Mu gravitasi), 6.6 (M penurunan).
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tahap6_tata_letak as tl  # noqa: E402

AKAR = Path(__file__).resolve().parents[1]
KELUAR = AKAR / "06 Struktur Bawah dan Basement"
BERKAS = KELUAR / "6.7 Desain Tiang dan Pile Cap.xlsx"
MD = KELUAR / "6.7 Desain Tiang dan Pile Cap.md"
VERIFIKASI = AKAR / "VERIFIKASI.md"

LABEL = "DATA SIMULASI untuk studi kasus portofolio. Bukan data proyek nyata. Tidak untuk konstruksi."
STATUS = ("disetujui Defsa 22 Nov 2026 (tiang, cap kolom, pit, sloof); revisi 22 Nov 2026: Cap C digabung ke Cap E dan Cap E didesain sebagai pelat di atas tiang "
          "(keputusan Defsa); Cap E pelat h 2.000 mm: usulan AI disetujui atas delegasi Defsa 22 Nov 2026")
LABEL_AI = f"DIHITUNG AI ATAS PERMINTAAN DEFSA (22 Nov 2026), sel hijau; STATUS: {STATUS}. Kunci jawaban tidak dibuka."

# toleransi T-105, ditetapkan sebelum membandingkan
TOL = {"tangan": 2.0, "excel": 0.1, "stm": 30.0, "sum_pelat": 0.5, "max_pelat": 25.0}      # %

# ------------------------------------------------------------------ data tiang (lembar isian A.1)
D = 800.0                       # mm
AG = math.pi * D ** 2 / 4       # mm2
FY, FYT, ES = 420.0, 420.0, 200000.0
SEL = 75.0                      # mm, Tabel 20.6.1.3.1 (kontak tanah permanen)
DB, DSP = 25.0, 13.0            # D25 memanjang; spiral D13 (D10 tidak cukup: s < 25 mm, lihat spiral())
KEPALA, UJUNG = 10.85, -27.60
U5_DASAR = {"SELATAN": -9.31, "UTARA": -8.85}         # atas U6 (6.6 lembar isian A.2)
NP2 = {"SELATAN": -16.72, "UTARA": -16.50}            # bidang netral kasus 2 pasca-likuifaksi (6.2)
Q_QN = {"SELATAN": 3003.0, "UTARA": 2929.0}           # Q + Qn kasus 1 (6.2, Q 911 kN)
QN = {"SELATAN": 2092.0, "UTARA": 2018.0}
M_INERSIA_UTARA, M_YOUD = 177.0, 966.0                # kNm (6.5)
V_YOUD, V_INERSIA = 366.0, 53.95                      # kN (6.5)
PU_TARIK = -1452.0                                    # kN, Pu min cap D (6.3)
PU_D, PU_E = 3254.0, 3230.0                           # Pu maks per tiang cap D (utara) dan cap E (selatan), 6.3
P_E = 1560.0                                          # Pmax layan per tiang Cap E
FC_VARIAN = (30.0, 35.0)

ACUAN = [
    ("SNI 2847:2019 13.4.1-13.4.3", "hal. PDF 289-290", "pile cap: d ≥ 300 mm; reaksi tiang di pusat tiang; Vn 22.5 dan 22.6; Vu 13.4.2.5; STM 13.4.2.4 (βs 0,60λ)"),
    ("SNI 2847:2019 13.2.6.3, 13.2.7", "hal. PDF 285", "STM pile cap diizinkan; penampang kritis Mu di muka kolom"),
    ("SNI 2847:2019 18.13.4.1, 18.13.4.3", "hal. PDF 450", "tulangan tarik tiang menerus; tulangan transversal 18.7.5.2-18.7.5.4 (kecuali (c) dan (f)) ≥ 5 dimensi dan ≥ 1,8 m di bawah cap"),
    ("SNI 1726:2019 7.13.8.3.3", "hal. PDF 108", "tiang di tanah terlikuifaksi: 18.7.5 sampai dasar lapisan terlikuifaksi + 7 dimensi"),
    ("SNI 2847:2019 10.6.1.1, 18.7.4.1", "hal. PDF 237, 408", "Ast 0,01-0,08 Ag (kolom); 0,01-0,06 Ag dan ≥ 6 batang (18.7.4)"),
    ("SNI 2847:2019 18.7.5.3, Tabel 18.7.5.4 (d), (e)", "hal. PDF 410-412", "spasi ≤ min(¼ dimensi, 6 db); ρs = terbesar 0,45 (Ag/Ach - 1) f'c/fyt dan 0,12 f'c/fyt"),
    ("SNI 2847:2019 22.4.2.1, 22.4.2.2", "hal. PDF 503", "Pn,maks = 0,85 Po (spiral); Po = 0,85 f'c (Ag - Ast) + fy Ast"),
    ("SNI 2847:2019 21.2.1, 21.2.2 Tabel 21.2.2", "hal. PDF 491, 493", "φ geser 0,75, STM 0,75; spiral 0,75 (tekan) - 0,90 (εt ≥ 0,005)"),
    ("SNI 2847:2019 22.5.2.2, 22.5.5.1, 22.5.6.1, 22.5.10.5.3", "hal. PDF 505-509", "penampang lingkaran d = 0,8 D, bw = D; Vc = 0,17 λ √f'c bw d; dengan tekan Vc × (1 + Nu / 14 Ag); Vs = Av fyt d / s"),
    ("SNI 2847:2019 22.6.4.1, 22.6.5.2, 22.6.5.3", "hal. PDF 518, 521", "bo di d/2; vc = terkecil 0,33; 0,17 (1 + 2/β); 0,083 (2 + αs d / bo) × λ √f'c; αs 40 / 30 / 20"),
    ("SNI 2847:2019 23.2.7, 23.4.3, 23.7.2, 23.9.2", "hal. PDF 556, 557, 561, 563", "sudut ≥ 25°; fce = 0,85 βs f'c; Fnt = Ats fy; nodal βn 1,0 / 0,8 / 0,6"),
    ("SNI 2847:2019 25.4.2.1, 25.4.3.1", "hal. PDF 587-591", "ld = fy db / (1,7 λ √f'c) (spasi ≥ 2 db, selimut ≥ db); ldh = 0,24 fy db / (λ √f'c)"),
    ("SNI 2847:2019 25.7.3.1, 25.7.3.2", "hal. PDF 624", "spiral: jarak bersih 25-75 mm; diameter ≥ 9,5 mm cor di tempat"),
    ("SNI 2847:2019 Tabel 20.6.1.3.1, Tabel 19.3.2.1, Tabel 24.4.3.2", "hal. PDF 482, 464, 575", "selimut 75 mm kontak tanah; S2: w/cm 0,45, f'c ≥ 31; susut-suhu 0,0018 (fy 420) [penerapan ke cap: usulan AI]"),
    ("SNI 8460:2017 9.3.3 b, 9.3.4", "hal. PDF 197", "uplift FK ≥ 1,5; buoyancy FK ≥ 1,5 dengan angkur, ≥ 1,1 dengan beban mati minimum; pasal 10.6 hanya angkur tanah (hal. 264-272)"),
]
KEPUTUSAN_DASAR = "lihat bagian Keputusan di md"
KEPUTUSAN_DEFSA = [
    "**Keputusan Defsa 22 Nov 2026: usulan AI dipakai** untuk butir 1-6 di bawah: f'c tiang 35 MPa dengan 16 D25 (rasio 0,83); tulangan tiang cap kolom dipotong di -17,76, cap inti penuh; "
    "spiral D13 40/80 mm sampai -14,91; tebal cap kolom minimum 1.000 / 800 / 950 mm (2/3/4 tiang; kepala tiang = muka cap +12,05 - h + 0,15, dicatat untuk 6.9); "
    "pit varian A (FK 1,110), pengikat B bila Q100 dipakai; pit berdiri di Cap E. Serakan Zhang (butir 7) tetap terbuka.",
    "**Keputusan Defsa 22 Nov 2026: tebal Cap E 1.500 mm** (sebelum penggabungan Cap C, baris h 1.500: STM 0,810, geser satu arah 0,622, pons inti 0,714, As x 218.479 mm² ρ 0,86 %). "
    "Mengubah B-3 (1.200) khusus Cap E; cap inti lain tetap 1.200. Akibat (dibawa ke 6.9): dasar Cap E +10,55 (muka +12,05), kepala tiang Cap E +10,70 (panjang 38,30 m, ujung -27,60); "
    "dasar pit +10,80 di atas dasar cap, jadi pit L-1..4 berdiri di dalam Cap E (butir 5).",
    "**Keputusan Defsa 22 Nov 2026: tetap 32 tiang; Cap E didesain sebagai pelat tebal di atas tiang (usulan h 1.800 mm); STM hanya lokal di sekitar inti.** "
    "Alasan: dengan h 1.500 model STM per tiang gagal (rasio 1,196, non-monoton terhadap h; model STM per tiang tidak cocok untuk cap selebar rakit), geser satu arah 1,168, pons inti 0,794. "
    "Hasil pelat (`skrip/tahap6_cap_pelat.py`) di bagian 4.",
    "**Keputusan (usulan AI, disetujui atas delegasi Defsa 22 Nov 2026): Cap E pelat h 2.000 mm, tanpa tulangan pons.** Setelah berat cap masuk 6.3 (temuan 6.9), h 1.800 gagal pons inti (1,079) dan 1.900 gagal tipis (1,014); "
    "h 2.000 lolos (pons inti 0,955). Cap E gabungan 54 tiang, 30,4 × 13,6 m; dasar Cap E +10,05, kepala tiang +10,20.",
]


def idn(v, d=1):
    return f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ================================================================== A. tiang bor Ø800
def beta1(fc):
    return 0.85 if fc <= 28 else max(0.65, 0.85 - 0.05 * (fc - 28) / 7)


def ec(fc):
    return 4700.0 * math.sqrt(fc)


def pm_kurva(fc, n, db=DB, sel=SEL, dsp=DSP, npt=400):
    """Diagram interaksi penampang lingkaran, n batang db merata pada lingkaran (satu batang di sisi tekan teratas), spiral (φ 0,75-0,90).
    Kembalikan dict: phiPn, phiMn (kN, kNm) urut c turun, phiPn_maks, phiTn, Po, Ast, epsilon_t."""
    R = D / 2
    Rs = R - sel - dsp - db / 2
    Asb = math.pi * db ** 2 / 4
    ast = n * Asb
    ang = 2 * math.pi * np.arange(n) / n
    di = R - Rs * np.cos(ang)               # kedalaman batang dari sisi tekan
    ley = R - di                            # lengan terhadap pusat (+ ke sisi tekan)
    po = 0.85 * fc * (AG - ast) + FY * ast
    pmaks = 0.75 * 0.85 * po / 1e3
    ety = FY / ES
    out = dict(phiPn=[], phiMn=[], et=[], c=[])
    for c in np.geomspace(5.0, 30 * D, npt)[::-1]:
        a = min(beta1(fc) * c, D)
        th = math.acos(max(-1.0, min(1.0, (R - a) / R)))
        ac = R ** 2 * (th - math.sin(th) * math.cos(th))
        yc = 0.0 if a >= D - 1e-9 else 2 * R * math.sin(th) ** 3 / (3 * (th - math.sin(th) * math.cos(th)))
        cc = 0.85 * fc * ac
        eps = 0.003 * (c - di) / c
        fs = np.clip(ES * eps, -FY, FY)
        f = Asb * (fs - np.where(di < a, 0.85 * fc, 0.0))
        pn = (cc + f.sum()) / 1e3
        mn = (cc * yc + (f * ley).sum()) / 1e6
        et = 0.003 * (di.max() - c) / c
        phi = 0.75 if et <= ety else (0.90 if et >= 0.005 else 0.75 + 0.15 * (et - ety) / (0.005 - ety))
        out["phiPn"].append(min(phi * pn, pmaks))
        out["phiMn"].append(phi * mn)
        out["et"].append(et)
        out["c"].append(c)
    out["phiTn"] = 0.9 * FY * ast / 1e3
    out["phiPn_maks"] = pmaks
    out["Po"] = po / 1e3
    out["Ast"] = ast
    out["phiPn"] = np.array(out["phiPn"])
    out["phiMn"] = np.array(out["phiMn"])
    return out


def phi_mn(kv, pu):
    """φMn pada Pu (kN, tekan positif) dari kurva; 0 bila di luar kurva (Pu > φPn,maks atau tarik > φTn)."""
    if pu > kv["phiPn_maks"] + 1e-6 or pu < -kv["phiTn"] - 1e-6:
        return 0.0
    p, m = np.append(kv["phiPn"], -kv["phiTn"]), np.append(kv["phiMn"], 0.0)
    best = 0.0
    for i in range(len(p) - 1):
        lo, hi = sorted((p[i], p[i + 1]))
        if lo - 1e-9 <= pu <= hi + 1e-9 and hi > lo:
            best = max(best, m[i] + (m[i + 1] - m[i]) * (pu - p[i]) / (p[i + 1] - p[i]))
    return float(best)


def kasus_tiang(pmax_zona=None):
    """Kasus cek tiang: (nama, Pu kN, M kNm, jenis). Asumsi kombinasi di md: statis+seret Pu = 1,3 Pmax layan + 1,2 Qn (rasio Pu/Pmax 5.6 ≈ 1,3;
    seret sebagai beban mati tetap); gempa tidak digabung dengan Qn (6.2, GEC10 hal. 332)."""
    pmz = pmax_zona or pmax_per_zona()
    k = [("Statis + seret selatan: 1,3 Pmax + 1,2 Qn", 1.3 * pmz["SELATAN"] + 1.2 * QN["SELATAN"], 0.0, "aksial"),
         ("Statis + seret utara: 1,3 Pmax + 1,2 Qn", 1.3 * pmz["UTARA"] + 1.2 * QN["UTARA"], 0.0, "aksial"),
         ("Gempa Pu 1.560 + inersia utara 177", P_E, M_INERSIA_UTARA, "pm"),
         ("Gempa Pu 1.560 + Youd 966", P_E, M_YOUD, "pm"),
         ("Gempa Pu 3.230 + inersia 177", PU_E, M_INERSIA_UTARA, "pm"),
         ("Gempa Pu 3.230 + Youd 966", PU_E, M_YOUD, "pm"),
         ("Gempa Pu 3.254 (Cap D) + inersia utara 177", PU_D, M_INERSIA_UTARA, "pm"),
         ("Tarik Pu min -1.452 (Cap D)", PU_TARIK, 0.0, "tarik"),
         ("Tarik -1.452 + inersia 177", PU_TARIK, M_INERSIA_UTARA, "pm")]
    return k


def pmax_per_zona():
    ck, ci = tl.rancang("a")
    out = {"SELATAN": 0.0, "UTARA": 0.0}
    for c in ck + ci:
        out[c["zona"]] = max(out[c["zona"]], c["r"]["P_layan"])
    return out


def cek_tiang(fc, n, db=DB):
    kv = pm_kurva(fc, n, db)
    pmz = pmax_per_zona()
    rows = []
    for nama, pu, m, jenis in kasus_tiang(pmz):
        pm = phi_mn(kv, pu)
        if jenis == "aksial":
            rasio = pu / kv["phiPn_maks"]
        elif jenis == "tarik":
            rasio = -pu / kv["phiTn"]
        else:
            rasio = m / pm if pm > 0 else float("inf")
        rows.append(dict(nama=nama, Pu=pu, M=m, jenis=jenis, phiMn=pm, rasio=rasio))
    ast = n * math.pi * db ** 2 / 4
    ok = all(r["rasio"] <= 1.0 for r in rows) and 0.01 * AG <= ast <= 0.06 * AG and n >= 6
    # layan: P / Ag ≤ 0,33 f'c [Asumsi praktik, bukan SNI]
    lay = {z: (pmz[z] + QN[z]) * 1e3 / AG for z in pmz}
    return dict(fc=fc, n=n, kv=kv, rows=rows, layan_ok=True, rasio_maks=max(r["rasio"] for r in rows), lolos=ok, rho=ast / AG,
                layan=lay, layan_batas=0.33 * fc)


def n_min(fc, db=DB):
    n0 = max(6, math.ceil(0.01 * AG / (math.pi * db ** 2 / 4)))
    for n in range(n0, 61):
        r = cek_tiang(fc, n, db)
        if r["lolos"]:
            return n, r
    raise RuntimeError("tidak ada n")


def ld_d25(fc, db=DB):
    """ld tarik lurus = fy db / (1,7 λ √f'c) (Tabel 25.4.2.2, spasi ≥ 2 db dan selimut ≥ db), ≥ 300 mm."""
    return max(300.0, FY * db / (1.7 * math.sqrt(fc)))


def spiral(fc, dsp=DSP):
    asp = math.pi * dsp ** 2 / 4
    dc = D - 2 * SEL
    ach = math.pi * dc ** 2 / 4
    rs_d = 0.45 * (AG / ach - 1) * fc / FYT
    rs_e = 0.12 * fc / FYT
    rs = max(rs_d, rs_e)
    s_rapat = math.floor(min(4 * asp / (dc * rs), 150.0) / 5) * 5       # s ≤ min(¼ D, 6 db, so ≤ 150): ρs menentukan
    s_luar = math.floor(min(4 * asp / (dc * rs_e), 150.0, 75 + dsp) / 5) * 5
    return dict(asp=asp, dc=dc, ach=ach, rs_d=rs_d, rs_e=rs_e, rs=rs, s_rapat=s_rapat, s_luar=s_luar,
                bersih_rapat=s_rapat - dsp, bersih_luar=s_luar - dsp,
                rs_pasang_rapat=4 * asp / (dc * s_rapat), rs_pasang_luar=4 * asp / (dc * s_luar))


def zona_rapat():
    """Panjang zona spiral rapat dari kepala: 18.13.4.3 a) max(5 D, 1,8 m); SNI 1726 7.13.8.3.3 sampai dasar U5 + 7 D."""
    a = max(5 * D / 1e3, 1.8)
    out = {}
    for z, e in U5_DASAR.items():
        b = KEPALA - (e - 7 * D / 1e3)
        out[z] = dict(a=a, b=b, rapat=max(a, b), elev=KEPALA - max(a, b))
    return out


def panjang_tulangan(fc):
    """(a) tiang di cap inti (tarik): penuh sampai ujung; (b) cap kolom (tekan): sampai bidang netral pasca-likuifaksi terdalam (-16,72) - ld
    (usulan AI; aturan max(-16,72; dasar U5 - 7D) mengambil yang lebih dalam = -16,72); (c) penuh semua."""
    ld = ld_d25(fc)
    elev_b = min(NP2["SELATAN"], U5_DASAR["SELATAN"] - 7 * D / 1e3) - ld / 1e3
    return dict(ld=ld, penuh=KEPALA - UJUNG, elev_b=elev_b, L_b=KEPALA - elev_b)


def geser_tiang(fc, n, nu=P_E):
    """Vc = 0,17 (1 + Nu / 14 Ag) λ √f'c bw d, bw = D, d = 0,8 D (22.5.2.2, 22.5.6.1); Vs = Av fyt d / s, Av = 2 Asp; φ 0,75."""
    bw, d = D, 0.8 * D
    vc = 0.17 * (1 + nu * 1e3 / (14 * AG)) * math.sqrt(fc) * bw * d / 1e3
    sp = spiral(fc)
    vs = {k: 2 * sp["asp"] * FYT * d / sp[k] / 1e3 for k in ("s_rapat", "s_luar")}
    return dict(Vc=vc, phiVc=0.75 * vc, Vs=vs, phiVn={k: 0.75 * (vc + v) for k, v in vs.items()},
                rasio_youd=V_YOUD / (0.75 * vc), rasio_inersia=V_INERSIA / (0.75 * vc), Nu=nu)


def tiang(fc):
    n, r = n_min(fc)
    r16 = cek_tiang(fc, 16)
    return dict(fc=fc, n_min=n, cek_min=r, cek16=r16, spiral=spiral(fc), panjang=panjang_tulangan(fc), geser=geser_tiang(fc, n),
                geser16=geser_tiang(fc, 16), rapat=zona_rapat(), ec=ec(fc))


# ================================================================== B. pile cap kolom
BC = 800.0          # mm, kolom konservatif (Ringkasan 5.6: K-P 750; Stek Kolom: 0,8 m)
H_STEK_MIN = 488.3  # mm, kait sloof SL-1 (5.6 Angkur Sloof Inti)
LDH_KP = 426.0      # mm, kait kolom K-P D25 (f'c 35, 5.6 Stek Kolom)
DB_CAP = 32.0       # mm, tulangan bawah cap D32 [Asumsi 5.6]
FC_CAP = 35.0
TEBAL_PILIHAN = [700 + 50 * i for i in range(11)]       # 700 ... 1.200 mm


def d_efektif(h, db=DB_CAP):
    return h - SEL - 1.5 * db       # dua lapis tulangan silang: pusat rata-rata 1,5 db dari sisi bawah (konservatif)


def frak_tiang(jarak_ke_penampang_m, dt=D / 1e3):
    """13.4.2.5: jarak = pusat tiang - penampang (+ bila di luar penampang). Penuh bila ≥ dt/2 di luar, nol bila ≥ dt/2 di dalam."""
    return max(0.0, min(1.0, (jarak_ke_penampang_m + dt / 2) / dt))


def vc_pons(fc, bo, d, beta, sisi):
    a_s = {4: 40, 3: 30, 2: 20}.get(sisi, 20)
    s = math.sqrt(fc)
    return min(0.33 * s, 0.17 * (1 + 2 / beta) * s, 0.083 * (2 + a_s * d / bo) * s)      # MPa (m/mm konsisten: d dan bo satuan sama)


def geser_satu_arah(pos, titik, ru, ukuran, fc, h, bc=BC):
    """Penampang kritis di d dari muka kolom (22.5, 13.2.7.2), tiap arah dan sisi. Mengembalikan (Vu, φVc, rasio, arah) terbesar."""
    d = d_efektif(h) / 1e3
    w, dpt = ukuran                       # panjang x dan y cap (m)
    cx, cy = titik
    best = None
    for ar, (lebar) in ((0, dpt), (1, w)):
        for sg in (1, -1):
            xs = sg * (bc / 2e3 + d)
            vu = 0.0
            for p, r in zip(pos, ru):
                rel = (p[ar] - (cx, cy)[ar]) * sg
                vu += r * frak_tiang(rel - (bc / 2e3 + d))
            pvc = 0.75 * 0.17 * math.sqrt(fc) * lebar * 1e3 * d      # kN (MPa × m × m × 1e3)
            ras = vu / pvc if pvc else float("inf")
            if best is None or ras > best["rasio"]:
                best = dict(Vu=vu, phiVc=pvc, rasio=ras, arah="xy"[ar], b=lebar, d=d)
    return best


def pons_kolom(pos, titik, ru, ukuran, fc, h, bc=BC):
    d = d_efektif(h) / 1e3
    cx, cy = titik
    w, dpt = ukuran
    xmin, xmax, ymin, ymax = cx - w / 2, cx + w / 2, cy - dpt / 2, cy + dpt / 2
    # cap tidak simetris terhadap kolom? posisi cap = pusat pos
    p = np.array(pos)
    xmin, xmax = p[:, 0].min() - 0.8, p[:, 0].max() + 0.8
    ymin, ymax = p[:, 1].min() - 0.8, p[:, 1].max() + 0.8
    a = bc / 2e3 + d / 2
    sisi, bo = 0, 0.0
    for (x0, y0, x1, y1) in ((cx + a, cy - a, cx + a, cy + a), (cx - a, cy - a, cx - a, cy + a),
                             (cx - a, cy + a, cx + a, cy + a), (cx - a, cy - a, cx + a, cy - a)):
        if x0 == x1:
            ok = xmin <= x0 <= xmax
            ln = max(0.0, min(y1, ymax) - max(y0, ymin))
        else:
            ok = ymin <= y0 <= ymax
            ln = max(0.0, min(x1, xmax) - max(x0, xmin))
        if ok and ln > 0:
            sisi += 1
            bo += ln
    vu = sum(r * frak_tiang(max(abs(q[0] - cx), abs(q[1] - cy)) - a) for q, r in zip(pos, ru))
    vc = vc_pons(fc, bo, d, 1.0, sisi)
    pvc = 0.75 * vc * bo * d * 1e3
    return dict(Vu=vu, phiVc=pvc, rasio=vu / pvc, bo=bo, sisi=sisi, vc=vc, a=a)


def pons_tiang(ru, jarak_tepi, fc, h):
    """Pons satu tiang Ø800 (perimeter lingkaran r = D/2 + d/2, terpotong tepi cap; tiang sudut: dua tepi)."""
    d = d_efektif(h) / 1e3
    r = D / 2e3 + d / 2
    cut = sum(2 * math.acos(e / r) for e in jarak_tepi if e < r)
    bo = r * (2 * math.pi - cut)
    sisi = 4 - sum(1 for e in jarak_tepi if e < r)
    vc = vc_pons(fc, bo, d, 1.0, sisi)
    pvc = 0.75 * vc * bo * d * 1e3
    return dict(Vu=ru, phiVc=pvc, rasio=ru / pvc, bo=bo, sisi=sisi, vc=vc, r=r)


def as_lentur(mu, b, d, fc, fy=FY):
    """As (mm2) untuk Mu (kNm) lebar b (m), d (m), φ 0,9; blok persegi."""
    if mu <= 0:
        return 0.0
    k = mu * 1e6 / (0.9 * 0.85 * fc * b * 1e3 * (d * 1e3) ** 2)
    if k >= 0.5:
        return float("inf")
    return 0.85 * fc * b * 1e3 * d * 1e3 / fy * (1 - math.sqrt(1 - 2 * k))


def lentur_cap(pos, titik, ru, ukuran, fc, h, bc=BC):
    d = d_efektif(h) / 1e3
    p = np.array(pos)
    cx, cy = titik
    res = {}
    for ar, nm in ((0, "x"), (1, "y")):
        mu = max(sum(r * ((q[ar] - (cx, cy)[ar]) * sg - bc / 2e3) for q, r in zip(pos, ru) if (q[ar] - (cx, cy)[ar]) * sg > bc / 2e3)
                 for sg in (1, -1))
        lebar = (p[:, 1 - ar].max() - p[:, 1 - ar].min()) + 1.6
        ap = as_lentur(mu, lebar, d, fc)
        amin = 0.0018 * lebar * 1e3 * h
        tepi = (p[:, ar].max() - (cx, cy)[ar]) + 0.8
        res[nm] = dict(Mu=mu, b=lebar, As_lentur=ap, As_min=amin, As=max(ap, amin), n32=math.ceil(max(ap, amin) / (math.pi * DB_CAP ** 2 / 4)),
                       ld=FY * DB_CAP / (1.7 * math.sqrt(fc)), tersedia=(tepi - SEL / 1e3 - bc / 2e3) * 1e3)
    return res


def desain_cap(c, h, fc=FC_CAP):
    t = c["titik"][0]
    pos, n = c["pos"], c["r"]["n"]
    ru = [c["r"]["sumPu"] / n] * n
    uk = c["ukuran"]
    sx = geser_satu_arah(pos, (t["x"], t["y"]), ru, uk, fc, h)
    pk = pons_kolom(pos, (t["x"], t["y"]), ru, uk, fc, h)
    ptp = []
    pa = np.array(pos)
    for q, r in zip(pos, ru):
        e = (q[0] - pa[:, 0].min() + 0.8, pa[:, 0].max() - q[0] + 0.8, q[1] - pa[:, 1].min() + 0.8, pa[:, 1].max() - q[1] + 0.8)
        ptp.append(pons_tiang(r, e, fc, h))
    pt = max(ptp, key=lambda z: z["rasio"])
    lt = lentur_cap(pos, (t["x"], t["y"]), ru, uk, fc, h)
    d = d_efektif(h)
    stek = dict(h_min=max(H_STEK_MIN, LDH_KP + SEL + 2 * DB_CAP), tersedia=h - SEL - 2 * DB_CAP)
    ok = (sx["rasio"] <= 1 and pk["rasio"] <= 1 and pt["rasio"] <= 1 and h >= stek["h_min"] and d >= 300
          and all(v["tersedia"] >= v["ld"] for v in lt.values() if v["Mu"] > 0))
    rasio = max(sx["rasio"], pk["rasio"], pt["rasio"])
    penentu = max((("geser satu arah", sx["rasio"]), ("pons kolom", pk["rasio"]), ("pons tiang", pt["rasio"])), key=lambda z: z[1])[0]
    return dict(id=c["id"], n=n, ukuran=uk, h=h, d=d, Ru=ru[0], geser=sx, pons_kolom=pk, pons_tiang=pt, lentur=lt, stek=stek,
                lolos=ok, rasio=rasio, penentu=penentu)


def pilih_cap_tipikal(ck):
    out = {}
    for n in (2, 3, 4):
        cs = [c for c in ck if c["r"]["n"] == n]
        out[n] = max(cs, key=lambda c: c["r"]["sumPu"] / n)
    return out


def cap_kolom_semua(ck=None):
    ck = ck or tl.rancang("a")[0]
    tip = pilih_cap_tipikal(ck)
    res = {}
    for n, c in tip.items():
        daftar = [desain_cap(c, h) for h in TEBAL_PILIHAN]
        usul = next((x for x in daftar if x["lolos"]), daftar[-1])
        res[n] = dict(cap=c, daftar=daftar, usul=usul, h1000=desain_cap(c, 1000.0), h1200=desain_cap(c, 1200.0))
    return res


# ================================================================== C. cap inti
H_INTI = 1200.0
H_E = tl.H_E * 1e3           # tebal Cap E: usulan Defsa 22 Nov 2026 (pelat), terbukti lolos di tahap6_cap_pelat (1.500 gagal)
INTI_LIF_BOX = (52.0, 56.0, 35.0, 43.0)      # x0, x1, y0, y1 m: kotak inti lif [Asumsi dari 5.5 pit x 51,10-56,90 dan 5.6 butir 6: kolom (52,35), (52,43) pada garis dinding]
T_DINDING = 0.35                              # m, 5.6 Angkur Sloof Inti
Z_RASIO = 0.85                                # lengan STM z = 0,85 d [Asumsi]
BETA_S, BETA_N_TIANG, BETA_N_KOL = 0.60, 0.60, 1.0     # 13.4.2.4 (βs 0,60 λ); nodal dua tie atau lebih; CCC
LB_TIANG = math.sqrt(math.pi * (D / 1e3) ** 2 / 4)     # m, lebar persegi ekuivalen tiang


def muatan_tiang_cap(c, berat=True):
    """Reaksi tiang (kN) tiap tiang: kombinasi pemberi Pu maks (tekan) dan kombinasi pemberi Pu min (tarik)."""
    titik, pos = c["titik"], c["pos"]
    uls = [(t["x"], t["y"], t["Pu"]) for t in titik]
    umin = [(t["x"], t["y"], t["Pumin"]) for t in titik]
    r_ = c["r"]
    if berat and r_.get("W"):       # berat cap 6.3 (revisi 22 Nov 2026): 1,2 W untuk Pu maks, 0,9 W untuk Pu min, di pusat telapak
        uls.append((r_["xc"], r_["yc"], r_["Wu"]))
        umin.append((r_["xc"], r_["yc"], r_["Wm"]))
    mux, muy = sum(abs(t["Mux"]) for t in titik), sum(abs(t["Muy"]) for t in titik)
    mak = [tl.beban_tiang(pos, uls, sx * mux, sy * muy) for sx, sy in tl.TANDA]
    mik = [tl.beban_tiang(pos, umin, sx * mux, sy * muy) for sx, sy in tl.TANDA]
    i1, i2 = int(np.argmax([m.max() for m in mak])), int(np.argmin([m.min() for m in mik]))
    c["_tanda"] = (tl.TANDA[i1], tl.TANDA[i2], mux, muy)
    return (mak[i1], mik[i2], uls, umin)


def stm_cap(c, h=H_INTI, fc=FC_CAP):
    """STM per tiang: tiap tiang dihubungkan dengan strut langsung ke titik beban terdekat; tie horizontal Hi = Ri li / z.
    Strut dalam STM hanya bila θ ≥ 25° (23.2.7); di luar itu cap bekerja sebagai balok/pelat (lentur dan geser, bukan STM)."""
    R, Rmin, uls, umin = muatan_tiang_cap(c, berat=False)      # STM global lama (pembanding): tanpa berat cap
    pos = np.array(c["pos"])
    loads = [(t["x"], t["y"], t["Pu"], t["nama"]) for t in c["titik"]]
    d = d_efektif(h) / 1e3
    z = Z_RASIO * d
    hta = 2 * (h - d * 1e3) / 1e3                  # m, tinggi zona angkur tie
    a_top = 2 * (d - z)                            # m, kedalaman nodal atas
    fce_s = 0.85 * BETA_S * fc                     # MPa
    fce_n = 0.85 * BETA_N_TIANG * fc
    fce_c = 0.85 * BETA_N_KOL * fc
    ap = math.pi * (D / 1e3) ** 2 / 4
    box = INTI_LIF_BOX
    a_node = {}
    for t in c["titik"]:
        a_node[t["nama"]] = (2 * (box[1] - box[0] + box[3] - box[2]) * T_DINDING) if t["nama"] == "INTI-LIF" else (BC / 1e3) ** 2
    rows = []
    for i, (q, r) in enumerate(zip(pos, R)):
        j = int(np.argmin([math.hypot(q[0] - l[0], q[1] - l[1]) for l in loads]))
        li = math.hypot(q[0] - loads[j][0], q[1] - loads[j][1])
        th = math.degrees(math.atan2(z, li)) if li > 1e-9 else 90.0
        ada = th >= 25.0 and r > 0
        row = dict(i=i, x=float(q[0]), y=float(q[1]), R=float(r), node=loads[j][3], li=li, theta=th, stm=ada)
        if ada:
            s = math.sin(math.radians(th))
            ws = LB_TIANG * s + hta * math.cos(math.radians(th))
            acs = ws * LB_TIANG
            row["F"] = r / s
            row["phiFns"] = 0.75 * fce_s * acs * 1e3
            row["r_strut"] = row["F"] / row["phiFns"]
            row["r_tiang"] = r / (0.75 * fce_n * ap * 1e3)
        rows.append(row)
    # beban per node dan cek tumpu kolom
    nod = {}
    for rw in rows:
        if rw["stm"]:
            nod[rw["node"]] = nod.get(rw["node"], 0.0) + rw["R"]
    r_node = {k: v / (0.75 * fce_c * a_node[k] * 1e3) for k, v in nod.items()}
    # tie: gaya yang menyilang potongan x = xc dan y = yc (strut tiang ke node di sisi seberang)
    def tie(ar, semua=False):
        mak = 0.0
        for xc in np.arange(pos[:, ar].min(), pos[:, ar].max(), 0.1):
            tot = 0.0
            for rw in rows:
                if not (rw["stm"] or (semua and rw["R"] > 0)):
                    continue
                lj = next(l for l in loads if l[3] == rw["node"])
                a, b = (rw["x"], rw["y"])[ar], (lj[0], lj[1])[ar]
                if (a - xc) * (b - xc) < 0:
                    tot += rw["R"] * abs(a - b) / z
            mak = max(mak, tot)
        return mak
    Tx_lok, Ty_lok = tie(0), tie(1)               # tie lokal (strut tiang STM ke node terdekat)
    # pembanding: balok lentur, Mu terbesar atas potongan (semua tiang dan beban)
    (sxm, sym), (sxn, syn), mux_, muy_ = c["_tanda"]
    # momen terpakai pada titik inti (6.3: Mux ditahan sebaran y, Muy sebaran x), tanda sesuai kombinasi pemberi reaksi
    mom_terpakai = {0: lambda l, sg: (sg[1] * muy_) if l[3].startswith("INTI") else 0.0, 1: lambda l, sg: (sg[0] * mux_) if l[3].startswith("INTI") else 0.0}

    def momen(ar):
        mk = 0.0
        for xc in np.arange(pos[:, ar].min() + 0.1, pos[:, ar].max(), 0.1):
            m = sum(Ri * (q[ar] - xc) for q, Ri in zip(pos, R) if q[ar] > xc)                 - sum(l[2] * ((l[0], l[1])[ar] - xc) + mom_terpakai[ar](l, (sxm, sym)) for l in loads if (l[0], l[1])[ar] > xc)
            mk = max(mk, abs(m))
        return mk
    Mx, My = momen(0), momen(1)
    b_x = (pos[:, 1].max() - pos[:, 1].min()) + 1.6
    b_y = (pos[:, 0].max() - pos[:, 0].min()) + 1.6
    As_beam = {"x": as_lentur(Mx, b_x, d, fc), "y": as_lentur(My, b_y, d, fc)}
    Tx, Ty = Mx / z, My / z                        # tie global dari kesetimbangan potongan (rangka STM dalam kesetimbangan): T = M / z
    As_stm = {"x": Tx * 1e3 / (0.75 * FY), "y": Ty * 1e3 / (0.75 * FY)}
    As_stm_semua = As_stm
    # pembanding pada besaran gaya tarik (tanpa φ): T STM = M / z vs T balok = Mu / (d - a/2), a dari As_beam
    lebar = {"x": b_x, "y": b_y}
    Tstm = {"x": Tx, "y": Ty}
    T_balok = {k: (M_ / ((d * 1e3 - As_beam[k] * FY / (0.85 * fc * lebar[k] * 1e3) / 2) / 1e3)) for k, M_ in (("x", Mx), ("y", My))}
    # tarik (tiang tarik): momen balik atas
    def momen_min(ar):
        mk = 0.0
        for xc in np.arange(pos[:, ar].min() + 0.1, pos[:, ar].max(), 0.1):
            lm = [(t["x"], t["y"], t["Pumin"], t["nama"]) for t in c["titik"]]
            m = sum(Ri * (q[ar] - xc) for q, Ri in zip(pos, Rmin) if q[ar] > xc)                 - sum(l[2] * ((l[0], l[1])[ar] - xc) + mom_terpakai[ar](l, (sxn, syn)) for l in lm if (l[0], l[1])[ar] > xc)
            mk = max(mk, abs(m))
        return mk
    Mt = {"x": momen_min(0), "y": momen_min(1)}
    As_atas = {"x": as_lentur(Mt["x"], b_x, d, fc), "y": as_lentur(Mt["y"], b_y, d, fc)}
    # geser satu arah global dan pons inti
    gs = geser_global(c, R, loads, h, fc)
    pi = pons_inti(c, R, h, fc)
    st = [rw for rw in rows if rw["stm"]]
    rasio_stm = max([rw["r_strut"] for rw in st] + [rw["r_tiang"] for rw in st] + list(r_node.values()) + [0.0])
    return dict(rows=rows, z=z, d=d, hta=hta, a_top=a_top, fce_s=fce_s, fce_n=fce_n, n_stm=len(st), n_luar=len(rows) - len(st),
                n_tarik=int(sum(1 for r in R if r < 0)), Tx=Tx, Ty=Ty, Mx=Mx, My=My, As_stm=As_stm, As_beam=As_beam, Mt=Mt, As_atas=As_atas,
                r_node=r_node, rasio_stm=rasio_stm, geser=gs, pons=pi, R=R, Rmin=Rmin, tie_max=max(Tx, Ty),
                Tx_lokal=Tx_lok, Ty_lokal=Ty_lok, As_stm_semua=As_stm_semua,
                T_balok=T_balok, dev_stm_beam=max(abs(Tstm[k] - T_balok[k]) / T_balok[k] * 100 for k in ("x", "y") if T_balok[k] > 0), d_ls=a_top)


def geser_global(c, R, loads, h, fc):
    """Geser satu arah: potongan vertikal/horizontal pada jarak ≥ d dari muka beban; V = Σ reaksi tiang (13.4.2.5) - Σ beban di satu sisi."""
    pos = np.array(c["pos"])
    d = d_efektif(h) / 1e3
    best = dict(rasio=0.0)
    for ar in (0, 1):
        b = (pos[:, 1 - ar].max() - pos[:, 1 - ar].min()) + 1.6
        pvc = 0.75 * 0.17 * math.sqrt(fc) * b * 1e3 * d
        for xc in np.arange(pos[:, ar].min() - 0.7, pos[:, ar].max() + 0.7, 0.1):
            if any(abs(((l[0], l[1])[ar]) - xc) < BC / 2e3 + d for l in loads):
                continue
            v = sum(Ri * frak_tiang(q[ar] - xc) for q, Ri in zip(pos, R) if Ri > 0 and q[ar] > xc) \
                - sum(l[2] for l in loads if (l[0], l[1])[ar] > xc)
            v = abs(v) if v > 0 else abs(v)
            if v / pvc > best["rasio"]:
                best = dict(rasio=v / pvc, Vu=v, phiVc=pvc, arah="xy"[ar], xc=float(xc), b=b)
    return best


def pons_inti(c, R, h, fc):
    """Pons kotak inti lif: keliling kotak (dinding 0,35) + d/2 tiap sisi, terpotong tepi cap; Vu = Σ reaksi tiang di luar perimeter (13.4.2.5)."""
    d = d_efektif(h) / 1e3
    pos = np.array(c["pos"])
    xmin, xmax = pos[:, 0].min() - 0.8, pos[:, 0].max() + 0.8
    ymin, ymax = pos[:, 1].min() - 0.8, pos[:, 1].max() + 0.8
    x0, x1, y0, y1 = INTI_LIF_BOX
    a = d / 2
    ring = ((x0 - a, y0 - a, x1 + a, y0 - a), (x0 - a, y1 + a, x1 + a, y1 + a), (x0 - a, y0 - a, x0 - a, y1 + a), (x1 + a, y0 - a, x1 + a, y1 + a))
    bo, sisi = 0.0, 0
    for (xa, ya, xb, yb) in ring:
        if xa == xb:
            ok = xmin <= xa <= xmax
            ln = max(0.0, min(yb, ymax) - max(ya, ymin))
        else:
            ok = ymin <= ya <= ymax
            ln = max(0.0, min(xb, xmax) - max(xa, xmin))
        if ok and ln > 0:
            bo += ln
            sisi += 1

    def sd(q):      # jarak bertanda ke persegi panjang (+ di luar perimeter pada offset a)
        dx = max(x0 - q[0], 0.0, q[0] - x1)
        dy = max(y0 - q[1], 0.0, q[1] - y1)
        return max(dx, dy) - a if (dx > 0 or dy > 0) else -(a + min(q[0] - x0, x1 - q[0], q[1] - y0, y1 - q[1]))
    vu = sum(r * frak_tiang(sd(q)) for q, r in zip(pos, R) if r > 0)
    beban = sum(t["Pu"] for t in c["titik"] if t["nama"] == "INTI-LIF")
    vc = vc_pons(fc, bo, d, 2.0, sisi)     # β = 2,0 (sisi panjang / sisi pendek 8 / 4)
    pvc = 0.75 * vc * bo * d * 1e3
    return dict(Vu=vu, phiVc=pvc, rasio=vu / pvc, bo=bo, sisi=sisi, vc=vc, beban=beban)


def cap_inti_semua(ci=None):
    ci = ci or tl.rancang("a")[1]
    out = []
    for c in ci:
        R, Rmin, _, _ = muatan_tiang_cap(c)
        pa = np.array(c["pos"])
        rmax = float(R.max())
        e = (0.8, 0.8)            # tiang sudut: dua tepi 0,8 m
        pt = pons_tiang(rmax, e, FC_CAP, H_E if c["kode"] == "E" else H_INTI)
        out.append(dict(id=c["id"], n=c["r"]["n"], ukuran=c["ukuran"], Pu_maks=rmax, Pu_min=float(Rmin.min()), pons_tiang=pt, rasio=pt["rasio"]))
    return out


# ================================================================== D. pit
PIT = dict(
    A=5.8 * 6.8,                   # m2, tapak luar L-1..4 (bukaan 5,2 x 6,2 + dinding 0,30)
    W={0.40: 601.7, 0.45: 648.3},  # kN, 5.5 (opsi A dipakai 0,45)
    muka_air=12.31,                # Q100
    bawah={0.40: 10.85, 0.45: 10.80},
    x=(51.10, 56.90), y=(35.60, 42.40),
    fy=FY,
)


def pit(cap_e=None):
    ci = cap_e or next(c for c in tl.rancang("a")[1] if c["kode"] == "E")
    pa = np.array(ci["pos"])
    x_tepi = pa[:, 0].max() + 0.8
    out = {}
    for t in (0.40, 0.45):
        h = PIT["muka_air"] - PIT["bawah"][t]
        u = 9.81 * h
        U = u * PIT["A"]
        W = PIT["W"][t]
        R = max(0.0, 1.5 * U - W)
        out[t] = dict(t=t, h=h, u=u, U=U, W=W, FK=W / U, ok_a=W / U >= 1.1, R=R, As=1.6 * R * 1e3 / (0.9 * PIT["fy"]),
                      FK_b=(W + R) / U)
    x0, x1 = PIT["x"]
    menjorok = max(0.0, x1 - x_tepi)
    dalam = (min(x1, x_tepi) - x0) / (x1 - x0)
    out["geom"] = dict(x_tepi=x_tepi, menjorok=menjorok, frak_dalam=dalam, R_luar=out[0.40]["R"] * (1 - dalam),
                       dasar_pit=PIT["bawah"][0.45], dasar_cap=12.05 - H_E / 1e3, atas_cap=12.05)
    return out


# ================================================================== E. sloof
SLOOF = {   # data 5.4 (Desain Sloof, Lentur Gravitasi, Kapasitas)
    "SL-2": dict(ukuran="400 × 800", tul="6 D29 / 4 D29", Mgrav_neg=363.1, Mgrav_pos=249.9, phiMn_neg=978.1, phiMn_pos=675.0, M_pen=383.0, Vgrav=234.1),
    "SL-3": dict(ukuran="400 × 800", tul="11 D22 / 5 D29", Mgrav_neg=364.2, Mgrav_pos=260.5, phiMn_neg=1012.9, phiMn_pos=829.2, M_pen=383.0, Vgrav=237.3),
}
M_SL1_PENURUNAN = 545.0
RASIO_SL1 = 0.65


def sloof():
    out = {}
    for k, v in SLOOF.items():
        mu = v["Mgrav_neg"] + v["M_pen"]
        r_neg, r_pos = mu / v["phiMn_neg"], v["Mgrav_pos"] / v["phiMn_pos"]
        extra = max(0.0, (mu - v["phiMn_neg"]) / v["phiMn_neg"])       # tambahan relatif bila > 1 (mendekati proporsional As)
        out[k] = dict(v, Mu_neg=mu, r_neg=r_neg, r_pos=r_pos, rasio=max(r_neg, r_pos), V=v["Vgrav"] + 2 * v["M_pen"] / 8.0, tambah=extra)
    return out


# ================================================================== semua
def semua():
    ck, ci = tl.rancang("a")
    h = dict(tiang={fc: tiang(fc) for fc in FC_VARIAN}, cap_kolom=cap_kolom_semua(ck), inti=cap_inti_semua(ci), pit=pit(), sloof=sloof())
    ce = next(c for c in ci if c["kode"] == "E")
    h["stm_E"] = stm_cap(ce, H_E)
    h["cap_E"] = ce
    import tahap6_cap_pelat as cp
    h["pelat"] = cp.semua(ce)
    h["pelat_E"] = h["pelat"]["hasil"][H_E]
    h["tebal_E"] = {}
    for ht in (1200.0, 1500.0, 1800.0, 2000.0):
        q = stm_cap(ce, ht)
        pa = np.array(ce["pos"])
        bx, by = (pa[:, 1].max() - pa[:, 1].min()) + 1.6, (pa[:, 0].max() - pa[:, 0].min()) + 1.6
        h["tebal_E"][ht] = dict(h=ht, d=q["d"], rasio_stm=q["rasio_stm"], As_x=q["As_beam"]["x"], As_y=q["As_beam"]["y"],
                                rho_x=q["As_beam"]["x"] / (bx * 1e3 * q["d"] * 1e3), rho_y=q["As_beam"]["y"] / (by * 1e3 * q["d"] * 1e3),
                                geser=q["geser"]["rasio"], pons=q["pons"]["rasio"], n_stm=q["n_stm"], dev=q["dev_stm_beam"])
    h["pmax_zona"] = pmax_per_zona()
    return h


# ================================================================== Excel
def buat_excel(keluar=BERKAS, h=None):
    import openpyxl
    from format_dokumen import AI, ISIAN, Lembar, set_font_bawaan
    h = h or semua()
    wb = openpyxl.Workbook()
    set_font_bawaan(wb)
    wb.remove(wb.active)
    ket = LABEL + " " + LABEL_AI
    adr = {}

    lp = Lembar(wb.create_sheet("Petunjuk"), 1, "Petunjuk dan daftar lembar", [26, 100])
    lp.catatan(f"STATUS: {STATUS}. " + ket)
    lp.kosong()
    lp.bagian("A", "Isi lembar")
    lp.tabel(["Lembar", "Isi"], [
        ["Ringkasan", "Hasil kunci: tulangan tiang dua f'c, tebal cap per tipe, STM Cap E, pit, sloof"],
        ["Tiang", "Tiang Ø800 f'c 30 dan 35: Ag, Ast, Po, φPn,maks, φTn, ld, spiral (rumus hidup); cek P-M per kasus; geser"],
        ["Interaksi", "Titik diagram interaksi P-M (nilai dari skrip, serat penampang lingkaran)"],
        ["Cap Kolom", "Cap 4 tiang (rumus hidup: geser satu arah, pons kolom, pons tiang, lentur) dan tebal terkecil per tipe 2/3/4"],
        ["Cap Inti", "Cap E (gabungan Cap C + Cap E): STM per tiang, tie, nodal; pembanding balok lentur; pons inti; enam cap inti (pons tiang)"],
        ["Pit", "Pit L-1..4 varian A dan B (rumus hidup), temuan letak terhadap Cap E"],
        ["Sloof", "SL-2 dan SL-3 pada δ 24,6 mm (rumus hidup)"],
        ["Verifikasi", "T-105"],
        ["Acuan", "Pasal dan halaman"],
        ["Keputusan", "Hal yang perlu diputuskan Defsa"]], rata=["l", "l"], beku=False)

    # ---- Tiang (rumus hidup)
    lt = Lembar(wb.create_sheet("Tiang"), 3, "Tiang bor Ø800: penampang, kapasitas, spiral", [46, 16, 16, 70])
    lt.catatan(ket)
    lt.kosong()
    lt.bagian("A", "Penampang dan kapasitas aksial (rumus hidup; n D25 dari hasil skrip)")
    t30, t35 = h["tiang"][30.0], h["tiang"][35.0]
    rows = [["f'c (MPa)", 30.0, 35.0, "varian f'c: 30 [Asumsi 6.2]; 35 usulan AI (S2 min 31, Tabel 19.3.2.1)"],
            ["fy = fyt (MPa)", FY, FY, "5.4, 5.5, 5.6"],
            ["Diameter D (mm)", D, D, "6.1"],
            ["Selimut ke spiral (mm)", SEL, SEL, "Tabel 20.6.1.3.1 hal. PDF 482"],
            ["n D25 (terkecil yang lolos semua kasus)", t30["n_min"], t35["n_min"], "skrip `n_min` (cek P-M seluruh kasus, 0,01 Ag ≤ Ast)"],
            ["Ag = π D² / 4 (mm²)", None, None, "rumus hidup"],
            ["Ast = n π 25² / 4 (mm²)", None, None, "rumus hidup"],
            ["ρ = Ast / Ag", None, None, "0,01-0,06 (18.7.4.1); 0,01-0,08 (10.6.1.1)"],
            ["Po = 0,85 f'c (Ag - Ast) + fy Ast (kN)", None, None, "SNI 2847:2019 22.4.2.2 hal. PDF 503"],
            ["φPn,maks = 0,75 × 0,85 Po (kN)", None, None, "22.4.2.1, Tabel 21.2.2 spiral (hal. PDF 503, 493)"],
            ["φTn = 0,9 Ast fy (kN)", None, None, "21.2.1; 18.13.4.1"],
            ["ld tarik lurus D25 = fy db / (1,7 √f'c) (mm)", None, None, "25.4.2.1, Tabel 25.4.2.2 (hal. PDF 587-588)"]]
    r0, a, b = lt.tabel(["Besaran", "f'c 30", "f'c 35", "Sumber"], rows, rata=["l", "r", "r", "l"], fill_kolom={1: AI, 2: AI}, beku=False)
    V = lambda i, k: f"{lt.kol(k)}{r0 + 1 + i}"
    for k in (1, 2):
        lt.ws[V(5, k)] = f"=PI()*{V(2, k)}^2/4"
        lt.ws[V(6, k)] = f"={V(4, k)}*PI()*25^2/4"
        lt.ws[V(7, k)] = f"={V(6, k)}/{V(5, k)}"
        lt.ws[V(8, k)] = f"=(0.85*{V(0, k)}*({V(5, k)}-{V(6, k)})+{V(1, k)}*{V(6, k)})/1000"
        lt.ws[V(9, k)] = f"=0.75*0.85*{V(8, k)}"
        lt.ws[V(10, k)] = f"=0.9*{V(6, k)}*{V(1, k)}/1000"
        lt.ws[V(11, k)] = f"=MAX(300,{V(1, k)}*25/(1.7*SQRT({V(0, k)})))"
        for i in (5, 6, 8, 9, 10, 11):
            lt.ws[V(i, k)].number_format = "#,##0.0"
        lt.ws[V(7, k)].number_format = "0.0000"
    adr["tiang"] = {"phiPn": {30: V(9, 1), 35: V(9, 2)}, "phiTn": {30: V(10, 1), 35: V(10, 2)}, "ld": {30: V(11, 1), 35: V(11, 2)}}
    lt.kosong()
    lt.bagian("B", "Spiral (D13): rumus hidup")
    sp = {30: t30["spiral"], 35: t35["spiral"]}
    rows = [["Diameter spiral (mm)", DSP, DSP, "D13 (D10 menghasilkan jarak bersih < 25 mm)"],
            ["dc = D - 2 × selimut (mm)", None, None, "diameter inti sampai luar spiral"],
            ["Asp = π d² / 4 (mm²)", None, None, "rumus hidup"],
            ["Ach = π dc² / 4 (mm²)", None, None, "rumus hidup"],
            ["ρs (d) = 0,45 (Ag / Ach - 1) f'c / fyt", None, None, "Tabel 18.7.5.4 (d), hal. PDF 411"],
            ["ρs (e) = 0,12 f'c / fyt", None, None, "Tabel 18.7.5.4 (e)"],
            ["s zona rapat (mm) = 4 Asp / (dc ρs), kelipatan 5", None, None, "18.13.4.3, SNI 1726 7.13.8.3.3"],
            ["Jarak bersih zona rapat (mm)", None, None, "25.7.3.1: 25-75 mm"],
            ["s luar zona rapat (mm), ρs (e), ≤ 150 dan ≤ 75 + d", None, None, "usulan AI"]]
    r0b, _, _ = lt.tabel(["Besaran", "f'c 30", "f'c 35", "Sumber"], rows, rata=["l", "r", "r", "l"], fill_kolom={1: AI, 2: AI}, beku=False)
    W = lambda i, k: f"{lt.kol(k)}{r0b + 1 + i}"
    for k, fc in ((1, 30), (2, 35)):
        lt.ws[W(1, k)] = f"={V(2, k)}-2*{V(3, k)}"
        lt.ws[W(2, k)] = f"=PI()*{W(0, k)}^2/4"
        lt.ws[W(3, k)] = f"=PI()*{W(1, k)}^2/4"
        lt.ws[W(4, k)] = f"=0.45*({V(5, k)}/{W(3, k)}-1)*{V(0, k)}/{V(1, k)}"
        lt.ws[W(5, k)] = f"=0.12*{V(0, k)}/{V(1, k)}"
        lt.ws[W(6, k)] = f"=FLOOR(MIN(4*{W(2, k)}/({W(1, k)}*MAX({W(4, k)},{W(5, k)})),150),5)"
        lt.ws[W(7, k)] = f"={W(6, k)}-{W(0, k)}"
        lt.ws[W(8, k)] = f"=FLOOR(MIN(4*{W(2, k)}/({W(1, k)}*{W(5, k)}),150,75+{W(0, k)}),5)"
        for i in (1, 2, 3):
            lt.ws[W(i, k)].number_format = "#,##0.0"
        for i in (4, 5):
            lt.ws[W(i, k)].number_format = "0.00000"
    adr["spiral"] = {"rs_d": {30: W(4, 1), 35: W(4, 2)}, "s_rapat": {30: W(6, 1), 35: W(6, 2)}, "s_luar": {30: W(8, 1), 35: W(8, 2)}}
    lt.kosong()
    lt.bagian("C", "Cek per kasus (n D25 hasil skrip; φMn dari diagram interaksi, lembar Interaksi)")
    rows = []
    for fc, tt in ((30, t30), (35, t35)):
        for r in tt["cek_min"]["rows"]:
            rows.append([f"f'c {fc}: {r['nama']}", r["Pu"], r["M"], r["phiMn"], r["rasio"]])
    lt.tabel(["Kasus", "Pu (kN)", "M (kNm)", "φMn pada Pu (kNm) / φPn,maks / φTn", "Rasio"], rows, rata=["l", "r", "r", "r", "r"],
             fmt=[None, "#,##0", "#,##0", "#,##0.0", "0.000"], fill_kolom={3: AI, 4: AI}, beku=False)
    lt.kosong()
    lt.bagian("D", "16 D25 (usulan awal 6.5) dan panjang tulangan")
    rows = []
    for fc, tt in ((30, t30), (35, t35)):
        r16 = tt["cek16"]
        rows.append([f"f'c {fc}: 16 D25, rasio terbesar", r16["rasio_maks"], "lolos" if r16["lolos"] else "gagal", f"φMn pada 1.560 kN = {idn(next(x for x in r16['rows'] if 'Youd 966' in x['nama'] and '1.560' in x['nama'])['phiMn'], 0)} kNm"])
    for fc, tt in ((30, t30), (35, t35)):
        p = tt["panjang"]
        rows.append([f"f'c {fc}: ld (mm) / penuh (m) / (b) panjang dari kepala (m)", p["ld"], p["penuh"], f"(b) sampai elev. {idn(p['elev_b'], 2)} = {idn(p['L_b'], 2)} m"])
    lt.tabel(["Butir", "Nilai", "Nilai 2", "Keterangan"], rows, rata=["l", "r", "r", "l"], fmt=[None, "#,##0.00", "#,##0.00", None], fill_kolom={1: AI, 2: AI}, beku=False)

    # ---- Interaksi
    li = Lembar(wb.create_sheet("Interaksi"), 4, "Titik diagram interaksi P-M tiang", [18, 18, 18, 18, 18])
    li.catatan(ket + " Serat penampang lingkaran, εcu 0,003, blok β1, φ spiral 0,75-0,90 (Tabel 21.2.2), φPn dibatasi φPn,maks.")
    li.kosong()
    for fc in FC_VARIAN:
        tt = h["tiang"][fc]
        kv = tt["cek_min"]["kv"]
        li.bagian("A" if fc == 30 else "B", f"f'c {int(fc)}: {tt['n_min']} D25 (kurva tiap 25 titik dari 400)")
        idx = list(range(0, len(kv["phiPn"]), 16))
        rows = [[float(kv["phiPn"][i]), float(kv["phiMn"][i]), float(kv["c"][i]), float(kv["et"][i])] for i in idx]
        li.tabel(["φPn (kN)", "φMn (kNm)", "c (mm)", "εt"], rows, rata=["r"] * 4, fmt=["#,##0", "#,##0", "#,##0", "0.0000"], fill_kolom={0: AI, 1: AI, 2: AI, 3: AI}, beku=False)
        li.kosong()

    # ---- Cap Kolom (cap 4 tiang rumus hidup)
    lc = Lembar(wb.create_sheet("Cap Kolom"), 5, "Pile cap kolom: cap 4 tiang (rumus hidup) dan tebal per tipe", [46, 16, 16, 16, 62])
    lc.catatan(ket)
    lc.kosong()
    c4 = h["cap_kolom"][4]
    cp4 = c4["cap"]
    pos4 = np.array(cp4["pos"])
    cx, cy = cp4["titik"][0]["x"], cp4["titik"][0]["y"]
    hh = c4["h1000"]["h"]
    lc.bagian("A", f"Cap 4 tiang ({cp4['id']}) pada h = 1.000 mm, f'c 35: masukan dan hasil")
    ru = c4["h1000"]["Ru"]
    rows = [["Tebal h (mm)", hh, None, None, "usulan awal Defsa 1.000"],
            ["f'c cap (MPa)", FC_CAP, None, None, "5.6 [Asumsi]; S2 ≥ 31"],
            ["Selimut (mm)", SEL, None, None, "Tabel 20.6.1.3.1"],
            ["Tulangan bawah D (mm)", DB_CAP, None, None, "5.6 [Asumsi]"],
            ["d = h - selimut - 1,5 D (mm)", None, None, None, "dua lapis silang, konservatif; 13.4.2.1 ≥ 300"],
            ["Kolom bc (mm)", BC, None, None, "800 konservatif; Ringkasan 5.6 memakai 750"],
            ["Diameter tiang (m)", D / 1e3, None, None, "6.1"],
            ["Pu cap (kN)", cp4["r"]["sumPu"], None, None, f"{cp4['id']} (6.3)"],
            ["Ru = Pu / 4 (kN)", None, None, None, "kepala sendi, M = 0"],
            ["Jarak tiang ke pusat kolom (m)", float(abs(pos4[0][0] - cx)), None, None, "tiang pada ±1,2 m"],
            ["Lebar cap tegak lurus potongan (m)", float(cp4["ukuran"][1]), None, None, "6.3"],
            ["Jarak tepi tiang ke tepi cap (m)", 0.8, None, None, "6.3 (tepi 0,80 m)"]]
    r0, a, b = lc.tabel(["Besaran", "Nilai", "", "", "Sumber"], rows, rata=["l", "r", "r", "r", "l"], fill_kolom={1: AI}, beku=False)
    X = lambda i: f"{lc.kol(1)}{r0 + 1 + i}"
    lc.ws[X(4)] = f"={X(0)}-{X(2)}-1.5*{X(3)}"
    lc.ws[X(8)] = f"={X(7)}/4"
    lc.kosong()
    lc.bagian("B", "Geser satu arah (22.5.5.1; 13.4.2.5), pons kolom (22.6), pons tiang, lentur (rumus hidup)")
    rows = [["d (m)", None, None, None, ""],
            ["Penampang kritis dari pusat kolom (m) = bc/2 + d", None, None, None, "13.2.7.2"],
            ["Fraksi reaksi tiang di penampang = (jarak + Dt/2) / Dt, batas 0-1", None, None, None, "13.4.2.5 (jarak pusat tiang - penampang, + di luar)"],
            ["Vu = 2 tiang × fraksi × Ru (kN)", None, None, None, ""],
            ["φVc = 0,75 × 0,17 √f'c b d (kN)", None, None, None, "22.5.5.1, φ 0,75"],
            ["Rasio geser satu arah", None, None, None, ""],
            ["a = bc/2 + d/2 (m)", None, None, None, "22.6.4.1"],
            ["bo = 4 (bc + d) (m)", None, None, None, "empat sisi, di dalam cap"],
            ["Fraksi tiang pada perimeter pons", None, None, None, "jarak Chebyshev - a"],
            ["Vu pons = 4 × fraksi × Ru (kN)", None, None, None, ""],
            ["vc = min(0,33; 0,17 (1 + 2/β); 0,083 (2 + 40 d / bo)) √f'c (MPa)", None, None, None, "22.6.5.2, β 1, αs 40"],
            ["φVc pons = 0,75 vc bo d (kN)", None, None, None, ""],
            ["Rasio pons kolom", None, None, None, ""],
            ["Mu di muka kolom = 2 Ru (jarak - bc/2) (kNm)", None, None, None, "13.2.7.1, 13.4.2.2"],
            ["As perlu lentur (mm²)", None, None, None, "φ 0,9, blok persegi"],
            ["As min = 0,0018 b h (mm²)", None, None, None, "Tabel 24.4.3.2 [penerapan ke cap: usulan AI]"]]
    r1, _, _ = lc.tabel(["Besaran", "Nilai", "", "", "Keterangan"], rows, rata=["l", "r", "r", "r", "l"], fill_kolom={1: AI}, beku=False)
    Y = lambda i: f"{lc.kol(1)}{r1 + 1 + i}"
    s = lambda c: X(c)
    lc.ws[Y(0)] = f"={s(4)}/1000"
    lc.ws[Y(1)] = f"={s(5)}/2000+{Y(0)}"
    lc.ws[Y(2)] = f"=MAX(0,MIN(1,({s(9)}-{Y(1)}+{s(6)}/2)/{s(6)}))"
    lc.ws[Y(3)] = f"=2*{Y(2)}*{s(8)}"
    lc.ws[Y(4)] = f"=0.75*0.17*SQRT({s(1)})*{s(10)}*{Y(0)}*1000"
    lc.ws[Y(5)] = f"={Y(3)}/{Y(4)}"
    lc.ws[Y(6)] = f"={s(5)}/2000+{Y(0)}/2"
    lc.ws[Y(7)] = f"=4*({s(5)}/1000+{Y(0)})"
    lc.ws[Y(8)] = f"=MAX(0,MIN(1,({s(9)}-{Y(6)}+{s(6)}/2)/{s(6)}))"
    lc.ws[Y(9)] = f"=4*{Y(8)}*{s(8)}"
    lc.ws[Y(10)] = f"=MIN(0.33,0.17*(1+2/1),0.083*(2+40*{Y(0)}/{Y(7)}))*SQRT({s(1)})"
    lc.ws[Y(11)] = f"=0.75*{Y(10)}*{Y(7)}*{Y(0)}*1000"
    lc.ws[Y(12)] = f"={Y(9)}/{Y(11)}"
    lc.ws[Y(13)] = f"=2*{s(8)}*({s(9)}-{s(5)}/2000)"
    k = f"({Y(13)}*1000000/(0.9*0.85*{s(1)}*{s(10)}*1000*({s(4)})^2))"
    lc.ws[Y(14)] = f"=0.85*{s(1)}*{s(10)}*1000*{s(4)}/{FY}*(1-SQRT(1-2*{k}))"
    lc.ws[Y(15)] = f"=0.0018*{s(10)}*1000*{s(0)}"
    for i in (0, 1, 6, 7):
        lc.ws[Y(i)].number_format = "0.0000"
    for i in (2, 8):
        lc.ws[Y(i)].number_format = "0.0000"
    for i in (3, 4, 9, 11, 13, 14, 15):
        lc.ws[Y(i)].number_format = "#,##0.0"
    for i in (5, 12):
        lc.ws[Y(i)].number_format = "0.0000"
    lc.ws[Y(10)].number_format = "0.0000"
    adr["cap4"] = {"d": Y(0), "Vu1": Y(3), "phiVc1": Y(4), "bo": Y(7), "phiVc2": Y(11), "Mu": Y(13), "As": Y(14), "Vu2": Y(9)}
    lc.kosong()
    lc.bagian("C", "Tebal terkecil yang memenuhi per tipe cap (skrip) dan rasio pada h 1.000 dan 1.200")
    rows = []
    for n in (2, 3, 4):
        e = h["cap_kolom"][n]
        u, a1, a2 = e["usul"], e["h1000"], e["h1200"]
        rows.append([f"{n} tiang ({e['cap']['id']}, {idn(e['cap']['ukuran'][0], 1)} × {idn(e['cap']['ukuran'][1], 2)} m, Ru {idn(u['Ru'], 0)} kN)", u["h"],
                     f"{u['penentu']} {idn(u['rasio'], 2)}", f"h 1.000: {idn(a1['rasio'], 2)}{'' if a1['lolos'] else ' (gagal)'}; h 1.200: {idn(a2['rasio'], 2)}"])
    lc.tabel(["Tipe", "h usulan (mm)", "Penentu dan rasio", "Rasio pada h 1.000 dan 1.200", ""], [r + [""] for r in rows], rata=["l", "r", "l", "l", "l"],
             fmt=[None, "#,##0", None, None, None], fill_kolom={1: AI, 2: AI, 3: AI}, beku=False)

    # ---- Cap Inti
    lci = Lembar(wb.create_sheet("Cap Inti"), 6, "Cap inti: STM Cap E, pembanding balok, pons, enam cap", [34, 14, 14, 14, 14, 14, 14, 40])
    lci.catatan(ket)
    lci.kosong()
    S = h["stm_E"]
    lci.bagian("A", "Cap E: parameter STM global per tiang (pembanding lama, tidak menentukan; Cap E didesain sebagai pelat, lembar Cap E Pelat)")
    rows = [["d (m)", S["d"], "h - 75 - 1,5 × 32"], ["z = 0,85 d (m)", S["z"], "[Asumsi]"], ["hta = 2 (h - d) (m)", S["hta"], "tinggi zona angkur tie"],
            ["fce strut = 0,85 × 0,60 × f'c (MPa)", S["fce_s"], "13.4.2.4, 23.4.3 (βs 0,60λ)"], ["fce nodal tiang = 0,85 × 0,60 × f'c (MPa)", S["fce_n"], "23.9.2 (dua tie atau lebih)"],
            ["Tiang dalam STM (θ ≥ 25°)", S["n_stm"], "23.2.7"], ["Tiang di luar STM (θ < 25°)", S["n_luar"], "lentur/geser balok"], ["Tiang tarik (kombinasi Pu min)", S["n_tarik"], "18.13.4.1"]]
    lci.tabel(["Besaran", "Nilai", "", "", "", "", "", "Sumber"], [r[:2] + ["", "", "", "", ""] + [r[2]] for r in rows], rata=["l", "r"] + ["r"] * 5 + ["l"], fmt=[None, "#,##0.000"] + [None] * 6,
              fill_kolom={1: AI}, beku=False)
    lci.kosong()
    lci.bagian("B", "Cap E: strut-and-tie per tiang (Ri dari kombinasi Pu maks, 6.3 rumus cap kaku)")
    rows = []
    for rw in S["rows"]:
        rows.append([f"({idn(rw['x'], 1)}; {idn(rw['y'], 1)})", rw["R"], rw["node"], rw["li"], rw["theta"], "ya" if rw["stm"] else "tidak",
                     rw.get("r_strut", ""), rw.get("r_tiang", "")])
    rr0, _, _ = lci.tabel(["Tiang", "Ri (kN)", "Node", "li (m)", "θ (°)", "STM", "Rasio strut", "Rasio tumpu tiang"], rows, rata=["l", "r", "l", "r", "r", "c", "r", "r"],
                          fmt=[None, "#,##0", None, "0.00", "0.0", None, "0.000", "0.000"], fill_kolom={1: AI, 3: AI, 4: AI, 6: AI, 7: AI}, beku=False)
    lci.kosong()
    # rumus hidup: tiang kritis (rasio strut terbesar)
    st = [rw for rw in S["rows"] if rw["stm"]]
    krit = max(st, key=lambda z: max(z["r_strut"], z["r_tiang"])) if st else None
    lci.bagian("C", "Cek strut dan nodal tiang kritis (rumus hidup)")
    if krit:
        rows = [["Ri (kN)", krit["R"], "kombinasi Pu maks"], ["θ (°)", krit["theta"], "arctan(z / li)"],
                ["lb = √(π Dt² / 4) (m)", LB_TIANG, "lebar persegi ekuivalen tiang"], ["hta (m)", S["hta"], ""],
                ["f'c (MPa)", FC_CAP, ""], ["F strut = Ri / sin θ (kN)", None, ""],
                ["ws = lb sin θ + hta cos θ (m)", None, "R23.9"], ["φ Fns = 0,75 × 0,85 × 0,60 f'c × ws × lb (kN)", None, "23.4.3, 23.4.1"],
                ["Rasio strut", None, ""], ["Rasio tumpu tiang = Ri / (0,75 × 0,85 × 0,60 f'c Apile)", None, "23.9.2"]]
        r2, _, _ = lci.tabel(["Besaran", "Nilai", "", "", "", "", "", "Keterangan"], [r[:2] + [""] * 5 + [r[2]] for r in rows], rata=["l", "r"] + ["r"] * 5 + ["l"],
                             fill_kolom={1: AI}, beku=False)
        Z = lambda i: f"{lci.kol(1)}{r2 + 1 + i}"
        lci.ws[Z(5)] = f"={Z(0)}/SIN(RADIANS({Z(1)}))"
        lci.ws[Z(6)] = f"={Z(2)}*SIN(RADIANS({Z(1)}))+{Z(3)}*COS(RADIANS({Z(1)}))"
        lci.ws[Z(7)] = f"=0.75*0.85*{BETA_S}*{Z(4)}*{Z(6)}*{Z(2)}*1000"
        lci.ws[Z(8)] = f"={Z(5)}/{Z(7)}"
        lci.ws[Z(9)] = f"={Z(0)}/(0.75*0.85*{BETA_N_TIANG}*{Z(4)}*PI()*0.8^2/4*1000)"
        for i in (5, 7):
            lci.ws[Z(i)].number_format = "#,##0.0"
        for i in (6, 8, 9):
            lci.ws[Z(i)].number_format = "0.0000"
        adr["stm"] = {"strut": Z(8), "tumpu": Z(9)}
    lci.kosong()
    lci.bagian("D", "Tie, pembanding balok lentur, geser satu arah, pons inti")
    rows = [["Tie x maks T (kN) / As = T / (0,75 fy) (mm²)", S["Tx"], S["As_stm"]["x"], S["As_beam"]["x"], "As balok lentur (φ 0,9, Mu max, lebar cap)"],
            ["Tie y maks T (kN) / As (mm²)", S["Ty"], S["As_stm"]["y"], S["As_beam"]["y"], ""],
            ["Mu maks balok x / y (kNm)", S["Mx"], S["My"], "", "momen terbesar di potongan, semua tiang dan beban"],
            ["Tarik: Mu balik atas x / y (kNm); As atas (mm²)", S["Mt"]["x"], S["Mt"]["y"], S["As_atas"]["x"], f"y: {idn(S['As_atas']['y'], 0)}"],
            ["Geser satu arah global: Vu, φVc (kN), rasio", S["geser"].get("Vu", 0.0), S["geser"].get("phiVc", 0.0), S["geser"]["rasio"], f"arah {S['geser'].get('arah', '')}"],
            ["Pons kotak inti lif (4 × 8 m [Asumsi]): Vu, φVc (kN), rasio", S["pons"]["Vu"], S["pons"]["phiVc"], S["pons"]["rasio"], f"bo {idn(S['pons']['bo'], 2)} m, {S['pons']['sisi']} sisi"],
            ["Rasio STM terbesar (strut, tumpu tiang, tumpu node)", S["rasio_stm"], "", "", ""]]
    lci.tabel(["Butir", "Nilai 1", "Nilai 2", "Nilai 3", "Keterangan", "", "", ""], [r + ["", "", ""] for r in rows], rata=["l", "r", "r", "r", "l", "r", "r", "r"],
              fmt=[None, "#,##0.00", "#,##0.00", "#,##0.0000", None, None, None, None], fill_kolom={1: AI, 2: AI, 3: AI}, beku=False)
    lci.kosong()
    lci.bagian("E", "Enam cap inti: Pu maks per tiang dan pons tiang sudut (h 1.200; Cap E h 1.500; f'c 35)")
    rows = [[f"{x['id']} ({x['n']} tiang, {idn(x['ukuran'][0], 1)} × {idn(x['ukuran'][1], 1)} m)", x["Pu_maks"], x["Pu_min"], x["pons_tiang"]["phiVc"], x["rasio"], "", "", ""]
            for x in h["inti"]]
    lci.tabel(["Cap", "Pu maks/tiang (kN)", "Pu min/tiang (kN)", "φVc pons (kN)", "Rasio pons tiang", "", "", ""], rows, rata=["l", "r", "r", "r", "r", "r", "r", "r"],
              fmt=[None, "#,##0", "#,##0", "#,##0", "0.000", None, None, None], fill_kolom={1: AI, 2: AI, 3: AI, 4: AI}, beku=False)

    # ---- Cap E pelat
    PE, PL = h["pelat_E"], h["pelat"]
    lp = Lembar(wb.create_sheet("Cap E Pelat", wb.sheetnames.index("Cap Inti") + 1), 12, "Cap E sebagai pelat di atas pegas tiang (OpenSees ShellMITC4)", [46, 16, 16, 16, 16, 16, 16, 52])
    lp.catatan(ket)
    lp.kosong()
    pad = lambda r, n=8: list(r) + [""] * (n - len(r))
    lp.bagian("A", "Model dan masukan (keputusan Defsa 22 Nov 2026: pelat di atas tiang, 32 tiang tetap)")
    rows = [["k tiang tunggal uji beban TP-1..4 (kN/mm)", PE["k"], "6.6 / 6.2"], ["FJ (faktor jangka panjang)", PE["fj"], "6.6 [Asumsi]"], ["n tiang Cap E", PE["n"], "6.3"],
            ["k_eff = k / (FJ √n) (kN/m)", None, "dari s = FJ Q0 √n / k (6.6 varian d); sama untuk semua tiang [Asumsi]"],
            ["Ec = 4700 √f'c (MPa)", ec(FC_CAP), "bruto, tanpa retak [Asumsi]"], ["h pelat terpilih (mm)", H_E, "usulan Defsa 1.800"], ["d = h - 75 - 1,5 × 32 (mm)", PE["d"], "dua lapis silang"],
            ["Jaring (m) / jenis elemen", "0,4 / ShellMITC4", "simpul tepat di as tiang; tiang = pegas di 3 × 3 simpul; kepala sendi 6.5"]]
    r0, _, _ = lp.tabel(["Besaran", "Nilai", "", "", "", "", "", "Sumber"], [pad(r[:2]) [:7] + [r[2]] for r in rows], rata=["l", "r"] + ["r"] * 5 + ["l"], fmt=[None, "#,##0.000"] + [None] * 6,
                        fill_kolom={1: AI}, beku=False)
    lp.ws[f"{lp.kol(1)}{r0 + 4}"] = f"={lp.kol(1)}{r0 + 1}*1000/({lp.kol(1)}{r0 + 2}*SQRT({lp.kol(1)}{r0 + 3}))"
    lp.ws[f"{lp.kol(1)}{r0 + 4}"].number_format = "#,##0"
    lp.kosong()
    lp.bagian("B", "Tebal pelat: rasio terhadap kapasitas (geser satu arah di d dari muka inti dan tiang; pons; STM lokal 2d dari dinding inti)")
    rows = []
    for hh, a in PL["hasil"].items():
        lb, ly = a["lentur"][("bawah", "x")], a["lentur"][("bawah", "y")]
        rows.append([hh, a["d"], a["rasio"]["geser"], a["rasio"]["pons_tiang"], a["rasio"]["pons_inti"], a["rasio"]["stm"],
                     f"{idn(lb['As_maks'], 0)} / {idn(ly['As_maks'], 0)}", f"{a['penentu']}; {'lolos' if a['lolos'] else 'gagal'}"])
    lp.tabel(["h (mm)", "d (mm)", "Geser 1 arah", "Pons tiang", "Pons inti", "STM lokal", "As bawah x / y (mm²/m)", "Penentu; hasil"], rows, rata=["r"] * 7 + ["l"],
             fmt=["#,##0", "#,##0", "0.000", "0.000", "0.000", "0.000", None, None], fill_kolom={1: AI, 2: AI, 3: AI, 4: AI, 5: AI, 6: AI, 7: AI}, beku=False)
    lp.kosong()
    b = PE["banding"]
    lp.bagian("C", "Reaksi tiang: pelat vs rumus cap kaku 6.3 (Pu maks + 1,2 berat cap; toleransi: Σ ≤ 0,5 %, maksimum ≤ 25 %)")
    lp.tabel(["Besaran", "Pelat", "Cap kaku (6.3)", "Selisih (%)", "", "", "", "Keterangan"], [
        ["Σ reaksi (kN) vs Σ P", b["sum_fe"], b["sumP"], b["d_sum"], "", "", "", "kesetimbangan"],
        ["Reaksi tiang maksimum (kN)", b["max_fe"], b["max_kaku"], b["d_max"], "", "", "", "lolos" if b["lolos"] else "GAGAL"],
        ["Reaksi tiang minimum (kN)", b["min_fe"], b["min_kaku"], "", "", "", "", "kombinasi Pu maks"],
        ["Tiang maks (1,2 berat cap bersih apung, seperti 6.3) (kN)", float(PE["r1"]["R"].max()), "", "", "", "", "", "berat cap ada di 6.3; tidak dihitung dua kali"],
        ["Tiang min kombinasi Pu min + 0,9 berat sendiri (kN)", float(PE["r2"]["R"].min()), float(PE["Rmin_kaku"].min()), "", "", "", "", "tarik, cap kaku 6.3 dengan berat cap"]],
        rata=["l", "r", "r", "r", "r", "r", "r", "l"], fmt=[None, "#,##0", "#,##0", "0.00", None, None, None, None], fill_kolom={1: AI, 2: AI, 3: AI}, beku=False)
    lp.kosong()
    lp.bagian("D", f"Tulangan lentur h {idn(H_E, 0)} (Wood-Armer, rata-rata lajur ± 2 m; D32; As = max(perlu, min 9.6.1.2 tetapi ≤ 4/3 perlu, susut 0,0018 b h))")
    rows = []
    for (sisi, ar), v in PE["lentur"].items():
        lap, sp = v["pilih"]
        rows.append([f"{sisi} arah {ar}", v["M_maks"], v["req"], v["susut"], v["As_maks"], f"{lap} lapis D32 - {sp}", "", ""])
    lp.tabel(["Muka / arah", "Mu lajur maks (kNm/m)", "As lentur (mm²/m)", "As susut (mm²/m)", "As desain (mm²/m)", "Susunan", "", ""], rows, rata=["l", "r", "r", "r", "r", "l", "r", "r"],
             fmt=[None, "#,##0", "#,##0", "#,##0", "#,##0", None, None, None], fill_kolom={1: AI, 2: AI, 3: AI, 4: AI, 5: AI}, beku=False)
    lp.kosong()
    g = PE["geser"]
    lp.bagian("E", "Geser satu arah penentu (rumus hidup φVc per meter)")
    r1, _, _ = lp.tabel(["Besaran", "Nilai", "", "", "", "", "", "Keterangan"], [
        ["Vu per meter, rata-rata jendela 2d (kN/m)", g["v"], "", "", "", "", "", f"penampang {g['arah']} = {idn(g['garis'], 2)} m, lebar {idn(g['lebar'], 1)} m"],
        ["d (m)", PE["d"] / 1e3, "", "", "", "", "", ""], ["f'c (MPa)", FC_CAP, "", "", "", "", "", ""],
        ["φVc = 0,75 × 0,17 √f'c × 1000 d (kN/m)", None, "", "", "", "", "", "22.5.5.1, 22.5.1.1"], ["Rasio Vu / φVc", None, "", "", "", "", "", ""]],
        rata=["l", "r"] + ["r"] * 5 + ["l"], fmt=[None, "#,##0.000"] + [None] * 6, fill_kolom={1: AI}, beku=False)
    K = lambda i: f"{lp.kol(1)}{r1 + 1 + i}"
    lp.ws[K(3)] = f"=0.75*0.17*SQRT({K(2)})*1000*{K(1)}"
    lp.ws[K(4)] = f"={K(0)}/{K(3)}"
    lp.ws[K(3)].number_format = "#,##0.0"
    lp.ws[K(4)].number_format = "0.0000"
    adr["pelat"] = {"geser": K(4)}
    lp.kosong()
    lp.bagian("F", f"As bawah per lajur (mm²/m), h {idn(H_E, 0)}")
    nb = max(len(PE["lentur"][("bawah", "x")]["As"]), len(PE["lentur"][("bawah", "y")]["As"]))
    rows = []
    for i in range(nb):
        row = [f"lajur {i + 1}"]
        for ar in ("x", "y"):
            v = PE["lentur"][("bawah", ar)]
            row += [v["M"][i], v["As"][i], f"{v['lap'][i][0]} × D32 - {v['lap'][i][1]}"] if i < len(v["As"]) else ["", "", ""]
        rows.append(pad(row + ["lajur ke-i sepanjang y (arah x) atau x (arah y), ±2 m"]))
    lp.tabel(["Lajur", "Mu x (kNm/m)", "As x", "Susunan x", "Mu y (kNm/m)", "As y", "Susunan y", "Keterangan"], rows, rata=["l", "r", "r", "l", "r", "r", "l", "l"],
             fmt=[None, "#,##0", "#,##0", None, "#,##0", "#,##0", None, None], fill_kolom={1: AI, 2: AI, 4: AI, 5: AI}, beku=False)

    # ---- Pit
    lpi = Lembar(wb.create_sheet("Pit"), 7, "Pit lift L-1..4: angkat dan pengangkuran (rumus hidup)", [46, 16, 16, 70])
    lpi.catatan(ket)
    lpi.kosong()
    lpi.bagian("A", "Varian A: berat sendiri (SNI 8460 9.3.4 b, FK ≥ 1,1) dan varian B: diikat (9.3.3 b / 9.3.4 a, FK 1,5)")
    p = h["pit"]
    rows = [["Tebal pelat dasar t (m)", 0.40, 0.45, "5.5: 0,40 awal; opsi A dipakai 0,45"],
            ["Muka air Q100 (m)", PIT["muka_air"], PIT["muka_air"], "5.5 (muka air tekan +11,20; Q50 +11,85)"],
            ["Elevasi sisi bawah pit (m)", PIT["bawah"][0.40], PIT["bawah"][0.45], "5.5: +10,85 untuk t 0,40; turun (t - 0,40) untuk t 0,45"],
            ["Tapak luar A (m²)", PIT["A"], PIT["A"], "5,8 × 6,8 (bukaan 5,2 × 6,2 + dinding 0,30)"],
            ["W berat pit (kN)", PIT["W"][0.40], PIT["W"][0.45], "5.5"],
            ["u = 9,81 (muka air - elevasi bawah) (kPa)", None, None, ""],
            ["U = u A (kN)", None, None, ""],
            ["FK = W / U", None, None, "9.3.4 b ≥ 1,1"],
            ["R = 1,5 U - W (kN)", None, None, "varian B: gaya angkur izin"],
            ["As stek = 1,6 R / (0,9 fy) (mm²)", None, None, "5.5 (As = 1,6 R / (0,9 fy))"],
            ["FK varian B = (W + R) / U", None, None, "9.3.3 b / 9.3.4 a ≥ 1,5"]]
    r0, a, b = lpi.tabel(["Besaran", "t 0,40", "t 0,45", "Sumber"], rows, rata=["l", "r", "r", "l"], fill_kolom={1: AI, 2: AI}, beku=False)
    Pp = lambda i, k: f"{lpi.kol(k)}{r0 + 1 + i}"
    for k in (1, 2):
        lpi.ws[Pp(5, k)] = f"=9.81*({Pp(1, k)}-{Pp(2, k)})"
        lpi.ws[Pp(6, k)] = f"={Pp(5, k)}*{Pp(3, k)}"
        lpi.ws[Pp(7, k)] = f"={Pp(4, k)}/{Pp(6, k)}"
        lpi.ws[Pp(8, k)] = f"=MAX(0,1.5*{Pp(6, k)}-{Pp(4, k)})"
        lpi.ws[Pp(9, k)] = f"=1.6*{Pp(8, k)}*1000/(0.9*{FY})"
        lpi.ws[Pp(10, k)] = f"=({Pp(4, k)}+{Pp(8, k)})/{Pp(6, k)}"
        for i in (5, 6, 8, 9):
            lpi.ws[Pp(i, k)].number_format = "#,##0.0"
        lpi.ws[Pp(7, k)].number_format = "0.0000"
        lpi.ws[Pp(10, k)].number_format = "0.0000"
    adr["pit"] = {"FK": {0.40: Pp(7, 1), 0.45: Pp(7, 2)}, "R": {0.40: Pp(8, 1), 0.45: Pp(8, 2)}, "As": {0.40: Pp(9, 1), 0.45: Pp(9, 2)}}
    lpi.kosong()
    g = p["geom"]
    lpi.bagian("B", "Letak terhadap Cap E (temuan)")
    lpi.tabel(["Besaran", "Nilai", "", "Keterangan"], [
        ["Tepi timur Cap E x (m)", g["x_tepi"], "", "pos tiang maks + 0,8"],
        ["Tapak pit x (m)", "51,10-56,90", "", "5.5"],
        ["Pit menjorok melewati tepi cap (m)", g["menjorok"], "", "usulan AI: perlebar Cap E ke timur ≥ 1,3 m atau pit berdiri di cap"],
        ["Fraksi tapak pit di dalam cap", g["frak_dalam"], "", ""],
        ["Bagian R di luar cap, t 0,40 (kN)", g["R_luar"], "", "diikat ke sloof/dinding, bukan cap"],
        ["Elevasi dasar pit t 0,45 (m) vs dasar cap (m)", g["dasar_pit"], g["dasar_cap"], "dasar pit di atas dasar cap; pit berdiri di dalam cap pejal 1,50 m (bentrok volume)"]],
        rata=["l", "r", "r", "l"], fmt=[None, "0.00", "0.00", None], fill_kolom={1: AI, 2: AI}, beku=False)

    # ---- Sloof
    ls = Lembar(wb.create_sheet("Sloof"), 8, "Sloof SL-2 dan SL-3 pada δ 24,6 mm (rumus hidup)", [46, 16, 16, 60])
    ls.catatan(ket)
    ls.kosong()
    ls.bagian("A", "Kombinasi 1,2D + 1,6L + 1,0T (pola 5.4; T = momen penurunan beda varian d 6.6)")
    sl = h["sloof"]
    rows = [["Ukuran", "400 × 800", "400 × 800", "5.4"], ["Tulangan atas / bawah", sl["SL-2"]["tul"], sl["SL-3"]["tul"], "5.4"],
            ["Mu- gravitasi 1,2D + 1,6L (kNm)", sl["SL-2"]["Mgrav_neg"], sl["SL-3"]["Mgrav_neg"], "5.4 Lentur Gravitasi"],
            ["Mu+ gravitasi (kNm)", sl["SL-2"]["Mgrav_pos"], sl["SL-3"]["Mgrav_pos"], "5.4"],
            ["M penurunan δ 24,6 mm (kNm)", sl["SL-2"]["M_pen"], sl["SL-3"]["M_pen"], "6.6 (400 × 800: 383 kNm)"],
            ["φMn- (kNm)", sl["SL-2"]["phiMn_neg"], sl["SL-3"]["phiMn_neg"], "5.4 Desain Sloof / Kapasitas"],
            ["φMn+ (kNm)", sl["SL-2"]["phiMn_pos"], sl["SL-3"]["phiMn_pos"], "5.4"],
            ["Mu- total = grav + penurunan (kNm)", None, None, ""],
            ["Rasio Mu- / φMn-", None, None, ""], ["Rasio Mu+ / φMn+", None, None, "Mu+ gravitasi tidak ditambah (pola 5.4)"],
            ["Rasio terbesar", None, None, "< 1 : tidak perlu tulangan tambahan"]]
    r0, a, b = ls.tabel(["Besaran", "SL-2", "SL-3", "Sumber"], rows, rata=["l", "r", "r", "l"], fill_kolom={1: AI, 2: AI}, beku=False)
    Q = lambda i, k: f"{ls.kol(k)}{r0 + 1 + i}"
    for k in (1, 2):
        ls.ws[Q(7, k)] = f"={Q(2, k)}+{Q(4, k)}"
        ls.ws[Q(8, k)] = f"={Q(7, k)}/{Q(5, k)}"
        ls.ws[Q(9, k)] = f"={Q(3, k)}/{Q(6, k)}"
        ls.ws[Q(10, k)] = f"=MAX({Q(8, k)},{Q(9, k)})"
        ls.ws[Q(7, k)].number_format = "#,##0.0"
        for i in (8, 9, 10):
            ls.ws[Q(i, k)].number_format = "0.0000"
    adr["sloof"] = {"SL-2": Q(10, 1), "SL-3": Q(10, 2)}
    ls.kosong()
    ls.catatan(f"SL-1 400 × 900: M penurunan {idn(M_SL1_PENURUNAN, 0)} kNm, rasio {idn(RASIO_SL1, 2)} (6.6, hanya dicatat). Catatan 6.6: rasio SL-1 pada δ 16 mm kode 0,534, teks 5.4 0,48.")

    # ---- Ringkasan
    lr = Lembar(wb.create_sheet("Ringkasan", 1), 2, "Ringkasan hasil", [44, 20, 20, 52])
    lr.catatan(ket)
    lr.kosong()
    lr.bagian("A", "Tiang Ø800 (D25, spiral D13)")
    rows = []
    for fc in FC_VARIAN:
        tt = h["tiang"][fc]
        rows.append([f"f'c {int(fc)}: n D25 minimum / rasio terbesar", tt["n_min"], tt["cek_min"]["rasio_maks"], f"spiral rapat s {tt['spiral']['s_rapat']:.0f} mm; luar s {tt['spiral']['s_luar']:.0f} mm"])
        rows.append([f"f'c {int(fc)}: 16 D25 rasio terbesar", 16, tt["cek16"]["rasio_maks"], "lolos" if tt["cek16"]["lolos"] else "gagal"])
    lr.tabel(["Butir", "n", "Rasio", "Catatan"], rows, rata=["l", "r", "r", "l"], fmt=[None, "0", "0.000", None], fill_kolom={1: AI, 2: AI}, beku=False)
    lr.kosong()
    lr.bagian("B", "Pile cap, STM, pit, sloof")
    rows = []
    for n in (2, 3, 4):
        u = h["cap_kolom"][n]["usul"]
        rows.append([f"Cap kolom {n} tiang: h usulan (mm)", u["h"], u["rasio"], f"penentu {u['penentu']}"])
    PE = h["pelat_E"]
    rows.append([f"Cap E pelat h {idn(H_E, 0)}: rasio penentu ({PE['penentu']})", H_E, max(PE["rasio"].values()), f"pelat OpenSees, STM lokal {PE['stm']['n_stm']} tiang"])
    rows.append(["Pit L-1..4 FK varian A (t 0,45)", "", p[0.45]["FK"], f"R varian B {idn(p[0.40]['R'], 1)} kN"])
    rows.append(["Sloof SL-2 / SL-3 rasio", "", f"{idn(sl['SL-2']['rasio'], 3)} / {idn(sl['SL-3']['rasio'], 3)}", "tulangan 5.4 cukup"])
    lr.tabel(["Butir", "Nilai", "Rasio / FK", "Catatan"], rows, rata=["l", "r", "r", "l"], fmt=[None, "#,##0", "0.000", None], fill_kolom={1: AI, 2: AI}, beku=False)
    lr.kosong()

    # ---- Verifikasi (diisi kemudian) dan Acuan, Keputusan
    lv = Lembar(wb.create_sheet("Verifikasi"), 9, "Verifikasi T-105", [44, 22, 22, 50])
    lv.catatan(ket)
    lv.kosong()
    lv.bagian("A", "Toleransi (ditetapkan sebelum membandingkan)")
    lv.tabel(["Butir", "Toleransi (%)", "", "Keterangan"], [
        ["(a) hitung tangan vs skrip (cap 4 tiang, tiang, pit, sloof)", TOL["tangan"], "", "uji `tests/test_tahap6_struktur.py`"],
        ["(b) Excel rumus hidup vs Python", TOL["excel"], "", "dihitung ulang di Excel"],
        ["(c) STM vs pendekatan balok lentur (Cap E), orde besaran", TOL["stm"], "", "T = M / z vs T = Mu / (d - a/2); φ tidak dibandingkan"],
        ["(d) pelat Cap E vs cap kaku 6.3: Σ reaksi vs ΣP", TOL["sum_pelat"], "", "Pu maks + 1,2 berat cap"],
        ["(d) pelat Cap E vs cap kaku 6.3: reaksi tiang maksimum", TOL["max_pelat"], "", "pelat lebih lentur dari cap kaku, jadi selisih lebih longgar"]], rata=["l", "r", "r", "l"], fmt=[None, "0.0", None, None], beku=False)
    la = Lembar(wb.create_sheet("Acuan"), 10, "Acuan dan status", [52, 26, 84])
    la.catatan(ket)
    la.kosong()
    la.tabel(["Acuan", "Halaman", "Isi yang dipakai"], [list(a) for a in ACUAN], rata=["l", "l", "l"], beku=False)
    lk = Lembar(wb.create_sheet("Keputusan"), 11, "Keputusan untuk Defsa", [8, 130])
    lk.catatan(ket)
    lk.kosong()
    lk.tabel(["No", "Keputusan (usulan AI)"], [[i + 1, t] for i, t in enumerate(keputusan(h))], rata=["c", "l"], beku=False)
    wb.save(keluar)
    return keluar, adr


def keputusan(h):
    t30, t35 = h["tiang"][30.0], h["tiang"][35.0]
    c = h["cap_kolom"]
    S = h["stm_E"]
    p = h["pit"]
    return [
        f"f'c tiang: 30 (asumsi 6.2) memerlukan {t30['n_min']} D25 minimum, 35 (S2 ≥ 31) {t35['n_min']} D25. Usulan AI: 35 MPa seragam dengan cap, sloof, pit; 16 D25 lolos pada keduanya "
        f"({'ya' if t30['cek16']['lolos'] and t35['cek16']['lolos'] else 'cek tabel'}).",
        f"Panjang tulangan: tiang cap inti penuh sampai -27,60; cap kolom sampai elevasi {idn(t35['panjang']['elev_b'], 2)} (usulan AI, {idn(t35['panjang']['L_b'], 1)} m dari kepala) atau penuh semua (varian).",
        f"Zona spiral rapat sampai {idn(KEPALA - zona_rapat()['SELATAN']['rapat'] , 2)} (SNI 1726 7.13.8.3.3; panjang {idn(zona_rapat()['SELATAN']['rapat'], 2)} m dari kepala); spiral D13 "
        f"s {t35['spiral']['s_rapat']:.0f} mm (rapat) dan {t35['spiral']['s_luar']:.0f} mm (luar) untuk f'c 35.",
        "Tebal cap kolom: usulan AI memakai tebal terkecil yang lolos (lihat Ringkasan); cap tetap 1.200 mm bila elevasi kepala tiang +10,85 dan reaksi 5.6 tidak diubah.",
        f"Cap E gabungan: pit L-1..4 menjorok {idn(p['geom']['menjorok'], 2)} m di luar tepi timur (x {idn(p['geom']['x_tepi'], 2)}); pit berdiri di dalam cap (dasar pit +10,80 di atas dasar cap +{idn(12.05 - H_E / 1e3, 2)}): cap dilubangi atau pit dicor menyatu dengan cap.",
        f"Pit: varian A FK {idn(p[0.45]['FK'], 3)} (lolos tipis, 9.3.4 b); varian B diikat R {idn(p[0.40]['R'], 1)} kN, stek {idn(p[0.40]['As'], 0)} mm² (FK 1,5). Usulan AI: A, tambah pengikat B bila Q100 dipakai.",
        "Serakan Zhang (6.5) tetap tidak ditahan tiang Ø800; tulangan didesain untuk Youd 0,19 m dan inersia; perbaikan tanah U5 atau tiang batas Ø600 (6.4) menjadi syarat.",
        "Ukuran kolom K-P 750 vs 0,8 m (5.6): perhitungan memakai 800 (konservatif).",
        f"Cap E pelat h {idn(H_E, 0)} mm (berat cap masuk 6.3, dinaikkan sekali dari 1.800): {'lolos' if h['pelat_E']['lolos'] else 'TIDAK lolos, penentu ' + h['pelat_E']['penentu'] + ' ' + idn(max(h['pelat_E']['rasio'].values()), 3)}; "
        f"h minimum lolos {idn(h['pelat']['h_min'], 0) if h['pelat']['h_min'] else 'tidak ada'} mm. Usulan AI (konservatif): h 2.000 mm bila 1.900 gagal; dasar Cap E +{idn(12.05 - 2.0, 2)} dan dampak ke 6.8, 6.9 mengikuti.",
    ]


def revisi_cap_c(h):
    """Paragraf revisi 22 Nov 2026: Cap C digabung ke Cap E (angka dari hasil hitung, dibandingkan dengan Cap E sebelum penggabungan)."""
    ce = h["cap_E"]
    tb = h["tebal_E"][1500.0]
    sb = ce.get("sebelum", {})
    u = ce.get("union")
    return (f"**Revisi 22 Nov 2026 (keputusan Defsa): Cap C digabung ke Cap E** (6.3): {ce['r']['n']} tiang, {idn(ce['ukuran'][0], 1)} × {idn(ce['ukuran'][1], 1)} m, "
            f"Σ P layan {idn(ce['r']['sumP'], 0)} kN. Sebelum: Cap E {sb['Cap E']['n']} tiang (Pu maks {idn(sb['Cap E']['Pu_maks'], 0)}, Pu min {idn(sb['Cap E']['Pu_min'], 0)} kN) dan Cap C "
            f"{sb['Cap C']['n']} tiang (Pu maks {idn(sb['Cap C']['Pu_maks'], 0)} kN). " + (f"Gabungan polos {u['n']} tiang gagal tekan gempa (Pu maks {idn(u['Pu_maks'], 0)} kN), "
            f"maka tata letak dicari ulang. " if u else "")
            + f"Setelah: Pu maks {idn(ce['r']['Pu_maks'], 0)}, Pu min {idn(ce['r']['Pu_min'], 0)} kN, P layan maks {idn(ce['r']['P_layan'], 0)} kN. "
            f"h 1.500 mm (STM global per tiang, sebelum keputusan pelat): rasio STM {idn(tb['rasio_stm'], 3)}, geser satu arah {idn(tb['geser'], 3)}, pons inti {idn(tb['pons'], 3)}, "
            f"As x {idn(tb['As_x'], 0)} mm² (ρ {idn(tb['rho_x'] * 100, 2)} %), As y {idn(tb['As_y'], 0)} mm² (ρ {idn(tb['rho_y'] * 100, 2)} %): "
            f"{'h 1.500 masih lolos' if max(tb['rasio_stm'], tb['geser'], tb['pons']) <= 1.0 else 'h 1.500 TIDAK lolos'} pada model itu.")


# ================================================================== T-105
def baca_excel(berkas, adr):
    import openpyxl
    wb = openpyxl.load_workbook(berkas, data_only=True)

    def b(sh, cel):
        return float(wb[sh][cel].value)
    return {"tiang": {k: {fc: b("Tiang", c) for fc, c in v.items()} for k, v in adr["tiang"].items()},
            "spiral": {k: {fc: b("Tiang", c) for fc, c in v.items()} for k, v in adr["spiral"].items()},
            "cap4": {k: b("Cap Kolom", c) for k, c in adr["cap4"].items()},
            "stm": {k: b("Cap Inti", c) for k, c in adr.get("stm", {}).items()},
            "pit": {k: {t: b("Pit", c) for t, c in v.items()} for k, v in adr["pit"].items()},
            "sloof": {k: b("Sloof", c) for k, c in adr["sloof"].items()},
            "pelat": {k: b("Cap E Pelat", c) for k, c in adr.get("pelat", {}).items()}}


def t105(h, berkas=None, adr=None):
    """(a) hitung tangan satu cap 4 tiang (h 1.000) vs skrip; (b) Excel vs Python; (c) STM vs balok lentur Cap E."""
    e = h["cap_kolom"][4]["h1000"]
    d = (1000 - 75 - 1.5 * 32) / 1e3
    # tangan: tiang di ±1,2, kolom 0,8, Dt 0,8
    ru = e["Ru"]
    pos_x = 1.2
    f = max(0, min(1, (pos_x - (0.4 + d) + 0.4) / 0.8))
    vu_t = 2 * f * ru
    pvc_t = 0.75 * 0.17 * math.sqrt(35) * 4.0 * 1e3 * d
    dts = [abs(e["geser"]["Vu"] - vu_t) / vu_t * 100, abs(e["geser"]["phiVc"] - pvc_t) / pvc_t * 100]
    dt = max(dts)
    dxl = None
    if berkas and adr:
        x = baca_excel(berkas, adr)
        ds = []
        for fc in FC_VARIAN:
            tt = h["tiang"][fc]
            ds += [abs(x["tiang"]["phiPn"][fc] - tt["cek_min"]["kv"]["phiPn_maks"]) / tt["cek_min"]["kv"]["phiPn_maks"] * 100,
                   abs(x["tiang"]["phiTn"][fc] - tt["cek_min"]["kv"]["phiTn"]) / tt["cek_min"]["kv"]["phiTn"] * 100,
                   abs(x["tiang"]["ld"][fc] - tt["panjang"]["ld"]) / tt["panjang"]["ld"] * 100,
                   abs(x["spiral"]["rs_d"][fc] - tt["spiral"]["rs_d"]) / tt["spiral"]["rs_d"] * 100,
                   abs(x["spiral"]["s_rapat"][fc] - tt["spiral"]["s_rapat"]) / tt["spiral"]["s_rapat"] * 100]
        c = x["cap4"]
        py = {"Vu1": e["geser"]["Vu"], "phiVc1": e["geser"]["phiVc"], "bo": e["pons_kolom"]["bo"], "phiVc2": e["pons_kolom"]["phiVc"],
              "Vu2": e["pons_kolom"]["Vu"], "Mu": e["lentur"]["x"]["Mu"], "As": e["lentur"]["x"]["As_lentur"], "d": e["d"] / 1e3}
        ds += [abs(c[k] - v) / abs(v) * 100 for k, v in py.items() if v]
        if x["stm"]:
            S = h["stm_E"]
            st = [rw for rw in S["rows"] if rw["stm"]]
            if st:
                kr = max(st, key=lambda z: max(z["r_strut"], z["r_tiang"]))
                ds += [abs(x["stm"]["strut"] - kr["r_strut"]) / kr["r_strut"] * 100, abs(x["stm"]["tumpu"] - kr["r_tiang"]) / kr["r_tiang"] * 100]
        for t in (0.40, 0.45):
            pt = h["pit"][t]
            ds += [abs(x["pit"]["FK"][t] - pt["FK"]) / pt["FK"] * 100]
            if pt["R"]:
                ds += [abs(x["pit"]["R"][t] - pt["R"]) / pt["R"] * 100, abs(x["pit"]["As"][t] - pt["As"]) / pt["As"] * 100]
        for k in ("SL-2", "SL-3"):
            ds.append(abs(x["sloof"][k] - h["sloof"][k]["rasio"]) / h["sloof"][k]["rasio"] * 100)
        if x["pelat"]:
            ds.append(abs(x["pelat"]["geser"] - h["pelat_E"]["geser"]["rasio"]) / h["pelat_E"]["geser"]["rasio"] * 100)
        dxl = max(ds)
    S = h["stm_E"]
    dstm = S["dev_stm_beam"]
    bp = h["pelat_E"]["banding"]
    dsum, dmax = bp["d_sum"], bp["d_max"]
    lolos = (dt <= TOL["tangan"] and dxl is not None and dxl <= TOL["excel"] and dstm is not None and dstm <= TOL["stm"]
             and dsum <= TOL["sum_pelat"] and dmax <= TOL["max_pelat"])
    return dict(dt=dt, dxl=dxl, dstm=dstm, dsum=dsum, dmax=dmax, lolos=lolos)


def catat_t105(r, h, berkas=VERIFIKASI):
    S = h["stm_E"]
    baris = ("| T-105 | Cek silang 6.7 desain tiang Ø800 (P-M, spiral), pile cap kolom (geser, pons, lentur), STM Cap E, pit L-1..4, sloof SL-2/SL-3 | "
             f"(a) hitung tangan satu cap 4 tiang (h 1.000; Vu geser satu arah, φVc) vs skrip: selisih terbesar {idn(r['dt'], 3)} %; "
             f"(b) Python vs Excel rumus hidup (tiang φPn,maks, φTn, ld, ρs, s; cap 4 tiang d, Vu, φVc, bo, Mu, As; STM tiang kritis; pit FK, R, As; sloof): "
             f"selisih terbesar {idn(r['dxl'], 4) if r['dxl'] is not None else 'tidak dihitung'} %; "
             f"(c) gaya tarik tie STM Cap E (T = M / z, z = 0,85 d) vs pendekatan balok lentur (T = Mu / (d - a/2)) pada Mu terbesar: selisih terbesar "
             f"{idn(r['dstm'], 1) if r['dstm'] is not None else 'n/a'} % (orde besaran; pembanding lama STM global, bukan penentu); "
             f"(d) Cap E sebagai pelat OpenSees (ShellMITC4, pegas tiang k/(FJ√n)) vs rumus cap kaku 6.3, kombinasi Pu maks + 1,2 berat cap: Σ reaksi vs ΣP {idn(r['dsum'], 4)} %, "
             f"reaksi tiang maksimum {idn(r['dmax'], 1)} % | (a) ≤ 2 %; (b) ≤ 0,1 %; (c) ≤ 30 %; (d) Σ ≤ 0,5 %, maks ≤ 25 % | "
             f"{'Lolos' if r['lolos'] else 'GAGAL'}, STATUS: {STATUS} | `skrip/tahap6_struktur.py`, `skrip/tahap6_cap_pelat.py`, `tests/test_tahap6_struktur.py`, `tests/test_tahap6_cap_pelat.py` | "
             "Ditetapkan sebelum membandingkan. Data simulasi. STM per tiang dengan z = 0,85 d [Asumsi]; tiang dengan θ < 25° dikerjakan sebagai balok/pelat. "
             "Pelat: Ec bruto, k_eff sama untuk semua tiang, inti T46/39 4 × 4 m [Asumsi]. |")
    teks = Path(berkas).read_text(encoding="utf-8").split("\n")
    teks = [ln for ln in teks if not ln.startswith("| T-105 |")]
    i = next(k for k, ln in enumerate(teks) if ln.startswith("| T-104 |"))
    teks.insert(i + 1, baris)
    Path(berkas).write_text("\n".join(teks), encoding="utf-8")
    return baris


# ================================================================== Markdown
def tabel_md(kep, baris):
    return ["| " + " | ".join(kep) + " |", "|" + "---|" * len(kep)] + ["| " + " | ".join(str(x) for x in b) + " |" for b in baris]


def md_pelat(h):
    """Bagian 4: Cap E sebagai pelat tebal di atas pegas tiang (keputusan Defsa 22 Nov 2026), STM hanya lokal."""
    PE, PL, S = h["pelat_E"], h["pelat"], h["stm_E"]
    c = h["cap_E"]
    b, gs = PE["banding"], PE["geser"]
    L = [f"**Cap E gabungan Cap C + Cap E** ({idn(c['ukuran'][0], 1)} × {idn(c['ukuran'][1], 1)} m, {c['r']['n']} tiang, jarak {idn(c['sx'], 1)} × {idn(c['sy'], 1)} m) didesain sebagai **pelat tebal di atas pegas tiang** "
         f"(keputusan Defsa 22 Nov 2026; `skrip/tahap6_cap_pelat.py`): pelat Mindlin ShellMITC4 (openseespy; sudah dipakai Tahap 4), jaring 0,4 m, Ec 4700 √f'c bruto. "
         f"Tiang = pegas vertikal k_eff = k / (FJ √n) = {idn(PE['k'], 0)} / ({idn(PE['fj'], 1)} √{PE['n']}) = {idn(PE['k_eff'] / 1e3, 1)} kN/mm tiap tiang (6.6 varian d: s = FJ Q0 √n / k) "
         "dan sendi di kepala (6.5, tanpa tahanan rotasi). Beban: dinding inti INTI-LIF (4 × 8 m, dinding 0,35 m) dan INTI-T46/39 (4 × 4 m [Asumsi]) sebagai cincin gaya vertikal linear "
         "(P dan Mux/Muy, kesetimbangan tepat), kolom (semua titik non-inti dari 6.3) 800 × 800, berat cap bersih apung (6.3, tekanan merata); kombinasi pemberi Pu maks (+ 1,2 W) dan Pu min (+ 0,9 W) dari 6.3. "
         "Tulangan dari Wood-Armer, rata-rata lajur ± 2 m; geser satu arah dari V elemen di d dari muka inti dan muka tiang (jendela 2d); pons tiang dan pons inti SNI 2847 22.6; "
         "STM (Pasal 23, βs 0,60, βn 0,60) hanya untuk tiang dalam 2d dari dinding inti.", "",
         "Pembanding reaksi tiang dengan rumus cap kaku 6.3 (Pu maks + 1,2 berat cap; toleransi ditetapkan dulu: Σ reaksi vs ΣP ≤ 0,5 %, reaksi maksimum ≤ 25 %):", ""]
    L += tabel_md(["Besaran", "Pelat", "Cap kaku 6.3", "Selisih (%)"],
                  [["Σ reaksi (kN)", idn(b["sum_fe"], 0), idn(b["sumP"], 0), idn(b["d_sum"], 4)], ["Reaksi maksimum (kN)", idn(b["max_fe"], 0), idn(b["max_kaku"], 0), idn(b["d_max"], 1)],
                   ["Reaksi minimum (kN)", idn(b["min_fe"], 0), idn(b["min_kaku"], 0), "-"],
                   ["Maks (1,2 berat cap, sama dengan baris atas) (kN)", idn(float(PE["r1"]["R"].max()), 0), "-", "-"],
                   ["Min kombinasi Pu min + 0,9 berat sendiri (kN)", idn(float(PE["r2"]["R"].min()), 0), idn(float(PE["Rmin_kaku"].min()), 0), "-"]])
    L += ["", f"Hasil: {'lolos' if b['lolos'] else 'GAGAL'}. Pelat lebih lentur daripada cap kaku sehingga reaksi menyebar ke tiang tengah (maksimum turun {idn(b['d_max'], 1)} %). "
          f"Berat cap sudah ada di beban 6.3 (revisi 22 Nov 2026, temuan 6.9; 1,2 W = {idn(c['r']['Wu'], 0)} kN, W bersih apung {idn(c['r']['W'], 0)} kN) dan dipakai di pelat sebagai tekanan merata dengan faktor yang sama "
          f"(1,2 untuk Pu maks, 0,9 untuk Pu min), jadi tidak dihitung dua kali; Pu maks per tiang {idn(float(PE['r1']['R'].max()), 0)} kN sudah lolos cek 6.3.", "",
          "Tebal pelat (rasio terhadap kapasitas; STM lokal = strut, tumpu tiang, tumpu node):", ""]
    L += tabel_md(["h (mm)", "d (mm)", "Geser 1 arah", "Pons tiang", "Pons inti", "STM lokal", "As bawah x / y (mm²/m)", "Lapis D32 maks", "Penentu", "Hasil"],
                  [[idn(hh, 0), idn(a["d"], 0), idn(a["rasio"]["geser"], 3), idn(a["rasio"]["pons_tiang"], 3), idn(a["rasio"]["pons_inti"], 3), idn(a["rasio"]["stm"], 3),
                    f"{idn(a['lentur'][('bawah', 'x')]['As_maks'], 0)} / {idn(a['lentur'][('bawah', 'y')]['As_maks'], 0)}", a["lapis_maks"], a["penentu"], "lolos" if a["lolos"] else "gagal"]
                   for hh, a in PL["hasil"].items()])
    L += ["", f"h minimum yang lolos pada pindai 1.500-2.700 (langkah 100 mm): {idn(PL['h_min'], 0) if PL['h_min'] else 'tidak ada'} mm. Model memakai **h {idn(H_E, 0)} mm** "
          f"(sesuai arahan: h Cap E dinaikkan sekali 100 mm dari 1.800 setelah berat cap masuk 6.3, tanpa iterasi otomatis): rasio penentu {PE['penentu']} {idn(max(PE['rasio'].values()), 3)}"
          + ("" if PE["lolos"] else " **> 1: h ini TIDAK lolos**; perlu h 2.000 mm (rasio pons inti 0,955) atau tulangan pons (stud/sengkang, 22.6.6) pada h 1.900: keputusan Defsa") +
          f"; geser satu arah {idn(gs['rasio'], 3)} pada penampang {gs['arah']} = {idn(gs['garis'], 2)} m (v {idn(gs['v'], 0)} kN/m terhadap φVc {idn(gs['phiVc'], 0)} kN/m); geser peka pada jaring dan letak penampang. "
          "Pons inti memakai Σ reaksi tiang di luar keliling d/2 (momen inti ditransfer lewat pasangan gaya vertikal; transfer momen geser tidak dicek).", "",
          f"Tulangan lentur h {idn(H_E, 0)} (D32; As = terbesar antara perlu, minimum 9.6.1.2 yang boleh dibatasi 4/3 perlu (9.6.1.3), dan susut 0,0018 b h per muka (24.4.3.2, usulan AI); "
          "d = h - 75 - 1,5 × 32):", ""]
    rows = []
    for (sisi, ar), v in PE["lentur"].items():
        lap, sp = v["pilih"]
        rows.append([f"{sisi}, tulangan arah {ar}", idn(v["M_maks"], 0), idn(v["req"], 0), idn(v["susut"], 0), idn(v["As_maks"], 0), f"{lap} lapis D32 - {sp} mm"])
    L += tabel_md(["Muka", "Mu lajur maks (kNm/m)", "As lentur (mm²/m)", "As susut (mm²/m)", "As desain (mm²/m)", "Susunan"], rows)
    L += ["", "Per lajur (bawah), Mu rata-rata lajur dan As:", ""]
    nb = max(len(PE["lentur"][("bawah", "x")]["As"]), len(PE["lentur"][("bawah", "y")]["As"]))
    rows = []
    for i in range(nb):
        row = [i + 1]
        for ar in ("x", "y"):
            v = PE["lentur"][("bawah", ar)]
            row += [idn(v["M"][i], 0), idn(v["As"][i], 0), f"{v['lap'][i][0]} × D32 - {v['lap'][i][1]}"] if i < len(v["As"]) else ["-", "-", "-"]
        rows.append(row)
    L += tabel_md(["Lajur", "Mu x (kNm/m)", "As x (mm²/m)", "Susunan x", "Mu y (kNm/m)", "As y (mm²/m)", "Susunan y"], rows)
    st = PE["stm"]
    L += ["", f"STM lokal (tiang dalam 2d = {idn(st['jarak'], 2)} m dari dinding inti, z = 0,85 d = {idn(st['z'], 3)} m): {st['n_stm']} tiang berstrut (θ ≥ 25°), {st['n_luar']} tiang θ < 25° (dikerjakan sebagai pelat), "
          f"rasio terbesar {idn(st['rasio'], 3)} (tumpu node {idn(st['r_node'], 3)}); tie lokal maksimum {idn(st['T_maks'], 0)} kN, As {idn(st['As_tie'], 0)} mm² (dalam tulangan bawah pelat).", "",
          f"Peta kontur momen dan reaksi: `Gambar/6.7 Cap E Pelat Momen.png`. Pembanding lama (tidak menentukan): STM global per tiang pada h {idn(H_E, 0)} memberi rasio {idn(S['rasio_stm'], 3)} "
          f"({S['n_stm']} tiang berstrut); pada h 1.500 {idn(h['tebal_E'][1500.0]['rasio_stm'], 3)} (non-monoton terhadap h; model STM per tiang tidak cocok untuk cap selebar rakit).", ""]
    return L


def tulis_md(h=None, r=None, keluar=MD):
    h = h or semua()
    r = r or t105(h)
    t30, t35 = h["tiang"][30.0], h["tiang"][35.0]
    S = h["stm_E"]
    p = h["pit"]
    sl = h["sloof"]
    L = ["# 6.7 Desain struktur tiang Ø800, pile cap, pit, dan sloof\n", LABEL,
         f"Dihitung AI atas permintaan Defsa (22 Nov 2026). STATUS: {STATUS}. Kunci jawaban tidak dibuka. "
         "Excel: `6.7 Desain Tiang dan Pile Cap.xlsx`; skrip: `skrip/tahap6_struktur.py`; uji: `tests/test_tahap6_struktur.py`; lembar isian: `6.7 Lembar Isian Tiang dan Cap.md`.\n",
         "## 1. Tujuan dan asumsi\n",
         "Menentukan tulangan tiang bor Ø800 (dua varian f'c 30 dan 35), tebal dan tulangan pile cap kolom (2, 3, 4 tiang), pile cap inti E (STM), pengangkuran pit L-1..4, "
         "dan cek sloof SL-2/SL-3 pada penurunan beda 24,6 mm (6.6). Angka masukan dari lembar isian A (6.1, 6.2, 6.3, 6.5, 5.4, 5.5, 5.6).\n",
         "- Tiang D25 memanjang, selimut 75 mm ke spiral (Tabel 20.6.1.3.1), spiral D13 fyt 420 (D10 memberi jarak bersih < 25 mm pada zona rapat). fy 420 MPa.",
         "- Diagram interaksi: serat penampang lingkaran, εcu 0,003, blok persegi β1 (0,836 untuk f'c 30; 0,80 untuk 35), φ spiral 0,75-0,90 (Tabel 21.2.2), φPn dibatasi 0,85 Po.",
         "- Kombinasi (asumsi AI): statis dengan seret Pu = 1,3 Pmax layan zona + 1,2 Qn (rasio Pu/Pmax 5.6 sekitar 1,3; seret sebagai beban mati tetap); gempa Pu 3.230/3.254 kN "
         "(6.3) tanpa Qn (6.2: kasus gempa tidak digabung); momen M 177 kNm (inersia utara) dan 966 kNm (Youd) dari 6.5; tarik Pu min -1.452 kN (Cap D).",
         "- Pile cap kolom: kepala sendi (M = 0), reaksi tiang sama Ru = Pu cap / n; kolom 800 mm (konservatif; Ringkasan 5.6 memakai 750); tulangan bawah D32 dua lapis silang, "
         "d = h - 75 - 1,5 D; tiang masuk cap 150 mm tidak mengurangi h. f'c cap 35 MPa (5.6 [Asumsi]; S2 min 31). SNI 2847:2019 tidak memakai faktor ukuran λs pada Tabel 22.5.5.1 (versi ini mengikuti ACI 318-14).",
         "- Cap E: STM per tiang (z = 0,85 d [Asumsi]); kotak inti lif 4 × 8 m dinding 0,35 m [Asumsi dari 5.5 dan 5.6]; ukuran inti sebenarnya belum ada di acuan.\n",
         "## 2. Tiang Ø800\n",
         f"Hasil (n D25 minimum yang lolos semua kasus, 0,01 Ag ≤ Ast ≤ 0,06 Ag, ≥ 6 batang):\n"]
    L += tabel_md(["f'c", "n D25 min", "ρ", "Rasio terbesar", "16 D25: rasio terbesar", "φMn pada 1.560 kN (n min / 16 D25)", "ld D25 (mm)", "Ec (MPa)"],
                  [[int(fc), t["n_min"], idn(t["cek_min"]["rho"] * 100, 2) + " %", idn(t["cek_min"]["rasio_maks"], 3), idn(t["cek16"]["rasio_maks"], 3),
                    f"{idn(next(x for x in t['cek_min']['rows'] if 'Youd' in x['nama'] and '1.560' in x['nama'])['phiMn'], 0)} / "
                    f"{idn(next(x for x in t['cek16']['rows'] if 'Youd' in x['nama'] and '1.560' in x['nama'])['phiMn'], 0)}", idn(t["panjang"]["ld"], 0), idn(t["ec"], 0)]
                   for fc, t in h["tiang"].items()])
    for fc, t in h["tiang"].items():
        L += ["", f"Cek per kasus, f'c {int(fc)}, {t['n_min']} D25 (φPn,maks {idn(t['cek_min']['kv']['phiPn_maks'], 0)} kN; φTn {idn(t['cek_min']['kv']['phiTn'], 0)} kN):", ""]
        L += tabel_md(["Kasus", "Pu (kN)", "M (kNm)", "φMn (kNm)", "Rasio"], [[x["nama"], idn(x["Pu"], 0), idn(x["M"], 0), idn(x["phiMn"], 0), idn(x["rasio"], 3)] for x in t["cek_min"]["rows"]])
    for fc, t in h["tiang"].items():
        sp, z, g = t["spiral"], zona_rapat(), t["geser"]
        pj = t["panjang"]
        L += ["", f"Spiral dan geser, f'c {int(fc)}: ρs (d) {idn(sp['rs_d'], 4)}; (e) {idn(sp['rs_e'], 4)}; s rapat {sp['s_rapat']:.0f} mm (jarak bersih {sp['bersih_rapat']:.0f} mm); "
              f"s luar zona {sp['s_luar']:.0f} mm (jarak bersih {sp['bersih_luar']:.0f} mm). Geser: φVc {idn(g['phiVc'], 0)} kN (Nu {idn(g['Nu'], 0)}), φVn rapat {idn(g['phiVn']['s_rapat'], 0)}, "
              f"luar {idn(g['phiVn']['s_luar'], 0)} kN; rasio Youd 366 kN {idn(g['rasio_youd'], 2)}, inersia 53,95 kN {idn(g['rasio_inersia'], 2)}.",
              f"Panjang: zona rapat dari kepala {idn(z['SELATAN']['rapat'], 2)} m (selatan, 7D di bawah dasar U5; 18.13.4.3 a menghasilkan {idn(z['SELATAN']['a'], 1)} m) dan {idn(z['UTARA']['rapat'], 2)} m (utara). "
              f"Tulangan: (a) tiang cap inti penuh {idn(pj['penuh'], 2)} m; (b) tiang cap kolom sampai elev. {idn(pj['elev_b'], 2)} ({idn(pj['L_b'], 2)} m, ld {idn(pj['ld'], 0)} mm, usulan AI); (c) penuh semua."]
    L += ["", f"Layan: (Pmax + Qn)/Ag selatan {idn(h['tiang'][35.0]['cek_min']['layan']['SELATAN'], 2)} MPa, utara {idn(h['tiang'][35.0]['cek_min']['layan']['UTARA'], 2)} MPa terhadap 0,33 f'c "
          f"({idn(0.33 * 30, 1)} dan {idn(0.33 * 35, 1)} MPa) [Asumsi: praktik, bukan SNI].", "",
          "## 3. Pile cap kolom\n",
          "Tiap tipe memakai cap dengan Pu per tiang terbesar (2/A, 2/D, 4/B). Tebal terkecil yang lolos di antara 700-1.200 mm (langkah 50):\n"]
    rows = []
    for n in (2, 3, 4):
        e = h["cap_kolom"][n]
        u = e["usul"]
        rows.append([f"{n} tiang ({e['cap']['id']})", f"{idn(u['ukuran'][0], 1)} × {idn(u['ukuran'][1], 2)}", idn(u["Ru"], 0), idn(u["h"], 0), idn(u["d"], 0), idn(u["geser"]["rasio"], 3),
                     idn(u["pons_kolom"]["rasio"], 3), idn(u["pons_tiang"]["rasio"], 3), u["penentu"], idn(e["h1000"]["rasio"], 3) + ("" if e["h1000"]["lolos"] else " (gagal)"),
                     idn(e["h1200"]["rasio"], 3)])
    L += tabel_md(["Tipe", "Ukuran (m)", "Ru (kN)", "h usulan (mm)", "d (mm)", "Geser 1 arah", "Pons kolom", "Pons tiang", "Penentu", "Rasio h 1.000", "Rasio h 1.200"], rows)
    L += ["", "Lentur (h usulan) dan stek:", ""]
    rows = []
    for n in (2, 3, 4):
        e = h["cap_kolom"][n]["usul"]
        lx, ly = e["lentur"]["x"], e["lentur"]["y"]
        rows.append([f"{n} tiang", idn(lx["Mu"], 0), idn(lx["As"], 0), f"{lx['n32']} D32", idn(ly["Mu"], 0), idn(ly["As"], 0), f"{ly['n32']} D32", idn(e["stek"]["h_min"], 0),
                     idn(e["stek"]["tersedia"], 0), idn(lx["tersedia"], 0) + " / " + idn(lx["ld"], 0)])
    L += tabel_md(["Tipe", "Mu x (kNm)", "As x (mm²)", "Batang x", "Mu y (kNm)", "As y (mm²)", "Batang y", "h min stek (mm)", "Tersedia kait (mm)", "Tersedia / ld lurus (mm)"], rows)
    L += ["", "As = terbesar antara lentur dan 0,0018 b h (Tabel 24.4.3.2, penerapan ke cap: usulan AI). h min stek = ldh K-P D25 426 + 75 + 2 × 32 (lembar isian A.4) dan ≥ 488,3 (kait sloof SL-1).", "",
          "## 4. Cap inti\n"]
    L += md_pelat(h)
    L += ["", "Enam cap inti (h 1.200; Cap E h 1.500; f'c 35): Pu maks per tiang dan pons tiang sudut:", ""]
    L += tabel_md(["Cap", "n", "Ukuran (m)", "Pu maks/tiang (kN)", "Pu min/tiang (kN)", "φVc pons (kN)", "Rasio"],
                  [[x["id"], x["n"], f"{idn(x['ukuran'][0], 1)} × {idn(x['ukuran'][1], 1)}", idn(x["Pu_maks"], 0), idn(x["Pu_min"], 0), idn(x["pons_tiang"]["phiVc"], 0), idn(x["rasio"], 3)] for x in h["inti"]])
    g = p["geom"]
    L += ["", "## 5. Pit L-1..4\n",
          f"Varian A (berat sendiri, t 0,45): U {idn(p[0.45]['U'], 1)} kN, W {idn(p[0.45]['W'], 1)} kN, FK {idn(p[0.45]['FK'], 3)} (≥ 1,1, SNI 8460 9.3.4 b: lolos tipis; t 0,40: {idn(p[0.40]['FK'], 3)}, gagal). "
          f"Varian B (diikat, FK 1,5, 9.3.3 b): R = 1,5 U - W = {idn(p[0.40]['R'], 1)} kN (t 0,40) / {idn(p[0.45]['R'], 1)} kN (t 0,45); stek As {idn(p[0.40]['As'], 0)} / {idn(p[0.45]['As'], 0)} mm². "
          f"Temuan: tapak pit x 51,10-56,90 menjorok {idn(g['menjorok'], 2)} m di luar tepi timur Cap E (x {idn(g['x_tepi'], 1)}); hanya {idn(g['frak_dalam'] * 100, 0)} % tapak di dalam cap; "
          f"dasar pit +{idn(g['dasar_pit'], 2)} sama dengan dasar cap +{idn(g['dasar_cap'], 2)} (muka cap +{idn(g['atas_cap'], 2)}), jadi pit bentrok volume dengan cap pejal. Kapasitas angkur: SNI 8460 pasal 10.6 hanya angkur tanah (belum ada di acuan untuk ikatan ke cap).\n",
          "## 6. Sloof SL-2 dan SL-3 pada δ 24,6 mm\n"]
    L += tabel_md(["Tipe", "Mu- grav. (kNm)", "M penurunan (kNm)", "Mu- total (kNm)", "φMn- (kNm)", "Rasio Mu-", "Rasio Mu+", "Rasio terbesar"],
                  [[k, idn(v["Mgrav_neg"], 1), idn(v["M_pen"], 0), idn(v["Mu_neg"], 1), idn(v["phiMn_neg"], 1), idn(v["r_neg"], 3), idn(v["r_pos"], 3), idn(v["rasio"], 3)] for k, v in sl.items()])
    L += ["", "Pola 5.4 (1,2D + 1,6L + 1,0T): momen penurunan ditambahkan ke momen negatif gravitasi. Rasio < 1: tulangan 5.4 cukup, tidak perlu tambahan. SL-1 400 × 900: M 545 kNm, rasio 0,65 (6.6, dicatat). Catatan 6.6: rasio SL-1 pada δ 16 mm kode 0,534 vs teks 5.4 0,48.\n",
          "## 7. Verifikasi T-105\n",
          f"Toleransi ditetapkan dulu: (a) hitung tangan vs skrip ≤ 2 %; (b) Excel vs Python ≤ 0,1 %; (c) gaya tie STM (M / z) vs pendekatan balok lentur (Mu / (d - a/2)) ≤ 30 %. Hasil: (a) {idn(r['dt'], 3)} %; (b) {idn(r['dxl'], 4) if r['dxl'] is not None else 'n/a'} %; "
          f"(c) {idn(r['dstm'], 1) if r['dstm'] is not None else 'n/a'} %. {'Lolos' if r['lolos'] else 'GAGAL'}.\n",
          "## 8. Keputusan yang dibutuhkan dari Defsa\n"]
    L += KEPUTUSAN_DEFSA + [revisi_cap_c(h), ""]
    L += [f"{i + 1}. {t}" for i, t in enumerate(keputusan(h))]
    L += ["", "## 9. Sumber", ""] + [f"- {a[0]} ({a[1]}): {a[2]}." for a in ACUAN]
    L += ["", f"Status: {STATUS}."]
    Path(keluar).write_text("\n".join(L) + "\n", encoding="utf-8")
    return keluar


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    from format_dokumen import hitung_ulang_excel
    h = semua()
    for fc, t in h["tiang"].items():
        print("f'c", fc, "n min", t["n_min"], "rasio", round(t["cek_min"]["rasio_maks"], 3), "16D25", round(t["cek16"]["rasio_maks"], 3), t["cek16"]["lolos"])
    for n in (2, 3, 4):
        u = h["cap_kolom"][n]["usul"]
        print("cap", n, u["id"], "h", u["h"], u["penentu"], round(u["rasio"], 3), "h1200", round(h["cap_kolom"][n]["h1200"]["rasio"], 3))
    S = h["stm_E"]
    print("STM", S["n_stm"], S["n_luar"], S["rasio_stm"], S["dev_stm_beam"])
    import tahap6_cap_pelat as cp
    print(cp.gambar(h["pelat_E"], h["cap_E"]))
    berkas, adr = buat_excel(h=h)
    print(berkas, hitung_ulang_excel(berkas))
    r = t105(h, berkas, adr)
    print(r)
    catat_t105(r, h)
    print(tulis_md(h=h, r=r))


if __name__ == "__main__":
    main()
