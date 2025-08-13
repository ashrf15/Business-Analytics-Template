import os
import tempfile
from io import BytesIO
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import plotly.express as px
import pandas as pd
import plotly.io as pio

pio.templates.default = "plotly"  # ensure modern layout/colors

def report(df, uploaded_file):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setFont("Helvetica", 10)

    y = 750  # Starting Y-position

    def add_text_block(text, x=50, line_spacing=15, max_width=90):
        nonlocal y
        lines = []
        for paragraph in text.split("\n"):
            while len(paragraph) > max_width:
                split_point = paragraph.rfind(" ", 0, max_width)
                if split_point == -1:
                    split_point = max_width
                lines.append(paragraph[:split_point])
                paragraph = paragraph[split_point + 1:]
            lines.append(paragraph)

        for line in lines:
            c.drawString(x, y, line)
            y -= line_spacing
            if y < 100:
                c.showPage()
                c.setFont("Helvetica", 10)
                y = 750

    # Header
    c.drawString(50, y, "📄 Incident Ticket Report Summary")
    y -= 15
    c.drawString(50, y, f"Total Rows: {df.shape[0]}")
    y -= 15
    c.drawString(50, y, f"Total Columns: {df.shape[1]}")
    y -= 30

    # Missing values
    c.drawString(50, y, "Missing Values:")
    for col, val in df.isnull().sum().items():
        if val > 0:
            y -= 15
            c.drawString(70, y, f"{col}: {val}")
            if y < 100:
                c.showPage()
                c.setFont("Helvetica", 10)
                y = 750

    y -= 30
    c.drawString(50, y, "Visual Insights:")
    y -= 20

    with tempfile.TemporaryDirectory() as tmpdir:
        chart_configs = []

        if 'technician' in df.columns:
            tech_counts = df['technician'].value_counts().head(10).reset_index()
            tech_counts.columns = ['Technician', 'count']
            fig = px.bar(tech_counts, x='Technician', y='count', color='count',
                         color_continuous_scale='Blues', title="Top 10 Technicians")
            insight = f"Top Technician: {tech_counts.iloc[0]['Technician']} handled the most tickets.\nRecommendation: Recognize {tech_counts.iloc[0]['Technician']} and consider mentoring roles."
            chart_configs.append((fig, "Top Technicians", insight))

        if 'department' in df.columns:
            dept_counts = df['department'].value_counts().head(10).reset_index()
            dept_counts.columns = ['Department', 'count']
            fig = px.bar(dept_counts, x='Department', y='count', color='count',
                         color_continuous_scale='Blues', title="Top 10 Departments")
            insight = f"Top Department: {dept_counts.iloc[0]['Department']} has the highest number of tickets.\nRecommendation: Investigate workload distribution or underlying issues."
            chart_configs.append((fig, "Top Departments", insight))

        if 'priority' in df.columns and 'resolution_time' in df.columns:
            fig = px.box(df, x='priority', y='resolution_time',
                         title="Resolution Time by Priority")
            insight = "Ensure high-priority tickets are resolved quicker than low-priority ones.\nRecommendation: Reassess escalation and SLA strategies."
            chart_configs.append((fig, "Resolution Time by Priority", insight))

        if 'site' in df.columns:
            site_counts = df['site'].value_counts().head(10).reset_index()
            site_counts.columns = ['Site', 'count']
            fig = px.bar(site_counts, x='Site', y='count', color='count',
                         color_continuous_scale='Blues', title="Top Sites by Ticket Volume")
            insight = f"Top Site: {site_counts.iloc[0]['Site']}.\nRecommendation: Assign focused support team or preventive strategy."
            chart_configs.append((fig, "Top Sites", insight))

        if 'category' in df.columns:
            cat_counts = df['category'].value_counts().reset_index()
            cat_counts.columns = ['Category', 'count']
            fig = px.bar(cat_counts, x='Category', y='count', color='count',
                         color_continuous_scale='Blues', title="Tickets by Category")
            insight = f"Top Category: {cat_counts.iloc[0]['Category']}.\nRecommendation: Investigate root causes and reduce reoccurrence via training or upgrades."
            chart_configs.append((fig, "Tickets by Category", insight))

        if 'resolution_time' in df.columns:
            fig = px.histogram(df, x='resolution_time', nbins=30, marginal="box",
                               title="Distribution of Resolution Time (hours)", color_discrete_sequence=['#1f77b4'])
            avg_res = df['resolution_time'].mean()
            if avg_res > 48:
                insight = f"Avg Resolution Time: {avg_res:.2f} hrs exceeds 48-hour benchmark.\nRecommendation: Streamline process. Potential savings RM {(avg_res - 48)*len(df)*50:,.0f}"
            else:
                insight = f"Avg Resolution Time: {avg_res:.2f} hrs.\nRecommendation: Maintain or improve current workflow."
            chart_configs.append((fig, "Resolution Time Distribution", insight))

        if 'created_time' in df.columns:
            df['created_month'] = df['created_time'].dt.to_period("M").astype(str)
            monthly = df.groupby('created_month').size().reset_index(name='count')
            fig = px.line(monthly, x='created_month', y='count', markers=True,
                          title="Monthly Ticket Volume")
            top_month = monthly.iloc[monthly['count'].idxmax()]['created_month']
            insight = f"Busiest month: {top_month}.\nRecommendation: Prepare early with staffing and preventive actions."
            chart_configs.append((fig, "Monthly Volume", insight))

        # Loop through charts
        for fig_obj, title, note in chart_configs:
            img_path = os.path.join(tmpdir, f"{title}.png")
            fig_obj.write_image(img_path, width=800, height=500)
            image = Image.open(img_path).resize((500, 300))

            # Ensure space, else new page
            if y < 400:
                c.showPage()
                c.setFont("Helvetica", 10)
                y = 750

            c.drawInlineImage(image, 50, y - 300)
            y -= 320
            c.drawString(50, y, title)
            y -= 15
            add_text_block(note, x=60, line_spacing=14)
            y -= 20

    c.save()
    buffer.seek(0)
    return buffer
