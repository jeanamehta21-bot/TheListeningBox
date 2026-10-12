
#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

sudo apt update
sudo apt install -y \
    python3 \
    python3-venv \
    python3-pip \
    alsa-utils \
    sqlite3 \
    ffmpeg

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python database.py

echo
echo "Base installation complete."
echo "Check the microphone with: arecord -l"
echo "Record one clip with: python main.py --once"
echo "Start the dashboard with: python dashboard.py"
echo "Optional AI dependencies are documented in README.md."
