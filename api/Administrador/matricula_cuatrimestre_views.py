import os
import csv
import json
import pandas as pd
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages
from django.conf import settings
from django.urls import reverse
from django.db.models import Sum, F

from api.models import (
    CicloEscolar, Periodo, CicloPeriodo,
    ProgramaEducativoAntiguo, ProgramaEducativoNuevo,  # ← AÑADIDO
    MatriculaPorCuatrimestre
)


def importar_matricula_cuatrimestres(request):
    if 'usuario_id' not in request.session:
        return redirect('login')

    archivo = os.path.join(settings.MEDIA_ROOT, "excels", "Indicadores historicos 07-02-25.xlsx")
    excel = pd.ExcelFile(archivo)

    hojas = ["Matricula 20-21", "Matricula 21-22", "Matricula 22-23", "Matricula 23-24", "Matricula 24-25"]

    carreras_antiguas = [
        "Ingenieria en sistemas electronicos",
        "Ingenieria en Mecatronica",
        "Ingenieria en sistemas Computacionales",
        "Ingenieria en logistica",
        "Licenciatura en Administracion",
        "Licenciatura en Comercio Internacional y aduanas",
    ]
    carreras_normalizadas = [c.lower() for c in carreras_antiguas]

    periodos_map = {
        "Sep-Dic": ("S-D", 0),
        "Ene-Abr": ("E-A", 1),
        "May-Ago": ("M-A", 1),
        "May- Ago": ("M-A", 1),
    }

    registros = 0

    for hoja in hojas:
        df = excel.parse(hoja).dropna(how="all")
        for i, row in df.iterrows():
            nombre = str(row.get("Unnamed: 1", "")).strip().lower()
            if nombre not in carreras_normalizadas:
                continue

            programa = ProgramaEducativoAntiguo.objects.filter(nombre__icontains=nombre).first()
            if not programa:
                continue

            for col in df.columns:
                for etiqueta, (clave_periodo, offset) in periodos_map.items():
                    if etiqueta in str(col):
                        try:
                            anio_base = hoja.replace("Matricula ", "").split("-")[0]
                            anio = int(anio_base) + offset
                            ciclo, _ = CicloEscolar.objects.get_or_create(anio=anio)
                            periodo, _ = Periodo.objects.get_or_create(clave=clave_periodo, defaults={"nombre": etiqueta})
                            ciclo_periodo, _ = CicloPeriodo.objects.get_or_create(ciclo=ciclo, periodo=periodo)
                            cantidad = int(row[col])
                            MatriculaPorCuatrimestre.objects.update_or_create(
                                ciclo_periodo=ciclo_periodo,
                                programa_antiguo=programa,
                                defaults={"cantidad": cantidad}
                            )
                            registros += 1
                        except:
                            continue

    print(f"✅ {registros} registros cargados en MatriculaPorCuatrimestre.")
    return redirect("matricula_por_cuatrimestre")


def matricula_por_cuatrimestre_view(request):
    ciclos = CicloPeriodo.objects.select_related('ciclo', 'periodo').order_by('ciclo__anio', 'periodo__clave')

    # nuevo filtro tipo_programa
    tipo_programa = request.GET.get('tipo_programa', 'antiguo')  # default: antiguo
    if tipo_programa == 'nuevo':
        programas = ProgramaEducativoNuevo.objects.all().order_by('nombre')
    else:
        programas = ProgramaEducativoAntiguo.objects.all().order_by('nombre')

    filtro_ciclo = request.GET.get('ciclo')
    filtro_programa = request.GET.get('programa')

    registros = MatriculaPorCuatrimestre.objects.select_related('ciclo_periodo', 'programa_antiguo')

    if filtro_ciclo and filtro_ciclo != "Todos":
        registros = registros.filter(ciclo_periodo__id=filtro_ciclo)

    if filtro_programa and filtro_programa != "Todos":
        if tipo_programa == 'nuevo':
            registros = registros.filter(programa_nuevo__id=filtro_programa)
        else:  # antiguo
            registros = registros.filter(programa_antiguo__id=filtro_programa)

    tabla = [
        {
            'programa': (
                r.programa_antiguo.nombre if r.programa_antiguo else
                (r.programa_nuevo.nombre if hasattr(r, 'programa_nuevo') and r.programa_nuevo else '')
            ),
            'periodo': f"{r.ciclo_periodo.periodo.nombre} {r.ciclo_periodo.ciclo.anio}",
            'cantidad': r.cantidad
        }
        for r in registros
    ]

    grafica_data = registros.values(
        anio=F('ciclo_periodo__ciclo__anio'),
        periodo=F('ciclo_periodo__periodo__clave')
    ).annotate(total=Sum('cantidad')).order_by('anio', 'periodo')

    datos_grafica = {
        'labels': [f"{g['anio']} - {g['periodo']}" for g in grafica_data],
        'valores': [g['total'] for g in grafica_data]
    }

    return render(request, "matricula_por_cuatrimestre.html", {
        'ciclos': ciclos,
        'programas': programas,
        'filtro_ciclo': filtro_ciclo,
        'filtro_programa': filtro_programa,
        'tipo_programa': tipo_programa,
        'tabla': tabla,
        'datos_grafica': json.dumps(datos_grafica)
    })


def descargar_plantilla_matricula_cuatrimestre(request):
    ciclo_periodo = CicloPeriodo.objects.order_by('-id').first()

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="plantilla_matricula_cuatrimestre.csv"'

    writer = csv.writer(response)
    writer.writerow(['ciclo_periodo_id', 'programa_antiguo_id', 'cantidad'])

    for programa in ProgramaEducativoAntiguo.objects.all():
        writer.writerow([ciclo_periodo.id if ciclo_periodo else '', programa.id, 0])

    return response


def subir_csv_matricula_cuatrimestre(request):
    if request.method == 'POST' and request.FILES.get('archivo_csv'):
        archivo = request.FILES['archivo_csv']
        decoded = archivo.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded)

        errores = 0
        guardados = 0

        for i, fila in enumerate(reader, start=1):
            try:
                ciclo_id = int(fila['ciclo_periodo_id'])
                programa_id = fila['programa_antiguo_id']
                cantidad = int(fila['cantidad'])

                ciclo = CicloPeriodo.objects.get(id=ciclo_id)
                programa = ProgramaEducativoAntiguo.objects.get(id=programa_id)

                MatriculaPorCuatrimestre.objects.update_or_create(
                    ciclo_periodo=ciclo,
                    programa_antiguo=programa,
                    defaults={'cantidad': cantidad}
                )
                guardados += 1
            except Exception as e:
                errores += 1
                print(f"Fila {i} error: {e}")

        if guardados:
            messages.success(request, f"✅ {guardados} registros guardados.")
        if errores:
            messages.error(request, f"⚠️ {errores} errores encontrados.")

        return HttpResponseRedirect(reverse('matricula_por_cuatrimestre'))

    messages.error(request, "Debes subir un archivo CSV válido.")
    return HttpResponseRedirect(reverse('matricula_por_cuatrimestre'))
