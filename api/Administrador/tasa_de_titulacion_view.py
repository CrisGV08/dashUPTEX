# tasa_de_titulacion_view.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.db import transaction
from django.db.models import F
from api.models import (
    TasaTitulacion,
    ProgramaEducativoAntiguo,
    ProgramaEducativoNuevo,
)
import json
import io
import math
import pandas as pd
import openpyxl

# ---- Config columnas esperadas en Excel ----
COLUMNS = [
    "programa_tipo",                    # 'ANTIGUO' o 'NUEVO'
    "programa_id",                      # PK string (ej. 'ISC')
    "programa_nombre",                  # informativo
    "anio_ingreso",
    "matricula_ingreso",
    "egresados",
    "eficiencia_terminal_porcentaje",   # si viene vacío, se calcula
    "titulados",
    "tasa_titulacion",                  # si viene vacío, se calcula
]

# ---- Helpers de tipado y porcentajes ----
def _to_int(x):
    try:
        if pd.isna(x): return 0
        v = int(float(x))
        return max(v, 0)
    except Exception:
        return 0

def _to_float(x):
    try:
        if pd.isna(x): return 0.0
        v = float(x)
        if math.isnan(v) or math.isinf(v):
            return 0.0
        return v
    except Exception:
        return 0.0

def _pct(num, den):
    if den and den != 0:
        return round((num / den) * 100.0, 2)
    return 0.0

def _clip_pct(v):
    return max(0.0, min(100.0, float(v)))

# =========================
# VISTA PRINCIPAL (listar + filtros + edición en línea)
# =========================
def tasa_de_titulacion_view(request):
    registros = (
        TasaTitulacion.objects
        .select_related("programa_antiguo", "programa_nuevo")
        .order_by(F('anio_ingreso').asc(), "programa_antiguo__id", "programa_nuevo__id")
    )

    # --- Filtros ---
    filtro_anio = request.GET.get('anio_ingreso')  # ej. "2022"
    filtro_tipo = request.GET.get('tipo_programa') # 'antiguo' | 'nuevo'

    if filtro_anio:
        try:
            registros = registros.filter(anio_ingreso=int(filtro_anio))
        except ValueError:
            messages.warning(request, "El filtro de año no es válido.")

    if filtro_tipo == 'antiguo':
        registros = registros.filter(programa_antiguo__isnull=False)
    elif filtro_tipo == 'nuevo':
        registros = registros.filter(programa_nuevo__isnull=False)

    # --- Guardar cambios desde la tabla (por fila) ---
    if request.method == 'POST' and 'guardar' in request.POST:
        try:
            id_registro = int(request.POST.get('guardar'))
            r = TasaTitulacion.objects.get(id=id_registro)

            r.matricula_ingreso = _to_int(request.POST.get(f'matricula_{id_registro}', 0))
            r.egresados = _to_int(request.POST.get(f'egresados_{id_registro}', 0))
            r.titulados = _to_int(request.POST.get(f'titulados_{id_registro}', 0))

            if r.matricula_ingreso > 0:
                r.eficiencia_terminal_porcentaje = _clip_pct(_pct(r.egresados, r.matricula_ingreso))
                r.tasa_titulacion = _clip_pct(_pct(r.titulados, r.matricula_ingreso))
            else:
                r.eficiencia_terminal_porcentaje = 0.0
                r.tasa_titulacion = 0.0

            r.save()
            messages.success(request, "✅ Registro actualizado correctamente.")
            return redirect('tasa_de_titulacion')
        except Exception as e:
            messages.error(request, f"❌ Error al actualizar: {e}")

    # --- Datos auxiliares para filtros ---
    anios_disponibles = (
        TasaTitulacion.objects
        .values_list('anio_ingreso', flat=True)
        .distinct()
        .order_by('anio_ingreso')
    )
    programas_antiguos = ProgramaEducativoAntiguo.objects.all()
    programas_nuevos = ProgramaEducativoNuevo.objects.all()

    # --- Datos para gráficas (JS) ---
    datos_json = []
    for r in registros:
        programa = r.programa_antiguo.nombre if r.programa_antiguo else (r.programa_nuevo.nombre if r.programa_nuevo else "SIN PROGRAMA")
        datos_json.append({
            'programa': programa,
            'anio_ingreso': r.anio_ingreso,
            'matricula': r.matricula_ingreso,
            'egresados': r.egresados,
            'titulados': r.titulados,
            'eficiencia_terminal': r.eficiencia_terminal_porcentaje,
            'tasa_titulacion': r.tasa_titulacion
        })

    context = {
        'registros': registros,
        'anios': anios_disponibles,
        'programas_antiguos': programas_antiguos,
        'programas_nuevos': programas_nuevos,
        'filtro_anio': filtro_anio,
        'filtro_tipo': filtro_tipo,
        'datos_json': json.dumps(datos_json),
    }
    return render(request, 'tasa_de_titulacion.html', context)

# =========================
# DESCARGA PLANTILLA (con datos actuales + hoja "Instrucciones")
# =========================
def descargar_plantilla_tasa_titulacion(request):
    qs = (
        TasaTitulacion.objects
        .select_related("programa_antiguo", "programa_nuevo")
        .order_by("anio_ingreso", "programa_antiguo__id", "programa_nuevo__id")
    )

    rows = []
    for r in qs:
        if r.programa_antiguo:
            tipo = "ANTIGUO"
            pid = r.programa_antiguo.id
            pnombre = r.programa_antiguo.nombre
        else:
            tipo = "NUEVO"
            pid = r.programa_nuevo.id if r.programa_nuevo else ""
            pnombre = r.programa_nuevo.nombre if r.programa_nuevo else ""

        rows.append({
            "programa_tipo": tipo,
            "programa_id": pid,
            "programa_nombre": pnombre,
            "anio_ingreso": r.anio_ingreso,
            "matricula_ingreso": r.matricula_ingreso,
            "egresados": r.egresados,
            "eficiencia_terminal_porcentaje": r.eficiencia_terminal_porcentaje,
            "titulados": r.titulados,
            "tasa_titulacion": r.tasa_titulacion,
        })

    df_datos = pd.DataFrame(rows, columns=COLUMNS)
    if df_datos.empty:
        df_datos = pd.DataFrame(columns=COLUMNS)

    instrucciones = [
        ["Columna", "Descripción", "Obligatorio", "Ejemplo / Valores"],
        ["programa_tipo", "Tipo de programa educativo", "Sí", "ANTIGUO | NUEVO"],
        ["programa_id", "PK del programa (texto)", "Sí", "ISC, IM, ..."],
        ["programa_nombre", "Solo informativo", "No", "Ingeniería en Sistemas Computacionales"],
        ["anio_ingreso", "Año de ingreso (1990-2100)", "Sí", "2018"],
        ["matricula_ingreso", "Entero ≥ 0", "Sí", "120"],
        ["egresados", "Entero ≥ 0", "Sí", "90"],
        ["eficiencia_terminal_porcentaje", "% (0–100); si vacío se calcula", "No", ""],
        ["titulados", "Entero ≥ 0", "Sí", "70"],
        ["tasa_titulacion", "% (0–100); si vacío se calcula", "No", ""],
    ]
    df_info = pd.DataFrame(instrucciones[1:], columns=instrucciones[0])

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_datos.to_excel(writer, index=False, sheet_name="TasaTitulacion")
        df_info.to_excel(writer, index=False, sheet_name="Instrucciones")
    buffer.seek(0)

    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=plantilla_tasa_titulacion.xlsx'
    return response

# =========================
# SUBIR EXCEL (validaciones + upsert atómico)
# =========================
def subir_excel_tasa_titulacion(request):
    if request.method != 'POST' or 'archivo_excel' not in request.FILES:
        messages.error(request, "No se recibió el archivo.")
        return redirect('tasa_de_titulacion')

    archivo = request.FILES['archivo_excel']

    # Lee con pandas para validar columnas y tipos
    try:
        df = pd.read_excel(archivo, engine="openpyxl")
    except Exception as e:
        messages.error(request, f"❌ Error leyendo Excel: {e}")
        return redirect('tasa_de_titulacion')

    faltantes = [c for c in COLUMNS if c not in df.columns]
    if faltantes:
        messages.error(request, f"Faltan columnas en el Excel: {', '.join(faltantes)}")
        return redirect('tasa_de_titulacion')

    df = df[COLUMNS].copy()
    df["programa_tipo"] = df["programa_tipo"].astype(str).str.upper().str.strip()
    df["programa_id"] = df["programa_id"].astype(str).str.strip()

    for col in ["anio_ingreso", "matricula_ingreso", "egresados", "titulados"]:
        df[col] = df[col].apply(_to_int)
    for col in ["eficiencia_terminal_porcentaje", "tasa_titulacion"]:
        df[col] = df[col].apply(_to_float)

    # -------- PASADA 1: VALIDAR TODO --------
    errores = []
    vistos = set()  # detectar duplicados dentro del archivo
    filas_ok = []

    def add_err(idx_excel, msg):
        errores.append(f"Fila {idx_excel}: {msg}")

    for idx_df, row in df.iterrows():
        idx_excel = idx_df + 2  # +2 por encabezado en fila 1

        tipo = row["programa_tipo"]
        pid = row["programa_id"]
        anio = row["anio_ingreso"]
        mat = row["matricula_ingreso"]
        egr = row["egresados"]
        tit = row["titulados"]
        eff = row["eficiencia_terminal_porcentaje"]
        tasa = row["tasa_titulacion"]

        # Reglas
        if tipo not in ("ANTIGUO", "NUEVO"):
            add_err(idx_excel, "programa_tipo debe ser 'ANTIGUO' o 'NUEVO'.")
            continue
        if not pid:
            add_err(idx_excel, "programa_id vacío.")
            continue
        if not (1990 <= anio <= 2100):
            add_err(idx_excel, f"anio_ingreso fuera de rango (1990-2100): {anio}.")
            continue
        if mat < 0 or egr < 0 or tit < 0:
            add_err(idx_excel, "valores numéricos deben ser ≥ 0.")
            continue

        # Catálogo
        prog_ant = prog_nvo = None
        if tipo == "ANTIGUO":
            prog_ant = ProgramaEducativoAntiguo.objects.filter(pk=pid).first()
            if not prog_ant:
                add_err(idx_excel, f"programa_id '{pid}' no existe en ProgramaEducativoAntiguo.")
                continue
        else:
            prog_nvo = ProgramaEducativoNuevo.objects.filter(pk=pid).first()
            if not prog_nvo:
                add_err(idx_excel, f"programa_id '{pid}' no existe en ProgramaEducativoNuevo.")
                continue

        # Duplicidad en Excel
        clave = (tipo, pid, anio)
        if clave in vistos:
            add_err(idx_excel, f"Duplicado en el archivo para (tipo,id,año)=({tipo},{pid},{anio}).")
            continue
        vistos.add(clave)

        # Cálculo/recorte de %
        if eff == 0.0:
            eff = _pct(egr, mat)
        if tasa == 0.0:
            tasa = _pct(tit, mat)
        eff = _clip_pct(eff)
        tasa = _clip_pct(tasa)

        # (Opcional) Bloquear conflicto con BD si existe del otro tipo de programa:
        # if tipo == "ANTIGUO" and TasaTitulacion.objects.filter(anio_ingreso=anio, programa_nuevo__id=pid).exists():
        #     add_err(idx_excel, f"Conflicto: ya existe NUEVO con id '{pid}' para año {anio} en BD.")
        #     continue
        # if tipo == "NUEVO" and TasaTitulacion.objects.filter(anio_ingreso=anio, programa_antiguo__id=pid).exists():
        #     add_err(idx_excel, f"Conflicto: ya existe ANTIGUO con id '{pid}' para año {anio} en BD.")
        #     continue

        filas_ok.append({
            "tipo": tipo,
            "pid": pid,
            "anio": anio,
            "matricula": mat,
            "egresados": egr,
            "titulados": tit,
            "eficiencia": eff,
            "tasa": tasa,
            "prog_ant": prog_ant,
            "prog_nvo": prog_nvo,
        })

    if errores:
        top = errores[:20]
        resto = len(errores) - len(top)
        for e in top:
            messages.error(request, e)
        if resto > 0:
            messages.error(request, f"…y {resto} error(es) más.")
        return redirect('tasa_de_titulacion')

    # -------- PASADA 2: ESCRIBIR (UPSERT) --------
    creados = actualizados = 0
    with transaction.atomic():
        for r in filas_ok:
            defaults = {
                "matricula_ingreso": r["matricula"],
                "egresados": r["egresados"],
                "eficiencia_terminal_porcentaje": r["eficiencia"],
                "titulados": r["titulados"],
                "tasa_titulacion": r["tasa"],
                "programa_antiguo": r["prog_ant"] if r["prog_ant"] else None,
                "programa_nuevo": r["prog_nvo"] if r["prog_nvo"] else None,
            }

            if r["prog_ant"]:
                obj, created = TasaTitulacion.objects.update_or_create(
                    anio_ingreso=r["anio"],
                    programa_antiguo=r["prog_ant"],
                    defaults=defaults,
                )
            else:
                obj, created = TasaTitulacion.objects.update_or_create(
                    anio_ingreso=r["anio"],
                    programa_nuevo=r["prog_nvo"],
                    defaults=defaults,
                )
            if created: creados += 1
            else: actualizados += 1

    messages.success(
        request,
        f"✅ Listo: {creados} creados, {actualizados} actualizados. (Filas procesadas: {len(filas_ok)})"
    )
    return redirect('tasa_de_titulacion')
