# app/views/tit_his_usuario.py
from django.shortcuts import render
import json
from datetime import date

from api.models import (
    GeneracionCarrera,
    ProgramaEducativoAntiguo,
    ProgramaEducativoNuevo,
)

def _prog_name(g: GeneracionCarrera) -> str:
    if g.programa_antiguo_id:
        try:
            return g.programa_antiguo.nombre
        except ProgramaEducativoAntiguo.DoesNotExist:
            return g.programa_antiguo_id
    if g.programa_nuevo_id:
        try:
            return g.programa_nuevo.nombre
        except ProgramaEducativoNuevo.DoesNotExist:
            return g.programa_nuevo_id
    return ""

def tit_his_usuario_view(request):
    # Catálogos (para filtros)
    carreras_antiguas = list(
        ProgramaEducativoAntiguo.objects.values("id", "nombre").order_by("nombre")
    )
    carreras_nuevas = list(
        ProgramaEducativoNuevo.objects.values("id", "nombre").order_by("nombre")
    )

    # Registros (lectura)
    generaciones = (
        GeneracionCarrera.objects
        .select_related("programa_antiguo", "programa_nuevo")
        .order_by("fecha_ingreso", "programa_antiguo__nombre", "programa_nuevo__nombre")
    )

    # Serie base para la gráfica (fallback)
    generaciones_json = [
        {
            "programa": _prog_name(g),
            "anio": g.fecha_ingreso.year if g.fecha_ingreso else None,
            "tasa": g.tasa_titulacion,
        }
        for g in generaciones
    ]

    return render(
        request,
        "tit_his_usuario.html",
        {
            "page_title": "Titulados – Histórico",
            "generaciones": generaciones,
            "generaciones_json": json.dumps(generaciones_json, ensure_ascii=False),
            "carreras_antiguas": json.dumps(carreras_antiguas, ensure_ascii=False),
            "carreras_nuevas": json.dumps(carreras_nuevas, ensure_ascii=False),
        },
    )
