import json
import pandas as pd
from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from api.models import GeneracionCarrera, ProgramaEducativoAntiguo, ProgramaEducativoNuevo


def titulados_historico_actual_view(request):
    registros = GeneracionCarrera.objects.all().order_by('fecha_ingreso')

    # Guardar cambios desde tabla editable
    if request.method == 'POST' and 'guardar' in request.POST:
        registro_id = request.POST.get('guardar')
        try:
            registro = GeneracionCarrera.objects.get(id=registro_id)
            registro.titulados_h = int(request.POST.get(f'titulados_h_{registro_id}', 0))
            registro.titulados_m = int(request.POST.get(f'titulados_m_{registro_id}', 0))
            registro.registrados_dgp_h = int(request.POST.get(f'dgp_h_{registro_id}', 0))
            registro.registrados_dgp_m = int(request.POST.get(f'dgp_m_{registro_id}', 0))
            registro.save()
            messages.success(request, "Cambios guardados correctamente.")
        except GeneracionCarrera.DoesNotExist:
            messages.error(request, "Registro no encontrado.")
        return redirect('titulados_historico_actual')

    # Convertir registros a JSON para JS
    datos_json = []
    for reg in registros:
        programa = reg.programa_antiguo.nombre if reg.programa_antiguo else reg.programa_nuevo.nombre
        datos_json.append({
            'id': reg.id,
            'nombre_programa': programa,
            'anio': reg.fecha_ingreso.year,
            'titulados': reg.total_titulados,
            'registrados': reg.total_dgp,
            'tasa_titulacion': reg.tasa_titulacion,
        })

    context = {
        'registros': registros,
        'datos_json': json.dumps(datos_json, ensure_ascii=False)
    }
    return render(request, 'titulados_historico_actual.html', context)


# Descargar plantilla vacía
def descargar_plantilla_titulados_historico_actual(request):
    columnas = [
        'Programa', 'Fecha Ingreso', 'Fecha Egreso',
        'Ingreso Hombres', 'Ingreso Mujeres',
        'Egresados Cohorte H', 'Egresados Cohorte M',
        'Egresados Rezagados H', 'Egresados Rezagados M',
        'Titulados H', 'Titulados M',
        'Registrados DGP H', 'Registrados DGP M'
    ]
    df = pd.DataFrame(columns=columnas)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=plantilla_titulados_historico_actual.xlsx'
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Titulados')
    return response


# Subir Excel con datos
@require_http_methods(["POST"])
def subir_excel_titulados_historico_actual(request):
    archivo = request.FILES.get('archivo_excel')
    if not archivo:
        messages.error(request, "Debes seleccionar un archivo.")
        return redirect('titulados_historico_actual')

    try:
        df = pd.read_excel(archivo)

        for _, row in df.iterrows():
            nombre_programa = str(row['Programa']).strip()
            programa = ProgramaEducativoAntiguo.objects.filter(nombre=nombre_programa).first() \
                       or ProgramaEducativoNuevo.objects.filter(nombre=nombre_programa).first()

            if not programa:
                continue

            fecha_ingreso = pd.to_datetime(row['Fecha Ingreso'], errors='coerce')
            fecha_egreso = pd.to_datetime(row['Fecha Egreso'], errors='coerce')

            if pd.isna(fecha_ingreso) or pd.isna(fecha_egreso):
                continue

            # Determinar tipo de programa
            if isinstance(programa, ProgramaEducativoAntiguo):
                programa_antiguo = programa
                programa_nuevo = None
            else:
                programa_antiguo = None
                programa_nuevo = programa

            GeneracionCarrera.objects.update_or_create(
                programa_antiguo=programa_antiguo,
                programa_nuevo=programa_nuevo,
                fecha_ingreso=fecha_ingreso,
                fecha_egreso=fecha_egreso,
                defaults={
                    'ingreso_hombres': int(row['Ingreso Hombres']),
                    'ingreso_mujeres': int(row['Ingreso Mujeres']),
                    'egresados_cohorte_h': int(row['Egresados Cohorte H']),
                    'egresados_cohorte_m': int(row['Egresados Cohorte M']),
                    'egresados_rezagados_h': int(row['Egresados Rezagados H']),
                    'egresados_rezagados_m': int(row['Egresados Rezagados M']),
                    'titulados_h': int(row['Titulados H']),
                    'titulados_m': int(row['Titulados M']),
                    'registrados_dgp_h': int(row['Registrados DGP H']),
                    'registrados_dgp_m': int(row['Registrados DGP M']),
                }
            )

        messages.success(request, "Archivo cargado correctamente.")
    except Exception as e:
        messages.error(request, f"Error al procesar el archivo: {e}")

    return redirect('titulados_historico_actual')
