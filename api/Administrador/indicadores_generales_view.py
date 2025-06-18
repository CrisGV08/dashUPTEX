import pandas as pd
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Sum
from django.http import HttpResponse
from api.models import IndicadoresGenerales, CicloPeriodo, Periodo, CicloEscolar, ProgramaEducativoAntiguo, ProgramaEducativoNuevo


def cargar_indicadores_generales(request):
    if request.method == 'POST':
        archivo = request.FILES['archivo']
        df = pd.read_excel(archivo)

        for index, row in df.iterrows():
            try:
                ciclo_texto = str(row['ciclo_periodo'])  # "2023 - S-D"
                anio, clave_periodo = [x.strip() for x in ciclo_texto.split('-')]

                ciclo = CicloEscolar.objects.get(anio=int(anio))
                periodo = Periodo.objects.get(clave=clave_periodo)
                ciclo_periodo = CicloPeriodo.objects.get(ciclo=ciclo, periodo=periodo)

                IndicadoresGenerales.objects.update_or_create(
                    ciclo_periodo=ciclo_periodo,
                    defaults={
                        'desertores': row['desertores'],
                        'reprobados': row['reprobados'],
                        'egresados': row['egresados'],
                    }
                )
            except Exception as e:
                print(f"Error en fila {index}: {e}")
                messages.error(request, f"Error en la fila {index + 2}: {e}")

        messages.success(request, "Archivo procesado correctamente.")
        return redirect('reprobacion_desercion')

    return redirect('reprobacion_desercion')


def descargar_plantilla_indicador(request):
    with open('static/plantillas/plantilla_indicadores.xlsx', 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="plantilla_indicadores.xlsx"'
        return response


def reprobacion_desercion_view(request):
    anio = request.GET.get('anio')
    periodo_clave = request.GET.get('periodo')
    tipo_programa = request.GET.get('tipo_programa')
    carrera_id = request.GET.get('carrera')
    tipo_grafica = request.GET.get('grafica')

    indicadores = IndicadoresGenerales.objects.all()

    if anio:
        indicadores = indicadores.filter(ciclo_periodo__ciclo__anio=anio)
    if periodo_clave:
        indicadores = indicadores.filter(ciclo_periodo__periodo__clave=periodo_clave)

    # Obtener listas de referencia
    ciclos = CicloEscolar.objects.all().order_by('anio')
    periodos = Periodo.objects.all().order_by('clave')

    # Obtener carreras según el tipo de programa
   # Obtener carreras según el tipo de programa
    if carrera_id:
        if tipo_programa == 'nuevo':
            indicadores = indicadores.filter(ciclo_periodo__matriculaporcuatrimestre__programa_nuevo__id=carrera_id)
        elif tipo_programa == 'antiguo':
            indicadores = indicadores.filter(ciclo_periodo__matriculaporcuatrimestre__programa_antiguo__id=carrera_id)

# Obtener todas las carreras según el tipo de programa (esto va fuera del if carrera_id)
    if tipo_programa == 'nuevo':
        carreras = ProgramaEducativoNuevo.objects.all()
    elif tipo_programa == 'antiguo':
        carreras = ProgramaEducativoAntiguo.objects.all()
    else:
        carreras = list(ProgramaEducativoNuevo.objects.all()) + list(ProgramaEducativoAntiguo.objects.all())


    # Preparar datos para tabla y gráfica
    datos = []
    for ind in indicadores:
        total = ind.desertores + ind.reprobados + ind.egresados
        datos.append({
            'periodo': f"{ind.ciclo_periodo.ciclo.anio} - {ind.ciclo_periodo.periodo.clave}",
            'matricula': total,
            'desertores': ind.desertores,
            'reprobados': ind.reprobados,
            'egresados': ind.egresados,
            'porc_desercion': round((ind.desertores / total) * 100, 2) if total else 0,
            'porc_reprobacion': round((ind.reprobados / total) * 100, 2) if total else 0,
        })

    context = {
        'datos': datos,
        'ciclos': ciclos,
        'periodos': periodos,
        'carreras': carreras,
        'anio_actual': anio,
        'periodo_actual': periodo_clave,
        'tipo_programa': tipo_programa,
        'carrera_actual': carrera_id,
        'tipo_grafica': tipo_grafica,
    }

    return render(request, 'indicadores_generales.html', context)
