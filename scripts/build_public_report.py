"""Build the public Listening Box PDF from the exact dashboard JSON used by Pages."""
import json
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "data" / "dashboard.json"
OUTPUT = ROOT / "docs" / "reports" / "listening-box-report.pdf"

def build():
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    summary = data.get("summary", {})
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Sub", parent=styles["Normal"], alignment=1,
                              textColor=colors.HexColor("#55736d"), spaceAfter=18))
    doc = SimpleDocTemplate(str(OUTPUT), pagesize=letter, rightMargin=.6*inch,
                            leftMargin=.6*inch, topMargin=.6*inch, bottomMargin=.6*inch)
    story = [Paragraph("THE LISTENING BOX", styles["Title"]),
             Paragraph("Acoustic Biodiversity — Public Data Report", styles["Sub"]),
             Paragraph("1. Dataset overview", styles["Heading2"])]

    def table(rows, widths):
        t = Table(rows, colWidths=widths, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#176d64")),
            ("TEXTCOLOR",(0,0),(-1,0),colors.white),
            ("GRID",(0,0),(-1,-1),.35,colors.HexColor("#dce8e5")),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#f2f7f5")]),
            ("PADDING",(0,0),(-1,-1),6),("VALIGN",(0,0),(-1,-1),"MIDDLE")
        ]))
        return t

    def number(v, digits=2):
        return f"{v:.{digits}f}" if isinstance(v,(int,float)) else "Not available"

    metrics = [["Measure","Result"],
        ["Recordings",str(summary.get("recordings","Not available"))],
        ["Candidate detections",str(summary.get("detections","Not available"))],
        ["Distinct candidate labels",str(summary.get("candidate_labels","Not available"))],
        ["Excluded model outputs",str(summary.get("filtered_out_detections","Not available"))],
        ["Recording duration",number(summary.get("total_recording_hours"))+" hours"],
        ["Mean model confidence",("Not available" if summary.get("average_confidence") is None else f'{summary["average_confidence"]:.1%}')],
        ["Shannon index",number(summary.get("shannon_diversity"),3)],
        ["Simpson index (1 − D)",number(summary.get("simpson_diversity"),3)]]
    story += [table(metrics,[3.5*inch,2.8*inch]),Spacer(1,16),
              Paragraph("2. Candidate species labels",styles["Heading2"])]
    rows=[["Candidate label","Scientific name","Detections"]]
    for item in data.get("species",[]):
        rows.append([str(item.get("label","—"))[:48],str(item.get("scientific_name") or "—")[:38],
                     str(item.get("detections",0))])
    if len(rows)==1: rows.append(["No candidate labels","—","0"])
    story += [table(rows,[2.5*inch,2.8*inch,1*inch]),Spacer(1,16),
              Paragraph("3. Activity by hour",styles["Heading2"])]
    hours=[["Hour","Candidate detections"]]
    hours += [[f'{int(x["hour"]):02d}:00',str(x.get("detections",0))]
              for x in data.get("hourly",[]) if x.get("detections",0)]
    if len(hours)==1: hours.append(["No timestamped detections","0"])
    story += [table(hours,[2.5*inch,2.5*inch]),PageBreak(),
              Paragraph("4. Daily activity",styles["Heading2"])]
    days=[["Date","Candidate detections"]]
    days += [[str(x.get("date","—")),str(x.get("detections",0))] for x in data.get("daily",[])]
    if len(days)==1: days.append(["No dated detections","0"])
    story += [table(days,[2.5*inch,2.5*inch]),Spacer(1,18),
              Paragraph("5. Interpretation and limitations",styles["Heading2"]),
              Paragraph("This report is generated from the same public dashboard JSON used by the website. "
                        "BirdNET results are automated candidate predictions, not independently verified "
                        "observations. Repeated detections do not represent unique individual animals. "
                        "Diversity indices describe candidate-label frequencies, not a complete ecological "
                        "census. Counts depend on recording effort, microphone placement, weather and model settings.",
                        styles["BodyText"])]
    for note in data.get("interpretation_notes",[]):
        story += [Spacer(1,6),Paragraph("• "+str(note),styles["BodyText"])]
    story += [Spacer(1,14),Paragraph("Dataset export timestamp: "+str(data.get("generated_at","Not supplied")),
                                    styles["Italic"])]
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    doc.build(story)
    print(f"Created {OUTPUT}")

if __name__ == "__main__":
    build()
