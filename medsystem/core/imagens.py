"""Galeria de imagens genérica, usada por expedições, bestiário, livros, doenças, raças, ingredientes e remédios."""
from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError

from .models import Imagem

TAMANHO_MAXIMO_MB = 10
CAMPO_IMAGEM = forms.ImageField()


def salvar_imagens(request, obj):
    """Processa os campos do partial _imagens_form.html: novas imagens, legendas e remoções."""
    existentes = {img.pk: img for img in obj.imagens.all()}

    remover = {int(i) for i in request.POST.getlist('remover_imagem') if i.isdigit()}
    for pk in remover & existentes.keys():
        existentes.pop(pk).delete()

    for pk, img in existentes.items():
        legenda = request.POST.get(f'legenda_imagem_{pk}')
        if legenda is not None and legenda.strip() != img.legenda:
            img.legenda = legenda.strip()[:200]
            img.save(update_fields=['legenda'])

    legendas_novas = request.POST.getlist('legenda_nova')
    for i, arquivo in enumerate(request.FILES.getlist('imagens_novas')):
        if arquivo.size > TAMANHO_MAXIMO_MB * 1024 * 1024:
            messages.warning(request, f'"{arquivo.name}" passa de {TAMANHO_MAXIMO_MB} MB e não foi enviada.')
            continue
        try:
            CAMPO_IMAGEM.clean(arquivo)
        except ValidationError:
            messages.warning(request, f'"{arquivo.name}" não é uma imagem válida e foi ignorada.')
            continue
        Imagem.objects.create(
            item=obj, arquivo=arquivo, enviada_por=request.user,
            legenda=(legendas_novas[i] if i < len(legendas_novas) else '').strip()[:200],
        )


class ImagensMixin:
    """Para CreateView/UpdateView: salva a galeria depois que o formulário principal foi salvo."""

    def form_valid(self, form):
        resposta = super().form_valid(form)
        if resposta.status_code in (301, 302) and getattr(self.object, 'pk', None):
            salvar_imagens(self.request, self.object)
        return resposta
