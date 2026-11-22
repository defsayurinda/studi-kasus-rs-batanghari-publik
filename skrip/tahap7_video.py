r"""Tahap 7 langkah 7.8: rakit video sinematik dari frame shot V-01..V-06 (dirender `tahap7_render.py --kamera V-0x`).

Pakai:
  alat\blender\blender.exe -b --python skrip\tahap7_render.py -- --kamera V-01      (ulang untuk V-02..V-06)
  .venv\Scripts\python.exe skrip\tahap7_video.py [--uji]
Keluaran: `07 DED dan RKS/Video/RSTB-Sinematik-T7.mp4` (1920 x 1080, 24 fps, H.264, bingkai 2,35:1, transisi silang).
Frame PNG ada di `07 DED dan RKS/Video/frame/` (tidak di-commit).
"""
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

AKAR = Path(__file__).resolve().parents[1]
VID = AKAR / "07 DED dan RKS" / "Video"
FRAME = VID / "frame"
FPS, W, H = 24, 1920, 1080
SILANG = 0.8  # detik transisi
SHOT = ["V-01", "V-02", "V-03", "V-04", "V-05", "V-06"]
_F = [Path(r"C:\Windows\Fonts"), AKAR / "alat" / "aset-render" / "font", Path("/usr/share/fonts/truetype/liberation")]
FONT_TEBAL = str(next((d / n for d in _F for n in ("segoeuib.ttf", "LiberationSans-Bold.ttf") if (d / n).exists()), ""))
FONT = str(next((d / n for d in _F for n in ("segoeui.ttf", "LiberationSans-Regular.ttf") if (d / n).exists()), ""))


def ffmpeg():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:  # Colab: ffmpeg sistem
        return "ffmpeg"


def kartu(path, baris, detik=3.5):
    """Kartu judul hitam dengan teks tengah; kembali berkas mp4."""
    im = Image.new("RGB", (W, H), (8, 10, 12))
    d = ImageDraw.Draw(im)
    y = H / 2 - sum(s for _t, s, _f in baris) * 0.7
    for teks, ukuran, tebal in baris:
        f = ImageFont.truetype(FONT_TEBAL if tebal else FONT, ukuran)
        w = d.textlength(teks, font=f)
        d.text(((W - w) / 2, y), teks, font=f, fill=(235, 235, 235) if tebal else (170, 175, 180))
        y += ukuran * 1.5
    png = path.with_suffix(".png")
    im.save(png)
    subprocess.run([ffmpeg(), "-y", "-loglevel", "error", "-loop", "1", "-i", str(png), "-t", str(detik), "-r", str(FPS),
                    "-vf", f"fade=in:0:{FPS},fade=out:st={detik - 1}:d=1", "-pix_fmt", "yuv420p", str(path)], check=True)
    return path


def segmen(shot, uji):
    d = FRAME / (shot + (" uji" if uji else ""))
    png = sorted(d.glob("*.png"))
    if not png:
        return None
    out = VID / "_seg" / f"{shot}.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)
    fps_in = FPS / 6 if uji else FPS
    # bingkai sinematik 2,35:1 (pita hitam atas-bawah) dan gradasi warna halus
    pita = int((H - W / 2.35) / 2)
    vf = (f"scale={W}:{H},eq=contrast=1.04:saturation=1.06,"
          f"drawbox=x=0:y=0:w=iw:h={pita}:color=black:t=fill,drawbox=x=0:y=ih-{pita}:w=iw:h={pita}:color=black:t=fill")
    daftar = out.with_suffix(".txt")  # demuxer concat: frame uji tidak berurutan (langkah 6)
    daftar.write_text("".join(f"file '{p.as_posix()}'\nduration {1 / fps_in:.5f}\n" for p in png), encoding="utf-8")
    subprocess.run([ffmpeg(), "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(daftar),
                    "-vf", vf, "-r", str(FPS), "-pix_fmt", "yuv420p", "-c:v", "libx264", "-crf", "16", str(out)], check=True)
    return out


def durasi(p):
    r = subprocess.run([ffmpeg(), "-i", str(p)], capture_output=True, text=True)
    t = r.stderr.split("Duration: ")[1].split(",")[0]
    h, m, s = t.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def rakit(uji=False):
    (VID / "_seg").mkdir(parents=True, exist_ok=True)
    seg = [kartu(VID / "_seg" / "judul.mp4", [("RUMAH SAKIT TEPIAN BATANGHARI", 64, True),
                                               ("RS tipe C · 6 lantai + basement · tepi Batanghari, Jambi", 30, False),
                                               ("Studi kasus terpadu (data simulasi)", 26, False)])]
    seg += [s for s in (segmen(k, uji) for k in SHOT) if s]
    seg.append(kartu(VID / "_seg" / "akhir.mp4", [("Model BIM → render Blender Cycles / Eevee", 34, True),
                                                  ("Portofolio Teknik Sipil · Defsa Yurinda", 28, False)]))
    masuk, filt, label, t = [], [], "[0:v]", durasi(seg[0])
    for i, s in enumerate(seg):
        masuk += ["-i", str(s)]
    for i in range(1, len(seg)):
        o = f"[v{i}]"
        filt.append(f"{label}[{i}:v]xfade=transition=fade:duration={SILANG}:offset={t - SILANG:.3f}{o}")
        t += durasi(seg[i]) - SILANG
        label = o
    keluar = VID / ("RSTB-Sinematik-T7 uji.mp4" if uji else "RSTB-Sinematik-T7.mp4")
    subprocess.run([ffmpeg(), "-y", "-loglevel", "error", *masuk, "-filter_complex", ";".join(filt), "-map", label,
                    "-r", str(FPS), "-pix_fmt", "yuv420p", "-c:v", "libx264", "-crf", "18", "-preset", "slow",
                    "-movflags", "+faststart", str(keluar)], check=True)
    print("VIDEO", keluar, round(durasi(keluar), 1), "detik")
    return keluar


if __name__ == "__main__":
    rakit("--uji" in sys.argv)
