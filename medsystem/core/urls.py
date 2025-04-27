from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import (
    DoencaListView, DoencaDetailView, DoencaCreateView,
    PacienteListView, PacienteDetailView, PacienteUpdateView, PacienteCreateView, PacienteDeleteView,
    RegistroMedicoCreateView, NovaDoencaView, DoencaDeleteView,
    BunkertListView, BunkerDetailView, 
    DiagnosticoCreateView, DiagnosticoUpdateView, DiagnosticoDeleteView,
    DoencaUpdateView, BestaCreateView, BestaDetailView, BestaListView, 
    BestaUpdateView, AdicionarDiagnosticoView, HomeView, RelatorioExpedicaoCreateView,
    RelatorioExpedicaoListView, registrar, RelatorioExpedicaoDeleteView, 
    RelatorioExpedicaoDetailView, RelatorioExpedicao, RelatorioExpedicaoUpdateView, BestaDeleteView,
    AnotacaoListView, AnotacaoCreateView, AnotacaoUpdateView, AnotacaoDeleteView, recuperar_senha
)
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('registrar/', registrar, name='registrar'),
    path('doencas/', DoencaListView.as_view(), name='doenca-list'),
    path('doencas/<int:pk>/', DoencaDetailView.as_view(), name='doenca-detail'),
    path('doencas/nova/', DoencaCreateView.as_view(), name='doenca-create'),
    path('pacientes/', PacienteListView.as_view(), name='paciente-list'),
    path('pacientes/<int:pk>/', PacienteDetailView.as_view(), name='paciente-detail'),
    path('pacientes/<int:pk>/editar/', PacienteUpdateView.as_view(), name='paciente-update'),
    path('registros/novo/', RegistroMedicoCreateView.as_view(), name='registro-create'),
    path('doencas/nova-com-sintomas/', NovaDoencaView.as_view(), name='nova-doenca-com-sintomas'),
    path('bunkers/', BunkertListView.as_view(), name='bunker-list'),
    path('pacientes/novo/', PacienteCreateView.as_view(), name='paciente-create'),
    path('doencas/nova/', DoencaCreateView.as_view(), name='doenca-create'),
    path('doencas/', DoencaListView.as_view(), name='doenca-list'),
    path('doencas/nova/', DoencaCreateView.as_view(), name='doenca-create'),
    path('doencas/<int:pk>/', DoencaDetailView.as_view(), name='doenca-detail'),
    path('doencas/<int:pk>/editar/', DoencaUpdateView.as_view(), name='doenca-update'),
    path('doencas/<int:pk>/excluir/', DoencaDeleteView.as_view(), name='doenca-delete'),
    path('bestiario/', BestaListView.as_view(), name='besta-list'),
    path('bestiario/nova/', BestaCreateView.as_view(), name='besta-create'),
    path('bestiario/<int:pk>/', BestaDetailView.as_view(), name='besta-detail'),
    path('bestiario/editar/<int:pk>/', BestaUpdateView.as_view(), name='besta-update'),
    path('bestiario/<int:pk>/excluir/', BestaDeleteView.as_view(), name='besta-delete'),
    path('pacientes/<int:paciente_id>/adicionar-diagnostico/', AdicionarDiagnosticoView.as_view(), name='adicionar-diagnostico'),
    path('', HomeView.as_view(), name='home'),
    
    path('relatorios/', RelatorioExpedicaoListView.as_view(), name='relatorio-list'),
    path('relatorios/novo/', RelatorioExpedicaoCreateView.as_view(), name='relatorio-create'),
    path('relatorios/<int:pk>/', RelatorioExpedicaoDetailView.as_view(), name='relatorio-detail'),
    path('relatorios/<int:pk>/editar/', RelatorioExpedicaoUpdateView.as_view(), name='relatorio-update'),
    path('relatorios/<int:pk>/excluir/', RelatorioExpedicaoDeleteView.as_view(), name='relatorio-delete'),
    
    path('bunkers/<int:pk>/', BunkerDetailView.as_view(), name='bunker-detail'),
    
    path('pacientes/<int:pk>/deletar/', PacienteDeleteView.as_view(), name='paciente-delete'),
    path('pacientes/<int:paciente_id>/diagnostico/', DiagnosticoCreateView.as_view(), name='diagnostico-create'),

    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='home'), name='logout'),

    path('diagnosticos/<int:pk>/editar/', DiagnosticoUpdateView.as_view(), name='diagnostico-update'),
    path('diagnosticos/<int:pk>/excluir/', DiagnosticoDeleteView.as_view(), name='diagnostico-delete'),

    path('anotacoes/', AnotacaoListView.as_view(), name='anotacao-list'),
    path('anotacoes/nova/', AnotacaoCreateView.as_view(), name='anotacao-create'),
    path('anotacoes/editar/<int:pk>/', AnotacaoUpdateView.as_view(), name='anotacao-update'),
    path('anotacoes/excluir/<int:pk>/', AnotacaoDeleteView.as_view(), name='anotacao-delete'),

    path('recuperar-senha/', recuperar_senha, name='recuperar_senha'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)