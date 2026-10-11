
from flask import Flask, jsonify, render_template_string

from config import HOST, PORT
from database import initialize_database, recent_detections, recent_recordings

app = Flask(__name__)

HTML = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Listening Box</title>
<style>
* { box-sizing: border-box; }
body {
    font-family: Arial, sans-serif;
    max-width: 1100px;
    margin: auto;
    padding: 24px;
    background: #f4f4f4;
    color: #222;
}
.card {
    background: white;
    padding: 20px;
    margin-bottom: 20px;
    border-radius: 12px;
    overflow-x: auto;
}
table { width: 100%; border-collapse: collapse; }
th, td {
    padding: 9px;
    text-align: left;
    border-bottom: 1px solid #ddd;
    overflow-wrap: anywhere;
}
th { background: #f8f8f8; }
.note { color: #555; font-size: 0.9rem; }
</style>
</head>
<body>
<div class="card">
    <h1>Listening Box</h1>
    <p>Outdoor sound monitoring and biodiversity observations.</p>
    <p class="note">
        Sound level is estimated from microphone amplitude. It is not
        a calibrated decibel reading or a confirmed sound identification.
    </p>
</div>

<div class="card">
    <h2>Recent bird detections</h2>
    {% if detections %}
    <table>
        <tr>
            <th>Species</th>
            <th>Confidence</th>
            <th>Time detected</th>
            <th>Recording</th>
        </tr>
        {% for d in detections %}
        <tr>
            <td>{{ d.species }}</td>
            <td>
                {% if d.confidence is not none %}
                    {{ "%.1f"|format(d.confidence * 100) }}%
                {% else %}
                    —
                {% endif %}
            </td>
            <td>{{ d.created_at }}</td>
            <td>{{ d.file_path }}</td>
        </tr>
        {% endfor %}
    </table>
    {% else %}
    <p>No bird detections recorded yet.</p>
    {% endif %}
</div>

<div class="card">
    <h2>Recent recordings and sound measurements</h2>
    {% if recordings %}
    <table>
        <tr>
            <th>Time</th>
            <th>Duration</th>
            <th>File size</th>
            <th>Relative sound level</th>
            <th>RMS amplitude</th>
            <th>Peak amplitude</th>
            <th>Pi CPU temperature</th>
        </tr>
        {% for r in recordings %}
        <tr>
            <td>{{ r.started_at }}</td>
            <td>
                {% if r.duration_seconds is not none %}
                    {{ "%.1f"|format(r.duration_seconds) }} sec
                {% else %}—{% endif %}
            </td>
            <td>
                {% if r.size_bytes is not none %}
                    {{ r.size_bytes }} bytes
                {% else %}—{% endif %}
            </td>
            <td>{{ r.sound_level or "not measured" }}</td>
            <td>
                {% if r.audio_rms is not none %}
                    {{ r.audio_rms }}
                {% else %}—{% endif %}
            </td>
            <td>
                {% if r.audio_peak is not none %}
                    {{ r.audio_peak }}
                {% else %}—{% endif %}
            </td>
            <td>
                {% if r.cpu_temperature_c is not none %}
                    {{ "%.1f"|format(r.cpu_temperature_c) }} °C
                {% else %}—{% endif %}
            </td>
        </tr>
        {% endfor %}
    </table>
    {% else %}
    <p>No recordings saved yet.</p>
    {% endif %}
    <p class="note">
        Older recordings may show dashes because these measurements
        were not stored when those recordings were first processed.
    </p>
</div>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(
        HTML,
        detections=recent_detections(),
        recordings=recent_recordings(),
    )


@app.route("/api/detections")
def api_detections():
    return jsonify(recent_detections())


@app.route("/api/recordings")
def api_recordings():
    return jsonify(recent_recordings())


if __name__ == "__main__":
    initialize_database()
    app.run(host=HOST, port=PORT, debug=False)
