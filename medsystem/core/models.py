from django.db import models
from django.contrib.auth.models import AbstractUser

class Usuario(AbstractUser):
    TIPO_CHOICES = [
        ('MED', 'Médico'),
        ('OUT', 'Outro'),
        ('ADM', 'Administrador'),
    ]

    nickname = models.CharField(max_length=100)
    tipo = models.CharField(max_length=3, choices=TIPO_CHOICES, default='OUT')
    cidade = models.ForeignKey('Cidade', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.nickname

PARTES_CORPO = [
    ('CAB', 'Cabeça'),
    ('OLH', 'Olhos'),
    ('OUV', 'Ouvidos'),
    ('NAR', 'Nariz'),
    ('BOC', 'Boca'),
    ('DEN', 'Dentes'),
    ('PES', 'Pescoço'),
    ('OMB', 'Ombros'),
    ('BRA', 'Braços'),
    ('COT', 'Cotovelos'),
    ('MAO', 'Mãos'),
    ('DED', 'Dedos'),
    ('TOR', 'Tórax'),
    ('COR', 'Coração'),
    ('PUL', 'Pulmões'),
    ('VAS', 'Vasos sanguíneos'),
    ('EST', 'Estômago'),
    ('FIG', 'Fígado'),
    ('BEX', 'Bexiga'),
    ('RIM', 'Rins'),
    ('INT', 'Intestinos'),
    ('ESP', 'Esôfago'),
    ('COL', 'Coluna vertebral'),
    ('OSS', 'Ossos'),
    ('MUS', 'Músculos'),
    ('JOE', 'Joelhos'),
    ('TOR', 'Tornozelos'),
    ('PES', 'Pés'),
    ('PEL', 'Pele'),
    ('MEN', 'Mente'),
    ('CAN', 'Canais de Essência'),
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

    def __str__(self):
        return f"{self.nome} ({self.idade} anos, {self.get_status_display()})"

    class Meta:
        ordering = ['cidade__nome', 'nome']
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

    def __str__(self):
        return f"{self.nome} - {self.get_nivel_ameaca_display()}"

class RelatorioExpedicao(models.Model):
    titulo = models.CharField(max_length=200)
    localizacao = models.CharField(max_length=200)
    data = models.DateTimeField(auto_now_add=True)
    descobertas = models.TextField()
    observacoes = models.TextField(blank=True)
    autor = models.ForeignKey(Usuario, on_delete=models.CASCADE)

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