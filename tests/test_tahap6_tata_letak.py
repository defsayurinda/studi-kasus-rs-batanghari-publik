import sys
from functools import lru_cache
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skrip"))
import tahap6_tata_letak as t  # noqa: E402


def test_izin_dan_tahanan_dari_62_61():
    s, u = t.sifat("SELATAN"), t.sifat("UTARA")
    assert abs(s["izin"] - 1583.2) < 0.5 and abs(u["izin"] - 1443.3) < 0.5
    assert abs(s["tekan_gm"] - 3294) < 2 and abs(u["tarik_gm"] - 1951) < 2
    assert abs(t.sifat("SELATAN", t.TAMBAH)["izin"] - 1750.1) < 0.5       # varian (b) 40,00 m


def test_cap_kaku_sama_dengan_matriks_dan_jumlah_beban():
    pos = [(0, 0), (2.4, 0), (0, 2.4), (2.4, 2.4), (4.8, 0), (4.8, 2.4)]
    beban = [(1.0, 1.0, 3000.0), (3.0, 1.5, 1000.0)]
    for mux, muy in ((0, 0), (5000, -2000)):
        a, b = t.beban_tiang(pos, beban, mux, muy), t.beban_matriks(pos, beban, mux, muy)
        assert np.allclose(a, b, atol=1e-6) and abs(a.sum() - 4000) < 1e-6


def test_total_tiang_dan_selisih_tahap3():
    ra, rb = t.ringkas("a"), t.ringkas("b")
    # berat cap dimasukkan (22 Nov 2026): 152/78/230 menjadi 143/108/251 (+9,1 %)
    assert (ra["n_kolom"], ra["n_inti"], ra["n"]) == (143, 108, 251)
    assert ra["n_t3"] == t.N_T3 == 305 and ra["n_t3_kolom"] == 173 and ra["n_t3_inti"] == 132
    assert rb["n"] == 249 and abs(rb["panjang"] - 9667.05) < 0.1   # varian b (hanya dilaporkan; Cap E gabungan tak lolos), selatan +1,55 m


def test_jarak_min_semua_tiang_dan_cek_lolos():
    pos = np.array(t.semua_tiang("a"))
    d = t.cKDTree(pos).query(pos, k=2)[0][:, 1]
    assert d.min() >= t.S - 1e-9
    ck, ci = t.rancang("a")
    assert all(c["r"]["lolos"] for c in ck + ci)
    ckb, cib = t.rancang("b")       # varian (b): hanya Cap E gabungan yang tak lolos dengan berat cap
    assert [c["id"] for c in ckb + cib if not c["r"]["lolos"]] == ["Cap E"]


def test_sum_beban_tiang_sama_sum_reaksi():
    tb = t.titik_beban()
    ck, ci = t.rancang("a")
    tot = sum(float(c["r"]["P_lay_semua"].sum()) for c in ck + ci)
    wtot = sum(c["r"]["W"] for c in ck + ci)          # berat cap ikut dalam reaksi tiang
    assert len(tb) == 77 and abs(tot - sum(x["Pmax"] for x in tb.values()) - wtot) < 1e-6 * tot
    for c in ci:
        assert abs(float(c["r"]["P_lay_semua"].sum()) - sum(x["Pmax"] for x in c["titik"]) - c["r"]["W"]) < 1e-6


def test_cap_e_dan_temuan_lif():
    f = t.temuan_lif()
    assert abs(f["per_tiang"] - 1709.6) < 0.5 and f["n_sendiri"] == 7
    e = next(c for c in t.rancang("a")[1] if c["kode"] == "E")
    assert {"Cap C", "Cap E"} <= set(e["gabungan"]) and e["r"]["n"] == 54 and e["n0"] == 44 and e["r"]["P_layan"] <= f["izin"]
    assert e["union"]["n"] == 60 and not e["union"]["cek"]["jarak"]    # gabungan polos 60 tiang melanggar jarak 2,4 m -> tata letak baru 54 tiang
    assert e["r"]["ef"]["eta"] == 1.0 and abs(e["r"]["sumP"] - 77748.6) < 0.5 and e["r"]["lolos"]
    assert abs(e["r"]["W"] - t.berat_cap(e["r"]["A"], t.H_E)) < 1e-6          # berat cap bersih (apung) Cap E h 1,8


def test_kepekaan_100_100_dan_efisiensi():
    kp = t.kepekaan_penuh()
    assert kp["n"] > t.ringkas("a")["n_inti"]            # 100 % + 100 % lebih banyak tiang
    for c in t.rancang("a")[1]:
        e = c["r"]["ef"]
        assert e["eta"] == 1.0 and e["eta_cl"] < 1.0      # blok tidak menentukan; Converse-Labarre hanya pembanding


def test_excel_dan_t101():
    import openpyxl
    assert t.BERKAS.exists()
    wb = openpyxl.load_workbook(t.BERKAS, data_only=True)
    assert wb["Ringkasan"].freeze_panes is not None
    assert {"Ringkasan", "Cap Inti", "Cap Kolom", "Varian 40 m", "Verifikasi", "Acuan", "Keputusan"} <= set(wb.sheetnames)
    ws = wb["Cap Inti"]
    nilai = [c.value for r in ws.iter_rows() for c in r if isinstance(c.value, (int, float))]
    assert nilai and max(nilai) > 1000                    # rumus hidup sudah dihitung ulang
    r = t.t101()
    assert r["lolos"] and r["pasang"] == 0, r


def test_berat_cap_tangan():
    """W = A h 24 - 9,81 A (11,20 - dasar) bila dasar < +11,20: A 100 m², h 1,0 (dasar 11,05): 2.400 - 9,81 × 100 × 0,15 = 2.252,85 kN; h 0,8 (dasar 11,25): 1.920."""
    assert abs(t.berat_cap(100.0, 1.0) - 2252.85) < 1e-6 and abs(t.berat_cap(100.0, 0.8) - 1920.0) < 1e-6


def test_tidak_ada_dua_cap_bertumpang():
    for v in "a":
        ck, ci = t.rancang(v)
        cs = ck + ci
        assert [(a["id"], b["id"]) for i, a in enumerate(cs) for b in cs[i + 1:] if t.bertumpang(a, b) > 1e-6] == []
