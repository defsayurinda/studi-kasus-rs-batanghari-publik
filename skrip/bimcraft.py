"""Klien BIMCraft (bimcraft-cli mcp), setara skrip/cadcraft.py untuk CADCraft.

Dua cara kerja:
  - Sesi(berkas): sesi tanpa jendela pada proyek .bimc/.bimt (dibuka lebih dulu). Model dibangun di sini supaya hasilnya
    pasti (perintah tidak nyasar ke dokumen lain).
  - Sesi(jendela=True): menyambung ke jendela BIMCraft yang dibuka Defsa dengan 'BUKA BIMCRAFT.cmd'
    (bimcraft.exe --control 0). Dipakai untuk menampilkan hasil: tampilkan(path) membuka berkas di jendela itu.
Aplikasi GUI yang diluncurkan dari sesi otomatis ditutup lagi oleh lingkungan Claude Code, jadi jendela BIMCraft dibuka
oleh Defsa (sekali klik), lalu skrip dan MCP 'bimcraft-jendela' menyambung ke sana.
Contoh:
    with Sesi(templat) as b:
        b.cmd("grid", {"start": [0, 0], "end": [0, 50000]})
        b.simpan("model/RSTB-ARS-T3-Massa.bimc")
    tampilkan("model/RSTB-ARS-T3-Massa.bimc")
"""
import json
import os
import socket
import subprocess
from pathlib import Path

AKAR = Path(__file__).resolve().parents[1]
CLI = AKAR / "alat" / "bimcraft" / "bimcraft-0.12.0-windows-x64-portable" / "bimcraft-cli.exe"
# Jendela memakai 0.11.0: jendela 0.12.0 berhenti sendiri di laptop ini (19 Nov 2026). 0.11.0 hanya membaca .bimc sampai
# format 17, jadi model buatan 0.12.0 ditampilkan lewat IFC-nya (diimpor 0.11.0, disimpan sebagai <nama>-v0.11.bimc).
CLI_JENDELA = (AKAR / "alat" / "bimcraft" / "bimcraft-0.11.0-windows-x64-portable" / "bimcraft-0.11.0-windows-x64-portable"
               / "bimcraft-cli.exe")
JEMBATAN = Path(os.environ.get("APPDATA", "")) / "BIMCraft" / "bridge.json"


class GalatBIM(RuntimeError):
    pass


def jendela_aktif():
    """True bila ada jendela BIMCraft yang membuka port kontrol (bridge.json menunjuk port yang hidup)."""
    try:
        port = json.loads(JEMBATAN.read_text())["port"]
    except (OSError, ValueError, KeyError):
        return False
    with socket.socket() as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", int(port))) == 0


class Sesi:
    def __init__(self, berkas=None, jendela=False):
        if not CLI.exists():
            raise GalatBIM(f"bimcraft-cli tidak ditemukan: {CLI} (di worktree jalankan skrip\\siapkan_worktree.ps1)")
        if jendela and not jendela_aktif():
            raise GalatBIM("Tidak ada jendela BIMCraft berport kontrol. Buka dulu dengan 'BUKA BIMCRAFT.cmd'.")
        cli = CLI_JENDELA if jendela and CLI_JENDELA.exists() else CLI
        argumen = [str(cli), "mcp"] + (["--connect"] if jendela else ([str(Path(berkas).resolve())] if berkas else []))
        self.p = subprocess.Popen(argumen, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  encoding="utf-8", bufsize=1)
        self._id = 0
        self._rpc("initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                                 "clientInfo": {"name": "studi-kasus", "version": "1"}})
        self._kirim({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def _kirim(self, obj):
        self.p.stdin.write(json.dumps(obj, ensure_ascii=False) + "\n")
        self.p.stdin.flush()

    def _rpc(self, method, params):
        self._id += 1
        self._kirim({"jsonrpc": "2.0", "id": self._id, "method": method, "params": params})
        while True:
            baris = self.p.stdout.readline()
            if not baris:
                raise GalatBIM("bimcraft-cli berhenti: " + (self.p.stderr.read() or "")[:500])
            d = json.loads(baris)
            if d.get("id") == self._id:
                if "error" in d:
                    raise GalatBIM(f"{method}: {d['error']}")
                return d["result"]

    def alat(self, nama, args):
        r = self._rpc("tools/call", {"name": nama, "arguments": args})
        teks = "".join(c.get("text", "") for c in r.get("content", []) if c.get("type") == "text")
        if r.get("isError"):
            raise GalatBIM(f"{nama} {json.dumps(args, ensure_ascii=False)[:300]}: {teks[:500]}")
        try:
            return json.loads(teks) if teks else {}
        except json.JSONDecodeError:
            return {"teks": teks}

    def cmd(self, perintah, params=None):
        return self.alat("execute", {"command": perintah, "params": params or {}})

    def buka(self, path):
        return self.alat("open", {"path": str(Path(path).resolve())})

    def simpan(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        return self.alat("save", {"path": str(Path(path).resolve())})

    def periksa(self):
        return self.alat("inspect_model", {})

    def tutup(self):
        if self.p.poll() is None:
            self.p.stdin.close()
            try:
                self.p.wait(10)
            except subprocess.TimeoutExpired:
                self.p.kill()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.tutup()


def ke_v011(ifc, kamera=None):
    """Impor IFC dengan BIMCraft 0.11.0 lalu simpan sebagai <nama>-v0.11.bimc (dapat dibuka jendela 0.11.0).
    kamera: parameter perintah `camera` untuk view 3D bernama yang ikut disimpan."""
    ifc = Path(ifc).resolve()
    keluar = ifc.with_name(ifc.stem + "-v0.11.bimc")
    lama, mod = None, globals()
    lama, mod["CLI"] = mod["CLI"], CLI_JENDELA
    try:
        with Sesi(ifc) as b:
            if kamera:
                b.cmd("camera", kamera)
            b.simpan(keluar)
    finally:
        mod["CLI"] = lama
    return keluar


def tampilkan(path, kamera=None):
    """Buka model di jendela BIMCraft yang sedang terbuka (bila ada). Berkas .bimc buatan 0.12.0 ditampilkan lewat
    salinan 0.11 dari IFC-nya. Kembalikan True bila tampil."""
    p = Path(path)
    if p.suffix == ".bimc" and p.with_suffix(".ifc").exists() and CLI_JENDELA.exists():
        p = ke_v011(p.with_suffix(".ifc"), kamera)
    if not jendela_aktif():
        return False
    with Sesi(jendela=True) as w:
        w.buka(p)
    return True
