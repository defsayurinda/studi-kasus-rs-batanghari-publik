r"""Jalankan render Blender satu per satu dengan pengaman suhu GPU (laptop mati karena panas, 22 Nov 2026).

Pakai: .venv\Scripts\python.exe skrip\render_aman.py R-02 R-03 ... V-01 ...
- Tiap kamera: proses Blender latar `tahap7_render.py -- --kamera <k>`; suhu GPU dibaca nvidia-smi tiap 5 s.
- Berhenti paksa bila >= BATAS_KERAS sekali, atau >= BATAS_LAMA terus-menerus LAMA detik; kamera itu dicoba lagi sekali
  setelah dingin.
- Sebelum kamera berikutnya: tunggu GPU < DINGIN (paling lama 6 menit).
Log suhu: cache/tahap7_render/suhu.csv
"""
import subprocess
import sys
import time
from pathlib import Path

AKAR = Path(__file__).resolve().parents[1]
BLENDER = AKAR / "alat" / "blender" / "blender.exe"
SMI = r"C:\Windows\System32\nvidia-smi.exe"
LOG = AKAR / "cache" / "tahap7_render"
EKSTRA = []
BATAS_KERAS, BATAS_LAMA, LAMA, DINGIN = 92, 90, 15, 58


def suhu():
    try:
        r = subprocess.run([SMI, "--query-gpu=temperature.gpu,power.draw,clocks.sm", "--format=csv,noheader,nounits"],
                           capture_output=True, text=True, timeout=15)
        t, w, c = (x.strip() for x in r.stdout.split(","))
        return int(t), float(w), int(c)
    except Exception:
        return None


def catat(k, s):
    with open(LOG / "suhu.csv", "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%H:%M:%S')},{k},{s[0]},{s[1]},{s[2]}\n")


def tunggu_dingin():
    t0 = time.time()
    while time.time() - t0 < 360:
        s = suhu()
        if s is None or s[0] < DINGIN:
            return
        time.sleep(10)


def render(k):
    log = open(LOG / f"log_{k}.txt", "w", encoding="utf-8", errors="replace")
    p = subprocess.Popen([str(BLENDER), "-b", "--python", str(AKAR / "skrip" / "tahap7_render.py"), "--", "--kamera", k] + EKSTRA,
                         cwd=AKAR, stdout=log, stderr=subprocess.STDOUT)
    panas_sejak, maks = None, 0
    while p.poll() is None:
        time.sleep(1)
        s = suhu()
        if s is None:
            continue
        catat(k, s)
        maks = max(maks, s[0])
        panas_sejak = (panas_sejak or time.time()) if s[0] >= BATAS_LAMA else None
        if s[0] >= BATAS_KERAS or (panas_sejak and time.time() - panas_sejak > LAMA):
            p.kill()
            print(f"{k}: DIHENTIKAN, GPU {s[0]} C", flush=True)
            return False, maks
    log.close()
    teks = (LOG / f"log_{k}.txt").read_text(encoding="utf-8", errors="replace")
    ok = "RENDER SELESAI" in teks or "VIDEO SELESAI" in teks
    print(f"{k}: {'selesai' if ok else 'GAGAL'}, GPU maks {maks} C", flush=True)
    return ok, maks


if __name__ == "__main__":
    EKSTRA = [a for a in sys.argv[1:] if a.startswith("--")]
    for k in [a for a in sys.argv[1:] if not a.startswith("--")]:
        tunggu_dingin()
        ok, _m = render(k)
        if not ok:
            tunggu_dingin()
            render(k)
