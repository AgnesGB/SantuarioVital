from django import forms
from .models import Postagem, Usuario, RelatorioExpedicao, Bunker, Besta, Doenca, Paciente, Diagnostico, RegistroMedico
from django.forms.widgets import DateInput
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

class DoencaForm(forms.ModelForm):
    class Meta:
        model = Doenca
        fields = '__all__'
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'input'}),
            'origem': forms.Textarea(attrs={'class': 'textarea', 'rows': 3}),
            'tratamento': forms.Textarea(attrs={'class': 'textarea', 'rows': 3}),
            'sintomas': forms.TextInput(attrs={'class': 'input'}),
        }

class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = ['nome', 'idade', 'tipo_sanguineo', 'bunker', 'status', 'observacoes']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'input'}),
            'idade': forms.NumberInput(attrs={
                'class': 'input',
                'min': '0',
                'max': '150'
            }),
            'tipo_sanguineo': forms.Select(attrs={'class': 'select'}),
            'bunker': forms.Select(attrs={'class': 'select'}),
            'status': forms.Select(attrs={'class': 'select'}),
            'observacoes': forms.Textarea(attrs={'class': 'textarea', 'rows': 3}),
        }

class RegistroMedicoForm(forms.ModelForm):
    sintomas_observados = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'textarea',
            'rows': 3,
            'placeholder': 'Descreva os sintomas observados'
        }),
        required=True
    )
    
    class Meta:
        model = RegistroMedico
        fields = ['paciente', 'sintomas_observados', 'observacoes', 'tratamento_aplicado']

class BunkerForm(forms.ModelForm):
    class Meta:
        model = Bunker
        fields = ['nome']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'input'}),
        }
        labels = {
            'nome': 'Nome do Bunker',
        }

class UsuarioCreationForm(UserCreationForm):
    nickname = forms.CharField(max_length=100, required=True)
    
    class Meta:
        model = Usuario
        fields = ['username', 'nickname', 'password1', 'password2', 'tipo', 'bunker']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'select'}),
            'bunker': forms.Select(attrs={'class': 'select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'input'})
        self.fields['nickname'].widget.attrs.update({'class': 'input'})
        self.fields['password1'].widget.attrs.update({'class': 'input'})
        self.fields['password2'].widget.attrs.update({'class': 'input'})
        
class PostagemForm(forms.ModelForm):
    class Meta:
        model = Postagem
        fields = ['titulo', 'descricao', 'imagem']

class RelatorioExpedicaoForm(forms.ModelForm):
    class Meta:
        model = RelatorioExpedicao
        fields = ['titulo', 'localizacao', 'descobertas', 'observacoes']

class DiagnosticoForm(forms.ModelForm):
    class Meta:
        model = Diagnostico
        fields = ['sintomas', 'observacoes', 'hipoteses', 'doenca']
        widgets = {
            'hipoteses': forms.SelectMultiple(attrs={
                'class': 'select is-multiple',
                'style': 'width: 100%'
            }),
            'doenca': forms.Select(attrs={'class': 'select'}),
            'sintomas': forms.Textarea(attrs={
                'class': 'textarea', 
                'rows': 3,
                'placeholder': 'Descreva os sintomas observados'
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'textarea', 
                'rows': 3,
                'placeholder': 'Anotações adicionais'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        paciente = kwargs.pop('paciente', None)
        super().__init__(*args, **kwargs)
        
        # Torna os campos opcionais
        self.fields['hipoteses'].required = False
        self.fields['doenca'].required = False
        
        # Configura o queryset para as hipóteses
        if paciente:
            self.fields['hipoteses'].queryset = Doenca.objects.all()
        
        # Se for uma instância existente, seleciona as hipóteses atuais
        if self.instance.pk:
            self.fields['hipoteses'].initial = self.instance.hipoteses.all()
    
    def __init__(self, *args, **kwargs):
        paciente = kwargs.pop('paciente', None)
        super().__init__(*args, **kwargs)
        self.fields['hipoteses'].required = False
        self.fields['doenca'].required = False
        if paciente:
            self.fields['hipoteses'].queryset = Doenca.objects.all()

class BestaForm(forms.ModelForm):
    doenca_relacionada = forms.ModelMultipleChoiceField(
        queryset=Doenca.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'select2'}),
        required=False  # Isso permite que o campo fique em branco
    )
    
    class Meta:
        model = Besta
        fields = '__all__'