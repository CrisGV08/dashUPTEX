from django.shortcuts import render

def egresados_view(request):
    return render(request, 'egresados.html')

