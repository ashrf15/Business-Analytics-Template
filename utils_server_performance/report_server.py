import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def report_server(df, uploaded_file):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 50, "Server Performance Report")

    c.setFont("Helvetica", 10)
    y = height - 80
    text_lines = [
        f"Total Records: {df.shape[0]}",
        f"Average Uptime: {df['uptime_percent'].mean():.2f}%" if "uptime_percent" in df.columns else "Average Uptime: N/A",
        f"Average CPU Usage: {df['cpu_usage'].mean():.2f}%" if "cpu_usage" in df.columns else "Average CPU Usage: N/A",
        f"Average Memory Usage: {df['memory_usage'].mean():.2f}%" if "memory_usage" in df.columns else "Average Memory Usage: N/A"
    ]

    for line in text_lines:
        c.drawString(50, y, line)
        y -= 20

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer
