import pandas as pd
import io
import json
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from api.models import GeneracionCarrera, ProgramaEducativoAntiguo, ProgramaEducativoNuevo

def titulados_historico_actual_view(request):
    generaciones = GeneracionCarrera.objects.select_related(
        'programa_antiguo', 'programa_nuevo'
    ).order_by('fecha_ingreso')

    # ✅ JSON corregido para que coincida con los filtros del JS
    generaciones_json = json.dumps([
        {
            "nombre_programa": g.programa_antiguo.nombre if g.programa_antiguo else g.programa_nuevo.nombre,
            "anio": g.fecha_ingreso.year,
            "tasa_titulacion": g.tasa_titulacion
        }
        for g in generaciones
    ])

    if request.method == 'POST' and request.FILES.get('archivo_excel'):
        excel = request.FILES['archivo_excel']
        try:
            df = pd.read_excel(excel)
            registros = 0
            errores = []

            for i, fila in df.iterrows():
                try:
                    id_programa = str(fila['PROGRAMA EDUCATIVO']).strip().upper()

                    programa = ProgramaEducativoAntiguo.objects.filter(id=id_programa).first()
                    if not programa:
                        programa = ProgramaEducativoNuevo.objects.filter(id=id_programa).first()

                    if not programa:
                        errores.append(f"Fila {i+2}: 'PROGRAMA EDUCATIVO' ({id_programa}) no encontrado")
                        continue

                    ingreso = pd.to_datetime(fila['INGRESO'], errors='coerce')
                    egreso = pd.to_datetime(fila['EGRESO'], errors='coerce')

                    if pd.isna(ingreso) or pd.isna(egreso):
                        errores.append(f"Fila {i+2}: Fechas inválidas")
                        continue

                    GeneracionCarrera.objects.create(
                        programa_antiguo=programa if isinstance(programa, ProgramaEducativoAntiguo) else None,
                        programa_nuevo=programa if isinstance(programa, ProgramaEducativoNuevo) else None,
                        fecha_ingreso=ingreso,
                        fecha_egreso=egreso,
                        ingreso_hombres=int(fila['ING H']),
                        ingreso_mujeres=int(fila['ING M']),
                        egresados_cohorte_h=int(fila['EGR COH H']),
                        egresados_cohorte_m=int(fila['EGR COH M']),
                        egresados_rezagados_h=int(fila['EGR REZ H']),
                        egresados_rezagados_m=int(fila['EGR REZ M']),
                        titulados_h=int(fila['TIT H']),
                        titulados_m=int(fila['TIT M']),
                        registrados_dgp_h=int(fila['REG H']),
                        registrados_dgp_m=int(fila['REG M']),
                    )
                    registros += 1
                except Exception as e:
                    errores.append(f"Fila {i+2}: {str(e)}")

            if registros:
                messages.success(request, f"✅ {registros} registros cargados correctamente.")
            if errores:
                messages.error(request, "⚠️ Errores: " + " | ".join(errores))

            return redirect('titulados_historico_actual')

        except Exception as e:
            messages.error(request, f"❌ Error al leer el archivo: {e}")

    return render(request, 'titulados_historico_actual.html', {
        'generaciones': generaciones,
        'generaciones_json': generaciones_json
    })

def descargar_plantilla_titulados_historico_actual(request):
    antiguos = ProgramaEducativoAntiguo.objects.all()
    nuevos = ProgramaEducativoNuevo.objects.all()

    datos = []
    for p in antiguos:
        datos.append({'PROGRAMA EDUCATIVO': p.id})
    for p in nuevos:
        datos.append({'PROGRAMA EDUCATIVO': p.id})

    columnas_extra = [
        'INGRESO', 'EGRESO', 'ING H', 'ING M',
        'EGR COH H', 'EGR COH M',
        'EGR REZ H', 'EGR REZ M',
        'TIT H', 'TIT M',
        'REG H', 'REG M'
    ]

    for row in datos:
        for col in columnas_extra:
            row[col] = 0 if 'INGRESO' not in col and 'EGRESO' not in col else ''

    df = pd.DataFrame(datos)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Titulados')

    buffer.seek(0)
    response = HttpResponse(
        buffer,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=titulados_historico_actual.xlsx'
    return response
