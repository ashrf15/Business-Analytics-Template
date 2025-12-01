import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def report_sla(df, uploaded_file):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 50, "SLA Compliance Report")

    c.setFont("Helvetica", 10)
    y = height - 80
    text_lines = [
        f"Total Records: {df.shape[0]}",
        f"Overall Compliance: {(df['met'].mean()*100):.1f}%" if "met" in df.columns else "Overall Compliance: N/A",
        f"Total Breaches: {df[df['met'] == False].shape[0]}" if "met" in df.columns else "Total Breaches: N/A",
        f"Average Customer Satisfaction: {df['customer_satisfaction'].mean():.2f}" if "customer_satisfaction" in df.columns else "Average CSAT: N/A"
    ]

    for line in text_lines:
        c.drawString(50, y, line)
        y -= 20

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer
