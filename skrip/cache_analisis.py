"""Cache disk bersama untuk analisis OpenSees Tahap 4 (balok, kolom, dinding inti) dan rancangan
turunannya (rancang 4.6/4.7/4.8, hasil 4.6-4.7 untuk 5.1).

Satu analisis 4.3 makan 50-150 detik dan dipanggil ulang oleh setiap skrip/uji Tahap 4-6 di setiap sesi.
Hasil disimpan di `cache/opensees/` (tidak di-commit; di worktree disambung ke folder utama lewat
`skrip/siapkan_worktree.ps1`). Kunci = nama fungsi + argumen + ukuran balok/kolom model + sidik semua skrip
tahap3/tahap4 dan data masukan, jadi hasil lama tidak pernah dipakai bila kode atau data berubah.
Matikan dengan env `TANPA_CACHE=1`; kosongkan dengan menghapus folder `cache/opensees/`.
"""
from __future__ import annotations

import functools
import hashlib
import os
import pickle
import sys
from pathlib import Path

AKAR = Path(__file__).resolve().parents[1]
FOLDER = AKAR / "cache" / "opensees"


@functools.lru_cache(maxsize=1)
def sidik_masukan():
    """Hash isi skrip yang membangun model dan data masukannya."""
    h = hashlib.sha256()
    berkas = sorted((AKAR / "skrip").glob("tahap[34]_*.py"))
    berkas += sorted((AKAR / "04 Struktur Atas").glob("*.csv"))
    berkas += sorted(p for p in (AKAR / "04 Struktur Atas" / "Data Owner").rglob("*") if p.is_file())
    for p in berkas:
        h.update(p.name.encode())
        h.update(p.read_bytes())
    return h.hexdigest()


def _sederhana(v):
    """Hanya argumen kecil yang repr-nya utuh (tanpa '...' numpy) boleh jadi kunci."""
    if v is None or isinstance(v, (str, int, float, bool)):
        return True
    if isinstance(v, (tuple, list, frozenset)):
        return all(_sederhana(x) for x in v)
    if isinstance(v, dict):
        return all(_sederhana(k) and _sederhana(x) for k, x in v.items())
    return False


def disk(fungsi):
    """Dekorator: simpan hasil fungsi analisis ke pickle di FOLDER."""
    @functools.wraps(fungsi)
    def bungkus(*args, **kwargs):
        if os.environ.get("TANPA_CACHE") or not _sederhana((args, kwargs)):
            return fungsi(*args, **kwargs)
        import tahap4_model as tm   # ukuran global model ikut kunci (dipasang pemanggil sebelum analisis)
        modul = Path(sys.modules[fungsi.__module__].__file__).read_bytes()   # skrip tahap 5+ ikut sidik bila didekorasi
        kunci = repr((fungsi.__module__, fungsi.__qualname__, args, sorted(kwargs.items()),
                      sorted(tm.UKURAN_BALOK.items()), sorted(tm.UKURAN_KOLOM.items()), sidik_masukan(),
                      hashlib.sha256(modul).hexdigest()))
        berkas = FOLDER / f"{fungsi.__module__}.{fungsi.__name__}-{hashlib.sha256(kunci.encode()).hexdigest()[:20]}.pkl"
        if berkas.exists():
            try:
                with open(berkas, "rb") as f:
                    return pickle.load(f)
            except Exception:   # berkas rusak/terpotong: hitung ulang
                pass
        hasil = fungsi(*args, **kwargs)
        FOLDER.mkdir(parents=True, exist_ok=True)
        sementara = berkas.with_suffix(f".{os.getpid()}.tmp")
        with open(sementara, "wb") as f:
            pickle.dump(hasil, f)
        os.replace(sementara, berkas)   # atomik: sesi paralel tidak membaca berkas setengah jadi
        return hasil
    return bungkus
