from django.shortcuts import render
from api.models import GeneracionCarrera

def titulados_historicos_actual_usuario_view(request):
    generaciones = GeneracionCarrera.objects.select_related('programa_antiguo', 'programa_nuevo').order_by('fecha_ingreso')

    context = {
        'generaciones': generaciones
    }
    return render(request, 'titulados_historicos_actual_usuario.html', context)