from django import forms
from .models import Bunker, Besta, Doenca, Paciente, Diagnostico, RegistroMedico, Sintoma
from django.forms.widgets import DateInput

class DoencaForm(forms.ModelForm):
    sintomas = forms.ModelMultipleChoiceField(
        queryset=Sintoma.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'select2'}),
        required=False
    )
    
    class Meta:
        model = Doenca
        fields = '__all__'
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'input'}),
            'origem': forms.Textarea(attrs={'class': 'textarea', 'rows': 3}),
            'forma_contagio': forms.Textarea(attrs={'class': 'textarea', 'rows': 2}),
            'tratamento': forms.Textarea(attrs={'class': 'textarea', 'rows': 4}),
            'reacoes_esperadas': forms.Textarea(attrs={'class': 'textarea', 'rows': 4}),
        }
        help_texts = {
            'sintomas': 'Segure Ctrl para selecionar múltiplos sintomas',
        }

class PacienteForm(forms.ModelForm):
    class Meta:
        model = Paciente
        fields = '__all__'
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
    sintomas_texto = forms.CharField(
        label='Descrição dos Sintomas',
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Descreva os sintomas observados (febre, dor de cabeça, etc.)'
        }),
        required=True
    )
    
    class Meta:
        model = RegistroMedico
        fields = ['paciente', 'sintomas_texto', 'observacoes', 'tratamento_aplicado']
        widgets = {
            'paciente': forms.HiddenInput(),
            'observacoes': forms.Textarea(attrs={'rows': 3}),
            'tratamento_aplicado': forms.Textarea(attrs={'rows': 3}),
        }

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

class DiagnosticoForm(forms.ModelForm):
    sintomas = forms.ModelMultipleChoiceField(
        queryset=Sintoma.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    
    class Meta:
        model = Diagnostico
        fields = ['doenca', 'observacoes']
        
    def __init__(self, *args, **kwargs):
        paciente = kwargs.pop('paciente', None)
        super().__init__(*args, **kwargs)
        if paciente:
            self.fields['doenca'].queryset = Doenca.objects.filter(
                sintomas__in=paciente.sintomas_observados.all()
            ).distinct()

class SintomaForm(forms.Form):
    sintoma = forms.ModelChoiceField(
        queryset=Sintoma.objects.all(),
        widget=forms.Select(attrs={'class': 'select'}),
        label="Adicionar Sintoma"
    )

class BestaForm(forms.ModelForm):
    class Meta:
        model = Besta
        fields = '__all__'
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'input'}),
            'titulo': forms.TextInput(attrs={'class': 'input'}),
            'aparencia': forms.Textarea(attrs={'class': 'textarea', 'rows': 3}),
            'habilidades': forms.Textarea(attrs={'class': 'textarea', 'rows': 3}),
            'anotacoes': forms.Textarea(attrs={'class': 'textarea', 'rows': 3}),
        }