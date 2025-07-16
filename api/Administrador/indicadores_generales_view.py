import csv
import json
import pandas as pd
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.db.models import Sum
from api.models import (
    CicloEscolar, Periodo, CicloPeriodo,
    IndicadoresGenerales, MatriculaPorCuatrimestre
)

# 📥 Descargar plantilla
def descargar_plantilla_indicadores(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="plantilla_indicadores.csv"'
    writer = csv.writer(response)
    writer.writerow(['ciclo_periodo', 'desercion', 'reprobacion', 'egresados'])

    ciclos = CicloPeriodo.objects.select_related('ciclo', 'periodo').order_by('ciclo__anio', 'periodo__clave')
    for c in ciclos:
        nombre = f"{c.ciclo.anio} - {c.periodo.clave}"
        writer.writerow([nombre, '', '', ''])

    return response

# 📤 Subida de CSV
def cargar_indicadores_generales(request):
    if request.method == 'POST':
        archivo = request.FILES.get('archivo_csv')
        if not archivo:
            messages.error(request, "No se recibió ningún archivo.")
            return redirect('indicadores_generales')

        try:
            df = pd.read_csv(archivo)
            guardados = 0

            for index, row in df.iterrows():
                try:
                    ciclo_texto = str(row['ciclo_periodo']).strip()
                    partes = ciclo_texto.split('-', 1)
                    if len(partes) != 2:
                        raise ValueError("Formato inválido en 'ciclo_periodo' (esperado '2023 - E-A')")

                    anio = partes[0].strip()
                    clave_periodo = partes[1].strip()

                    ciclo = CicloEscolar.objects.get(anio=int(anio))
                    periodo = Periodo.objects.get(clave=clave_periodo)
                    ciclo_periodo = CicloPeriodo.objects.get(ciclo=ciclo, periodo=periodo)

                    matricula_total = MatriculaPorCuatrimestre.objects.filter(
                        ciclo_periodo=ciclo_periodo
                    ).aggregate(total=Sum('cantidad'))['total']

                    if not matricula_total:
                        messages.warning(request, f"⚠️ Sin matrícula en: {ciclo_texto}. Registro omitido.")
                        continue

                    IndicadoresGenerales.objects.update_or_create(
                        ciclo_periodo=ciclo_periodo,
                        defaults={
                            'desertores': int(row['desercion']),
                            'reprobados': int(row['reprobacion']),
                            'egresados': int(row['egresados']),
                        }
                    )
                    guardados += 1
                except Exception as e:
                    messages.error(request, f"Error en fila {index + 2}: {e}")

            if guardados > 0:
                messages.success(request, f"{guardados} registros guardados correctamente.")
            else:
                messages.warning(request, "No se guardaron registros.")
        except Exception as e:
            messages.error(request, f"Error general al procesar el archivo: {e}")

    return redirect('indicadores_generales')

# 🖥️ Vista principal
def reprobacion_desercion_view(request):
    mensaje = request.GET.get("mensaje")

    ciclos_periodos = CicloPeriodo.objects.select_related('ciclo', 'periodo')
    opciones_ciclo = sorted(
        [f"{cp.ciclo.anio} - {cp.periodo.clave}" for cp in ciclos_periodos],
        reverse=True
    )

    filtros = request.GET.getlist("filtro_anio")
    ciclos_objetivos = []

    if filtros and "Todos" not in filtros:
        for filtro in filtros:
            try:
                anio_str, periodo_clave = filtro.split(" - ")
                ciclo = CicloPeriodo.objects.select_related("ciclo", "periodo").get(
                    ciclo__anio=anio_str, periodo__clave=periodo_clave
                )
                ciclos_objetivos.append(ciclo)
            except CicloPeriodo.DoesNotExist:
                continue
    else:
        ciclos_objetivos = list(CicloPeriodo.objects.all())

    datos_graficas = {'desercion': 0, 'reprobacion': 0}
    detalle_ciclos = []

    if ciclos_objetivos:
        registros = IndicadoresGenerales.objects.select_related('ciclo_periodo__ciclo', 'ciclo_periodo__periodo').filter(
            ciclo_periodo__in=ciclos_objetivos
        )

        for r in registros:
            total = MatriculaPorCuatrimestre.objects.filter(
                ciclo_periodo=r.ciclo_periodo
            ).aggregate(total=Sum('cantidad'))['total'] or 0

            if total == 0:
                continue

            porcentaje_desercion = round((r.desertores / total) * 100, 2)
            porcentaje_reprobacion = round((r.reprobados / total) * 100, 2)

            datos_graficas['desercion'] += r.desertores
            datos_graficas['reprobacion'] += r.reprobados

            detalle_ciclos.append({
                'ciclo': str(r.ciclo_periodo),
                'matricula': total,
                'desercion': r.desertores,
                'reprobacion': r.reprobados,
                'egresados': r.egresados,
                'porcentaje_desercion': porcentaje_desercion,
                'porcentaje_reprobacion': porcentaje_reprobacion
            })

    return render(request, 'indicadores_generales.html', {
        'mensaje': mensaje,
        'anios': opciones_ciclo,
        'datos_graficas': datos_graficas,
        'detalle_ciclos': detalle_ciclos
    })
