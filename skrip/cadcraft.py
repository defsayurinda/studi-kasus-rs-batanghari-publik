"""Klien CADCraft (cadcraft-cli mcp, sesi gambar tanpa jendela) untuk membuat gambar DWG dari skrip.

Contoh:
    with Sesi() as cad:
        cad.cmd("line", {"points": [[0, 0], [10, 0]]})
        cad.simpan("gambar.dwg")
Lokasi program: variabel lingkungan CADCRAFT_CLI atau bawaan di Program Files.
"""
import json
import os
import subprocess
from pathlib import Path

CLI = Path(os.environ.get("CADCRAFT_CLI", r"C:\Program Files\ArtCraft\CADCraft\cadcraft-cli.exe"))


def _polos(o):
    """Nilai numpy (float64, bool_, larik) menjadi tipe JSON biasa."""
    if hasattr(o, "tolist"):
        return o.tolist()
    if hasattr(o, "item"):
        return o.item()
    raise TypeError(type(o))


class GalatCAD(RuntimeError):
    pass


APP = CLI.with_name("cadcraft.exe")
PORT_JENDELA = int(os.environ.get("CADCRAFT_PORT", "7979"))


def buka_jendela(port=PORT_JENDELA):
    """Buka aplikasi CADCraft (GUI) dengan port kontrol, bila belum terbuka. Gambar lalu dibuat di jendela itu."""
    import socket
    import time

    with socket.socket() as s:
        if s.connect_ex(("127.0.0.1", port)) == 0:
            return False
    subprocess.Popen([str(APP), "--control", str(port)], creationflags=getattr(subprocess, "DETACHED_PROCESS", 0))
    for _ in range(60):
        time.sleep(0.5)
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", port)) == 0:
                return True
    raise GalatCAD(f"CADCraft tidak membuka port kontrol {port}")


class Sesi:
    """Sesi CADCraft. jendela=True (atau env CADCRAFT_JENDELA=1): menggambar di aplikasi CADCraft yang terbuka
    (dibuka otomatis dengan --control), sehingga prosesnya terlihat dan berkas bisa langsung diteruskan manual."""

    def __init__(self, jendela=None):
        if not CLI.exists():
            raise GalatCAD(f"cadcraft-cli tidak ditemukan: {CLI}")
        if jendela is None:
            jendela = os.environ.get("CADCRAFT_JENDELA") == "1"
        argumen = [str(CLI), "mcp"]
        if jendela:
            buka_jendela()
            argumen += ["--connect", f"127.0.0.1:{PORT_JENDELA}"]
        self.p = subprocess.Popen(argumen, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, encoding="utf-8", bufsize=1)
        self._id = 0
        self._rpc("initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                                 "clientInfo": {"name": "studi-kasus", "version": "1"}})
        self._kirim({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def _kirim(self, obj):
        self.p.stdin.write(json.dumps(obj, ensure_ascii=False, default=_polos) + "\n")
        self.p.stdin.flush()

    def _rpc(self, method, params):
        self._id += 1
        self._kirim({"jsonrpc": "2.0", "id": self._id, "method": method, "params": params})
        while True:
            baris = self.p.stdout.readline()
            if not baris:
                raise GalatCAD("cadcraft-cli berhenti")
            d = json.loads(baris)
            if d.get("id") == self._id:
                if "error" in d:
                    raise GalatCAD(f"{method}: {d['error']}")
                return d["result"]

    def alat(self, nama, args):
        r = self._rpc("tools/call", {"name": nama, "arguments": args})
        teks = "".join(c.get("text", "") for c in r.get("content", []) if c.get("type") == "text")
        if r.get("isError"):
            raise GalatCAD(f"{nama} {json.dumps(args, ensure_ascii=False)[:300]}: {teks[:500]}")
        try:
            return json.loads(teks) if teks else {}
        except json.JSONDecodeError:
            return {"teks": teks}

    def cmd(self, perintah, params=None):
        return self.alat("execute", {"command": perintah, "params": params or {}})

    def baru(self, metric=True):
        return self.alat("new_drawing", {"metric": metric})

    def buka(self, path):
        return self.alat("open", {"path": str(path)})

    def simpan(self, path):
        return self.alat("save", {"path": str(path)})

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
