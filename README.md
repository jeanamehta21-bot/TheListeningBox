
# The Listening Box

The Listening Box is a Raspberry Pi audio-monitoring project for recording outdoor sounds, measuring basic audio amplitude, and optionally classifying environmental sounds or identifying bird candidates.

## What it can do

- Record audio from a configured microphone.
- Save WAV recordings locally.
- Store recording metadata and AI candidates in SQLite.
- Measure digital RMS amplitude and peak amplitude.
- Read the Raspberry Pi CPU temperature when the operating system exposes it.
- Display recordings and candidate detections in a Flask dashboard.
- Optionally use BirdNET for bird-species candidates.
- Optionally use YAMNet for general sound categories.

## Important limitations

- AI predictions are candidates, not verified observations.
- BirdNET and YAMNet perform different jobs. YAMNet does not identify exact bird species.
- RMS and peak values are digital audio measurements, not calibrated sound-pressure levels in dB SPL.
- Sound-level labels use provisional thresholds and should not be treated as scientific decibel readings.
- CPU temperature is not outdoor temperature.
- The microphone does not provide GPS. Coordinates must be configured manually if needed.
- This project does not measure humidity, wind, rainfall, or outdoor temperature without additional hardware.
- The Raspberry Pi 3 has limited computing resources. Optional AI models may be slow or incompatible with the installed operating system and Python version.

## Install the base application

From the project directory on the Raspberry Pi:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip alsa-utils sqlite3 ffmpeg

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

python database.py
```

## Configure the microphone

List the available recording devices:

```bash
arecord -l
```

The default configured device is `plughw:2,0`, but device numbers depend on the connected hardware.

To override the configured device for a session:

```bash
export LISTENING_BOX_AUDIO_DEVICE="plughw:2,0"
```

Replace that example with the device appropriate for your microphone.

## Record and analyze one clip

Activate the virtual environment, then run:

```bash
python main.py --once
```

The default recording is 30 seconds at 48 kHz, mono, 16-bit PCM.

Recordings are stored under:

```text
recordings/YYYY-MM-DD/
```

Recording metadata and candidate detections are stored in:

```text
data/listeningbox.db
```

Logs are stored in:

```text
logs/listeningbox.log
```

## Run repeated recordings

```bash
python scheduler.py
```

The default schedule is one recording every 10 minutes. The interval is measured between cycle starts when a cycle finishes before the next scheduled start; if a cycle runs longer than the interval, the next cycle starts immediately afterward.

Change `RECORD_SECONDS` and `INTERVAL_MINUTES` in `config.py` to adjust the schedule.

## Open the dashboard

Run:

```bash
python dashboard.py
```

On the Raspberry Pi itself, open:

```text
http://127.0.0.1:5000
```

To access it from another device on the same trusted local network, find the Pi's address:

```bash
hostname -I
```

Then open `http://PI_IP:5000`, replacing `PI_IP` with the Pi's actual address.

The dashboard is not an authenticated public website. Do not forward its port to the public internet or expose it on an untrusted network.

## Optional AI models

The base application can record audio without either AI model.

Install the optional dependencies only when you are ready to test them:

```bash
python -m pip install -r requirements-ai.txt
```

This installation may fail or run poorly on a Raspberry Pi 3. Test compatibility with your Python version and operating system before relying on either model.

Enable BirdNET for a session:

```bash
export LISTENING_BOX_BIRDNET=1
python main.py --once
```

Enable YAMNet for a session:

```bash
export LISTENING_BOX_YAMNET=1
python main.py --once
```

To test both in one session:

```bash
export LISTENING_BOX_BIRDNET=1
export LISTENING_BOX_YAMNET=1
python main.py --once
```

Enabling both may exceed the Pi's available memory or processing capacity. If a model fails to load, check the log file.

### BirdNET

BirdNET is intended to produce bird-species candidates. Its Python API can vary by package version, so verify the adapter against the installed version before relying on the results.

### YAMNet

YAMNet classifies general environmental sound categories. It expects 16-bit PCM WAV audio at 16 kHz or 48 kHz.

For 48 kHz recordings, the adapter uses filtered polyphase resampling to convert the audio to 16 kHz. It does not simply discard two out of every three samples.

The current adapter ranks sound classes using their average model scores across the clip. It does not yet provide precise event start and end times for each environmental sound.

## Data and backups

Back up `data/listeningbox.db` before replacing project code on an existing installation.

Do not commit real recordings, database contents, logs, credentials, or private location details to a public repository.

## Testing

The repository includes hardware-free tests for database operations, audio measurements, pipeline behavior, and YAMNet audio preparation.

The tests do not prove that the microphone works or that BirdNET and YAMNet will run on the actual Raspberry Pi. Hardware and model testing is still required.
