from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

class MedicoRequiredMixin(LoginRequiredMixin):
    """Verifica se o usuário é médico"""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.tipo != 'MED':
            raise PermissionDenied("Apenas médicos podem acessar esta página.")
        return super().dispatch(request, *args, **kwargs)