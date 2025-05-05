# Matricula_H_Nuevo_Ingreso_view.py

import io
import pandas as pd
import json
from collections import defaultdict
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from api.models import MatriculaNuevoIngreso, ProgramaEducativoAntiguo, ProgramaEducativoNuevo, CicloPeriodo

def matricula_h_nuevo_ingreso_view(request):
    datos = MatriculaNuevoIngreso.objects.select_related(
        'ciclo_periodo', 'programa_antiguo', 'programa_nuevo'
    ).all()

    if request.method == "POST" and request.FILES.get('archivo_excel'):
        excel_file = request.FILES['archivo_excel']

        try:
            df = pd.read_excel(excel_file)
            errores = []
            registros_guardados = 0

            for i, fila in df.iterrows():
                try:
                    ciclo_periodo = CicloPeriodo.objects.get(id=int(fila['ciclo_periodo_id']))

                    # Validación y limpieza segura de programa_antiguo y programa_nuevo
                    programa_antiguo = None
                    programa_nuevo = None

                    if pd.notna(fila['programa_antiguo_id']) and str(fila['programa_antiguo_id']).strip() != '':
                        programa_antiguo = ProgramaEducativoAntiguo.objects.filter(id=int(fila['programa_antiguo_id'])).first()

                    if pd.notna(fila['programa_nuevo_id']) and str(fila['programa_nuevo_id']).strip() != '':
                        programa_nuevo = ProgramaEducativoNuevo.objects.filter(id=int(fila['programa_nuevo_id'])).first()

                    if not programa_antiguo and not programa_nuevo:
                        errores.append(f"Fila {i+2}: Programa no encontrado.")
                        continue

                    MatriculaNuevoIngreso.objects.update_or_create(
                        ciclo_periodo=ciclo_periodo,
                        programa_antiguo=programa_antiguo,
                        programa_nuevo=programa_nuevo,
                        defaults={'cantidad': int(fila['cantidad'])}
                    )
                    registros_guardados += 1
                except Exception as e:
                    errores.append(f"Fila {i+2}: Error - {str(e)}")

            if registros_guardados > 0:
                messages.success(request, f"✅ {registros_guardados} registro(s) guardado(s) correctamente.")
            if errores:
                messages.error(request, "⚠️ Errores: " + " | ".join(errores))

            return redirect('matricula_h_nuevo_ingreso')

        except Exception as e:
            messages.error(request, f"❌ Error al procesar el archivo: {e}")

    # 🔍 Preparar datos para gráficas
    datos_por_ciclo = defaultdict(int)
    programas_totales = defaultdict(lambda: [0] * 20)  # Máximo 20 ciclos
    ciclos_unicos = []

    for d in datos:
        ciclo_label = f"{d.ciclo_periodo.ciclo.anio} - {d.ciclo_periodo.periodo.clave}"
        if ciclo_label not in ciclos_unicos:
            ciclos_unicos.append(ciclo_label)
        datos_por_ciclo[ciclo_label] += d.cantidad

        prog = str(d.programa_antiguo or d.programa_nuevo)
        index = ciclos_unicos.index(ciclo_label)
        programas_totales[prog][index] += d.cantidad

    labels = ciclos_unicos
    valores = [datos_por_ciclo[label] for label in labels]

    total_antiguos = sum(d.cantidad for d in datos if d.programa_antiguo)
    total_nuevos = sum(d.cantidad for d in datos if d.programa_nuevo)

    datos_dashboard = {
        "labels": labels,
        "totales": valores,
        "total_antiguos": total_antiguos,
        "total_nuevos": total_nuevos,
        "programas_totales": programas_totales
    }

    return render(request, 'matricula_h_nuevo_ingreso.html', {
        'datos': datos,
        'datos_grafica_json': json.dumps(datos_dashboard),
        'datos_dashboard': json.dumps(datos_dashboard)
    })


def descargar_plantilla_matricula_h_nuevo_ingreso(request):
    ciclo_periodo = CicloPeriodo.objects.order_by('-id').first()
    programas_antiguos = ProgramaEducativoAntiguo.objects.all()
    programas_nuevos = ProgramaEducativoNuevo.objects.all()

    columnas = ['ciclo_periodo_id', 'programa_antiguo_id', 'programa_nuevo_id', 'cantidad']
    datos = []

    for pa in programas_antiguos:
        datos.append({
            'ciclo_periodo_id': ciclo_periodo.id if ciclo_periodo else '',
            'programa_antiguo_id': pa.id,
            'programa_nuevo_id': '',
            'cantidad': 0
        })

    for pn in programas_nuevos:
        datos.append({
            'ciclo_periodo_id': ciclo_periodo.id if ciclo_periodo else '',
            'programa_antiguo_id': '',
            'programa_nuevo_id': pn.id,
            'cantidad': 0
        })

    df = pd.DataFrame(datos, columns=columnas)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Plantilla')

    buffer.seek(0)

    response = HttpResponse(
        buffer,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=matricula_h_nuevo_ingreso.xlsx'

    return response