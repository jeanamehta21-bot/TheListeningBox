# Listening Box

Complete single-Raspberry-Pi software for a Raspberry Pi 3 Model B v1.2.

## Install

On the Pi:

    sudo apt update
    sudo apt full-upgrade -y
    sudo apt install -y python3 python3-venv python3-pip alsa-utils sqlite3 ffmpeg

Then:

    cd ~/listening_box
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    python3 database.py

Check the microphone:

    arecord -l
    arecord -d 5 -f S16_LE -r 48000 -c 1 test.wav
    aplay test.wav

Test the Listening Box:

    python3 main.py --once

Start the dashboard:

    python3 dashboard.py

Find the Pi IP:

    hostname -I

Open http://PI_IP:5000 on another device on the same Wi-Fi.

For automatic recording:

    python3 scheduler.py

The default is one 60-second recording every 10 minutes.

## BirdNET

BirdNET is an optional backend. If the installed BirdNET package is incompatible with this Pi, the recorder still works and logs that BirdNET is unavailable.

AI predictions should be treated as candidate detections, not automatically confirmed observations.

## Data

recordings/YYYY-MM-DD/*.wav
data/listeningbox.db
logs/listeningbox.log
