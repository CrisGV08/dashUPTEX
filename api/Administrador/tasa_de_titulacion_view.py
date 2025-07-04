from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from api.models import (
    TasaTitulacion,
    ProgramaEducativoAntiguo,
    ProgramaEducativoNuevo
)
import json
import io
import openpyxl

def tasa_de_titulacion_view(request):
    registros = TasaTitulacion.objects.all().order_by('anio_ingreso')

    # Filtros
    filtro_anio = request.GET.get('anio_ingreso')
    filtro_tipo = request.GET.get('tipo_programa')

    if filtro_anio:
        registros = registros.filter(anio_ingreso=filtro_anio)

    if filtro_tipo == 'antiguo':
        registros = registros.filter(programa_antiguo__isnull=False)
    elif filtro_tipo == 'nuevo':
        registros = registros.filter(programa_nuevo__isnull=False)

    # Guardar cambios desde la tabla
    if request.method == 'POST' and 'guardar' in request.POST:
        try:
            id_registro = int(request.POST.get('guardar'))
            registro = TasaTitulacion.objects.get(id=id_registro)
            registro.matricula_ingreso = int(request.POST.get(f'matricula_{id_registro}', 0))
            registro.egresados = int(request.POST.get(f'egresados_{id_registro}', 0))
            registro.titulados = int(request.POST.get(f'titulados_{id_registro}', 0))

            if registro.matricula_ingreso > 0:
                registro.eficiencia_terminal_porcentaje = round((registro.egresados / registro.matricula_ingreso) * 100, 2)
                registro.tasa_titulacion = round((registro.titulados / registro.matricula_ingreso) * 100, 2)
            else:
                registro.eficiencia_terminal_porcentaje = 0.0
                registro.tasa_titulacion = 0.0

            registro.save()
            messages.success(request, "✅ Registro actualizado correctamente.")
            return redirect('tasa_de_titulacion')
        except Exception as e:
            messages.error(request, f"❌ Error al actualizar: {e}")

    # Datos auxiliares para filtros
    anios_disponibles = TasaTitulacion.objects.values_list('anio_ingreso', flat=True).distinct().order_by('anio_ingreso')
    programas_antiguos = ProgramaEducativoAntiguo.objects.all()
    programas_nuevos = ProgramaEducativoNuevo.objects.all()

    # Datos para gráficas en JS
    datos_json = []
    for r in registros:
        programa = r.programa_antiguo.nombre if r.programa_antiguo else r.programa_nuevo.nombre
        datos_json.append({
            'programa': programa,
            'anio_ingreso': r.anio_ingreso,
            'matricula': r.matricula_ingreso,
            'egresados': r.egresados,
            'titulados': r.titulados,
            'eficiencia_terminal': r.eficiencia_terminal_porcentaje,
            'tasa_titulacion': r.tasa_titulacion
        })

    context = {
        'registros': registros,
        'anios': anios_disponibles,
        'programas_antiguos': programas_antiguos,
        'programas_nuevos': programas_nuevos,
        'filtro_anio': filtro_anio,
        'filtro_tipo': filtro_tipo,
        'datos_json': json.dumps(datos_json)
    }

    return render(request, 'tasa_de_titulacion.html', context)

def descargar_plantilla_tasa_titulacion(request):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Plantilla Tasa Titulación"
    ws.append(["Programa Antiguo", "Programa Nuevo", "Año Ingreso", "Matrícula", "Egresados", "Titulados"])

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=plantilla_tasa_titulacion.xlsx'
    return response

def subir_excel_tasa_titulacion(request):
    if request.method == 'POST' and request.FILES.get('archivo_excel'):
        archivo = request.FILES['archivo_excel']
        try:
            wb = openpyxl.load_workbook(archivo)
            ws = wb.active
            filas = list(ws.iter_rows(min_row=2, values_only=True))

            nuevos_registros = 0
            filas_omitidas = 0

            for fila in filas:
                if len(fila) < 6:
                    filas_omitidas += 1
                    continue

                programa_antiguo, programa_nuevo, anio, matricula, egresados, titulados = fila

                # Validación básica
                if not anio or (matricula is None) or (egresados is None) or (titulados is None):
                    filas_omitidas += 1
                    continue

                prog_antiguo = ProgramaEducativoAntiguo.objects.filter(nombre=programa_antiguo).first() if programa_antiguo else None
                prog_nuevo = ProgramaEducativoNuevo.objects.filter(nombre=programa_nuevo).first() if programa_nuevo else None

                if not (prog_antiguo or prog_nuevo):
                    filas_omitidas += 1
                    continue

                registro, created = TasaTitulacion.objects.get_or_create(
                    programa_antiguo=prog_antiguo,
                    programa_nuevo=prog_nuevo,
                    anio_ingreso=anio,
                    defaults={
                        'matricula_ingreso': matricula or 0,
                        'egresados': egresados or 0,
                        'titulados': titulados or 0
                    }
                )

                if not created:
                    registro.matricula_ingreso = matricula or 0
                    registro.egresados = egresados or 0
                    registro.titulados = titulados or 0

                if registro.matricula_ingreso > 0:
                    registro.eficiencia_terminal_porcentaje = round((registro.egresados / registro.matricula_ingreso) * 100, 2)
                    registro.tasa_titulacion = round((registro.titulados / registro.matricula_ingreso) * 100, 2)
                else:
                    registro.eficiencia_terminal_porcentaje = 0.0
                    registro.tasa_titulacion = 0.0

                registro.save()
                nuevos_registros += 1

            mensaje = f"✅ Se cargaron {nuevos_registros} registros."
            if filas_omitidas > 0:
                mensaje += f" ⚠️ {filas_omitidas} filas fueron omitidas por errores o datos incompletos."
            messages.success(request, mensaje)

        except Exception as e:
            messages.error(request, f"❌ Error al procesar el archivo: {e}")

    return redirect('tasa_de_titulacion')
