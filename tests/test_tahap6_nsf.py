import sys
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))
import tahap6_nsf as n  # noqa: E402


@lru_cache(maxsize=None)
def _np(zona):
    return n.np_zona(zona)


def test_bidang_netral_dua_cara_cocok():
    for z in n.ZONA2:
        for k in (1, 2):
            r = _np(z)[k]
            assert abs(r["z"] - r["z_tertutup"]) <= n.TOL["np"]
            assert abs(r["Qn"] - r["Qn_tertutup"]) < 5.0


def test_qn_positif_dan_kurang_dari_seret_total_dan_kurva_berpotongan():
    for z in n.ZONA2:
        r = _np(z)[1]
        assert 0 < r["Qn"] < r["Sd_tot"]
        # di bidang netral Kurva A = Kurva B = Q + Qn
        i = next(i for i, zb in enumerate(r["zb"]) if zb >= r["z"])
        assert abs(r["A"][i] - r["B"][i]) < 0.02 * r["Qmaks"]
        assert r["Qmaks"] == n.Q_KERJA + r["Qn"]


def test_kasus_likuifaksi_u5_lima_puluh_persen():
    for z in n.ZONA2:
        for s in _np(z)["sl"]:
            if s["unit"] == "U5":
                assert abs(s["f2d"] - 0.5 * s["fs"]) < 1e-9 and s["f2r"] == 0.0
            elif s["unit"] in ("U1", "U2", "U3", "U4", "U6", "U7"):
                assert s["f2d"] == s["f1"] == s["f2r"]
        assert _np(z)[2]["Qn"] < _np(z)[1]["Qn"]


def test_izin_sni_sama_dengan_rumus():
    for z in n.ZONA2:
        i = n.izin_sni(z)
        assert abs(i["izin_st"] - (i["Qult_st"] / 2.5 - i["Qn1"])) < 1e-6
        assert abs(i["izin_lik"] - (i["Qult_tanpaU5"] / 1.1 - i["Qn2"])) < 1e-6
        assert i["izin"] == min(i["izin_st"], i["izin_lik"])


def test_setelan_beta_tahap3_mereproduksi_nsf_statis():
    for z in n.ZONA2:
        ref = n.t3.kapasitas("BOR-800", profil=z)["NSF_statis"]
        assert abs(n.nsf_u1u4_beta(z) - ref) / ref * 100 <= 0.5


def test_sisa_penurunan_dan_asaoka():
    ps = n.penurunan_sisa()
    for z in n.ZONA2:
        v = ps["zona"][z]
        assert v["sisa"] > 10.0 and 0.5 < v["k"] < 1.5
        assert profil_ok(z, ps)
    assert ps["pelat"]["SPL-07"]["s_inf"] > ps["pelat"]["SPL-01"]["s_inf"]


def profil_ok(z, ps):
    s = n.profil_sisa(z, ps)
    return s(0.0) > s(15.0) > s(30.0) >= 0.0 and abs(s(0.0) - ps["zona"][z]["sisa"]) < 1e-6


def test_uji_beban_davisson_tidak_terlampaui_dan_t218_dikeluarkan():
    u = n.telaah_uji()
    assert all(k["davisson"] > k["s200_ukur"] for k in u["kurva"].values())
    assert abs(u["rasio_rata"] - 1) * 100 <= n.TOL["capwap"]
    assert "T218" in [r["tiang"] for r in u["capwap"]]
    assert min(r["rasio"] for r in u["capwap"]) < 0.6   # T218 anomali (set 0,6 mm)


def test_excel_dan_t100():
    import openpyxl
    assert n.BERKAS.exists()
    r = n.t100()
    assert r["lolos"], r
    wb = openpyxl.load_workbook(n.BERKAS)
    assert wb["Ringkasan"].freeze_panes is not None
    assert {"Irisan Selatan", "Irisan Utara", "Pasca-Likuifaksi", "Izin Akhir", "Telaah Data Uji", "Penurunan Sisa"} <= set(wb.sheetnames)
