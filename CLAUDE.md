# Finanzas personales · Luis Miguel Ñaupari

App de control de ingresos, egresos e inversiones, orientada a comprar una finca
ganadera de ~$100.000 en Santo Domingo de los Tsáchilas. Un solo archivo HTML
sincronizado con Google Sheets vía Apps Script, publicado como PWA.

Última versión: **v41** · 2026-11-09

---

## Dónde vive cada cosa

| Qué | Dónde |
|---|---|
| Código vivo | Este repo, `index.html` (un solo archivo) · **es la única copia editable** |
| App publicada | https://lsmiguel91-ui.github.io/finanzas/ (GitHub Pages, desde `main`) |
| Base de datos | Google Sheet `1kCmVig1u4LlgcWsATOHMOuwDhSeXOmkSBdUDZoLiDMU`, hoja `datos` |
| Backend | Apps Script `1dAF8G9J0zPz6llx0B1XafwKwwQO9VBZR2lnc3Ouym1rIjf4EGYWo22Bt` |
| Respaldos fechados | OneDrive `LUIS MIGUEL IA APPS\_versiones\finanzas\` |
| Estados de cuenta TC | OneDrive `LUIS MIGUEL IA APPS\Estados de cuenta TC\` |
| Reportes mensuales | Google Drive, carpeta `1ExvMDEZzXsY2pM8L5ISfdZsKwemm1UFr` |
| Generador del reporte | `reportes/` en este repo |

La URL del Apps Script **no está en el código**: el repo es público y ese endpoint
no tiene autenticación. La app la pide una vez por dispositivo y la guarda en
`localStorage`.

---

## Reglas de trabajo (no negociables)

1. **El repositorio es la única copia viva.** OneDrive guarda solo respaldos
   fechados. Nunca editar un HTML suelto: dos copias editables se separan y el
   error aparece tarde.
2. **`APP_VERSION` (index.html) y `VERSION` (sw.js) suben en el mismo commit.**
   Si no, el dispositivo se queda en la versión vieja y el usuario trabaja con
   código antiguo creyendo que está actualizado.
3. **Verificar antes de entregar.** `node --check` sobre el bloque `<script>`, y
   para cualquier cambio de lógica, una prueba real en navegador (ver *Cómo
   probar*). Reproducir el fallo antes de arreglarlo.
4. **Claude no puede escribir en el Sheet**, solo leerlo. Todo cambio de datos se
   hace con una migración dentro de la app, que corre al cargar.
5. **Las migraciones llevan flag** (`db._migXxx`) y llaman a `save()`. Sin flag,
   reescriben los datos del usuario en cada carga.
6. Antes de tocar cualquier app del usuario que sincronice con Sheets/Drive,
   leer primero cómo lo resuelve esta, que ya funciona, en vez de escribir algo
   nuevo a ciegas.
7. Si un problema se repite tras varios intentos, parar y buscar la causa raíz
   en lugar de encadenar parches.

### Preferencias del usuario para este proyecto

- Español, respuestas cortas, sin introducciones ni cierres. En lo técnico: qué
  se cambió y por qué, **sin mostrar código ni volcados de terminal**.
- Preguntas numeradas en un solo mensaje, máximo dos rondas. Si delega una
  decisión, decidir como experto y decírselo.
- Avisar desde el inicio cuando algo no se puede hacer por falta de acceso, en
  vez de prometer y fallar.
- Señalar siempre los problemas o mejoras detectados, aunque no sean el tema.
- Los entregables de tareas programadas van a **Google Drive, no a su PC**: la
  computadora puede estar apagada cuando la tarea corre.

---

## Cómo leer la base de datos

El Sheet guarda **un solo JSON partido en trozos de 40.000 caracteres** en las
celdas A1, A2, A3… de la hoja `datos` (el límite de GAS es 50.000 por celda).

```
download_file_content(fileId, exportMimeType='text/csv')
→ base64 → CSV → concatenar en orden las celdas no vacías de la col. A → json.loads
```

`read_file_content` **devuelve truncado**: no usarlo para esto.

### Estructura

```
saldoInicial          número, punto de partida de la cadena (mayo 2026 = 170,80)
movimientos[]         {id, fecha, monto, categoria, descripcion, tipo,
                       sinFactura?, flujoInv?}
hist[]                {a, m, ing, ev, imp, deu, aho} — recalculado, no fuente
inv.ganado[]          lotes de ganado
inv.plazo[]           plazos fijos (se ELIMINAN al vencer)
inv.metas[]           metas de ahorro con tramosAporte[], aportesExtra[], retiros[]
inv.ganadoVinculados[]
diferidos[]           tracker de compras diferidas de la TC
tcPagos[]             estados de cuenta importados, con detalle[] por consumo
invCerradas[]
_mig*                 flags de migración
```

**`hist` es derivado**: `recalcHistMes()` lo recalcula desde `movimientos`. Nunca
escribir en `hist` directamente.

**Los consumos de tarjeta NO están en `movimientos`**, viven en el `detalle[]` de
`tcPagos`. Por eso sumar ambos no duplica.

---

## Decisiones tomadas (no revertir)

- Netlify descartado por cobro. GitHub Pages es gratis.
- PF y metas vencidas se eliminan al cerrar. **Consecuencia importante**: el
  patrimonio de meses pasados no se puede reconstruir desde el JSON, por eso el
  reporte mensual guarda un snapshot aparte.
- Retorno de lote de ganado = capital + 50% de la utilidad (modelo con socio).
- Retornos y reinversiones (`flujoInv`) quedan fuera de las estadísticas pero
  dentro del cash.
- Las categorías desconocidas suman a Estilo de Vida y avisan: lo prioritario es
  que el total de egresos y el cash cuadren.
- La TC **no se proyecta**. Se espera el estado de cuenta real; el usuario no
  quiere estimaciones ahí.
- Notion fuera de la documentación de este y los demás proyectos.
- Paleta verde esmeralda.

---

## Categorías y gastos deducibles (SRI Ecuador)

El selector arranca con el grupo **DEDUCIBLES SRI** y Alimentación primero: es lo
que más registra.

`CAT_DEDUCIBLES = ['Vivienda','Alimentación','Salud','Educación y cultura','Vestimenta','Turismo']`

Son las seis categorías que el SRI acepta. Cine, libros y museos van en
*Educación y cultura*, no en Entretenimiento, porque ahí sí son deducibles.

**Categoría y factura son cosas distintas.** La categoría dice en qué gastó; el
campo `sinFactura` dice si hay respaldo. La comida del reparto es alimentación
pero no da comprobante. El panel de deducibles muestra lo facturado como cifra
principal y lo gastado como contexto; la rebaja del 18% se calcula sobre lo
facturado.

La casilla del formulario aparece solo en categorías deducibles y viene marcada
por defecto. Se guarda solo la excepción (`sinFactura: true`).

Criterio aplicado al histórico (migración v39): **tarjeta = con factura,
efectivo = sin factura**. v40 lo reaplicó tras perderse en la hoja, solo a lo
registrado antes de publicar v39 (4-nov-2026 15:15); lo posterior lo decide la casilla.

`TC_CAT_MAP` reconoce los comercios reales del usuario y clasifica los consumos
al importar el PDF. Ampliarlo cuando aparezcan comercios nuevos en "Otros".

---

## Problemas resueltos (no reinventar)

| Síntoma | Causa | Arreglo |
|---|---|---|
| Un plazo fijo creado en el celular desapareció | El refresco automático aplicaba una lectura que salió de la hoja **antes** del último guardado, y pisaba lo recién registrado | v33: `_saveSeq`/`_savePend`; la lectura se descarta si hubo un guardado después de iniciarla |
| Saldo inflado a inicio de mes | El ahorro mensual (débito automático) no se restaba hasta registrarlo a mano | v34: `ahorrosPendientesMes()` lo descuenta; si ya está registrado da 0, sin doble conteo |
| Proyección de $681 con un gasto de $23,50 | Usaba el ritmo del propio mes, que el día 1 no existe | v35: mediana diaria de los 6 meses anteriores mezclada con el ritmo del mes, ponderando por el día |
| 59% de la tarjeta en "Otros" | Faltaban categorías (Vestimenta era el mayor rubro y no existía) | v36: categorías alineadas al SRI |
| $796,47 fantasma en la TC de noviembre | `periodoImport` salía de la fecha de importación, no del corte del estado | v38 |
| Consumos fechados un año en el futuro | Las filas de diferidos llevan la fecha de la **compra**, y el parser les ponía el año del estado | v38: `anioDe()` — si el mes es posterior al del corte, es del año anterior |
| Cuotas de diferidos en el mes equivocado | Se imputaban al mes de la compra, no al del cobro | v38: se imputan a la fecha de corte; la compra queda en `fechaCompra` |
| TC importada que no persistía | Límite de 50.000 caracteres por celda del GAS | GAS v2 con almacenamiento partido |
| Valores que "cambian solos" | Migraciones corriendo después de `recalcTodo()` | Migraciones **antes** de `recalcTodo()` |
| Desfases de fecha | UTC: `new Date('YYYY-MM-DD')` cae el día anterior en Ecuador (UTC-5) | `parseLocalDate()` y `today()` locales, siempre |
| Un dispositivo en v28 y otro en v29 | GitHub Pages sirve con `max-age=600` | v30: `cache:'no-store'` y `updateViaCache:'none'` |
| Casilla «con factura» oculta al abrir el formulario con Alimentación ya elegida | Solo se evaluaba al cambiar la categoría | v41: `onCatChange()` al arrancar y en `setTipo()` |
| Elegir otro mes en el Dashboard no cambiaba la tabla de movimientos hasta cambiar de pestaña | El selector llamaba solo a `refreshDash()`; la tabla la pinta `renderReg()` | v41: el selector llama a ambas, y el resumen sobre la tabla sigue el mismo mes |
| Marcas «sin factura» de v39 perdidas (facturado $5.553 en vez de $3.849) con la bandera `_migFacturaV39` puesta | Una escritura con datos anteriores a v39 (pestaña vieja abierta o sync de Ganadería sin bloqueo) pisó la hoja; al leer, `Object.assign` conservó la bandera **local** y la migración no volvió a correr | v40: `load()` suelta las claves `_*` que la hoja no trae; `migrarFacturaV40()` repara; `db._appVer` + recarga si la hoja la escribió una versión más nueva; lectura al volver a la app |

**Hueco conocido, aún abierto**: si el guardado falla por falta de señal, no hay
reintento ni marca persistente; la siguiente lectura buena se lleva el cambio. El
usuario lo conoce y decidió no abordarlo todavía.

---

## Reporte mensual (tarea programada)

Corre el **día 3 de cada mes a las 19:34** (America/Guayaquil) y reporta el mes
anterior. Trigger `trig_01J9NUMxxUSxyK47txEdH4Qc`. Corre en la nube, sin depender
de la computadora del usuario.

```
reportes/calc_finanzas.py   calcula los números desde el JSON. No opina.
                            uso: calc_finanzas.py db.json AÑO MES [historico.json]
reportes/reporte_finanzas.py  arma el PDF desde analisis.json
```

La separación es deliberada: el script calcula, Claude escribe los textos. Así el
reporte no inventa cifras y Claude no hace aritmética.

**El gráfico se dibuja vectorial con reportlab, nunca como PNG de matplotlib.**
Con imagen el PDF pesaba 45 KB y subirlo a Drive era inviable: hay que
codificarlo en base64 y son ~60.000 caracteres que fallan al transcribirse.
Vectorial pesa 8 KB.

`historico_patrimonio.json` guarda el patrimonio mes a mes. Es necesario porque
los instrumentos cerrados se borran del JSON y el pasado no es reconstruible.
**Fuente única: el repo** (`reportes/historico_patrimonio.json`); el trigger lo
sube con el conector de GitHub. El archivo de Drive
(`1cArrD5GSh_GfNXnBoFCrlXm6JqY-ko5f`) es una copia congelada de oct-2026 y no se
actualiza: el conector de Drive no reescribe contenido.

---

## Cómo probar un cambio

Hay un patrón que funciona bien y conviene reutilizar: servir el repo en local,
abrirlo con Playwright interceptando las peticiones al Apps Script y devolviendo
un `db` controlado (o el real, descargado del Sheet).

Sin Playwright (no está instalado en Windows) sirve igual un servidor Python que
entregue el repo y simule `/gas` (`leer`/`guardar` sobre un JSON en disco), con
`finanzas_gas_url` apuntando a él en `localStorage`, y el navegador integrado.
Así se probó v40.

```bash
cd <repo> && python3 -m http.server 8099 --bind 127.0.0.1 &
node test/<prueba>.js 8099
```

Así se reprodujeron, antes de arreglarlos, la carrera del plazo fijo perdido y el
fantasma de los $796,47. Para un cambio de cálculo, comprobar siempre que **la
suma total de egresos y el cash de cada mes no cambien** si solo se reclasifica.

---

## Estado al 2026-11-08

- v40 publicada el 2026-11-08 (respaldo `finanzas_2026-11-08_v40.html`).
- GAS v4 (con bloqueo) implementado por el usuario el 2026-11-09.
- v41 lista: casilla de factura visible al abrir y selector de mes que refresca la tabla.
- Estados de cuenta cargados: dic-2025 a oct-2026.
- Gasto deducible 2026: **$3.849,14 facturado** de $5.562,21 gastado (cifra que
  v40 restituye; en la hoja hoy figura $5.553,96 hasta que se abra v40).
- Patrimonio: ~$19.269 (ganado $10.000, PF $1.000, metas $8.269). 19,3% de la
  meta de $100.000; al ritmo actual, agosto de 2030.
- Diferidos activos: PMZ Mirgor (hasta may-2027), Sony y Nike (dic-2026).
- El reporte de octubre se generó y archivó solo el 5 de noviembre.

### Pendientes

1. **Vivienda quedó con $0 facturado** ($541,10 en efectivo). Si ahí hay planillas
   de luz, agua o internet, sí tienen factura electrónica y el usuario debería
   marcarlas; si son pagos familiares, está bien así.
2. El reporte del coach sigue generando el gráfico como imagen; si falla su
   subida a Drive, la causa y el arreglo son los mismos que aquí.
3. Categoría *Cuidado personal* (peluquería, aseo, gimnasio): propuesta y
   descartada por ahora, el usuario dejó esos gastos en "Otros". Retomar si
   "Otros" vuelve a crecer.
