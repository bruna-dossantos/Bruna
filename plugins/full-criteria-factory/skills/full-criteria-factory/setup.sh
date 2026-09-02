#!/usr/bin/env bash
# One-time setup per install: create the Python venv the render/pdf/pdfplumber steps need.
# Run from this skill directory:  bash setup.sh
set -euo pipefail
cd "$(dirname "$0")"
python3 -m venv .venv
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r requirements.txt
echo "venv ready: $(pwd)/.venv  (python-docx, reportlab, pdfplumber installed)"
