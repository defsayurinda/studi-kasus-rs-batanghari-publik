# Sambungkan folder yang tidak di-commit (alat, .venv, acuan privat/pustaka/jurnal) dari folder utama ke worktree
# Claude Code, supaya MCP BIMCraft (.mcp.json memakai path relatif alat/...), skrip, dan uji jalan di worktree.
# Jalankan dari akar worktree:  powershell -ExecutionPolicy Bypass -File skrip\siapkan_worktree.ps1
# Junction tidak menyalin isi; menghapus junction tidak menghapus isi folder utama.

$akar = (git rev-parse --show-toplevel).Trim()
$utama = (Split-Path (git rev-parse --path-format=absolute --git-common-dir).Trim() -Parent)
if ($akar -eq $utama) { Write-Output "Ini folder utama, tidak perlu junction."; exit 0 }

# cache analisis OpenSees bersama (skrip/cache_analisis.py): dibuat di folder utama bila belum ada
New-Item -ItemType Directory -Force -Path (Join-Path $utama "cache") | Out-Null

foreach ($rel in @("alat", ".venv", "cache", "acuan\privat", "acuan\pustaka", "acuan\jurnal")) {
    $sumber = Join-Path $utama $rel
    $tujuan = Join-Path $akar $rel
    if (-not (Test-Path $sumber)) { Write-Output "lewati $rel (tidak ada di folder utama)"; continue }
    if (Test-Path $tujuan) { Write-Output "sudah ada $rel"; continue }
    New-Item -ItemType Junction -Path $tujuan -Target $sumber | Out-Null
    Write-Output "junction $rel -> $sumber"
}
