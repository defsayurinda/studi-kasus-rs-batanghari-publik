import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "skrip"))
import tahap9_jadwal as tj  # noqa: E402


def test_bobot_dan_biaya_utuh():
    c = {b["kode"]: b for b in tj.cek_silang()}
    assert c["T-122a"]["lolos"] and c["T-122b"]["lolos"] and c["T-122c"]["lolos"]


def test_cpm_urutan_dan_lintasan_kritis():
    j = tj.jadwal()
    d = {k["kode"]: k for k in j["kegiatan"]}
    for k in j["kegiatan"]:
        for p, t, lag in k["rel"]:
            if k["kode"] in ("TC",):
                continue
            acuan = d[p]["selesai"] if t == "FS" else d[p]["mulai"]
            assert k["mulai"] >= acuan + lag
    kritis = [k for k in j["kegiatan"] if k["kritis"]]
    assert kritis and max(k["selesai"] for k in kritis) == j["T"] == d["UJI"]["selesai"]
    assert all(k["float"] >= 0 for k in j["kegiatan"] if "float" in k)


def test_durasi_wajar():
    c = {b["kode"]: b for b in tj.cek_silang()}
    assert c["T-123"]["lolos"] and c["T-124"]["lolos"]     # tiang bor dan durasi total dalam toleransi rencana
    assert 15 <= c["T-124"]["x1"] <= 24                    # bulan, orde gedung RS 6 lantai
