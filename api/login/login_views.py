from django.shortcuts import render, redirect
from django.contrib import messages
from api.models import Usuarios

def login_view(request):
    template_view = "login.html"
    
    if request.method == 'POST':
        usuario_id = request.POST.get('usuario_id')
        password = request.POST.get('password')

        try:
            usuario = Usuarios.objects.get(usuario_id=usuario_id, password=password)
            # Guardar en sesión
            request.session['usuario_id'] = usuario.usuario_id
            request.session['usuario_id'] = usuario.usuario_id
            

            return redirect('administrador')
        except Usuarios.DoesNotExist:
            messages.error(request, '⚠️ Matrícula o contraseña incorrecta ⚠️')

    return render(request, template_view)

def logout_view(request):
    request.session.flush()  # Elimina toda la sesión
    return redirect('login')