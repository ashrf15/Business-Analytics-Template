import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def report_network(df, uploaded_file):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 50, "Network Performance Report")

    c.setFont("Helvetica", 10)
    y = height - 80
    text_lines = [
        f"Total Records: {df.shape[0]}",
        f"Average Uptime: {df['uptime_percent'].mean():.2f}%" if "uptime_percent" in df.columns else "Average Uptime: N/A",
        f"Average Latency: {df['latency_ms'].mean():.2f} ms" if "latency_ms" in df.columns else "Average Latency: N/A",
        f"Average Bandwidth Usage: {df['bandwidth_usage_mbps'].mean():.2f} Mbps" if "bandwidth_usage_mbps" in df.columns else "Average Bandwidth: N/A"
    ]

    for line in text_lines:
        c.drawString(50, y, line)
        y -= 20

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer
