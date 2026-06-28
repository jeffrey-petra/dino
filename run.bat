@echo off
set "PYTHON_BIN=python"
set "VENV_DIR=.venv"

if not exist "%VENV_DIR%" (
    "%PYTHON_BIN%" -m venv "%VENV_DIR%"
    call "%VENV_DIR%\Scripts\activate.bat"
    "%PYTHON_BIN%" -m pip install --upgrade pip
    "%PYTHON_BIN%" -m pip install -r requirements.txt
) else (
    call "%VENV_DIR%\Scripts\activate.bat"
)

cd src
"%PYTHON_BIN%" main.py
