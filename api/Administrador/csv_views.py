import csv
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from api.models import (
    CicloPeriodo,
    ProgramaEducativoAntiguo,
    ProgramaEducativoNuevo,
    NuevoIngreso
)

# Descargar plantilla CSV
def descargar_plantilla_nuevo_ingreso(request):
    ciclo_periodo = CicloPeriodo.objects.order_by('-id').first()

    if not ciclo_periodo:
        return HttpResponse("⚠️ No hay ciclo_periodo creado todavía.", content_type='text/plain')

    programas_antiguos = ProgramaEducativoAntiguo.objects.all()
    programas_nuevos = ProgramaEducativoNuevo.objects.all()

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="plantilla_nuevo_ingreso.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'ciclo_periodo_id',
        'programa_antiguo_id',
        'programa_nuevo_id',
        'examen',
        'renoes',
        'uaem_gem',
        'pase_directo'
    ])

    for pa in programas_antiguos:
        writer.writerow([
            ciclo_periodo.id,
            pa.id,
            '',
            0, 0, 0, 0
        ])
    for pn in programas_nuevos:
        writer.writerow([
            ciclo_periodo.id,
            '',
            pn.id,
            0, 0, 0, 0
        ])

    return response

# Subir y procesar CSV
def subir_csv_nuevo_ingreso(request):
    if request.method == 'POST' and request.FILES.get('archivo_csv'):
        archivo = request.FILES['archivo_csv']
        decoded = archivo.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded)

        registros_guardados = 0
        errores = []

        for i, fila in enumerate(reader, start=1):
            try:
                ciclo_periodo_id = int(fila['ciclo_periodo_id'])
                programa_antiguo_id = fila['programa_antiguo_id'] or None
                programa_nuevo_id = fila['programa_nuevo_id'] or None

                examen = int(fila['examen'])
                renoes = int(fila['renoes'])
                uaem_gem = int(fila['uaem_gem'])
                pase_directo = int(fila['pase_directo'])

                ciclo_periodo = CicloPeriodo.objects.get(id=ciclo_periodo_id)
                programa_antiguo = ProgramaEducativoAntiguo.objects.filter(id=programa_antiguo_id).first()
                programa_nuevo = ProgramaEducativoNuevo.objects.filter(id=programa_nuevo_id).first()

                if not programa_antiguo and not programa_nuevo:
                    errores.append(f"Fila {i}: No se encontró programa válido.")
                    continue

                NuevoIngreso.objects.create(
                    ciclo_periodo=ciclo_periodo,
                    programa_antiguo=programa_antiguo,
                    programa_nuevo=programa_nuevo,
                    examen=examen,
                    renoes=renoes,
                    uaem_gem=uaem_gem,
                    pase_directo=pase_directo
                )
                registros_guardados += 1

            except Exception as e:
                errores.append(f"Fila {i}: Error - {str(e)}")

        if registros_guardados > 0:
            messages.success(request, f"✅ {registros_guardados} registro(s) cargado(s) correctamente.")
        if errores:
            messages.error(request, "⚠️ Se encontraron errores: " + " | ".join(errores))

        return HttpResponseRedirect(reverse('examen_admision'))

    messages.error(request, '⚠️ Debes subir un archivo CSV válido.')
    return HttpResponseRedirect(reverse('examen_admision'))
