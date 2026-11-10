@echo off
chcp 65001 >nul
title Simulador de Markov - Iglesia de Santo Domingo
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo No se encontro Python. Instalalo desde https://www.python.org/downloads/ y marca "Add Python to PATH".
  pause
  exit /b
)
echo Instalando dependencias (solo la primera vez tarda un poco)...
python -m pip install -r requirements.txt --quiet
echo.
python app.py
pause
