from django.urls import path
from .views import (
    DoencaListView, DoencaDetailView, DoencaCreateView,
    PacienteListView, PacienteDetailView, PacienteUpdateView,
    RegistroMedicoCreateView, NovaDoencaView, buscar_sintomas,
    BunkerCreateView, BunkertListView, PacienteCreateView,
    DoencaUpdateView, BestaCreateView, BestaDetailView, BestaListView, 
    BestaUpdateView, AdicionarDiagnosticoView, adicionar_sintoma, remover_sintoma,
)

urlpatterns = [
    path('doencas/', DoencaListView.as_view(), name='doenca-list'),
    path('doencas/<int:pk>/', DoencaDetailView.as_view(), name='doenca-detail'),
    path('doencas/nova/', DoencaCreateView.as_view(), name='doenca-create'),
    path('pacientes/', PacienteListView.as_view(), name='paciente-list'),
    path('pacientes/<int:pk>/', PacienteDetailView.as_view(), name='paciente-detail'),
    path('pacientes/<int:pk>/editar/', PacienteUpdateView.as_view(), name='paciente-update'),
    path('registros/novo/', RegistroMedicoCreateView.as_view(), name='registro-create'),
    path('doencas/nova-com-sintomas/', NovaDoencaView.as_view(), name='nova-doenca-com-sintomas'),
    path('buscar-sintomas/', buscar_sintomas, name='buscar-sintomas'),
    path('bunkers/', BunkertListView.as_view(), name='bunker-list'),
    path('bunkers/novo/', BunkerCreateView.as_view(), name='bunker-create'),
    path('pacientes/novo/', PacienteCreateView.as_view(), name='paciente-create'),
    path('doencas/nova/', DoencaCreateView.as_view(), name='doenca-create'),
    path('doencas/editar/<int:pk>/', DoencaUpdateView.as_view(), name='doenca-update'),
    path('pacientes/<int:paciente_id>/adicionar-diagnostico/', AdicionarDiagnosticoView.as_view(), name='adicionar-diagnostico'),
    path('pacientes/<int:paciente_id>/adicionar-sintoma/', adicionar_sintoma, name='adicionar-sintoma'),
    path('pacientes/<int:paciente_id>/remover-sintoma/<int:sintoma_id>/', remover_sintoma, name='remover-sintoma'),
    path('bestiario/', BestaListView.as_view(), name='besta-list'),
    path('bestiario/nova/', BestaCreateView.as_view(), name='besta-create'),
    path('bestiario/<int:pk>/', BestaDetailView.as_view(), name='besta-detail'),
    path('bestiario/editar/<int:pk>/', BestaUpdateView.as_view(), name='besta-update'),
]