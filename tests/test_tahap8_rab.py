import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "skrip"))
import tahap8_rab as rb  # noqa: E402


def test_t121d_item_8a_utuh_di_divisi():
    b = {x["kode"]: x for x in rb.cek_silang()}["T-121d"]
    assert b["lolos"] and b["x2"] > 100e9


def test_rekap_konsisten():
    r = rb.rekap()
    assert abs(sum(j for *_, j in r["sub"]) + r["j_smkk"] - r["jumlah"]) < 1
    assert abs(r["total"] - r["jumlah"] * (1 + rb.PPN)) < 1
    assert 10e6 < r["per_m2"] < 20e6        # orde biaya RS per m² (Rp juta), pembanding asumsi owner 14 juta


def test_smkk_sembilan_komponen_dan_car():
    r = rb.rekap()
    assert {x["komponen"] for x in r["smkk"]} == set(range(1, 10))
    car = next(x for x in r["smkk"] if x["komponen"] == 4)
    assert abs(car["jumlah"] - rb.CAR * r["fisik"]) < 1


def test_ve_positif_dan_berurutan():
    v = rb.ve()
    assert 3 <= len(v) <= 5 and all(o["hemat"] > 0 for o in v)
    assert all(a["sisa"] > b["sisa"] for a, b in zip(v, v[1:]))
