import json
import os
import tempfile
from datetime import timedelta

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import (Besta, Cidade, ComentarioLivro, Imagem, Livro, MapaTeorizacao, Paciente, RelatorioExpedicao, Tema,
                     Usuario)


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


def imagem_teste(nome='teste.png'):
    from io import BytesIO
    from django.core.files.uploadedfile import SimpleUploadedFile
    from PIL import Image as PILImage
    buf = BytesIO()
    PILImage.new('RGB', (8, 8), 'red').save(buf, 'PNG')
    return SimpleUploadedFile(nome, buf.getvalue(), content_type='image/png')


MEDIA_TESTE = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_TESTE)
class ImagensTests(TestCase):
    def setUp(self):
        self.ana = Usuario.objects.create_user(username='ana', password='x', nickname='Ana', tipo='ADM')
        self.client.force_login(self.ana)

    def test_relatorio_com_imagens_e_legenda(self):
        resp = self.client.post(reverse('relatorio-create'), {
            'titulo': 'Vale', 'localizacao': 'Norte', 'descobertas': 'Ruínas',
            'imagens_novas': [imagem_teste('a.png'), imagem_teste('b.png')], 'legenda_nova': ['Entrada', ''],
        })
        self.assertEqual(resp.status_code, 302)
        relatorio = RelatorioExpedicao.objects.get()
        self.assertEqual([i.legenda for i in relatorio.imagens.all()], ['Entrada', ''])
        self.assertContains(self.client.get(reverse('relatorio-detail', args=[relatorio.pk])), 'Entrada')

    def test_arquivo_que_nao_e_imagem_e_ignorado(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        self.client.post(reverse('relatorio-create'), {
            'titulo': 'Vale', 'localizacao': 'Norte', 'descobertas': 'Ruínas',
            'imagens_novas': [SimpleUploadedFile('x.png', b'nada', content_type='image/png')],
        })
        self.assertEqual(Imagem.objects.count(), 0)

    def test_remover_imagem_ao_editar(self):
        besta = Besta.objects.create(nome='Lobo', aparencia='Cinza', habilidades='Uivar')
        img = Imagem.objects.create(item=besta, arquivo=imagem_teste())
        caminho = img.arquivo.path
        resp = self.client.post(reverse('besta-update', args=[besta.pk]), {
            'nome': 'Lobo', 'titulo': '', 'nivel_ameaca': '02', 'aparencia': 'Cinza', 'habilidades': 'Uivar',
            'remover_imagem': [img.pk],
        })
        self.assertEqual(resp.status_code, 302, getattr(resp, 'context', None) and resp.context['form'].errors)
        self.assertFalse(besta.imagens.exists())
        self.assertFalse(os.path.exists(caminho))

    def test_mapa_imagem_e_catalogo(self):
        mapa = MapaTeorizacao.objects.create(usuario=self.ana, titulo='M', dados={'nos': [], 'conexoes': []})
        Besta.objects.create(nome='Lobo', aparencia='Cinza', habilidades='Uivar')
        Paciente.objects.create(nome='Joana', idade=30, cidade=Cidade.objects.create(nome='Norte', funcao='Vila'))
        resp = self.client.post(reverse('mapa-imagem-enviar', args=[mapa.pk]), {'imagem': imagem_teste()})
        self.assertEqual(resp.status_code, 201)
        img_id = resp.json()['id']
        tela = self.client.get(reverse('mapa-detail', args=[mapa.pk]))
        tipos = {i['tipo'] for i in tela.context['itens_json']}
        self.assertTrue({'besta', 'paciente'} <= tipos)
        self.assertIn(img_id, tela.context['imagens_mapa_json'])

        # Imagem que saiu do mapa é apagada (depois do tempo de folga)
        Imagem.objects.filter(pk=img_id).update(data_envio=timezone.now() - timedelta(hours=1))
        self.client.post(reverse('mapa-salvar', args=[mapa.pk]), json.dumps({'nos': [], 'conexoes': []}),
                         content_type='application/json')
        self.assertFalse(Imagem.objects.filter(pk=img_id).exists())

    def test_paciente_fora_do_catalogo_para_nao_medicos(self):
        from .views_acervo import catalogo_teorizacao
        Paciente.objects.create(nome='Joana', idade=30, cidade=Cidade.objects.create(nome='Norte', funcao='Vila'))
        comum = Usuario.objects.create_user(username='c', password='x', nickname='C', tipo='OUT')
        self.assertNotIn('paciente', {i['tipo'] for i in catalogo_teorizacao(comum)})


class CompartilhamentoTests(TestCase):
    def setUp(self):
        self.ana = Usuario.objects.create_user(username='ana', password='x', nickname='Ana')
        self.bia = Usuario.objects.create_user(username='bia', password='x', nickname='Bia')
        self.caio = Usuario.objects.create_user(username='caio', password='x', nickname='Caio')
        self.livro = Livro.objects.create(titulo='Herbário', tema=Tema.objects.create(nome='Ervas'))
        Livro.objects.create(titulo='Fora do mapa', tema=self.livro.tema)
        self.mapa = MapaTeorizacao.objects.create(usuario=self.ana, titulo='Teoria', dados={
            'nos': [{'id': 'n1', 'tipo': 'livro', 'ref_id': self.livro.pk, 'x': 0, 'y': 0}], 'conexoes': []})
        self.link = reverse('mapa-compartilhado', args=[self.mapa.token_link])

    def salvar(self, usuario, versao, nos):
        self.client.force_login(usuario)
        return self.client.post(reverse('mapa-salvar', args=[self.mapa.pk]),
                                json.dumps({'versao': versao, 'nos': nos, 'conexoes': []}), content_type='application/json')

    def compartilhar(self, quem, **dados):
        self.client.force_login(quem)
        return self.client.post(reverse('mapa-compartilhamento', args=[self.mapa.pk]), json.dumps(dados),
                                content_type='application/json')

    def test_link_desativado_nao_abre(self):
        self.client.force_login(self.bia)
        self.assertEqual(self.client.get(self.link).status_code, 404)

    def test_link_ativo_abre_somente_leitura(self):
        self.compartilhar(self.ana, acao='link', ativo=True)
        self.client.force_login(self.bia)
        resp = self.client.get(self.link)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context['somente_leitura'])
        self.assertEqual([i['titulo'] for i in resp.context['itens_json']], ['Herbário'])
        self.assertEqual(self.client.get(reverse('mapa-compartilhado-estado', args=[self.mapa.token_link])).status_code, 200)
        # Quem só tem o link não edita nem abre o editor
        self.assertEqual(self.salvar(self.bia, 0, []).status_code, 404)
        self.assertEqual(self.client.get(reverse('mapa-detail', args=[self.mapa.pk])).status_code, 404)

    def test_link_exige_login(self):
        self.compartilhar(self.ana, acao='link', ativo=True)
        self.client.logout()
        self.assertEqual(self.client.get(self.link).status_code, 302)

    def test_novo_link_invalida_o_antigo(self):
        self.compartilhar(self.ana, acao='link', ativo=True)
        self.compartilhar(self.ana, acao='novo_link')
        self.client.force_login(self.bia)
        self.assertEqual(self.client.get(self.link).status_code, 404)

    def test_colaborador_edita(self):
        resp = self.compartilhar(self.ana, acao='adicionar', usuario='Bia')
        self.assertEqual([c['username'] for c in resp.json()['colaboradores']], ['bia'])
        self.client.force_login(self.bia)
        tela = self.client.get(reverse('mapa-detail', args=[self.mapa.pk]))
        self.assertFalse(tela.context['somente_leitura'])
        self.assertFalse(tela.context['eh_dono'])
        self.assertEqual(self.salvar(self.bia, 0, []).status_code, 200)
        self.assertIn(self.mapa, [m for m in self.client.get(reverse('mapa-list')).context['compartilhados']])
        # Pelo link, o colaborador vai direto para o editor
        self.assertRedirects(self.client.get(self.link), reverse('mapa-detail', args=[self.mapa.pk]))

    def test_conflito_de_versao(self):
        self.compartilhar(self.ana, acao='adicionar', usuario='bia')
        self.assertEqual(self.salvar(self.ana, 0, []).status_code, 200)
        resp = self.salvar(self.bia, 0, [{'id': 'n2', 'tipo': 'ideia', 'x': 0, 'y': 0}])
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.json()['versao'], 1)
        self.assertEqual(self.salvar(self.bia, 1, [{'id': 'n2', 'tipo': 'ideia', 'x': 0, 'y': 0}]).status_code, 200)

    def test_so_dono_gerencia_e_exclui(self):
        self.compartilhar(self.ana, acao='adicionar', usuario='bia')
        self.assertEqual(self.compartilhar(self.bia, acao='adicionar', usuario='caio').status_code, 404)
        self.assertEqual(self.client.post(reverse('mapa-delete', args=[self.mapa.pk])).status_code, 404)
        self.client.post(reverse('mapa-sair', args=[self.mapa.pk]))
        self.assertFalse(self.mapa.colaboradores.exists())

    def test_usuario_inexistente(self):
        self.assertEqual(self.compartilhar(self.ana, acao='adicionar', usuario='ninguem').status_code, 400)


class UsuariosAdminTests(TestCase):
    def setUp(self):
        self.adm = Usuario.objects.create_user(username='adm', password='x', nickname='Adm', tipo='ADM')
        self.joao = Usuario.objects.create_user(username='joao', password='x', nickname='João', tipo='OUT')
        self.client.force_login(self.adm)

    def dados(self, u, **extra):
        return {'username': u.username, 'nickname': u.nickname, 'tipo': u.tipo, 'cidade': '', 'is_active': 'on', **extra}

    def test_home_mostra_profissoes(self):
        self.joao.tipo = 'BRU'
        self.joao.save()
        resp = self.client.get(reverse('home'))
        self.assertContains(resp, 'Bruxo')
        self.assertContains(resp, 'Alquimista')   # opção no menu do admin

    def test_alterar_tipo_para_nova_profissao(self):
        self.client.post(reverse('alterar-tipo-usuario', args=[self.joao.pk]), {'tipo': 'FER'})
        self.joao.refresh_from_db()
        self.assertEqual(self.joao.get_tipo_display(), 'Ferreiro')

    def test_admin_edita_usuario_e_senha(self):
        resp = self.client.post(reverse('usuario-update', args=[self.joao.pk]),
                                self.dados(self.joao, nickname='Joãozinho', tipo='ALQ', nova_senha='SenhaNova!2026'))
        self.assertRedirects(resp, reverse('home'))
        self.joao.refresh_from_db()
        self.assertEqual((self.joao.nickname, self.joao.tipo), ('Joãozinho', 'ALQ'))
        self.assertTrue(self.joao.check_password('SenhaNova!2026'))

    def test_admin_nao_se_rebaixa_nem_se_desativa(self):
        resp = self.client.post(reverse('usuario-update', args=[self.adm.pk]), self.dados(self.adm, tipo='OUT'))
        self.assertEqual(resp.status_code, 200)
        dados = self.dados(self.adm)
        del dados['is_active']
        self.assertEqual(self.client.post(reverse('usuario-update', args=[self.adm.pk]), dados).status_code, 200)
        self.client.post(reverse('alterar-tipo-usuario', args=[self.adm.pk]), {'tipo': 'MED'})
        self.adm.refresh_from_db()
        self.assertEqual((self.adm.tipo, self.adm.is_active), ('ADM', True))

    def test_excluir_usuario_transfere_conteudo(self):
        from .models import AnotacaoPessoal
        relatorio = RelatorioExpedicao.objects.create(titulo='T', localizacao='L', descobertas='D', autor=self.joao)
        anotacao = AnotacaoPessoal.objects.create(usuario=self.joao, titulo='Nota', conteudo='x', tags='ervas')
        mapa = MapaTeorizacao.objects.create(usuario=self.joao, titulo='Mapa', dados={'nos': [], 'conexoes': []})
        mapa.colaboradores.add(self.adm)
        tela = self.client.get(reverse('usuario-delete', args=[self.joao.pk]))
        self.assertContains(tela, '1 relatório(s) de expedição')
        self.client.post(reverse('usuario-delete', args=[self.joao.pk]))
        self.assertFalse(Usuario.objects.filter(pk=self.joao.pk).exists())
        relatorio.refresh_from_db(); anotacao.refresh_from_db(); mapa.refresh_from_db()
        self.assertEqual((relatorio.autor, anotacao.usuario, mapa.usuario), (self.adm, self.adm, self.adm))
        self.assertIn('João', relatorio.observacoes)
        self.assertEqual(anotacao.tags, 'ervas, de João')
        self.assertEqual(mapa.titulo, 'Mapa (de João)')
        self.assertFalse(mapa.colaboradores.exists())
        self.assertEqual(self.client.get(reverse('usuario-delete', args=[self.adm.pk])).status_code, 404)

    def test_nao_admin_nao_gerencia(self):
        self.client.force_login(self.joao)
        self.assertEqual(self.client.get(reverse('usuario-update', args=[self.adm.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse('usuario-delete', args=[self.adm.pk])).status_code, 403)


class HomeTests(TestCase):
    def test_cards_por_tipo_de_usuario(self):
        comum = Usuario.objects.create_user(username='f', password='x', nickname='Ferreira', tipo='FER')
        self.client.force_login(comum)
        resp = self.client.get(reverse('home'))
        for url in ['acervo', 'mapa-list', 'besta-list', 'relatorio-list', 'doenca-list', 'anotacao-list']:
            self.assertContains(resp, f'href="{reverse(url)}" class="inline-flex', msg_prefix=url)
        self.assertNotContains(resp, 'Gerenciar Pacientes')

        medico = Usuario.objects.create_user(username='m', password='x', nickname='Med', tipo='MED')
        self.client.force_login(medico)
        self.assertContains(self.client.get(reverse('home')), 'Gerenciar Pacientes')


class OrdemAlfabeticaTests(TestCase):
    def test_livros_em_ordem_ignorando_acentos_e_maiusculas(self):
        tema = Tema.objects.create(nome='Geral')
        for titulo in ['Zumbis do Norte', 'Árvores Sagradas', 'bestas menores', 'Éter e Essência', 'Alquimia', 'ervas']:
            Livro.objects.create(titulo=titulo, tema=tema)
        esperado = ['Alquimia', 'Árvores Sagradas', 'bestas menores', 'ervas', 'Éter e Essência', 'Zumbis do Norte']
        self.assertEqual([l.titulo for l in Livro.objects.all()], esperado)
        self.assertEqual([l.titulo for l in tema.livros.all()], esperado)

    def test_renomear_reordena(self):
        tema = Tema.objects.create(nome='Geral')
        livro = Livro.objects.create(titulo='Zeta', tema=tema)
        Livro.objects.create(titulo='Beta', tema=tema)
        livro.titulo = 'Água'
        livro.save(update_fields=['titulo'])
        self.assertEqual(Livro.objects.first().titulo, 'Água')

    def test_pacientes_em_ordem_ignorando_acentos(self):
        medico = Usuario.objects.create_user(username='m', password='x', nickname='Med', tipo='MED')
        cidade = Cidade.objects.create(nome='Norte', funcao='Vila')
        for nome in ['Zélia', 'Ícaro', 'bruno', 'Ana', 'Íris', 'Igor']:
            Paciente.objects.create(nome=nome, idade=30, cidade=cidade)
        esperado = ['Ana', 'bruno', 'Ícaro', 'Igor', 'Íris', 'Zélia']
        self.assertEqual([p.nome for p in Paciente.objects.all()], esperado)
        self.client.force_login(medico)
        lista = self.client.get(reverse('paciente-list')).context['pacientes']
        self.assertEqual([p.nome for p in lista], esperado)
