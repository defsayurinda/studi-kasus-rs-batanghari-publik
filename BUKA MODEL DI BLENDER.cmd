@echo off
rem Buka model IFC proyek di Blender + Bonsai (3D, bisa diedit). Tanpa argumen: model konsep gabungan Tahap 3.
set "APP=%~dp0alat\blender\blender.exe"
set "MODEL=%~1"
if "%MODEL%"=="" set "MODEL=%~dp0model\RSTB-T3-Konsep.ifc"
start "" "%APP%" --python "%~dp0skrip\buka_ifc_blender.py" -- "%MODEL%"
