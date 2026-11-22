import math
import os
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))
import tahap6_penurunan as t  # noqa: E402


@pytest.fixture(scope="module")
def h():
    os.environ["TAHAP6_PENURUNAN_CACHE"] = "1"      # hasil berat di cache (%TEMP%\tahap6_penurunan_hasil.pkl)
    return t.semua()


def test_de_tangan_vs_integrasi(h):
    """Δe: Pers. 9-20 dengan Q rata-rata per ruas vs integrasi Q(z): selisih <= 10 % untuk semua 63 cap."""
    for c in h["caps"]:
        assert abs(c["de"]["de"] - c["de"]["tangan"]) / c["de"]["de"] * 100 <= t.TOL["de"]
        assert 1.0 < c["de"]["de"] < 20.0          # mm, orde pemendekan tiang 38 m


def test_boussinesq_satu_persegi_pusat():
    """Pusat persegi B pada z = B/2: faktor 4 f(1,1) = 0,700 (Newmark); lalu cocok dengan integral beban titik Boussinesq."""
    B, z = 2.0, 1.0
    assert t.bous(100.0, 0, 0, B, B, 0, 0, z) == pytest.approx(70.0, abs=0.1)
    n = 400
    g = (np.arange(n) + 0.5) / n * B - B / 2
    X, Y = np.meshgrid(g, g)
    R = np.sqrt(X ** 2 + Y ** 2 + z ** 2)
    num = float(np.sum(3 * 100.0 * z ** 3 / (2 * math.pi * R ** 5)) * (B / n) ** 2)
    assert num == pytest.approx(float(t.bous(100.0, 0, 0, B, B, 0, 0, z)), rel=1e-3)
    # di luar persegi (titik di sudut luar) dan superposisi dua separuh = utuh
    ut = t.bous(100.0, 0, 0, 4.0, 2.0, 0.5, 0.2, 1.5)
    dua = t.bous(100.0, -1, 0, 2.0, 2.0, 0.5, 0.2, 1.5) + t.bous(100.0, 1, 0, 2.0, 2.0, 0.5, 0.2, 1.5)
    assert float(ut) == pytest.approx(float(dua), rel=1e-9)


def test_cr_cc_pindah_di_sigma_p():
    """s_u6: di bawah σ'p hanya Cr; melewati σ'p Cr sampai σ'p lalu Cc; di atas σ'p hanya Cc; kontinu dan naik."""
    h1 = 1.0
    cr = float(t.s_u6(200.0, 100.0, h1))
    assert cr == pytest.approx(h1 / (1 + t.E0) * t.CR * math.log10(300 / 200), rel=1e-9)
    lewat = float(t.s_u6(300.0, 200.0, h1))
    assert lewat == pytest.approx(h1 / (1 + t.E0) * (t.CR * math.log10(400 / 300) + t.CC * math.log10(500 / 400)), rel=1e-9)
    cc = float(t.s_u6(500.0, 100.0, h1))
    assert cc == pytest.approx(h1 / (1 + t.E0) * t.CC * math.log10(600 / 500), rel=1e-9)
    ds = np.linspace(1, 400, 200)
    s = t.s_u6(300.0, ds, h1)
    assert np.all(np.diff(s) > 0) and np.max(np.abs(np.diff(s, 2))) < 0.01


def test_jumlah_cap_dan_beban(h):
    caps = h["caps"]
    assert len(caps) == 58 and sum(c["jenis"] == "kolom" for c in caps) == 52 and sum(c["jenis"] == "inti" for c in caps) == 6      # berat cap masuk 6.3: 4/B, 4/C, 7/B, 7/C ikut Cap E
    assert sum(c["n"] for c in caps) == 251
    assert {"Cap E", "Cap A", "9/C", "3/B", "3/C"} <= {c["id"] for c in caps}
    for c in caps:
        assert c["Q0"] == pytest.approx(c["W"] / c["n"]) and c["B"] >= 0.8 - 1e-9 and c["L"] >= 0.8 - 1e-9


def test_sublapis_menutup_tebal():
    for tz, e in (("SELATAN", -21.5), ("UTARA", -13.99), ("TENGAH", -14.04)):
        sl = t.sublapis(tz, e)
        zr = t.p3.PROFIL[tz]["elev"] - e
        assert float(np.sum(sl["h"])) == pytest.approx(t.Z_DASAR - zr, rel=1e-9)
        assert sl["h"].max() <= t.H_SUB + 1e-9 and np.all(np.diff(sl["z"]) > 0)


def test_boussinesq_tidak_kurang_dari_cap_sendiri(h):
    """Superposisi 63 cap di pusat suatu cap >= pengaruh cap itu sendiri (semua kontribusi positif)."""
    caps = h["caps"]
    i = next(k for k, c in enumerate(caps) if c["id"] == "3/C")
    c = caps[i]
    sl = t.kolom_cap(c, h["tz"], "a")
    sendiri = t.bous(c["W"] / (c["B"] * c["L"]), c["cx"], c["cy"], c["B"], c["L"], c["cx"], c["cy"], h["tz"][c["tz"]]["e_a"] - sl["e"])
    semua = h["res"][("a", "bous")]["ds"][i]
    assert np.all(semua >= sendiri - 1e-9) and np.all(semua[:3] > sendiri[:3])


def test_pasangan_dan_sloof(h):
    ps = h["pasangan"]
    assert all(p["L"] <= t.JARAK_TETANGGA + 1e-9 for p in ps) and all(p["delta"] >= 0 for p in ps)
    assert ps[0]["delta"] == max(p["delta"] for p in ps)
    caps = h["caps"]
    s = h["total"][("c", "bous")]
    assert ps[0]["delta"] == pytest.approx(abs(float(s[ps[0]["i"]] - s[ps[0]["j"]])))
    ada = {frozenset((p["a"], p["b"])) for p in ps}
    assert frozenset(("3/B", "3/C")) in ada                      # pasangan lintas zona
    assert any(p["lintas"] for p in ps)
    m16, m32 = t.momen_sloof(16.0), t.momen_sloof(32.0)
    assert m16["400x800"] == pytest.approx(249.1) and m32["SL-1 400x900"] == pytest.approx(2 * 354.7)
    assert t.momen_sloof(16.0, L=4.0)["400x800"] == pytest.approx(4 * 249.1)   # 1/L2
    r16, _ = t.rasio_sl1(16.0)
    assert 0.3 < r16 < 0.7 and t.rasio_sl1(100.0)[0] > r16 and t.rasio_sl1(h["sloof"]["delta_batas"])[0] == pytest.approx(1.0, abs=1e-3)


def test_excel_sama_dengan_python(h):
    """Butir a T-104: Excel rumus hidup (sudah dihitung ulang di Excel oleh main()) vs Python <= 1 %."""
    if not t.BERKAS.exists():
        pytest.skip("Excel belum dibangun (jalankan skrip/tahap6_penurunan.py)")
    import openpyxl
    wb = openpyxl.load_workbook(t.BERKAS, data_only=True)
    ws = wb["Per Cap"]
    kep = None
    for row in ws.iter_rows():
        if row[2].value == "No" and row[3].value == "Cap":
            kep = row[2].row
            break
    assert kep is not None
    caps = h["caps"]
    for k, c in enumerate(caps):
        r = kep + 1 + k
        assert ws.cell(r, 4).value == c["id"]
        py_a = c["s_np"] + h["res"][("a", "bous")]["s_kel"][k] + c["de"]["de"]
        xl_a = ws.cell(r, 3 + 16).value                       # kolom s tot (a), indeks 16 dari C
        assert xl_a is not None and abs(float(xl_a) - py_a) / py_a * 100 <= t.TOL["excel"]


def test_varian_d_rumus_dan_uji_beban(h):
    """(d) = s NP + FJ x (Q0/k) x sqrt(n) + s global; model s tunggal pada 1.400 kN cocok uji beban TP (10 %); (d) jauh di bawah (a)/(b)."""
    d = h["d"]
    for i, c in enumerate(h["caps"]):
        assert d["total"][i] == pytest.approx(c["s_np"] + t.FJ * c["Q0"] / h["uji"]["k"] * math.sqrt(c["n"]) + d["s_glob"][i], rel=1e-9)
    assert abs(h["uji"]["s_model_1400"] - np.mean(h["uji"]["ukur_1400"])) / np.mean(h["uji"]["ukur_1400"]) <= 0.10
    assert 450 < h["uji"]["k"] < 520 and d["total"].max() < h["total"][("c", "bous")].max() / 2


def test_varian_d_ocr_dan_pasangan(h):
    """σ'p = OCR x σ'v0 tanah asli mengecilkan s kelompok (a); pasangan (d) lebih sedikit melebihi 16 mm daripada (c)."""
    assert np.all(h["ocr_a"] <= h["res"][("a", "bous")]["s_kel"] + 1e-9) and h["ocr_a"].sum() < h["res"][("a", "bous")]["s_kel"].sum()
    n_d = sum(p["delta"] > t.DELTA_IZIN for p in h["pasangan_v"][("d", "bous")])
    assert n_d < sum(p["delta"] > t.DELTA_IZIN for p in h["pasangan"]) and h["sloof_d"]["rasio"] < h["sloof"]["rasio"]
