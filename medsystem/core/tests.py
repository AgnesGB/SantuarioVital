import json

from django.test import TestCase
from django.urls import reverse

from .models import ComentarioLivro, Livro, MapaTeorizacao, Tema, Usuario


class AcervoTests(TestCase):
    def setUp(self):
        self.ana = Usuario.objects.create_user(username='ana', password='x', nickname='Ana')
        self.bia = Usuario.objects.create_user(username='bia', password='x', nickname='Bia')
        self.tema = Tema.objects.create(nome='Alquimia', criado_por=self.ana)
        self.sub = Tema.objects.create(nome='Ervas', pai=self.tema, criado_por=self.ana)
        self.livro = Livro.objects.create(titulo='Herbário', tema=self.sub, adicionado_por=self.ana,
                                          conteudo='A raiz de mandrágora cura febres.\nUse com cuidado.')
        self.client.force_login(self.ana)

    def test_paginas_renderizam(self):
        for url in [reverse('acervo'), reverse('acervo') + '?busca=mandrágora',
                    reverse('tema-detail', args=[self.tema.pk]), reverse('tema-detail', args=[self.sub.pk]),
                    reverse('livro-detail', args=[self.livro.pk]), reverse('tema-create') + f'?pai={self.tema.pk}',
                    reverse('livro-create') + f'?tema={self.sub.pk}', reverse('livro-update', args=[self.livro.pk]),
                    reverse('tema-delete', args=[self.sub.pk]), reverse('livro-delete', args=[self.livro.pk]),
                    reverse('mapa-create')]:
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_caminho_do_subtema(self):
        self.assertEqual(self.sub.caminho(), [self.tema, self.sub])
        self.assertEqual(str(self.sub), 'Alquimia / Ervas')

    def test_tema_nao_pode_ser_pai_de_si_mesmo(self):
        resp = self.client.post(reverse('tema-update', args=[self.tema.pk]), {'nome': 'Alquimia', 'pai': self.sub.pk})
        self.assertEqual(resp.status_code, 200)
        self.tema.refresh_from_db()
        self.assertIsNone(self.tema.pai)

    def test_criar_comentario_em_trecho(self):
        inicio = self.livro.conteudo.index('mandrágora')
        resp = self.client.post(reverse('comentario-livro-create', args=[self.livro.pk]),
                                json.dumps({'inicio': inicio, 'fim': inicio + 10, 'texto': 'Venenosa!'}),
                                content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        comentario = ComentarioLivro.objects.get()
        self.assertEqual(comentario.trecho, 'mandrágora')

    def test_comentario_com_selecao_invalida(self):
        resp = self.client.post(reverse('comentario-livro-create', args=[self.livro.pk]),
                                json.dumps({'inicio': 5, 'fim': 9999, 'texto': 'x'}), content_type='application/json')
        self.assertEqual(resp.status_code, 400)

    def test_so_autor_exclui_comentario(self):
        c = ComentarioLivro.objects.create(livro=self.livro, autor=self.ana, trecho='raiz', inicio=2, fim=6, texto='ok')
        self.client.force_login(self.bia)
        self.assertEqual(self.client.post(reverse('comentario-livro-delete', args=[c.pk])).status_code, 403)
        self.client.force_login(self.ana)
        self.assertEqual(self.client.post(reverse('comentario-livro-delete', args=[c.pk])).status_code, 200)

    def test_outro_usuario_nao_edita_livro(self):
        self.client.force_login(self.bia)
        self.assertEqual(self.client.get(reverse('livro-update', args=[self.livro.pk])).status_code, 403)

    def test_editar_conteudo_realoca_comentarios(self):
        c1 = ComentarioLivro.objects.create(livro=self.livro, autor=self.ana, trecho='febres', inicio=27, fim=33, texto='a')
        c2 = ComentarioLivro.objects.create(livro=self.livro, autor=self.ana, trecho='cuidado', inicio=42, fim=49, texto='b')
        self.client.post(reverse('livro-update', args=[self.livro.pk]), {
            'titulo': 'Herbário', 'tema': self.sub.pk, 'conteudo': 'Prefácio.\r\nA raiz de mandrágora cura febres.',
        })
        c1.refresh_from_db(); c2.refresh_from_db()
        self.livro.refresh_from_db()
        self.assertNotIn('\r', self.livro.conteudo)
        self.assertEqual(self.livro.conteudo[c1.inicio:c1.fim], 'febres')
        self.assertIsNone(c2.inicio)


class TeorizacaoTests(TestCase):
    def setUp(self):
        self.ana = Usuario.objects.create_user(username='ana', password='x', nickname='Ana')
        self.bia = Usuario.objects.create_user(username='bia', password='x', nickname='Bia')
        self.mapa = MapaTeorizacao.objects.create(usuario=self.ana, titulo='Teoria das ervas',
                                                  dados={'nos': [], 'conexoes': []})

    def test_salvar_mapa(self):
        self.client.force_login(self.ana)
        dados = {'nos': [{'id': 'n1', 'tipo': 'ideia', 'texto': 'Oi', 'x': 0, 'y': 0}], 'conexoes': []}
        resp = self.client.post(reverse('mapa-salvar', args=[self.mapa.pk]), json.dumps(dados), content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.mapa.refresh_from_db()
        self.assertEqual(self.mapa.dados, dados)
        self.assertEqual(self.client.get(reverse('mapa-detail', args=[self.mapa.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse('mapa-list')).status_code, 200)

    def test_mapa_e_pessoal(self):
        self.client.force_login(self.bia)
        self.assertEqual(self.client.get(reverse('mapa-detail', args=[self.mapa.pk])).status_code, 404)
        resp = self.client.post(reverse('mapa-salvar', args=[self.mapa.pk]),
                                json.dumps({'nos': [], 'conexoes': []}), content_type='application/json')
        self.assertEqual(resp.status_code, 404)
