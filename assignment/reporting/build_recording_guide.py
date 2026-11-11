"""Build a printable English recording guide from its Markdown source; no API calls."""
from pathlib import Path
import re
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

OUT = Path(__file__).resolve().parents[1] / "deliverables"


def build():
    font = "Helvetica"
    font_path = Path("C:/Windows/Fonts/arial.ttf")
    if font_path.exists():
        pdfmetrics.registerFont(TTFont("GuideArial", str(font_path)))
        font = "GuideArial"
    styles = {
        "body": ParagraphStyle("body", fontName=font, fontSize=10, leading=14, spaceAfter=8),
        "title": ParagraphStyle("title", fontName=font, fontSize=19, leading=24, spaceAfter=14, textColor=colors.HexColor("#156082")),
        "heading": ParagraphStyle("heading", fontName=font, fontSize=13, leading=17, spaceBefore=12, spaceAfter=9, keepWithNext=True, textColor=colors.HexColor("#156082")),
        "cell": ParagraphStyle("cell", fontName=font, fontSize=7.4, leading=10),
    }

    def inline(text):
        text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", text)
        text = escape(text)
        text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
        return text.replace("`", "")

    story, paragraph, table_rows = [], [], []

    def flush_paragraph():
        if paragraph:
            story.append(Paragraph(inline(" ".join(paragraph)), styles["body"]))
            paragraph.clear()

    def flush_table():
        if not table_rows:
            return
        data = [[Paragraph(inline(v), styles["cell"]) for v in row] for row in table_rows]
        table = Table(data, colWidths=[72, 40, 215, 180], repeatRows=1, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e7f0f5")),
            ("GRID", (0, 0), (-1, -1), .35, colors.HexColor("#b8c7d1")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.extend([table, Spacer(1, 12)])
        table_rows.clear()

    text = (OUT / "RECORDING_SCRIPT_EN.md").read_text(encoding="utf-8")
    for line in text.splitlines() + [""]:
        if line.startswith("|"):
            flush_paragraph()
            row = [x.strip() for x in line.strip("|").split("|")]
            if not all(re.fullmatch(r":?-+:?", x) for x in row):
                table_rows.append(row)
            continue
        flush_table()
        if not line.strip():
            flush_paragraph()
        elif line.startswith("# ") or line.startswith("## "):
            flush_paragraph()
            story.append(Paragraph(inline(line.lstrip("# ")), styles["title" if line.startswith("# ") else "heading"]))
        elif re.match(r"\d+\. ", line):
            flush_paragraph()
            story.append(Paragraph(inline(line), styles["body"]))
        else:
            paragraph.append(line.strip())

    def footer(canvas, doc):
        canvas.setFont(font, 8)
        canvas.setFillColor(colors.HexColor("#667085"))
        canvas.drawString(44, 26, "SANG Yuchen | 1155262204 | English recording guide")
        canvas.drawRightString(A4[0] - 44, 26, str(doc.page))

    path = OUT / "FTEC5660_Recording_Script_EN.pdf"
    SimpleDocTemplate(str(path), pagesize=A4, leftMargin=44, rightMargin=44, topMargin=38, bottomMargin=44,
                      title="FTEC5660 - 12-minute English recording guide", author="SANG Yuchen").build(
                          story, onFirstPage=footer, onLaterPages=footer)
    print(path)


if __name__ == "__main__":
    build()
