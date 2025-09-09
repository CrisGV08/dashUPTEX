# Vista de solo lectura para usuarios
from django.shortcuts import render

def titulados_tsu_inge_usuario_view(request):
    # Usa los endpoints nombrados 'tsui_api' y 'tsui_programas_api' (del admin)
    # Solo renderiza la página de usuario.
    return render(request, "titulados_tsu_inge_usuario.html", {})
