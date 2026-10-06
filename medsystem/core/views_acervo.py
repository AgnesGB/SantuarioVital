import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from .forms import LivroForm, MapaTeorizacaoForm, TemaForm
from .models import ComentarioLivro, Livro, MapaTeorizacao, Tema


def pode_editar(usuario, dono):
    return usuario.tipo == 'ADM' or (dono is not None and dono == usuario)


def arvore_temas():
    """Monta a árvore completa de temas (com contagem de livros) usando uma única consulta."""
    temas = list(Tema.objects.annotate(total_livros=Count('livros')))
    por_pai = {}
    for tema in temas:
        por_pai.setdefault(tema.pai_id, []).append(tema)
    for tema in temas:
        tema.filhos = por_pai.get(tema.pk, [])
    return por_pai.get(None, [])


class DonoRequiredMixin:
    """Só quem criou (ou um administrador) pode editar/excluir."""
    campo_dono = None

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not pode_editar(self.request.user, getattr(obj, self.campo_dono)):
            raise PermissionDenied("Apenas quem adicionou ou um administrador pode alterar este item.")
        return obj


# ---------- Acervo: temas ----------

class AcervoView(LoginRequiredMixin, TemplateView):
    template_name = 'core/acervo.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['arvore'] = arvore_temas()
        busca = self.request.GET.get('busca', '').strip()
        context['busca'] = busca
        if busca:
            context['resultados'] = Livro.objects.select_related('tema').filter(
                Q(titulo__icontains=busca) | Q(autor__icontains=busca) |
                Q(resumo__icontains=busca) | Q(conteudo__icontains=busca)
            )
        else:
            context['temas_principais'] = context['arvore']
            context['livros_recentes'] = Livro.objects.select_related('tema').order_by('-data_criacao')[:6]
        return context


class TemaDetailView(LoginRequiredMixin, DetailView):
    model = Tema
    template_name = 'core/tema_detail.html'
    context_object_name = 'tema'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['arvore'] = arvore_temas()
        context['caminho'] = self.object.caminho()
        context['caminho_ids'] = [t.pk for t in context['caminho']]
        context['tema_atual_id'] = self.object.pk
        context['subtemas'] = self.object.subtemas.annotate(total_livros=Count('livros', distinct=True), total_subtemas=Count('subtemas', distinct=True))
        context['livros'] = self.object.livros.annotate(total_comentarios=Count('comentarios'))
        context['pode_editar'] = pode_editar(self.request.user, self.object.criado_por)
        return context


class TemaCreateView(LoginRequiredMixin, CreateView):
    model = Tema
    form_class = TemaForm
    template_name = 'core/tema_form.html'

    def get_initial(self):
        return {'pai': self.request.GET.get('pai')}

    def form_valid(self, form):
        form.instance.criado_por = self.request.user
        messages.success(self.request, 'Tema criado com sucesso!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('tema-detail', args=[self.object.pk])


class TemaUpdateView(LoginRequiredMixin, DonoRequiredMixin, UpdateView):
    model = Tema
    form_class = TemaForm
    template_name = 'core/tema_form.html'
    campo_dono = 'criado_por'

    def form_valid(self, form):
        messages.success(self.request, 'Tema atualizado com sucesso!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('tema-detail', args=[self.object.pk])


class TemaDeleteView(LoginRequiredMixin, DonoRequiredMixin, DeleteView):
    model = Tema
    template_name = 'core/acervo_confirm_delete.html'
    campo_dono = 'criado_por'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tipo'] = 'tema'
        context['aviso'] = 'Todos os subtemas e livros dentro deste tema também serão excluídos.'
        context['voltar'] = reverse('tema-detail', args=[self.object.pk])
        return context

    def get_success_url(self):
        if self.object.pai_id:
            return reverse('tema-detail', args=[self.object.pai_id])
        return reverse('acervo')

    def form_valid(self, form):
        messages.success(self.request, 'Tema excluído com sucesso!')
        return super().form_valid(form)


# ---------- Acervo: livros ----------

class LivroCreateView(LoginRequiredMixin, CreateView):
    model = Livro
    form_class = LivroForm
    template_name = 'core/livro_form.html'

    def get_initial(self):
        return {'tema': self.request.GET.get('tema')}

    def form_valid(self, form):
        form.instance.adicionado_por = self.request.user
        messages.success(self.request, 'Livro adicionado ao acervo!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('livro-detail', args=[self.object.pk])


class LivroUpdateView(LoginRequiredMixin, DonoRequiredMixin, UpdateView):
    model = Livro
    form_class = LivroForm
    template_name = 'core/livro_form.html'
    campo_dono = 'adicionado_por'

    def form_valid(self, form):
        resposta = super().form_valid(form)
        self.object.realocar_comentarios()
        messages.success(self.request, 'Livro atualizado com sucesso!')
        return resposta

    def get_success_url(self):
        return reverse('livro-detail', args=[self.object.pk])


class LivroDeleteView(LoginRequiredMixin, DonoRequiredMixin, DeleteView):
    model = Livro
    template_name = 'core/acervo_confirm_delete.html'
    campo_dono = 'adicionado_por'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tipo'] = 'livro'
        context['aviso'] = 'Todos os comentários deste livro também serão excluídos.'
        context['voltar'] = reverse('livro-detail', args=[self.object.pk])
        return context

    def get_success_url(self):
        return reverse('tema-detail', args=[self.object.tema_id])

    def form_valid(self, form):
        messages.success(self.request, 'Livro excluído com sucesso!')
        return super().form_valid(form)


def comentario_json(comentario, usuario):
    return {
        'id': comentario.pk,
        'autor': comentario.autor.nickname,
        'trecho': comentario.trecho,
        'inicio': comentario.inicio,
        'fim': comentario.fim,
        'texto': comentario.texto,
        'data': timezone.localtime(comentario.data_criacao).strftime('%d/%m/%Y %H:%M'),
        'pode_excluir': pode_editar(usuario, comentario.autor),
        'url_excluir': reverse('comentario-livro-delete', args=[comentario.pk]),
    }


class LivroDetailView(LoginRequiredMixin, DetailView):
    model = Livro
    template_name = 'core/livro_detail.html'
    context_object_name = 'livro'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['caminho'] = self.object.tema.caminho()
        context['pode_editar'] = pode_editar(self.request.user, self.object.adicionado_por)
        comentarios = self.object.comentarios.select_related('autor')
        context['comentarios_json'] = [comentario_json(c, self.request.user) for c in comentarios]
        return context


@login_required
@require_POST
def comentario_livro_criar(request, pk):
    livro = get_object_or_404(Livro, pk=pk)
    try:
        dados = json.loads(request.body)
        inicio, fim = int(dados['inicio']), int(dados['fim'])
        texto = dados['texto'].strip()
    except (ValueError, KeyError, TypeError, AttributeError):
        return JsonResponse({'erro': 'Dados inválidos.'}, status=400)

    if not texto:
        return JsonResponse({'erro': 'O comentário não pode ficar vazio.'}, status=400)
    if not (0 <= inicio < fim <= len(livro.conteudo)):
        return JsonResponse({'erro': 'Seleção inválida.'}, status=400)

    comentario = ComentarioLivro.objects.create(
        livro=livro, autor=request.user, texto=texto,
        inicio=inicio, fim=fim, trecho=livro.conteudo[inicio:fim],
    )
    return JsonResponse(comentario_json(comentario, request.user), status=201)


@login_required
@require_POST
def comentario_livro_excluir(request, pk):
    comentario = get_object_or_404(ComentarioLivro, pk=pk)
    if not pode_editar(request.user, comentario.autor):
        return JsonResponse({'erro': 'Você não pode excluir este comentário.'}, status=403)
    comentario.delete()
    return JsonResponse({'ok': True})


# ---------- Teorização ----------

class MapaListView(LoginRequiredMixin, ListView):
    model = MapaTeorizacao
    template_name = 'core/mapa_list.html'
    context_object_name = 'mapas'

    def get_queryset(self):
        return super().get_queryset().filter(usuario=self.request.user)


class MapaCreateView(LoginRequiredMixin, CreateView):
    model = MapaTeorizacao
    form_class = MapaTeorizacaoForm
    template_name = 'core/mapa_form.html'

    def form_valid(self, form):
        form.instance.usuario = self.request.user
        form.instance.dados = {'nos': [], 'conexoes': []}
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('mapa-detail', args=[self.object.pk])


class MapaUpdateView(LoginRequiredMixin, UpdateView):
    model = MapaTeorizacao
    form_class = MapaTeorizacaoForm
    template_name = 'core/mapa_form.html'

    def get_queryset(self):
        return super().get_queryset().filter(usuario=self.request.user)

    def get_success_url(self):
        return reverse('mapa-detail', args=[self.object.pk])


class MapaDeleteView(LoginRequiredMixin, DeleteView):
    model = MapaTeorizacao
    template_name = 'core/acervo_confirm_delete.html'
    success_url = reverse_lazy('mapa-list')

    def get_queryset(self):
        return super().get_queryset().filter(usuario=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tipo'] = 'mapa'
        context['aviso'] = 'O mapa e todas as suas conexões serão perdidos.'
        context['voltar'] = reverse('mapa-detail', args=[self.object.pk])
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Mapa excluído com sucesso!')
        return super().form_valid(form)


class MapaDetailView(LoginRequiredMixin, DetailView):
    model = MapaTeorizacao
    template_name = 'core/mapa_detail.html'
    context_object_name = 'mapa'

    def get_queryset(self):
        return super().get_queryset().filter(usuario=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        livros = Livro.objects.select_related('tema', 'tema__pai').annotate(total_comentarios=Count('comentarios'))
        context['livros_json'] = [{
            'id': livro.pk,
            'titulo': livro.titulo,
            'autor': livro.autor,
            'tema': str(livro.tema),
            'resumo': livro.resumo,
            'comentarios': livro.total_comentarios,
            'url': reverse('livro-detail', args=[livro.pk]),
        } for livro in livros]
        dados = self.object.dados or {}
        context['dados_json'] = {'nos': dados.get('nos', []), 'conexoes': dados.get('conexoes', [])}
        return context


@login_required
@require_POST
def mapa_salvar(request, pk):
    mapa = get_object_or_404(MapaTeorizacao, pk=pk, usuario=request.user)
    try:
        dados = json.loads(request.body)
        nos, conexoes = dados['nos'], dados['conexoes']
        if not isinstance(nos, list) or not isinstance(conexoes, list):
            raise ValueError
    except (ValueError, KeyError, TypeError):
        return JsonResponse({'erro': 'Dados inválidos.'}, status=400)

    mapa.dados = {'nos': nos, 'conexoes': conexoes}
    mapa.save(update_fields=['dados', 'data_atualizacao'])
    return JsonResponse({'ok': True, 'salvo_em': timezone.localtime(mapa.data_atualizacao).strftime('%H:%M:%S')})
