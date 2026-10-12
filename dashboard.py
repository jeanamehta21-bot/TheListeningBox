
from flask import Flask, jsonify, render_template_string

from config import HOST, PORT
from database import (
    initialize_database,
    recent_detections,
    recent_recordings,
)

app = Flask(__name__)

HTML = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>The Listening Box</title>
<style>
body {
    font-family: Arial, sans-serif;
    max-width: 1200px;
    margin: auto;
    padding: 20px;
    background: #f3f5f4;
    color: #222;
}
.card {
    background: white;
    padding: 18px;
    margin-bottom: 18px;
    border-radius: 12px;
    overflow-x: auto;
}
table {
    width: 100%;
    border-collapse: collapse;
}
th, td {
    text-align: left;
    padding: 9px;
    border-bottom: 1px solid #ddd;
    overflow-wrap: anywhere;
}
th {
    background: #eef1ef;
}
.note {
    color: #555;
    font-size: .9rem;
}
</style>
</head>
<body>
<div class="card">
<h1>The Listening Box</h1>
<p>Outdoor audio monitoring and biodiversity candidate detections.</p>
<p class="note">
AI predictions are candidates, not confirmed observations.
RMS and peak are digital audio measurements, not calibrated decibels.
CPU temperature is not outdoor temperature.
The microphone does not determine GPS coordinates.
</p>
</div>

<div class="card">
<h2>Recent sound detections</h2>
{% if detections %}
<table>
<tr>
<th>Model</th><th>Type</th><th>Label</th>
<th>Scientific name</th><th>Confidence</th>
<th>Time</th><th>Recording</th>
</tr>
{% for d in detections %}
<tr>
<td>{{ d.model_name }}</td>
<td>{{ d.category }}</td>
<td>{{ d.species }}</td>
<td>{{ d.scientific_name if d.scientific_name is not none else "—" }}</td>
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
<p>No detections have been saved yet. Check the logs and AI settings.</p>
{% endif %}
</div>

<div class="card">
<h2>Recent recordings and acoustic measurements</h2>
{% if recordings %}
<table>
<tr>
<th>Time</th><th>Duration (s)</th><th>Size (bytes)</th>
<th>Relative level</th><th>RMS amplitude</th>
<th>Peak amplitude</th><th>Pi CPU (°C)</th>
</tr>
{% for r in recordings %}
<tr>
<td>{{ r.started_at }}</td>
<td>{{ r.duration_seconds if r.duration_seconds is not none else "—" }}</td>
<td>{{ r.size_bytes if r.size_bytes is not none else "—" }}</td>
<td>{{ r.sound_level if r.sound_level is not none else "—" }}</td>
<td>{{ r.audio_rms if r.audio_rms is not none else "—" }}</td>
<td>{{ r.audio_peak if r.audio_peak is not none else "—" }}</td>
<td>{{ r.cpu_temperature_c if r.cpu_temperature_c is not none else "—" }}</td>
</tr>
{% endfor %}
</table>
{% else %}
<p>No recordings have been saved yet.</p>
{% endif %}
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
