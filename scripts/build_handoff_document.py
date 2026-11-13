"""Build the reviewed handoff PDF from its Markdown source using ReportLab."""
from pathlib import Path
import html
import json
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'docs/成熟度评估baseline调研结果.md'
OUTPUT = ROOT / 'output/pdf/成熟度评估baseline调研结果.pdf'
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
pdfmetrics.registerFont(TTFont('BodyCN', 'C:/Windows/Fonts/simsun.ttc', subfontIndex=0))
pdfmetrics.registerFont(TTFont('HeadingCN', 'C:/Windows/Fonts/simhei.ttf'))
pdfmetrics.registerFontFamily('BodyCN', normal='BodyCN', bold='HeadingCN', italic='BodyCN', boldItalic='HeadingCN')

body = ParagraphStyle('Body', fontName='BodyCN', fontSize=10.5, leading=17,
                      spaceAfter=7, wordWrap='CJK', splitLongWords=True)
styles = {
    'body': body,
    'title': ParagraphStyle('Title', parent=body, fontName='HeadingCN', fontSize=22, leading=30, spaceAfter=14, keepWithNext=True),
    'h1': ParagraphStyle('H1', parent=body, fontName='HeadingCN', fontSize=15, leading=22, spaceBefore=15, spaceAfter=8, keepWithNext=True),
    'h2': ParagraphStyle('H2', parent=body, fontName='HeadingCN', fontSize=12, leading=19, spaceBefore=9, spaceAfter=6, keepWithNext=True),
    'cell': ParagraphStyle('Cell', parent=body, fontSize=9, leading=14, spaceAfter=0),
    'head': ParagraphStyle('TableHead', parent=body, fontName='HeadingCN', fontSize=9, leading=14, spaceAfter=0),
    'code': ParagraphStyle('Code', parent=body, fontSize=8.5, leading=12, leftIndent=9, rightIndent=5, spaceAfter=2),
    'bullet': ParagraphStyle('Bullet', parent=body, leftIndent=12, firstLineIndent=-10),
}

def inline(text):
    def link(match):
        label, target = match.groups()
        if not target.startswith(('https://', 'http://')):
            target = (SOURCE.parent / target).resolve().as_uri()
        return '<link href="' + html.escape(target, quote=True) + '" color="#24527A">' + html.escape(label) + '</link>'
    parts = []
    pos = 0
    for match in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', text):
        parts.append(html.escape(text[pos:match.start()]))
        parts.append(link(match))
        pos = match.end()
    parts.append(html.escape(text[pos:]))
    value = ''.join(parts)
    value = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', value)
    return value

class HandoffDoc(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name == 'H1':
            text = flowable.getPlainText()
            anchor = 'section-' + text.split()[0]
            self.canv.bookmarkPage(anchor)
            self.canv.addOutlineEntry(text, anchor, level=0)

def page_header(canvas, doc):
    canvas.saveState()
    canvas.setFont('BodyCN', 8)
    canvas.setFillColor(colors.HexColor('#4D4D4D'))
    canvas.drawString(48, A4[1]-29, '成熟度评估  四基线工作交接')
    canvas.drawRightString(A4[0]-48, A4[1]-29, '2026年11月4日')
    canvas.drawCentredString(A4[0]/2, 27, str(doc.page))
    canvas.restoreState()

lines = SOURCE.read_text(encoding='utf-8').splitlines()
story = []
i = 0
width = A4[0] - 96
while i < len(lines):
    line = lines[i].strip()
    if not line:
        i += 1
        continue
    if line.startswith('~~~'):
        story.append(Spacer(1, 3))
        i += 1
        while i < len(lines) and not lines[i].startswith('~~~'):
            code = html.escape(lines[i]).replace(' ', '&#160;')
            story.append(Paragraph(code or '&#160;', styles['code']))
            i += 1
        story.append(Spacer(1, 7))
        i += 1
        continue
    if line.startswith('|'):
        rows = []
        while i < len(lines) and lines[i].strip().startswith('|'):
            cells = [x.strip() for x in lines[i].strip().strip('|').split('|')]
            if not all(re.fullmatch(r':?-+:?', x) for x in cells):
                rows.append(cells)
            i += 1
        cols = len(rows[0])
        ratios = {2: [.28, .72], 3: [.23, .36, .41], 4: [.29, .15, .19, .37]}[cols]
        values = [[Paragraph(inline(cell), styles['head' if j == 0 else 'cell']) for cell in row] for j, row in enumerate(rows)]
        table = Table(values, colWidths=[width*r for r in ratios], repeatRows=1, hAlign='LEFT')
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E5ECF2')),
            ('GRID', (0,0), (-1,-1), .45, colors.HexColor('#D9D9D9')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (-1,-1), 7), ('RIGHTPADDING', (0,0), (-1,-1), 7),
            ('TOPPADDING', (0,0), (-1,-1), 6), ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        story.extend([table, Spacer(1, 9)])
        continue
    if line.startswith('# '):
        story.append(Paragraph(inline(line[2:]), styles['title']))
    elif line.startswith('## '):
        story.append(Paragraph(inline(line[3:]), styles['h1']))
    elif line.startswith('### '):
        story.append(Paragraph(inline(line[4:]), styles['h2']))
    elif line.startswith('- '):
        story.append(Paragraph('• ' + inline(line[2:]), styles['bullet']))
    else:
        story.append(Paragraph(inline(line), styles['body']))
    i += 1

doc = HandoffDoc(str(OUTPUT), pagesize=A4, leftMargin=48, rightMargin=48,
                topMargin=49, bottomMargin=46, title='成熟度评估baseline调研结果',
                author='成熟度评估项目', pageCompression=1)
doc.build(story, onFirstPage=page_header, onLaterPages=page_header)
reader = PdfReader(OUTPUT)
texts = [p.extract_text() for p in reader.pages]
for key in ['feTruth', 'Kivi', 'Reynard', 'Fairwinds Insights', '70.6328%', 'commercial_runs']:
    assert key in '\n'.join(texts), key
print(json.dumps({'pdf': str(OUTPUT), 'pages': len(reader.pages), 'characters': sum(map(len, texts))}, ensure_ascii=False))
