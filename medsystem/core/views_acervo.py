import json
import uuid
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Count, Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from .forms import LivroForm, MapaTeorizacaoForm, TemaForm
from .imagens import CAMPO_IMAGEM, TAMANHO_MAXIMO_MB, ImagensMixin
from .models import (Besta, ComentarioLivro, Doenca, Imagem, Ingrediente, Livro, MapaTeorizacao, Paciente,
                     Raca, RelatorioExpedicao, Remedio, Tema, Usuario)


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
            context['livros_recentes'] = Livro.objects.select_related('tema').prefetch_related('imagens').order_by('-data_criacao')[:6]
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
        context['livros'] = self.object.livros.annotate(total_comentarios=Count('comentarios')).prefetch_related('imagens')
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

class LivroCreateView(ImagensMixin, LoginRequiredMixin, CreateView):
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


class LivroUpdateView(ImagensMixin, LoginRequiredMixin, DonoRequiredMixin, UpdateView):
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

def mapas_editaveis(usuario):
    """Mapas que o usuário pode editar: os dele e aqueles em que é colaborador."""
    return MapaTeorizacao.objects.filter(Q(usuario=usuario) | Q(colaboradores=usuario)).distinct()


class MapaListView(LoginRequiredMixin, ListView):
    model = MapaTeorizacao
    template_name = 'core/mapa_list.html'
    context_object_name = 'mapas'

    def get_queryset(self):
        return super().get_queryset().filter(usuario=self.request.user).prefetch_related('colaboradores')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['compartilhados'] = self.request.user.mapas_colaborando.select_related('usuario')
        return context


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
        return mapas_editaveis(self.request.user)

    def get_success_url(self):
        return reverse('mapa-detail', args=[self.object.pk])


class MapaDeleteView(LoginRequiredMixin, DeleteView):
    model = MapaTeorizacao
    template_name = 'core/acervo_confirm_delete.html'
    success_url = reverse_lazy('mapa-list')

    def get_queryset(self):
        # Só o dono exclui
        return super().get_queryset().filter(usuario=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tipo'] = 'mapa'
        context['aviso'] = 'O mapa e todas as suas conexões serão perdidos, também para os colaboradores.'
        context['voltar'] = reverse('mapa-detail', args=[self.object.pk])
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Mapa excluído com sucesso!')
        return super().form_valid(form)


def _imagens_mapa(mapa):
    return {img.pk: {'url': img.arquivo.url, 'legenda': img.legenda} for img in mapa.imagens.all()}


def _contexto_editor(mapa, usuario, somente_leitura):
    dados = mapa.dados or {}
    nos = dados.get('nos', [])
    return {
        'mapa': mapa,
        'somente_leitura': somente_leitura,
        'eh_dono': mapa.usuario_id == usuario.pk,
        'participantes': [mapa.usuario] + list(mapa.colaboradores.all()),
        # Quem só visualiza recebe apenas os registros que estão no mapa
        'itens_json': itens_por_chaves({f"{n.get('tipo')}:{n.get('ref_id')}" for n in nos}, usuario)
                      if somente_leitura else catalogo_teorizacao(usuario),
        'imagens_mapa_json': _imagens_mapa(mapa),
        'dados_json': {'nos': nos, 'conexoes': dados.get('conexoes', []), 'versao': mapa.versao},
        'url_estado': (reverse('mapa-compartilhado-estado', args=[mapa.token_link]) if somente_leitura
                       else reverse('mapa-estado', args=[mapa.pk])),
    }


class MapaDetailView(LoginRequiredMixin, DetailView):
    model = MapaTeorizacao
    template_name = 'core/mapa_detail.html'
    context_object_name = 'mapa'

    def get_queryset(self):
        return mapas_editaveis(self.request.user).select_related('usuario')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(_contexto_editor(self.object, self.request.user, somente_leitura=False))
        if context['eh_dono']:
            context['link_compartilhamento'] = self.request.build_absolute_uri(
                reverse('mapa-compartilhado', args=[self.object.token_link]))
            context['usuarios_json'] = [
                {'id': u.pk, 'nickname': u.nickname, 'username': u.username}
                for u in Usuario.objects.exclude(pk=self.request.user.pk).order_by('nickname')
            ]
        return context


@login_required
def mapa_compartilhado(request, token):
    """Link de visualização: qualquer pessoa logada com o link vê o mapa, sem poder alterar."""
    mapa = get_object_or_404(MapaTeorizacao.objects.select_related('usuario'), token_link=token)
    if mapa.pode_editar(request.user):
        return redirect('mapa-detail', pk=mapa.pk)
    if not mapa.link_ativo:
        raise Http404('Este link de compartilhamento foi desativado.')
    return render(request, 'core/mapa_detail.html', _contexto_editor(mapa, request.user, somente_leitura=True))


def _primeira_imagem(obj):
    imagens = list(obj.imagens.all())
    return imagens[0].arquivo.url if imagens else ''


def _item(tipo, obj, titulo, subtitulo, resumo, url_name):
    return {
        'tipo': tipo, 'id': obj.pk, 'titulo': titulo, 'subtitulo': subtitulo or '',
        'resumo': (resumo or '')[:300],
        'imagem': _primeira_imagem(obj) if hasattr(obj, 'imagens') else '',
        'url': reverse(url_name, args=[obj.pk]),
    }


# tipo -> (consulta, conversor para o formato do editor, se o usuário pode ver)
TIPOS_TEORIZACAO = {
    'livro': (lambda: Livro.objects.select_related('tema').prefetch_related('imagens'),
              lambda l: _item('livro', l, l.titulo, ' · '.join(filter(None, [l.autor, l.tema.nome])), l.resumo, 'livro-detail'),
              lambda u: True),
    'relatorio': (lambda: RelatorioExpedicao.objects.prefetch_related('imagens'),
                  lambda r: _item('relatorio', r, r.titulo, f'{r.localizacao} · {timezone.localtime(r.data):%d/%m/%Y}', r.descobertas, 'relatorio-detail'),
                  lambda u: True),
    'besta': (lambda: Besta.objects.prefetch_related('imagens').order_by('nome'),
              lambda b: _item('besta', b, b.nome, f'{b.titulo + " · " if b.titulo else ""}Ameaça {b.get_nivel_ameaca_display()}', b.aparencia, 'besta-detail'),
              lambda u: True),
    'doenca': (lambda: Doenca.objects.prefetch_related('imagens'),
               lambda d: _item('doenca', d, d.nome, f'{d.get_tipo_display()} · {d.get_parte_afetada_display()}', d.sintomas, 'doenca-detail'),
               lambda u: True),
    'raca': (lambda: Raca.objects.prefetch_related('imagens'),
             lambda r: _item('raca', r, r.nome, r.afinidade_magica, r.caracteristicas_fisicas, 'raca-detail'),
             lambda u: True),
    'ingrediente': (lambda: Ingrediente.objects.prefetch_related('imagens'),
                    lambda i: _item('ingrediente', i, i.nome, '', i.o_que_faz, 'ingrediente-detail'),
                    lambda u: True),
    'remedio': (lambda: Remedio.objects.prefetch_related('imagens'),
                lambda r: _item('remedio', r, r.nome, '', r.descricao, 'remedio-detail'),
                lambda u: True),
    'paciente': (lambda: Paciente.objects.order_by('nome'),
                 lambda p: _item('paciente', p, p.nome, f'{p.idade} anos · {p.get_status_display()}', p.observacoes, 'paciente-detail'),
                 lambda u: u.tipo in ('MED', 'ADM')),
}


def catalogo_teorizacao(usuario):
    """Tudo o que o usuário pode colocar num mapa, no formato que o editor espera."""
    itens = []
    for consulta, converter, permitido in TIPOS_TEORIZACAO.values():
        if permitido(usuario):
            itens.extend(converter(obj) for obj in consulta())
    return itens


def itens_por_chaves(chaves, usuario):
    """Só os registros pedidos (chaves "tipo:id"), respeitando o que o usuário pode ver."""
    por_tipo = {}
    for chave in chaves:
        tipo, _, ref = str(chave).partition(':')
        if tipo in TIPOS_TEORIZACAO and ref.isdigit():
            por_tipo.setdefault(tipo, set()).add(int(ref))
    itens = []
    for tipo, ids in por_tipo.items():
        consulta, converter, permitido = TIPOS_TEORIZACAO[tipo]
        if permitido(usuario):
            itens.extend(converter(obj) for obj in consulta().filter(pk__in=ids))
    return itens


def _estado_json(mapa, usuario, request):
    dados = mapa.dados or {}
    faltam = [c for c in request.GET.get('faltam', '').split(',') if c][:200]
    return JsonResponse({
        'versao': mapa.versao,
        'nos': dados.get('nos', []),
        'conexoes': dados.get('conexoes', []),
        'imagens': _imagens_mapa(mapa),
        'itens': itens_por_chaves(faltam, usuario) if faltam else [],
    })


@login_required
def mapa_estado(request, pk):
    mapa = get_object_or_404(mapas_editaveis(request.user), pk=pk)
    return _estado_json(mapa, request.user, request)


@login_required
def mapa_compartilhado_estado(request, token):
    mapa = get_object_or_404(MapaTeorizacao, token_link=token)
    if not mapa.link_ativo and not mapa.pode_editar(request.user):
        raise Http404
    return _estado_json(mapa, request.user, request)


@login_required
@require_POST
def mapa_imagem_enviar(request, pk):
    mapa = get_object_or_404(mapas_editaveis(request.user), pk=pk)
    arquivo = request.FILES.get('imagem')
    if not arquivo:
        return JsonResponse({'erro': 'Nenhuma imagem enviada.'}, status=400)
    if arquivo.size > TAMANHO_MAXIMO_MB * 1024 * 1024:
        return JsonResponse({'erro': f'A imagem passa de {TAMANHO_MAXIMO_MB} MB.'}, status=400)
    try:
        CAMPO_IMAGEM.clean(arquivo)
    except ValidationError:
        return JsonResponse({'erro': 'Arquivo não é uma imagem válida.'}, status=400)
    img = Imagem.objects.create(item=mapa, arquivo=arquivo, enviada_por=request.user)
    return JsonResponse({'id': img.pk, 'url': img.arquivo.url, 'legenda': ''}, status=201)


@login_required
@require_POST
def mapa_salvar(request, pk):
    try:
        dados = json.loads(request.body)
        nos, conexoes = dados['nos'], dados['conexoes']
        versao_base = dados.get('versao')
        if not isinstance(nos, list) or not isinstance(conexoes, list):
            raise ValueError
    except (ValueError, KeyError, TypeError):
        return JsonResponse({'erro': 'Dados inválidos.'}, status=400)

    get_object_or_404(mapas_editaveis(request.user), pk=pk)
    with transaction.atomic():
        mapa = MapaTeorizacao.objects.select_for_update().get(pk=pk)
        # Alguém salvou depois da versão em que este editor se baseou: devolve o estado atual
        # para o navegador juntar as alterações e tentar de novo
        if versao_base is not None and versao_base != mapa.versao:
            dados_atuais = mapa.dados or {}
            return JsonResponse({
                'conflito': True, 'versao': mapa.versao,
                'nos': dados_atuais.get('nos', []), 'conexoes': dados_atuais.get('conexoes', []),
                'imagens': _imagens_mapa(mapa),
            }, status=409)
        mapa.dados = {'nos': nos, 'conexoes': conexoes}
        mapa.versao += 1
        mapa.save(update_fields=['dados', 'versao', 'data_atualizacao'])

    # Imagens soltas no mapa que não estão mais em nenhum cartão são apagadas
    # (as recém-enviadas ficam um tempo de folga, caso um salvamento antigo chegue depois do upload)
    usadas = {n.get('ref_id') for n in nos if isinstance(n, dict) and n.get('tipo') == 'imagem'}
    limite = timezone.now() - timedelta(minutes=5)
    for img in mapa.imagens.filter(data_envio__lt=limite):
        if img.pk not in usadas:
            img.delete()
    return JsonResponse({'ok': True, 'versao': mapa.versao,
                         'salvo_em': timezone.localtime(mapa.data_atualizacao).strftime('%H:%M:%S')})


def _compartilhamento_json(mapa, request):
    return {
        'link_ativo': mapa.link_ativo,
        'link': request.build_absolute_uri(reverse('mapa-compartilhado', args=[mapa.token_link])),
        'colaboradores': [{'id': u.pk, 'nickname': u.nickname, 'username': u.username}
                          for u in mapa.colaboradores.order_by('nickname')],
    }


@login_required
@require_POST
def mapa_compartilhamento(request, pk):
    """Só o dono: liga/desliga o link, gera um link novo, adiciona ou remove colaboradores."""
    mapa = get_object_or_404(MapaTeorizacao, pk=pk, usuario=request.user)
    try:
        dados = json.loads(request.body)
        acao = dados['acao']
    except (ValueError, KeyError, TypeError):
        return JsonResponse({'erro': 'Dados inválidos.'}, status=400)

    if acao == 'link':
        mapa.link_ativo = bool(dados.get('ativo'))
        mapa.save(update_fields=['link_ativo'])
    elif acao == 'novo_link':
        mapa.token_link = uuid.uuid4()
        mapa.save(update_fields=['token_link'])
    elif acao == 'adicionar':
        termo = str(dados.get('usuario', '')).strip()
        usuario = (Usuario.objects.filter(username__iexact=termo).first()
                   or Usuario.objects.filter(nickname__iexact=termo).first())
        if not usuario:
            return JsonResponse({'erro': f'Nenhum usuário chamado "{termo}".'}, status=400)
        if usuario.pk == mapa.usuario_id:
            return JsonResponse({'erro': 'Você já é o dono do mapa.'}, status=400)
        mapa.colaboradores.add(usuario)
    elif acao == 'remover':
        mapa.colaboradores.remove(*Usuario.objects.filter(pk=dados.get('usuario_id')))
    else:
        return JsonResponse({'erro': 'Ação desconhecida.'}, status=400)
    return JsonResponse(_compartilhamento_json(mapa, request))


@login_required
@require_POST
def mapa_sair(request, pk):
    """Um colaborador deixa de participar do mapa."""
    mapa = get_object_or_404(MapaTeorizacao, pk=pk, colaboradores=request.user)
    mapa.colaboradores.remove(request.user)
    messages.success(request, f'Você saiu do mapa "{mapa.titulo}".')
    return redirect('mapa-list')
