# Memasang semua alat studi kasus di laptop ini. Aman dijalankan ulang: yang sudah ada dilewati.
# Pakai: powershell -ExecutionPolicy Bypass -File SIAPKAN.ps1
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$alat = Join-Path $root 'alat'
$unduh = Join-Path $alat '_unduhan'
New-Item -ItemType Directory -Force $unduh | Out-Null

function Get-Berkas($nama, $url, $sha256) {
    $f = Join-Path $unduh $nama
    if (-not (Test-Path $f)) {
        Write-Host "Mengunduh $nama"
        curl.exe -sSL -o $f $url
        if ($LASTEXITCODE -ne 0) { throw "Gagal mengunduh $url" }
    }
    $h = (Get-FileHash $f -Algorithm SHA256).Hash.ToLower()
    if ($h -ne $sha256) { Remove-Item $f; throw "Checksum $nama tidak cocok (berkas dihapus, jalankan ulang)" }
    return $f
}

# 1. BIMCraft (pemodelan BIM)
if (-not (Test-Path "$alat\bimcraft\bimcraft-0.12.0-windows-x64-portable\bimcraft.exe")) {
    $f = Get-Berkas 'bimcraft-0.12.0-windows-x64-portable.zip' 'https://github.com/IPedrax/BIMCraft/releases/download/v0.12.0/bimcraft-0.12.0-windows-x64-portable.zip' '2f6e0d23035c355792002eda14360b041fcac998d90c5923832c467f01d6d8a6'
    Expand-Archive $f "$alat\bimcraft" -Force
}
# BIMCraft 0.11.0 untuk jendela: jendela 0.12.0 berhenti sendiri di laptop ini (PROGRES.md, 19 Nov 2026)
if (-not (Test-Path "$alat\bimcraft\bimcraft-0.11.0-windows-x64-portable\bimcraft-0.11.0-windows-x64-portable\bimcraft.exe")) {
    $f = Get-Berkas 'bimcraft-0.11.0-windows-x64-portable.zip' 'https://github.com/IPedrax/BIMCraft/releases/download/v0.11.0/bimcraft-0.11.0-windows-x64-portable.zip' 'ddd288244ba202a3b271dd2d14843e7150c5bf993e2be5b00e7906cbce657c5d'
    Expand-Archive $f "$alat\bimcraft\bimcraft-0.11.0-windows-x64-portable" -Force
}

# 2. Blender 5.2.4 LTS portable + Bonsai 0.9.0
if (-not (Test-Path "$alat\blender\blender.exe")) {
    $f = Get-Berkas 'blender-5.2.4-windows-x64.zip' 'https://download.blender.org/release/Blender5.2/blender-5.2.4-windows-x64.zip' 'bbd78f8931dc940444da4ff2983374930f9f5c092ae0e330588e9760bb9d967c'
    Expand-Archive $f $alat -Force
    Rename-Item "$alat\blender-5.2.4-windows-x64" 'blender'
    New-Item -ItemType Directory -Force "$alat\blender\portable" | Out-Null  # konfigurasi Blender disimpan di folder ini
}
if (-not (Test-Path "$alat\blender\portable\extensions\user_default\bonsai")) {
    $f = Get-Berkas 'bonsai_py313-0.9.0-post1-windows-x64.zip' 'https://github.com/IfcOpenShell/IfcOpenShell/releases/download/bonsai-0.9.0post1/bonsai_py313-0.9.0-post1-windows-x64.zip' '9467fdfbea8f3506f788135ba33bb62bfd2d465858360390321f54698ec04d6c'
    & "$alat\blender\blender.exe" --command extension install-file -r user_default -e $f
}

# 3. FreeCAD 1.1.4 portable (7z, diekstrak dengan tar bawaan Windows)
if (-not (Test-Path "$alat\freecad\bin\FreeCAD.exe")) {
    $f = Get-Berkas 'FreeCAD_1.1.4-Windows-x86_64-py311.7z' 'https://github.com/FreeCAD/FreeCAD/releases/download/1.1.4/FreeCAD_1.1.4-Windows-x86_64-py311.7z' '4828741fc91ee37fafcdb97a1abacb18b04ba451ac4372d9ff7a7349b36f4d6d'
    Push-Location $alat; tar.exe -xf $f; Pop-Location
    Rename-Item "$alat\FreeCAD_1.1.4-Windows-x86_64-py311" 'freecad'
}

# 4. QGIS LTR dan ProjectLibre (dipasang di sistem lewat winget)
foreach ($id in 'OSGeo.QGIS_LTR', 'ProjectLibre.ProjectLibre') {
    winget list --id $id --exact | Out-Null
    if ($LASTEXITCODE -ne 0) { winget install --id $id --exact --silent --accept-package-agreements --accept-source-agreements }
}

# 5. Lingkungan Python proyek
if (-not (Test-Path "$root\.venv\Scripts\python.exe")) {
    $py = 'C:\Users\Defsa\AppData\Local\Programs\Python\Python312\python.exe'
    if (-not (Test-Path $py)) { $py = (Get-Command python).Source }
    & $py -m venv "$root\.venv"
}
& "$root\.venv\Scripts\python.exe" -m pip install -q --upgrade pip
& "$root\.venv\Scripts\python.exe" -m pip install -q -r "$root\requirements.txt"

Write-Host 'Selesai. Salin dokumen SNI ke acuan\privat\ (tidak ikut di repo).'
