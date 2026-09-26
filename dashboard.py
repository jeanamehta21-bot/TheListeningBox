from flask import Flask, jsonify, render_template_string

from config import HOST, PORT
from database import initialize_database, recent_detections, recent_recordings

app = Flask(__name__)

HTML = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Listening Box</title>
<style>
body { font-family: Arial, sans-serif; max-width: 1100px; margin: auto;
       padding: 24px; background: #f4f4f4; color: #222; }
.card { background: white; padding: 20px; margin-bottom: 20px;
        border-radius: 12px; }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 9px; text-align: left; border-bottom: 1px solid #ddd; }
</style>
</head>
<body>
<div class="card">
<h1>Listening Box</h1>
<p>Local biodiversity sound-monitoring dashboard.</p>
</div>

<div class="card">
<h2>Recent detections</h2>
{% if detections %}
<table>
<tr><th>Species</th><th>Confidence</th><th>Time</th><th>Recording</th></tr>
{% for d in detections %}
<tr>
<td>{{ d.species }}</td>
<td>{{ "%.1f"|format(d.confidence * 100) }}%</td>
<td>{{ d.created_at }}</td>
<td>{{ d.file_path }}</td>
</tr>
{% endfor %}
</table>
{% else %}
<p>No AI detections yet.</p>
{% endif %}
</div>

<div class="card">
<h2>Recent recordings</h2>
<table>
<tr><th>Time</th><th>Duration</th><th>Size</th><th>Pi CPU temperature</th></tr>
{% for r in recordings %}
<tr>
<td>{{ r.started_at }}</td>
<td>{{ "%.1f"|format(r.duration_seconds) }} sec</td>
<td>{{ r.size_bytes }} bytes</td>
<td>
{% if r.cpu_temperature_c is not none %}
{{ "%.1f"|format(r.cpu_temperature_c) }} °C
{% else %}—{% endif %}
</td>
</tr>
{% endfor %}
</table>
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
