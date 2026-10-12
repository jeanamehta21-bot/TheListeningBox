# The Listening Box

A Raspberry Pi audio-monitoring project that records outdoor sound, measures basic audio amplitude, and can optionally run BirdNET for bird candidates and YAMNet for broad environmental sound categories.

## Important limitations

- A model prediction is a candidate, not a verified observation.
- YAMNet's broad sound categories are not exact species identification.
- The CPU temperature reading is the Raspberry Pi's temperature, not outdoor temperature.
- The microphone does not provide GPS. Set a real monitoring location manually if location-based filtering is enabled.
- Raspberry Pi 3 resources are limited. Test the models on a computer before enabling both on the Pi.
- The BirdNET Python API can vary by package version. Confirm the installed package's API before relying on its predictions.

## Install base application

On the Raspberry Pi, from the project directory:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip alsa-utils sqlite3 ffmpeg
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python database.py
```

## Configure the microphone

The default `AUDIO_DEVICE` in `config.py` is `plughw:2,0`, based on the USB microphone previously tested on one setup. Device numbers can change. Check with:

```bash
arecord -l
```

If needed, edit `AUDIO_DEVICE` in `config.py`. The program now uses that setting rather than hardcoding `default`.

## Run

```bash
python main.py --once
```

Start the web dashboard:

```bash
python dashboard.py
```

Find the Pi address with `hostname -I`, then open `http://PI_IP:5000` from another device on the same network.

For repeated cycles:

```bash
python scheduler.py
```

The default is one 30-second recording every 10 minutes. Change `RECORD_SECONDS` in `config.py` as needed.

## Optional AI models

AI dependencies are separated from the base install on purpose:

```bash
pip install -r requirements-ai.txt
```

This may not install successfully or run efficiently on Raspberry Pi 3. Test on a computer first.

Enable a model using environment variables before launching Python:

```bash
export LISTENING_BOX_BIRDNET=1
export LISTENING_BOX_YAMNET=1
```

YAMNet expects 16-bit mono WAV at 16 kHz or 48 kHz; 48 kHz is downsampled to 16 kHz by taking every third sample. This simple method is suitable only for this expected rate; use a proper resampler for other rates.

BirdNET uses the adapter in `birdnet_analyzer.py`; verify the API against the installed version. The code intentionally leaves location filtering disabled by default rather than using a made-up location.

## Data

- `recordings/YYYY-MM-DD/*.wav`
- `data/listeningbox.db`
- `logs/listeningbox.log`

The database schema is migrated additively to preserve existing data. Back up your database before using a rewritten project on an existing installation.
