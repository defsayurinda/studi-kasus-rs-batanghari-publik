@echo off
rem Buka BIMCraft dengan port kontrol supaya skrip dan MCP 'bimcraft-jendela' bisa menampilkan model di jendela ini.
rem Memakai BIMCraft 0.11.0: jendela 0.12.0 berhenti sendiri di laptop ini (lihat PROGRES.md, 19 Nov 2026).
rem Tanpa argumen: membuka model konsep gabungan versi 0.11. Dengan argumen: membuka berkas .bimc atau .ifc yang diberikan.
set "APP=%~dp0alat\bimcraft\bimcraft-0.11.0-windows-x64-portable\bimcraft-0.11.0-windows-x64-portable\bimcraft.exe"
set "MODEL=%~1"
if "%MODEL%"=="" set "MODEL=%~dp0model\RSTB-T3-Konsep-v0.11.bimc"
start "" "%APP%" --control 0 "%MODEL%"
