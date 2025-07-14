import pandas as pd
import io
import json
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from api.models import ProgramaEducativoAntiguo, ProgramaEducativoNuevo, TituladosHistoricos


def titulados_historicos_view(request):
    datos = TituladosHistoricos.objects.select_related(
        'programa_antiguo', 'programa_nuevo'
    ).order_by('anio_ingreso')

    datos_json = json.dumps([
        {
            "nombre_programa": (
                d.programa_antiguo.nombre if d.programa_antiguo
                else d.programa_nuevo.nombre if d.programa_nuevo
                else "No definido"
            ),
            "clave_programa": (
                d.programa_antiguo.id if d.programa_antiguo
                else d.programa_nuevo.id if d.programa_nuevo
                else "ND"
            ),
            "anio": d.anio_ingreso,
            "egreso": d.anio_egreso,
            "titulados_hombres": d.titulados_hombres,
            "titulados_mujeres": d.titulados_mujeres,
            "registrados_dgp_h": d.registrados_dgp_h,
            "registrados_dgp_m": d.registrados_dgp_m,
            "total_titulados": d.total_titulados,
            "total_dgp": d.total_dgp
        }
        for d in datos
    ])

    if request.method == 'POST' and request.FILES.get('archivo_excel'):
        archivo_excel = request.FILES['archivo_excel']
        try:
            df = pd.read_excel(archivo_excel)
            registros_exitosos = 0
            errores = []

            for i, fila in df.iterrows():
                try:
                    clave = str(fila.get('PROGRAMA EDUCATIVO')).strip().upper()
                    programa = ProgramaEducativoAntiguo.objects.filter(id=clave).first() or \
                               ProgramaEducativoNuevo.objects.filter(id=clave).first()

                    if not programa:
                        errores.append(f"❌ Fila {i + 2}: Programa '{clave}' no encontrado.")
                        continue

                    ingreso = int(fila.get('AÑO INGRESO', 0) or 0)
                    egreso = int(fila.get('AÑO EGRESO', 0) or 0)
                    tit_h = int(fila.get('TITULADOS H', 0) or 0)
                    tit_m = int(fila.get('TITULADOS M', 0) or 0)
                    reg_h = int(fila.get('REG DGP H', 0) or 0)
                    reg_m = int(fila.get('REG DGP M', 0) or 0)

                    existe = TituladosHistoricos.objects.filter(
                        anio_ingreso=ingreso,
                        anio_egreso=egreso,
                        programa_antiguo=programa if isinstance(programa, ProgramaEducativoAntiguo) else None,
                        programa_nuevo=programa if isinstance(programa, ProgramaEducativoNuevo) else None
                    ).exists()

                    if existe:
                        errores.append(f"⚠️ Fila {i + 2}: Ya existe un registro con el mismo año y programa.")
                        continue

                    TituladosHistoricos.objects.create(
                        anio_ingreso=ingreso,
                        anio_egreso=egreso,
                        titulados_hombres=tit_h,
                        titulados_mujeres=tit_m,
                        registrados_dgp_h=reg_h,
                        registrados_dgp_m=reg_m,
                        programa_antiguo=programa if isinstance(programa, ProgramaEducativoAntiguo) else None,
                        programa_nuevo=programa if isinstance(programa, ProgramaEducativoNuevo) else None
                    )
                    registros_exitosos += 1

                except Exception as e:
                    errores.append(f"⚠️ Fila {i + 2}: Error inesperado. {str(e)}")

            if registros_exitosos:
                messages.success(request, f"✅ {registros_exitosos} registros cargados correctamente.")
            if errores:
                messages.error(request, "Errores encontrados:<br>" + "<br>".join(errores))

            return redirect('titulados_historicos')

        except Exception as e:
            messages.error(request, f"❌ Error al leer el archivo Excel: {str(e)}")

    return render(request, 'titulados_historicos.html', {
        'datos': datos,
        'datos_json': datos_json
    })


def descargar_plantilla_titulados_historicos(request):
    antiguos = ProgramaEducativoAntiguo.objects.all()
    nuevos = ProgramaEducativoNuevo.objects.all()

    filas = []
    for p in list(antiguos) + list(nuevos):
        filas.append({
            'PROGRAMA EDUCATIVO': p.id,
            'AÑO INGRESO': '',
            'AÑO EGRESO': '',
            'TITULADOS H': 0,
            'TITULADOS M': 0,
            'REG DGP H': 0,
            'REG DGP M': 0,
        })

    df = pd.DataFrame(filas)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Titulados')

    buffer.seek(0)
    response = HttpResponse(
        buffer, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="plantilla_titulados_historicos.xlsx"'
    return response
