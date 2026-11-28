# Finanzas personales

App de control de ingresos, egresos e inversiones. Un solo archivo HTML
sincronizado con Google Sheets vía Apps Script, publicado como PWA.

Última publicación: **App actualizada 28-nov-2026** (interno v48)

> **El repositorio es público.** Aquí no van cifras, ids de archivos ni datos del
> usuario: todo eso está en el archivo privado de Google Drive `finanzas_privado_AAAA-MM-DD.md`
> (en la PC, también en `CLAUDE.local.md`, ignorado por git). Tampoco se suben
> datos al repo: los datos viven solo en la hoja y en Google Drive.

---

## Dónde vive cada cosa

| Qué | Dónde |
|---|---|
| Código vivo | Este repo, `index.html` (un solo archivo) · **es la única copia editable** |
| App publicada | https://lsmiguel91-ui.github.io/finanzas/ (GitHub Pages, desde `main`) |
| Base de datos, backend, reportes, histórico, estado y pendientes | Archivo privado en Google Drive: buscar por título `finanzas_privado` y usar el de fecha más reciente (`finanzas_privado_AAAA-MM-DD.md`). En la PC existe además `CLAUDE.local.md` (fuera del repo), que puede estar atrasado |
| Respaldo de cada versión | El historial de git de `main`. **No se crean tags** |
| Generador del reporte | `reportes/` en este repo (solo código, sin datos) |

**Orden en Drive (desde 18-nov-2026):** todo lo de este proyecto (hoja, archivo privado, copia del GAS,
carpeta de reportes mensuales) está en la carpeta `Finanzas` de Drive. Todo archivo nuevo, incluido cada
`finanzas_privado_AAAA-MM-DD.md`, se crea **dentro de esa carpeta** (`parentId`), nunca suelto en la raíz.
Mover no cambia los ids.

La URL del Apps Script **no está en el código**: el repo es público y ese endpoint
no tiene autenticación. La app la pide una vez por dispositivo y la guarda en
`localStorage`.

---

## Reglas de trabajo (no negociables)

1. **El repositorio es la única copia viva y su historial de git es el respaldo.**
   No crear tags ni pedirle al usuario nada en git (regla del usuario, 18-nov-2026).
   Los respaldos fechados de OneDrive anteriores al 18-nov-2026 quedan como archivo
   histórico. Nunca editar un HTML suelto: dos copias editables se separan y el
   error aparece tarde.
2. **En cada publicación suben juntos, en el mismo commit: `APP_VERSION`
   (index.html), `VERSION` (sw.js) y `APP_FECHA` (index.html, fecha del día).**
   El número es solo interno (caché y control entre equipos); el usuario ve
   «App actualizada DD-mmm-AAAA», que sale de `APP_FECHA`. Si no suben juntos, el
   dispositivo se queda en la versión vieja creyendo que está actualizado.
   **Al publicar, decirle al usuario solo: «verifica que diga App actualizada
   <fecha de hoy>»**.
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
saldoInicial          número, punto de partida de la cadena (mayo 2026)
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
| Proyección del mes desproporcionada el día 1 | Usaba el ritmo del propio mes, que el día 1 no existe | v35: mediana diaria de los 6 meses anteriores mezclada con el ritmo del mes, ponderando por el día |
| 59% de la tarjeta en "Otros" | Faltaban categorías (Vestimenta era el mayor rubro y no existía) | v36: categorías alineadas al SRI |
| Monto fantasma en la TC del mes en curso | `periodoImport` salía de la fecha de importación, no del corte del estado | v38 |
| Consumos fechados un año en el futuro | Las filas de diferidos llevan la fecha de la **compra**, y el parser les ponía el año del estado | v38: `anioDe()` — si el mes es posterior al del corte, es del año anterior |
| Cuotas de diferidos en el mes equivocado | Se imputaban al mes de la compra, no al del cobro | v38: se imputan a la fecha de corte; la compra queda en `fechaCompra` |
| TC importada que no persistía | Límite de 50.000 caracteres por celda del GAS | GAS v2 con almacenamiento partido |
| Valores que "cambian solos" | Migraciones corriendo después de `recalcTodo()` | Migraciones **antes** de `recalcTodo()` |
| Desfases de fecha | UTC: `new Date('YYYY-MM-DD')` cae el día anterior en Ecuador (UTC-5) | `parseLocalDate()` y `today()` locales, siempre |
| Un dispositivo en v28 y otro en v29 | GitHub Pages sirve con `max-age=600` | v30: `cache:'no-store'` y `updateViaCache:'none'` |
| Casilla «con factura» oculta al abrir el formulario con Alimentación ya elegida | Solo se evaluaba al cambiar la categoría | v41: `onCatChange()` al arrancar y en `setTipo()` |
| Elegir otro mes en el Dashboard no cambiaba la tabla de movimientos hasta cambiar de pestaña | El selector llamaba solo a `refreshDash()`; la tabla la pinta `renderReg()` | v41: el selector llama a ambas, y el resumen sobre la tabla sigue el mismo mes |
| Movimientos de 2027 invisibles (F3) | `dYear` tenía opciones fijas hasta 2026 | v42: opciones de 2024 al año en curso, generadas al arrancar |
| Botón «Registrar retorno» de lotes de la Bitácora daba `ReferenceError`; retorno recortado dos veces (F4) | ids de texto (`gld_…`) sin comillas en el `onclick`; `retornoGanado` aplicaba el 50% a un `ventaReal` que ya es capital + 50% | v42: `jsArg()` para todo id en `onclick`; lotes `origen:'ganaderia'` usan `ventaReal` tal cual; los gastos `glm_…` muestran «🐄 Bitácora» en vez de botones |
| Montos de la TC ≥ $1.000 leídos como $1 (F5) | `[\d.]+` cortaba en la coma de miles ("$ 1,301.17") | v42: `numBG()` y cuadre contra «Consumos / débitos titular» del PDF antes de importar; verificado con los 7 estados reales |
| Aporte 13 en metas de 12 meses; ahorros no confirmados olvidados al cambiar de mes (F6) | Se comparaba con la fecha de fin; el aviso solo miraba el mes en curso | v42: aporta del mes de inicio a inicio+plazo−1; pendientes desde nov-2026 se arrastran hasta registrar o descartar (✕, `db.ahorrosDescartados`) |
| «Con factura» y «nunca decidido» eran el mismo dato (F7) | Solo se guardaba `sinFactura:true` | v42: se guarda `sinFactura` explícito (true/false) y v39 también tiene tope de fecha. Las correcciones hechas en v41 (campo borrado) no se distinguen |
| Retornos de inversión contados como ingreso ordinario | Anotados a mano como «Retorno Inversión» sin `flujoInv` | v42–v43: `migrarSalidaAgo26()` y `migrarRetornosFlujoV43()`; al registrar un retorno a mano se marca solo. El cash no cambia |
| Datos financieros reales en el repo público (F8) | Valores por defecto de `db`, comentarios con cifras, histórico de patrimonio y este archivo | v43: `db` por defecto vacío, ejemplos ficticios, histórico a Drive, lo privado a `CLAUDE.local.md` |
| Marcas «sin factura» de v39 perdidas (todo contaba como facturado) con la bandera `_migFacturaV39` puesta | Una escritura con datos anteriores a v39 (pestaña vieja abierta o sync de Ganadería sin bloqueo) pisó la hoja; al leer, `Object.assign` conservó la bandera **local** y la migración no volvió a correr | v40: `load()` suelta las claves `_*` que la hoja no trae; `migrarFacturaV40()` repara; `db._appVer` + recarga si la hoja la escribió una versión más nueva; lectura al volver a la app |
| Señal de venta del lote decía «No aceptes menos de» el precio normal del mercado, por debajo de lo pagado; y «VENDE» a un lote recién comprado | La señal viene de Ganadería y solo mira el mercado, no el costo del lote | v44: una tarjeta por lote; piso = mayor entre mercado y `senal.precioEquilibrio` (más `precioObjetivo` y `capitalRecuperado`), que debe enviar Ganadería; si el lote no llegó a su fecha de venta dice «En engorde» |
| El Panel no reflejaba la TC recién importada | Solo se repintaba al cambiar de pestaña o con `repintarTodo`; `sincronizar()` y otros caminos refrescaban solo el Dashboard. Y la gráfica de cash mostraba la TC solo como un salto al final del mes | v47: `pnRefrescar()` (agrupado, solo si el Panel está a la vista) desde `save()`, `refreshDash()` y `confirmarTC()`; línea «💳 Descontando la tarjeta» con cada consumo del estado en su día real, que cierra en `cashRealFinMes` |
| Gastos de lote de la Bitácora («gll_…») contados como consumo («Ganado») en vez de reinversión | Ganadería los manda con `categoria:'Reinversión'` y `flujoInv:true`, pero `syncEgresosGanaderia` del Apps Script (hasta v5) fijaba `'Ganado'` y descartaba `flujoInv` | v48: `migrarGllReinversionV48()` repara los existentes (solo categoría y `flujoInv`); `esFlujoInv` y `es_flujo_inv` del reporte reconocen el prefijo `gll_` aunque un script viejo los reescriba; Apps Script v6 respeta `categoria`/`flujoInv` del egreso (cambio en Drive, lo pega el usuario). Verificado: cash de may–nov idéntico; solo pasan de Imprevistos a flujo de inversiones |

### Sincronización desde v42 (auditoría del 15-nov-2026, hallazgos F1–F9)

Cada equipo guarda dos copias en `localStorage`: **local** (`finanzas_drive_v1`, lo
que se ve y edita) y **base** (`finanzas_base_v1`, la última versión conocida de la
hoja, con su revisión). Lo que difiere entre ambas son cambios aún no subidos.

- **F1**: `save()` no sube nada hasta que hubo una lectura correcta en la sesión
  (`_lecturaOk`). Una lectura con 0 movimientos frente a ≥20 locales se rechaza.
- **F2**: antes de subir se combina con la hoja (`merge3`, fusión de tres vías por
  `id` + número de aparición; las banderas `_mig*` las manda la hoja y las
  migraciones se reevalúan). Con GAS v5 la hoja tiene revisión (`PropertiesService`
  'rev'); un guardado sobre una revisión vieja vuelve con `conflicto:true` y la app
  relee, combina y reintenta. Con GAS v4 la app relee y combina justo antes de cada
  guardado (ventana de ~1 s en vez de 5 min).
- **F9**: un guardado fallido queda pendiente, sobrevive a cerrar la app y se
  reintenta (30 s, evento `online`, al volver a la app y al leer). Ya no hay hueco
  abierto por falta de señal.
- Las migraciones están en una sola función, `correrMigraciones()`.


## Panel (pestaña 🚀, desde v46)

Gráficas vivas para el celular, sin cifras propias: todo sale de las funciones del
Dashboard (`efectivoHoy`, `cashRealFinMes`, `calcProyeccion`, `ahorrosEsperadosMes`,
`calcMetaConRetiros`, `saldoFinalMeta`, `retornoPF`). Funciones `pn*` y `renderPanel*`.

- **Indicadores**: efectivo hoy, egresos del mes (los mismos del Dashboard, con su
  proyectado), ingreso pasivo por día y gastos fijos con su cobertura.
- **Cash del mes día a día**: cada movimiento sube o baja la línea, rotulado (+/−) y
  con su detalle al tocar el punto. Cierra exacto en `efectivoHoy`; la parte punteada
  es el egreso proyectado que ya calcula la app (`calcProyeccion`) y la TC el último
  día, y cierra exacto en `cashRealFinMes`. Segunda línea: el cash menos la deuda de la
  tarjeta (consumos del estado que se paga este mes, cada uno en su día; lo comprado
  antes del mes cuenta desde el día 1). **No se usan promedios para el día a día**
  (decisión del usuario, 21-nov-2026).
- **Pasivo contra gastos**: rendimiento del capital por fuente frente a dos líneas:
  gastos fijos (regla de «fijo» de la proyección, sin ahorro) y gasto total típico
  (efectivo + TC, sin ahorro). **Mediana de los últimos 3 meses cerrados, por
  categoría para los fijos**: un gasto que dejó de repetirse (el carro ya pagado) no
  cuenta. El promedio simple daba >$2.000 por un pago único y el usuario lo rechazó.
- **¿Qué hago con el dinero que se libera?**: metas, PF y lotes que vencen en 12
  meses (o un monto manual). Compara todo a ganado, todo a PF y la recomendación, más
  el mal año del ganado (−25 %, la misma escala de la tabla de riesgo de Inversiones).
  Recomendación: primero el fondo de emergencia (3 meses de gasto típico; cuenta las
  metas con «emergencia» en el nombre), luego ganado hasta el tope del perfil, el
  resto a PF.
- **Portafolio**: reparto actual contra Conservador 20/50/30 (el de Inversiones),
  Balanceado 40/40/20 y Crecimiento 60/25/15: ganancia en año normal y en mal año.
  Se recomienda Conservador mientras falte fondo de emergencia; luego Balanceado.
- Supuestos de `pnProyectar`: ganado al rendimiento real de los lotes vendidos (tu
  parte, vía `retornoGanado`), PF y metas a su `tasaA`, todo reinvertido; las metas se
  renuevan con su aporte actual. **Al vencer, cada meta (salvo el fondo de emergencia)
  entrega su saldo y se reparte como la recomendación** (emergencia → ganado hasta el
  tope del perfil → PF); `pnProyectar(m,sim,{reparto:false})` da el caso sin reparto y
  la nota muestra ambas fechas (pedido del usuario, 21-nov-2026: sin reparto el morado
  de metas dominaba y parecía que convenía invertir en metas). Meta de la finca:
  `PN_META_FINCA`.
- Paleta de series validada para el fondo oscuro: ganado `#c97d26`, PF `#1fa196`,
  metas `#8a6be6`; recomendado `#f2c94c`, mal año `#e07a6a`.
- Para capturar pantallas en pruebas: hacerlo por tarjeta con la gráfica a la vista;
  en una captura de página completa las gráficas fuera de pantalla salen a medio animar.

---

## Reporte mensual (tarea programada)

Corre el día 3 de cada mes en la nube (trigger y hora en el archivo privado de Drive) y
reporta el mes anterior, sin depender de la computadora del usuario.

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

El histórico de patrimonio (mes a mes) es necesario porque los instrumentos
cerrados se borran del JSON y el pasado no es reconstruible. **Vive en Google
Drive, nunca en el repo** (detalles en el archivo privado de Drive). `.gitignore` bloquea
`historico_patrimonio*.json`.

---

## Cómo probar un cambio

Hay un patrón que funciona bien y conviene reutilizar: servir el repo en local,
abrirlo con Playwright interceptando las peticiones al Apps Script y devolviendo
un `db` controlado (o el real, descargado del Sheet).

Sin Playwright (no está instalado en Windows) sirve igual un servidor Python que
entregue el repo y simule `/gas` (`leer`/`guardar` sobre un JSON en disco), con
`finanzas_gas_url` apuntando a él en `localStorage`, y el navegador integrado.
Así se probó v40.

Para v42 se usó además el arnés del auditor en Node (`harness.js`: carga el
`<script>` de la app en una VM con DOM y `fetch` simulados) y el Apps Script v5
real ejecutado en otra VM con `SpreadsheetApp`/`LockService`/`PropertiesService`
simulados (prueba extremo a extremo de conflictos). Comprobado: cash, egresos, TC y
deducibles de may–nov 2026 idénticos entre v41 y v42 con los datos reales.
Los datos de prueba se descargan a la carpeta temporal, nunca al repo.

```bash
cd <repo> && python3 -m http.server 8099 --bind 127.0.0.1 &
node test/<prueba>.js 8099
```

Así se reprodujeron, antes de arreglarlos, la carrera del plazo fijo perdido y el
monto fantasma de la TC. Para un cambio de cálculo, comprobar siempre que **la
suma total de egresos y el cash de cada mes no cambien** si solo se reclasifica.

---

## Estado y pendientes

En el archivo privado de Google Drive (`finanzas_privado_AAAA-MM-DD.md`, el más
reciente). Al cerrar una etapa, crear uno nuevo con la fecha del día y el contenido
completo actualizado (el conector de Drive no reescribe archivos).

---

## Dónde se trabaja (desde 18-nov-2026: en la nube)

Esta app se maneja desde una sesión de Claude Code en la nube (claude.ai/code o la
app Claude del celular), para poder trabajar con la PC apagada.
- **Al empezar:** `git pull` de `main` y leer el archivo privado de Drive. Si el
  conector de Google Drive no está disponible, decirlo al inicio en vez de suponer
  datos.
- **Una sola sesión a la vez.** No trabajar Finanzas en la PC y en la nube al mismo
  tiempo.
- **Al terminar:** todo cambio verificado queda subido a `main` (sin tags); nunca
  dejar trabajo solo en la VM, porque se borra.
- **Pruebas:** Playwright/Chromium en la VM (instalar con pip o npm si falta), con
  el patrón de *Cómo probar*.
- **Publicar solo con aprobación del usuario.** Hallazgos y propuestas en tabla
  (problema, causa, solución, ¿aprueba?).
- **Repo público:** ningún dato personal, id ni cifra en el repo; van al archivo
  privado de Drive.
