"""Export privacy-conscious aggregate data and a printable PDF for GitHub Pages.

Run on the computer that has the Listening Box SQLite database:
    python publish_static.py
"""
import json
import math
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from config import DATABASE_PATH

ROOT = Path(__file__).resolve().parent
PUBLIC_DATA = ROOT / "docs" / "data" / "dashboard.json"
PDF_PATH = ROOT / "docs" / "reports" / "listening-box-report.pdf"


def safe_float(value):
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


# Conservative allowlist for bird species recorded in Connecticut.
# Scientific names are used because common-name spellings can vary.
# Rare and migratory Connecticut birds are retained when they are on the
# state checklist; clearly non-local taxa and non-bird classifier labels are not.
CONNECTICUT_BIRD_SCIENTIFIC_NAMES = {
    "Sitta carolinensis",       # White-breasted Nuthatch
    "Melanerpes carolinus",     # Red-bellied Woodpecker
    "Cyanocitta cristata",      # Blue Jay
    "Zonotrichia albicollis",   # White-throated Sparrow
    "Spinus tristis",           # American Goldfinch
    "Contopus virens",          # Eastern Wood-Pewee
    "Loxia curvirostra",        # Red Crossbill
    "Setophaga coronata",       # Yellow-rumped Warbler
    "Bubo virginianus",         # Great Horned Owl
    "Chordeiles minor",         # Common Nighthawk
    "Falco peregrinus",         # Peregrine Falcon
    "Aegolius acadicus",        # Northern Saw-whet Owl
    "Columba livia",            # Rock Pigeon / Rock Dove
    "Anas platyrhynchos",       # Mallard
    "Dumetella carolinensis",   # Gray Catbird
    "Polioptila caerulea",      # Blue-gray Gnatcatcher
    "Passer montanus",          # Eurasian Tree Sparrow
    "Passer domesticus",        # House Sparrow
    "Passerculus sandwichensis",# Savannah Sparrow
    "Certhia americana",        # Brown Creeper
    "Calidris alpina",          # Dunlin
    "Turdus migratorius",       # American Robin
    "Cardinalis cardinalis",    # Northern Cardinal
    "Poecile atricapillus",     # Black-capped Chickadee
    "Baeolophus bicolor",       # Tufted Titmouse
    "Dryobates pubescens",      # Downy Woodpecker
    "Agelaius phoeniceus",      # Red-winged Blackbird
    "Melospiza melodia",        # Song Sparrow
    "Junco hyemalis",           # Dark-eyed Junco
    "Quiscalus quiscula",       # Common Grackle
    "Melanerpes erythrocephalus",# Red-headed Woodpecker
    "Icterus galbula",          # Baltimore Oriole
    "Geothlypis trichas",       # Common Yellowthroat
    "Corvus brachyrhynchos",    # American Crow
    "Sitta canadensis",         # Red-breasted Nuthatch
    "Sayornis phoebe",          # Eastern Phoebe
    "Spizella passerina",       # Chipping Sparrow
    "Zenaida macroura",         # Mourning Dove
    "Buteo jamaicensis",        # Red-tailed Hawk
    "Strix varia",              # Barred Owl
    "Cyanocitta cristata",      # Blue Jay
}

def is_plausible_connecticut_bird(row):
    model = (row["model_name"] or "").strip().casefold()
    category = (row["category"] or "").strip().casefold()
    scientific_name = (row["scientific_name"] or "").strip()
    return (
        "birdnet" in model
        and category == "bird"
        and scientific_name in CONNECTICUT_BIRD_SCIENTIFIC_NAMES
    )


def build_payload():
    if not DATABASE_PATH.exists():
        raise SystemExit(
            f"Database not found: {DATABASE_PATH}\n"
            "Put your existing listeningbox.db in the project's data/ folder."
        )
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        recordings = conn.execute(
            "SELECT id, started_at, duration_seconds FROM recordings"
        ).fetchall()
        detections = conn.execute(
            """SELECT d.species, d.confidence, d.created_at, d.model_name,
                      d.category, d.scientific_name
               FROM detections d ORDER BY d.created_at"""
        ).fetchall()
    finally:
        conn.close()

    species_counts = Counter()
    species_scientific = {}
    hours, days, models, categories = Counter(), Counter(), Counter(), Counter()
    confidences = []
    accepted_detections = [row for row in detections if is_plausible_connecticut_bird(row)]
    filtered_out_detections = len(detections) - len(accepted_detections)
    for row in accepted_detections:
        label = (row["species"] or "Unknown").strip() or "Unknown"
        species_counts[label] += 1
        if row["scientific_name"]:
            species_scientific[label] = row["scientific_name"]
        models[(row["model_name"] or "Unknown").strip()] += 1
        categories[(row["category"] or "Unknown").strip()] += 1
        confidence = safe_float(row["confidence"])
        if confidence is not None:
            confidences.append(confidence)
        try:
            parsed = datetime.fromisoformat(row["created_at"] or "")
            hours[parsed.hour] += 1
            days[parsed.date().isoformat()] += 1
        except (TypeError, ValueError):
            pass

    total = sum(species_counts.values())
    proportions = [count / total for count in species_counts.values()] if total else []
    shannon = -sum(p * math.log(p) for p in proportions if p > 0) if total else None
    simpson = 1 - sum(p * p for p in proportions) if total else None
    duration = sum(safe_float(row["duration_seconds"]) or 0 for row in recordings)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "summary": {
            "recordings": len(recordings),
            "detections": len(accepted_detections),
            "candidate_labels": len(species_counts),
            "filtered_out_detections": filtered_out_detections,
            "average_confidence": sum(confidences) / len(confidences) if confidences else None,
            "total_recording_hours": duration / 3600,
            "shannon_diversity": shannon,
            "simpson_diversity": simpson,
        },
        "species": [
            {"label": label, "scientific_name": species_scientific.get(label), "detections": count}
            for label, count in species_counts.most_common()
        ],
        "hourly": [{"hour": hour, "detections": hours.get(hour, 0)} for hour in range(24)],
        "daily": [{"date": day, "detections": count} for day, count in sorted(days.items())],
        "models": [{"model": name, "detections": count} for name, count in models.most_common()],
        "categories": [{"category": name, "detections": count} for name, count in categories.most_common()],
        "interpretation_notes": [
            "BirdNET outputs are candidate detections, not independently verified observations.",
            "Repeated detections do not represent unique individual animals.",
            "Shannon and Simpson values describe candidate-label detection frequencies, not a complete ecological census.",
            "Detection counts depend on recording effort, microphone placement, weather, model settings and confidence thresholds.",
            "Model confidence is a score, not a guarantee that a species was present.",
        ],
    }


def write_pdf(payload):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

    PDF_PATH.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(PDF_PATH), pagesize=letter,
        rightMargin=.62 * inch, leftMargin=.62 * inch,
        topMargin=.62 * inch, bottomMargin=.62 * inch,
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="ReportSubtitle", parent=styles["Normal"],
        alignment=1, textColor=colors.HexColor("#55736d"), spaceAfter=18,
    ))
    story = [
        Paragraph("THE LISTENING BOX", styles["Title"]),
        Paragraph("Acoustic Biodiversity — Data Analysis Report", styles["ReportSubtitle"]),
        Paragraph("1. Dataset overview", styles["Heading2"]),
    ]
    s = payload["summary"]
    avg = s["average_confidence"]
    metrics = [
        ["Measure", "Result"],
        ["Recordings", str(s["recordings"])],
        ["Candidate detections", str(s["detections"])],
        ["Distinct candidate labels", str(s["candidate_labels"])],
        ["Total recording duration", f'{s["total_recording_hours"]:.2f} hours'],
        ["Mean model confidence", f"{avg:.1%}" if avg is not None else "Not available"],
        ["Shannon index (candidate detections)", f'{s["shannon_diversity"]:.3f}' if s["shannon_diversity"] is not None else "Not available"],
        ["Simpson index (1 - D)", f'{s["simpson_diversity"]:.3f}' if s["simpson_diversity"] is not None else "Not available"],
    ]
    def styled_table(rows, widths):
        table = Table(rows, colWidths=widths, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#176d64")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), .35, colors.HexColor("#dce8e5")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f7f5")]),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        return table

    story += [styled_table(metrics, [3.3 * inch, 3 * inch]), Spacer(1, 16),
              Paragraph("2. Most frequent candidate labels", styles["Heading2"])]
    species_rows = [["Candidate label", "Scientific name", "Detections"]]
    species_rows += [[x["label"][:48], (x["scientific_name"] or "—")[:42], str(x["detections"])]
                     for x in payload["species"][:30]]
    if len(species_rows) == 1:
        species_rows.append(["No detections", "—", "0"])
    story += [styled_table(species_rows, [2.5 * inch, 2.8 * inch, 1 * inch]),
              Spacer(1, 16), Paragraph("3. Hourly activity", styles["Heading2"])]
    hourly_rows = [["Hour", "Candidate detections"]]
    hourly_rows += [[f'{x["hour"]:02d}:00', str(x["detections"])]
                    for x in payload["hourly"] if x["detections"]]
    if len(hourly_rows) == 1:
        hourly_rows.append(["No timestamped detections", "0"])
    story += [styled_table(hourly_rows, [2 * inch, 2.5 * inch]), PageBreak(),
              Paragraph("4. Daily activity", styles["Heading2"])]
    daily_rows = [["Date", "Candidate detections"]]
    daily_rows += [[x["date"], str(x["detections"])] for x in payload["daily"]]
    if len(daily_rows) == 1:
        daily_rows.append(["No dated detections", "0"])
    story += [styled_table(daily_rows, [2.5 * inch, 2.5 * inch]), Spacer(1, 16),
              Paragraph("5. Methods and limitations", styles["Heading2"]),
              Paragraph(
                  "This report summarizes the Listening Box SQLite recordings and detections tables. "
                  "Counts are model-generated candidate detections. Diversity indices describe the "
                  "relative frequency of candidate labels; they are not a verified estimate of animal "
                  "abundance or a complete ecological census.", styles["BodyText"]
              )]
    for note in payload["interpretation_notes"]:
        story += [Spacer(1, 5), Paragraph("• " + note, styles["BodyText"])]
    story += [Spacer(1, 12), Paragraph(
        "Generated from the local Listening Box database: " + payload["generated_at"],
        styles["Italic"],
    )]
    doc.build(story)


def main():
    payload = build_payload()
    PUBLIC_DATA.parent.mkdir(parents=True, exist_ok=True)
    PUBLIC_DATA.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_pdf(payload)
    print(f"Public dashboard data: {PUBLIC_DATA}")
    print(f"PDF report: {PDF_PATH}")
    print("Review both generated files before committing them to the public repository.")


if __name__ == "__main__":
    main()
