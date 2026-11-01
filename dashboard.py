from collections import Counter
from datetime import datetime

from flask import Flask, jsonify, render_template_string

from config import HOST, PORT
from database import (
    initialize_database,
    recent_detections,
    recent_recordings,
)

app = Flask(__name__)

from research_dashboard import research
app.register_blueprint(research)

HTML = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#102b2b">
<title>The Listening Box</title>
<style>
:root {
  color-scheme: light;
  --ink: #193334;
  --muted: #6b8180;
  --line: #dce8e5;
  --paper: #f3f7f5;
  --card: #ffffff;
  --teal: #187c73;
  --teal-dark: #105c57;
  --mint: #e4f2ed;
  --gold: #e8b85c;
  --shadow: 0 10px 30px rgba(22, 58, 54, .06);
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--paper);
  color: var(--ink);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  line-height: 1.5;
}
a { color: inherit; }
.shell { max-width: 1440px; margin: 0 auto; padding: 28px clamp(16px, 3vw, 42px) 48px; }
.topbar {
  display: flex; justify-content: space-between; align-items: center;
  gap: 20px; margin-bottom: 26px;
}
.brand { display: flex; align-items: center; gap: 13px; }
.mark {
  width: 44px; height: 44px; display: grid; place-items: center;
  border-radius: 14px; color: white; background: var(--teal);
  font-size: 21px; box-shadow: 0 7px 16px rgba(24,124,115,.2);
}
.brand-name { font-size: 15px; font-weight: 800; letter-spacing: .11em; text-transform: uppercase; }
.brand-sub { color: var(--muted); font-size: 12px; margin-top: 1px; }
.status {
  display: inline-flex; align-items: center; gap: 8px; padding: 8px 12px;
  border: 1px solid var(--line); border-radius: 999px; background: var(--card);
  color: var(--muted); font-size: 12px; font-weight: 650;
}
.dot { width: 8px; height: 8px; border-radius: 50%; background: #75a99a; }
.hero {
  display: grid; grid-template-columns: minmax(0, 1.5fr) minmax(240px, .8fr);
  gap: 22px; margin-bottom: 22px;
}
.hero-main {
  padding: clamp(24px, 4vw, 42px); border-radius: 22px;
  color: #f3fbf7; background: linear-gradient(125deg, #123b39, #176d64);
  box-shadow: var(--shadow); position: relative; overflow: hidden;
}
.hero-main:after {
  content: ""; position: absolute; width: 260px; height: 260px; right: -75px; top: -115px;
  border: 1px solid rgba(255,255,255,.13); border-radius: 50%;
  box-shadow: 0 0 0 28px rgba(255,255,255,.035), 0 0 0 58px rgba(255,255,255,.025);
}
.eyebrow { text-transform: uppercase; letter-spacing: .15em; font-size: 10px; font-weight: 800; opacity: .72; }
h1 { margin: 9px 0 8px; font-size: clamp(29px, 4vw, 43px); letter-spacing: -.04em; line-height: 1.08; }
.hero-main p { max-width: 620px; margin: 0; color: #d0e5df; font-size: 14px; }
.hero-side {
  background: var(--card); border: 1px solid var(--line); border-radius: 22px;
  padding: 23px; box-shadow: var(--shadow); display: flex; flex-direction: column; justify-content: space-between;
}
.side-label { color: var(--muted); font-size: 11px; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; }
.side-number { font-size: 38px; font-weight: 780; letter-spacing: -.05em; margin: 7px 0 2px; }
.side-note { color: var(--muted); font-size: 12px; }
.nav { display: flex; gap: 8px; flex-wrap: wrap; margin: 0 0 22px; }
.nav a {
  text-decoration: none; padding: 8px 13px; border: 1px solid var(--line);
  border-radius: 999px; background: rgba(255,255,255,.65); color: var(--muted);
  font-size: 12px; font-weight: 700;
}
.nav a:first-child { background: var(--mint); color: var(--teal-dark); border-color: #c6e1d7; }
.section-head { display: flex; justify-content: space-between; align-items: end; gap: 12px; margin: 28px 0 13px; }
.section-head h2 { margin: 0; font-size: 18px; letter-spacing: -.02em; }
.section-head p { margin: 3px 0 0; color: var(--muted); font-size: 12px; }
.kpis { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 13px; }
.card {
  min-width: 0; background: var(--card); border: 1px solid var(--line);
  border-radius: 17px; padding: 18px; box-shadow: var(--shadow);
}
.kpi-label { color: var(--muted); font-size: 11px; font-weight: 750; letter-spacing: .08em; text-transform: uppercase; }
.kpi-value { font-size: 28px; font-weight: 800; letter-spacing: -.04em; margin-top: 7px; }
.kpi-foot { color: var(--muted); font-size: 11px; margin-top: 2px; }
.columns { display: grid; grid-template-columns: minmax(0, 1.15fr) minmax(280px, .85fr); gap: 16px; }
.chart { display: flex; align-items: end; gap: 8px; height: 145px; padding: 15px 2px 0; }
.bar-wrap { flex: 1; min-width: 0; height: 100%; display: flex; flex-direction: column; justify-content: end; align-items: center; gap: 7px; }
.bar {
  width: min(100%, 34px); min-height: 3px; border-radius: 7px 7px 3px 3px;
  background: linear-gradient(180deg, #5db5a0, #187c73);
}
.bar-label { color: var(--muted); font-size: 10px; }
.species-list { display: grid; gap: 13px; margin-top: 13px; }
.species-row { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 8px; font-size: 12px; }
.species-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-weight: 650; }
.species-count { color: var(--muted); font-variant-numeric: tabular-nums; }
.track { grid-column: 1 / -1; height: 5px; border-radius: 99px; background: #edf3f0; overflow: hidden; }
.fill { height: 100%; border-radius: inherit; background: #65aa98; }
.table-card { padding: 0; overflow: hidden; }
.table-top { padding: 17px 18px; display: flex; justify-content: space-between; gap: 12px; align-items: center; }
.table-top h2 { font-size: 16px; margin: 0; }
.search {
  width: min(220px, 48%); border: 1px solid var(--line); border-radius: 9px;
  padding: 8px 10px; font: inherit; font-size: 12px; background: #fbfdfc; color: var(--ink);
}
.table-scroll { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; min-width: 690px; }
th, td { text-align: left; padding: 12px 16px; border-top: 1px solid #edf2f0; font-size: 12px; white-space: nowrap; }
th { color: var(--muted); background: #f9fbfa; font-size: 10px; text-transform: uppercase; letter-spacing: .08em; }
td strong { font-weight: 700; }
.pill {
  display: inline-block; border-radius: 999px; padding: 4px 8px;
  background: var(--mint); color: var(--teal-dark); font-size: 10px; font-weight: 800;
}
.muted { color: var(--muted); }
.empty { padding: 24px 18px; color: var(--muted); font-size: 13px; }
.note {
  margin-top: 18px; padding: 14px 16px; border-radius: 13px;
  background: #edf4f1; color: #58716d; font-size: 11px;
}
.footer { color: #8a9b98; font-size: 11px; text-align: center; padding-top: 25px; }
@media (max-width: 850px) {
  .hero, .columns { grid-template-columns: 1fr; }
  .kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 480px) {
  .shell { padding: 18px 13px 32px; }
  .topbar { align-items: flex-start; }
  .status { font-size: 10px; }
  .kpis { gap: 9px; }
  .card { padding: 14px; }
  .kpi-value { font-size: 24px; }
  .table-top { align-items: flex-start; flex-direction: column; }
  .search { width: 100%; }
}
@media (prefers-color-scheme: dark) {
  :root {
    color-scheme: dark; --ink: #e2efeb; --muted: #9bb2ac; --line: #294744;
    --paper: #0d1d1d; --card: #142827; --mint: #1b3c37; --shadow: 0 10px 30px rgba(0,0,0,.15);
  }
  .hero-main { background: linear-gradient(125deg, #102d2c, #14574f); }
  .nav a { background: #142827; }
  .nav a:first-child { background: #1b3c37; color: #b6e0d1; border-color: #315c53; }
  .search { background: #102221; color: var(--ink); }
  th { background: #192f2d; }
  .track { background: #263d39; }
  .note { background: #182f2c; color: #a9c4bb; }
}
</style>
</head>
<body>
<main class="shell">
  <header class="topbar">
    <div class="brand">
      <div class="mark" aria-hidden="true">◖</div>
      <div>
        <div class="brand-name">The Listening Box</div>
        <div class="brand-sub">Acoustic biodiversity monitor</div>
      </div>
    </div>
    <div class="status"><span class="dot"></span> Local monitoring station</div>
  </header>

  <section class="hero">
    <div class="hero-main">
      <div class="eyebrow">Field station · Soundscape overview</div>
      <h1>Listen closer.<br>Understand more.</h1>
      <p>Explore the sounds recorded around your monitoring site, review AI-generated candidates, and follow changes in local acoustic activity.</p>
    </div>
    <div class="hero-side">
      <div>
        <div class="side-label">Latest recording</div>
        <div class="side-number">{{ latest_recording }}</div>
        <div class="side-note">{{ latest_recording_note }}</div>
      </div>
      <div class="side-note" style="margin-top:18px">Recording history shown below is read from the existing Listening Box database.</div>
    </div>
  </section>

  <nav class="nav" aria-label="Dashboard sections">
    <a href="#overview">Overview</a>
    <a href="#activity">Activity</a>
    <a href="#detections">Detections</a>
    <a href="#recordings">Recordings</a>
  </nav>

  <section id="overview">
    <div class="section-head">
      <div><h2>Station overview</h2><p>Recent saved activity · not lifetime totals</p></div>
    </div>
    <div class="kpis">
      <div class="card"><div class="kpi-label">Detections shown</div><div class="kpi-value">{{ detections|length }}</div><div class="kpi-foot">Latest 100 database entries</div></div>
      <div class="card"><div class="kpi-label">Recordings shown</div><div class="kpi-value">{{ recordings|length }}</div><div class="kpi-foot">Latest 30 saved recordings</div></div>
      <div class="card"><div class="kpi-label">Candidate labels</div><div class="kpi-value">{{ species_count }}</div><div class="kpi-foot">Distinct labels in recent detections</div></div>
      <div class="card"><div class="kpi-label">Average confidence</div><div class="kpi-value">{{ average_confidence }}</div><div class="kpi-foot">Recent model scores, when available</div></div>
    </div>
  </section>

  <section id="activity">
    <div class="section-head"><div><h2>Activity patterns</h2><p>Distribution of the latest saved detections by hour</p></div></div>
    <div class="columns">
      <div class="card">
        <div class="kpi-label">Detections by hour</div>
        {% if hourly_values %}
        <div class="chart" role="img" aria-label="Bar chart showing recent detections by hour">
          {% for hour, count, height in hourly_values %}
          <div class="bar-wrap" title="{{ hour }}:00 — {{ count }} detections">
            <div class="bar" style="height: {{ height }}%"></div>
            <div class="bar-label">{{ hour }}</div>
          </div>
          {% endfor %}
        </div>
        <div class="side-note">Hours use the timestamps saved by the station. The chart is descriptive, not a measure of species abundance.</div>
        {% else %}
        <div class="empty">Hourly activity will appear after detections are saved.</div>
        {% endif %}
      </div>
      <div class="card">
        <div class="kpi-label">Most frequent recent labels</div>
        {% if top_species %}
        <div class="species-list">
          {% for name, count, width in top_species %}
          <div class="species-row">
            <div class="species-name">{{ name }}</div><div class="species-count">{{ count }}</div>
            <div class="track"><div class="fill" style="width: {{ width }}%"></div></div>
          </div>
          {% endfor %}
        </div>
        {% else %}
        <div class="empty">No candidate labels yet.</div>
        {% endif %}
      </div>
    </div>
  </section>

  <section id="detections">
    <div class="section-head"><div><h2>Recent sound detections</h2><p>AI predictions are candidates, not confirmed observations.</p></div></div>
    <div class="card table-card">
      <div class="table-top"><h2>Detection log</h2><input class="search" id="detectionSearch" type="search" placeholder="Filter detections…" aria-label="Filter detections"></div>
      {% if detections %}
      <div class="table-scroll">
        <table id="detectionTable">
          <thead><tr><th>Model</th><th>Type</th><th>Candidate label</th><th>Scientific name</th><th>Confidence</th><th>Time</th><th>Recording</th></tr></thead>
          <tbody>
          {% for d in detections %}
          <tr>
            <td>{{ d.model_name }}</td><td><span class="pill">{{ d.category }}</span></td>
            <td><strong>{{ d.species }}</strong></td>
            <td class="muted">{{ d.scientific_name if d.scientific_name else "—" }}</td>
            <td>{% if d.confidence is not none %}{{ "%.1f"|format(d.confidence * 100) }}%{% else %}—{% endif %}</td>
            <td>{{ d.created_at }}</td><td class="muted">{{ d.file_path }}</td>
          </tr>
          {% endfor %}
          </tbody>
        </table>
      </div>
      {% else %}
      <div class="empty">No detections have been saved yet. Check the analysis settings and logs.</div>
      {% endif %}
    </div>
  </section>

  <section id="recordings">
    <div class="section-head"><div><h2>Recording archive</h2><p>Audio measurements saved with each recording</p></div></div>
    <div class="card table-card">
      {% if recordings %}
      <div class="table-scroll">
        <table>
          <thead><tr><th>Started</th><th>Duration (s)</th><th>Size (bytes)</th><th>Relative level</th><th>RMS amplitude</th><th>Peak amplitude</th><th>Pi CPU (°C)</th></tr></thead>
          <tbody>
          {% for r in recordings %}
          <tr>
            <td>{{ r.started_at }}</td>
            <td>{{ r.duration_seconds if r.duration_seconds is not none else "—" }}</td>
            <td>{{ r.size_bytes if r.size_bytes is not none else "—" }}</td>
            <td>{{ r.sound_level if r.sound_level else "—" }}</td>
            <td>{{ r.audio_rms if r.audio_rms is not none else "—" }}</td>
            <td>{{ r.audio_peak if r.audio_peak is not none else "—" }}</td>
            <td>{{ r.cpu_temperature_c if r.cpu_temperature_c is not none else "—" }}</td>
          </tr>
          {% endfor %}
          </tbody>
        </table>
      </div>
      {% else %}
      <div class="empty">No recordings have been saved yet.</div>
      {% endif %}
    </div>
  </section>

  <div class="note">
    <strong>Reading the data carefully:</strong> confidence is a model score, not a verified probability. RMS and peak are digital audio measurements, not calibrated decibels. CPU temperature is the Raspberry Pi's temperature, not outdoor air temperature. The microphone does not determine GPS coordinates.
  </div>
  <footer class="footer">The Listening Box · Local-first acoustic biodiversity monitoring</footer>
</main>
<script>
(() => {
  const search = document.getElementById("detectionSearch");
  const table = document.getElementById("detectionTable");
  if (!search || !table) return;
  search.addEventListener("input", () => {
    const term = search.value.toLowerCase().trim();
    table.querySelectorAll("tbody tr").forEach(row => {
      row.hidden = !row.textContent.toLowerCase().includes(term);
    });
  });
})();
</script>
</body>
</html>
"""


def _dashboard_context():
    detections = recent_detections()
    recordings = recent_recordings()

    labels = Counter(
        (d.get("species") or "Unknown") for d in detections
    )
    top_count = max(labels.values(), default=1)
    top_species = [
        (name, count, round(count / top_count * 100))
        for name, count in labels.most_common(6)
    ]

    hourly = Counter()
    for detection in detections:
        timestamp = detection.get("created_at") or ""
        try:
            hour = datetime.fromisoformat(timestamp).hour
        except (TypeError, ValueError):
            continue
        hourly[hour] += 1

    max_hourly = max(hourly.values(), default=1)
    hourly_values = [
        (hour, hourly[hour], max(4, round(hourly[hour] / max_hourly * 100)))
        for hour in range(24)
    ] if hourly else []

    confidences = [
        float(d["confidence"])
        for d in detections
        if d.get("confidence") is not None
    ]
    average_confidence = (
        f"{sum(confidences) / len(confidences) * 100:.1f}%"
        if confidences else "—"
    )

    latest = recordings[0].get("started_at") if recordings else None
    if latest:
        latest_recording = latest[11:16] if len(latest) >= 16 else latest
        latest_recording_note = latest
    else:
        latest_recording = "—"
        latest_recording_note = "No saved recordings yet"

    return {
        "detections": detections,
        "recordings": recordings,
        "species_count": len(labels),
        "average_confidence": average_confidence,
        "top_species": top_species,
        "hourly_values": hourly_values,
        "latest_recording": latest_recording,
        "latest_recording_note": latest_recording_note,
    }


@app.route("/")
def index():
    return render_template_string(HTML, **_dashboard_context())


@app.route("/api/detections")
def api_detections():
    return jsonify(recent_detections())


@app.route("/api/recordings")
def api_recordings():
    return jsonify(recent_recordings())


if __name__ == "__main__":
    initialize_database()
    app.run(host=HOST, port=PORT, debug=False)
