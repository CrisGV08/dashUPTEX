import csv
import json
import pandas as pd
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.db.models import Sum
from api.models import (
    CicloEscolar, Periodo, CicloPeriodo,
    EficienciaTerminal, MatriculaPorCuatrimestre,
    ProgramaEducativoAntiguo, ProgramaEducativoNuevo
)

# 📥 Descargar plantilla
def descargar_plantilla_eficiencia_terminal(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="plantilla_eficiencia_terminal.csv"'
    writer = csv.writer(response)
    writer.writerow(['ciclo_periodo', 'programa', 'matricula_ingreso', 'egresados'])

    ciclos = CicloPeriodo.objects.select_related('ciclo', 'periodo').order_by('ciclo__anio', 'periodo__clave')
    for c in ciclos:
        nombre = f"{c.ciclo.anio} - {c.periodo.clave}"
        writer.writerow([nombre, '', '', ''])

    return response

# 📤 Cargar datos desde Excel
def cargar_eficiencia_terminal(request):
    if request.method == 'POST':
        archivo = request.FILES.get('archivo_csv')
        if not archivo:
            messages.error(request, "No se recibió ningún archivo.")
            return redirect('eficiencia_terminal')

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

                    programa_clave = str(row['programa']).strip()
                    programa_antiguo = ProgramaEducativoAntiguo.objects.filter(id=programa_clave).first()
                    programa_nuevo = ProgramaEducativoNuevo.objects.filter(id=programa_clave).first()

                    if not programa_antiguo and not programa_nuevo:
                        raise ValueError(f"Programa '{programa_clave}' no encontrado.")

                    EficienciaTerminal.objects.update_or_create(
                        ciclo_periodo=ciclo_periodo,
                        programa_antiguo=programa_antiguo if programa_antiguo else None,
                        programa_nuevo=programa_nuevo if programa_nuevo else None,
                        defaults={
                            'matricula_ingreso': int(row['matricula_ingreso']),
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

    return redirect('eficiencia_terminal')

# 🖥️ Vista principal
def eficiencia_terminal_view(request):
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

    datos_graficas = {'eficiencia': 0}
    detalle_ciclos = []

    if ciclos_objetivos:
        registros = EficienciaTerminal.objects.select_related(
            'ciclo_periodo__ciclo', 'ciclo_periodo__periodo',
            'programa_antiguo', 'programa_nuevo'
        ).filter(ciclo_periodo__in=ciclos_objetivos)

        for r in registros:
            eficiencia = r.porcentaje_eficiencia
            datos_graficas['eficiencia'] += eficiencia

            detalle_ciclos.append({
                'ciclo': str(r.ciclo_periodo),
                'programa': r.programa_antiguo.nombre if r.programa_antiguo else r.programa_nuevo.nombre,
                'matricula_ingreso': r.matricula_ingreso,
                'egresados': r.egresados,
                'porcentaje': eficiencia
            })

    return render(request, 'eficiencia_terminal.html', {
        'mensaje': mensaje,
        'anios': opciones_ciclo,
        'datos_graficas': datos_graficas,
        'detalle_ciclos': detalle_ciclos
    })
