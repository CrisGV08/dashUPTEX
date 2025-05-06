from django.shortcuts import render
from django.db.models import Sum
from api.models import EficienciaTerminal

def eficiencia_terminal_usuario_view(request):
    eficiencia = EficienciaTerminal.objects.select_related('programa_antiguo', 'programa_nuevo', 'ciclo_periodo')

    eficiencia_por_programa = []
    ciclos = set()

    for item in eficiencia:
        nombre = item.programa_antiguo.nombre if item.programa_antiguo else item.programa_nuevo.nombre
        ciclo = item.ciclo_periodo.ciclo.anio
        ciclos.add(ciclo)

        eficiencia_por_programa.append({
            'programa': nombre,
            'ciclo': ciclo,
            'promedio': round((item.egresados / item.matricula_ingreso) * 100, 2) if item.matricula_ingreso else 0
        })

    ciclos = sorted(list(ciclos))

    context = {
        'eficiencia_por_programa': eficiencia_por_programa,
        'ciclos': ciclos,
    }
    return render(request, 'eficiencia_terminal_usuario.html', context)