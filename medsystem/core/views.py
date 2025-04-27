from django.views.generic import DeleteView, ListView, DetailView, CreateView, UpdateView, TemplateView
from django.urls import reverse_lazy, reverse
from django.db.models import Q
from django.http import JsonResponse
from .models import Doenca, RelatorioExpedicao, Postagem, Comentario, Usuario, Besta, Bunker, Paciente, RegistroMedico, Diagnostico, AnotacaoPessoal
from .forms import UsuarioCreationForm, DoencaForm, BestaForm, PacienteForm, RegistroMedicoForm, BunkerForm, DiagnosticoForm, AnotacaoPessoalForm
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import datetime
from .mixins import MedicoRequiredMixin 
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

class HomeView(TemplateView):
    template_name = 'core/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['usuarios'] = Usuario.objects.all().order_by('nickname')
        context['is_medico'] = self.request.user.is_authenticated and self.request.user.tipo == 'MED'
        return context

class RelatorioExpedicaoListView(LoginRequiredMixin, ListView):
    model = RelatorioExpedicao
    template_name = 'core/relatorio_list.html'

class RelatorioExpedicaoCreateView(LoginRequiredMixin, CreateView):
    model = RelatorioExpedicao
    fields = ['titulo', 'localizacao', 'descobertas', 'observacoes']
    template_name = 'core/relatorio_form.html'
    success_url = reverse_lazy('relatorio-list')
    
    def form_valid(self, form):
        form.instance.autor = self.request.user
        return super().form_valid(form)

class BunkerDetailView(DetailView):
    model = Bunker
    template_name = 'core/bunker_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['membros'] = Usuario.objects.filter(bunker=self.object)
        context['pacientes'] = Paciente.objects.filter(bunker=self.object).only('nome', 'idade', 'tipo_sanguineo')
        return context

class BunkertListView(ListView):
    model = Bunker
    template_name = 'core/bunker_list.html'
    context_object_name = 'bunkers'

class DoencaListView(MedicoRequiredMixin, ListView):
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

class DoencaDetailView(MedicoRequiredMixin, DetailView):
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

# diagnostico
class DiagnosticoCreateView(MedicoRequiredMixin, CreateView):
    model = Diagnostico
    form_class = DiagnosticoForm
    template_name = 'core/diagnostico_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['paciente'] = get_object_or_404(Paciente, pk=self.kwargs['paciente_id'])
        context['doencas'] = Doenca.objects.all()
        return context

    def form_valid(self, form):
        form.instance.paciente = get_object_or_404(Paciente, pk=self.kwargs['paciente_id'])
        form.instance.responsavel = self.request.user
        
        # Salva o diagnóstico primeiro
        response = super().form_valid(form)
        
        # Processa as hipóteses (enviadas como string separada por vírgulas)
        hipoteses_ids = [int(id) for id in self.request.POST.get('hipoteses', '').split(',') if id]
        self.object.hipoteses.set(hipoteses_ids)
        
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
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        
        if form.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)

    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Processa as hipóteses
        hipoteses_ids = self.request.POST.get('hipoteses', '').split(',')
        hipoteses_ids = [int(id) for id in hipoteses_ids if id]  # Remove valores vazios
        self.object.hipoteses.set(hipoteses_ids)
        
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


#paciente
class PacienteDeleteView(MedicoRequiredMixin, DeleteView):
    model = Paciente
    template_name = 'core/paciente_confirm_delete.html'
    success_url = reverse_lazy('paciente-list')

class PacienteCreateView(MedicoRequiredMixin, CreateView):
    model = Paciente
    fields = ['nome', 'idade', 'tipo_sanguineo', 'status', 'bunker', 'observacoes']  # Remova form_class temporariamente
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
        queryset = super().get_queryset().select_related('bunker').order_by('nome')  # Ordenação padrão por nome
        
        # Aplica filtros se existirem
        nome = self.request.GET.get('nome')
        status = self.request.GET.get('status')
        tipo_sanguineo = self.request.GET.get('tipo_sanguineo')
        bunker = self.request.GET.get('bunker')
        
        if nome:
            queryset = queryset.filter(nome__icontains=nome)
        if status:
            queryset = queryset.filter(status=status)
        if tipo_sanguineo:
            queryset = queryset.filter(tipo_sanguineo=tipo_sanguineo)
        if bunker:
            queryset = queryset.filter(bunker_id=bunker)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['bunkers'] = Bunker.objects.all()
        context['status_choices'] = Paciente.STATUS_CHOICES
        context['tipo_sanguineo_choices'] = Paciente.TIPO_SANGUINEO_CHOICES
        
        # Adiciona flag para saber se há filtros ativos
        context['has_filters'] = any([
            self.request.GET.get('nome'),
            self.request.GET.get('status'),
            self.request.GET.get('tipo_sanguineo'),
            self.request.GET.get('bunker')
        ])
        
        return context

class PacienteDetailView(MedicoRequiredMixin, DetailView):
    model = Paciente
    template_name = 'core/paciente_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['diagnosticos'] = self.object.diagnostico_set.all()
        context['todas_doencas'] = Doenca.objects.all()
        return context

class RelatorioExpedicaoListView(LoginRequiredMixin, ListView):
    model = RelatorioExpedicao
    template_name = 'core/relatorio_list.html'
    context_object_name = 'relatorios'
    ordering = ['-data']

class RelatorioExpedicaoCreateView(LoginRequiredMixin, CreateView):
    model = RelatorioExpedicao
    fields = ['titulo', 'localizacao', 'descobertas', 'observacoes']
    template_name = 'core/relatorio_form.html'
    success_url = reverse_lazy('relatorio-list')
    
    def form_valid(self, form):
        form.instance.autor = self.request.user
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

class RelatorioExpedicaoDeleteView(LoginRequiredMixin, DeleteView):
    model = RelatorioExpedicao
    template_name = 'core/relatorio_confirm_delete.html'
    success_url = reverse_lazy('relatorio-list')

class AnotacaoListView(LoginRequiredMixin, ListView):
    model = AnotacaoPessoal
    template_name = 'core/anotacao_list.html'
    context_object_name = 'anotacoes'

    def get_queryset(self):
        queryset = super().get_queryset().filter(usuario=self.request.user)
        
        # Filtros
        search = self.request.GET.get('search')
        tags = self.request.GET.get('tags')
        data = self.request.GET.get('data')
        
        if search:
            queryset = queryset.filter(
                Q(titulo__icontains=search) |
                Q(conteudo__icontains=search)
            )
        
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