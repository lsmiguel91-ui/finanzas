#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
reporte_finanzas.py — arma el PDF del reporte mensual de finanzas de Luis Miguel.

Entrada: analisis.json = la salida de calc_finanzas.py (clave "datos") mas los
textos que escribe Claude (semaforo, titular, txt_*, recomendaciones, alertas).

Uso:  python3 reporte_finanzas.py analisis.json salida.pdf

Sin emojis: la fuente base del PDF no los dibuja.
"""
import json, sys, os, textwrap
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as rl_canvas

W, H = A4
VERDE = (0.02, 0.47, 0.34)
VERDE_CLARO = (0.86, 0.94, 0.90)
DORADO = (0.78, 0.60, 0.09)
GRIS = (0.42, 0.45, 0.50)
GRIS_CLARO = (0.94, 0.95, 0.96)
ROJO = (0.78, 0.25, 0.24)
TINTA = (0.11, 0.15, 0.18)
SEMAFORO = {'verde': (0.13, 0.62, 0.38), 'amarillo': (0.85, 0.65, 0.13), 'rojo': ROJO}


def money(v):
    if v is None:
        return '—'
    s = '%0.2f' % abs(v)
    ent, dec = s.split('.')
    out = ''
    while len(ent) > 3:
        out = '.' + ent[-3:] + out
        ent = ent[:-3]
    return ('-' if v < 0 else '') + '$' + ent + out + ',' + dec


def wrap(c, txt, x, y, w, size=9.5, leading=13, color=TINTA, font='Helvetica'):
    c.setFillColorRGB(*color)
    c.setFont(font, size)
    cpl = max(20, int(w / (size * 0.50)))
    for linea in (txt or '').split('\n'):
        for l in (textwrap.wrap(linea, cpl) or ['']):
            c.drawString(x, y, l)
            y -= leading
    return y


def ficha(c, x, y, w, h, titulo, valor, sub='', color=VERDE):
    c.setFillColorRGB(*GRIS_CLARO)
    c.roundRect(x, y, w, h, 3 * mm, stroke=0, fill=1)
    c.setFillColorRGB(*color)
    c.rect(x, y + h - 2.2 * mm, w, 2.2 * mm, stroke=0, fill=1)
    c.setFillColorRGB(*GRIS)
    c.setFont('Helvetica', 7.6)
    c.drawString(x + 4 * mm, y + h - 8 * mm, titulo.upper())
    c.setFillColorRGB(*color)
    c.setFont('Helvetica-Bold', 15)
    c.drawString(x + 4 * mm, y + h - 16 * mm, valor)
    if sub:
        c.setFillColorRGB(*GRIS)
        c.setFont('Helvetica', 7.4)
        for i, l in enumerate(textwrap.wrap(sub, int(w / (7.4 * 0.52)))[:2]):
            c.drawString(x + 4 * mm, y + h - 21 * mm - i * 3.6 * mm, l)


def titulo_seccion(c, x, y, txt):
    c.setFillColorRGB(*VERDE)
    c.setFont('Helvetica-Bold', 11)
    c.drawString(x, y, txt)
    c.setStrokeColorRGB(*VERDE_CLARO)
    c.setLineWidth(1.2)
    c.line(x, y - 2.2 * mm, W - 18 * mm, y - 2.2 * mm)
    return y - 8 * mm


def grafico_tc(cats, path):
    """Barras horizontales: gasto por categoria, mes vs mes anterior."""
    cats = [c for c in cats if c['mes'] or c['anterior']][:8]
    if not cats:
        return None
    cats = cats[::-1]
    etiquetas = [c['categoria'][:18] for c in cats]
    mes = [c['mes'] for c in cats]
    ant = [c['anterior'] for c in cats]
    n = len(cats)
    fig, ax = plt.subplots(figsize=(7.1, max(2.0, 0.46 * n + 0.6)), dpi=190)
    ypos = range(n)
    ax.barh([y + 0.20 for y in ypos], mes, height=0.38, color='#059669', label='Este mes')
    ax.barh([y - 0.20 for y in ypos], ant, height=0.38, color='#cbd5d8', label='Mes anterior')
    ax.set_yticks(list(ypos))
    ax.set_yticklabels(etiquetas, fontsize=8.5)
    ax.tick_params(axis='x', labelsize=8)
    for s in ('top', 'right', 'left'):
        ax.spines[s].set_visible(False)
    ax.grid(axis='x', color='#e6eaec', linewidth=0.7)
    ax.set_axisbelow(True)
    lim = max(mes + ant + [1]) * 1.18
    ax.set_xlim(0, lim)
    for i, v in enumerate(mes):
        if v:
            ax.text(v + lim * 0.012, i + 0.20, money(v), va='center', fontsize=7.6, color='#047857')
    ax.legend(loc='lower right', fontsize=8, frameon=False)
    fig.tight_layout(pad=0.4)
    fig.savefig(path, transparent=True)
    plt.close(fig)
    return path


def barra_progreso(c, x, y, w, pct):
    h = 7 * mm
    c.setFillColorRGB(*GRIS_CLARO)
    c.roundRect(x, y, w, h, 1.6 * mm, stroke=0, fill=1)
    llena = max(2 * mm, w * min(pct, 100) / 100.0)
    c.setFillColorRGB(*VERDE)
    c.roundRect(x, y, llena, h, 1.6 * mm, stroke=0, fill=1)
    c.setFillColorRGB(1, 1, 1)
    c.setFont('Helvetica-Bold', 8.5)
    c.drawString(x + 3 * mm, y + 2.2 * mm, '%.1f%%' % pct)


def main():
    an = json.load(open(sys.argv[1], encoding='utf-8'))
    salida = sys.argv[2]
    d = an['datos']
    per, tar, efe, aho = d['periodo'], d['tarjeta'], d['efectivo'], d['ahorro']
    inv, fin = d['inversiones'], d['finca']

    c = rl_canvas.Canvas(salida, pagesize=A4)
    c.setTitle('Reporte de finanzas — %s' % per['nombre'])
    M = 18 * mm

    # ── Cabecera ──
    c.setFillColorRGB(*VERDE)
    c.rect(0, H - 26 * mm, W, 26 * mm, stroke=0, fill=1)
    c.setFillColorRGB(1, 1, 1)
    c.setFont('Helvetica-Bold', 17)
    c.drawString(M, H - 14 * mm, 'Reporte de finanzas')
    c.setFont('Helvetica', 11.5)
    c.drawString(M, H - 21 * mm, per['nombre'])
    col = SEMAFORO.get(an.get('semaforo', 'verde'), SEMAFORO['verde'])
    c.setFillColorRGB(*col)
    c.circle(W - M - 3 * mm, H - 13 * mm, 3.4 * mm, stroke=0, fill=1)
    c.setFillColorRGB(1, 1, 1)
    c.setFont('Helvetica', 7.5)
    c.drawRightString(W - M - 9 * mm, H - 14.6 * mm, an.get('semaforo', '').upper())

    y = H - 34 * mm
    c.setFillColorRGB(*TINTA)
    c.setFont('Helvetica-Bold', 12)
    for l in textwrap.wrap(an.get('titular', ''), 74)[:2]:
        c.drawString(M, y, l)
        y -= 6 * mm
    y -= 2 * mm

    # ── Fichas ──
    aw = (W - 2 * M - 9 * mm) / 4.0
    fh = 26 * mm
    fy = y - fh
    dlt = efe.get('delta') or 0
    ficha(c, M, fy, aw, fh, 'Efectivo al cierre', money(efe.get('cierre')),
          ('%s vs %s' % (('+' + money(dlt)) if dlt >= 0 else money(dlt), per['anterior'])),
          VERDE if (efe.get('cierre') or 0) >= 0 else ROJO)
    ficha(c, M + (aw + 3 * mm), fy, aw, fh, 'Tarjeta del mes', money(tar['total']),
          ('%s vs mes anterior' % (('+' + money(tar['delta'])) if tar['delta'] >= 0 else money(tar['delta'])))
          if tar.get('cargado') else 'Estado de cuenta no cargado',
          ROJO if tar['delta'] > 0 else VERDE)
    ficha(c, M + 2 * (aw + 3 * mm), fy, aw, fh, 'Ahorro del mes', money(aho['real']),
          ('Cumplido · esperado %s' % money(aho['esperado'])) if aho['cumplido']
          else ('Faltó %s' % money(aho['esperado'] - aho['real'])),
          VERDE if aho['cumplido'] else ROJO)
    ficha(c, M + 3 * (aw + 3 * mm), fy, aw, fh, 'Capital invertido',
          money(inv['patrimonio']['total']),
          'Ganado %s · PF %s · Metas %s' % (money(inv['patrimonio']['ganado']),
                                            money(inv['patrimonio']['plazo']),
                                            money(inv['patrimonio']['metas'])), DORADO)
    y = fy - 10 * mm

    # ── Tarjeta de crédito ──
    y = titulo_seccion(c, M, y, 'En qué se fue la tarjeta')
    img = grafico_tc(tar['por_categoria'], os.path.join(os.path.dirname(salida) or '.', '_tc.png'))
    if img:
        ir = ImageReader(img)
        iw, ih = ir.getSize()
        gw = W - 2 * M
        gh = gw * ih / iw
        gh = min(gh, 66 * mm)
        c.drawImage(ir, M, y - gh, width=gw, height=gh, mask='auto')
        y -= gh + 5 * mm
    y = wrap(c, an.get('txt_tarjeta', ''), M, y, W - 2 * M)
    y -= 4 * mm

    # ── Efectivo ──
    y = titulo_seccion(c, M, y, 'Efectivo')
    y = wrap(c, an.get('txt_efectivo', ''), M, y, W - 2 * M)

    c.setFillColorRGB(*GRIS)
    c.setFont('Helvetica', 7.2)
    c.drawString(M, 12 * mm, 'Generado automáticamente desde tu app de finanzas · %s' % d.get('generado', '')[:10])
    c.drawRightString(W - M, 12 * mm, 'Página 1 de 2')
    c.showPage()

    # ══ Página 2 ══
    c.setFillColorRGB(*VERDE)
    c.rect(0, H - 13 * mm, W, 13 * mm, stroke=0, fill=1)
    c.setFillColorRGB(1, 1, 1)
    c.setFont('Helvetica-Bold', 10.5)
    c.drawString(M, H - 8.8 * mm, 'Ahorro, inversiones y la finca — %s' % per['nombre'])
    y = H - 24 * mm

    y = titulo_seccion(c, M, y, 'Ahorro e inversiones')
    y = wrap(c, an.get('txt_ahorro', ''), M, y, W - 2 * M)
    y -= 2 * mm
    ev = inv.get('eventos') or []
    if ev:
        c.setFillColorRGB(*GRIS)
        c.setFont('Helvetica-Bold', 8)
        c.drawString(M, y, 'MOVIMIENTOS DE INVERSIÓN DEL MES')
        y -= 5 * mm
        for e in ev[:9]:
            c.setFillColorRGB(*(VERDE if e['tipo'] == 'ingreso' else GRIS))
            c.setFont('Helvetica', 8.6)
            c.drawString(M + 2 * mm, y, '%s   %s' % (e['fecha'][-5:], (e['detalle'] or '')[:62]))
            c.drawRightString(W - M, y, ('+' if e['tipo'] == 'ingreso' else '−') + money(e['monto']))
            y -= 4.6 * mm
        y -= 3 * mm

    # ── Finca ──
    y = titulo_seccion(c, M, y, 'Avance hacia la finca')
    c.setFillColorRGB(*TINTA)
    c.setFont('Helvetica-Bold', 13)
    c.drawString(M, y, '%s de %s' % (money(fin['acumulado']), money(fin['meta'])))
    c.setFillColorRGB(*GRIS)
    c.setFont('Helvetica', 9)
    if fin.get('fecha_estimada'):
        c.drawRightString(W - M, y, 'Al ritmo actual: %s (%d meses)'
                          % (fin['fecha_estimada'], fin['meses_faltantes']))
    y -= 9 * mm
    barra_progreso(c, M, y, W - 2 * M, fin['pct'])
    y -= 9 * mm
    if fin.get('fecha_estimada_anterior'):
        c.setFillColorRGB(*GRIS)
        c.setFont('Helvetica', 8.4)
        c.drawString(M, y, 'Mes anterior estimaba: %s' % fin['fecha_estimada_anterior'])
        y -= 5 * mm
    y -= 1 * mm
    y = wrap(c, an.get('txt_finca', ''), M, y, W - 2 * M)
    y -= 4 * mm

    # ── Recomendaciones ──
    recs = an.get('recomendaciones') or []
    if recs:
        y = titulo_seccion(c, M, y, 'Qué hacer este mes')
        for i, r in enumerate(recs[:4], 1):
            c.setFillColorRGB(*VERDE)
            c.setFont('Helvetica-Bold', 10)
            c.drawString(M, y, str(i) + '.')
            y = wrap(c, r, M + 6 * mm, y, W - 2 * M - 6 * mm)
            y -= 2.5 * mm

    # ── Alertas ──
    al = an.get('alertas') or []
    if al:
        # Alto real segun las lineas que ocupara cada alerta al envolverse
        cpl = max(20, int((W - 2 * M - 8 * mm) / (8.4 * 0.50)))
        nlineas = sum(max(1, len(textwrap.wrap(a, cpl))) for a in al)
        bh = 13 * mm + nlineas * 3.75 * mm
        c.setFillColorRGB(1.0, 0.97, 0.90)
        c.roundRect(M, y - bh, W - 2 * M, bh, 2 * mm, stroke=0, fill=1)
        c.setFillColorRGB(*DORADO)
        c.setFont('Helvetica-Bold', 8.4)
        c.drawString(M + 4 * mm, y - 6 * mm, 'OJO')
        yy = y - 11 * mm
        for a in al:
            yy = wrap(c, a, M + 4 * mm, yy, W - 2 * M - 8 * mm, size=8.4, leading=10.5, color=TINTA)
        y -= bh + 4 * mm

    c.setFillColorRGB(*GRIS)
    c.setFont('Helvetica', 7.2)
    c.drawString(M, 12 * mm, 'Reporte de finanzas · %s' % per['nombre'])
    c.drawRightString(W - M, 12 * mm, 'Página 2 de 2')
    c.showPage()
    c.save()
    print(salida)


if __name__ == '__main__':
    main()
