@echo off
cd /d "%~dp0"
py -m simulador
if errorlevel 1 pause
