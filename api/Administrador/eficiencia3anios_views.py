# api/Administrador/eficiencia3anios_views.py

from django.shortcuts import render

def eficiencia_3anios_view(request):
    context = {}  # No mandamos nada todavía, solo contexto vacío
    return render(request, 'eficiencia_3anios.html', context)
