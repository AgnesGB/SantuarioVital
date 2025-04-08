from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy, reverse
from django.db.models import Q
from django.http import JsonResponse
from .models import Doenca, Sintoma, Besta, Bunker, Paciente, RegistroMedico, Diagnostico
from .forms import DoencaForm, SintomaForm, BestaForm, PacienteForm, RegistroMedicoForm, BunkerForm, DiagnosticoForm
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404

class BunkerCreateView(CreateView):
    model = Bunker
    form_class = BunkerForm
    template_name = 'core/bunker_form.html'
    success_url = reverse_lazy('bunker-list')

class BunkertListView(ListView):
    model = Bunker
    template_name = 'core/bunker_list.html'
    context_object_name = 'bunkers'

class PacienteCreateView(CreateView):
    model = Paciente
    form_class = PacienteForm
    template_name = 'core/paciente_form.html'
    success_url = reverse_lazy('paciente-list')

class DoencaListView(ListView):
    model = Doenca
    template_name = 'core/doenca_list.html'
    context_object_name = 'doencas'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        nome = self.request.GET.get('nome')
        tipo = self.request.GET.get('tipo')
        sintoma_query = self.request.GET.get('sintoma_query')
        
        if nome:
            queryset = queryset.filter(nome__icontains=nome)
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        if sintoma_query:
            queryset = queryset.filter(
                Q(sintomas__nome__icontains=sintoma_query) |
                Q(sintomas__descricao__icontains=sintoma_query)
                )
            
        return queryset.distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sintomas'] = Sintoma.objects.all()
        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            doencas = list(context['doencas'].values('id', 'nome'))
            return JsonResponse(doencas, safe=False)
        return super().render_to_response(context, **response_kwargs)

class DoencaDetailView(DetailView):
    model = Doenca
    template_name = 'core/doenca_detail.html'
    context_object_name = 'doenca'

class DoencaCreateView(CreateView):
    model = Doenca
    form_class = DoencaForm
    template_name = 'core/doenca_form.html'
    success_url = reverse_lazy('doenca-list')

class DoencaUpdateView(UpdateView):
    model = Doenca
    form_class = DoencaForm
    template_name = 'core/doenca_form.html'
    success_url = reverse_lazy('doenca-list')

class PacienteListView(ListView):
    model = Paciente
    template_name = 'core/paciente_list.html'
    context_object_name = 'pacientes'
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('bunker')
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
        return context

class PacienteDetailView(DetailView):
    model = Paciente
    template_name = 'core/paciente_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        paciente = self.object
        
        # Diagnosticos existentes
        context['diagnosticos'] = paciente.diagnostico_set.select_related('doenca')
        
        # Formulários
        context['form_sintoma'] = SintomaForm()
        context['form_diagnostico'] = DiagnosticoForm()
        
        # Doenças sugeridas pelos sintomas
        context['doencas_sugeridas'] = Doenca.objects.filter(
            sintomas__in=paciente.sintomas_observados.all()
        ).distinct()
        
        # Todas as doenças para seleção manual
        context['todas_doencas'] = Doenca.objects.all()
        
        return context

class AdicionarDiagnosticoView(CreateView):
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

class PacienteUpdateView(UpdateView):
    model = Paciente
    form_class = PacienteForm
    template_name = 'core/paciente_form.html'
    
    def get_success_url(self):
        return reverse_lazy('paciente-detail', kwargs={'pk': self.object.pk})

class PacienteCreateView(CreateView):
    model = Paciente
    form_class = PacienteForm
    template_name = 'core/paciente_form.html'
    success_url = reverse_lazy('paciente-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Paciente cadastrado com sucesso!')
        return response

    def form_invalid(self, form):
        messages.error(self.request, 'Erro ao cadastrar paciente. Verifique os dados.')
        return super().form_invalid(form)

class PacienteUpdateView(UpdateView):
    model = Paciente
    form_class = PacienteForm
    template_name = 'core/paciente_form.html'

    def get_success_url(self):
        messages.success(self.request, 'Paciente atualizado com sucesso!')
        return reverse_lazy('paciente-detail', kwargs={'pk': self.object.pk})

    def form_invalid(self, form):
        messages.error(self.request, 'Erro ao atualizar paciente. Verifique os dados.')
        return super().form_invalid(form)
    
class RegistroMedicoCreateView(CreateView):
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

class NovaDoencaView(CreateView):
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
    
def buscar_sintomas(request):
    termo = request.GET.get('termo', '')
    sintomas = Sintoma.objects.filter(
        Q(nome__icontains=termo) |
        Q(descricao__icontains=termo)
    ).values('id', 'nome', 'tipo')[:10]
    return JsonResponse(list(sintomas), safe=False)

def adicionar_sintoma(request, paciente_id):
    paciente = get_object_or_404(Paciente, pk=paciente_id)
    if request.method == 'POST':
        sintoma_id = request.POST.get('sintoma')
        sintoma = get_object_or_404(Sintoma, pk=sintoma_id)
        paciente.sintomas_observados.add(sintoma)
        messages.success(request, 'Sintoma adicionado com sucesso!')
    return redirect('paciente-detail', pk=paciente_id)

def remover_sintoma(request, paciente_id, sintoma_id):
    paciente = get_object_or_404(Paciente, pk=paciente_id)
    sintoma = get_object_or_404(Sintoma, pk=sintoma_id)
    paciente.sintomas_observados.remove(sintoma)
    messages.success(request, 'Sintoma removido com sucesso!')
    return redirect('paciente-detail', pk=paciente_id)

class BestaListView(ListView):
    model = Besta
    template_name = 'core/besta_list.html'
    context_object_name = 'bestas'

class BestaCreateView(CreateView):
    model = Besta
    form_class = BestaForm
    template_name = 'core/besta_form.html'
    success_url = reverse_lazy('besta-list')

class BestaDetailView(DetailView):
    model = Besta
    template_name = 'core/besta_detail.html'
    context_object_name = 'besta'

class BestaUpdateView(UpdateView):
    model = Besta
    form_class = BestaForm
    template_name = 'core/besta_form.html'
    success_url = reverse_lazy('besta-list')