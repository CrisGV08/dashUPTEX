#api/Administrador/titulados_historico_actual_view.py

import pandas as pd
import io
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from api.models import GeneracionCarrera, ProgramaEducativoAntiguo, ProgramaEducativoNuevo

def titulados_historico_actual_view(request):
    generaciones = GeneracionCarrera.objects.select_related(
        'programa_antiguo', 'programa_nuevo'
    ).order_by('fecha_ingreso')

    if request.method == 'POST' and request.FILES.get('archivo_excel'):
        excel = request.FILES['archivo_excel']
        try:
            df = pd.read_excel(excel, skiprows=5)
            registros = 0
            errores = []

            for i, fila in df.iterrows():
                try:
                    nombre_programa = str(fila['PROGRAMA EDUCATIVO']).strip()
                    programa = ProgramaEducativoAntiguo.objects.filter(nombre__icontains=nombre_programa).first()
                    if not programa:
                        programa = ProgramaEducativoNuevo.objects.filter(nombre__icontains=nombre_programa).first()

                    if not programa:
                        errores.append(f"Fila {i+6}: Programa no encontrado ({nombre_programa})")
                        continue

                    ingreso = pd.to_datetime(fila['INGRESO'], errors='coerce')
                    egreso = pd.to_datetime(fila['EGRESO'], errors='coerce')

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
                    errores.append(f"Fila {i+6}: {str(e)}")

            if registros:
                messages.success(request, f"✅ {registros} registros cargados correctamente.")
            if errores:
                messages.error(request, "⚠️ Errores: " + " | ".join(errores))

            return redirect('titulados_historico_actual')

        except Exception as e:
            messages.error(request, f"❌ Error al leer el archivo: {e}")

    return render(request, 'titulados_historico_actual.html', {
        'generaciones': generaciones
    })

# NUEVA FUNCIÓN: Exportar plantilla con datos reales
def descargar_plantilla_titulados_historico_actual(request):
    generaciones = GeneracionCarrera.objects.select_related(
        'programa_antiguo', 'programa_nuevo'
    ).order_by('fecha_ingreso')

    datos = []
    for g in generaciones:
        datos.append({
            'PROGRAMA EDUCATIVO': str(g.programa_antiguo or g.programa_nuevo),
            'INGRESO': g.fecha_ingreso.strftime('%Y-%m-%d'),
            'EGRESO': g.fecha_egreso.strftime('%Y-%m-%d'),
            'ING H': g.ingreso_hombres,
            'ING M': g.ingreso_mujeres,
            'EGR COH H': g.egresados_cohorte_h,
            'EGR COH M': g.egresados_cohorte_m,
            'EGR REZ H': g.egresados_rezagados_h,
            'EGR REZ M': g.egresados_rezagados_m,
            'TIT H': g.titulados_h,
            'TIT M': g.titulados_m,
            'REG H': g.registrados_dgp_h,
            'REG M': g.registrados_dgp_m,
        })

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
