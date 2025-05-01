from django.shortcuts import render, redirect
from django.contrib import messages
from api.models import EficienciaTerminal, CicloEscolar, Periodo, CicloPeriodo, ProgramaEducativoAntiguo, ProgramaEducativoNuevo
from api.Administrador.eficiencia_terminal_tools import procesar_excel_eficiencia_terminal
from django.db.models import Avg

def eficiencia_terminal_view(request):
    if request.method == 'POST' and request.FILES.get('archivo_excel'):
        archivo = request.FILES['archivo_excel']
        exito, mensaje = procesar_excel_eficiencia_terminal(archivo)
        if exito:
            messages.success(request, mensaje)
        else:
            messages.error(request, mensaje)
        return redirect('eficiencia_terminal')

    eficiencia = EficienciaTerminal.objects.all()

    eficiencia_promedio = []
    for prog in set(list(eficiencia.values_list("programa_antiguo__nombre", flat=True)) +
                    list(eficiencia.values_list("programa_nuevo__nombre", flat=True))):
        if prog:
            datos = eficiencia.filter(programa_antiguo__nombre=prog) | eficiencia.filter(programa_nuevo__nombre=prog)
            promedio = round(sum([x.porcentaje_eficiencia for x in datos]) / len(datos), 2)
            eficiencia_promedio.append({'programa': prog, 'promedio': promedio})

    ciclos = sorted(set(cp.ciclo.anio for cp in CicloPeriodo.objects.all()))

    context = {
        'eficiencia': eficiencia,
        'eficiencia_por_programa': eficiencia_promedio,
        'ciclos': ciclos,
    }

    return render(request, 'eficiencia_terminal.html', context)
