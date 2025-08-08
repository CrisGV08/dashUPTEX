from django.shortcuts import redirect
from django.conf import settings

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.login_url = settings.LOGIN_URL

    def __call__(self, request):
        print("🧩 Middleware ejecutado:", request.path)

        # Proteger rutas que inicien con /administrador/
        if request.path.startswith('/administrador/'):
            if not request.user.is_authenticated:
                return redirect(f'{self.login_url}?next={request.path}')
            
            # Solo permitir acceso a usuarios con permisos (is_staff o superuser)
            if not (request.user.is_staff or request.user.is_superuser):
                return redirect('/no-autorizado/')  # 👈 Puedes crear una vista para mostrar error

        return self.get_response(request)
