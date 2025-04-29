from django.shortcuts import render, redirect
from django.http import HttpResponse
from api.models import CicloEscolar, Periodo, CicloPeriodo, IndicadoresGenerales
from django.db.models import Sum
from django.contrib import messages
import pandas as pd
import io

def indicadores_generales_view(request):
    mensaje = None
    datos_matricula = []
    datos_desercion = []
    datos_reprobacion = []
    datos_egresados = []
    ciclos_mostrar = []

    if request.method == 'POST' and 'crear_ciclo' in request.POST:
        # Aquí podrías agregar la lógica de creación automática de ciclos
        pass

    ciclos_periodos = CicloPeriodo.objects.select_related('ciclo', 'periodo')
    opciones_ciclo = sorted(
        [f"{cp.ciclo.anio} - {cp.periodo.clave}" for cp in ciclos_periodos],
        reverse=True
    )

    indicadores = []
    filtro = request.GET.get("filtro_anio")

    if filtro and filtro != "Todos":
        try:
            anio_str, periodo_clave = filtro.split(" - ")
            ciclo_periodo = CicloPeriodo.objects.select_related("ciclo", "periodo").get(
                ciclo__anio=anio_str, periodo__clave=periodo_clave
            )
            indicadores = IndicadoresGenerales.objects.filter(ciclo_periodo=ciclo_periodo)

            for i in indicadores:
                datos_matricula.append(i.matricula_total)
                datos_desercion.append(i.desertores)
                datos_reprobacion.append(i.reprobados)
                datos_egresados.append(i.egresados)
                ciclos_mostrar.append(str(i.ciclo_periodo))

        except CicloPeriodo.DoesNotExist:
            pass

    return render(request, 'indicadores_generales.html', {
        'mensaje': mensaje,
        'anios': opciones_ciclo,
        'indicadores': indicadores,
        'datos_matricula': datos_matricula,
        'datos_desercion': datos_desercion,
        'datos_reprobacion': datos_reprobacion,
        'datos_egresados': datos_egresados,
        'ciclos_mostrar': ciclos_mostrar
    })

def descargar_plantilla_indicadores(request):
    output = io.StringIO()
    columnas = ['Matricula', 'Desercion', 'Reprobacion', 'Egresados']
    df = pd.DataFrame(columns=columnas)
    df.to_csv(output, index=False)

    response = HttpResponse(output.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="PLANTILLA_INDICADORES_GENERALES.csv"'
    return response

def subir_csv_indicadores(request):
    if request.method == 'POST' and request.FILES.get('archivo_csv'):
        archivo = request.FILES['archivo_csv']
        errores = []

        try:
            df = pd.read_csv(archivo)

            # Buscar el último ciclo/periodo
            ultimo_ciclo = CicloPeriodo.objects.order_by('-ciclo__anio', '-periodo__clave').first()
            if not ultimo_ciclo:
                messages.error(request, "⚠️ No existe un ciclo/periodo creado. Primero debes crear uno.")
                return redirect('indicadores_generales')

            for index, fila in df.iterrows():
                fila_num = index + 2

                try:
                    desertores = int(fila['Desercion'])
                    reprobados = int(fila['Reprobacion'])
                    egresados = int(fila['Egresados'])

                    IndicadoresGenerales.objects.create(
                        ciclo_periodo=ultimo_ciclo,
                        desertores=desertores,
                        reprobados=reprobados,
                        egresados=egresados,
                    )

                except ValueError as ve:
                    errores.append(f"Fila {fila_num}: Datos inválidos ({ve})")
                except Exception as e:
                    errores.append(f"Fila {fila_num}: {e}")

            if errores:
                mensaje_error = "<br>".join(errores)
                messages.error(request, f"❌ Errores encontrados:<br>{mensaje_error}")
            else:
                messages.success(request, "✅ Archivo procesado correctamente y datos guardados.")

        except Exception as e:
            messages.error(request, f"❌ Error al procesar el archivo: {e}")

    return redirect('indicadores_generales')
