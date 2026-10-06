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
    AnotacaoListView, AnotacaoCreateView, AnotacaoDetailView, AnotacaoUpdateView, AnotacaoDeleteView, recuperar_senha, DiagnosticoDetailView,
    RacaListView, RacaDetailView, RacaCreateView, RacaUpdateView, RacaDeleteView,
    IngredienteListView, IngredienteDetailView, IngredienteCreateView, IngredienteUpdateView, IngredienteDeleteView,
    RemedioListView, RemedioDetailView, RemedioCreateView, RemedioUpdateView, RemedioDeleteView, alterar_tipo_usuario,
    UsuarioUpdateView, UsuarioDeleteView
)
from . import views_acervo
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('registrar/', registrar, name='registrar'),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='home'), name='logout'),
    path('recuperar-senha/', recuperar_senha, name='recuperar_senha'),
    path('usuario/<int:usuario_id>/alterar-tipo/', alterar_tipo_usuario, name='alterar-tipo-usuario'),
    path('usuario/<int:pk>/editar/', UsuarioUpdateView.as_view(), name='usuario-update'),
    path('usuario/<int:pk>/excluir/', UsuarioDeleteView.as_view(), name='usuario-delete'),
    
    # Doenças
    path('doencas/', DoencaListView.as_view(), name='doenca-list'),
    path('doencas/<int:pk>/', DoencaDetailView.as_view(), name='doenca-detail'),
    path('doencas/nova/', DoencaCreateView.as_view(), name='doenca-create'),
    path('doencas/<int:pk>/editar/', DoencaUpdateView.as_view(), name='doenca-update'),
    path('doencas/<int:pk>/excluir/', DoencaDeleteView.as_view(), name='doenca-delete'),
    path('doencas/nova-com-sintomas/', NovaDoencaView.as_view(), name='nova-doenca-com-sintomas'),
    
    # Pacientes
    path('pacientes/', PacienteListView.as_view(), name='paciente-list'),
    path('pacientes/<int:pk>/', PacienteDetailView.as_view(), name='paciente-detail'),
    path('pacientes/novo/', PacienteCreateView.as_view(), name='paciente-create'),
    path('pacientes/<int:pk>/editar/', PacienteUpdateView.as_view(), name='paciente-update'),
    path('pacientes/<int:pk>/deletar/', PacienteDeleteView.as_view(), name='paciente-delete'),
    
    # Diagnósticos
    path('pacientes/<int:paciente_id>/diagnostico/', DiagnosticoCreateView.as_view(), name='diagnostico-create'),
    path('pacientes/<int:paciente_id>/adicionar-diagnostico/', AdicionarDiagnosticoView.as_view(), name='adicionar-diagnostico'),
    path('diagnostico/<int:pk>/', DiagnosticoDetailView.as_view(), name='diagnostico-detail'),
    path('diagnosticos/<int:pk>/editar/', DiagnosticoUpdateView.as_view(), name='diagnostico-update'),
    path('diagnosticos/<int:pk>/excluir/', DiagnosticoDeleteView.as_view(), name='diagnostico-delete'),
    
    # Registros Médicos
    path('registros/novo/', RegistroMedicoCreateView.as_view(), name='registro-create'),
    
    # Cidades (antigo Bunkers)
    path('cidades/', BunkertListView.as_view(), name='bunker-list'),
    path('cidades/<int:pk>/', BunkerDetailView.as_view(), name='bunker-detail'),
    
    # Bestiário
    path('bestiario/', BestaListView.as_view(), name='besta-list'),
    path('bestiario/nova/', BestaCreateView.as_view(), name='besta-create'),
    path('bestiario/<int:pk>/', BestaDetailView.as_view(), name='besta-detail'),
    path('bestiario/editar/<int:pk>/', BestaUpdateView.as_view(), name='besta-update'),
    path('bestiario/<int:pk>/excluir/', BestaDeleteView.as_view(), name='besta-delete'),
    
    # Relatórios de Expedição
    path('relatorios/', RelatorioExpedicaoListView.as_view(), name='relatorio-list'),
    path('relatorios/novo/', RelatorioExpedicaoCreateView.as_view(), name='relatorio-create'),
    path('relatorios/<int:pk>/', RelatorioExpedicaoDetailView.as_view(), name='relatorio-detail'),
    path('relatorios/<int:pk>/editar/', RelatorioExpedicaoUpdateView.as_view(), name='relatorio-update'),
    path('relatorios/<int:pk>/excluir/', RelatorioExpedicaoDeleteView.as_view(), name='relatorio-delete'),

    # Anotações Pessoais
    path('anotacoes/', AnotacaoListView.as_view(), name='anotacao-list'),
    path('anotacoes/nova/', AnotacaoCreateView.as_view(), name='anotacao-create'),
    path('anotacoes/<int:pk>/', AnotacaoDetailView.as_view(), name='anotacao-detail'),
    path('anotacoes/editar/<int:pk>/', AnotacaoUpdateView.as_view(), name='anotacao-update'),
    path('anotacoes/excluir/<int:pk>/', AnotacaoDeleteView.as_view(), name='anotacao-delete'),
    
    # Raças
    path('racas/', RacaListView.as_view(), name='raca-list'),
    path('racas/<int:pk>/', RacaDetailView.as_view(), name='raca-detail'),
    path('racas/nova/', RacaCreateView.as_view(), name='raca-create'),
    path('racas/<int:pk>/editar/', RacaUpdateView.as_view(), name='raca-update'),
    path('racas/<int:pk>/excluir/', RacaDeleteView.as_view(), name='raca-delete'),
    
    # Ingredientes (apenas médicos)
    path('ingredientes/', IngredienteListView.as_view(), name='ingrediente-list'),
    path('ingredientes/<int:pk>/', IngredienteDetailView.as_view(), name='ingrediente-detail'),
    path('ingredientes/novo/', IngredienteCreateView.as_view(), name='ingrediente-create'),
    path('ingredientes/<int:pk>/editar/', IngredienteUpdateView.as_view(), name='ingrediente-update'),
    path('ingredientes/<int:pk>/excluir/', IngredienteDeleteView.as_view(), name='ingrediente-delete'),
    
    # Remédios (apenas médicos)
    path('remedios/', RemedioListView.as_view(), name='remedio-list'),
    path('remedios/<int:pk>/', RemedioDetailView.as_view(), name='remedio-detail'),
    path('remedios/novo/', RemedioCreateView.as_view(), name='remedio-create'),
    path('remedios/<int:pk>/editar/', RemedioUpdateView.as_view(), name='remedio-update'),
    path('remedios/<int:pk>/excluir/', RemedioDeleteView.as_view(), name='remedio-delete'),

    # Acervo (biblioteca)
    path('acervo/', views_acervo.AcervoView.as_view(), name='acervo'),
    path('acervo/temas/novo/', views_acervo.TemaCreateView.as_view(), name='tema-create'),
    path('acervo/temas/<int:pk>/', views_acervo.TemaDetailView.as_view(), name='tema-detail'),
    path('acervo/temas/<int:pk>/editar/', views_acervo.TemaUpdateView.as_view(), name='tema-update'),
    path('acervo/temas/<int:pk>/excluir/', views_acervo.TemaDeleteView.as_view(), name='tema-delete'),
    path('acervo/livros/novo/', views_acervo.LivroCreateView.as_view(), name='livro-create'),
    path('acervo/livros/<int:pk>/', views_acervo.LivroDetailView.as_view(), name='livro-detail'),
    path('acervo/livros/<int:pk>/editar/', views_acervo.LivroUpdateView.as_view(), name='livro-update'),
    path('acervo/livros/<int:pk>/excluir/', views_acervo.LivroDeleteView.as_view(), name='livro-delete'),
    path('acervo/livros/<int:pk>/comentarios/', views_acervo.comentario_livro_criar, name='comentario-livro-create'),
    path('acervo/comentarios/<int:pk>/excluir/', views_acervo.comentario_livro_excluir, name='comentario-livro-delete'),

    # Teorização (mapas mentais pessoais)
    path('teorizacao/', views_acervo.MapaListView.as_view(), name='mapa-list'),
    path('teorizacao/novo/', views_acervo.MapaCreateView.as_view(), name='mapa-create'),
    path('teorizacao/<int:pk>/', views_acervo.MapaDetailView.as_view(), name='mapa-detail'),
    path('teorizacao/<int:pk>/editar/', views_acervo.MapaUpdateView.as_view(), name='mapa-update'),
    path('teorizacao/<int:pk>/excluir/', views_acervo.MapaDeleteView.as_view(), name='mapa-delete'),
    path('teorizacao/<int:pk>/salvar/', views_acervo.mapa_salvar, name='mapa-salvar'),
    path('teorizacao/<int:pk>/imagens/', views_acervo.mapa_imagem_enviar, name='mapa-imagem-enviar'),
    path('teorizacao/<int:pk>/estado/', views_acervo.mapa_estado, name='mapa-estado'),
    path('teorizacao/<int:pk>/compartilhamento/', views_acervo.mapa_compartilhamento, name='mapa-compartilhamento'),
    path('teorizacao/<int:pk>/sair/', views_acervo.mapa_sair, name='mapa-sair'),
    path('teorizacao/compartilhado/<uuid:token>/', views_acervo.mapa_compartilhado, name='mapa-compartilhado'),
    path('teorizacao/compartilhado/<uuid:token>/estado/', views_acervo.mapa_compartilhado_estado, name='mapa-compartilhado-estado'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)