from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

class MedicoRequiredMixin(LoginRequiredMixin):
    """Verifica se o usuário é médico ou administrador"""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.tipo not in ['MED', 'ADM']:
            raise PermissionDenied("Apenas médicos e administradores podem acessar esta página.")
        return super().dispatch(request, *args, **kwargs)

class AdminRequiredMixin(LoginRequiredMixin):
    """Verifica se o usuário é administrador"""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.tipo != 'ADM':
            raise PermissionDenied("Apenas administradores podem acessar esta página.")
        return super().dispatch(request, *args, **kwargs)