#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
calc_finanzas.py — calcula los NUMEROS del reporte mensual de finanzas de Luis Miguel.

No opina ni redacta: solo produce cifras verificables a partir del JSON de la app,
replicando las mismas formulas del archivo index.html (v35). Los textos y las
recomendaciones los escribe Claude despues, leyendo este resultado.

Uso:  python3 calc_finanzas.py db.json 2026 10 [historico_patrimonio.json] > datos.json
      (ano y mes del periodo a reportar; mes 1-12)

IMPORTANTE sobre el patrimonio: la app ELIMINA los plazos fijos y las metas cuando
vencen, asi que el patrimonio de meses pasados NO se puede reconstruir desde el JSON
(un PF cerrado en octubre ya no existe en los datos de septiembre). Por eso el
historico se guarda aparte, en historico_patrimonio.json: cada corrida agrega el
snapshot del mes. Mientras no haya snapshot del mes anterior, la comparacion se
marca comparable=false y el reporte no debe afirmar que el patrimonio "crecio".
"""
import json, sys, calendar, datetime

MN = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto',
      'Septiembre','Octubre','Noviembre','Diciembre']
CAT_EV = ['Alimentación','Combustible','Parqueadero','Movilización','Entretenimiento',
          'Educación','Salud','Vivienda','Suscripciones','Compras Online','Otros']
CAT_IMP = ['Imprevistos','Gastos Ganado','Ganado','Mantenimiento Vehículo']
CAT_DEU = ['Crédito','Pago de Carro']
CAT_AHO = ['Ahorros CPN','Ahorros Banco Guayaquil','Otros Ahorros']
INICIO = (2026, 4)        # mayo 2026, inicio del tracking acumulado
META_FINCA = 100000.0


def es_flujo_inv(m):
    return bool(m.get('flujoInv') or m.get('categoria') == 'Reinversión')


def mes_ant(yr, mi):
    return (yr - 1, 11) if mi == 0 else (yr, mi - 1)


def hist_de(db, yr, mi):
    for h in db.get('hist', []):
        if h.get('a') == yr and h.get('m') == MN[mi]:
            return h
    return {'ing': 0, 'ev': 0, 'imp': 0, 'deu': 0, 'aho': 0}


def tc_estado(db, yr, mi):
    """Total del estado de cuenta de la TC de ese mes (misma regla que la app)."""
    mn = MN[mi]
    por_import = [p for p in db.get('tcPagos', [])
                  if p.get('periodoImport') and p['periodoImport'].get('anyo') == yr
                  and p['periodoImport'].get('mes') == mn]
    if por_import:
        return por_import[0].get('periodoTotal') or sum(p.get('total', 0) for p in por_import)
    return sum(p.get('total', 0) for p in db.get('tcPagos', [])
               if not p.get('periodoImport') and p.get('anyo') == yr and p.get('mes') == mn)


def tc_por_categoria(db, yr, mi):
    """Gasto de tarjeta del mes, agrupado por categoria, desde el detalle del estado."""
    mn, out = MN[mi], {}
    for p in db.get('tcPagos', []):
        pi = p.get('periodoImport') or {}
        if not ((pi.get('anyo') == yr and pi.get('mes') == mn) or
                (not pi and p.get('anyo') == yr and p.get('mes') == mn)):
            continue
        for d in p.get('detalle', []) or []:
            cat = d.get('categoria') or 'Sin categoría'
            out[cat] = round(out.get(cat, 0) + (d.get('monto') or 0), 2)
    return out


def flujo_inv(db, yr, mi):
    ent = sal = 0.0
    for m in db.get('movimientos', []):
        if not es_flujo_inv(m):
            continue
        f = m.get('fecha') or ''
        if f[:7] != '%04d-%02d' % (yr, mi + 1):
            continue
        if m.get('tipo') == 'ingreso':
            ent += m.get('monto', 0)
        else:
            sal += m.get('monto', 0)
    return {'entradas': round(ent, 2), 'salidas': round(sal, 2), 'neto': round(ent - sal, 2)}


def efectivo_por_categoria(db, yr, mi):
    """Egresos en efectivo del mes por categoria (sin flujo de inversiones)."""
    out = {}
    for m in db.get('movimientos', []):
        if m.get('tipo') != 'egreso' or es_flujo_inv(m):
            continue
        if (m.get('fecha') or '')[:7] != '%04d-%02d' % (yr, mi + 1):
            continue
        cat = m.get('categoria') or 'Sin categoría'
        out[cat] = round(out.get(cat, 0) + (m.get('monto') or 0), 2)
    return out


def cash_fin_mes(db, yr, mi, _memo=None):
    """Cash real post-TC al cierre del mes. Encadenado desde el inicio del tracking."""
    if _memo is None:
        _memo = {}
    k = (yr, mi)
    if k in _memo:
        return _memo[k]
    if (yr, mi) < INICIO:
        return None
    if (yr, mi) == INICIO:
        saldo_ini = db.get('saldoInicial', 0)
    else:
        prev = cash_fin_mes(db, *mes_ant(yr, mi), _memo=_memo)
        saldo_ini = prev if prev is not None else db.get('saldoInicial', 0)
    h = hist_de(db, yr, mi)
    egr_ef = h.get('ev', 0) + h.get('imp', 0) + h.get('deu', 0) + h.get('aho', 0)
    v = saldo_ini + (h.get('ing', 0) - egr_ef) - tc_estado(db, yr, mi) + flujo_inv(db, yr, mi)['neto']
    _memo[k] = round(v, 2)
    return _memo[k]


def tramo_vigente(meta, yr, mi):
    """Aporte mensual vigente de una meta para ese mes (ultimo tramo ya iniciado)."""
    tramos = sorted(meta.get('tramosAporte') or
                    [{'desde': meta.get('fi', ''), 'monto': meta.get('aporte', 0)}],
                    key=lambda t: t.get('desde') or '')
    ref = '%04d-%02d-01' % (yr, mi + 1)
    v = 0.0
    for t in tramos:
        if (t.get('desde') or '') <= ref:
            v = t.get('monto', 0)
    return v


def capital_meta(meta, yr, mi):
    """Capital aportado a una meta hasta el cierre de ese mes (sin interes).
    Suma los tramos mes a mes mas aportes extra, menos retiros."""
    fi = meta.get('fi')
    if not fi:
        return 0.0
    y0, m0 = int(fi[:4]), int(fi[5:7]) - 1
    total = 0.0
    y, m = y0, m0
    plazo = int(meta.get('plazo') or 12)
    pasos = 0
    while (y, m) <= (yr, mi) and pasos < plazo:
        total += tramo_vigente(meta, y, m)
        m += 1
        if m > 11:
            m = 0
            y += 1
        pasos += 1
    lim = '%04d-%02d-31' % (yr, mi + 1)
    for a in meta.get('aportesExtra') or []:
        if (a.get('fecha') or '') <= lim:
            total += a.get('monto', 0)
    for r in meta.get('retiros') or []:
        if (r.get('fecha') or '') <= lim:
            total -= r.get('monto', 0)
    return round(total, 2)


def patrimonio(db, yr, mi):
    """Capital invertido al cierre del mes, por instrumento."""
    lim = '%04d-%02d-31' % (yr, mi + 1)
    ganado = 0.0
    for g in db.get('inv', {}).get('ganado', []) or []:
        if g.get('enFormacion'):
            continue
        if g.get('ventaReal') and (g.get('fventa') or '') <= lim:
            continue                       # ya vendido: su capital volvio al cash
        if (g.get('fi') or '9999') <= lim:
            ganado += g.get('cap', 0)
    plazo = 0.0
    for p in db.get('inv', {}).get('plazo', []) or []:
        if (p.get('fi') or '9999') <= lim:
            plazo += p.get('cap', 0)
    metas = sum(capital_meta(m, yr, mi) for m in db.get('inv', {}).get('metas', []) or [])
    return {'ganado': round(ganado, 2), 'plazo': round(plazo, 2),
            'metas': round(metas, 2), 'total': round(ganado + plazo + metas, 2)}


def proyeccion_finca(acumulado, aporte_mensual, tasa_anual, yr, mi):
    """Meses hasta los $100k al ritmo actual, con interes compuesto mensual."""
    if aporte_mensual <= 0:
        return None, None
    tm = (tasa_anual / 100.0) / 12.0
    s, n = acumulado, 0
    while s < META_FINCA and n < 600:
        s = s * (1 + tm) + aporte_mensual
        n += 1
    if n >= 600:
        return None, None
    y, m = yr, mi + n
    y += m // 12
    m = m % 12
    return n, '%s %d' % (MN[m][:3].lower(), y)


def main():
    if len(sys.argv) < 4:
        print('uso: calc_finanzas.py db.json ANO MES', file=sys.stderr)
        sys.exit(1)
    db = json.load(open(sys.argv[1], encoding='utf-8'))
    yr, mi = int(sys.argv[2]), int(sys.argv[3]) - 1
    pyr, pmi = mes_ant(yr, mi)
    hist_path = sys.argv[4] if len(sys.argv) > 4 else None
    historico = {}
    if hist_path:
        try:
            historico = json.load(open(hist_path, encoding='utf-8'))
        except Exception:
            historico = {}

    h, hp = hist_de(db, yr, mi), hist_de(db, pyr, pmi)
    tc, tcp = tc_estado(db, yr, mi), tc_estado(db, pyr, pmi)
    cat_tc, cat_tc_p = tc_por_categoria(db, yr, mi), tc_por_categoria(db, pyr, pmi)

    # comparativo por categoria de tarjeta, ordenado por el cambio mas grande
    cats = sorted(set(cat_tc) | set(cat_tc_p))
    comp = []
    for c in cats:
        a, b = cat_tc.get(c, 0), cat_tc_p.get(c, 0)
        comp.append({'categoria': c, 'mes': round(a, 2), 'anterior': round(b, 2),
                     'delta': round(a - b, 2)})
    comp.sort(key=lambda x: -abs(x['delta']))

    egr_ef = h.get('ev', 0) + h.get('imp', 0) + h.get('deu', 0) + h.get('aho', 0)
    cierre, cierre_p = cash_fin_mes(db, yr, mi), cash_fin_mes(db, pyr, pmi)
    pat = patrimonio(db, yr, mi)
    # El patrimonio del mes anterior SOLO es valido si quedo guardado entonces: los
    # instrumentos cerrados se borran del JSON y recalcularlos hacia atras da de menos.
    clave_ant = '%04d-%02d' % (pyr, pmi + 1)
    pat_p = historico.get(clave_ant)
    comparable = bool(pat_p)

    # ahorro esperado = tramo vigente de cada meta + recargo de la entidad
    esperado = []
    for m in db.get('inv', {}).get('metas', []) or []:
        base = tramo_vigente(m, yr, mi)
        if base <= 0:
            continue
        esperado.append({'meta': ((m.get('nombre') + ' · ') if m.get('nombre') else '') + (m.get('desc') or ''),
                         'aporte': base, 'recargo': m.get('recargo', 0) or 0,
                         'total': round(base + (m.get('recargo', 0) or 0), 2)})
    aho_esperado = round(sum(e['total'] for e in esperado), 2)

    # tasa promedio ponderada de los instrumentos, para la proyeccion
    tasas, pesos = [], []
    for p in db.get('inv', {}).get('plazo', []) or []:
        tasas.append(p.get('tasaA', 0)); pesos.append(p.get('cap', 0))
    for m in db.get('inv', {}).get('metas', []) or []:
        tasas.append(m.get('tasaA', 0)); pesos.append(capital_meta(m, yr, mi))
    tasa_prom = round(sum(t * w for t, w in zip(tasas, pesos)) / sum(pesos), 2) if sum(pesos) else 0

    aporte_mes = round(sum(e['aporte'] for e in esperado), 2)
    meses, fecha = proyeccion_finca(pat['total'], aporte_mes, tasa_prom, yr, mi)
    meses_p = fecha_p = None
    if comparable:
        meses_p, fecha_p = proyeccion_finca(pat_p['total'], aporte_mes, tasa_prom, pyr, pmi)

    # movimientos de inversion del mes (para narrar que paso)
    eventos = []
    for m in db.get('movimientos', []):
        if (m.get('fecha') or '')[:7] != '%04d-%02d' % (yr, mi + 1):
            continue
        if es_flujo_inv(m):
            eventos.append({'fecha': m.get('fecha'), 'tipo': m.get('tipo'),
                            'monto': m.get('monto'), 'detalle': m.get('descripcion') or m.get('categoria')})
    eventos.sort(key=lambda e: e['fecha'])

    dias = calendar.monthrange(yr, mi + 1)[1]
    out = {
        'periodo': {'anio': yr, 'mes': mi + 1, 'nombre': '%s %d' % (MN[mi], yr),
                    'anterior': '%s %d' % (MN[pmi], pyr), 'dias': dias},
        'ingresos': {'mes': round(h.get('ing', 0), 2), 'anterior': round(hp.get('ing', 0), 2)},
        'egresos_efectivo': {
            'variables': round(h.get('ev', 0), 2), 'variables_ant': round(hp.get('ev', 0), 2),
            'imprevistos': round(h.get('imp', 0), 2), 'imprevistos_ant': round(hp.get('imp', 0), 2),
            'deudas': round(h.get('deu', 0), 2), 'ahorros': round(h.get('aho', 0), 2),
            'ahorros_ant': round(hp.get('aho', 0), 2), 'total': round(egr_ef, 2),
            'por_categoria': efectivo_por_categoria(db, yr, mi)},
        'tarjeta': {'total': round(tc, 2), 'anterior': round(tcp, 2),
                    'delta': round(tc - tcp, 2), 'cargado': tc > 0,
                    'por_categoria': comp},
        'efectivo': {'cierre': cierre, 'cierre_anterior': cierre_p,
                     'delta': round((cierre or 0) - (cierre_p or 0), 2)},
        'ahorro': {'esperado': aho_esperado, 'real': round(h.get('aho', 0), 2),
                   'cumplido': round(h.get('aho', 0), 2) + 0.01 >= aho_esperado,
                   'detalle_esperado': esperado},
        'inversiones': {'patrimonio': pat, 'patrimonio_anterior': pat_p,
                        'comparable': comparable,
                        'nota_comparable': ('' if comparable else
                            'Sin snapshot del mes anterior: los instrumentos cerrados se '
                            'borran del JSON, así que el patrimonio pasado no es reconstruible. '
                            'La comparación empieza el mes que viene.'),
                        'delta': (round(pat['total'] - pat_p['total'], 2) if comparable else None),
                        'tasa_promedio': tasa_prom, 'flujo': flujo_inv(db, yr, mi),
                        'eventos': eventos},
        'finca': {'meta': META_FINCA, 'acumulado': pat['total'],
                  'pct': round(pat['total'] / META_FINCA * 100, 1),
                  'aporte_mensual': aporte_mes, 'meses_faltantes': meses,
                  'fecha_estimada': fecha, 'fecha_estimada_anterior': fecha_p,
                  'meses_anterior': meses_p},
        'generado': datetime.datetime.now().isoformat(timespec='seconds'),
    }
    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)

    # Guardar el snapshot de este mes para que el proximo reporte pueda comparar
    if hist_path:
        historico['%04d-%02d' % (yr, mi + 1)] = dict(pat, efectivo=cierre,
                                                     fecha_estimada=fecha, meses_faltantes=meses)
        try:
            with open(hist_path, 'w', encoding='utf-8') as f:
                json.dump(historico, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print('aviso: no se pudo guardar el historico: %s' % e, file=sys.stderr)


if __name__ == '__main__':
    main()
