from django.shortcuts import render

def home_view(request):
    return render(request, 'index.html')

def home_calificaciones(request):
    return render(request, 'calificaciones.html')

def home_aprobados(request):
    return render(request, 'aprobados.html')

def home_reprobados(request):  # ✅ Asegúrate de que esta función esté definida
    return render(request, 'reprobados.html')

def home_promedios(request):
    return render(request, 'promedios.html')

def home_mapa(request):
    return render(request, 'mapa.html')