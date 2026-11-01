
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

### BirdNET-Analyzer

The project adapter calls the official `birdnet-analyze` command-line tool and requests the BirdNET 3.0 acoustic model. It converts the Analyzer CSV output into the Listening Box detection format, preserving species names, confidence scores, and segment start/end times.

Install `requirements-ai.txt` in a dedicated environment on a capable analysis computer (Windows or another supported desktop). The full Analyzer is not intended to run inside the Raspberry Pi 3 recording scheduler, which should continue recording independently. Use Python 3.13 for the analysis environment until the full dependency stack explicitly supports newer Python versions.

The official Analyzer is invoked as a separate process, so the project's `birdnet_analyzer.py` adapter filename does not replace or shadow the installed package. BirdNET 3.0 is explicitly selected; it is not the older `birdnet==0.1.4` API.

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


## Research dashboard pages

The Flask dashboard also provides local research views:

- `/activity`: hourly and daily candidate-detection patterns.
- `/timeline`: detections for a selected date.
- `/species`: searchable candidate-label index.
- `/review`: manually classify candidate detections as confirmed, uncertain, or false positive. Reviews are stored separately and do not delete raw model output.
- `/insights`: descriptive dawn/night activity summaries, with cautions against over-interpreting small samples.
- `/weather`: stored hourly weather history.
- `/year`: yearly and monthly candidate-detection summary.
- `/health`: database-level counts and last recording timestamp.

### Weather setup

Weather uses the free Open-Meteo forecast API without an API key. It is regional weather-model data, not a physical sensor at the microphone. Configure the actual monitoring site's `LATITUDE` and `LONGITUDE` in `config.py`; do not use a private home location unless the station is installed there. Then run:

```bash
python weather_sync.py
```

The sync retrieves the previous seven days plus the near-term forecast and stores hourly temperature, humidity, precipitation, wind speed, and weather code in a separate SQLite table. Re-run it periodically to refresh the history. No coordinates are committed to the public repository.

The review queue, timeline, activity charts, species index, and yearly summary are based on existing database fields. They do not yet provide audio playback, spectrograms, photo galleries, verified eBird exports, live streaming, or ecological health scores. Those require additional validated data and/or services and should not be represented as available until implemented and tested.
