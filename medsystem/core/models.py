from django.db import models
from django.contrib.auth.models import AbstractUser

class Usuario(AbstractUser):
    TIPO_CHOICES = [
        ('MED', 'Médico'),
        ('OUT', 'Outro'),
    ]
    
    nickname = models.CharField(max_length=100)
    tipo = models.CharField(max_length=3, choices=TIPO_CHOICES, default='OUT')
    bunker = models.ForeignKey('Bunker', on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self):
        return f"{self.username} ({self.get_tipo_display()})"

PARTES_CORPO = [
    ('CAB', 'Cabeça'),
    ('COR', 'Coração'),
    ('PUL', 'Pulmões'),
    ('EST', 'Estômago'),
    ('PEL', 'Pele'),
    ('OSS', 'Ossos'),
    ('MEN', 'Mente'),
]

TIPO_DOENCA = [
    ('F', 'Física'),
    ('M', 'Mental'),
    ('B', 'Ambas'),
]

TIPO_SINTOMA = [
    ('F', 'Físico'),
    ('M', 'Mental'),
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

class Bunker(models.Model):
    nome = models.CharField(max_length=100)
    funcao = models.CharField(max_length=100, default=None)
    
    def __str__(self):
        return self.nome

class Paciente(models.Model):
    STATUS_CHOICES = [
        ('ESTAVEL', 'Estável'),
        ('TRATAMENTO', 'Em Tratamento'),
        ('CRONICO', 'Tratamento Crônico'),
        ('OBITO', 'Óbito'),
    ]
    
    TIPO_SANGUINEO_CHOICES = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    ]
    
    nome = models.CharField(max_length=100)
    idade = models.PositiveIntegerField(verbose_name="Idade")
    tipo_sanguineo = models.CharField(max_length=3, choices=TIPO_SANGUINEO_CHOICES, blank=True)
    bunker = models.ForeignKey(Bunker, on_delete=models.CASCADE, related_name='pacientes')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ESTAVEL')
    observacoes = models.TextField(blank=True)
    doencas = models.ManyToManyField(Doenca, through='Diagnostico', related_name='pacientes')
    
    def __str__(self):
        return f"{self.nome} ({self.idade} anos, {self.get_status_display()})"
    
    class Meta:
        ordering = ['bunker__nome', 'nome']
        verbose_name_plural = "Pacientes"

class Diagnostico(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    sintomas = models.TextField(blank=True)
    observacoes = models.TextField(blank=True)
    hipoteses = models.ManyToManyField(Doenca, related_name='diagnosticos_hipotese', blank=True)
    doenca = models.ForeignKey(Doenca, on_delete=models.SET_NULL, null=True, blank=True)
    data = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    responsavel = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    
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
    imagem = models.ImageField(upload_to='bestas/', null=True, blank=True)
    nivel_ameaca = models.CharField(max_length=2, choices=NIVEL_AMEAÇA_CHOICES, default='01')
    aparencia = models.TextField()
    habilidades = models.TextField()
    doenca_relacionada = models.ManyToManyField(
        Doenca,
        related_name='bestas'
    )
    anotacoes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.nome} - {self.get_nivel_ameaca_display()}"


class Postagem(models.Model):
    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    data = models.DateTimeField(auto_now_add=True)
    imagem = models.ImageField(upload_to='postagens/', null=True, blank=True)
    autor = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    
    class Meta:
        ordering = ['-data']
    
    def __str__(self):
        return self.titulo

class Comentario(models.Model):
    postagem = models.ForeignKey(Postagem, on_delete=models.CASCADE, related_name='comentarios')
    autor = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    texto = models.TextField()
    data = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['data']
    
    def __str__(self):
        return f"Comentário de {self.autor} em {self.postagem}"

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