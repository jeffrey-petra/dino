#!/bin/bash
PYTHON_BIN="python"
VENV_DIR=".venv"

if [ ! -d "$VENV_DIR" ]; then
    "$PYTHON_BIN" -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    "$PYTHON_BIN" -m pip install --upgrade pip
    "$PYTHON_BIN" -m pip install -r requirements.txt
else
    source "$VENV_DIR/bin/activate"
fi

cd src
"$PYTHON_BIN" main.py
