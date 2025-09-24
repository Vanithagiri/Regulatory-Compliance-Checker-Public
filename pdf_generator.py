from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

def generate_rewritten_pdf(df):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>AI-Rewritten Contract Clauses Report</b>", styles["Title"]))
    story.append(Spacer(1, 20))

    for _, row in df.iterrows():
        clause_id = row["clause_id"]
        original = row["clause"]
        modified = row.get("AI-Modified Clause", "⚠️ Not available")
        original_risk = row.get("risk_level", "Unknown")

        story.append(Paragraph(f"<b>Clause ID: {clause_id}</b>", styles["h2"]))
        story.append(Spacer(1, 12))
        
        
        story.append(Paragraph(f"<b>Original Risk Level:</b> {original_risk}", styles["h3"]))
        story.append(Paragraph("<b>Original Clause:</b>", styles["h3"]))
        story.append(Paragraph(original, styles["Normal"]))
        story.append(Spacer(1, 12))
        story.append(Paragraph("<b>AI-Modified Clause:</b>", styles["h3"]))
        story.append(Paragraph(modified, styles["Normal"]))
        story.append(Spacer(1, 24))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()