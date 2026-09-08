@echo off
REM Doble clic: refresca cada 5 min y sirve la pagina en la red local.
cd /d "%~dp0"
python uso.py --loop 5 --serve 8787
pause
