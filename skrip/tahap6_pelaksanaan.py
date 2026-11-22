"""Tahap 6, langkah 6.8: interpretasi uji beban statis TP-1..4, program uji akhir, dewatering galian cap, urutan kerja.

Data SIMULASI. Sumber: `06 Struktur Bawah dan Basement/Data Uji/` (kurva TP-1..4, PDA, PIT, CSL), 6.2 (izin, Q+Qn, k 489 kN/mm),
6.3 (cap), 6.5 (lateral), 6.6 (sisa penurunan), 6.7 (tebal cap, Cap E pelat h 1.800 usulan Defsa, hasil 6.7), `6.8 Lembar Isian Uji dan Pelaksanaan.md`,
SNI 8460:2017 Ps. 9.8 (hal. PDF 205-209), Ps. 11 (hal. PDF 277, 279), FHWA GEC10 bab 13, 14, 16, 17, NHI-06-089 hal. 275-276 (Davisson).
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tahap3_pondasi as p3  # noqa: E402
import tahap6_struktur as ts  # noqa: E402
import tahap6_tata_letak as tl_  # noqa: E402

H_E = ts.H_E                                          # tebal Cap E (6.7, pelat)
HE_LABEL = f"{H_E:,.0f}".replace(",", ".")
DASAR_E = round(12.05 - H_E / 1e3, 2)                 # m, dasar Cap E (muka cap +12,05)
DASAR_E_TXT = f"{DASAR_E:.2f}".replace(".", ",")
E_UK = tuple(next(c for c in tl_.rancang("a")[1] if c["kode"] == "E")["ukuran"])      # m, telapak Cap E gabungan (6.3)

AKAR = Path(__file__).resolve().parents[1]
KELUAR = AKAR / "06 Struktur Bawah dan Basement"
UJI = KELUAR / "Data Uji" / "Uji Beban Statis Tiang.xlsx"
BERKAS = KELUAR / "6.8 Uji Tiang dan Pelaksanaan.xlsx"
MD = KELUAR / "6.8 Uji Tiang dan Pelaksanaan.md"
VERIFIKASI = AKAR / "VERIFIKASI.md"

LABEL = "DATA SIMULASI untuk studi kasus portofolio. Bukan data proyek nyata. Tidak untuk konstruksi."
STATUS = "disetujui Defsa 22 Nov 2026 (usulan AI)"
LABEL_AI = f"DIHITUNG AI ATAS PERMINTAAN DEFSA (22 Nov 2026), sel hijau; STATUS: {STATUS}. Kunci jawaban tidak dibuka."
TOL = {"tangan": 2.0, "excel": 0.1, "orde": 100.0, "k": 1.0}      # %, ditetapkan sebelum membandingkan

D = 0.8
AG = math.pi * D ** 2 / 4
EC = {30.0: 4700 * math.sqrt(30.0), 35.0: 4700 * math.sqrt(35.0)}   # MPa
BEBAN_KERJA = 911.0
K_6_6 = 489.0                          # kN/mm (6.6)
IZIN = {"SELATAN": 1583.0, "UTARA": 1443.0}
PU_MAKS, PU_TARIK = 3254.0, 1452.0
FK_PERLU = 2278.0                      # kN, 2,5 x 911 (6.2)
import tahap6_tata_letak as _tl  # noqa: E402
_RK = _tl.ringkas("a")
N_TOTAL, N_UTAMA, N_TARIK = _RK["total"], _RK["n"], _RK["n_inti"]   # 298, 230, 78 setelah Cap C digabung ke Cap E (22 Nov 2026)
ADA = {"statik": 4, "tarik": 0, "lateral": 0, "PDA": 10, "PDA_kerja": 8, "PIT": 40, "CSL": 24, "CSL_kerja": 20}
LAT = {"H": 53.95, "y_sendi_selatan": 15.29, "y_sendi_utara": 26.01}      # kN, mm (6.5: sendi, U5 pengali 0,1)
PANJANG_TP = {"TP-1": 37.01, "TP-2": 37.01, "TP-3": 37.97, "TP-4": 37.82}
ZONA_TP = {"TP-1": "UTARA", "TP-2": "UTARA", "TP-3": "SELATAN", "TP-4": "SELATAN"}
SISA_RINGKASAN = {"TP-1": 1.96, "TP-2": 2.42, "TP-3": 1.78, "TP-4": 1.81}   # mm, lembar Ringkasan
CAPWAP = {"TP-1": 3912.0, "TP-3": 3665.0}                                     # Ru kN


def idn(v, d=1):
    return f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ================================================================== A. uji statik
def baca_kurva(tp, berkas=UJI):
    """Envelope beban-penurunan: akhir tahap tiap kali beban naik ke maksimum baru; (beban load cell kN, penurunan rata-rata mm)."""
    import openpyxl
    ws = openpyxl.load_workbook(berkas, data_only=True)[f"Kurva {tp}"]
    rows = [[x for x in r if x is not None] for r in ws.iter_rows(min_row=5, values_only=True)]
    rows = [r for r in rows if len(r) >= 10 and isinstance(r[1], (int, float))]
    tahap, prev = [], None
    for r in rows:
        if r[1] != prev:
            tahap.append(r)
            prev = r[1]
        else:
            tahap[-1] = r
    env, mak = [(0.0, 0.0)], -1.0
    for r in tahap:
        if r[1] > mak:
            env.append((float(r[2]), float(r[-1])))
            mak = r[1]
    sisa = float(tahap[-1][-1])
    return dict(env=env, sisa=sisa, tahap=[(r[1], float(r[2]), float(r[-1])) for r in tahap])


def davisson(p_kn, panjang, fc=30.0):
    """s_D = P L / (A E) + 4 mm + D / 120 (NHI-06-089 hal. 275-276); P kN, L m, hasil mm."""
    ae = EC[fc] * 1e3 * AG                  # kN
    return p_kn * panjang / ae * 1e3 + 4.0 + D * 1e3 / 120.0


def chin(env):
    """Chin-Kondner: s/P = C1 s + C2 pada titik 50-200 %; Qult = 1/C1 (ekstrapolasi, [Literatur: belum ada di acuan/])."""
    pts = [(p, s) for p, s in env if p >= 0.45 * BEBAN_KERJA]
    s = np.array([x[1] for x in pts])
    y = np.array([x[1] / x[0] for x in pts])
    c1, c2 = np.polyfit(s, y, 1)
    return dict(C1=float(c1), C2=float(c2), Qult=float(1 / c1), P25=float(25.0 / (c1 * 25.0 + c2)))


def interpolasi(env, p):
    ps, ss = zip(*env)
    return float(np.interp(p, ps, ss))


def statik(fc=30.0):
    out = {}
    for tp in PANJANG_TP:
        k = baca_kurva(tp)
        env = k["env"]
        pm, sm = env[-1]
        p100 = min(env, key=lambda x: abs(x[0] - BEBAN_KERJA))
        ch = chin(env)
        dv = davisson(pm, PANJANG_TP[tp], fc)
        # Davisson: penurunan kurva vs garis pada tiap titik
        perpotong = any(s >= davisson(p, PANJANG_TP[tp], fc) for p, s in env if p > 0)
        out[tp] = dict(env=env, Pmaks=pm, s200=sm, sisa=k["sisa"], P100=p100[0], s100=p100[1], k100=p100[0] / p100[1],
                       s_davisson=dv, davisson_tercapai=perpotong, elastis=pm * PANJANG_TP[tp] / (EC[fc] * 1e3 * AG) * 1e3,
                       chin=ch, lolos_25=sm <= 25.0, lolos_12=k["sisa"] <= 12.0)
    ks = [v["k100"] for v in out.values()]
    return dict(tp=out, k_rata=float(np.mean(ks)), k_6_6=K_6_6, dev_k=abs(float(np.mean(ks)) - K_6_6) / K_6_6 * 100, fc=fc)


# ================================================================== B. program uji
def jumlah_uji():
    """SNI 8460 9.8 (hal. PDF 206-209): 1 per 75 (statik), 1 % N, 1 per 100 tiang tarik, 1 per 20 (CSL), 1 per 5 (PIT), PDA <= 4 x 40 % statik."""
    out = {}
    for nama, n in (("utama", N_UTAMA), ("total", N_TOTAL)):
        s75, s1 = n / 75, 0.01 * n
        statik_ = math.ceil(max(s75, s1))
        out[nama] = dict(n=n, statik_75=s75, statik_1pct=s1, statik=statik_, konstruksi=math.ceil(0.4 * statik_), pda_maks=4 * 0.4 * statik_,
                         csl=math.ceil(n / 20), csl_ex=n / 20, pit=math.ceil(n / 5), pit_ex=n / 5, tarik=math.ceil(N_TARIK / 100), lateral=1)
    return out


def tambahan(j=None):
    j = j or jumlah_uji()
    t = j["total"]
    return dict(statik=max(t["statik"] - ADA["statik"], t["konstruksi"]), konstruksi=t["konstruksi"], pit=t["pit"] - ADA["PIT"], pit_utama=j["utama"]["pit"] - ADA["PIT"],
                csl=max(0, t["csl"] - ADA["CSL_kerja"]), pda=max(0, math.floor(t["pda_maks"]) - ADA["PDA_kerja"]), tarik=t["tarik"], lateral=t["lateral"])


def beban_uji():
    st = {z: 2 * IZIN[z] for z in IZIN}
    lat = dict(duax=2 * LAT["H"], y_selatan=LAT["y_sendi_selatan"], y_utara=LAT["y_sendi_utara"])
    ae = EC[35.0] * 1e3 * AG
    tarik = dict(P=1.5 * PU_TARIK, pu_min=PU_TARIK, batas=1.5 * PU_TARIK * 38.45 / ae * 1e3 + 4.0)     # mm, PL/EA + 4 mm (9.8.2), EA beton bruto
    return dict(statik=st, fk25=FK_PERLU, lat=lat, tarik=tarik, selisih_1822=st["SELATAN"] - 1822.0, pu_vs_uji=PU_MAKS / 1822.0)


def lokasi_uji():
    """Usulan letak tiang uji tambahan per zona dari cap hasil 6.3 (tiang berbeban terbesar) dan tiang tarik terbesar (Cap D)."""
    import tahap6_struktur as t7
    import tahap6_tata_letak as tl
    ck, ci = tl.rancang("a")
    caps = ck + ci
    tb = tl.titik_beban()
    out = {}
    for z in ("SELATAN", "UTARA"):
        c = max((c for c in caps if c["zona"] == z), key=lambda c: c["r"]["P_layan"])
        pl = c["r"]["P_lay_semua"]
        i = int(np.argmax(pl))
        out[z] = dict(cap=c["id"], x=float(c["pos"][i][0]), y=float(c["pos"][i][1]), P=float(pl.max()))
    tg = [t for t in tb.values() if t["zona"] == "TENGAH"]
    if tg:
        t = max(tg, key=lambda q: q["Pmax"])
        cc = next((c for c in caps if any(tt["nama"] == t["nama"] for tt in c["titik"])), None)
        if cc:
            pl = cc["r"]["P_lay_semua"]
            i = int(np.argmax(pl))
            out["TENGAH"] = dict(cap=cc["id"], x=float(cc["pos"][i][0]), y=float(cc["pos"][i][1]), P=float(pl.max()), titik=t["nama"])
    cd = next(c for c in ci if c["kode"] == "D")
    _, rmin, _, _ = t7.muatan_tiang_cap(cd)
    i = int(np.argmin(rmin))
    out["TARIK"] = dict(cap="Cap D", x=float(cd["pos"][i][0]), y=float(cd["pos"][i][1]), P=float(rmin.min()))
    return out


T113 = dict(x=46.4, y=41.8, cap_lod200="C031", cap_63="Cap E (gabungan; semula Cap C: INTI-T46/39 + 5/B + 5/C, digabung ke Cap E 22 Nov 2026)", csl="D 3 profil, G 3 profil")


# ================================================================== C. dewatering
MUKA_AIR, Q50 = 11.20, 11.85
URUGAN = 11.50
BASE_FILL = {"SELATAN": 9.95, "UTARA": 9.23}          # muka tanah asli = dasar urugan (6.5, tahap3_pondasi.PROFIL)
K_SKEN = (1e-6, 1e-5, 1e-4)                           # m/s [Asumsi: k urugan dan U1 belum ada di Tahap 2]
KERJA = 1.0                                           # m ruang kerja tiap sisi [Asumsi]
TURUN_BAWAH = 0.5                                     # m drawdown di bawah dasar (arahan)
BATAS_GUDANG = 8.6
GUDANG_X, TIANG_UTIL_X = 144.0, 135.2                 # 2.7 (tahap3_pondasi.GUDANG_X); 6.0 tiang utilitas terdekat
TEPI_CAP = 0.8
CAP_DEW = [   # nama, dasar cap (m), panjang, lebar (m)
    ("Kolom 3 tiang h 800", 11.25, 4.0, 3.68), ("Kolom 4 tiang h 950", 11.10, 4.0, 4.0), ("Kolom 2 tiang h 1.000", 11.05, 4.0, 1.6),
    ("Cap h 1.200 (4 tiang)", 10.85, 4.0, 4.0), (f"Cap E h {HE_LABEL} (pelat, 6.7)", DASAR_E, E_UK[0], E_UK[1]), ("Pit L-1..4 (t 0,45)", 10.80, 5.8, 6.8)]


def sumur_ekuivalen(k, base, dasar, pj, lb):
    """Galian persegi panjang sebagai sumur ekuivalen (Dupuit, akuifer bebas di atas dasar kedap = dasar urugan): Q = π k (H² - h²) / ln(R / re),
    R = re + 3000 s √k (Sichardt, s dalam m, k dalam m/s)."""
    a, b = pj + 2 * KERJA, lb + 2 * KERJA
    re = math.sqrt(a * b / math.pi)
    target = dasar - TURUN_BAWAH
    s = max(0.0, MUKA_AIR - target)
    H = MUKA_AIR - base
    h = max(0.02, target - base)
    if s <= 0:
        return dict(a=a, b=b, re=re, target=target, s=0.0, H=H, h=h, Rs=0.0, R=re, Q=0.0, Qp=0.0)
    Rs = 3000.0 * s * math.sqrt(k)
    R = re + Rs
    q = math.pi * k * (H ** 2 - h ** 2) / math.log(R / re)
    qp = k * (H ** 2 - h ** 2) * 2 * (a + b) / (2 * Rs)            # pembanding: aliran 1-D tiap sisi
    return dict(a=a, b=b, re=re, target=target, s=s, H=H, h=h, Rs=Rs, R=R, Q=q, Qp=qp)


def muka_air_x(res, k, base, x):
    """Muka air (elevasi) pada jarak x dari tepi galian; Dupuit h(r)² = h² + (H² - h²) ln(r/re) / ln(R/re); = +11,20 di luar R."""
    if res["s"] <= 0 or x >= res["Rs"]:
        return MUKA_AIR
    r = res["re"] + x
    h2 = res["h"] ** 2 + (res["H"] ** 2 - res["h"] ** 2) * math.log(r / res["re"]) / math.log(res["R"] / res["re"])
    return base + math.sqrt(h2)


def dewatering():
    out = []
    for nama, dasar, pj, lb in CAP_DEW:
        for z, base in BASE_FILL.items():
            for k in K_SKEN:
                r = sumur_ekuivalen(k, base, dasar, pj, lb)
                r.update(nama=nama, dasar=dasar, zona=z, k=k, galian=URUGAN - dasar, di_bawah_air=MUKA_AIR - dasar, base=base)
                out.append(r)
    return out


def profil_x(res, k, base, xs=(5, 8, 10, 15, 20, 30)):
    return [(x, muka_air_x(res, k, base, x)) for x in xs]


def heave(target=None):
    """Angkat dasar galian oleh tekanan artesis U5 (tinggi tekan +11,20): FS = tegangan total di puncak U5 / u. Profil p3.PROFIL; urugan 19 kN/m³."""
    out = {}
    for prof in ("SELATAN", "UTARA", "TENGAH"):
        pf = p3.PROFIL[prof]
        elev = pf["elev"]
        atas, sig = 0.0, 0.0
        for unit, bawah, g, *_ in pf["lapisan"]:
            if unit == "U5":
                break
            sig += g * (bawah - atas)
            atas = bawah
        elev_u5 = elev - atas
        u = 9.81 * (MUKA_AIR - elev_u5)
        for nm, dasar in (("Cap h 800", 11.25), (f"Cap E h {HE_LABEL}", DASAR_E), ("Pit", 10.80)):
            e = dasar - TURUN_BAWAH if target is None else target
            tambah = 19.0 * (e - elev)        # urugan di atas muka tanah asli sampai dasar penggalian (dikurangi bila e < elev)
            out[(prof, nm)] = dict(elev_u5=elev_u5, sig=sig + tambah, u=u, FS=(sig + tambah) / u, e=e)
    return out


def delta_sigma(s):
    return 9.81 * s


# ================================================================== D. urutan
def urutan():
    return [
        ("1", "Survei kondisi gudang timur (retak lama, patok), pasang patok gudang, piezometer, inklinometer INC-3", "sebelum pekerjaan dalam 20 m (permintaan pemilik 14 Jul 2027); pemberitahuan 3 hari", "Data Gudang Timur"),
        ("2", "Urugan bertahap ±1 m dengan PVD segitiga 1,2 m (±5 bulan per tahap), hingga +11,50", "tebal urugan 0,95-2,68 m: 1-3 tahap; hamparan tahap 1 mulai 26 Feb 2027", "2.8, 3.3"),
        ("3", "Tunggu konsolidasi: sisa penurunan setelah tiang selatan 271, tengah 581, utara 874 mm", "batas lantai dan sloof: 6.6 varian d (δ 22,2 mm); INC-1 laju 0,177 mm/hari (batas 0,18)", "6.2, 6.6, 6.4"),
        ("4", "Bor tiang gedung utama; uji PDA/PIT/CSL tiang kerja; tiang uji statik tambahan", "tiang dicor mulai 3 Mei 2027; radius 6 m tiang uji tidak diurug", "Data Uji"),
        ("5", "Uji statik tambahan, uji tarik dan lateral (setelah umur beton ≥ 28 hari)", "T088: PDA umur 5 hari tidak sahih", "SNI 8460 9.8"),
        ("6", "Galian cap per zona: selatan lebih dulu, utara terakhir; dewatering sump terbuka; Cap E dan pit dengan sumur dangkal", f"dasar galian +{DASAR_E_TXT} sampai +11,25; muka air tidak di bawah +8,6 di sisi gudang", "6.7, 6.8"),
        ("7", "Papas kepala tiang, PIT/CSL susulan, cor cap dan stek", "kepala tiang +10,85", "6.7"),
        ("8", "Sloof, pelat LT1, urugan balik", "sloof setelah penurunan beda memenuhi 22,2 mm", "5.4, 6.6"),
    ]


# ================================================================== semua
def semua():
    h = dict(statik=statik(30.0), statik35=statik(35.0), jumlah=jumlah_uji(), beban=beban_uji())
    h["tambahan"] = tambahan(h["jumlah"])
    h["lokasi"] = lokasi_uji()
    h["dew"] = dewatering()
    h["heave"] = heave()
    return h


# ================================================================== Excel
ACUAN = [
    ("SNI 8460:2017 9.8, 9.8.1", "hal. PDF 205-207", "uji aksial tekan: min 1 per 75 tiang bor, + 1,0 % N, ≥ 40 % saat konstruksi, 200 %, 25 mm (Ø ≤ 80 cm), permanen 12 mm"),
    ("SNI 8460:2017 9.8.2, 9.8.3", "hal. PDF 207-208", "tarik 1 per 100 tiang tarik (PL/EA + 4 mm, maks 25 mm); lateral 1 per ukuran (10 mm @100 %, 25 mm @200 %)"),
    ("SNI 8460:2017 9.8.4-9.8.6", "hal. PDF 208-209", "PDA (≤ 4 × 40 % statik, ditafsirkan), CSL 1 per 20, PIT 1 per 5"),
    ("SNI 8460:2017 9.5.3.4, Pasal 11", "hal. PDF 201, 277, 279", "air tanah dan dewatering; dampak dewatering ke fondasi eksisting; kriteria drawdown galian dangkal: belum ada di acuan"),
    ("NHI-06-089 (Davisson)", "hal. 275-276 (dari 6.2)", "s = PL/AE + 4 mm + D/120"),
    ("Chin (1970)", "-", "[Literatur: belum ada di acuan/]; ekstrapolasi hiperbola s/P = C1 s + C2"),
    ("Dupuit, Sichardt", "-", "[Literatur: belum ada di acuan/]; R = 3000 s √k (s m, k m/s)"),
    ("FHWA GEC10 13.1.2-13.1.4, 14.6, 14.7", "hal. PDF 393-395, 467-468", "program uji dan proof test; uji beban dan integritas pada spesifikasi"),
    ("FHWA GEC10 16.2-16.3, 16.4", "hal. PDF 492-516 (16.3 coring hal. 513)", "metode integritas, drilling dan coring, uji beban evaluasi integritas"),
    ("FHWA GEC10 17.2.2, 17.4, 17.5.2-17.5.5", "hal. PDF 519, 525, 528-534", "evaluasi cacat; perbaikan: tiang pengganti, penggantian, perkuatan struktur, grouting"),
]


def buat_excel(keluar=BERKAS, h=None):
    import openpyxl
    from format_dokumen import AI, Lembar, set_font_bawaan
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
        ["Ringkasan", "Hasil kunci uji statik, program uji, dewatering"],
        ["Statik", "Envelope TP-1..4, garis Davisson, Chin, kekakuan k (rumus hidup)"],
        ["Program", "Jumlah uji perlu vs ada vs tambahan (rumus hidup), beban uji, letak usulan"],
        ["Dewatering", "Sumur ekuivalen Dupuit-Sichardt per cap dan k (rumus hidup), muka air s(x), heave artesis"],
        ["Urutan", "Urutan kerja dan syarat"], ["Verifikasi", "T-106"], ["Acuan", "Pasal dan halaman"], ["Keputusan", "Keputusan Defsa"]], rata=["l", "l"], beku=False)

    # ---- Statik
    ls = Lembar(wb.create_sheet("Statik"), 3, "Uji statik TP-1..4: Davisson, Chin, kekakuan", [18, 16, 16, 16, 16, 16, 16, 36])
    ls.catatan(ket)
    ls.kosong()
    ls.bagian("A", "Titik ukur (akhir tahap, beban naik ke maksimum baru; load cell) dan garis Davisson (rumus hidup, Ec f'c 30)")
    adr["statik"] = {}
    ae_row = ["EA = Ec A (kN), f'c 30", EC[30.0] * 1e3 * AG, "", "", "", "", "", "SNI 2847 Ps. 19.2.2.1; sama dengan 6.6"]
    r0, a, b = ls.tabel(["Besaran", "Nilai", "", "", "", "", "", "Sumber"], [ae_row, ["D/120 + 4 mm", None, "", "", "", "", "", "Davisson (NHI-06-089 hal. 275-276)"]],
                        rata=["l", "r", "r", "r", "r", "r", "r", "l"], fmt=[None, "#,##0", None, None, None, None, None, None], fill_kolom={1: AI}, beku=False)
    EAc = f"{ls.kol(1)}{r0 + 1}"
    ls.ws[f"{ls.kol(1)}{r0 + 2}"] = "=4+800/120"
    ls.ws[f"{ls.kol(1)}{r0 + 2}"].number_format = "0.000"
    D4 = f"{ls.kol(1)}{r0 + 2}"
    ls.ws[f"{ls.kol(1)}{r0 + 1}"] = f"=4700*SQRT(30)*1000*PI()*0.8^2/4"
    ls.kosong()
    for tp, v in h["statik"]["tp"].items():
        L = PANJANG_TP[tp]
        rows = [[f"{int(round(p / BEBAN_KERJA * 100))} %", p, s, None, None, "", "", ""] for p, s in v["env"] if p > 0]
        rr, a, b = ls.tabel([f"{tp} (L {idn(L, 2)} m)", "Beban (kN)", "s (mm)", "s_Davisson (mm)", "s / P (mm/kN)", "", "", ""], rows,
                            rata=["l", "r", "r", "r", "r", "r", "r", "r"], fmt=[None, "#,##0", "0.00", "0.00", "0.00000", None, None, None], fill_kolom={1: AI, 2: AI, 3: AI, 4: AI}, beku=False)
        for i in range(len(rows)):
            row = rr + 1 + i
            ls.ws[f"{ls.kol(3)}{row}"] = f"={ls.kol(1)}{row}*{L}/{EAc}*1000+{D4}"
            ls.ws[f"{ls.kol(4)}{row}"] = f"={ls.kol(2)}{row}/{ls.kol(1)}{row}"
        # Chin dari titik P >= 50 % (baris dengan beban >= 0,45 x 911)
        idx = [i for i, (p, s) in enumerate([x for x in v["env"] if x[0] > 0]) if p >= 0.45 * BEBAN_KERJA]
        r1, r2 = rr + 1 + idx[0], rr + 1 + idx[-1]
        rows2 = [["C1 = SLOPE(s/P, s)", None, "Qult Chin = 1/C1 (kN)", None, "k100 = P100 / s100 (kN/mm)", None, "", ""]]
        rc, _, _ = ls.tabel(["Besaran", "Nilai", "Besaran", "Nilai", "Besaran", "Nilai", "", ""], rows2, rata=["l", "r", "l", "r", "l", "r", "r", "r"], fill_kolom={1: AI, 3: AI, 5: AI}, beku=False)
        ro = rc + 1
        i100 = next(i for i, (p, s) in enumerate([x for x in v["env"] if x[0] > 0]) if abs(p - BEBAN_KERJA) < 20)
        ls.ws[f"{ls.kol(1)}{ro}"] = f"=SLOPE({ls.kol(4)}{r1}:{ls.kol(4)}{r2},{ls.kol(2)}{r1}:{ls.kol(2)}{r2})"
        ls.ws[f"{ls.kol(3)}{ro}"] = f"=1/{ls.kol(1)}{ro}"
        ls.ws[f"{ls.kol(5)}{ro}"] = f"={ls.kol(1)}{rr + 1 + i100}/{ls.kol(2)}{rr + 1 + i100}"
        ls.ws[f"{ls.kol(1)}{ro}"].number_format = "0.000000"
        ls.ws[f"{ls.kol(3)}{ro}"].number_format = "#,##0"
        ls.ws[f"{ls.kol(5)}{ro}"].number_format = "0.0"
        adr["statik"][tp] = {"Qult": f"{ls.kol(3)}{ro}", "k100": f"{ls.kol(5)}{ro}", "D200": f"{ls.kol(3)}{rr + len(rows)}"}
        ls.kosong()

    # ---- Program
    lg = Lembar(wb.create_sheet("Program"), 4, "Program uji: perlu, ada, tambahan; beban uji", [46, 16, 16, 16, 62])
    lg.catatan(ket)
    lg.kosong()
    lg.bagian("A", "Jumlah uji SNI 8460 9.8 (rumus hidup)")
    rows = [["N gedung utama / total", N_UTAMA, N_TOTAL, "", "6.3"],
            ["Statik: 1 per 75 (N / 75)", None, None, "", "9.8.1 a)"], ["Statik: 1,0 % N", None, None, "", "9.8.1 (N ≤ 1000)"],
            ["Statik perlu = bulat ke atas (nilai terbesar, tafsir AI)", None, None, "", "usulan AI"], ["Statik ada", ADA["statik"], ADA["statik"], "", "Data Uji"],
            ["Statik tambahan", None, None, "", ""], ["Statik saat konstruksi ≥ 40 %", None, None, "", "9.8.1"],
            ["CSL perlu (N / 20)", None, None, "", "9.8.5"], ["PIT perlu (N / 5)", None, None, "", "9.8.6"], ["PIT ada", ADA["PIT"], ADA["PIT"], "", "Data Uji"],
            ["PIT tambahan", None, None, "", ""], ["PDA maks = 4 × 40 % statik", None, None, "", "9.8.4 (tafsir)"]]
    r0, a, b = lg.tabel(["Butir", "Gedung utama", f"Total {N_TOTAL}", "", "Sumber"], rows, rata=["l", "r", "r", "r", "l"], fmt=[None, "0.00", "0.00", None, None], fill_kolom={1: AI, 2: AI}, beku=False)
    G = lambda i, k: f"{lg.kol(k)}{r0 + 1 + i}"
    for k in (1, 2):
        lg.ws[G(1, k)] = f"={G(0, k)}/75"
        lg.ws[G(2, k)] = f"=0.01*{G(0, k)}"
        lg.ws[G(3, k)] = f"=ROUNDUP(MAX({G(1, k)},{G(2, k)}),0)"
        lg.ws[G(5, k)] = f"={G(3, k)}-{G(4, k)}"
        lg.ws[G(6, k)] = f"=ROUNDUP(0.4*{G(3, k)},0)"
        lg.ws[G(7, k)] = f"=ROUNDUP({G(0, k)}/20,0)"
        lg.ws[G(8, k)] = f"=ROUNDUP({G(0, k)}/5,0)"
        lg.ws[G(10, k)] = f"={G(8, k)}-{G(9, k)}"
        lg.ws[G(11, k)] = f"=4*0.4*{G(3, k)}"
    adr["program"] = {"statik": G(3, 2), "tambah": G(5, 2), "pit": G(8, 2), "pit_tambah": G(10, 2), "csl": G(7, 2)}
    lg.kosong()
    b_ = h["beban"]
    lg.bagian("B", "Beban uji (kN)")
    rows = [["200 % × izin selatan 1.583", b_["statik"]["SELATAN"], "", "", "SNI 8460 9.8.1 (used pile)"], ["200 % × izin utara 1.443", b_["statik"]["UTARA"], "", "", ""],
            ["FK 2,5 × 911", b_["fk25"], "", "", "6.2"], ["Uji ada 200 % × 911", 1822.0, "", "", "TP-1..4"],
            ["Uji tarik 1,5 × Pu min 1.452", b_["tarik"]["P"], "", "", "usulan AI; batas PL/EA + 4 mm"], ["Batas deformasi tarik (mm)", b_["tarik"]["batas"], "", "", "EA beton bruto f'c 35, L 38,45 m"],
            ["Uji lateral 2 × 53,95", b_["lat"]["duax"], "", "", "usulan AI; y 6.5 pada 53,95 kN: selatan 15,3 mm, utara 26,0 mm > 10 mm (9.8.3)"]]
    lg.tabel(["Butir", "Nilai", "", "", "Keterangan"], rows, rata=["l", "r", "r", "r", "l"], fmt=[None, "#,##0.0", None, None, None], fill_kolom={1: AI}, beku=False)
    lg.kosong()
    lg.bagian("C", "Letak usulan tiang uji tambahan (tiang berbeban layan terbesar per zona; tiang tarik terbesar)")
    rows = [[k, v["cap"], v["x"], v["y"], idn(v["P"], 0)] for k, v in h["lokasi"].items()]
    lg.tabel(["Zona", "Cap", "x (m)", "y (m)", "P (kN)"], rows, rata=["l", "l", "r", "r", "r"], fmt=[None, None, "0.0", "0.0", None], fill_kolom={2: AI, 3: AI, 4: AI}, beku=False)

    # ---- Dewatering
    ld = Lembar(wb.create_sheet("Dewatering"), 5, "Dewatering galian cap: sumur ekuivalen Dupuit-Sichardt (rumus hidup)", [34, 12, 12, 12, 12, 14, 14, 14, 36])
    ld.catatan(ket + " k urugan dan U1 belum ada di Tahap 2 [Asumsi: 10⁻⁶, 10⁻⁵, 10⁻⁴ m/s]. Dasar kedap = muka tanah asli (gambut U3/U4), air +11,20 sebagai muka air bebas di urugan.")
    ld.kosong()
    ld.bagian("A", "Q per cap (zona selatan, base +9,95; zona utara +9,23): s, R, Q (m³/jam)")
    rows = []
    sel = [r for r in h["dew"] if r["k"] == 1e-5]
    for r in sel:
        rows.append([f"{r['nama']} ({r['zona'].lower()})", r["k"], r["a"], r["b"], r["base"], r["dasar"], None, None, None])
    r0, a, b = ld.tabel(["Cap (zona)", "k (m/s)", "a (m)", "b (m)", "Base (m)", "Dasar (m)", "s (m)", "R (m)", "Q (m³/jam)"], rows, rata=["l", "r", "r", "r", "r", "r", "r", "r", "r"],
                        fmt=[None, "0.0E+00", "0.00", "0.00", "0.00", "0.00", "0.000", "0.00", "0.0000"], fill_kolom={1: AI, 2: AI, 3: AI, 4: AI, 5: AI}, beku=False)
    for i, r in enumerate(sel):
        row = r0 + 1 + i
        c = lambda j: f"{ld.kol(j)}{row}"
        re = f"SQRT({c(2)}*{c(3)}/PI())"
        ld.ws[c(6)] = f"=MAX(0,{MUKA_AIR}-({c(5)}-{TURUN_BAWAH}))"
        ld.ws[c(7)] = f"=IF({c(6)}=0,{re},{re}+3000*{c(6)}*SQRT({c(1)}))"
        H = f"({MUKA_AIR}-{c(4)})"
        hh = f"MAX(0.02,{c(5)}-{TURUN_BAWAH}-{c(4)})"
        ld.ws[c(8)] = f"=IF({c(6)}=0,0,PI()*{c(1)}*({H}^2-{hh}^2)/LN({c(7)}/{re})*3600)"
    adr["dew"] = {(r["nama"], r["zona"]): f"{ld.kol(8)}{r0 + 1 + i}" for i, r in enumerate(sel)}
    adr["dew_s"] = {(r["nama"], r["zona"]): f"{ld.kol(6)}{r0 + 1 + i}" for i, r in enumerate(sel)}
    ld.kosong()
    ld.bagian("B", "Debit hasil skrip untuk tiga k (m³/jam) dan muka air s(x) di tepi gudang")
    rows = []
    for nm, _, _, _ in CAP_DEW:
        for z in BASE_FILL:
            qs = [r for r in h["dew"] if r["nama"] == nm and r["zona"] == z]
            rows.append([f"{nm} ({z.lower()})", *[q["Q"] * 3600 for q in qs], qs[1]["s"], qs[1]["Rs"], qs[1]["Qp"] * 3600, ""])
    ld.tabel(["Cap (zona)", "Q k 1e-6", "Q k 1e-5", "Q k 1e-4", "s (m)", "Rs k 1e-5 (m)", "Q parit k 1e-5", "", ""], rows, rata=["l"] + ["r"] * 8,
             fmt=[None, "0.0000", "0.0000", "0.0000", "0.00", "0.0", "0.0000", None, None], fill_kolom={i: AI for i in range(1, 7)}, beku=False)
    ld.kosong()
    ld.bagian("C", "Heave artesis dasar galian (FS = tegangan total di puncak U5 / u; syarat ≥ 1,1 [Asumsi: analog SNI 8460 9.3.4 b])")
    rows = [[f"{p} {n}", v["e"], v["elev_u5"], v["sig"], v["u"], v["FS"]] for (p, n), v in h["heave"].items()]
    lh0, _, _ = ld.tabel(["Profil dan cap", "Target (m)", "Puncak U5 (m)", "σ total (kPa)", "u (kPa)", "FS"], rows, rata=["l"] + ["r"] * 5,
                          fmt=[None, "0.00", "0.00", "0.0", "0.0", "0.000"], fill_kolom={i: AI for i in range(1, 6)}, beku=False)
    for i in range(len(rows)):
        row = lh0 + 1 + i
        ld.ws[f"{ld.kol(4)}{row}"] = f"=9.81*({MUKA_AIR}-{ld.kol(2)}{row})"
        ld.ws[f"{ld.kol(5)}{row}"] = f"={ld.kol(3)}{row}/{ld.kol(4)}{row}"
    adr["heave"] = f"{ld.kol(5)}{lh0 + 1}"

    # ---- Urutan
    lu = Lembar(wb.create_sheet("Urutan"), 6, "Urutan kerja", [6, 70, 60, 20])
    lu.catatan(ket)
    lu.kosong()
    lu.tabel(["No", "Pekerjaan", "Syarat dan data", "Acuan"], [list(x) for x in urutan()], rata=["c", "l", "l", "l"], beku=False)

    lv = Lembar(wb.create_sheet("Verifikasi"), 7, "Verifikasi T-106", [50, 20, 20, 50])
    lv.catatan(ket)
    lv.kosong()
    lv.tabel(["Butir", "Toleransi (%)", "", "Keterangan"], [
        ["(a) hitung tangan vs skrip (Davisson TP-1, Chin, k100, jumlah uji)", TOL["tangan"], "", "uji `tests/test_tahap6_pelaksanaan.py`"],
        ["(b) Excel rumus hidup vs Python", TOL["excel"], "", "dihitung ulang di Excel"],
        ["(c) sumur ekuivalen vs aliran 1-D keliling galian, orde besaran", TOL["orde"], "", "faktor dua (ditetapkan sebelum hitung); aliran 1-D adalah batas bawah bila Rs ≫ re, jadi selisih besar wajar tetapi tetap dicatat GAGAL"],
        ["(d) k rata-rata TP-1..4 vs 489 kN/mm (6.6)", TOL["k"], "", "data sama"]], rata=["l", "r", "r", "l"], fmt=[None, "0.0", None, None], beku=False)
    la = Lembar(wb.create_sheet("Acuan"), 8, "Acuan dan status", [52, 30, 84])
    la.catatan(ket)
    la.kosong()
    la.tabel(["Acuan", "Halaman", "Isi"], [list(a) for a in ACUAN], rata=["l", "l", "l"], beku=False)
    lk = Lembar(wb.create_sheet("Keputusan"), 9, "Keputusan untuk Defsa", [8, 130])
    lk.catatan(ket)
    lk.kosong()
    lk.tabel(["No", "Keputusan (usulan AI)"], [[i + 1, t] for i, t in enumerate(keputusan(h))], rata=["c", "l"], beku=False)

    lr = Lembar(wb.create_sheet("Ringkasan", 1), 2, "Ringkasan hasil", [46, 18, 18, 52])
    lr.catatan(ket)
    lr.kosong()
    lr.bagian("A", "Uji statik TP-1..4 (f'c 30)")
    rows = [[tp, v["s200"], v["k100"], f"Chin Qult {idn(v['chin']['Qult'], 0)} kN; sisa {idn(v['sisa'], 2)} mm; Davisson {idn(v['s_davisson'], 1)} mm {'terlampaui' if v['davisson_tercapai'] else 'tidak tercapai'}"]
            for tp, v in h["statik"]["tp"].items()]
    rows.append(["k rata-rata (kN/mm) vs 489", h["statik"]["k_rata"], h["statik"]["dev_k"], "selisih %"])
    lr.tabel(["Tiang", "s 200 % (mm) / k", "k100 / selisih", "Catatan"], rows, rata=["l", "r", "r", "l"], fmt=[None, "0.00", "0.0", None], fill_kolom={1: AI, 2: AI}, beku=False)
    lr.kosong()
    lr.bagian("B", "Program uji tambahan")
    t_ = h["tambahan"]
    lr.tabel(["Butir", "Nilai", "", "Catatan"], [["Statik tambahan", t_["statik"], "", f"saat konstruksi ≥ {t_['konstruksi']}"], [f"PIT tambahan ({N_TOTAL} / {N_UTAMA} tiang)", t_["pit"], t_["pit_utama"], ""],
                                                    ["CSL tambahan", t_["csl"], "", "ada 20 tiang kerja"], ["Tarik / lateral", t_["tarik"], t_["lateral"], ""]], rata=["l", "r", "r", "l"], fill_kolom={1: AI}, beku=False)
    wb.save(keluar)
    return keluar, adr


def keputusan(h):
    t = h["tambahan"]
    hv = h["heave"]
    fs_min = min(v["FS"] for v in hv.values())
    return [
        "Lingkup: usulan AI tetap di Tahap 6 untuk program uji (jumlah, beban, kriteria, letak) dan syarat dewatering; spesifikasi rinci, kapasitas pompa, dan uji dilapangan ke RKS Tahap 7.",
        f"Uji statik tambahan: {t['statik']} tiang saat konstruksi (≥ 40 % dari {h['jumlah']['total']['statik']}); beban uji 200 % × izin ({idn(h['beban']['statik']['SELATAN'], 0)} kN selatan, {idn(h['beban']['statik']['UTARA'], 0)} kN utara). "
        f"Usulan AI: ya, selatan dan utara; alternatif minimal {idn(FK_PERLU, 0)} kN bila kentledge tidak memungkinkan.",
        f"Uji tarik 1 tiang di Cap D ({idn(h['lokasi']['TARIK']['x'], 1)}; {idn(h['lokasi']['TARIK']['y'], 1)}), beban {idn(h['beban']['tarik']['P'], 0)} kN (usulan AI 1,5 × Pu min), tulangan tiang uji ≥ 16 D25.",
        f"Uji lateral 1 tiang free-head; 6.5 memprediksi y {idn(LAT['y_sendi_selatan'], 1)} mm (selatan) dan {idn(LAT['y_sendi_utara'], 1)} mm (utara) pada 53,95 kN, di atas batas 10 mm pada 100 % (SNI 8460 9.8.3): kriteria uji tidak sama dengan model; perlu diputuskan.",
        f"Dewatering: sump terbuka untuk cap kolom (Q ≤ beberapa m³/jam); sumur dangkal dan pengisian ulang di dekat gudang hanya untuk tiang utilitas (tepi cap ±8 m dari gudang); muka air di urugan tidak dapat turun di bawah dasar urugan +9,23 sampai +9,95, di atas batas +8,6. Heave artesis FS minimum {idn(fs_min, 2)} (syarat ≥ 1,1 [Asumsi]).",
        "T113 (CSL D 3 dari 6 profil, Cap E gabungan, semula Cap C): usulan AI: CSL ulang dan coring (GEC10 16.3 hal. PDF 513); bila cacat terkonfirmasi evaluasi 17.4 (hal. 525) dengan grouting (17.5.5 hal. 534) atau tiang pengganti dan cap diperlebar (17.5.2-17.5.3 hal. 528-531).",
        "T218 dan T088 PDA diulang (palu 9 t, umur ≥ 28 hari) sebagai pengganti, bukan tambahan jumlah.",
        "Gudang: survei kondisi sebelum dan sesudah tiap tahap; patok penurunan; peringatan tebing INC-1 laju 0,18 mm/hari (laju sekarang 0,177).",
    ]


# ================================================================== T-106
def baca_excel(berkas, adr):
    import openpyxl
    wb = openpyxl.load_workbook(berkas, data_only=True)

    def b(sh, c):
        return float(wb[sh][c].value)
    return dict(statik={tp: {k: b("Statik", c) for k, c in v.items()} for tp, v in adr["statik"].items()},
                program={k: b("Program", c) for k, c in adr["program"].items()},
                dew={k: b("Dewatering", c) for k, c in adr["dew"].items()}, heave=b("Dewatering", adr["heave"]))


def t106(h, berkas=None, adr=None):
    # (a) hitung tangan: Davisson TP-1 pada 1.822 kN; k100 TP-1; jumlah uji
    tp = h["statik"]["tp"]["TP-1"]
    ae = 4700 * math.sqrt(30) * 1e3 * math.pi * 0.8 ** 2 / 4
    sd = 1822.0 * 37.01 / ae * 1e3 + 4 + 800 / 120
    ds = [abs(davisson(1822.0, 37.01) - sd) / sd * 100, abs(h["jumlah"]["total"]["statik_75"] - N_TOTAL / 75) / (N_TOTAL / 75) * 100,
          abs(tp["k100"] - tp["P100"] / tp["s100"]) / tp["k100"] * 100]
    dt = max(ds)
    dxl = None
    if berkas and adr:
        x = baca_excel(berkas, adr)
        e = []
        for k, v in h["statik"]["tp"].items():
            e += [abs(x["statik"][k]["Qult"] - v["chin"]["Qult"]) / v["chin"]["Qult"] * 100, abs(x["statik"][k]["k100"] - v["k100"]) / v["k100"] * 100,
                  abs(x["statik"][k]["D200"] - v["s_davisson"]) / v["s_davisson"] * 100]
        t = h["jumlah"]["total"]
        e += [abs(x["program"]["statik"] - t["statik"]) / t["statik"] * 100, abs(x["program"]["pit"] - t["pit"]) / t["pit"] * 100, abs(x["program"]["csl"] - t["csl"]) / t["csl"] * 100]
        for (nm, z), q in x["dew"].items():
            ref = next(r for r in h["dew"] if r["nama"] == nm and r["zona"] == z and r["k"] == 1e-5)["Q"] * 3600
            if ref > 0:
                e.append(abs(q - ref) / ref * 100)
        hv = h["heave"][("SELATAN", "Cap h 800")]["FS"]
        e.append(abs(x["heave"] - hv) / hv * 100)
        dxl = max(e)
    # (c) orde: sumur ekuivalen vs parit
    rs = [abs(r["Q"] - r["Qp"]) / r["Qp"] * 100 for r in h["dew"] if r["Q"] > 0 and r["Qp"] > 0]
    dor = max(rs)
    dk = h["statik"]["dev_k"]
    lolos = dt <= TOL["tangan"] and dxl is not None and dxl <= TOL["excel"] and dor <= TOL["orde"] and dk <= TOL["k"]
    return dict(dt=dt, dxl=dxl, dor=dor, dk=dk, lolos=lolos)


def catat_t106(r, h, berkas=VERIFIKASI):
    baris = ("| T-106 | Cek silang 6.8 interpretasi uji statik TP-1..4 (Davisson, Chin, kekakuan), jumlah uji SNI 8460 9.8, dewatering galian cap (Dupuit-Sichardt), heave artesis | "
             f"(a) hitung tangan (Davisson TP-1, jumlah statik, k100) vs skrip: selisih terbesar {idn(r['dt'], 3)} %; (b) Python vs Excel rumus hidup (Chin, k100, Davisson, jumlah uji, Q dewatering, FS heave): "
             f"selisih terbesar {idn(r['dxl'], 4) if r['dxl'] is not None else 'tidak dihitung'} %; (c) sumur ekuivalen vs aliran 1-D keliling galian (orde besaran): selisih terbesar {idn(r['dor'], 1)} %; "
             f"(d) k rata-rata TP-1..4 {idn(h['statik']['k_rata'], 1)} kN/mm vs 489 (6.6): {idn(r['dk'], 2)} % | (a) ≤ 2 %; (b) ≤ 0,1 %; (c) ≤ 100 % (faktor dua, ditetapkan sebelum hitung; aliran 1-D adalah batas bawah untuk Rs jauh lebih besar dari re, sehingga debit dipakai dari sumur ekuivalen yang lebih besar/konservatif); (d) ≤ 1 % | "
             f"{'Lolos' if r['lolos'] else 'GAGAL'}, STATUS: {STATUS} | `skrip/tahap6_pelaksanaan.py`, `tests/test_tahap6_pelaksanaan.py` | "
             "Ditetapkan sebelum membandingkan. Data simulasi. k urugan [Asumsi]. Rencana lama T-106 (volume IFC vs rencana) bergeser ke T-107 dan Excel = Python ke T-108. |")
    teks = Path(berkas).read_text(encoding="utf-8").split("\n")
    teks = [ln for ln in teks if not ln.startswith("| T-106 | Cek silang 6.8")]
    i = next(k for k, ln in enumerate(teks) if ln.startswith("| T-105 |"))
    teks.insert(i + 1, baris)
    Path(berkas).write_text("\n".join(teks), encoding="utf-8")
    return baris


# ================================================================== Markdown
def tabel_md(kep, baris):
    return ["| " + " | ".join(kep) + " |", "|" + "---|" * len(kep)] + ["| " + " | ".join(str(x) for x in b) + " |" for b in baris]


def tulis_md(h=None, r=None, keluar=MD):
    h = h or semua()
    r = r or t106(h)
    st = h["statik"]
    j, t, b_, lok = h["jumlah"], h["tambahan"], h["beban"], h["lokasi"]
    L = ["# 6.8 Uji tiang dan metode pelaksanaan\n", LABEL,
         f"Dihitung AI atas permintaan Defsa (22 Nov 2026). STATUS: {STATUS}. Kunci jawaban tidak dibuka. "
         "Excel: `6.8 Uji Tiang dan Pelaksanaan.xlsx`; skrip: `skrip/tahap6_pelaksanaan.py`; uji: `tests/test_tahap6_pelaksanaan.py`; lembar isian: `6.8 Lembar Isian Uji dan Pelaksanaan.md`.\n",
         f"Cap E h {HE_LABEL} (pelat, usulan Defsa; hasil 6.7). Cek silang T-106; rencana lama T-106 (volume IFC vs rencana) bergeser ke T-107 dan Excel = Python ke T-108.\n",
         "## 1. Interpretasi uji beban statis TP-1..4\n",
         "Titik ukur: akhir tahap tiap kali beban naik ke maksimum baru (load cell). Davisson: s = PL/AE + 4 mm + D/120 (NHI-06-089 hal. 275-276), Ec 4.700 √f'c dengan f'c 30 (sama dengan 6.6, EA 12.940 MN); "
         f"f'c 35 memberi selisih ≤ {idn(max(abs(st['tp'][k]['s_davisson'] - h['statik35']['tp'][k]['s_davisson']) for k in st['tp']), 2)} mm pada garis Davisson. Chin (ekstrapolasi hiperbola, [Literatur: belum ada di acuan/]).\n"]
    L += tabel_md(["Tiang", "Zona", "L (m)", "s 100 % (mm)", "k100 (kN/mm)", "s 200 % (mm)", "Sisa (mm)", "Elastis PL/AE (mm)", "s Davisson 1.822 (mm)", "Davisson", "Chin Qult (kN)", "Beban pada s = 25 mm (Chin)"],
                  [[tp, ZONA_TP[tp].lower(), idn(PANJANG_TP[tp], 2), idn(v["s100"], 2), idn(v["k100"], 0), idn(v["s200"], 2), idn(v["sisa"], 2), idn(v["elastis"], 2),
                    idn(v["s_davisson"], 1), "tidak tercapai" if not v["davisson_tercapai"] else "tercapai", idn(v["chin"]["Qult"], 0), idn(v["chin"]["P25"], 0)] for tp, v in st["tp"].items()])
    L += ["", f"Kekakuan: k rata-rata {idn(st['k_rata'], 1)} kN/mm terhadap 489 (6.6): selisih {idn(st['dev_k'], 2)} %. Kriteria SNI 8460 9.8.1 (hal. PDF 207): s pada 200 % ≤ 25 mm (Ø 80 cm): "
          f"terbesar {idn(max(v['s200'] for v in st['tp'].values()), 2)} mm, lolos; permanen ≤ 12 mm: terbesar {idn(max(v['sisa'] for v in st['tp'].values()), 2)} mm, lolos. Penurunan pada 200 % hampir seluruhnya elastis "
          f"(PL/AE {idn(min(v['elastis'] for v in st['tp'].values()), 1)}-{idn(max(v['elastis'] for v in st['tp'].values()), 1)} mm): tahanan tanah belum termobilisasi penuh, kondisi masih elastik "
          "dan SNI 9.8.1 tidak mengharuskan interpretasi failure (tiga cara hanya untuk kondisi failure).\n",
          "Kesimpulan terhadap desain:\n",
          f"- 200 % × 911 = 1.822 kN membuktikan FK 2,0 pada 911 kN, bukan pada izin 6.2: izin selatan 1.583 kN memerlukan 200 % = {idn(b_['statik']['SELATAN'], 0)} kN, utara 1.443 kN memerlukan {idn(b_['statik']['UTARA'], 0)} kN; FK 2,5 pada 911 kN memerlukan {idn(FK_PERLU, 0)} kN.",
          f"- Pu maks 3.254 kN (6.3, Cap D) adalah {idn(b_['pu_vs_uji'], 2)} kali beban uji: tidak diuji. Pendukung: CAPWAP Ru TP-1 {idn(CAPWAP['TP-1'], 0)} kN dan TP-3 {idn(CAPWAP['TP-3'], 0)} kN (tiang uji), rata-rata tiang kerja 3.906 kN (6.2); "
          f"terhadap izin selatan {idn(CAPWAP['TP-3'] / IZIN['SELATAN'], 2)} dan utara {idn(CAPWAP['TP-1'] / IZIN['UTARA'], 2)} (CAPWAP selatan di bawah FK 2,5).",
          "- Ekstrapolasi Chin jauh lebih besar dari CAPWAP karena kurva elastis hingga 200 %: tidak dipakai sebagai kapasitas; hanya indikasi kekakuan.\n",
          "## 2. Program uji akhir (SNI 8460 9.8)\n"]
    tj, uj = j["total"], j["utama"]
    L += tabel_md(["Uji", "Aturan", f"Gedung utama ({N_UTAMA})", f"Total {N_TOTAL}", "Ada", f"Tambahan ({N_TOTAL} / {N_UTAMA})"], [
        ["Statik tekan", "1 per 75; 1,0 % N (terbesar, tafsir AI); ≥ 40 % saat konstruksi", f"{uj['statik']} ({idn(uj['statik_75'], 2)}; {idn(uj['statik_1pct'], 2)})", f"{tj['statik']} ({idn(tj['statik_75'], 2)}; {idn(tj['statik_1pct'], 2)})", f"{ADA['statik']} (semua sebelum konstruksi)", f"{t['statik']} / {uj['statik'] - ADA['statik']} (konstruksi ≥ {tj['konstruksi']})"],
        ["Statik tarik", f"1 per 100 tiang tarik ({N_TARIK} tiang cap inti)", 1, 1, 0, 1],
        ["Lateral", "1 per ukuran (tanpa besmen)", 1, 1, 0, 1],
        ["PDA", "≤ 4 × 40 % statik (tafsir)", idn(uj["pda_maks"], 1), idn(tj["pda_maks"], 1), f"{ADA['PDA']} (8 tiang kerja)", "0 (batas terlampaui; T218, T088 diulang sebagai pengganti)"],
        ["CSL", "1 per 20", f"{uj['csl']} ({idn(uj['csl_ex'], 1)})", f"{tj['csl']} ({idn(tj['csl_ex'], 1)})", f"{ADA['CSL_kerja']} tiang kerja (+4 uji)", f"{t['csl']} (+ susulan T113)"],
        ["PIT", "1 per 5", f"{uj['pit']} ({idn(uj['pit_ex'], 1)})", f"{tj['pit']} ({idn(tj['pit_ex'], 1)})", ADA["PIT"], f"{t['pit']} / {t['pit_utama']}"]])
    L += ["", "Beban dan kriteria uji tambahan:", ""]
    L += tabel_md(["Uji", "Beban maksimum", "Kriteria", "Dasar"], [
        ["Statik selatan", f"{idn(b_['statik']['SELATAN'], 0)} kN (200 % × 1.583); alternatif {idn(FK_PERLU, 0)} kN", "s ≤ 25 mm; permanen ≤ 12 mm; Davisson", "SNI 8460 9.8.1"],
        ["Statik utara", f"{idn(b_['statik']['UTARA'], 0)} kN (200 % × 1.443)", "idem", "idem"],
        ["Tarik (usulan AI)", f"{idn(b_['tarik']['P'], 0)} kN = 1,5 × Pu min 1.452; tahanan tarik gempa 1.951 kN", f"deformasi ≤ PL/EA + 4 mm = {idn(b_['tarik']['batas'], 1)} mm (EA beton bruto), maks 25 mm", "SNI 8460 9.8.2"],
        ["Lateral (usulan AI)", f"{idn(b_['lat']['duax'], 1)} kN = 2 × 53,95", "10 mm pada 100 %, 25 mm pada 200 %; 6.5 memprediksi 15,3 mm (selatan) dan 26,0 mm (utara) pada 100 %", "SNI 8460 9.8.3"]])
    L += ["", "Letak usulan (tiang berbeban layan terbesar per zona, 6.3; tiang tarik terbesar Cap D):", ""]
    L += tabel_md(["Peran", "Cap", "x (m)", "y (m)", "P (kN)"], [[k, v["cap"], idn(v["x"], 1), idn(v["y"], 1), idn(v["P"], 0)] for k, v in lok.items()])
    L += ["", f"T113 ({idn(T113['x'], 1)}; {idn(T113['y'], 1)}; {T113['cap_lod200']}, {T113['cap_63']}): CSL D pada 3 dari 6 profil, G 3 profil. Usulan AI: CSL ulang dan coring dari kepala (GEC10 16.3, hal. PDF 513; 16.2.1 sonic hal. 493); "
          "evaluasi cacat (17.4 hal. 525; NDT 17.2.2 hal. 519); bila terkonfirmasi: grouting (17.5.5, hal. 534), perkuatan struktur (17.5.4, hal. 532), atau tiang pengganti dan cap diperlebar (17.5.2-17.5.3, hal. 528-531). "
          "T218 (palu 4 t = ±1,0 % Ru, set 0,6 mm) dan T088 (umur beton 5 hari) PDA diulang dengan palu 9 t dan umur ≥ 28 hari. TP-2 CSL D dasar: tidak dipakai kalibrasi (6.2).\n",
          "## 3. Dewatering galian cap\n",
          "Pendekatan: galian persegi panjang (cap + 1,0 m ruang kerja tiap sisi [Asumsi]) sebagai sumur ekuivalen, Dupuit akuifer bebas, dasar kedap = muka tanah asli (+9,95 selatan, +9,23 utara; gambut U3/U4 di bawahnya), "
          "muka air +11,20 sebagai muka air bebas di urugan [Asumsi]; jari-jari pengaruh Sichardt R = re + 3000 s √k. Drawdown s = +11,20 - (dasar - 0,5). k urugan dan U1 belum ada di Tahap 2 "
          "(hanya k akuifer U5 8,3 × 10⁻⁵ m/s): tiga skenario 10⁻⁶, 10⁻⁵, 10⁻⁴ m/s [Asumsi]. Debit dalam m³/jam.\n"]
    rows = []
    for nm, dasar, pj, lb in CAP_DEW:
        for z in BASE_FILL:
            qs = [q for q in h["dew"] if q["nama"] == nm and q["zona"] == z]
            q5 = qs[1]
            rows.append([nm, z.lower(), idn(URUGAN - dasar, 2), idn(MUKA_AIR - dasar, 2), idn(q5["s"], 2), idn(q5["Rs"], 1), idn(qs[0]["Q"] * 3600, 3), idn(qs[1]["Q"] * 3600, 3), idn(qs[2]["Q"] * 3600, 3)])
    L += tabel_md(["Cap", "Zona", "Galian dari +11,50 (m)", "Dasar di bawah air +11,20 (m)", "s (m)", "Rs k 1e-5 (m)", "Q k 1e-6", "Q k 1e-5", "Q k 1e-4"], rows)
    q_e = next(q for q in h["dew"] if q["nama"].startswith("Cap E") and q["zona"] == "SELATAN" and q["k"] == 1e-4)
    L += ["", f"Pengaruh di gudang: muka air tidak dapat turun di bawah dasar urugan (+9,23 sampai +9,95) karena di bawahnya gambut kedap, sehingga selalu di atas batas +8,6 (kepala cerucuk +8,62). "
          f"Tepi gudang barat x {idn(GUDANG_X, 0)} (2.7); tiang utilitas terdekat x {idn(TIANG_UTIL_X, 1)}, tepi cap ±{idn(TIANG_UTIL_X + TEPI_CAP, 1)}: jarak ±{idn(GUDANG_X - TIANG_UTIL_X - TEPI_CAP, 1)} m; "
          f"cap gedung utama terdekat x ±86: ±{idn(GUDANG_X - 86, 0)} m. Muka air s(x) di tepi galian Cap E (selatan, k 1e-4, Rs {idn(q_e['Rs'], 1)} m):\n"]
    xs = (5, 8, 10, 15, 20, 30)
    prof = []
    for k in K_SKEN:
        qe = next(q for q in h["dew"] if q["nama"].startswith("Cap E") and q["zona"] == "SELATAN" and q["k"] == k)
        prof.append([f"{k:.0e}".replace("e-0", "e-")] + [idn(muka_air_x(qe, k, BASE_FILL["SELATAN"], x), 2) for x in xs])
    L += tabel_md(["k (m/s)"] + [f"x = {x} m" for x in xs], prof)
    L += ["", "Penurunan akibat dewatering: Δσ' = 9,81 s ≤ " + idn(delta_sigma(max(q["s"] for q in h["dew"])), 1) + " kPa pada lapisan di bawah muka air turun; penurunan gambut tidak dihitung (kompresibilitas U3 untuk beban kecil belum dipakai). "
          "Dampak ke gudang pada jarak ≥ 8 m: kecil (Rs k 1e-4 sampai 30 m), dipantau dengan patok.\n",
          "Heave artesis (tinggi tekan U5 +11,20 pada puncak U5; FS = tegangan total di puncak U5 / u; syarat ≥ 1,1 [Asumsi: analog SNI 8460 9.3.4 b]):\n"]
    L += tabel_md(["Profil", "Cap", "Target (m)", "Puncak U5 (m)", "σ total (kPa)", "u (kPa)", "FS"], [[p, n, idn(v["e"], 2), idn(v["elev_u5"], 2), idn(v["sig"], 1), idn(v["u"], 1), idn(v["FS"], 2)] for (p, n), v in h["heave"].items()])
    L += ["", "Usulan metode (AI): sump terbuka dan parit pompa untuk cap kolom (debit kecil, urugan di atas gambut); Cap E dan pit: parit keliling dengan sump dan pompa cadangan, muka air dijaga ≥ dasar galian - 0,5 m dan ≥ +8,6 di sisi gudang; "
          "pengisian ulang dan sheet pile hanya bila pemantauan piezometer dan patok gudang melampaui ambang. Lereng galian ≤ 1,0 m: tegak sementara atau 1:1 bila kering; SNI 8460 Pasal 11 (hal. PDF 277, 279) mengharuskan tinjauan dampak dewatering pada fondasi eksisting; "
          "kriteria drawdown dan debit galian dangkal: belum ada di acuan.\n",
          "## 4. Urutan kerja\n"]
    L += tabel_md(["No", "Pekerjaan", "Syarat dan data", "Acuan"], [list(x) for x in urutan()])
    L += ["", "## 5. Verifikasi T-106\n",
          f"Toleransi ditetapkan dulu: (a) hitung tangan vs skrip ≤ 2 %; (b) Excel vs Python ≤ 0,1 %; (c) sumur ekuivalen vs aliran 1-D keliling ≤ 100 % (faktor dua); (d) k rata-rata vs 489 ≤ 1 %. "
          f"Hasil: (a) {idn(r['dt'], 3)} %; (b) {idn(r['dxl'], 4) if r['dxl'] is not None else 'n/a'} %; (c) {idn(r['dor'], 1)} %; (d) {idn(r['dk'], 2)} %. {'Lolos' if r['lolos'] else 'GAGAL butir (c)'}. "
          "Butir (c) gagal: aliran 1-D keliling adalah batas bawah bila Rs jauh lebih besar dari re, jadi debit desain dipakai dari sumur ekuivalen (lebih besar, konservatif); "
          "toleransi tidak dilonggarkan sesudah melihat hasil.\n",
          "## 6. Keputusan yang dibutuhkan dari Defsa\n",
          "**Keputusan Defsa 22 Nov 2026: usulan AI dipakai untuk semua butir.** Program uji tetap di Tahap 6 (spesifikasi rinci ke RKS Tahap 7); 2 uji statik konstruksi sampai 200 % × izin (3.166 / 2.886 kN); 1 uji tarik (Cap D, 2.178 kN) dan 1 uji lateral (2 × 53,95 kN) dengan kriteria lateral disesuaikan ke prediksi 6.5; dewatering sump terbuka cap kolom, parit keliling + sump Cap E dan pit; T113 CSL ulang dan coring dulu.\n"]
    L += [f"{i + 1}. {x}" for i, x in enumerate(keputusan(h))]
    L += ["", "## 7. Sumber", ""] + [f"- {a[0]} ({a[1]}): {a[2]}." for a in ACUAN]
    L += ["", f"Status: {STATUS}."]
    Path(keluar).write_text("\n".join(L) + "\n", encoding="utf-8")
    return keluar


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    from format_dokumen import hitung_ulang_excel
    h = semua()
    for tp, v in h["statik"]["tp"].items():
        print(tp, round(v["k100"], 1), round(v["s200"], 2), round(v["sisa"], 2), round(v["chin"]["Qult"]), round(v["s_davisson"], 1), v["davisson_tercapai"])
    print("k rata", h["statik"]["k_rata"], h["statik"]["dev_k"])
    print(h["tambahan"], h["lokasi"])
    berkas, adr = buat_excel(h=h)
    print(berkas, hitung_ulang_excel(berkas))
    r = t106(h, berkas, adr)
    print(r)
    catat_t106(r, h)
    print(tulis_md(h=h, r=r))


if __name__ == "__main__":
    main()
