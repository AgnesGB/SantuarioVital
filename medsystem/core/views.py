from django.views.generic import DeleteView, ListView, DetailView, CreateView, UpdateView, TemplateView
from django.urls import reverse_lazy, reverse
from django.db.models import Q
from django.http import JsonResponse
from .models import Doenca, RelatorioExpedicao, Usuario, Besta, Cidade, Paciente, RegistroMedico, Diagnostico, AnotacaoPessoal, Raca, Ingrediente, Remedio, RemedioIngrediente
from .forms import UsuarioCreationForm, DoencaForm, BestaForm, PacienteForm, RegistroMedicoForm, CidadeForm, DiagnosticoForm, AnotacaoPessoalForm, RacaForm, IngredienteForm, RemedioForm, RemedioIngredienteFormSet
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from .mixins import MedicoRequiredMixin, AdminRequiredMixin
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import datetime
from django.contrib.auth import get_user_model

def registrar(request):
    if request.method == 'POST':
        form = UsuarioCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UsuarioCreationForm()
    return render(request, 'core/registrar.html', {'form': form})

@login_required
@require_POST
def alterar_tipo_usuario(request, usuario_id):
    # Verifica se o usuário logado é admin
    if request.user.tipo != 'ADM':
        messages.error(request, 'Apenas administradores podem alterar o tipo de usuário.')
        return redirect('home')
    
    usuario = get_object_or_404(Usuario, id=usuario_id)
    novo_tipo = request.POST.get('tipo')
    
    if novo_tipo in ['MED', 'OUT', 'ADM']:
        usuario.tipo = novo_tipo
        usuario.save()
        messages.success(request, f'Tipo de usuário de {usuario.nickname} alterado para {usuario.get_tipo_display()}.')
    else:
        messages.error(request, 'Tipo de usuário inválido.')
    
    return redirect('home')

class HomeView(TemplateView):
    template_name = 'core/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['usuarios'] = Usuario.objects.all().order_by('nickname')
        return context

class BunkerDetailView(DetailView):
    model = Cidade
    template_name = 'core/bunker_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['membros'] = Usuario.objects.filter(cidade=self.object)
        context['pacientes'] = Paciente.objects.filter(cidade=self.object).only('nome', 'idade')
        return context

class BunkertListView(ListView):
    model = Cidade
    template_name = 'core/bunker_list.html'
    context_object_name = 'bunkers'

class DoencaListView(LoginRequiredMixin, ListView):
    model = Doenca
    template_name = 'core/doenca_list.html'
    context_object_name = 'doencas'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        nome = self.request.GET.get('nome')
        tipo = self.request.GET.get('tipo')
        sintoma_query = self.request.GET.get('sintoma', '').strip()
        
        if nome:
            queryset = queryset.filter(nome__icontains=nome)
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        if sintoma_query:
            # Divide os termos de busca por vírgula ou espaço
            termos = [termo.strip() for termo in sintoma_query.replace(',', ' ').split()]
            # Cria uma consulta OR para cada termo
            q_objects = Q()
            for termo in termos:
                q_objects |= Q(sintomas__icontains=termo)
            queryset = queryset.filter(q_objects)
            
        return queryset

class DoencaDetailView(LoginRequiredMixin, DetailView):
    model = Doenca
    template_name = 'core/doenca_detail.html'
    context_object_name = 'doenca'

class DoencaCreateView(MedicoRequiredMixin, CreateView):
    model = Doenca
    form_class = DoencaForm
    template_name = 'core/doenca_form.html'
    success_url = reverse_lazy('doenca-list')

class DoencaUpdateView(MedicoRequiredMixin, UpdateView):
    model = Doenca
    form_class = DoencaForm
    template_name = 'core/doenca_form.html'
    success_url = reverse_lazy('doenca-list')

class DoencaDeleteView(MedicoRequiredMixin, DeleteView):
    model = Doenca
    template_name = 'core/doenca_confirm_delete.html'
    success_url = reverse_lazy('doenca-list')

class AdicionarDiagnosticoView(MedicoRequiredMixin, CreateView):
    model = Diagnostico
    form_class = DiagnosticoForm
    template_name = 'core/adicionar_diagnostico.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['paciente'] = Paciente.objects.get(pk=self.kwargs['paciente_id'])
        return kwargs
    
    def form_valid(self, form):
        paciente = Paciente.objects.get(pk=self.kwargs['paciente_id'])
        form.instance.paciente = paciente
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('paciente-detail', kwargs={'pk': self.kwargs['paciente_id']})
    
class RegistroMedicoCreateView(MedicoRequiredMixin, CreateView):
    model = RegistroMedico
    form_class = RegistroMedicoForm
    template_name = 'core/registro_form.html'
    
    def get_success_url(self):
        return reverse_lazy('paciente-detail', kwargs={'pk': self.object.paciente.pk})
    
    def get_initial(self):
        initial = super().get_initial()
        paciente_id = self.request.GET.get('paciente_id')
        if paciente_id:
            initial['paciente'] = Paciente.objects.get(pk=paciente_id)
        return initial
    
    def form_valid(self, form):
        sintomas_texto = form.cleaned_data.get('sintomas_texto', '')
        doenca = self.encontrar_doenca(sintomas_texto)
        form.instance.doenca = doenca
        return super().form_valid(form)
    
    def encontrar_doenca(self, sintomas_texto):
        # Busca por correspondência textual nos sintomas
        doencas = Doenca.objects.filter(
            Q(sintomas__nome__icontains=sintomas_texto) |
            Q(sintomas__descricao__icontains=sintomas_texto)
        ).distinct()
        
        # Tenta encontrar a doença que melhor se encaixa
        for doenca in doencas:
            sintomas_doenca = " ".join([s.nome for s in doenca.sintomas.all()])
            if sintomas_texto.lower() in sintomas_doenca.lower():
                return doenca
        return None

class DoencaCreateView(MedicoRequiredMixin, CreateView):
    model = Doenca
    form_class = DoencaForm
    template_name = 'core/doenca_form.html'
    success_url = reverse_lazy('doenca-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Você pode adicionar lógica adicional aqui se necessário
        return response

class NovaDoencaView(MedicoRequiredMixin, CreateView):
    model = Doenca
    form_class = DoencaForm
    template_name = 'core/nova_doenca.html'
    success_url = reverse_lazy('doenca-list')
    
    def get_initial(self):
        initial = super().get_initial()
        sintomas_texto = self.request.GET.get('sintomas_texto', '')
        if sintomas_texto:
            initial['sintomas_texto'] = sintomas_texto
        return initial

class BestaListView(LoginRequiredMixin, ListView):
    model = Besta
    template_name = 'core/besta_list.html'
    context_object_name = 'bestas'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtros
        nome = self.request.GET.get('nome')
        nivel_ameaca = self.request.GET.get('nivel_ameaca')
        habilidades = self.request.GET.get('habilidades')
        
        if nome:
            queryset = queryset.filter(nome__icontains=nome)
        if nivel_ameaca:
            queryset = queryset.filter(nivel_ameaca=nivel_ameaca)
        if habilidades:
            queryset = queryset.filter(habilidades__icontains=habilidades)
            
        return queryset.order_by('nome')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Adiciona os parâmetros de filtro ao contexto para manter os valores nos campos
        context['request'] = self.request
        return context

class BestaCreateView(LoginRequiredMixin, CreateView):
    model = Besta
    form_class = BestaForm
    template_name = 'core/besta_form.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Criatura criada com sucesso!')
        return response

    def get_success_url(self):
        return reverse('besta-detail', kwargs={'pk': self.object.pk})

class BestaUpdateView(LoginRequiredMixin, UpdateView):
    model = Besta
    form_class = BestaForm
    template_name = 'core/besta_form.html'

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        # Verifica se o usuário é admin
        if request.user.tipo != 'ADM':
            messages.error(request, 'Apenas administradores podem editar criaturas.')
            return redirect('besta-detail', pk=obj.pk)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Criatura atualizada com sucesso!')
        return response

    def get_success_url(self):
        return reverse('besta-detail', kwargs={'pk': self.object.pk})

class BestaDetailView(LoginRequiredMixin, DetailView):
    model = Besta
    template_name = 'core/besta_detail.html'
    context_object_name = 'besta'

class BestaDeleteView(LoginRequiredMixin, DeleteView):
    model = Besta
    template_name = 'core/besta_confirm_delete.html'
    success_url = reverse_lazy('besta-list')

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        # Verifica se o usuário é admin
        if request.user.tipo != 'ADM':
            messages.error(request, 'Apenas administradores podem excluir criaturas.')
            return redirect('besta-detail', pk=obj.pk)
        return super().dispatch(request, *args, **kwargs)

# diagnostico
class DiagnosticoCreateView(MedicoRequiredMixin, CreateView):
    model = Diagnostico
    form_class = DiagnosticoForm
    template_name = 'core/diagnostico_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['paciente'] = get_object_or_404(Paciente, pk=self.kwargs['paciente_id'])
        context['doencas'] = Doenca.objects.all()
        context['remedios'] = Remedio.objects.all()
        return context

    def form_valid(self, form):
        form.instance.paciente = get_object_or_404(Paciente, pk=self.kwargs['paciente_id'])
        form.instance.responsavel = self.request.user
        
        # Processa o campo tratado (checkbox)
        form.instance.tratado = self.request.POST.get('tratado') == 'true'
        
        # Salva o diagnóstico primeiro
        response = super().form_valid(form)
        
        # Processa as hipóteses (enviadas como lista de checkboxes)
        hipoteses_ids = self.request.POST.getlist('hipoteses')
        hipoteses_ids = [int(id) for id in hipoteses_ids if id]
        self.object.hipoteses.set(hipoteses_ids)
        
        # Processa os remédios prescritos
        remedios_ids = self.request.POST.getlist('remedios')
        remedios_ids = [int(id) for id in remedios_ids if id]
        self.object.remedios.set(remedios_ids)
        
        messages.success(self.request, 'Diagnóstico salvo com sucesso!')
        return response

    def get_success_url(self):
        return reverse('paciente-detail', kwargs={'pk': self.kwargs['paciente_id']})
    
class DiagnosticoUpdateView(MedicoRequiredMixin, UpdateView):
    model = Diagnostico
    template_name = 'core/diagnostico_form.html'
    fields = ['sintomas', 'observacoes', 'doenca']  # Campos básicos

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['paciente'] = self.object.paciente
        context['doencas'] = Doenca.objects.all()
        context['remedios'] = Remedio.objects.all()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        
        if form.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)

    def form_valid(self, form):
        # Processa o campo tratado (checkbox)
        form.instance.tratado = self.request.POST.get('tratado') == 'true'
        
        response = super().form_valid(form)
        
        # Processa as hipóteses (enviadas como lista de checkboxes)
        hipoteses_ids = self.request.POST.getlist('hipoteses')
        hipoteses_ids = [int(id) for id in hipoteses_ids if id]
        self.object.hipoteses.set(hipoteses_ids)
        
        # Processa os remédios prescritos
        remedios_ids = self.request.POST.getlist('remedios')
        remedios_ids = [int(id) for id in remedios_ids if id]
        self.object.remedios.set(remedios_ids)
        
        messages.success(self.request, 'Diagnóstico atualizado com sucesso!')
        return response

    def get_success_url(self):
        return reverse('paciente-detail', kwargs={'pk': self.object.paciente.pk})

class DiagnosticoDeleteView(MedicoRequiredMixin, DeleteView):
    model = Diagnostico
    template_name = 'core/diagnostico_confirm_delete.html'

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Diagnóstico excluído com sucesso!')
        return super().delete(request, *args, **kwargs)

    def get_success_url(self):
        paciente_id = self.object.paciente.pk
        return reverse('paciente-detail', kwargs={'pk': paciente_id})

class DiagnosticoDetailView(LoginRequiredMixin, DetailView):
    model = Diagnostico
    template_name = 'core/diagnostico_detail.html'
    context_object_name = 'diagnostico'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Adiciona os registros médicos do paciente (não do diagnóstico diretamente)
        context['registros_paciente'] = self.object.paciente.registros.all()
        return context

#paciente
class PacienteDeleteView(MedicoRequiredMixin, DeleteView):
    model = Paciente
    template_name = 'core/paciente_confirm_delete.html'
    success_url = reverse_lazy('paciente-list')

class PacienteCreateView(MedicoRequiredMixin, CreateView):
    model = Paciente
    form_class = PacienteForm
    template_name = 'core/paciente_form.html'
    
    def form_valid(self, form):
        try:
            self.object = form.save()
            messages.success(self.request, 'Salvo com sucesso!')
            return redirect('paciente-list')
        except Exception as e:
            messages.error(self.request, f'ERRO GRAVE: {str(e)}')
            return self.form_invalid(form)

class PacienteUpdateView(MedicoRequiredMixin, UpdateView):
    model = Paciente
    form_class = PacienteForm
    template_name = 'core/paciente_form.html'
    
    def get_success_url(self):
        return reverse_lazy('paciente-detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        messages.success(self.request, 'Paciente atualizado com sucesso!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Erro ao atualizar paciente. Verifique os dados.')
        return super().form_invalid(form)
    
class PacienteListView(MedicoRequiredMixin, ListView):
    model = Paciente
    template_name = 'core/paciente_list.html'
    context_object_name = 'pacientes'
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('cidade').order_by('nome')  # Ordenação padrão por nome
        
        # Aplica filtros se existirem
        nome = self.request.GET.get('nome')
        status = self.request.GET.get('status')
        afinidade = self.request.GET.get('afinidade')
        cidade = self.request.GET.get('cidade')
        
        if nome:
            queryset = queryset.filter(nome__icontains=nome)
        if status:
            queryset = queryset.filter(status=status)
        if afinidade:
            queryset = queryset.filter(afinidade=afinidade)
        if cidade:
            queryset = queryset.filter(cidade_id=cidade)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cidades'] = Cidade.objects.all()
        context['status_choices'] = Paciente.STATUS_CHOICES
        context['afinidade_choices'] = Paciente.AFINIDADE
        
        # Adiciona flag para saber se há filtros ativos
        context['has_filters'] = any([
            self.request.GET.get('nome'),
            self.request.GET.get('status'),
            self.request.GET.get('afinidade'),
            self.request.GET.get('cidade')
        ])
        
        return context

class PacienteDetailView(MedicoRequiredMixin, DetailView):
    model = Paciente
    template_name = 'core/paciente_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['diagnosticos'] = self.object.diagnostico_set.all()
        context['todas_doencas'] = Doenca.objects.all()
        
        # Contagens de diagnósticos
        diagnosticos = self.object.diagnostico_set.all()
        context['total_diagnosticos'] = diagnosticos.count()
        context['diagnosticos_tratados'] = diagnosticos.filter(tratado=True).count()
        context['diagnosticos_nao_tratados'] = diagnosticos.filter(tratado=False).count()
        
        return context

class RelatorioExpedicaoListView(LoginRequiredMixin, ListView):
    model = RelatorioExpedicao
    template_name = 'core/relatorio_list.html'
    context_object_name = 'relatorios'
    ordering = ['-data']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtro por título
        titulo = self.request.GET.get('titulo')
        if titulo:
            queryset = queryset.filter(titulo__icontains=titulo)
        
        # Filtro por localização
        localizacao = self.request.GET.get('localizacao')
        if localizacao:
            queryset = queryset.filter(localizacao__icontains=localizacao)
        
        # Filtro por autor
        autor = self.request.GET.get('autor')
        if autor:
            queryset = queryset.filter(autor__nickname__icontains=autor)
        
        # Busca geral
        busca = self.request.GET.get('busca')
        if busca:
            queryset = queryset.filter(
                Q(titulo__icontains=busca) |
                Q(localizacao__icontains=busca) |
                Q(descobertas__icontains=busca) |
                Q(observacoes__icontains=busca)
            )
        
        return queryset

class RelatorioExpedicaoCreateView(LoginRequiredMixin, CreateView):
    model = RelatorioExpedicao
    fields = ['titulo', 'localizacao', 'descobertas', 'observacoes']
    template_name = 'core/relatorio_form.html'
    success_url = reverse_lazy('relatorio-list')
    
    def form_valid(self, form):
        form.instance.autor = self.request.user
        messages.success(self.request, 'Relatório criado com sucesso!')
        return super().form_valid(form)

class RelatorioExpedicaoDetailView(LoginRequiredMixin, DetailView):
    model = RelatorioExpedicao
    template_name = 'core/relatorio_detail.html'
    context_object_name = 'relatorio'  # Isso define o nome da variável no template

class RelatorioExpedicaoUpdateView(LoginRequiredMixin, UpdateView):
    model = RelatorioExpedicao
    fields = ['titulo', 'localizacao', 'descobertas', 'observacoes']
    template_name = 'core/relatorio_form.html'
    success_url = reverse_lazy('relatorio-list')
    
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        # Verifica se o usuário é o autor ou admin
        if obj.autor != request.user and request.user.tipo != 'ADM':
            messages.error(request, 'Você só pode editar seus próprios relatórios.')
            return redirect('relatorio-detail', pk=obj.pk)
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        messages.success(self.request, 'Relatório atualizado com sucesso!')
        return super().form_valid(form)

class RelatorioExpedicaoDeleteView(LoginRequiredMixin, DeleteView):
    model = RelatorioExpedicao
    template_name = 'core/relatorio_confirm_delete.html'
    success_url = reverse_lazy('relatorio-list')
    
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        # Verifica se o usuário é o autor ou admin
        if obj.autor != request.user and request.user.tipo != 'ADM':
            messages.error(request, 'Você só pode excluir seus próprios relatórios.')
            return redirect('relatorio-detail', pk=obj.pk)
        return super().dispatch(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Relatório excluído com sucesso!')
        return super().delete(request, *args, **kwargs)

class AnotacaoListView(LoginRequiredMixin, ListView):
    model = AnotacaoPessoal
    template_name = 'core/anotacao_list.html'
    context_object_name = 'anotacoes'

    def get_queryset(self):
        queryset = super().get_queryset().filter(usuario=self.request.user)
        
        # Busca geral
        busca = self.request.GET.get('busca')
        if busca:
            queryset = queryset.filter(
                Q(titulo__icontains=busca) |
                Q(conteudo__icontains=busca) |
                Q(tags__icontains=busca)
            )
        
        # Filtros específicos
        titulo = self.request.GET.get('titulo')
        if titulo:
            queryset = queryset.filter(titulo__icontains=titulo)
        
        tags = self.request.GET.get('tags')
        data = self.request.GET.get('data')
        
        if tags:
            tags_list = [tag.strip() for tag in tags.split(',')]
            for tag in tags_list:
                queryset = queryset.filter(tags__icontains=tag)
        
        if data:
            try:
                date_obj = datetime.strptime(data, '%Y-%m-%d').date()
                queryset = queryset.filter(
                    Q(data_criacao__date=date_obj) |
                    Q(data_atualizacao__date=date_obj))
            except ValueError:
                pass
                
        return queryset

class AnotacaoCreateView(LoginRequiredMixin, CreateView):
    model = AnotacaoPessoal
    form_class = AnotacaoPessoalForm
    template_name = 'core/anotacao_form.html'
    success_url = reverse_lazy('anotacao-list')

    def form_valid(self, form):
        form.instance.usuario = self.request.user
        messages.success(self.request, 'Anotação criada com sucesso!')
        return super().form_valid(form)

class AnotacaoDetailView(LoginRequiredMixin, DetailView):
    model = AnotacaoPessoal
    template_name = 'core/anotacao_detail.html'
    context_object_name = 'anotacao'

    def get_queryset(self):
        return super().get_queryset().filter(usuario=self.request.user)

class AnotacaoUpdateView(LoginRequiredMixin, UpdateView):
    model = AnotacaoPessoal
    form_class = AnotacaoPessoalForm
    template_name = 'core/anotacao_form.html'
    success_url = reverse_lazy('anotacao-list')

    def get_queryset(self):
        return super().get_queryset().filter(usuario=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Anotação atualizada com sucesso!')
        return super().form_valid(form)

class AnotacaoDeleteView(LoginRequiredMixin, DeleteView):
    model = AnotacaoPessoal
    template_name = 'core/anotacao_confirm_delete.html'
    success_url = reverse_lazy('anotacao-list')

    def get_queryset(self):
        return super().get_queryset().filter(usuario=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Anotação excluída com sucesso!')
        return super().delete(request, *args, **kwargs)

def recuperar_senha(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        new_password = request.POST.get('new_password')
        
        User = get_user_model()
        try:
            user = User.objects.get(username=username)
            user.set_password(new_password)
            user.save()
            messages.success(request, "Senha alterada com sucesso!")
            return redirect('login')
        except User.DoesNotExist:
            messages.error(request, "Usuário não encontrado!")
    
    return render(request, 'core/recuperar_senha.html')


# Views para Raça
class RacaListView(LoginRequiredMixin, ListView):
    model = Raca
    template_name = 'core/raca_list.html'
    context_object_name = 'racas'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtro por nome
        nome = self.request.GET.get('nome')
        if nome:
            queryset = queryset.filter(nome__icontains=nome)
        
        # Filtro por longevidade
        longevidade = self.request.GET.get('longevidade')
        if longevidade:
            queryset = queryset.filter(longevidade__icontains=longevidade)
        
        # Filtro por afinidade mágica
        afinidade = self.request.GET.get('afinidade')
        if afinidade:
            queryset = queryset.filter(afinidade_magica__icontains=afinidade)
        
        # Busca geral
        busca = self.request.GET.get('busca')
        if busca:
            queryset = queryset.filter(
                Q(nome__icontains=busca) |
                Q(longevidade__icontains=busca) |
                Q(caracteristicas_fisicas__icontains=busca) |
                Q(afinidade_magica__icontains=busca) |
                Q(cor_sangue__icontains=busca)
            )
        
        return queryset

class RacaDetailView(LoginRequiredMixin, DetailView):
    model = Raca
    template_name = 'core/raca_detail.html'
    context_object_name = 'raca'

class RacaCreateView(AdminRequiredMixin, CreateView):
    model = Raca
    form_class = RacaForm
    template_name = 'core/raca_form.html'
    success_url = reverse_lazy('raca-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Raça criada com sucesso!')
        return super().form_valid(form)

class RacaUpdateView(AdminRequiredMixin, UpdateView):
    model = Raca
    form_class = RacaForm
    template_name = 'core/raca_form.html'
    success_url = reverse_lazy('raca-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Raça atualizada com sucesso!')
        return super().form_valid(form)

class RacaDeleteView(AdminRequiredMixin, DeleteView):
    model = Raca
    template_name = 'core/raca_confirm_delete.html'
    success_url = reverse_lazy('raca-list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Raça excluída com sucesso!')
        return super().delete(request, *args, **kwargs)


# Views para Ingrediente
class IngredienteListView(LoginRequiredMixin, ListView):
    model = Ingrediente
    template_name = 'core/ingrediente_list.html'
    context_object_name = 'ingredientes'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtro por nome
        nome = self.request.GET.get('nome')
        if nome:
            queryset = queryset.filter(nome__icontains=nome)
        
        # Filtro por descrição (o_que_e)
        descricao = self.request.GET.get('descricao')
        if descricao:
            queryset = queryset.filter(o_que_e__icontains=descricao)
        
        # Filtro por efeitos (o_que_faz)
        efeitos = self.request.GET.get('efeitos')
        if efeitos:
            queryset = queryset.filter(o_que_faz__icontains=efeitos)
        
        # Filtro combinado (busca em nome, descrição e efeitos)
        busca = self.request.GET.get('busca')
        if busca:
            queryset = queryset.filter(
                Q(nome__icontains=busca) |
                Q(o_que_e__icontains=busca) |
                Q(o_que_faz__icontains=busca)
            )
        
        return queryset

class IngredienteDetailView(LoginRequiredMixin, DetailView):
    model = Ingrediente
    template_name = 'core/ingrediente_detail.html'
    context_object_name = 'ingrediente'

class IngredienteCreateView(MedicoRequiredMixin, CreateView):
    model = Ingrediente
    form_class = IngredienteForm
    template_name = 'core/ingrediente_form.html'
    success_url = reverse_lazy('ingrediente-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Ingrediente criado com sucesso!')
        return super().form_valid(form)

class IngredienteUpdateView(MedicoRequiredMixin, UpdateView):
    model = Ingrediente
    form_class = IngredienteForm
    template_name = 'core/ingrediente_form.html'
    success_url = reverse_lazy('ingrediente-list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Ingrediente atualizado com sucesso!')
        return super().form_valid(form)

class IngredienteDeleteView(MedicoRequiredMixin, DeleteView):
    model = Ingrediente
    template_name = 'core/ingrediente_confirm_delete.html'
    success_url = reverse_lazy('ingrediente-list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Ingrediente excluído com sucesso!')
        return super().delete(request, *args, **kwargs)


# Views para Remédio
class RemedioListView(LoginRequiredMixin, ListView):
    model = Remedio
    template_name = 'core/remedio_list.html'
    context_object_name = 'remedios'
    
    def get_queryset(self):
        queryset = super().get_queryset().prefetch_related('ingredientes', 'doencas')
        
        # Filtro por nome
        nome = self.request.GET.get('nome')
        if nome:
            queryset = queryset.filter(nome__icontains=nome)
        
        # Filtro por doença
        doenca = self.request.GET.get('doenca')
        if doenca:
            queryset = queryset.filter(doencas__id=doenca)
        
        # Filtro por descrição
        descricao = self.request.GET.get('descricao')
        if descricao:
            queryset = queryset.filter(descricao__icontains=descricao)
        
        # Filtro por modo de uso
        modo_uso = self.request.GET.get('modo_uso')
        if modo_uso:
            queryset = queryset.filter(modo_uso__icontains=modo_uso)
        
        # Filtro por ingrediente
        ingrediente = self.request.GET.get('ingrediente')
        if ingrediente:
            queryset = queryset.filter(ingredientes__id=ingrediente)
        
        # Busca geral
        busca = self.request.GET.get('busca')
        if busca:
            queryset = queryset.filter(
                Q(nome__icontains=busca) |
                Q(descricao__icontains=busca) |
                Q(modo_uso__icontains=busca) |
                Q(observacoes__icontains=busca)
            )
            
        return queryset.distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['doencas'] = Doenca.objects.all()
        context['ingredientes'] = Ingrediente.objects.all()
        return context

class RemedioDetailView(LoginRequiredMixin, DetailView):
    model = Remedio
    template_name = 'core/remedio_detail.html'
    context_object_name = 'remedio'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ingredientes_remedio'] = RemedioIngrediente.objects.filter(remedio=self.object).select_related('ingrediente')
        return context

class RemedioCreateView(MedicoRequiredMixin, CreateView):
    model = Remedio
    form_class = RemedioForm
    template_name = 'core/remedio_form.html'
    success_url = reverse_lazy('remedio-list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['ingredientes_formset'] = RemedioIngredienteFormSet(self.request.POST, instance=self.object)
        else:
            context['ingredientes_formset'] = RemedioIngredienteFormSet(instance=self.object)
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        ingredientes_formset = context['ingredientes_formset']
        
        if ingredientes_formset.is_valid():
            self.object = form.save()
            ingredientes_formset.instance = self.object
            ingredientes_formset.save()
            messages.success(self.request, 'Remédio criado com sucesso!')
            return redirect(self.success_url)
        else:
            return self.render_to_response(self.get_context_data(form=form))

class RemedioUpdateView(MedicoRequiredMixin, UpdateView):
    model = Remedio
    form_class = RemedioForm
    template_name = 'core/remedio_form.html'
    success_url = reverse_lazy('remedio-list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['ingredientes_formset'] = RemedioIngredienteFormSet(self.request.POST, instance=self.object)
        else:
            context['ingredientes_formset'] = RemedioIngredienteFormSet(instance=self.object)
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        ingredientes_formset = context['ingredientes_formset']
        
        if ingredientes_formset.is_valid():
            self.object = form.save()
            ingredientes_formset.instance = self.object
            ingredientes_formset.save()
            messages.success(self.request, 'Remédio atualizado com sucesso!')
            return redirect(self.success_url)
        else:
            return self.render_to_response(self.get_context_data(form=form))

class RemedioDeleteView(MedicoRequiredMixin, DeleteView):
    model = Remedio
    template_name = 'core/remedio_confirm_delete.html'
    success_url = reverse_lazy('remedio-list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Remédio excluído com sucesso!')
        return super().delete(request, *args, **kwargs)