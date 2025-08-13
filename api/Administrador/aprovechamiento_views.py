import csv
import json
import pandas as pd
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.db.models import Avg, Q
from api.models import (
    CicloEscolar, Periodo, CicloPeriodo,
    AprovechamientoAcademico, ProgramaEducativoAntiguo, ProgramaEducativoNuevo
)

def descargar_plantilla_aprovechamiento(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="plantilla_aprovechamiento.csv"'
    writer = csv.writer(response)
    writer.writerow(['ciclo_periodo', 'programa', 'promedio'])

    ciclos = CicloPeriodo.objects.select_related('ciclo', 'periodo').order_by('ciclo__anio', 'periodo__clave')
    programas = list(ProgramaEducativoAntiguo.objects.all()) + list(ProgramaEducativoNuevo.objects.all())

    for ciclo in ciclos:
        for prog in programas:
            nombre = f"{ciclo.ciclo.anio} - {ciclo.periodo.clave}"
            writer.writerow([nombre, prog.nombre, ''])

    return response

def cargar_aprovechamiento(request):
    if request.method == 'POST':
        archivo = request.FILES.get('archivo_csv')
        if not archivo:
            messages.error(request, "No se recibió ningún archivo.")
            return redirect('aprovechamiento')

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

                    programa_nombre = str(row['programa']).strip()
                    programa_antiguo = ProgramaEducativoAntiguo.objects.filter(nombre=programa_nombre).first()
                    programa_nuevo = ProgramaEducativoNuevo.objects.filter(nombre=programa_nombre).first()

                    if not (programa_antiguo or programa_nuevo):
                        raise ValueError(f"Programa no encontrado: {programa_nombre}")

                    AprovechamientoAcademico.objects.update_or_create(
                        ciclo_periodo=ciclo_periodo,
                        programa_antiguo=programa_antiguo,
                        programa_nuevo=programa_nuevo,
                        defaults={'promedio': float(row['promedio'])}
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

    return redirect('aprovechamiento')

def aprovechamiento_view(request):
    mensaje = request.GET.get("mensaje")

    # Obtener todos los programas educativos
    programas_antiguos = ProgramaEducativoAntiguo.objects.all()
    programas_nuevos = ProgramaEducativoNuevo.objects.all()
    
    # Filtro de ciclos
    ciclos_periodos = CicloPeriodo.objects.select_related('ciclo', 'periodo')
    opciones_ciclo = sorted(
        [f"{cp.ciclo.anio} - {cp.periodo.clave}" for cp in ciclos_periodos],
        reverse=True
    )
    
    # Procesar filtros
    filtro_ciclo = request.GET.get("filtro_anio", "Todos")
    filtro_programas = request.GET.getlist("programas[]")
    
    # Construir queryset filtrado
    registros = AprovechamientoAcademico.objects.select_related(
        'ciclo_periodo__ciclo', 'ciclo_periodo__periodo',
        'programa_antiguo', 'programa_nuevo'
    )
    
    # Aplicar filtro de ciclo
    if filtro_ciclo and filtro_ciclo != "Todos":
        try:
            anio_str, periodo_clave = filtro_ciclo.split(" - ")
            ciclo = CicloPeriodo.objects.get(ciclo__anio=anio_str, periodo__clave=periodo_clave)
            registros = registros.filter(ciclo_periodo=ciclo)
        except (ValueError, CicloPeriodo.DoesNotExist):
            pass
    
    # Aplicar filtro de programas
    if filtro_programas:
        q_antiguos = Q(programa_antiguo__id__in=filtro_programas)
        q_nuevos = Q(programa_nuevo__id__in=filtro_programas)
        registros = registros.filter(q_antiguos | q_nuevos)
    
    # Preparar datos para gráficos
    datos_graficas = {
        'programas': [],
        'promedios': [],
        'tipos': []  # Para distinguir antiguo/nuevo en gráficos
    }
    
    detalle_ciclos = []
    
    for r in registros:
        if r.programa_antiguo:
            nombre_prog = f"{r.programa_antiguo.nombre} (Antiguo)"
            tipo = "antiguo"
        else:
            nombre_prog = f"{r.programa_nuevo.nombre} (Nuevo)"
            tipo = "nuevo"
            
        datos_graficas['programas'].append(nombre_prog)
        datos_graficas['promedios'].append(float(r.promedio))
        datos_graficas['tipos'].append(tipo)
        
        detalle_ciclos.append({
            'ciclo': str(r.ciclo_periodo),
            'programa': nombre_prog,
            'promedio': r.promedio
        })

    return render(request, 'aprovechamiento.html', {
        'mensaje': mensaje,
        'anios': opciones_ciclo,
        'programas_antiguos': programas_antiguos,
        'programas_nuevos': programas_nuevos,
        'datos_graficas': json.dumps(datos_graficas),
        'detalle_ciclos': detalle_ciclos,
        'filtros_aplicados': {
            'ciclo': filtro_ciclo,
            'programas': filtro_programas
        }
    })