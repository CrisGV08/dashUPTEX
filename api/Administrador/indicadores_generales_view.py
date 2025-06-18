# views/indicadores_generales_view.py

from django.shortcuts import render
from django.db.models import Sum
from django.http import HttpResponse
import pandas as pd
from django.contrib import messages
from django.template.loader import get_template
from weasyprint import HTML
from openpyxl import Workbook
from django.http import HttpResponse
from api.models import IndicadoresGenerales, CicloEscolar, Periodo, CicloPeriodo, ProgramaEducativoAntiguo, ProgramaEducativoNuevo, MatriculaPorCuatrimestre
from api.forms import ExcelUploadForm


def reprobacion_desercion_view(request):
    filtros = get_filtros_desercion(request)
    indicadores = filtrar_indicadores_queryset(**filtros)
    context = generar_contexto_indicadores(request, indicadores, filtros)
    return render(request, 'indicadores_generales.html', context)


def get_filtros_desercion(request):
    anio = request.GET.get('anio')
    periodo = request.GET.get('periodo')
    tipo_programa = request.GET.get('tipo_programa')
    programa = request.GET.get('programa')
    tipo_grafica = request.GET.get('tipo_grafica', 'todos')

    return {
        'anio': anio,
        'periodo': periodo,
        'tipo_programa': tipo_programa,
        'programa': programa,
        'tipo_grafica': tipo_grafica,
    }


def filtrar_indicadores_queryset(anio, periodo, tipo_programa, programa, tipo_grafica):
    queryset = IndicadoresGenerales.objects.select_related('ciclo_periodo__ciclo', 'ciclo_periodo__periodo')

    if anio:
        queryset = queryset.filter(ciclo_periodo__ciclo__anio=anio)
    if periodo:
        queryset = queryset.filter(ciclo_periodo__periodo__clave=periodo)
    if tipo_programa and programa:
        if tipo_programa == 'antiguo':
            queryset = queryset.filter(ciclo_periodo__matriculaporcuatrimestre__programa_antiguo__id=programa)
        else:
            queryset = queryset.filter(ciclo_periodo__matriculaporcuatrimestre__programa_nuevo__id=programa)

    return queryset.distinct()


def generar_contexto_indicadores(request, indicadores, filtros):
    context = {
        'form': ExcelUploadForm(),
        'indicadores': indicadores,
        'anios': CicloEscolar.objects.all(),
        'periodos': Periodo.objects.all(),
        'programas_antiguos': ProgramaEducativoAntiguo.objects.all(),
        'programas_nuevos': ProgramaEducativoNuevo.objects.all(),
        'tipo_grafica': filtros['tipo_grafica'],
        'anio_seleccionado': filtros['anio'],
        'periodo_seleccionado': filtros['periodo'],
        'tipo_programa': filtros['tipo_programa'],
        'programa_seleccionado': filtros['programa'],
    }
    return context


def descargar_plantilla_indicador(request):
    wb = Workbook()
    ws = wb.active
    ws.title = "Plantilla Indicadores Generales"

    # Encabezados
    columnas = ["anio", "periodo", "programa_id", "desertores", "reprobados", "egresados"]
    ws.append(columnas)

    # Crear respuesta
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="plantilla_indicadores_generales.xlsx"'
    wb.save(response)
    return response
