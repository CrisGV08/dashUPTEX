# api/Administrador/tasa_de_titulacion_view.py

from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import F
from django.db.models.functions import ExtractYear

from api.models import (
    # Ajusta si en tu proyecto se llama distinto
    GeneracionCarrera,
    ProgramaEducativoAntiguo,
    ProgramaEducativoNuevo,
)

import json


def _int0(v):
    try:
        return int(v or 0)
    except Exception:
        return 0


def _pct(num, den):
    n = float(_int0(num))
    d = float(_int0(den))
    return round((n / d) * 100.0, 2) if d > 0 else 0.0


def tasa_de_titulacion_view(request):
    """
    Construye datos desde el histórico de titulados:
    - Año = año(fecha_ingreso) o, si falta, año(fecha_egreso)
    - Matrícula = ingreso_hombres + ingreso_mujeres
    - Egresados = cohorte(h/m) + rezagados(h/m)
    - Titulados = titulados_h + titulados_m
    Envia `datos_json` al front para filtros y gráficas.
    """

    qs = (
        GeneracionCarrera.objects
        .select_related("programa_antiguo", "programa_nuevo")
        .annotate(
            anio_ingreso=ExtractYear("fecha_ingreso"),
            anio_egreso=ExtractYear("fecha_egreso"),
        )
        .order_by(
            "programa_antiguo__id",
            "programa_nuevo__id",
            "anio_ingreso",
        )
    )

    datos = []
    for r in qs:
        anio = r.anio_ingreso or r.anio_egreso
        if not anio:
            continue

        if r.programa_antiguo_id:
            tipo = "ANTIGUO"
            prog_id = r.programa_antiguo.id
            prog_nombre = r.programa_antiguo.nombre
        elif r.programa_nuevo_id:
            tipo = "NUEVO"
            prog_id = r.programa_nuevo.id
            prog_nombre = r.programa_nuevo.nombre
        else:
            continue  # sin programa asociado

        matricula = _int0(r.ingreso_hombres) + _int0(r.ingreso_mujeres)
        egresados = (
            _int0(r.egresados_cohorte_h) + _int0(r.egresados_cohorte_m) +
            _int0(r.egresados_rezagados_h) + _int0(r.egresados_rezagados_m)
        )
        titulados = _int0(r.titulados_h) + _int0(r.titulados_m)

        datos.append({
            "programa_id": prog_id,
            "programa": prog_nombre,
            "tipo": tipo,                         # filtro ANTIGUO/NUEVO
            "anio_ingreso": int(anio),
            "matricula": int(matricula),
            "egresados": int(egresados),
            "titulados": int(titulados),
            "eficiencia_terminal": _pct(egresados, matricula),
            "tasa_titulacion": _pct(titulados, matricula),
        })

    anios_disponibles = sorted({d["anio_ingreso"] for d in datos})

    context = {
        "anios": anios_disponibles,
        "programas_antiguos": ProgramaEducativoAntiguo.objects.all(),
        "programas_nuevos": ProgramaEducativoNuevo.objects.all(),
        "datos_json": json.dumps(datos),
    }
    return render(request, "tasa_de_titulacion.html", context)


# ---- Stubs opcionales por si tu urls.py aún importa estas rutas (no rompen) ----
def descargar_plantilla_tasa_titulacion(request):
    return HttpResponse(
        "Deshabilitado: ahora los datos se leen de Titulados (sin CSV).",
        status=501, content_type="text/plain",
    )


def subir_excel_tasa_titulacion(request):
    return HttpResponse(
        "Deshabilitado: ahora los datos se leen de Titulados (sin CSV).",
        status=501, content_type="text/plain",
    )
