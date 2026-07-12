import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib import colors
from datetime import datetime
import os

COLOR_PALETTE = ['#EF476F', '#FFD166', '#06D6A0', '#118AB2', '#FF6B35', '#8338EC', '#2ECC71', '#9090a8']

def generar_grafico_donut(gastos_por_categoria):
    fig, ax = plt.subplots(figsize=(5, 4))
    fig.patch.set_facecolor('#1a1a1a')
    ax.set_facecolor('#1a1a1a')
    labels = list(gastos_por_categoria.keys())
    values = list(gastos_por_categoria.values())
    if not values:
        labels, values = ['Sin datos'], [1]
    colors_ = COLOR_PALETTE[:len(labels)]
    wedges, texts, autotexts = ax.pie(
        values, labels=None, autopct='%1.1f%%', startangle=90,
        colors=colors_, textprops={'color': 'white'},
        pctdistance=0.8, wedgeprops={'linewidth': 1, 'edgecolor': '#1a1a1a'}
    )
    for t in autotexts:
        t.set_color('white')
        t.set_fontsize(9)
    ax.legend(
        wedges, [f'{l}  ${v:,.0f}' for l, v in zip(labels, values)],
        loc='center left', bbox_to_anchor=(1, 0.5),
        fontsize=8, frameon=False,
        labelcolor='white'
    )
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=180, bbox_inches='tight', transparent=False, facecolor='#1a1a1a')
    plt.close(fig)
    buf.seek(0)
    return buf

def generar_grafico_linea(evolucion):
    fig, ax = plt.subplots(figsize=(6.5, 3.5))
    fig.patch.set_facecolor('#1a1a1a')
    ax.set_facecolor('#1a1a1a')
    labels = [e['periodo_label'] for e in evolucion]
    ingresos = [e['ingreso'] for e in evolucion]
    egresos = [e['egreso'] for e in evolucion]
    x = range(len(labels))
    ax.plot(x, ingresos, color='#06D6A0', marker='o', linewidth=2, label='Ingresos')
    ax.plot(x, egresos, color='#EF476F', marker='o', linewidth=2, label='Gastos')
    ax.fill_between(x, ingresos, alpha=0.08, color='#06D6A0')
    ax.fill_between(x, egresos, alpha=0.08, color='#EF476F')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=30, ha='right', color='white', fontsize=8)
    ax.yaxis.set_tick_params(labelcolor='white', labelsize=8)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('#333')
    ax.spines['left'].set_color('#333')
    ax.legend(fontsize=8, frameon=False, labelcolor='white')
    ax.grid(True, alpha=0.15, color='white')
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=180, bbox_inches='tight', facecolor='#1a1a1a')
    plt.close(fig)
    buf.seek(0)
    return buf

def generar_pdf(resumen, periodo, mes_nombre, año):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title2', parent=styles['Title'], fontSize=20, textColor=colors.HexColor('#FF6B35'), spaceAfter=4)
    subtitle_style = ParagraphStyle('Sub', parent=styles['Normal'], fontSize=11, textColor=colors.white, spaceAfter=20)
    normal_style = ParagraphStyle('Normal2', parent=styles['Normal'], fontSize=9, textColor=colors.white)
    header_style = ParagraphStyle('Header', parent=styles['Normal'], fontSize=8, textColor=colors.white, alignment=1)

    elements = []
    elements.append(Paragraph('Control de Gastos', title_style))
    elements.append(Paragraph(f'Informe {periodo} - {mes_nombre} {año}', subtitle_style))
    elements.append(Spacer(1, 0.5*cm))

    kpi_data = [
        ['Ingresos', 'Gastos', 'Balance', 'Prom. Diario'],
        [f"${resumen['total_ingresos']:,.2f}", f"${resumen['total_egresos']:,.2f}",
         f"${resumen['balance']:,.2f}", f"${resumen['promedio_diario']:,.2f}"]
    ]
    t = Table(kpi_data, colWidths=[4*cm]*4)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF6B35')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#2a2a3a')),
        ('TEXTCOLOR', (0, 1), (-1, 1), colors.white),
        ('FONTSIZE', (0, 1), (-1, 1), 12),
        ('TOPPADDING', (0, 1), (-1, 1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#444')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#FF6B35')),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 1*cm))

    donut_buf = generar_grafico_donut(resumen['gastos_por_categoria'])
    donut_img = Image(donut_buf, width=11*cm, height=8*cm)
    line_buf = generar_grafico_linea(resumen['evolucion'])
    line_img = Image(line_buf, width=14*cm, height=7*cm)

    chart_table = Table([[donut_img, line_img]], colWidths=[11*cm, 14*cm])
    chart_table.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER')]))
    elements.append(chart_table)
    elements.append(Spacer(1, 1*cm))

    elements.append(Paragraph('Transacciones Recientes', subtitle_style))
    elements.append(Spacer(1, 0.3*cm))

    tx_header = ['Fecha', 'Concepto', 'Ingreso', 'Egreso', 'Categoría']
    tx_rows = [[t.get('fecha', ''), t.get('concepto', '')[:30],
                f"${t.get('ingreso',0):,.2f}" if t.get('ingreso',0) > 0 else '-',
                f"${t.get('egreso',0):,.2f}" if t.get('egreso',0) > 0 else '-',
                t.get('categoria', '')]
               for t in resumen['transacciones'][:25]]

    tx_data = [tx_header] + tx_rows
    col_w = [2.2*cm, 6*cm, 2.8*cm, 2.8*cm, 2.8*cm]
    t2 = Table(tx_data, colWidths=col_w, repeatRows=1)
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF6B35')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#1e1e2e'), colors.HexColor('#2a2a3a')]),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#444')),
    ]))
    elements.append(t2)
    doc.build(elements)
    buf.seek(0)
    return buf
