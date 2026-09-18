import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def md_to_reportlab_html(text):
    """Converts markdown formatting (**bold**, *italic*, math) to ReportLab compatible HTML."""
    # Escape XML special characters first
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    
    # Unescape &lt;b&gt; or &lt;i&gt; if introduced, but better to convert markdown syntax:
    # Convert **bold**
    parts = text.split("**")
    new_parts = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            new_parts.append(f"<b>{part}</b>")
        else:
            new_parts.append(part)
    text = "".join(new_parts)

    # Convert *italic*
    parts = text.split("*")
    new_parts = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            new_parts.append(f"<i>{part}</i>")
        else:
            new_parts.append(part)
    text = "".join(new_parts)

    return text

def build_viva_pdf():
    pdf_filename = "Psychodermatology_Viva_Study_Guide.pdf"
    doc = SimpleDocTemplate(
        pdf_filename,
        pagesize=letter,
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1A365D"),
        alignment=1,
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#4A5568"),
        alignment=1,
        spaceAfter=15
    )

    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#2B6CB0"),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor("#2C5282"),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#2D3748"),
        spaceAfter=5
    )

    qa_question_style = ParagraphStyle(
        'QAQuestion',
        parent=styles['Heading4'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor("#742A2A"),
        spaceBefore=8,
        spaceAfter=3,
        keepWithNext=True
    )

    qa_answer_style = ParagraphStyle(
        'QAAnswer',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#1A202C"),
        backColor=colors.HexColor("#FFF5F5"),
        borderColor=colors.HexColor("#FEB2B2"),
        borderWidth=0.5,
        borderPadding=5,
        spaceAfter=8
    )

    story = []

    # Title Header
    story.append(Paragraph("A-to-Z VIVA &amp; PANEL PRESENTATION STUDY GUIDE", title_style))
    story.append(Paragraph("Psychodermatological Disorder Detection &amp; AI Health Assistant", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2B6CB0"), spaceAfter=10))

    md_path = r"C:\Users\Santosh\.gemini\antigravity\brain\b1410472-ceda-42fa-8eda-15f7cce588c2\viva_study_guide_combined.md"
    
    if os.path.exists(md_path):
        with open(md_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        in_code_block = False
        code_lines = []
        
        for line in lines:
            line_str = line.rstrip()
            if line_str.startswith("# A-to-Z") or line_str.startswith("## Psychodermatological"):
                continue # Skip title duplicates
            
            if line_str.startswith("```"):
                if in_code_block:
                    in_code_block = False
                    code_text = "<br/>".join([c.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;") for c in code_lines])
                    code_style = ParagraphStyle('CodeBlock', parent=body_style, fontName='Courier', fontSize=7.5, leading=9.5, backColor=colors.HexColor("#EDF2F7"), borderPadding=4)
                    story.append(Paragraph(code_text, code_style))
                    story.append(Spacer(1, 4))
                    code_lines = []
                else:
                    in_code_block = True
                continue
            
            if in_code_block:
                code_lines.append(line_str)
                continue

            if line_str.startswith("### "):
                story.append(Paragraph(md_to_reportlab_html(line_str[4:]), h1_style))
            elif line_str.startswith("#### Q"):
                story.append(Paragraph(md_to_reportlab_html(line_str[5:]), qa_question_style))
            elif line_str.startswith("#### "):
                story.append(Paragraph(md_to_reportlab_html(line_str[5:]), h2_style))
            elif line_str.startswith("> **Ideal Answer**:") or line_str.startswith("> "):
                clean_ans = line_str.replace("> **Ideal Answer**:", "<b>Ideal Answer:</b>").replace("> ", "")
                story.append(Paragraph(md_to_reportlab_html(clean_ans), qa_answer_style))
            elif line_str.startswith("---"):
                story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E2E8F0"), spaceBefore=4, spaceAfter=4))
            elif line_str.strip():
                story.append(Paragraph(md_to_reportlab_html(line_str), body_style))

    doc.build(story)
    print("Viva PDF Study Guide successfully generated:", pdf_filename)

if __name__ == "__main__":
    build_viva_pdf()
