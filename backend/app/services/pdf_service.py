from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import datetime, date
from typing import Optional

IGREJA_NOME = "Igreja Kairos"
IGREJA_ENDERECO = "Sede - Endereço da Igreja"
IGREJA_CNPJ = "00.000.000/0001-00"

def _header(canvas_obj, doc):
    canvas_obj.saveState()
    canvas_obj.setFont("Helvetica-Bold", 14)
    canvas_obj.drawCentredString(A4[0]/2, A4[1] - 1.5*cm, IGREJA_NOME)
    canvas_obj.setFont("Helvetica", 9)
    canvas_obj.drawCentredString(A4[0]/2, A4[1] - 2.1*cm, IGREJA_ENDERECO)
    canvas_obj.setStrokeColor(colors.HexColor("#1a365d"))
    canvas_obj.setLineWidth(1.5)
    canvas_obj.line(2*cm, A4[1] - 2.5*cm, A4[0] - 2*cm, A4[1] - 2.5*cm)
    canvas_obj.restoreState()

def _footer(canvas_obj, doc):
    canvas_obj.saveState()
    canvas_obj.setFont("Helvetica", 8)
    canvas_obj.drawCentredString(A4[0]/2, 1.5*cm, f"Documento gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')} | Kairos Igreja")
    canvas_obj.restoreState()

def gerar_certificado_batismo(membro: dict, data_doc: Optional[date] = None) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=3.5*cm, bottomMargin=2.5*cm)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18, alignment=TA_CENTER, spaceAfter=20, textColor=colors.HexColor("#1a365d"))
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=12, alignment=TA_CENTER, leading=18, spaceAfter=12)
    name_style = ParagraphStyle('Name', parent=styles['Normal'], fontSize=16, alignment=TA_CENTER, fontName="Helvetica-Bold", spaceAfter=12, textColor=colors.HexColor("#2b6cb0"))
    
    story = []
    story.append(Paragraph("CERTIFICADO DE BATISMO", title_style))
    story.append(Spacer(1, 0.8*cm))
    story.append(Paragraph("Certificamos que", body_style))
    story.append(Paragraph(membro.get("nome_completo", "").upper(), name_style))
    story.append(Paragraph(
        f"foi batizado(a) nas águas em {membro.get('data_batismo', '____/____/________')}, "
        f"conforme os ensinamentos das Sagradas Escrituras, "
        f"na {IGREJA_NOME}.",
        body_style
    ))
    if membro.get("congregacao_nome"):
        story.append(Paragraph(f"Congregação: {membro['congregacao_nome']}", body_style))
    
    story.append(Spacer(1, 1.5*cm))
    data_str = (data_doc or date.today()).strftime("%d de %B de %Y").replace(
        "January", "janeiro").replace("February", "fevereiro").replace("March", "março")\
        .replace("April", "abril").replace("May", "maio").replace("June", "junho")\
        .replace("July", "julho").replace("August", "agosto").replace("September", "setembro")\
        .replace("October", "outubro").replace("November", "novembro").replace("December", "dezembro")
    
    story.append(Paragraph(f"{IGREJA_NOME}, {data_str}.", body_style))
    story.append(Spacer(1, 2*cm))
    
    # Assinaturas
    sig_data = [
        ["_" * 35, "_" * 35],
        ["Pastor Presidente", "Secretaria"],
    ]
    t = Table(sig_data, colWidths=[8*cm, 8*cm])
    t.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 20),
    ]))
    story.append(t)
    
    doc.build(story, onFirstPage=_header, onLaterPages=_header)
    return buffer.getvalue()

def gerar_declaracao_membro(membro: dict, data_doc: Optional[date] = None) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=3.5*cm, bottomMargin=2.5*cm)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=16, alignment=TA_CENTER, spaceAfter=20, textColor=colors.HexColor("#1a365d"))
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=11, alignment=TA_LEFT, leading=16, spaceAfter=10, firstLineIndent=1*cm)
    
    story = []
    story.append(Paragraph("DECLARAÇÃO DE MEMBRO", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    texto = (
        f"Declaramos para os devidos fins que <b>{membro.get('nome_completo', '').upper()}</b>, "
        f"portador(a) do CPF nº {membro.get('cpf') or '______________'}, "
        f"é membro regularmente filiado(a) desta igreja"
    )
    if membro.get("congregacao_nome"):
        texto += f", congregação <b>{membro['congregacao_nome']}</b>"
    if membro.get("data_filiacao"):
        texto += f", desde {membro['data_filiacao']}"
    texto += ", encontrando-se em plena comunhão com esta comunidade de fé."
    
    story.append(Paragraph(texto, body_style))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(
        "Esta declaração é válida para todos os fins legais e eclesiásticos.",
        body_style
    ))
    
    story.append(Spacer(1, 1.5*cm))
    data_str = (data_doc or date.today()).strftime("%d/%m/%Y")
    story.append(Paragraph(f"{IGREJA_NOME}, {data_str}.", ParagraphStyle('Right', parent=styles['Normal'], alignment=TA_RIGHT)))
    
    story.append(Spacer(1, 2*cm))
    sig_data = [
        ["_" * 35, "_" * 35],
        ["Pastor Presidente", "Secretaria"],
    ]
    t = Table(sig_data, colWidths=[8*cm, 8*cm])
    t.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    story.append(t)
    
    doc.build(story, onFirstPage=_header, onLaterPages=_header)
    return buffer.getvalue()

def gerar_carta_transferencia(membro: dict, igreja_destino: str = "", data_doc: Optional[date] = None) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=3.5*cm, bottomMargin=2.5*cm)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=16, alignment=TA_CENTER, spaceAfter=20, textColor=colors.HexColor("#1a365d"))
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=11, alignment=TA_LEFT, leading=16, spaceAfter=10, firstLineIndent=1*cm)
    
    story = []
    story.append(Paragraph("CARTA DE TRANSFERÊNCIA", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    texto = (
        f"A {IGREJA_NOME} recomenda e transfere o(a) irmão(ã) "
        f"<b>{membro.get('nome_completo', '').upper()}</b>, "
        f"CPF {membro.get('cpf') or '______________'}, "
        f"membro desta igreja"
    )
    if membro.get("congregacao_nome"):
        texto += f" (congregação {membro['congregacao_nome']})"
    texto += f", para a igreja <b>{igreja_destino or '________________'}</b>, "
    texto += "encontrando-se em plena comunhão e sem pendências eclesiásticas."
    
    story.append(Paragraph(texto, body_style))
    story.append(Spacer(1, 1.5*cm))
    data_str = (data_doc or date.today()).strftime("%d/%m/%Y")
    story.append(Paragraph(f"{IGREJA_NOME}, {data_str}.", ParagraphStyle('Right', parent=styles['Normal'], alignment=TA_RIGHT)))
    
    story.append(Spacer(1, 2*cm))
    sig_data = [
        ["_" * 35, "_" * 35],
        ["Pastor Presidente", "Secretaria"],
    ]
    t = Table(sig_data, colWidths=[8*cm, 8*cm])
    t.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    story.append(t)
    
    doc.build(story, onFirstPage=_header, onLaterPages=_header)
    return buffer.getvalue()

def gerar_carteirinha(membro: dict) -> bytes:
    """Gera uma carteirinha simples em PDF (frente)"""
    buffer = BytesIO()
    # Tamanho aproximado de cartão
    width, height = 9*cm, 5.5*cm
    c = canvas.Canvas(buffer, pagesize=(width, height))
    
    # Fundo
    c.setFillColor(colors.HexColor("#1a365d"))
    c.rect(0, 0, width, height, fill=1, stroke=0)
    
    # Faixa
    c.setFillColor(colors.HexColor("#2b6cb0"))
    c.rect(0, height - 1.2*cm, width, 1.2*cm, fill=1, stroke=0)
    
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(width/2, height - 0.8*cm, IGREJA_NOME.upper())
    
    c.setFont("Helvetica-Bold", 8)
    c.drawString(0.4*cm, height - 2*cm, "CARTEIRINHA DE MEMBRO")
    
    c.setFont("Helvetica", 7)
    c.drawString(0.4*cm, height - 2.7*cm, f"Nome: {membro.get('nome_completo', '')[:28]}")
    c.drawString(0.4*cm, height - 3.3*cm, f"Nº: {membro.get('numero_carteirinha') or membro.get('id', '')}")
    if membro.get("congregacao_nome"):
        c.drawString(0.4*cm, height - 3.9*cm, f"Congr.: {membro['congregacao_nome'][:22]}")
    if membro.get("validade_carteirinha"):
        c.drawString(0.4*cm, height - 4.5*cm, f"Validade: {membro['validade_carteirinha']}")
    
    c.setFont("Helvetica", 6)
    c.drawCentredString(width/2, 0.3*cm, "Kairos Igreja")
    
    c.save()
    return buffer.getvalue()

def gerar_relatorio_membros(membros: list, titulo: str = "Relatório de Membros") -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=3.5*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=14, alignment=TA_CENTER, spaceAfter=15, textColor=colors.HexColor("#1a365d"))
    
    story = []
    story.append(Paragraph(titulo, title_style))
    story.append(Paragraph(f"Total: {len(membros)} membros | Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", 
                          ParagraphStyle('Sub', parent=styles['Normal'], fontSize=9, alignment=TA_CENTER, spaceAfter=15)))
    
    data = [["#", "Nome", "Congregação", "WhatsApp", "Obreiro"]]
    for i, m in enumerate(membros, 1):
        data.append([
            str(i),
            (m.get("nome_completo") or "")[:30],
            (m.get("congregacao_nome") or "")[:20],
            m.get("whatsapp") or "",
            "Sim" if m.get("eh_obreiro") else "Não"
        ])
    
    t = Table(data, colWidths=[1*cm, 6.5*cm, 4.5*cm, 3.5*cm, 2*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1a365d")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (4, 0), (4, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f8")]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    
    doc.build(story, onFirstPage=_header, onLaterPages=_header)
    return buffer.getvalue()
