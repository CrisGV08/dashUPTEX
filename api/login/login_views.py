from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.urls import reverse

def login_view(request):
    template_view = "login.html"
    
    if request.method == 'POST':
        usuario_id = request.POST.get('usuario_id')
        password = request.POST.get('password')

        # Autenticación usando el modelo de usuario por defecto de Django
        user = authenticate(request, username=usuario_id, password=password)

        if user is not None:
            login(request, user)
            # ✅ Redirige a la vista de administrador si el login fue exitoso
            return redirect(reverse('examen_admision'))
        else:
            messages.error(request, '⚠️ Usuario o contraseña incorrectos ⚠️')

    return render(request, template_view)

def logout_view(request):
    logout(request)
    return redirect('login')
