#!/bin/bash
set -euo pipefail

sudo apt update
sudo apt install -y python3 python3-venv python3-pip alsa-utils sqlite3 ffmpeg

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python database.py

echo "Base installation complete."
echo "Check microphone: arecord -l"
echo "Run one recording: python main.py --once"
echo "Start dashboard: python dashboard.py"
echo "AI packages are optional; read README.md before installing requirements-ai.txt."
