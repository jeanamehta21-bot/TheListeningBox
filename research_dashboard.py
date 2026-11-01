"""Research views for The Listening Box.

These pages use the existing SQLite detections and recordings. Weather is
optional and only syncs after a monitoring-site location is configured.
"""
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from flask import Blueprint, abort, redirect, render_template_string, request, url_for
from database import get_connection
from config import LATITUDE, LONGITUDE

research = Blueprint("research", __name__)

BASE = """
<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ title }} · The Listening Box</title>
<style>
:root{color-scheme:light;--bg:#f2f6f4;--panel:#fff;--ink:#193334;--muted:#6b8180;--line:#dce8e5;--teal:#187c73;--mint:#e4f2ed}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.55 system-ui,-apple-system,Segoe UI,sans-serif}
main{max-width:1200px;margin:auto;padding:28px 22px 50px}.top{display:flex;justify-content:space-between;gap:16px;align-items:center;margin-bottom:22px}
.brand{font-weight:800;letter-spacing:.08em;text-transform:uppercase}.sub,.muted{color:var(--muted);font-size:12px}
nav{display:flex;flex-wrap:wrap;gap:8px;margin:18px 0 26px}nav a,.btn{border:1px solid var(--line);border-radius:999px;padding:7px 12px;text-decoration:none;color:var(--ink);background:var(--panel);font-size:12px}
h1{font-size:30px;letter-spacing:-.04em;margin:8px 0}h2{font-size:17px;margin:0 0 12px}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:18px;margin:14px 0;overflow:auto}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px}
.metric{font-size:27px;font-weight:800}.eyebrow{font-size:10px;text-transform:uppercase;letter-spacing:.12em;color:var(--muted);font-weight:800}
table{border-collapse:collapse;width:100%;min-width:620px}th,td{text-align:left;padding:10px;border-bottom:1px solid var(--line);font-size:12px}th{color:var(--muted);text-transform:uppercase;font-size:10px}
input,select,button{font:inherit;padding:8px;border:1px solid var(--line);border-radius:8px;background:var(--panel);color:var(--ink)}
button{background:var(--teal);color:white;border:0;cursor:pointer}.bar{height:8px;background:var(--mint);border-radius:8px;overflow:hidden}.bar span{display:block;height:100%;background:var(--teal)}
.notice{background:var(--mint);padding:12px 14px;border-radius:10px;color:#315b53;font-size:12px}
@media(prefers-color-scheme:dark){:root{color-scheme:dark;--bg:#0d1d1d;--panel:#142827;--ink:#e2efeb;--muted:#9bb2ac;--line:#294744;--mint:#1b3c37}.notice{color:#c3ded3}}
</style></head><body><main>
<div class="top"><div><div class="brand">The Listening Box</div><div class="sub">Acoustic biodiversity research station</div></div><div class="sub">Local data · private by default</div></div>
<nav><a href="/">Today</a><a href="/activity">Activity</a><a href="/timeline">Timeline</a><a href="/species">Species</a><a href="/review">Review</a><a href="/insights">Insights</a><a href="/weather">Weather</a><a href="/year">Year in review</a><a href="/health">Station health</a></nav>
<h1>{{ title }}</h1><div class="sub">{{ subtitle }}</div>
{{ body|safe }}
</main></body></html>
"""

def page(title, subtitle, body, **context):
    return render_template_string(BASE, title=title, subtitle=subtitle, body=render_template_string(body, **context))

def init_research_tables():
    with get_connection() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS detection_reviews(
          detection_id INTEGER PRIMARY KEY,
          status TEXT NOT NULL CHECK(status IN ('confirmed','uncertain','false_positive')),
          notes TEXT DEFAULT '',
          reviewed_at TEXT NOT NULL,
          FOREIGN KEY(detection_id) REFERENCES detections(id)
        );
        CREATE TABLE IF NOT EXISTS weather_observations(
          observed_at TEXT PRIMARY KEY,
          temperature_c REAL, relative_humidity REAL, precipitation_mm REAL,
          wind_speed_kmh REAL, weather_code INTEGER, synced_at TEXT NOT NULL
        );
        """)

@research.before_app_request
def ensure_research_tables():
    init_research_tables()

@research.get("/activity")
def activity():
    with get_connection() as c:
        rows=[dict(r) for r in c.execute("SELECT created_at,species FROM detections ORDER BY created_at")]
    days=Counter((r["created_at"] or "")[:10] for r in rows)
    hours=Counter()
    for r in rows:
        try: hours[datetime.fromisoformat(r["created_at"]).hour]+=1
        except (ValueError,TypeError): pass
    body="""<div class="grid">{% for label,value in metrics %}<section class="panel"><div class="eyebrow">{{label}}</div><div class="metric">{{value}}</div></section>{% endfor %}</div>
    <section class="panel"><h2>Hourly activity</h2>{% for h,n in hours %}<p>{{"%02d"|format(h)}}:00 · {{n}} detections</p><div class="bar"><span style="width:{{(n/max_count*100) if max_count else 0}}%"></span></div>{% endfor %}</section>
    <section class="panel"><h2>Daily detection volume</h2><table><tr><th>Date</th><th>Candidate detections</th></tr>{% for d,n in days %}<tr><td>{{d or "Unknown date"}}</td><td>{{n}}</td></tr>{% endfor %}</table></section>"""
    return page("Activity","Patterns calculated from saved detections; repeated detections are not unique animals.",body,
        metrics=[("Total candidate detections",len(rows)),("Days with detections",len(days)),("Distinct candidate labels",len(set(r["species"] for r in rows)))],
        hours=sorted(hours.items()),max_count=max(hours.values(),default=0),days=sorted(days.items(),reverse=True))

@research.get("/timeline")
def timeline():
    selected=request.args.get("date",date.today().isoformat())
    with get_connection() as c:
        rows=[dict(r) for r in c.execute("""SELECT d.*,r.file_path FROM detections d JOIN recordings r ON r.id=d.recording_id WHERE substr(d.created_at,1,10)=? ORDER BY d.created_at""",(selected,))]
    body="""<section class="panel"><form><label>Choose day <input type="date" name="date" value="{{selected}}"></label><button>Show day</button></form></section>
    <section class="panel"><h2>{{selected}} · {{rows|length}} candidate detections</h2>{% if rows %}<table><tr><th>Time</th><th>Candidate</th><th>Scientific name</th><th>Confidence</th><th>Clip</th></tr>{% for r in rows %}<tr><td>{{r.created_at}}</td><td>{{r.species}}</td><td>{{r.scientific_name or "—"}}</td><td>{{"%.1f"|format((r.confidence or 0)*100)}}%</td><td>{{r.file_path}}</td></tr>{% endfor %}</table>{% else %}<p class="muted">No saved detections for this date.</p>{% endif %}</section>"""
    return page("Timeline","Browse a day of recorded candidate activity.",body,selected=selected,rows=rows)

@research.get("/species")
def species():
    with get_connection() as c:
        rows=[dict(r) for r in c.execute("SELECT species,scientific_name,COUNT(*) AS count,MAX(created_at) AS last_seen FROM detections GROUP BY species,scientific_name ORDER BY count DESC")]
    body="""<section class="panel"><input id="q" placeholder="Search candidate labels" oninput="document.querySelectorAll('tbody tr').forEach(r=>r.hidden=!r.innerText.toLowerCase().includes(this.value.toLowerCase()))"><table><thead><tr><th>Candidate label</th><th>Scientific name</th><th>Saved detections</th><th>Last seen</th></tr></thead><tbody>{% for r in rows %}<tr><td>{{r.species}}</td><td>{{r.scientific_name or "—"}}</td><td>{{r.count}}</td><td>{{r.last_seen}}</td></tr>{% endfor %}</tbody></table></section><p class="muted">These are model labels, not a verified species checklist.</p>"""
    return page("Species","A searchable index of candidate labels in your database.",body,rows=rows)

@research.route("/review",methods=["GET","POST"])
def review():
    if request.method=="POST":
        did=request.form.get("detection_id",type=int); status=request.form.get("status")
        if not did or status not in ("confirmed","uncertain","false_positive"): abort(400)
        with get_connection() as c:
            c.execute("""INSERT INTO detection_reviews(detection_id,status,notes,reviewed_at) VALUES(?,?,?,?) ON CONFLICT(detection_id) DO UPDATE SET status=excluded.status,notes=excluded.notes,reviewed_at=excluded.reviewed_at""",(did,status,request.form.get("notes","")[:1000],datetime.now().isoformat(timespec="seconds")))
        return redirect(url_for("research.review"))
    with get_connection() as c:
        rows=[dict(r) for r in c.execute("""SELECT d.*,r.file_path,rv.status AS review_status,rv.notes AS review_notes FROM detections d JOIN recordings r ON r.id=d.recording_id LEFT JOIN detection_reviews rv ON rv.detection_id=d.id WHERE rv.detection_id IS NULL OR rv.status='uncertain' ORDER BY d.confidence ASC,d.created_at DESC LIMIT 100""")]
    body="""<section class="notice">Review is manual. A model score is not proof. Mark a candidate only after listening and checking the evidence.</section>{% for r in rows %}<section class="panel"><div class="eyebrow">{{r.created_at}} · {{r.model_name}}</div><h2>{{r.species}} <span class="muted">{{r.scientific_name or ""}}</span></h2><p>Confidence: {{ "%.1f"|format((r.confidence or 0)*100) }}% · {{r.file_path}}</p><form method="post"><input type="hidden" name="detection_id" value="{{r.id}}"><select name="status"><option value="confirmed">Confirmed</option><option value="uncertain" selected>Still uncertain</option><option value="false_positive">False positive</option></select> <input name="notes" placeholder="Review notes" value="{{r.review_notes or ''}}"><button>Save review</button></form></section>{% else %}<section class="panel">No unreviewed or uncertain detections in the queue.</section>{% endfor %}"""
    return page("Review queue","Review uncertain model candidates and record your own verdict.",body,rows=rows)

@research.get("/insights")
def insights():
    with get_connection() as c:
        rows=[dict(r) for r in c.execute("SELECT species,created_at FROM detections WHERE id NOT IN (SELECT detection_id FROM detection_reviews WHERE status='false_positive') ORDER BY created_at")]
    by_species=defaultdict(list)
    for r in rows: by_species[r["species"]].append(r["created_at"])
    dawn=[]; nocturnal=[]
    for name,times in by_species.items():
        hours=[]
        for t in times:
            try: hours.append(datetime.fromisoformat(t).hour)
            except (ValueError,TypeError): pass
        if any(4<=h<7 for h in hours): dawn.append(name)
        if any(h>=22 or h<5 for h in hours): nocturnal.append(name)
    body="""<div class="grid"><section class="panel"><div class="eyebrow">Dawn-active candidate labels</div><div class="metric">{{dawn|length}}</div>{% for x in dawn %}<p>{{x}}</p>{% else %}<p class="muted">Not enough evidence yet.</p>{% endfor %}</section><section class="panel"><div class="eyebrow">Night-active candidate labels</div><div class="metric">{{night|length}}</div>{% for x in night %}<p>{{x}}</p>{% else %}<p class="muted">Not enough evidence yet.</p>{% endfor %}</section></div><p class="notice">These are descriptive time-of-day patterns in your recordings, not proof of dawn-chorus participation, migration, absence, rarity, or ecological health. More weeks of consistent recordings improve comparisons.</p>"""
    return page("Insights","Early descriptive patterns; avoid ecological conclusions from small samples.",body,dawn=sorted(dawn),night=sorted(nocturnal))

@research.get("/weather")
def weather():
    with get_connection() as c:
        rows=[dict(r) for r in c.execute("SELECT * FROM weather_observations ORDER BY observed_at DESC LIMIT 168")]
    body="""<section class="panel"><div class="eyebrow">Weather source</div><h2>Open-Meteo · hourly regional estimates</h2>{% if configured %}<p>Monitoring-site coordinates are configured. Latest saved weather: {{rows[0].observed_at if rows else "not synced yet"}}.</p>{% else %}<p>Weather is waiting for a monitoring-site location. Add latitude and longitude to config.py. Use the actual Listening Box site, not your home address unless that is where it is installed.</p>{% endif %}<p class="muted">Weather is regional model data, not a sensor reading at the microphone. The sync script stores hourly temperature, humidity, precipitation, wind and weather code. Run <code>python weather_sync.py</code> on a computer with internet access.</p></section>
    <section class="panel"><h2>Recent hourly conditions</h2>{% if rows %}<table><tr><th>Time</th><th>Temp °C</th><th>Humidity</th><th>Rain mm</th><th>Wind km/h</th><th>Code</th></tr>{% for r in rows %}<tr><td>{{r.observed_at}}</td><td>{{r.temperature_c}}</td><td>{{r.relative_humidity}}</td><td>{{r.precipitation_mm}}</td><td>{{r.wind_speed_kmh}}</td><td>{{r.weather_code}}</td></tr>{% endfor %}</table>{% else %}<p class="muted">No weather history has been synced yet.</p>{% endif %}</section>"""
    return page("Weather","Weather-aware analysis starts only after the monitoring site is configured.",body,configured=LATITUDE is not None and LONGITUDE is not None,rows=rows)

@research.get("/year")
def year():
    y=request.args.get("year",date.today().year,type=int)
    with get_connection() as c:
        rows=[dict(r) for r in c.execute("SELECT species,created_at FROM detections WHERE substr(created_at,1,4)=?",(str(y),))]
    months=Counter((r["created_at"] or "")[5:7] for r in rows)
    leaders=Counter(r["species"] for r in rows)
    body="""<section class="panel"><form><label>Year <input name="year" type="number" min="2000" max="2100" value="{{year}}"></label><button>View</button></form><div class="grid"><div><div class="eyebrow">Candidate detections</div><div class="metric">{{rows|length}}</div></div><div><div class="eyebrow">Distinct labels</div><div class="metric">{{leaders|length}}</div></div></div></section><section class="panel"><h2>Monthly activity</h2>{% for m in range(1,13) %}<p>{{"%02d"|format(m)}} · {{months.get("%02d"|format(m),0)}} detections</p><div class="bar"><span style="width:{{(months.get("%02d"|format(m),0)/max_month*100) if max_month else 0}}%"></span></div>{% endfor %}</section><section class="panel"><h2>Most frequent candidate labels</h2>{% for name,n in leaders.most_common(10) %}<p>{{name}} · {{n}}</p>{% else %}<p>No data for this year yet.</p>{% endfor %}</section>"""
    return page("Year in review","A summary of saved candidate detections, not a verified bird census.",body,year=y,rows=rows,leaders=leaders,months=months,max_month=max(months.values(),default=0))

@research.get("/health")
def health():
    with get_connection() as c:
        recordings=c.execute("SELECT COUNT(*) FROM recordings").fetchone()[0]
        detections=c.execute("SELECT COUNT(*) FROM detections").fetchone()[0]
        latest=c.execute("SELECT MAX(started_at) FROM recordings").fetchone()[0]
        reviews=c.execute("SELECT COUNT(*) FROM detection_reviews").fetchone()[0]
        weather=c.execute("SELECT COUNT(*) FROM weather_observations").fetchone()[0]
    body="""<div class="grid">{% for label,value in metrics %}<section class="panel"><div class="eyebrow">{{label}}</div><div class="metric">{{value}}</div></section>{% endfor %}</div><section class="panel"><h2>Interpretation</h2><p>This page checks database records, not the live microphone, network, disk, or scheduler service. Use the Pi's service logs for operational diagnostics.</p></section>"""
    return page("Station health","Database-level status only; no live hardware claims.",body,metrics=[("Saved recordings",recordings),("Saved candidate detections",detections),("Reviewed detections",reviews),("Weather hours stored",weather),("Latest recording",latest or "—")])
