import unicodedata
import uuid

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_delete
from django.dispatch import receiver

def chave_alfabetica(texto):
    """Texto sem acentos e em minúsculas, para ordenar "Árvore" junto com "arvore" e antes de "Bruma"."""
    sem_acento = ''.join(c for c in unicodedata.normalize('NFKD', texto or '') if not unicodedata.combining(c))
    return sem_acento.casefold().strip()


class Usuario(AbstractUser):
    # Só MED e ADM têm permissões especiais; as demais profissões são apenas identificação
    TIPO_CHOICES = [
        ('MED', 'Médico'),
        ('ENG', 'Engenheiro'),
        ('FER', 'Ferreiro'),
        ('COZ', 'Cozinheiro'),
        ('ALQ', 'Alquimista'),
        ('BRU', 'Bruxo'),
        ('OUT', 'Outro'),
        ('ADM', 'Administrador'),
    ]
    CORES_TIPO = {
        'MED': 'bg-green-100 text-green-700',
        'ENG': 'bg-slate-200 text-slate-700',
        'FER': 'bg-orange-100 text-orange-700',
        'COZ': 'bg-red-100 text-red-700',
        'ALQ': 'bg-teal-100 text-teal-700',
        'BRU': 'bg-purple-100 text-purple-700',
        'OUT': 'bg-gray-100 text-gray-700',
        'ADM': 'bg-yellow-100 text-yellow-700',
    }

    nickname = models.CharField(max_length=100)
    tipo = models.CharField(max_length=3, choices=TIPO_CHOICES, default='OUT')
    cidade = models.ForeignKey('Cidade', on_delete=models.SET_NULL, null=True, blank=True)

    @property
    def classes_tipo(self):
        """Classes Tailwind da etiqueta da profissão."""
        return self.CORES_TIPO.get(self.tipo, self.CORES_TIPO['OUT'])

    def __str__(self):
        return self.nickname

PARTES_CORPO = [
    ('CAB', 'Cabeça'),
    ('OLH', 'Olhos'),
    ('OUV', 'Ouvidos'),
    ('BRA', 'Braços'),
    ('MAO', 'Mãos'),
    ('DED', 'Dedos'),
    ('TOR', 'Tórax'),
    ('COR', 'Coração'),
    ('PUL', 'Pulmões'),
    ('VAS', 'Vasos sanguíneos'),
    ('EST', 'Estômago'),
    ('FIG', 'Fígado'),
    ('RIM', 'Rins'),
    ('INT', 'Intestinos'),
    ('COL', 'Coluna vertebral'),
    ('OSS', 'Ossos'),
    ('MUS', 'Músculos'),
    ('PEL', 'Pele'),
    ('MEN', 'Mente'),
    ('CAN', 'Canais de Essência'),
    ('SAN', 'Sangue'),
    ('OUT', 'Outros'),
]

TIPO_DOENCA = [
    ('F', 'Física'),
    ('M', 'Mental'),
    ('A', 'Mágica'),
]

TIPO_SINTOMA = [
    ('F', 'Físico'),
    ('M', 'Mental'),
    ('A', 'Mágico'),
]

# Doenças

class Doenca(models.Model):
    nome = models.CharField(max_length=100)
    origem = models.TextField(blank=True)
    contagiosa = models.BooleanField(default=False)
    forma_contagio = models.CharField(max_length=255, blank=True, null=True)
    parte_afetada = models.CharField(max_length=3, choices=PARTES_CORPO)
    tipo = models.CharField(max_length=1, choices=TIPO_DOENCA)
    sintomas = models.TextField('Sintomas', blank=True, help_text="Descreva os sintomas, separados por vírgula")
    tratamento = models.TextField(blank=True, help_text="Protocolo de tratamento recomendado")
    reacoes_esperadas = models.TextField(blank=True, help_text="Reações esperadas ao tratamento")
    imagens = GenericRelation('Imagem')

    class Meta:
        verbose_name = "Doença"
        verbose_name_plural = "Doenças"
        ordering = ['nome']

    def __str__(self):
        return self.nome

class Cidade(models.Model):
    nome = models.CharField(max_length=100)
    funcao = models.CharField(max_length=100, default=None)

    def __str__(self):
        return self.nome

class Raca(models.Model):
    nome = models.CharField(max_length=100, unique=True, verbose_name="Nome")
    longevidade = models.CharField(max_length=200, blank=True, verbose_name="Longevidade", help_text="Ex: 80-100 anos")
    caracteristicas_fisicas = models.TextField(blank=True, verbose_name="Características físicas")
    cor_sangue = models.CharField(max_length=100, blank=True, verbose_name="Cor do sangue")
    pressao_arterial = models.CharField(max_length=200, blank=True, verbose_name="Pressão arterial", help_text="Ex: 120/80 mmHg")
    bpm = models.CharField(max_length=200, blank=True, verbose_name="Batimentos por minuto", help_text="Ex: 60-100 bpm")
    afinidade_magica = models.CharField(max_length=200, blank=True, verbose_name="Afinidade mágica")
    cuidados_especiais = models.TextField(blank=True, verbose_name="Cuidados especiais")
    alimentacao = models.TextField(blank=True, verbose_name="Alimentação")
    peculiaridades = models.TextField(blank=True, verbose_name="Peculiaridades")
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    imagens = GenericRelation('Imagem')

    class Meta:
        verbose_name = "Raça"
        verbose_name_plural = "Raças"
        ordering = ['nome']

    def __str__(self):
        return self.nome

class Paciente(models.Model):
    STATUS_CHOICES = [
        ('ESTAVEL', 'Estável'),
        ('TRATAMENTO', 'Em Tratamento'),
        ('CRONICO', 'Tratamento Crônico'),
        ('OBITO', 'Óbito'),
    ]

    AFINIDADE = [
        ('fo', 'Fogo'),
        ('ra', 'Raio'),
        ('cu', 'Cura'),
        ('na', 'Natureza'),
        ('ag', 'Água'),
        ('ge', 'Gelo'),
        ('sa', 'Sangue'),
        ('ev', 'Evocação'),
        ('va', 'Vazio'),
        ('nn', 'Nenhuma'),
    ]

    nome = models.CharField(max_length=200)
    idade = models.PositiveIntegerField(verbose_name="Idade")
    raca = models.ManyToManyField(Raca, related_name='racas')
    afinidade = models.CharField(max_length=2, choices=AFINIDADE, blank=True)
    fay_normal = models.CharField(max_length=100, blank=True, null=True, verbose_name="Fay Normal", help_text="Tipo de Fay predominante ou natural do paciente")
    cidade = models.ForeignKey(Cidade, on_delete=models.CASCADE, related_name='pacientes')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ESTAVEL')
    contatos_emergencia = models.TextField(blank=True, verbose_name="Contatos de Emergência", help_text="Nomes e informações de contato de emergência")
    observacoes = models.TextField(blank=True)
    doencas = models.ManyToManyField(Doenca, through='Diagnostico', related_name='pacientes')
    # Preenchido automaticamente; é por ele que os pacientes ficam em ordem alfabética
    nome_ordenacao = models.CharField(max_length=200, editable=False, db_index=True, default='')

    def __str__(self):
        return f"{self.nome} ({self.idade} anos, {self.get_status_display()})"

    def save(self, *args, **kwargs):
        self.nome_ordenacao = chave_alfabetica(self.nome)
        if kwargs.get('update_fields') is not None and 'nome' in kwargs['update_fields']:
            kwargs['update_fields'] = set(kwargs['update_fields']) | {'nome_ordenacao'}
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['cidade__nome', 'nome_ordenacao', 'nome']
        verbose_name_plural = "Pacientes"

class Diagnostico(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    sintomas = models.TextField(blank=True)
    observacoes = models.TextField(blank=True)
    hipoteses = models.ManyToManyField(Doenca, related_name='diagnosticos_hipotese', blank=True)
    doenca = models.ForeignKey(Doenca, on_delete=models.SET_NULL, null=True, blank=True)
    remedios = models.ManyToManyField('Remedio', blank=True, related_name='diagnosticos', verbose_name="Remédios prescritos")
    data = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    responsavel = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    tratado = models.BooleanField(default=False)

    class Meta:
        ordering = ['-data']

    def __str__(self):
        return f"Diagnóstico para {self.paciente} em {self.data}"

class RegistroMedico(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='registros')
    data = models.DateTimeField(auto_now_add=True)
    doenca = models.ForeignKey(Doenca, on_delete=models.SET_NULL, null=True, blank=True)
    sintomas_observados = models.TextField(help_text="Descrição detalhada dos sintomas observados")
    observacoes = models.TextField(blank=True, help_text="Anotações adicionais sobre o diagnóstico")
    tratamento_aplicado = models.TextField(blank=True, help_text="Tratamento aplicado")

    class Meta:
        ordering = ['-data']
        verbose_name = "Registro Médico"
        verbose_name_plural = "Registros Médicos"

    def __str__(self):
        return f"{self.paciente.nome} - {self.doenca.nome if self.doenca else 'Sem diagnóstico'} - {self.data.strftime('%d/%m/%Y')}"


class Besta(models.Model):
    NIVEL_AMEAÇA_CHOICES = [
        ('01', '1/10'),
        ('02', '2/10'),
        ('03', '3/10'),
        ('04', '4/10'),
        ('05', '5/10'),
        ('06', '6/10'),
        ('07', '7/10'),
        ('08', '8/10'),
        ('09', '9/10'),
        ('10', '10/10'),
    ]

    nome = models.CharField(max_length=100)
    titulo = models.CharField(max_length=200, blank=True)
    nivel_ameaca = models.CharField(max_length=2, choices=NIVEL_AMEAÇA_CHOICES, default='01')
    aparencia = models.TextField()
    pode_contaminar = models.BooleanField(default=False)
    contagio = models.TextField(blank=True, help_text="Descrição de como a besta pode contaminar outros")
    relacionada_com_essencia = models.BooleanField(default=False)
    corrompida_por_essencia = models.BooleanField(default=False)
    habilidades = models.TextField()
    doenca_relacionada = models.ManyToManyField(
        Doenca,
        related_name='bestas'
    )
    anotacoes = models.TextField(blank=True)
    imagens = GenericRelation('Imagem')

    def __str__(self):
        return f"{self.nome} - {self.get_nivel_ameaca_display()}"

class RelatorioExpedicao(models.Model):
    titulo = models.CharField(max_length=200)
    localizacao = models.CharField(max_length=200)
    data = models.DateTimeField(auto_now_add=True)
    descobertas = models.TextField()
    observacoes = models.TextField(blank=True)
    autor = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    imagens = GenericRelation('Imagem')

    class Meta:
        ordering = ['-data']

    def __str__(self):
        return self.titulo

class AnotacaoPessoal(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='anotacoes')
    titulo = models.CharField(max_length=100)
    conteudo = models.TextField()
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    tags = models.CharField(max_length=255, blank=True, help_text="Palavras-chave separadas por vírgula")

    class Meta:
        ordering = ['-data_atualizacao']
        verbose_name_plural = 'Anotações Pessoais'

    def __str__(self):
        return f"{self.titulo} - {self.usuario.nickname}"


class Ingrediente(models.Model):
    nome = models.CharField(max_length=200, unique=True, verbose_name="Nome")
    o_que_e = models.TextField(verbose_name="O que é", help_text="Descrição do ingrediente")
    o_que_faz = models.TextField(verbose_name="O que faz", help_text="Propriedades e efeitos do ingrediente")
    contra_indicacoes = models.TextField(blank=True, verbose_name="Contraindicações", help_text="Situações em que não deve ser usado")
    reacoes_adversas = models.TextField(blank=True, verbose_name="Reações adversas", help_text="Possíveis efeitos colaterais")
    cuidados_ao_uso = models.TextField(blank=True, verbose_name="Cuidados ao uso", help_text="Precauções necessárias")
    imagens = GenericRelation('Imagem')

    class Meta:
        verbose_name = "Ingrediente"
        verbose_name_plural = "Ingredientes"
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Remedio(models.Model):
    nome = models.CharField(max_length=200, verbose_name="Nome")
    descricao = models.TextField(blank=True, verbose_name="Descrição", help_text="Descrição geral do remédio")
    modo_uso = models.TextField(blank=True, verbose_name="Modo de uso", help_text="Instruções de como usar")
    ingredientes = models.ManyToManyField(Ingrediente, through='RemedioIngrediente', related_name='remedios')
    doencas = models.ManyToManyField(Doenca, blank=True, related_name='remedios', verbose_name="Doenças", help_text="Doenças que este remédio trata")
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    imagens = GenericRelation('Imagem')

    class Meta:
        verbose_name = "Remédio"
        verbose_name_plural = "Remédios"
        ordering = ['nome']

    def __str__(self):
        return self.nome


class RemedioIngrediente(models.Model):
    remedio = models.ForeignKey(Remedio, on_delete=models.CASCADE)
    ingrediente = models.ForeignKey(Ingrediente, on_delete=models.CASCADE)
    quantidade = models.CharField(max_length=200, verbose_name="Quantidade", help_text="Ex: 2 colheres, 100g, 5 gotas")

    class Meta:
        verbose_name = "Ingrediente do Remédio"
        verbose_name_plural = "Ingredientes do Remédio"
        unique_together = ['remedio', 'ingrediente']

    def __str__(self):
        return f"{self.ingrediente.nome} ({self.quantidade}) - {self.remedio.nome}"


# Acervo (biblioteca)


class Tema(models.Model):
    nome = models.CharField(max_length=150, verbose_name="Nome")
    descricao = models.TextField(blank=True, verbose_name="Descrição")
    pai = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                            related_name='subtemas', verbose_name="Tema pai")
    criado_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Tema"
        verbose_name_plural = "Temas"
        ordering = ['nome']

    def __str__(self):
        return " / ".join(t.nome for t in self.caminho())

    def caminho(self):
        """Lista de temas da raiz até este (para o breadcrumb)."""
        temas = []
        atual = self
        while atual is not None:
            temas.insert(0, atual)
            atual = atual.pai
        return temas

    def descendentes_ids(self):
        ids = [self.pk]
        for sub in self.subtemas.all():
            ids.extend(sub.descendentes_ids())
        return ids


class Livro(models.Model):
    titulo = models.CharField(max_length=200, verbose_name="Título")
    autor = models.CharField(max_length=200, blank=True, verbose_name="Autor")
    tema = models.ForeignKey(Tema, on_delete=models.CASCADE, related_name='livros', verbose_name="Tema")
    resumo = models.TextField(blank=True, verbose_name="Resumo")
    conteudo = models.TextField(blank=True, verbose_name="Conteúdo", help_text="Texto do livro (é nele que se fazem os comentários)")
    adicionado_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    imagens = GenericRelation('Imagem')
    # Preenchido automaticamente; é por ele que os livros ficam em ordem alfabética
    titulo_ordenacao = models.CharField(max_length=200, editable=False, db_index=True, default='')

    class Meta:
        verbose_name = "Livro"
        verbose_name_plural = "Livros"
        ordering = ['titulo_ordenacao', 'titulo']

    def __str__(self):
        return self.titulo

    def save(self, *args, **kwargs):
        self.titulo_ordenacao = chave_alfabetica(self.titulo)
        if kwargs.get('update_fields') is not None and 'titulo' in kwargs['update_fields']:
            kwargs['update_fields'] = set(kwargs['update_fields']) | {'titulo_ordenacao'}
        super().save(*args, **kwargs)

    def realocar_comentarios(self):
        """Depois de editar o conteúdo, reposiciona cada comentário procurando o trecho no novo texto."""
        for comentario in self.comentarios.all():
            if comentario.inicio is not None and self.conteudo[comentario.inicio:comentario.fim] == comentario.trecho:
                continue
            pos = self.conteudo.find(comentario.trecho) if comentario.trecho else -1
            if pos >= 0:
                comentario.inicio, comentario.fim = pos, pos + len(comentario.trecho)
            else:
                comentario.inicio = comentario.fim = None
            comentario.save(update_fields=['inicio', 'fim'])


class ComentarioLivro(models.Model):
    livro = models.ForeignKey(Livro, on_delete=models.CASCADE, related_name='comentarios')
    autor = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='comentarios_livro')
    trecho = models.TextField(verbose_name="Trecho selecionado")
    inicio = models.PositiveIntegerField(null=True, blank=True)
    fim = models.PositiveIntegerField(null=True, blank=True)
    texto = models.TextField(verbose_name="Comentário")
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Comentário de livro"
        verbose_name_plural = "Comentários de livros"
        ordering = ['inicio', 'data_criacao']

    def __str__(self):
        return f"{self.autor} em {self.livro}: {self.texto[:40]}"


# Teorização (mapas mentais pessoais)

class MapaTeorizacao(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='mapas')
    titulo = models.CharField(max_length=150, verbose_name="Título")
    descricao = models.TextField(blank=True, verbose_name="Descrição")
    # {"nos": [{"id", "tipo", "ref_id", "texto", "x", "y", "cor"}],
    #  "conexoes": [{"id", "de", "para", "rotulo"}]}
    # tipo: "ideia", "imagem" (ref_id = Imagem deste mapa) ou um registro do sistema
    # ("livro", "relatorio", "besta", "doenca", "raca", "ingrediente", "remedio", "paciente")
    dados = models.JSONField(default=dict, blank=True)
    imagens = GenericRelation('Imagem')
    # Aumenta a cada salvamento; usado para detectar edições simultâneas de colaboradores
    versao = models.PositiveIntegerField(default=0)
    # Compartilhamento: colaboradores editam; quem tem o link (se ativo) só visualiza
    colaboradores = models.ManyToManyField(Usuario, blank=True, related_name='mapas_colaborando')
    link_ativo = models.BooleanField(default=False, verbose_name="Link de visualização ativo")
    token_link = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Mapa de teorização"
        verbose_name_plural = "Mapas de teorização"
        ordering = ['-data_atualizacao']

    def __str__(self):
        return f"{self.titulo} - {self.usuario.nickname}"

    def pode_editar(self, usuario):
        return usuario.pk == self.usuario_id or self.colaboradores.filter(pk=usuario.pk).exists()


# Imagens (galeria genérica: expedições, bestiário, livros, doenças...)

def caminho_imagem(instancia, nome_arquivo):
    return f"imagens/{instancia.content_type.model}/{instancia.object_id}/{nome_arquivo}"


class Imagem(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    item = GenericForeignKey('content_type', 'object_id')
    arquivo = models.ImageField(upload_to=caminho_imagem, verbose_name="Imagem")
    legenda = models.CharField(max_length=200, blank=True, verbose_name="Legenda")
    enviada_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    data_envio = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Imagem"
        verbose_name_plural = "Imagens"
        ordering = ['data_envio', 'pk']
        indexes = [models.Index(fields=['content_type', 'object_id'])]

    def __str__(self):
        return self.legenda or self.arquivo.name


@receiver(post_delete, sender=Imagem)
def apagar_arquivo_imagem(sender, instance, **kwargs):
    instance.arquivo.delete(save=False)
