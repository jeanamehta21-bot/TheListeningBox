#!/bin/bash
set -e

sudo apt update
sudo apt full-upgrade -y
sudo apt install -y python3 python3-venv python3-pip alsa-utils sqlite3 ffmpeg

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

python database.py

echo "Installation complete."
echo "Test microphone with: arecord -l"
echo "Run one cycle with: python3 main.py --once"
